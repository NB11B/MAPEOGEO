from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from .config import NanoConfig
from .equation_witness import EquationWitnessRecord, extract_equation_witnesses_from_passage
from .morphology import (
    analyze_russian_word,
    detect_historical_orthography,
    make_lemma_id,
    modern_spelling_from_historical,
)
from .notation import SymbolOccurrence, extract_symbol_occurrences
from .passages import PassageRecord
from .term_occurrence import extract_occurrences_from_passage, split_sentences
from .terminology import (
    DEFINITION_TRIGGERS,
    DefinitionCandidate,
    NativeTerm,
    TermOccurrence,
    TermRelation,
    make_definition_id,
    make_term_id,
)
from .work_db import WorkDatabase


@dataclass
class TerminologyExtractionResult:
    source_id: str
    passages_processed: int
    terms: list[NativeTerm] = field(default_factory=list)
    occurrences: list[TermOccurrence] = field(default_factory=list)
    relations: list[TermRelation] = field(default_factory=list)
    definitions: list[DefinitionCandidate] = field(default_factory=list)
    symbols: list[SymbolOccurrence] = field(default_factory=list)
    equation_witnesses: list[EquationWitnessRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "passages_processed": self.passages_processed,
            "term_count": len(self.terms),
            "occurrence_count": len(self.occurrences),
            "relation_count": len(self.relations),
            "definition_count": len(self.definitions),
            "symbol_count": len(self.symbols),
            "equation_witness_count": len(self.equation_witnesses),
        }


class TerminologyExtractor:
    """Deterministic Native Terminology, Symbol Witness, and Definition Extractor (Gate N1.5)."""

    def __init__(self, config: NanoConfig, db: Optional[WorkDatabase] = None) -> None:
        self.config = config
        self.db = db or WorkDatabase(config.work_db_path, config.sqlite)

    def process_passage(self, passage: PassageRecord) -> TerminologyExtractionResult:
        """Process a single passage record and return extracted terminology evidence."""
        return self.process_passages([passage], source_id=passage.source_id)

    def process_passages(
        self,
        passages: list[PassageRecord],
        source_id: str,
        persist: bool = True,
    ) -> TerminologyExtractionResult:
        """Process a batch of passage records from a source and extract terminological evidence."""
        all_terms_map: dict[str, NativeTerm] = {}
        all_occurrences: list[TermOccurrence] = []
        all_relations: list[TermRelation] = []
        all_definitions: list[DefinitionCandidate] = []
        all_symbols: list[SymbolOccurrence] = []
        all_equations: list[EquationWitnessRecord] = []

        for p in passages:
            text = p.text_source
            p_terms, p_occs, p_contains = extract_occurrences_from_passage(
                passage_id=p.id,
                source_id=source_id,
                text=text,
            )

            for t in p_terms:
                if t.id not in all_terms_map:
                    all_terms_map[t.id] = t
            all_occurrences.extend(p_occs)

            # CONTAINS_TERM relations for multiword phrases
            for parent_id, child_id, phrase_str in p_contains:
                rel_id = hashlib.sha256(f"{parent_id}\0CONTAINS_TERM\0{child_id}".encode("utf-8")).hexdigest()[:20]
                all_relations.append(
                    TermRelation(
                        id=f"SOVTREL:{rel_id}",
                        from_term_id=parent_id,
                        to_term_id=child_id,
                        relation_type="CONTAINS_TERM",
                        method="phrase_decomposition",
                        confidence=1.0,
                        details={"phrase": phrase_str},
                    )
                )

            # Definition candidates detection
            sentences = split_sentences(text)
            for s_start, s_end, s_text in sentences:
                for pattern, trigger_name, trig_conf in DEFINITION_TRIGGERS:
                    match = pattern.search(s_text)
                    if match:
                        def_id = make_definition_id(p.id, s_start, s_end, trigger_name)
                        # Find nearest term before trigger in the same sentence as subject
                        trig_offset = s_start + match.start()
                        candidate_subjects = [
                            occ for occ in p_occs
                            if s_start <= occ.char_start < trig_offset
                        ]
                        subject_term_id = candidate_subjects[-1].term_id if candidate_subjects else None

                        all_definitions.append(
                            DefinitionCandidate(
                                id=def_id,
                                passage_id=p.id,
                                source_id=source_id,
                                subject_term_id=subject_term_id,
                                trigger=trigger_name,
                                defining_span=s_text.strip(),
                                confidence=trig_conf,
                            )
                        )
                        break  # Match at most one primary definition trigger per sentence

            # Symbols
            p_symbols = extract_symbol_occurrences(
                text=text,
                source_id=source_id,
                passage_id=p.id,
            )
            all_symbols.extend(p_symbols)

            # Equation witnesses
            p_equations = extract_equation_witnesses_from_passage(
                text=text,
                source_id=source_id,
                passage_id=p.id,
                page_physical=p.page_physical,
                extraction_method=p.extraction_method,
            )
            # Bind neighboring terms in the same passage to equations
            term_surfaces = [t.surface_form for t in p_terms[:10]]
            for eq in p_equations:
                eq.neighboring_terms = term_surfaces
            all_equations.extend(p_equations)

        # Morphological relations on unique terms
        for t_id, t in list(all_terms_map.items()):
            if t.language == "ru":
                # Check for historical orthography
                if detect_historical_orthography(t.surface_form):
                    mod_spelling = modern_spelling_from_historical(t.surface_form)
                    mod_id = make_term_id(mod_spelling, "ru")
                    if mod_id not in all_terms_map:
                        all_terms_map[mod_id] = NativeTerm(
                            id=mod_id,
                            surface_form=mod_spelling,
                            normalized_unicode=mod_spelling,
                            language="ru",
                            script="Cyrillic",
                            term_type=t.term_type,
                            technicality_score=t.technicality_score,
                            signals=t.signals + ["derived_modern_spelling"],
                        )
                    rel_id = hashlib.sha256(f"{t_id}\0HISTORICAL_SPELLING_OF\0{mod_id}".encode("utf-8")).hexdigest()[:20]
                    all_relations.append(
                        TermRelation(
                            id=f"SOVTREL:{rel_id}",
                            from_term_id=t_id,
                            to_term_id=mod_id,
                            relation_type="HISTORICAL_SPELLING_OF",
                            method="pre_1918_orthography_rules",
                            confidence=0.95,
                            details={"historical_form": t.surface_form, "modern_form": mod_spelling},
                        )
                    )

                # Lemmatization candidate
                if t.term_type == "single_token":
                    morph = analyze_russian_word(t.surface_form)
                    if morph.lemma_candidate and morph.lemma_candidate != t.surface_form.lower():
                        lemma_id = make_lemma_id(morph.lemma_candidate, "ru")
                        rel_id = hashlib.sha256(f"{t_id}\0LEMMATIZED_AS\0{lemma_id}".encode("utf-8")).hexdigest()[:20]
                        all_relations.append(
                            TermRelation(
                                id=f"SOVTREL:{rel_id}",
                                from_term_id=t_id,
                                to_term_id=lemma_id,
                                relation_type="LEMMATIZED_AS",
                                method="rule_heuristic_v0.1",
                                confidence=morph.lemma_confidence,
                                details={
                                    "lemma": morph.lemma_candidate,
                                    "features": morph.grammatical_features,
                                },
                            )
                        )

        # Persist to database if requested
        if persist and self.db is not None:
            self.db.insert_candidate_terms_batch(
                terms=list(all_terms_map.values()),
                occurrences=all_occurrences,
                relations=all_relations,
                definitions=all_definitions,
                symbols=all_symbols,
                equations=all_equations,
            )

        return TerminologyExtractionResult(
            source_id=source_id,
            passages_processed=len(passages),
            terms=list(all_terms_map.values()),
            occurrences=all_occurrences,
            relations=all_relations,
            definitions=all_definitions,
            symbols=all_symbols,
            equation_witnesses=all_equations,
        )
