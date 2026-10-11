from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Optional

from .citations import (
    ReferenceCandidateRecord,
    extract_references_from_passage,
)
from .entities import (
    EntityMentionRecord,
    extract_entity_mentions,
    is_institution_entity,
)
from .frontier import (
    FrontierEvidenceRecord,
    FrontierItemRecord,
    SourceNominationRecord,
    compute_terminology_frontier_score,
    make_dedup_key,
    make_frontier_id,
    make_nomination_id,
    utc_now_iso,
)
from .passages import PassageRecord
from .resolution import ReferenceResolutionAttempt, resolve_reference
from .terminology import DefinitionCandidate, NativeTerm
from .equation_witness import EquationWitnessRecord
from .work_db import WorkDatabase


@dataclass
class CoordinatorSummary:
    sources_processed: int
    references_extracted: int
    resolutions_attempted: int
    entity_mentions_extracted: int
    frontier_items_created: int
    frontier_evidence_recorded: int
    nominations_generated: int
    negative_controls_rejected: int


def _passage_text(p: Any) -> str:
    if hasattr(p, "text") and p.text:
        return p.text
    if hasattr(p, "text_unicode") and p.text_unicode:
        return p.text_unicode
    if hasattr(p, "text_source") and p.text_source:
        return p.text_source
    if isinstance(p, dict):
        return p.get("text") or p.get("text_unicode") or p.get("text_source") or ""
    return str(p)


class FrontierCoordinator:
    def __init__(self, db: WorkDatabase) -> None:
        self.db = db

    def process_cohort_data(
        self,
        cohort: list[dict[str, Any]],
        candidate_source_pool: Optional[list[dict[str, Any]]] = None,
        max_nominations: int = 20,
    ) -> CoordinatorSummary:
        """Process extracted N1/N1.5 data across a cohort and generate N2 citations, entities, and frontier items."""
        summary = CoordinatorSummary(
            sources_processed=len(cohort),
            references_extracted=0,
            resolutions_attempted=0,
            entity_mentions_extracted=0,
            frontier_items_created=0,
            frontier_evidence_recorded=0,
            nominations_generated=0,
            negative_controls_rejected=0,
        )

        all_references: list[ReferenceCandidateRecord] = []
        all_resolutions: list[ReferenceResolutionAttempt] = []
        all_mentions: list[EntityMentionRecord] = []
        all_nominations: list[SourceNominationRecord] = []

        pool = candidate_source_pool or []

        # Track sources where each term appears for independent source weighting
        term_source_map: dict[str, set[str]] = {}
        for item in cohort:
            src_id = item["source_id"]
            terms: list[NativeTerm] = item.get("terms", [])
            for t in terms:
                term_source_map.setdefault(t.normalized_unicode, set()).add(src_id)

        for item in cohort:
            source_id = item["source_id"]
            passages: list[Any] = item.get("passages", [])
            terms: list[NativeTerm] = item.get("terms", [])
            definitions: list[DefinitionCandidate] = item.get("definitions", [])
            equations: list[EquationWitnessRecord] = item.get("equations", [])

            def_term_ids = {d.subject_term_id for d in definitions if d.subject_term_id}
            eq_passage_ids = {e.passage_id for e in equations}

            # -----------------------------------------------------------
            # 1. Bibliographic Reference Extraction & Resolution
            # -----------------------------------------------------------
            for p in passages:
                p_text = _passage_text(p)
                p_id = getattr(p, "id", None) or (p.get("id") if isinstance(p, dict) else "unknown")
                refs = extract_references_from_passage(p_text, source_id, p_id)
                if refs:
                    all_references.extend(refs)
                    summary.references_extracted += len(refs)

                    for ref in refs:
                        res = resolve_reference(ref, pool)
                        all_resolutions.append(res)
                        summary.resolutions_attempted += 1

                        # Create F0 Frontier Item for direct citation
                        dedup = make_dedup_key("F0_CITATION_DIRECT", ref.raw_reference[:120])
                        front_id = make_frontier_id(dedup)
                        f_item = FrontierItemRecord(
                            id=front_id,
                            frontier_type="F0_CITATION_DIRECT",
                            priority="P1",
                            dedup_key=dedup,
                            target_label=ref.raw_reference[:100],
                            normalized_target=ref.raw_reference.lower()[:120],
                            origin_source_id=source_id,
                            origin_passage_id=p_id,
                        )
                        ev = FrontierEvidenceRecord(
                            frontier_id=front_id,
                            evidence_type="CITATION",
                            evidence_id=ref.id,
                            source_id=source_id,
                            passage_id=p_id,
                            weight=res.confidence if res.confidence > 0 else 0.85,
                        )
                        self.db.upsert_frontier_item(f_item, [ev])
                        summary.frontier_items_created += 1
                        summary.frontier_evidence_recorded += 1

                        # If resolved or has identifier/URL, generate bounded nomination
                        nom_url = res.resolved_url or ref.identifier_raw
                        if nom_url and len(all_nominations) < max_nominations:
                            nom_id = make_nomination_id(front_id, nom_url)
                            nom = SourceNominationRecord(
                                id=nom_id,
                                frontier_id=front_id,
                                nominated_url=nom_url,
                                goal=f"Acquire resolved citation: {ref.title_raw or ref.raw_reference[:60]}",
                                priority="P1",
                                nomination_reason=f"Resolved with state={res.resolution_state}, confidence={res.confidence}",
                            )
                            all_nominations.append(nom)

            # -----------------------------------------------------------
            # 2. Historical Entity Mention Extraction & Routing
            # -----------------------------------------------------------
            for p in passages:
                p_text = _passage_text(p)
                p_id = getattr(p, "id", None) or (p.get("id") if isinstance(p, dict) else "unknown")
                mentions = extract_entity_mentions(p_text, source_id, p_id)
                if mentions:
                    all_mentions.extend(mentions)
                    summary.entity_mentions_extracted += len(mentions)

                    for m in mentions:
                        # STRICT ROUTING:
                        # Institutions must route to F2_INSTITUTION_VENUE, NEVER F3_NATIVE_TERMINOLOGY
                        if m.entity_type == "INSTITUTION":
                            f_type = "F2_INSTITUTION_VENUE"
                            prio = "P1"
                        elif m.entity_type == "PERSON":
                            f_type = "F1_AUTHOR_BIBLIOGRAPHY"
                            prio = "P1"
                        elif m.entity_type == "METHOD":
                            f_type = "F5_METHOD_OPERATOR"
                            prio = "P2"
                        else:
                            f_type = "F2_INSTITUTION_VENUE"
                            prio = "P3"

                        dedup = make_dedup_key(f_type, m.normalized_name)
                        front_id = make_frontier_id(dedup)
                        f_item = FrontierItemRecord(
                            id=front_id,
                            frontier_type=f_type,
                            priority=prio,
                            dedup_key=dedup,
                            target_label=m.surface_text,
                            normalized_target=m.normalized_name,
                            origin_source_id=source_id,
                            origin_passage_id=p_id,
                        )
                        ev = FrontierEvidenceRecord(
                            frontier_id=front_id,
                            evidence_type="ENTITY",
                            evidence_id=m.id,
                            source_id=source_id,
                            passage_id=p_id,
                            weight=m.confidence,
                        )
                        self.db.upsert_frontier_item(f_item, [ev])
                        summary.frontier_items_created += 1
                        summary.frontier_evidence_recorded += 1

            # -----------------------------------------------------------
            # 3. Native Terminology Frontier Scoring & Negative Controls
            # -----------------------------------------------------------
            for t in terms:
                # Institution routing safety: If term is an institution abbreviation, reject from term frontier
                if is_institution_entity(t.surface_form) or is_institution_entity(t.normalized_unicode):
                    continue

                indep_sources = len(term_source_map.get(t.normalized_unicode, {source_id}))
                in_def = t.id in def_term_ids
                near_eq = any(p.id in eq_passage_ids for p in passages)

                t_score = compute_terminology_frontier_score(
                    term=t.normalized_unicode,
                    independent_source_count=indep_sources,
                    occurs_in_definition=in_def,
                    near_equation=near_eq,
                    technicality_score=t.technicality_score,
                )

                if t_score.is_negative_control:
                    summary.negative_controls_rejected += 1
                    continue

                # Conservative threshold: F(t) >= 0.65
                if t_score.qualifies_for_frontier:
                    dedup = make_dedup_key("F3_NATIVE_TERMINOLOGY", t.normalized_unicode)
                    front_id = make_frontier_id(dedup)
                    f_item = FrontierItemRecord(
                        id=front_id,
                        frontier_type="F3_NATIVE_TERMINOLOGY",
                        priority="P2",
                        dedup_key=dedup,
                        target_label=t.surface_form,
                        normalized_target=t.normalized_unicode,
                        origin_source_id=source_id,
                        origin_passage_id=None,
                        raw_support_count=1,
                        independent_source_count=indep_sources,
                    )
                    ev = FrontierEvidenceRecord(
                        frontier_id=front_id,
                        evidence_type="TERM",
                        evidence_id=t.id,
                        source_id=source_id,
                        passage_id=None,
                        weight=t_score.score,
                    )
                    self.db.upsert_frontier_item(f_item, [ev])
                    summary.frontier_items_created += 1
                    summary.frontier_evidence_recorded += 1

        # -----------------------------------------------------------
        # 4. Save batches to database
        # -----------------------------------------------------------
        self.db.save_reference_candidates(all_references)
        for res in all_resolutions:
            self.db.save_reference_resolution(res)
        self.db.save_entity_mentions(all_mentions)
        self.db.save_source_nominations(all_nominations)
        summary.nominations_generated = len(all_nominations)

        return summary
