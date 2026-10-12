"""Controlled Historical Bridge: SOVCTX -> BCIG.

Formulates explicit, non-destructive epistemic connections between Soviet/Russian
mathematical foundations (SOVCTX) and bionic/cybernetic adaptive intelligence (BCIG).

Enforces strict separation:
- SOVCTX remains the mathematical context graph.
- BCIG remains the international adaptive intelligence graph.
- Bridges are external, typed cross-graph assertions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class SOVCTXBridgeRelation(str, Enum):
    """Controlled relationship types connecting SOVCTX mathematical operators to BCIG concepts."""
    MATHEMATICAL_FOUNDATION_OF = "MATHEMATICAL_FOUNDATION_OF"
    OPERATOR_INSTANTIATION = "OPERATOR_INSTANTIATION"
    PARALLEL_RESEARCH_COMMUNITY = "PARALLEL_RESEARCH_COMMUNITY"
    DIRECT_PERSONNEL_CROSSING = "DIRECT_PERSONNEL_CROSSING"


@dataclass
class SOVCTXBridgeRecord:
    bridge_id: str
    sovctx_entity_id: str
    sovctx_concept_label: str
    bcig_entity_id: str
    bcig_concept_label: str
    bridge_relation: SOVCTXBridgeRelation
    epistemic_justification: str
    documented_sources: List[str]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["bridge_relation"] = self.bridge_relation.value
        return d


CANONICAL_SOVCTX_BCIG_BRIDGES: List[SOVCTXBridgeRecord] = [
    SOVCTXBridgeRecord(
        bridge_id="BRIDGE:SOVCTX_BCIG_01",
        sovctx_entity_id="OP:STATE",
        sovctx_concept_label="Lyapunov Phase State Coordinates & Vector Field",
        bcig_entity_id="BCIG:ARCHITECTURAL_PRINCIPLE:BERNSTEIN_DEGREES_OF_FREEDOM",
        bcig_concept_label="Bernstein Multi-Joint Biomechanical Degrees of Freedom",
        bridge_relation=SOVCTXBridgeRelation.MATHEMATICAL_FOUNDATION_OF,
        epistemic_justification=(
            "Bernstein explicitly formalized physiological movement as trajectories through high-dimensional phase space, "
            "directly invoking Lyapunov-style differential systems to model peripheral biomechanical dynamics."
        ),
        documented_sources=["Bernstein (1947) 'On the Construction of Movements'"],
    ),
    SOVCTXBridgeRecord(
        bridge_id="BRIDGE:SOVCTX_BCIG_02",
        sovctx_entity_id="OP:STABILITY",
        sovctx_concept_label="Lyapunov Asymptotic Stability & Invariant Subspaces",
        bcig_entity_id="BCIG:CONTROL_PRINCIPLE:ANOKHIN_ACTION_ACCEPTOR",
        bcig_concept_label="Anokhin Action Acceptor & Return Afference Convergence",
        bridge_relation=SOVCTXBridgeRelation.OPERATOR_INSTANTIATION,
        epistemic_justification=(
            "Anokhin's action acceptor functions as an attractor basin: return sensory afference is compared against "
            "the expected result until the discrepancy Delta converges to the invariant zero set."
        ),
        documented_sources=["Anokhin (1968) 'Biology and Neurophysiology of the Conditioned Reflex'"],
    ),
    SOVCTXBridgeRecord(
        bridge_id="BRIDGE:SOVCTX_BCIG_03",
        sovctx_entity_id="PERSON:GELFAND_IM",
        sovctx_concept_label="I. M. Gelfand (Steklov / MIAN Spectral Theory)",
        bcig_entity_id="BCIG:PERSON:TSETLIN_ML",
        bcig_concept_label="M. L. Tsetlin (Soviet Cybernetics & Automata)",
        bridge_relation=SOVCTXBridgeRelation.DIRECT_PERSONNEL_CROSSING,
        epistemic_justification=(
            "Direct documented collaboration: Gelfand and Tsetlin co-founded the Moscow physiological seminar (1957–1966), "
            "jointly authoring foundational works on nonlocal search, respiratory-locomotor synergies, and automata in random media."
        ),
        documented_sources=[
            "Gelfand, Gurfinkel, Tsetlin (1962) 'Tactics of Movement Construction'",
            "Gelfand & Tsetlin (1962) 'Some Methods of Control for Complex Systems'",
        ],
    ),
    SOVCTXBridgeRecord(
        bridge_id="BRIDGE:SOVCTX_BCIG_04",
        sovctx_entity_id="FAMILY:TIKHONOV_REGULARIZATION",
        sovctx_concept_label="Tikhonov Regularized Ill-Posed Inverse Recovery",
        bcig_entity_id="BCIG:CONTROL_PRINCIPLE:ACTIVE_PERCEPTION_REGULARIZATION",
        bcig_concept_label="Sensory Afference Inversion under Compact Constraints",
        bridge_relation=SOVCTXBridgeRelation.MATHEMATICAL_FOUNDATION_OF,
        epistemic_justification=(
            "Sensory state estimation from indirect receptors constitutes a Fredholm integral equation of the first kind; "
            "motor synergies act as a priori compact constraints guaranteeing stable, well-posed inverse reconstruction."
        ),
        documented_sources=["Gelfand & Tsetlin (1961) 'Principles of Nonlocal Search'"],
    ),
]

# Grounded discoveries from the 2-Hour Autonomous Research Shakedown on Jetson Nano
EXPANDED_SOVCTX_BCIG_BRIDGES: List[SOVCTXBridgeRecord] = list(CANONICAL_SOVCTX_BCIG_BRIDGES) + [
    SOVCTXBridgeRecord(
        bridge_id="BRIDGE:SOVCTX_BCIG_05",
        sovctx_entity_id="PUB:FELDBAUM_1960_DUAL_CONTROL",
        sovctx_concept_label="Feldbaum Dual Control Theory & Stochastic State Probing",
        bcig_entity_id="BCIG:CONTROL_PRINCIPLE:DUAL_CONTROL_EXPLORATION_EXPLOITATION",
        bcig_concept_label="Epistemic vs Pragmatic Action Decomposition (Active Inference & RL)",
        bridge_relation=SOVCTXBridgeRelation.MATHEMATICAL_FOUNDATION_OF,
        epistemic_justification=(
            "Feldbaum (1960) mathematically proved that in stochastic systems with unobserved parameters, the optimal control "
            "action is intrinsically dual: simultaneously probing to acquire information (epistemic value) and steering toward "
            "the objective (pragmatic value). This directly anticipates the active inference expected free energy decomposition "
            "(Friston 2010) and exploration bonuses in modern reinforcement learning."
        ),
        documented_sources=[
            "Feldbaum (1960) 'Dual Control Theory I & II'",
            "Tsetlin (1961) 'On the Behavior of Finite Automata in Random Media'",
        ],
    ),
    SOVCTXBridgeRecord(
        bridge_id="BRIDGE:SOVCTX_BCIG_06",
        sovctx_entity_id="PUB:KRASOVSKII_1959_STABILITY",
        sovctx_concept_label="Krasovskii Extremal Targeting & Positional Differential Games",
        bcig_entity_id="BCIG:CONTROL_PRINCIPLE:ROBUST_SAFE_REGULATION",
        bcig_concept_label="Control Barrier Functions & Adversarially Robust Invariance",
        bridge_relation=SOVCTXBridgeRelation.OPERATOR_INSTANTIATION,
        epistemic_justification=(
            "Krasovskii unified Lyapunov stability functions with Pontryagin extremal regulation under discontinuous feedback "
            "and worst-case adversary disturbances using quasi-solutions. This represents the mathematical ancestor to modern "
            "Control Barrier Functions (CBFs) and robust safe reinforcement learning."
        ),
        documented_sources=[
            "Krasovskii (1959) 'Stability of Motion'",
            "Krasovskii & Subbotin (1974) 'Positional Differential Games'",
        ],
    ),
    SOVCTXBridgeRecord(
        bridge_id="BRIDGE:SOVCTX_BCIG_07",
        sovctx_entity_id="PUB:VLASOV_1938",
        sovctx_concept_label="Vlasov-Bogolyubov Self-Consistent Field & Kinetic Hierarchy",
        bcig_entity_id="BCIG:ARCHITECTURAL_PRINCIPLE:FUNCTIONAL_SYSTEM",
        bcig_concept_label="Anokhin Macroscopic Functional System Coalition Assembly",
        bridge_relation=SOVCTXBridgeRelation.OPERATOR_INSTANTIATION,
        epistemic_justification=(
            "Vlasov's microscopic-to-macroscopic kinetic reduction grammar directly mirrors Anokhin's Functional Systems Theory: "
            "distributed neural and somatic elements coordinate via a macroscopic self-consistent field of return afference "
            "rather than point-to-point central commands, matching modern Mean-Field Multi-Agent Games and dynamic MoE routing."
        ),
        documented_sources=[
            "Vlasov (1938) 'Vibration Properties of an Electron Gas'",
            "Anokhin (1968) 'Biology and Neurophysiology of the Conditioned Reflex'",
        ],
    ),
    SOVCTXBridgeRecord(
        bridge_id="BRIDGE:SOVCTX_BCIG_08",
        sovctx_entity_id="PUB:SAMARSKII_1967_DIFFERENCE_SCHEMES",
        sovctx_concept_label="Chebyshev-Samarskii Regularization Solvers on BESM Mainframes",
        bcig_entity_id="BCIG:COMPUTATIONAL_PRINCIPLE:FINITE_PRECISION_REGULARIZATION",
        bcig_concept_label="Quantized Regularized Inversion on Ill-Conditioned Loss Manifolds",
        bridge_relation=SOVCTXBridgeRelation.MATHEMATICAL_FOUNDATION_OF,
        epistemic_justification=(
            "Samarskii and Lebedev integrated Chebyshev minimax approximation into discrete regularization kernels on BESM-6 "
            "computers to maintain inversion stability under finite floating-point word lengths, preceding contemporary quantized "
            "deep learning and ill-conditioned optimization techniques."
        ),
        documented_sources=[
            "Samarskii (1967) 'Theory of Difference Schemes'",
            "Tikhonov & Samarskii (1977) 'Equations of Mathematical Physics'",
        ],
    ),
]


def get_sovctx_bridges() -> List[SOVCTXBridgeRecord]:
    """Returns the canonical baseline bridges between SOVCTX and BCIG (BCIG-0 through BCIG-7)."""
    return list(CANONICAL_SOVCTX_BCIG_BRIDGES)


def get_expanded_sovctx_bridges() -> List[SOVCTXBridgeRecord]:
    """Returns all 8 grounded bridges including the 2-Hour Autonomous Shakedown discoveries."""
    return list(EXPANDED_SOVCTX_BCIG_BRIDGES)


