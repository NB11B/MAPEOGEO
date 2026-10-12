"""BCIG Controlled Cross-Graph Hypothesis Layer.

Establishes a non-destructive, typed epistemic bridge connecting the SOVCTX mathematical context
graph and the BCIG bionic/cybernetic adaptive intelligence graph.

Core Axioms:
1. DIRECT_LINEAGE != MATHEMATICAL_DESCENT != ARCHITECTURAL_RECURRENCE != FUNCTIONAL_ANALOGUE.
2. No source objects cross the physical graph boundary; only typed hypothesis records exist.
3. Introduces the relational primitive PROBE (ACT_TO_KNOW):
       REPRESENT -> PROBE (ACT_TO_KNOW) -> OBSERVE -> UPDATE -> CONTROL
4. Formalizes the fundamental architectural boundary:
       EXTERNALLY_EVALUATED_SYSTEMS vs INTERNALLY_CLOSED_ADAPTIVE_SYSTEMS
5. Defines ENDOGENOUS_SELF_MAINTENANCE:
       Computational self-maintenance integrated into the intelligence loop as an internally valued condition.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class HypothesisBridgeType(str, Enum):
    STRUCTURAL_BRIDGE = "STRUCTURAL_BRIDGE"          # Same operational loop topology reconstructed
    ARCHITECTURAL_BRIDGE = "ARCHITECTURAL_BRIDGE"    # Matching internal closure and goal-formation mechanics
    COMPUTATIONAL_PRINCIPLE = "COMPUTATIONAL_PRINCIPLE" # Bounded numerical/algorithmic realization principle


class SystemClosureTaxonomy(str, Enum):
    EXTERNALLY_EVALUATED = "EXTERNALLY_EVALUATED"    # External objective -> computation -> external evaluation
    INTERNALLY_CLOSED = "INTERNALLY_CLOSED"          # Internal condition -> endogenous goal -> action -> restored condition


@dataclass
class CrossGraphHypothesis:
    hypothesis_id: str
    sovctx_thread_id: str
    sovctx_thread_name: str
    bcig_target_concept: str
    bridge_type: HypothesisBridgeType
    relational_grammar: str
    epistemic_claim: str
    counter_evidence_risks: List[str]
    falsification_criteria: str
    primary_sources: List[str]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["bridge_type"] = self.bridge_type.value
        return d


CANONICAL_CROSS_GRAPH_HYPOTHESES: List[CrossGraphHypothesis] = [
    CrossGraphHypothesis(
        hypothesis_id="HYP:XGRAPH:01_EPISTEMIC_ACTION",
        sovctx_thread_id="T10",
        sovctx_thread_name="Dual Control & Adaptive State Estimation",
        bcig_target_concept="BCIG:Epistemic Action (ACT_TO_KNOW)",
        bridge_type=HypothesisBridgeType.STRUCTURAL_BRIDGE,
        relational_grammar="REPRESENT -> PROBE (ACT_TO_KNOW) -> OBSERVE -> UPDATE -> CONTROL",
        epistemic_claim=(
            "In stochastic systems with unknown environmental dynamics, the action itself is epistemic: "
            "acting to probe and reduce uncertainty is inextricably unified with acting to achieve a goal. "
            "Modern curiosity-driven RL and Active Inference are structural recurrences of this principle."
        ),
        counter_evidence_risks=[
            "Conflating generic trial-and-error RL with explicit dual control where action variance is optimized for parameter identification."
        ],
        falsification_criteria=(
            "Falsified if modern active inference can be shown to directly cite Feldbaum, proving genetic lineage "
            "rather than structural recurrence, or if modern RL policies do not alter trajectories for information gain."
        ),
        primary_sources=["Feldbaum (1960) 'Dual Control Theory I & II'", "Tsetlin (1961)"],
    ),
    CrossGraphHypothesis(
        hypothesis_id="HYP:XGRAPH:02_CLOSED_ADAPTIVE_SYSTEMS",
        sovctx_thread_id="T11",
        sovctx_thread_name="Physiological Cybernetics & Functional Systems",
        bcig_target_concept="BCIG:Closed Adaptive Intelligence",
        bridge_type=HypothesisBridgeType.ARCHITECTURAL_BRIDGE,
        relational_grammar="NEED -> ENDOGENOUS_GOAL -> ACTION_ACCEPTOR (PREDICT) -> ACT -> RETURN_AFFERENCE -> COMPARE -> CORRECT",
        epistemic_claim=(
            "Anokhin's Functional System formalizes the boundary between externally evaluated systems (prompt-in / answer-out) "
            "and internally closed adaptive systems: success is determined endogenously by matching return sensory afference "
            "against the anticipatory action acceptor."
        ),
        counter_evidence_risks=[
            "Treating standard feedback loops (Wiener negative feedback) as equivalent to Anokhin's forward efference simulation."
        ],
        falsification_criteria=(
            "Falsified if prompt-response foundation models are demonstrated to possess endogenous goal formation "
            "independent of prompt context."
        ),
        primary_sources=["Anokhin (1968) 'Biology and Neurophysiology of the Conditioned Reflex'"],
    ),
    CrossGraphHypothesis(
        hypothesis_id="HYP:XGRAPH:03_RESOURCE_BOUNDED_INTELLIGENCE",
        sovctx_thread_id="T12",
        sovctx_thread_name="Finite Computational Regularization on Soviet Mainframes",
        bcig_target_concept="BCIG:Resource-Bounded Intelligence",
        bridge_type=HypothesisBridgeType.COMPUTATIONAL_PRINCIPLE,
        relational_grammar="ILL_POSED_TASK -> DISCRETIZE -> MINIMAX_BOUND -> REGULARIZE -> NUMERICAL_SOLVE",
        epistemic_claim=(
            "Chebyshev-Samarskii regularization on BESM-6 demonstrates that real-world intelligence is bounded by finite word lengths, "
            "discrete grid approximations, and computational ceilings. Bounded computation is an intrinsic mathematical constraint "
            "on state recovery rather than an implementation detail."
        ),
        counter_evidence_risks=[
            "Equating numerical stability of Fredholm integral solvers directly with modern low-bit neural network quantization (overreach)."
        ],
        falsification_criteria=(
            "Falsified if ill-posed inverse operators can be stably recovered without compact parameter regularization in finite precision."
        ),
        primary_sources=["Samarskii (1967) 'Theory of Difference Schemes'", "Tikhonov & Samarskii (1977)"],
    ),
]


def get_cross_graph_hypotheses() -> List[CrossGraphHypothesis]:
    return list(CANONICAL_CROSS_GRAPH_HYPOTHESES)
