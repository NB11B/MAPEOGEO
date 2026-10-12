#!/usr/bin/env python3
"""
Developmental Transition & Transfer Engine.
Milestone SOVCTX-DEV2: Pedagogical Transition & Transfer Test.

Investigates three core developmental questions:
1. Agency Progression:
   Does a primitive move systematically along the trajectory:
       SUPPLIED -> HINTED -> INVENTED?
   Evaluates empirical transition curves across curricular stages for all active primitives.

2. Transfer Demand Progression:
   Does transfer demand increase systematically:
       SAME_FORM -> NEAR_TRANSFER -> FAR_TRANSFER?
   Computes coupling between transfer requirements and scaffolding depth (DIRECT -> PARTIAL -> NONE).

3. Noncommutative Operation Ordering & M6.2 Grammar Concordance:
   Do the operation-order patterns discovered in M6.2 appear in the educational sequence?
   Evaluates ordered primitive sequences (p_1 -> p_2 -> ... -> p_k) in dense episodes against the
   16x16 Methodological Grammar Matrix Gamma from M6.2, testing whether educational materials
   systematically teach the structure-preserving, mathematically optimal order first.
"""

from __future__ import annotations

import enum
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKTREE = Path(__file__).resolve().parents[2]
if str(WORKTREE) not in sys.path:
    sys.path.insert(0, str(WORKTREE))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sovctx.node.developmental_dense_extractor import DevelopmentalDenseExtractor
from sovctx.node.developmental_schema import (
    CorpusBatch,
    DevelopmentalEpisode,
    DevelopmentalStage,
    MoveOrigin,
    ScaffoldingDepth,
    SubstitutionMode,
    TransferRequirement,
)
from sovctx.node.methodological_grammar_engine import (
    GrammarLevel,
    GrammarOutcome,
    MethodologicalGrammarEngine,
)


@dataclass
class AgencyStageMetrics:
    stage_name: str
    sample_size: int
    supplied_count: int
    hinted_count: int
    invented_count: int
    pct_supplied: float
    pct_hinted: float
    pct_invented: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PrimitiveAgencyTrajectory:
    primitive_symbol: str
    total_occurrences: int
    stage_metrics: Dict[str, AgencyStageMetrics]
    is_monotonically_scaffold_stripping: bool  # P(invented) or P(hinted) increases over time
    invention_onset_stage: Optional[str]  # Earliest stage where invented > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "primitive_symbol": self.primitive_symbol,
            "total_occurrences": self.total_occurrences,
            "stage_metrics": {k: v.to_dict() for k, v in self.stage_metrics.items()},
            "is_monotonically_scaffold_stripping": self.is_monotonically_scaffold_stripping,
            "invention_onset_stage": self.invention_onset_stage,
        }


@dataclass
class TransferDemandReport:
    stage_name: str
    sample_size: int
    same_form_count: int
    near_transfer_count: int
    far_transfer_count: int
    pct_same_form: float
    pct_near_transfer: float
    pct_far_transfer: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ScaffoldingTransferCoupling:
    scaffolding_depth: str
    total_episodes: int
    same_form_count: int
    near_transfer_count: int
    far_transfer_count: int
    pct_same_form: float
    pct_near_transfer: float
    pct_far_transfer: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EducationalTransitionGrammarMatch:
    episode_id: str
    stage_name: str
    primitive_from: str
    primitive_to: str
    primitive_from_id: str
    primitive_to_id: str
    m6_2_gamma_level: int
    m6_2_outcome: str
    is_order_optimal_or_valid: bool
    is_structure_preserving: bool
    mathematical_rationale: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DevelopmentalTransitionSummary:
    total_episodes_analyzed: int
    active_primitives_count: int
    tracked_primitives: List[str]
    agency_trajectories: Dict[str, PrimitiveAgencyTrajectory]
    transfer_demand_by_stage: Dict[str, TransferDemandReport]
    scaffolding_transfer_coupling: Dict[str, ScaffoldingTransferCoupling]
    total_directed_transitions: int
    transitions_evaluated_against_m6_2: int
    gamma_level_counts: Dict[str, int]
    concordant_order_count: int
    grammar_concordance_rate: float
    structure_preserving_rate: float
    high_gamma_episodes_count: int  # Gamma >= 2
    high_gamma_concordance_rate: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_episodes_analyzed": self.total_episodes_analyzed,
            "active_primitives_count": self.active_primitives_count,
            "tracked_primitives": self.tracked_primitives,
            "agency_trajectories": {k: v.to_dict() for k, v in self.agency_trajectories.items()},
            "transfer_demand_by_stage": {k: v.to_dict() for k, v in self.transfer_demand_by_stage.items()},
            "scaffolding_transfer_coupling": {k: v.to_dict() for k, v in self.scaffolding_transfer_coupling.items()},
            "total_directed_transitions": self.total_directed_transitions,
            "transitions_evaluated_against_m6_2": self.transitions_evaluated_against_m6_2,
            "gamma_level_counts": self.gamma_level_counts,
            "concordant_order_count": self.concordant_order_count,
            "grammar_concordance_rate": round(self.grammar_concordance_rate, 4),
            "structure_preserving_rate": round(self.structure_preserving_rate, 4),
            "high_gamma_episodes_count": self.high_gamma_episodes_count,
            "high_gamma_concordance_rate": round(self.high_gamma_concordance_rate, 4),
        }


class DevelopmentalTransitionEngine:
    """
    Core engine for Milestone SOVCTX-DEV2.
    Evaluates agency progression, transfer demand curves, and noncommutative grammar alignment.
    """

    def __init__(self, dense_extractor: Optional[DevelopmentalDenseExtractor] = None) -> None:
        self.extractor = dense_extractor or DevelopmentalDenseExtractor()
        self.grammar_engine = MethodologicalGrammarEngine()
        self.grammar_engine.run_grammar_sweep()

        # Map primitive symbol to full ID in M6.2 basis
        self.symbol_to_id: Dict[str, str] = {
            p.get("symbol", p["id"]): p["id"] for p in self.grammar_engine.primitive_list
        }
        self.id_to_symbol: Dict[str, str] = {
            v: k for k, v in self.symbol_to_id.items()
        }

        # Defined Curricular Stages
        self.stages: Dict[str, Tuple[List[DevelopmentalStage], Optional[CorpusBatch], bool]] = {
            "STAGE_1_GRADE_1": (
                [DevelopmentalStage.GRADE_1_FIRST_DECADE, DevelopmentalStage.GRADE_1_SECOND_DECADE],
                CorpusBatch.BATCH_A_ORDINARY_PROGRESSION,
                False,  # Exclude teacher doctrine
            ),
            "STAGE_2_GRADES_2_4": (
                [
                    DevelopmentalStage.GRADE_2_HUNDRED,
                    DevelopmentalStage.GRADE_3_THOUSAND_FRACTIONS,
                    DevelopmentalStage.GRADE_4_MULTIDIGIT_PROPORTIONS,
                ],
                CorpusBatch.BATCH_A_ORDINARY_PROGRESSION,
                False,
            ),
            "STAGE_3_GRADES_6_8": (
                [
                    DevelopmentalStage.GRADE_6_7_PLANAR_GEOMETRY,
                    DevelopmentalStage.GRADE_6_7_ELEMENTARY_ALGEBRA,
                    DevelopmentalStage.GRADE_8_9_QUADRATICS_SYSTEMS,
                ],
                CorpusBatch.BATCH_A_ORDINARY_PROGRESSION,
                False,
            ),
            "STAGE_4_OLYMPIAD_CIRCLES": (
                [DevelopmentalStage.GRADE_8_9_QUADRATICS_SYSTEMS],
                CorpusBatch.BATCH_B_OLYMPIAD_ENRICHMENT,
                False,
            ),
            "TEACHER_DOCTRINE_TRACK": (
                [DevelopmentalStage.TEACHER_METHODOLOGY_DOCTRINE],
                CorpusBatch.BATCH_A_ORDINARY_PROGRESSION,
                True,  # Include only teacher doctrine
            ),
        }

    def run_transition_test(self) -> DevelopmentalTransitionSummary:
        """Executes full DEV2 transition and transfer investigation."""
        agency_trajectories = self._analyze_agency_trajectories()
        transfer_reports = self._analyze_transfer_demand()
        scaffolding_coupling = self._analyze_scaffolding_transfer_coupling()
        grammar_matches, grammar_summary = self._analyze_educational_grammar_concordance()

        active_prims = sorted(list(agency_trajectories.keys()))

        return DevelopmentalTransitionSummary(
            total_episodes_analyzed=len(self.extractor.episodes),
            active_primitives_count=len(active_prims),
            tracked_primitives=active_prims,
            agency_trajectories=agency_trajectories,
            transfer_demand_by_stage=transfer_reports,
            scaffolding_transfer_coupling=scaffolding_coupling,
            total_directed_transitions=grammar_summary["total_directed_transitions"],
            transitions_evaluated_against_m6_2=grammar_summary["transitions_evaluated"],
            gamma_level_counts=grammar_summary["gamma_level_counts"],
            concordant_order_count=grammar_summary["concordant_order_count"],
            grammar_concordance_rate=grammar_summary["grammar_concordance_rate"],
            structure_preserving_rate=grammar_summary["structure_preserving_rate"],
            high_gamma_episodes_count=grammar_summary["high_gamma_count"],
            high_gamma_concordance_rate=grammar_summary["high_gamma_concordance_rate"],
        )

    # -------------------------------------------------------------------------
    # Core Question 1: Agency Progression Analysis
    # -------------------------------------------------------------------------
    def _analyze_agency_trajectories(self) -> Dict[str, PrimitiveAgencyTrajectory]:
        """Tracks Supplied -> Hinted -> Invented across all active primitives."""
        all_symbols: Set[str] = set()
        for m in self.extractor.primitive_mappings.values():
            all_symbols.update(m.primitive_symbols)

        trajectories: Dict[str, PrimitiveAgencyTrajectory] = {}

        for sym in sorted(list(all_symbols)):
            stage_metrics: Dict[str, AgencyStageMetrics] = {}
            total_occs = 0
            onset_stage: Optional[str] = None

            for stage_name, (stages_list, batch_filter, is_doctrine_only) in self.stages.items():
                matching_eps: List[DevelopmentalEpisode] = []
                for ep_id, ep in self.extractor.episodes.items():
                    m = self.extractor.primitive_mappings[ep_id]
                    if sym not in m.primitive_symbols:
                        continue
                    if ep.is_teacher_doctrine != is_doctrine_only:
                        continue
                    if batch_filter is not None and ep.corpus_batch != batch_filter:
                        continue
                    if ep.grade_stage in stages_list:
                        matching_eps.append(ep)

                n_match = len(matching_eps)
                total_occs += n_match
                if n_match == 0:
                    stage_metrics[stage_name] = AgencyStageMetrics(
                        stage_name=stage_name,
                        sample_size=0,
                        supplied_count=0,
                        hinted_count=0,
                        invented_count=0,
                        pct_supplied=0.0,
                        pct_hinted=0.0,
                        pct_invented=0.0,
                    )
                    continue

                sup = sum(1 for e in matching_eps if e.move_origin == MoveOrigin.SUPPLIED)
                hnt = sum(1 for e in matching_eps if e.move_origin == MoveOrigin.HINTED)
                inv = sum(1 for e in matching_eps if e.move_origin == MoveOrigin.STUDENT_EXPECTED_TO_INVENT)

                if inv > 0 and onset_stage is None and not is_doctrine_only:
                    onset_stage = stage_name

                stage_metrics[stage_name] = AgencyStageMetrics(
                    stage_name=stage_name,
                    sample_size=n_match,
                    supplied_count=sup,
                    hinted_count=hnt,
                    invented_count=inv,
                    pct_supplied=round(sup / n_match, 4),
                    pct_hinted=round(hnt / n_match, 4),
                    pct_invented=round(inv / n_match, 4),
                )

            s4 = stage_metrics.get("STAGE_4_OLYMPIAD_CIRCLES")
            is_monotone = True
            if s4 and s4.sample_size > 0:
                school_max_inv = max(
                    stage_metrics["STAGE_1_GRADE_1"].pct_invented,
                    stage_metrics["STAGE_2_GRADES_2_4"].pct_invented,
                    stage_metrics["STAGE_3_GRADES_6_8"].pct_invented,
                )
                if s4.pct_invented < school_max_inv:
                    is_monotone = False

            trajectories[sym] = PrimitiveAgencyTrajectory(
                primitive_symbol=sym,
                total_occurrences=total_occs,
                stage_metrics=stage_metrics,
                is_monotonically_scaffold_stripping=is_monotone,
                invention_onset_stage=onset_stage,
            )

        return trajectories

    # -------------------------------------------------------------------------
    # Core Question 2: Transfer Demand Progression Analysis
    # -------------------------------------------------------------------------
    def _analyze_transfer_demand(self) -> Dict[str, TransferDemandReport]:
        """Tracks Same_Form -> Near_Transfer -> Far_Transfer across stages."""
        reports: Dict[str, TransferDemandReport] = {}

        for stage_name, (stages_list, batch_filter, is_doctrine_only) in self.stages.items():
            eps = [
                ep for ep in self.extractor.episodes.values()
                if ep.is_teacher_doctrine == is_doctrine_only
                and (batch_filter is None or ep.corpus_batch == batch_filter)
                and ep.grade_stage in stages_list
            ]
            n = len(eps)
            if n == 0:
                reports[stage_name] = TransferDemandReport(
                    stage_name=stage_name,
                    sample_size=0,
                    same_form_count=0,
                    near_transfer_count=0,
                    far_transfer_count=0,
                    pct_same_form=0.0,
                    pct_near_transfer=0.0,
                    pct_far_transfer=0.0,
                )
                continue

            sf = sum(1 for e in eps if e.transfer_requirement == TransferRequirement.SAME_FORM)
            nt = sum(1 for e in eps if e.transfer_requirement == TransferRequirement.NEAR_TRANSFER)
            ft = sum(1 for e in eps if e.transfer_requirement == TransferRequirement.FAR_TRANSFER)

            reports[stage_name] = TransferDemandReport(
                stage_name=stage_name,
                sample_size=n,
                same_form_count=sf,
                near_transfer_count=nt,
                far_transfer_count=ft,
                pct_same_form=round(sf / n, 4),
                pct_near_transfer=round(nt / n, 4),
                pct_far_transfer=round(ft / n, 4),
            )

        return reports

    def _analyze_scaffolding_transfer_coupling(self) -> Dict[str, ScaffoldingTransferCoupling]:
        """Couples ScaffoldingDepth (DIRECT, PARTIAL, NONE) with TransferRequirement."""
        coupling: Dict[str, ScaffoldingTransferCoupling] = {}

        for depth in ScaffoldingDepth:
            eps = [e for e in self.extractor.episodes.values() if e.scaffolding_depth == depth]
            n = len(eps)
            if n == 0:
                continue

            sf = sum(1 for e in eps if e.transfer_requirement == TransferRequirement.SAME_FORM)
            nt = sum(1 for e in eps if e.transfer_requirement == TransferRequirement.NEAR_TRANSFER)
            ft = sum(1 for e in eps if e.transfer_requirement == TransferRequirement.FAR_TRANSFER)

            coupling[depth.value] = ScaffoldingTransferCoupling(
                scaffolding_depth=depth.value,
                total_episodes=n,
                same_form_count=sf,
                near_transfer_count=nt,
                far_transfer_count=ft,
                pct_same_form=round(sf / n, 4),
                pct_near_transfer=round(nt / n, 4),
                pct_far_transfer=round(ft / n, 4),
            )

        return coupling

    # -------------------------------------------------------------------------
    # Core Question 3: Noncommutative Grammar & Operation Ordering Alignment
    # -------------------------------------------------------------------------
    def _analyze_educational_grammar_concordance(
        self,
    ) -> Tuple[List[EducationalTransitionGrammarMatch], Dict[str, Any]]:
        """
        Extracts directed sequential pairs (p_a -> p_b) from every episode and
        evaluates their alignment with the M6.2 Noncommutative Methodological Grammar Matrix.
        """
        matches: List[EducationalTransitionGrammarMatch] = []
        gamma_counts: Counter[str] = Counter()
        total_transitions = 0
        concordant_transitions = 0
        structure_preserving_transitions = 0
        high_gamma_count = 0
        high_gamma_concordant = 0

        for ep_id, ep in self.extractor.episodes.items():
            m = self.extractor.primitive_mappings.get(ep_id)
            if not m or len(m.primitive_symbols) < 2:
                continue

            syms = m.primitive_symbols
            stage_str = ep.grade_stage.value

            for idx in range(len(syms) - 1):
                p_from = syms[idx]
                p_to = syms[idx + 1]
                total_transitions += 1

                id_from = self.symbol_to_id.get(p_from)
                id_to = self.symbol_to_id.get(p_to)

                if not id_from or not id_to:
                    continue

                lvl = self.grammar_engine.gamma_matrix.get((id_from, id_to), 0)
                gamma_code = f"G{lvl}" if lvl >= 0 else "INVALID"
                gamma_counts[gamma_code] += 1

                pair_eval = next(
                    (e for e in self.grammar_engine.pair_evaluations
                     if e.primitive_i_id == id_from and e.primitive_j_id == id_to),
                    None
                )

                is_valid_order = True
                is_struct_preserving = True
                rationale = "Commutative or representational pair"

                if pair_eval:
                    rationale = pair_eval.mathematical_rationale
                    if pair_eval.grammar_level == -1:
                        is_valid_order = False
                        is_struct_preserving = False
                    elif pair_eval.grammar_level == 0:
                        is_valid_order = True
                        is_struct_preserving = True
                    elif pair_eval.grammar_level == 1:
                        is_valid_order = True
                        is_struct_preserving = True
                    elif pair_eval.grammar_level >= 2:
                        high_gamma_count += 1
                        if ("ADMISSIBILITY" in id_from and "EXTREMAL" in id_to):
                            is_struct_preserving = True
                        elif ("EXTREMAL" in id_from and "ADMISSIBILITY" in id_to):
                            is_struct_preserving = False
                        elif ("NEGATIVE_INFORMATION" in id_from and "INVERSE" in id_to):
                            is_struct_preserving = True
                        elif ("INVERSE" in id_from and "NEGATIVE_INFORMATION" in id_to):
                            is_struct_preserving = False
                        elif ("INVARIANT" in id_from and "STATE_REDUCTION" in id_to):
                            is_struct_preserving = True
                        elif ("STATE_REDUCTION" in id_from and "INVARIANT" in id_to):
                            is_struct_preserving = True
                        elif ("STATE_AUGMENTATION" in id_from and "CONTROL" in id_to):
                            is_struct_preserving = True
                        elif ("CONTROL" in id_from and "STATE_AUGMENTATION" in id_to):
                            is_struct_preserving = False
                        else:
                            is_struct_preserving = pair_eval.order_ij_valid

                        if is_struct_preserving:
                            high_gamma_concordant += 1

                if is_valid_order:
                    concordant_transitions += 1
                if is_struct_preserving:
                    structure_preserving_transitions += 1

                matches.append(
                    EducationalTransitionGrammarMatch(
                        episode_id=ep_id,
                        stage_name=stage_str,
                        primitive_from=p_from,
                        primitive_to=p_to,
                        primitive_from_id=id_from,
                        primitive_to_id=id_to,
                        m6_2_gamma_level=lvl,
                        m6_2_outcome=pair_eval.outcome.value if pair_eval else "UNKNOWN",
                        is_order_optimal_or_valid=is_valid_order,
                        is_structure_preserving=is_struct_preserving,
                        mathematical_rationale=rationale,
                    )
                )

        concordance_rate = (concordant_transitions / total_transitions) if total_transitions > 0 else 0.0
        struct_rate = (structure_preserving_transitions / total_transitions) if total_transitions > 0 else 0.0
        high_gamma_rate = (high_gamma_concordant / high_gamma_count) if high_gamma_count > 0 else 0.0

        summary = {
            "total_directed_transitions": total_transitions,
            "transitions_evaluated": len(matches),
            "gamma_level_counts": dict(gamma_counts),
            "concordant_order_count": concordant_transitions,
            "grammar_concordance_rate": concordance_rate,
            "structure_preserving_rate": struct_rate,
            "high_gamma_count": high_gamma_count,
            "high_gamma_concordance_rate": high_gamma_rate,
        }

        return matches, summary


def main() -> None:
    engine = DevelopmentalTransitionEngine()
    summary = engine.run_transition_test()

    print("=" * 80)
    print("SOVCTX-DEV2: PEDAGOGICAL TRANSITION & TRANSFER TEST")
    print("=" * 80)
    print(f"Total Episodes Analyzed: {summary.total_episodes_analyzed}")
    print(f"Active Primitives Tracked: {summary.active_primitives_count} ({', '.join(summary.tracked_primitives)})")
    print("\n1. TRANSFER DEMAND PROGRESSION ACROSS STAGES:")
    for stage, rep in summary.transfer_demand_by_stage.items():
        print(f"  {stage:30s}: n={rep.sample_size:2d} | SAME_FORM={rep.pct_same_form:.1%} | NEAR={rep.pct_near_transfer:.1%} | FAR={rep.pct_far_transfer:.1%}")

    print("\n2. SCAFFOLDING DEPTH & TRANSFER COUPLING:")
    for scaff, coup in summary.scaffolding_transfer_coupling.items():
        print(f"  {scaff:15s}: n={coup.total_episodes:2d} | SAME_FORM={coup.pct_same_form:.1%} | NEAR={coup.pct_near_transfer:.1%} | FAR={coup.pct_far_transfer:.1%}")

    print("\n3. M6.2 NONCOMMUTATIVE GRAMMAR CONCORDANCE:")
    print(f"  Total Directed Sequential Transitions: {summary.total_directed_transitions}")
    print(f"  Gamma Level Counts: {summary.gamma_level_counts}")
    print(f"  Grammar Concordance Rate: {summary.grammar_concordance_rate:.1%}")
    print(f"  Structure-Preserving Rate: {summary.structure_preserving_rate:.1%}")
    print(f"  High-Gamma (Gamma >= 2) Transitions: {summary.high_gamma_episodes_count} (Concordance: {summary.high_gamma_concordance_rate:.1%})")
    print("=" * 80)


if __name__ == "__main__":
    main()
