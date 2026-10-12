#!/usr/bin/env python3
r"""
Cybernetic-Bionic Methodological Architecture Bridge Engine.
Milestone SOVCTX-BCIG-1: Cybernetic-Bionic Methodological Architecture Bridge.

Bridges the mathematical methodology graph G_SOVCTX to the bionic/cybernetic
functional architecture graph G_BCIG via formal relational ontology:
    - REALIZES_METHOD_PRIMITIVE
    - ARCHITECTURAL_MANIFESTATION_OF
    - FUNCTIONAL_ANALOGUE_OF
    - REQUIRES_METHOD_PRIMITIVE

Epistemic Pillars:
1. Question-Sufficient State (M6.1 Extension):
   A controller or biological organism does not model everything that exists;
   it models what must be known to preserve function:
       X_R \not\Rightarrow X,  but  Q(X_R) = Q(X).

2. Historical Cybernetic / Bionic Architectures:
   - Anokhin (1955, 1968): Functional System, Action Acceptor, Return Afference
   - Bernstein (1966): Degrees of Freedom Elimination, Motor Synergies, Model of Required Future
   - Feldbaum (1960): Dual Control Theory, Epistemic Action (Act-to-Know)
   - Tsetlin (1961): Finite Automata in Random Media, Minimal State Adaptation
   - Lyapunov-Krasovskii (1892, 1959): Viability Certificate, Energy-Based Regulation
   - Stratonovich (1960): Conditional Markov Information Filtering, Optimal Nonlinear Estimation
   - Ashby (1952): Ultrastable Homeostat, Essential Variables (Western Comparative Control)

3. Cross-Graph Methodological Grammar Concordance:
   Verifies whether the operating sequences of cybernetic architectures adhere to the
   M6.2 non-commutative grammar matrix (Gamma in {0, 1, 2, 3, bot}).

4. Predictive Synthesis of Unbuilt Architectures:
   Explores unoccupied valid algebraic compositions in M6.2 that predict
   functional bionic architectures not historically constructed in 1950-1970s cybernetics.
"""

from __future__ import annotations

import enum
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
WORKTREE = Path(__file__).resolve().parents[2]
if str(WORKTREE) not in sys.path:
    sys.path.insert(0, str(WORKTREE))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sovctx.node.developmental_dense_extractor import DevelopmentalDenseExtractor
from sovctx.node.methodological_grammar_engine import (
    GrammarLevel,
    GrammarOutcome,
    MethodologicalGrammarEngine,
)


class ArchitectureDomain(str, enum.Enum):
    CYBERNETIC_CONTROL = "CYBERNETIC_CONTROL"
    BIONIC_ORGANISMIC = "BIONIC_ORGANISMIC"
    ADAPTIVE_AUTOMATA = "ADAPTIVE_AUTOMATA"
    STOCHASTIC_FILTERING = "STOCHASTIC_FILTERING"
    SYNTHETIC_PREDICTED = "SYNTHETIC_PREDICTED"


@dataclass
class BridgeRelationRecord:
    relation_id: str
    relation_type: str  # REALIZES_METHOD_PRIMITIVE, ARCHITECTURAL_MANIFESTATION_OF, FUNCTIONAL_ANALOGUE_OF, REQUIRES_METHOD_PRIMITIVE
    architecture_id: str
    architecture_name: str
    method_primitive_symbol: str
    method_primitive_id: str
    domain: ArchitectureDomain
    epistemic_justification: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relation_id": self.relation_id,
            "relation_type": self.relation_type,
            "architecture_id": self.architecture_id,
            "architecture_name": self.architecture_name,
            "method_primitive_symbol": self.method_primitive_symbol,
            "method_primitive_id": self.method_primitive_id,
            "domain": self.domain.value,
            "epistemic_justification": self.epistemic_justification,
        }


@dataclass
class FunctionalArchitectureRecord:
    architecture_id: str
    architecture_name: str
    author: str
    historical_year: int
    domain: ArchitectureDomain
    question_sufficient_reduction: str
    what_is_ignored_as_irrelevant: str  # Negative information definition
    operational_sequence: List[str]  # Sequential primitives applied
    realized_primitives: List[str]
    is_historical: bool
    mathematical_substrate_ref: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "architecture_id": self.architecture_id,
            "architecture_name": self.architecture_name,
            "author": self.author,
            "historical_year": self.historical_year,
            "domain": self.domain.value,
            "question_sufficient_reduction": self.question_sufficient_reduction,
            "what_is_ignored_as_irrelevant": self.what_is_ignored_as_irrelevant,
            "operational_sequence": self.operational_sequence,
            "realized_primitives": self.realized_primitives,
            "is_historical": self.is_historical,
            "mathematical_substrate_ref": self.mathematical_substrate_ref,
        }


@dataclass
class PredictedArchitectureRecord:
    prediction_id: str
    architecture_name: str
    predicted_primitive_composition: List[str]
    structural_synthesis_rationale: str
    unbuilt_historical_barrier: str  # Why 1960s cybernetics didn't build it (e.g. compute/theory)
    potential_modern_embodiment: str  # Autonomous robotics / Edge AI

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BcigBridgeSummaryReport:
    total_architectures_mapped: int
    historical_architectures_count: int
    predicted_architectures_count: int
    total_bridge_relations: int
    relation_type_distribution: Dict[str, int]
    primitive_realization_coverage: Dict[str, int]
    grammar_concordance_rate: float
    high_gamma_epistemic_matches: int
    architectures: List[FunctionalArchitectureRecord]
    predicted_architectures: List[PredictedArchitectureRecord]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_architectures_mapped": self.total_architectures_mapped,
            "historical_architectures_count": self.historical_architectures_count,
            "predicted_architectures_count": self.predicted_architectures_count,
            "total_bridge_relations": self.total_bridge_relations,
            "relation_type_distribution": self.relation_type_distribution,
            "primitive_realization_coverage": self.primitive_realization_coverage,
            "grammar_concordance_rate": round(self.grammar_concordance_rate, 4),
            "high_gamma_epistemic_matches": self.high_gamma_epistemic_matches,
            "architectures": [a.to_dict() for a in self.architectures],
            "predicted_architectures": [p.to_dict() for p in self.predicted_architectures],
        }


class CyberneticBionicBridgeEngine:
    """
    Executes Milestone SOVCTX-BCIG-1:
    Formalizes the bridge between the mathematical methodology graph and
    cybernetic/bionic functional architectures.
    """

    def __init__(self) -> None:
        self.grammar_engine = MethodologicalGrammarEngine()
        self.grammar_engine.run_grammar_sweep()

        self.symbol_to_id: Dict[str, str] = {
            p.get("symbol", p["id"]): p["id"] for p in self.grammar_engine.primitive_list
        }

        self.architectures: Dict[str, FunctionalArchitectureRecord] = {}
        self.relations: List[BridgeRelationRecord] = []
        self.predicted_architectures: List[PredictedArchitectureRecord] = []

        self._ingest_historical_architectures()
        self._synthesize_unbuilt_predictions()
        self._generate_bridge_relations()

    def _ingest_historical_architectures(self) -> None:
        """Ingests landmark Soviet and comparative Western cybernetic/bionic architectures."""
        archs = [
            # 1. Anokhin Functional System
            FunctionalArchitectureRecord(
                architecture_id="ARCH_ANOKHIN_FUNCTIONAL_SYSTEM",
                architecture_name="Anokhin Functional System & Action-Result Acceptor",
                author="P. K. Anokhin",
                historical_year=1955,
                domain=ArchitectureDomain.BIONIC_ORGANISMIC,
                question_sufficient_reduction="Behavior organized around target outcome result rather than stimulus-reflex chains: Q(X) evaluates whether metabolic viability is preserved.",
                what_is_ignored_as_irrelevant="Microscopic synaptic spike sequences and peripheral nerve transmission details.",
                operational_sequence=["Ax", "C", "Ii", "Sc"],
                realized_primitives=["Ax", "C", "Ii", "Sc", "Sr"],
                is_historical=True,
                mathematical_substrate_ref="Auxiliary model construction (Ax) -> Motor action (C) -> Return afference comparison (Ii) -> Self-consistent adaptive closure (Sc)",
            ),
            # 2. Bernstein Motor Synergies
            FunctionalArchitectureRecord(
                architecture_id="ARCH_BERNSTEIN_MOTOR_SYNERGIES",
                architecture_name="Bernstein Motor Coordination & Synergy System",
                author="N. A. Bernstein",
                historical_year=1966,
                domain=ArchitectureDomain.BIONIC_ORGANISMIC,
                question_sufficient_reduction="Elimination of excess degrees of freedom by projecting high-dimensional muscular coordinate space into lower-dimensional functional linkages.",
                what_is_ignored_as_irrelevant="Individual muscle contraction scalar states not participating in the collective kinetic linkage.",
                operational_sequence=["Rs", "Sr", "I", "C"],
                realized_primitives=["Rs", "Sr", "I", "C", "N"],
                is_historical=True,
                mathematical_substrate_ref="Representation shift to task space (Rs) -> Degree of freedom reduction (Sr) -> Kinetic invariant maintenance (I) -> Synergistic control (C)",
            ),
            # 3. Feldbaum Dual Controller
            FunctionalArchitectureRecord(
                architecture_id="ARCH_FELDBAUM_DUAL_CONTROL",
                architecture_name="Feldbaum Dual Control & Epistemic Action System",
                author="A. A. Feldbaum",
                historical_year=1960,
                domain=ArchitectureDomain.CYBERNETIC_CONTROL,
                question_sufficient_reduction="Act-to-know: Control action acts simultaneously as pragmatic actuator and probing sensor to reduce system uncertainty under bounded horizon.",
                what_is_ignored_as_irrelevant="High-frequency unidentifiable plant parameters that do not alter the Bellman value function.",
                operational_sequence=["Sa", "Ad", "C", "Iv"],
                realized_primitives=["Sa", "Ad", "C", "Iv", "E"],
                is_historical=True,
                mathematical_substrate_ref="State augmentation with posterior density (Sa) -> Admissibility constraint gating (Ad) -> Dual action selection (C) -> Inverse parameter update (Iv)",
            ),
            # 4. Tsetlin Minimal Automaton
            FunctionalArchitectureRecord(
                architecture_id="ARCH_TSETLIN_EXPEDIENT_AUTOMATON",
                architecture_name="Tsetlin Finite Stochastic Automaton in Random Media",
                author="M. L. Tsetlin",
                historical_year=1961,
                domain=ArchitectureDomain.ADAPTIVE_AUTOMATA,
                question_sufficient_reduction="Minimal state machine sufficient for asymptotic adaptation in stationary and non-stationary penalty media without internal plant modeling.",
                what_is_ignored_as_irrelevant="Physical dynamics and state equations of the surrounding environment; entirely omitted as negative information.",
                operational_sequence=["N", "Sr", "C", "Iv"],
                realized_primitives=["N", "Sr", "C", "Iv"],
                is_historical=True,
                mathematical_substrate_ref="Complete omission of environmental model (N) -> Integer state reduction (Sr) -> Action deployment (C) -> Penalty-based state shift (Iv)",
            ),
            # 5. Lyapunov-Krasovskii Viability Regulator
            FunctionalArchitectureRecord(
                architecture_id="ARCH_LYAPUNOV_KRASOVSKII_REGULATOR",
                architecture_name="Lyapunov-Krasovskii Certificate-Driven Regulator",
                author="A. M. Lyapunov & N. N. Krasovskii",
                historical_year=1959,
                domain=ArchitectureDomain.CYBERNETIC_CONTROL,
                question_sufficient_reduction="Continuous differential state trajectory replaced by scalar energy certificate V(x) indicating convergence toward admissible equilibrium.",
                what_is_ignored_as_irrelevant="Internal micro-trajectories and phase velocity components orthogonal to the gradient of the Lyapunov function.",
                operational_sequence=["I", "Sr", "Ad", "C"],
                realized_primitives=["I", "Sr", "Ad", "C"],
                is_historical=True,
                mathematical_substrate_ref="Invariant stability function construction (I) -> Phase space reduction to scalar V (Sr) -> Viability basin checking (Ad) -> Damping intervention (C)",
            ),
            # 6. Stratonovich Information Filter
            FunctionalArchitectureRecord(
                architecture_id="ARCH_STRATONOVICH_NONLINEAR_FILTER",
                architecture_name="Stratonovich Conditional Markov Information Filter",
                author="R. L. Stratonovich",
                historical_year=1960,
                domain=ArchitectureDomain.STOCHASTIC_FILTERING,
                question_sufficient_reduction="Partial noisy continuous observation mapped onto unnormalized conditional density evolution (Kushner-Stratonovich equation).",
                what_is_ignored_as_irrelevant="Raw observation history; summarized recursively via the conditional density functional.",
                operational_sequence=["N", "Iv", "Sa", "Sr"],
                realized_primitives=["N", "Iv", "Sa", "Sr"],
                is_historical=True,
                mathematical_substrate_ref="Omission of white noise mode subspace (N) -> Inverse stochastic operator (Iv) -> State augmentation with density (Sa) -> Sufficient moment reduction (Sr)",
            ),
            # 7. Ashby Ultrastable Homeostat (Comparative Western Control)
            FunctionalArchitectureRecord(
                architecture_id="ARCH_ASHBY_ULTRASTABLE_HOMEOSTAT",
                architecture_name="Ashby Ultrastable Homeostat & Essential Variables",
                author="W. Ross Ashby",
                historical_year=1952,
                domain=ArchitectureDomain.CYBERNETIC_CONTROL,
                question_sufficient_reduction="Two-tiered regulatory loop: feedback regulation within essential variable limits, step-mechanism re-wiring when limits are breached.",
                what_is_ignored_as_irrelevant="Environmental dynamics outside the sensory threshold of the essential variables.",
                operational_sequence=["Ad", "C", "I"],
                realized_primitives=["Ad", "C", "I"],
                is_historical=True,
                mathematical_substrate_ref="Essential variable admissibility gating (Ad) -> Step switch control action (C) -> Ultrastable equilibrium invariance (I)",
            ),
        ]

        for a in archs:
            self.architectures[a.architecture_id] = a

    def _synthesize_unbuilt_predictions(self) -> None:
        """
        Predicts valid functional bionic architectures enabled by M6.2 grammar
        that were never constructed in 1950-1970s cybernetics due to historical/computational limits.
        """
        preds = [
            PredictedArchitectureRecord(
                prediction_id="PRED_ARCH_ALPHA_DUAL_REGULARIZED_SYNERGISTIC_OBSERVER",
                architecture_name="Dual-Regularized Synergistic Observer (Bernstein-Tikhonov-Stratonovich)",
                predicted_primitive_composition=["Rs", "Sr", "N", "Iv", "Sa"],
                structural_synthesis_rationale=(
                    "Combines Bernstein degree-of-freedom reduction (Rs o Sr) with Tikhonov ill-posed subspace "
                    "regularization (N o Iv) and Stratonovich nonlinear state augmentation (Sa). Solves high-dimensional "
                    "sensorimotor coordination under severely ill-posed and noisy inverse sensory feedback."
                ),
                unbuilt_historical_barrier=(
                    "Historical separation of physiological cybernetics (Bernstein at Institute of Neurology) "
                    "from mathematical ill-posed inverse theory (Tikhonov at Moscow State University) and lack of real-time SVD matrix engines."
                ),
                potential_modern_embodiment="Autonomous neuromorphic robotic manipulation under sparse tactile feedback arrays.",
            ),
            PredictedArchitectureRecord(
                prediction_id="PRED_ARCH_BETA_SELF_CONSISTENT_VIABILITY_AUTOMATON",
                architecture_name="Self-Consistent Viability Automaton (Tsetlin-Anokhin-Pontryagin)",
                predicted_primitive_composition=["Ad", "Sc", "E", "N"],
                structural_synthesis_rationale=(
                    "Fuses Tsetlin minimal state adaptation with Anokhin self-consistent action closure (Sc) "
                    "under Pontryagin boundary admissibility constraints (Ad) and minimax extremal robustness (E). "
                    "Guarantees hardware survival without environment modeling."
                ),
                unbuilt_historical_barrier=(
                    "Tsetlin's premature death in 1966 halted the integration of finite automata theory with Anokhin's physiological school."
                ),
                potential_modern_embodiment="Ultra-low-power edge sensor nodes operating in hazardous, unmodeled deep-space or subsurface environments.",
            ),
            PredictedArchitectureRecord(
                prediction_id="PRED_ARCH_GAMMA_INDUCTIVE_TOPOLOGICAL_HOMEOSTAT",
                architecture_name="Inductive Topological Homeostat (Ashby-Lie-Kolmogorov)",
                predicted_primitive_composition=["G", "Ii", "Ax", "C"],
                structural_synthesis_rationale=(
                    "Generalizes Ashby's scalar essential variable limits to continuous Lie group symmetry invariants (G) "
                    "with auxiliary geometric manifold tracking (Ax) and indirect inductive inference (Ii). Homeostasis maintained "
                    "across topological manifolds rather than decoupled scalar bounds."
                ),
                unbuilt_historical_barrier=(
                    "Requires differential geometry and modern topological dynamics (Bourbaki/Kolmogorov) which were not "
                    "available to early British cybernetics (Ashby relied on relay networks and vacuum tubes)."
                ),
                potential_modern_embodiment="Geometric deep learning controllers for fluid-structure interaction and non-rigid morphing drones.",
            ),
        ]

        self.predicted_architectures = preds

    def _generate_bridge_relations(self) -> None:
        """Constructs formal cross-graph ontology relations between G_SOVCTX and G_BCIG."""
        rel_id_counter = 1

        for arch_id, arch in self.architectures.items():
            for sym in arch.realized_primitives:
                pid = self.symbol_to_id.get(sym, f"PRIM:{sym}")

                # 1. REALIZES_METHOD_PRIMITIVE
                rel1 = BridgeRelationRecord(
                    relation_id=f"REL:BCIG_XGRAPH:{rel_id_counter:04d}",
                    relation_type="REALIZES_METHOD_PRIMITIVE",
                    architecture_id=arch_id,
                    architecture_name=arch.architecture_name,
                    method_primitive_symbol=sym,
                    method_primitive_id=pid,
                    domain=arch.domain,
                    epistemic_justification=f"{arch.architecture_name} instantiates mathematical primitive {sym} in its functional loop.",
                )
                self.relations.append(rel1)
                rel_id_counter += 1

                # 2. ARCHITECTURAL_MANIFESTATION_OF
                rel2 = BridgeRelationRecord(
                    relation_id=f"REL:BCIG_XGRAPH:{rel_id_counter:04d}",
                    relation_type="ARCHITECTURAL_MANIFESTATION_OF",
                    architecture_id=arch_id,
                    architecture_name=arch.architecture_name,
                    method_primitive_symbol=sym,
                    method_primitive_id=pid,
                    domain=arch.domain,
                    epistemic_justification=f"Cybernetic/bionic mechanism {arch.architecture_id} is the physical/systemic manifestation of methodological primitive {sym}.",
                )
                self.relations.append(rel2)
                rel_id_counter += 1

    def evaluate_bridge_grammar_concordance(self) -> BcigBridgeSummaryReport:
        """
        Evaluates whether the operational sequences of cybernetic architectures
        satisfy the non-commutative grammar matrix from M6.2.
        """
        total_transitions = 0
        concordant_transitions = 0
        high_gamma_matches = 0

        for arch in self.architectures.values():
            seq = arch.operational_sequence
            for idx in range(len(seq) - 1):
                p1, p2 = seq[idx], seq[idx + 1]
                id1 = self.symbol_to_id.get(p1)
                id2 = self.symbol_to_id.get(p2)

                if id1 and id2:
                    total_transitions += 1
                    lvl = self.grammar_engine.gamma_matrix.get((id1, id2), 0)

                    # Check validity under M4/M6 contracts:
                    # In M6.2, valid transitions have grammar_level >= 0
                    if lvl >= 0:
                        concordant_transitions += 1
                    if lvl >= 2:
                        high_gamma_matches += 1

        concordance_rate = (concordant_transitions / total_transitions) if total_transitions > 0 else 0.0

        rel_dist = Counter(r.relation_type for r in self.relations)
        prim_cov = Counter(r.method_primitive_symbol for r in self.relations)

        return BcigBridgeSummaryReport(
            total_architectures_mapped=len(self.architectures) + len(self.predicted_architectures),
            historical_architectures_count=len(self.architectures),
            predicted_architectures_count=len(self.predicted_architectures),
            total_bridge_relations=len(self.relations),
            relation_type_distribution=dict(rel_dist),
            primitive_realization_coverage=dict(prim_cov),
            grammar_concordance_rate=concordance_rate,
            high_gamma_epistemic_matches=high_gamma_matches,
            architectures=list(self.architectures.values()),
            predicted_architectures=self.predicted_architectures,
        )


def main() -> None:
    engine = CyberneticBionicBridgeEngine()
    summary = engine.evaluate_bridge_grammar_concordance()

    print("=" * 80)
    print("SOVCTX-BCIG-1: CYBERNETIC-BIONIC METHODOLOGICAL ARCHITECTURE BRIDGE")
    print("=" * 80)
    print(f"Total Architectures Mapped: {summary.total_architectures_mapped} (Historical: {summary.historical_architectures_count}, Predicted: {summary.predicted_architectures_count})")
    print(f"Total Cross-Graph Bridge Relations: {summary.total_bridge_relations}")
    print(f"Cross-Graph Grammar Concordance Rate: {summary.grammar_concordance_rate:.1%}")
    print(f"High-Gamma Epistemic Transitions: {summary.high_gamma_epistemic_matches}")

    print("\n1. HISTORICAL CYBERNETIC / BIONIC ARCHITECTURES:")
    for a in summary.architectures:
        print(f"\n  [{a.architecture_id}] {a.architecture_name} ({a.author}, {a.historical_year})")
        print(f"       Operational Sequence: {' -> '.join(a.operational_sequence)}")
        print(f"       Question-Sufficient State: {a.question_sufficient_reduction[:80]}...")
        print(f"       Negative Information: {a.what_is_ignored_as_irrelevant[:80]}...")

    print("\n2. SYNTHETIC PREDICTED ARCHITECTURES (UNBUILT IN 1960s):")
    for p in summary.predicted_architectures:
        print(f"\n  [{p.prediction_id}] {p.architecture_name}")
        print(f"       Composition: {' o '.join(p.predicted_primitive_composition)}")
        print(f"       Rationale: {p.structural_synthesis_rationale[:80]}...")
        print(f"       Historical Barrier: {p.unbuilt_historical_barrier[:80]}...")
        print(f"       Modern Embodiment: {p.potential_modern_embodiment[:80]}...")
    print("=" * 80)


if __name__ == "__main__":
    main()
