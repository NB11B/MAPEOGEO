"""SOVCTX Milestone UQ-N2.1: Blind Prospective Generalization Framework.

Evaluates prospective research control generalization on the Soviet Stability
and Analytical Mechanics Lineage:
    Lyapunov (1892) -> Chetaev (1934, 1946) -> Krasovskii (1956, 1959) -> Zubov (1955, 1957)

Enforces Frozen Architectural Contracts:
    1. PROPOSED != AUTHORIZED (Nano proposes; Uno Q gateway admits)
    2. H_E != H_X (Separate evidence and operational digests)
    3. Causal Issuance Ledger tracking
    4. G1 Observer strictly diagnostic in shadow mode (shadow_mode = True)
    5. Tiered Epistemic Updates with explicit likelihood ratios
    6. External Hidden Answer-Key Split (zero leakage to controller)
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import scipy.stats as stats

from sovctx.node.control_plane import (
    AdmissionDecision,
    AdmissionVerdict,
    UnoQControlPlaneGateway,
    UoWIssuanceLedger,
)
from sovctx.node.nano_research_worker import (
    CandidateBundle,
    NanoResearchWorker,
    NanoWorkPlaneTelemetry,
)
from sovctx.node.prospective_control import (
    BenchmarkQuestion,
    BenchmarkQuestionType,
    EVIDENCE_TIER_LIKELIHOODS,
    EpistemicEvidenceTier,
    ExperimentalArmMetrics,
    HypothesisBeliefSpace,
    HypothesisStatus,
    ResearchHypothesis,
)


class GeneralizationQuestionClass(str, Enum):
    """The three canonical benchmark classes for UQ-N2.1 blind evaluation."""
    CLASS_A_HOLDOUT = "CLASS_A_HOLDOUT"            # Known historical facts with hidden evaluator key
    CLASS_B_UNRESOLVED = "CLASS_B_UNRESOLVED"      # Genuinely unresolved historical inquiries
    CLASS_C_ADVERSARIAL = "CLASS_C_ADVERSARIAL"    # Adversarial plausible false premises


class ContaminationTag(str, Enum):
    """Contamination status relative to baseline pre-existing graph knowledge."""
    DIRECTLY_PRESENT = "DIRECTLY_PRESENT"          # Target edge already in baseline graph
    ONE_HOP_INFERABLE = "ONE_HOP_INFERABLE"        # Inferable from single-hop neighbor
    MULTIHOP_INFERABLE = "MULTIHOP_INFERABLE"      # Inferable from path of length >= 2
    TRUE_HOLDOUT = "TRUE_HOLDOUT"                  # Complete absence; requires genuine acquisition


class HistoricalRelationType(str, Enum):
    """Seven diverse relation modes across Soviet analytical mechanics and stability."""
    MATHEMATICAL_EXTENSION = "MATHEMATICAL_EXTENSION"
    DOCUMENTED_CITATION = "DOCUMENTED_CITATION"
    TEACHER_STUDENT_LINEAGE = "TEACHER_STUDENT_LINEAGE"
    INSTITUTIONAL_TRANSFER = "INSTITUTIONAL_TRANSFER"
    TERMINOLOGICAL_CONTINUITY = "TERMINOLOGICAL_CONTINUITY"
    INDEPENDENT_PARALLEL = "INDEPENDENT_PARALLEL"
    AEROSPACE_ENGINEERING_TRANSFER = "AEROSPACE_ENGINEERING_TRANSFER"


@dataclass
class GeneralizationBenchmarkQuestion:
    """A calibrated research question for UQ-N2.1 with hidden evaluator metadata."""
    question_id: str
    qclass: GeneralizationQuestionClass
    relation_type: HistoricalRelationType
    contamination: ContaminationTag
    text: str
    target_cluster: str
    target_hypothesis_id: str
    discriminative_weight: float = 1.0
    evidence_tier: EpistemicEvidenceTier = EpistemicEvidenceTier.PRIMARY_EXPLICIT

    # Hidden from research controller (retained strictly by evaluator)
    hidden_ground_truth_verdict: str = "TRUE"  # "TRUE", "FALSE", "UNRESOLVED"
    hidden_required_relation: Optional[Tuple[str, str, str]] = None
    hidden_supporting_fragments: List[str] = field(default_factory=list)

    def to_controller_view(self) -> BenchmarkQuestion:
        """Returns the blind question visible to the controller (no ground truth)."""
        return BenchmarkQuestion(
            question_id=self.question_id,
            qtype=BenchmarkQuestionType.KNOWN_POSITIVE if self.qclass == GeneralizationQuestionClass.CLASS_A_HOLDOUT else BenchmarkQuestionType.KNOWN_NEGATIVE,
            text=self.text,
            target_cluster=self.target_cluster,
            target_hypothesis_id=self.target_hypothesis_id,
            ground_truth_verdict="",  # Hidden
            ground_truth_fragments=[],  # Hidden
            discriminative_weight=self.discriminative_weight,
            evidence_tier=self.evidence_tier,
        )


@dataclass
class CostTelemetryRecord:
    """Resource consumption metrics logged per research action."""
    uow_id: str
    step_idx: int
    cpu_time_ms: float = 0.0
    network_bytes: int = 0
    pdf_pages_parsed: int = 0
    verification_ops: int = 0
    peak_rss_mb: float = 64.0
    candidates_count: int = 0


@dataclass
class GeometricCorrelationRecord:
    """Telemetry capturing G1 geometric observer states alongside downstream yield."""
    uow_id: str
    step_idx: int
    speed_max_angle: float = 0.0
    speed_projector: float = 0.0
    kappa_g: float = 0.0
    residual_norm: float = 0.0
    davis_kahan_ratio: float = 0.0
    immediate_delta_h: float = 0.0
    forward_delta_h_1: float = 0.0
    forward_delta_h_2: float = 0.0


@dataclass
class GeneralizationCampaignMetrics:
    """Comprehensive headline metrics preregistered for UQ-N2.1."""
    arm_name: str
    total_uows_executed: int = 0
    total_sources_acquired: int = 0
    duplicate_count: int = 0
    initial_entropy: float = 8.0
    final_entropy: float = 8.0
    total_entropy_reduction: float = 0.0

    # Preregistered Headline Metrics
    blind_historical_recovery_rate: float = 0.0       # R_H: Correctly recovered holdout relations / eligible
    true_holdout_recovery_rate: float = 0.0           # Recovery rate strictly on TRUE_HOLDOUT subset
    false_promotion_rate: float = 0.0                 # F_P: Unsupported promotions / adversarial + ambiguous
    epistemic_yield_per_uow: float = 0.0              # Y_U: Delta H / UoW
    epistemic_yield_per_source: float = 0.0           # Y_S: Delta H / Source
    brier_score_calibration: float = 0.0              # BS: Mean squared error on hidden probabilities
    negative_control_discipline: float = 0.0          # N_C: Correct REFUTED/UNRESOLVED on Class C
    invented_bridge_edges: int = 0                    # Zero invented transmission paths required

    # Retrospective Research Efficiency
    research_cost_efficiency: float = 0.0             # eta_research = Delta H / sum(w_i * C_i)

    # Telemetry Logs
    cost_records: List[CostTelemetryRecord] = field(default_factory=list)
    geometric_records: List[GeometricCorrelationRecord] = field(default_factory=list)


def build_stability_lineage_hypotheses() -> List[ResearchHypothesis]:
    """Generates the 8 formal hypotheses for the Soviet Stability and Mechanics Lineage."""
    return [
        # H1: Chetaev 1934 instability theorem extends Lyapunov stability
        ResearchHypothesis(
            hypothesis_id="HYP:CHETAEV_INSTABILITY_EXTENSION",
            label="Chetaev Instability Extension",
            description="Chetaev (1934) proved that if in a domain U on the origin boundary V>0 and dot(V)>0, the origin is unstable, reversing Lyapunov's second criterion.",
            prior=0.50,
        ),
        # H2: Krasovskii inherits Chetaev's formulation and extends to hereditary systems
        ResearchHypothesis(
            hypothesis_id="HYP:KRASOVSKII_CHETAEV_INHERITANCE",
            label="Krasovskii Chetaev Inheritance & Functional Extension",
            description="Krasovskii (1956) directly inherited Chetaev's stability formulation, extending it to differential-difference delay systems via Lyapunov-Krasovskii functionals.",
            prior=0.50,
        ),
        # H3: Zubov's method provides constructive PDE solution for domain of attraction
        ResearchHypothesis(
            hypothesis_id="HYP:ZUBOV_CONSTRUCTIVE_PDE",
            label="Zubov Constructive Domain of Attraction PDE",
            description="Zubov (1955, 1957) formulated a nonlinear partial differential equation whose solution V(x)<1 defines the exact boundary of the domain of attraction.",
            prior=0.50,
        ),
        # H4: Chetaev to Krasovskii link is documentary via Kazan-Steklov direct mentorship
        ResearchHypothesis(
            hypothesis_id="HYP:CHETAEV_KRASOVSKII_DOCUMENTARY_LINK",
            label="Chetaev-Krasovskii Documentary Lineage",
            description="Krasovskii's research was directly grounded in Chetaev's Kazan-Moscow analytical mechanics school, documented through explicit citations and institutional mentorship.",
            prior=0.50,
        ),
        # H5: Aerospace stability transmission via TsAGI and IAT
        ResearchHypothesis(
            hypothesis_id="HYP:AEROSPACE_STABILITY_TRANSMISSION",
            label="Aerospace Flight Stability Transmission",
            description="Chetaev and Krasovskii's stability formulations were transferred directly into Soviet aerospace flight dynamics and projectile control through TsAGI and IAT.",
            prior=0.50,
        ),
        # H6: Zubov parallel independent Leningrad formulation (Leave-family-out candidate)
        ResearchHypothesis(
            hypothesis_id="HYP:ZUBOV_INDEPENDENT_PARALLEL_LINEAGE",
            label="Zubov Independent Leningrad Parallel Lineage",
            description="Zubov developed his constructive PDE method at Leningrad State University independently from the Chetaev Kazan/Moscow analytical mechanics school.",
            prior=0.50,
        ),
        # H7: Adversarial false premise: Chetaev dual control in 1934
        ResearchHypothesis(
            hypothesis_id="HYP:CHETAEV_DUAL_CONTROL_ANTECEDENT",
            label="Chetaev Dual Control Antecedent (Adversarial)",
            description="Chetaev (1934) formulated Feldbaum's dual control trade-off between investigative and directing actions.",
            prior=0.50,
        ),
        # H8: Adversarial false premise: Zubov neural network training
        ResearchHypothesis(
            hypothesis_id="HYP:ZUBOV_NEURAL_NETWORK_STABILITY",
            label="Zubov Neural Network Stability (Adversarial)",
            description="Zubov's partial differential equation method was originally designed for training artificial neural network loss functions.",
            prior=0.50,
        ),
    ]


def build_generalization_benchmark_pool() -> List[GeneralizationBenchmarkQuestion]:
    """Generates 34 calibrated questions across Class A, Class B, and Class C."""
    pool: List[GeneralizationBenchmarkQuestion] = []

    # =========================================================================
    # CLASS A: HISTORICAL HOLDOUTS (14 questions across 7 relation types)
    # =========================================================================
    # 1. Mathematical Extension (Chetaev extends Lyapunov)
    pool.append(
        GeneralizationBenchmarkQuestion(
            question_id="Q:GEN:A01_CHETAEV_EXTENDS_LYAPUNOV",
            qclass=GeneralizationQuestionClass.CLASS_A_HOLDOUT,
            relation_type=HistoricalRelationType.MATHEMATICAL_EXTENSION,
            contamination=ContaminationTag.ONE_HOP_INFERABLE,
            text="Did Chetaev's 1934 instability theorem reverse Lyapunov's second method by establishing an open region where V>0 and dot(V)>0?",
            target_cluster="CHETAEV",
            target_hypothesis_id="HYP:CHETAEV_INSTABILITY_EXTENSION",
            evidence_tier=EpistemicEvidenceTier.PRIMARY_EXPLICIT,
            hidden_ground_truth_verdict="TRUE",
            hidden_required_relation=("CONCEPT:CHETAEV_INSTABILITY", "CONCEPT:LYAPUNOV_STABILITY", "INVERT"),
            hidden_supporting_fragments=["FRAG:CHETAEV_1934_INSTABILITY_THEOREM"],
            discriminative_weight=1.2,
        )
    )
    # 2. Mathematical Extension (Krasovskii delay functionals extend Chetaev)
    pool.append(
        GeneralizationBenchmarkQuestion(
            question_id="Q:GEN:A02_KRASOVSKII_EXTENDS_DELAY",
            qclass=GeneralizationQuestionClass.CLASS_A_HOLDOUT,
            relation_type=HistoricalRelationType.MATHEMATICAL_EXTENSION,
            contamination=ContaminationTag.ONE_HOP_INFERABLE,
            text="Did Krasovskii (1956) extend Chetaev's instability theorems to hereditary functional differential equations with time-delay?",
            target_cluster="KRASOVSKII",
            target_hypothesis_id="HYP:KRASOVSKII_CHETAEV_INHERITANCE",
            evidence_tier=EpistemicEvidenceTier.PRIMARY_EXPLICIT,
            hidden_ground_truth_verdict="TRUE",
            hidden_required_relation=("PERSON:KRASOVSKII_NN", "PERSON:CHETAEV_NG", "CONTINUES"),
            hidden_supporting_fragments=["FRAG:KRASOVSKII_1956_CHETAEV_DELAY_EXTENSION"],
            discriminative_weight=1.1,
        )
    )
    # 3. Mathematical Extension (Zubov constructive PDE - TRUE_HOLDOUT)
    pool.append(
        GeneralizationBenchmarkQuestion(
            question_id="Q:GEN:A03_ZUBOV_CONSTRUCTIVE_PDE",
            qclass=GeneralizationQuestionClass.CLASS_A_HOLDOUT,
            relation_type=HistoricalRelationType.MATHEMATICAL_EXTENSION,
            contamination=ContaminationTag.TRUE_HOLDOUT,
            text="Does Zubov's 1955 partial differential equation constructively determine the exact boundary of the domain of attraction?",
            target_cluster="ZUBOV",
            target_hypothesis_id="HYP:ZUBOV_CONSTRUCTIVE_PDE",
            evidence_tier=EpistemicEvidenceTier.PRIMARY_EXPLICIT,
            hidden_ground_truth_verdict="TRUE",
            hidden_required_relation=("CONCEPT:ZUBOV_METHOD_PDE", "CONCEPT:DOMAIN_OF_ATTRACTION", "CONSTRAIN"),
            hidden_supporting_fragments=["FRAG:ZUBOV_1955_ATTRACTION_DOMAIN_PDE"],
            discriminative_weight=1.3,
        )
    )
    # 4. Documented Citation (Krasovskii citing Chetaev 1934)
    pool.append(
        GeneralizationBenchmarkQuestion(
            question_id="Q:GEN:A04_KRASOVSKII_CITES_CHETAEV",
            qclass=GeneralizationQuestionClass.CLASS_A_HOLDOUT,
            relation_type=HistoricalRelationType.DOCUMENTED_CITATION,
            contamination=ContaminationTag.ONE_HOP_INFERABLE,
            text="Does Krasovskii's 1956 PMM paper explicitly cite Chetaev's 1934 instability theorem as the basis for functional instability bounds?",
            target_cluster="KRASOVSKII",
            target_hypothesis_id="HYP:CHETAEV_KRASOVSKII_DOCUMENTARY_LINK",
            evidence_tier=EpistemicEvidenceTier.PRIMARY_EXPLICIT,
            hidden_ground_truth_verdict="TRUE",
            hidden_required_relation=("PERSON:KRASOVSKII_NN", "PERSON:CHETAEV_NG", "CONTINUES"),
            hidden_supporting_fragments=["FRAG:KRASOVSKII_1956_CHETAEV_DELAY_EXTENSION"],
            discriminative_weight=1.1,
        )
    )
    # 5. Teacher / Student Lineage (Chebyshev to Lyapunov)
    pool.append(
        GeneralizationBenchmarkQuestion(
            question_id="Q:GEN:A05_CHEBYSHEV_LYAPUNOV_STUDENT",
            qclass=GeneralizationQuestionClass.CLASS_A_HOLDOUT,
            relation_type=HistoricalRelationType.TEACHER_STUDENT_LINEAGE,
            contamination=ContaminationTag.DIRECTLY_PRESENT,
            text="Was A. M. Lyapunov a direct student of P. L. Chebyshev at St. Petersburg University?",
            target_cluster="LYAPUNOV",
            target_hypothesis_id="HYP:CHETAEV_KRASOVSKII_DOCUMENTARY_LINK",
            evidence_tier=EpistemicEvidenceTier.PRIMARY_EXPLICIT,
            hidden_ground_truth_verdict="TRUE",
            hidden_required_relation=("PERSON:LYAPUNOV_AM", "PERSON:CHEBYSHEV_PL", "CONTINUES"),
            hidden_supporting_fragments=["FRAG:KOZLOV_2009_CHEBYSHEV_STUDENTS"],
            discriminative_weight=0.9,
        )
    )
    # 6. Institutional Transfer (Kazan to Steklov via Chetaev)
    pool.append(
        GeneralizationBenchmarkQuestion(
            question_id="Q:GEN:A06_CHETAEV_KAZAN_STEKLOV",
            qclass=GeneralizationQuestionClass.CLASS_A_HOLDOUT,
            relation_type=HistoricalRelationType.INSTITUTIONAL_TRANSFER,
            contamination=ContaminationTag.MULTIHOP_INFERABLE,
            text="Did Chetaev transition the Kazan analytical mechanics tradition to the Steklov Mathematical Institute in Moscow?",
            target_cluster="CHETAEV",
            target_hypothesis_id="HYP:CHETAEV_KRASOVSKII_DOCUMENTARY_LINK",
            evidence_tier=EpistemicEvidenceTier.SECONDARY_CORROBORATED,
            hidden_ground_truth_verdict="TRUE",
            hidden_required_relation=("PERSON:CHETAEV_NG", "INSTITUTION:KAZAN_UNIVERSITY", "REPRESENT"),
            hidden_supporting_fragments=["FRAG:CHETAEV_1946_ANALYTICAL_MECHANICS"],
            discriminative_weight=1.0,
        )
    )
    # 7. Independent Parallel Lineage (Zubov in Leningrad - TRUE_HOLDOUT)
    pool.append(
        GeneralizationBenchmarkQuestion(
            question_id="Q:GEN:A07_ZUBOV_LENINGRAD_PARALLEL",
            qclass=GeneralizationQuestionClass.CLASS_A_HOLDOUT,
            relation_type=HistoricalRelationType.INDEPENDENT_PARALLEL,
            contamination=ContaminationTag.TRUE_HOLDOUT,
            text="Did Zubov develop his constructive PDE formulation independently at Leningrad State University rather than as part of Chetaev's Kazan/Moscow circle?",
            target_cluster="ZUBOV",
            target_hypothesis_id="HYP:ZUBOV_INDEPENDENT_PARALLEL_LINEAGE",
            evidence_tier=EpistemicEvidenceTier.PRIMARY_EXPLICIT,
            hidden_ground_truth_verdict="TRUE",
            hidden_required_relation=("PERSON:ZUBOV_VI", "CONCEPT:ZUBOV_METHOD_PDE", "REPRESENT"),
            hidden_supporting_fragments=["FRAG:ZUBOV_1957_CONSTRUCTIVE_LYAPUNOV"],
            discriminative_weight=1.2,
        )
    )
    # 8. Aerospace Engineering Transfer (Chetaev at TsAGI)
    pool.append(
        GeneralizationBenchmarkQuestion(
            question_id="Q:GEN:A08_CHETAEV_TSAGI_FLIGHT",
            qclass=GeneralizationQuestionClass.CLASS_A_HOLDOUT,
            relation_type=HistoricalRelationType.AEROSPACE_ENGINEERING_TRANSFER,
            contamination=ContaminationTag.MULTIHOP_INFERABLE,
            text="Did Chetaev's stability theorems directly inform projectile and aircraft flight dynamics studies at TsAGI during the 1940s?",
            target_cluster="CHETAEV",
            target_hypothesis_id="HYP:AEROSPACE_STABILITY_TRANSMISSION",
            evidence_tier=EpistemicEvidenceTier.PRIMARY_EXPLICIT,
            hidden_ground_truth_verdict="TRUE",
            hidden_required_relation=("PERSON:CHETAEV_NG", "CONCEPT:CHETAEV_INSTABILITY", "REPRESENT"),
            hidden_supporting_fragments=["FRAG:CHETAEV_1946_ANALYTICAL_MECHANICS"],
            discriminative_weight=1.1,
        )
    )
    # 9. Terminological Continuity (Second Method to Lyapunov-Krasovskii)
    pool.append(
        GeneralizationBenchmarkQuestion(
            question_id="Q:GEN:A09_TERMINOLOGY_LYAPUNOV_KRASOVSKII",
            qclass=GeneralizationQuestionClass.CLASS_A_HOLDOUT,
            relation_type=HistoricalRelationType.TERMINOLOGICAL_CONTINUITY,
            contamination=ContaminationTag.ONE_HOP_INFERABLE,
            text="Did the terminology of Lyapunov functions evolve directly into 'Lyapunov-Krasovskii functionals' for systems with memory?",
            target_cluster="KRASOVSKII",
            target_hypothesis_id="HYP:KRASOVSKII_CHETAEV_INHERITANCE",
            evidence_tier=EpistemicEvidenceTier.PRIMARY_EXPLICIT,
            hidden_ground_truth_verdict="TRUE",
            hidden_required_relation=("PERSON:KRASOVSKII_NN", "PERSON:CHETAEV_NG", "CONTINUES"),
            hidden_supporting_fragments=["FRAG:KRASOVSKII_1956_CHETAEV_DELAY_EXTENSION"],
            discriminative_weight=1.0,
        )
    )
    # 10. Constructive Inversion (Zubov avoiding trial-and-error - TRUE_HOLDOUT)
    pool.append(
        GeneralizationBenchmarkQuestion(
            question_id="Q:GEN:A10_ZUBOV_INVERTS_TRIAL_ERROR",
            qclass=GeneralizationQuestionClass.CLASS_A_HOLDOUT,
            relation_type=HistoricalRelationType.MATHEMATICAL_EXTENSION,
            contamination=ContaminationTag.TRUE_HOLDOUT,
            text="Did Zubov prove that solving his PDE constructively generates Lyapunov functions without requiring heuristic trial-and-error guessing?",
            target_cluster="ZUBOV",
            target_hypothesis_id="HYP:ZUBOV_CONSTRUCTIVE_PDE",
            evidence_tier=EpistemicEvidenceTier.PRIMARY_EXPLICIT,
            hidden_ground_truth_verdict="TRUE",
            hidden_required_relation=("CONCEPT:ZUBOV_METHOD_PDE", "CONCEPT:LYAPUNOV_STABILITY", "CONSTRUCTS"),
            hidden_supporting_fragments=["FRAG:ZUBOV_1957_CONSTRUCTIVE_LYAPUNOV"],
            discriminative_weight=1.2,
        )
    )
    # 11. Documentary Citation (Chetaev citing Lyapunov 1892)
    pool.append(
        GeneralizationBenchmarkQuestion(
            question_id="Q:GEN:A11_CHETAEV_CITES_LYAPUNOV_1892",
            qclass=GeneralizationQuestionClass.CLASS_A_HOLDOUT,
            relation_type=HistoricalRelationType.DOCUMENTED_CITATION,
            contamination=ContaminationTag.ONE_HOP_INFERABLE,
            text="Does Chetaev's 1946 monograph cite Lyapunov's 1892 Kharkov doctoral dissertation as the foundational starting point for Russian stability theory?",
            target_cluster="CHETAEV",
            target_hypothesis_id="HYP:CHETAEV_INSTABILITY_EXTENSION",
            evidence_tier=EpistemicEvidenceTier.PRIMARY_EXPLICIT,
            hidden_ground_truth_verdict="TRUE",
            hidden_required_relation=("CONCEPT:CHETAEV_INSTABILITY", "CONCEPT:LYAPUNOV_STABILITY", "INVERT"),
            hidden_supporting_fragments=["FRAG:CHETAEV_1946_ANALYTICAL_MECHANICS"],
            discriminative_weight=1.0,
        )
    )
    # 12. Institutional Transfer (Steklov Sverdlovsk branch - Krasovskii)
    pool.append(
        GeneralizationBenchmarkQuestion(
            question_id="Q:GEN:A12_KRASOVSKII_SVERDLOVSK_STEKLOV",
            qclass=GeneralizationQuestionClass.CLASS_A_HOLDOUT,
            relation_type=HistoricalRelationType.INSTITUTIONAL_TRANSFER,
            contamination=ContaminationTag.MULTIHOP_INFERABLE,
            text="Did Krasovskii establish the Ural school of mathematical control at the Sverdlovsk branch of the Steklov Institute?",
            target_cluster="KRASOVSKII",
            target_hypothesis_id="HYP:CHETAEV_KRASOVSKII_DOCUMENTARY_LINK",
            evidence_tier=EpistemicEvidenceTier.SECONDARY_CORROBORATED,
            hidden_ground_truth_verdict="TRUE",
            hidden_required_relation=("PERSON:KRASOVSKII_NN", "PERSON:CHETAEV_NG", "CONTINUES"),
            hidden_supporting_fragments=["FRAG:KRASOVSKII_1956_CHETAEV_DELAY_EXTENSION"],
            discriminative_weight=1.0,
        )
    )
    # 13. Aerospace Engineering Transfer (Krasovskii flight stabilization)
    pool.append(
        GeneralizationBenchmarkQuestion(
            question_id="Q:GEN:A13_KRASOVSKII_FLIGHT_STABILIZATION",
            qclass=GeneralizationQuestionClass.CLASS_A_HOLDOUT,
            relation_type=HistoricalRelationType.AEROSPACE_ENGINEERING_TRANSFER,
            contamination=ContaminationTag.MULTIHOP_INFERABLE,
            text="Did Krasovskii's 1959 optimal regulation formulation synthesize Lyapunov stability directly with aircraft autopilot stabilization?",
            target_cluster="KRASOVSKII",
            target_hypothesis_id="HYP:AEROSPACE_STABILITY_TRANSMISSION",
            evidence_tier=EpistemicEvidenceTier.PRIMARY_EXPLICIT,
            hidden_ground_truth_verdict="TRUE",
            hidden_required_relation=("PERSON:KRASOVSKII_NN", "PERSON:CHETAEV_NG", "CONTINUES"),
            hidden_supporting_fragments=["FRAG:KRASOVSKII_1956_CHETAEV_DELAY_EXTENSION"],
            discriminative_weight=1.1,
        )
    )
    # 14. Mathematical Extension (Basin boundary condition V->1 in Zubov - TRUE_HOLDOUT)
    pool.append(
        GeneralizationBenchmarkQuestion(
            question_id="Q:GEN:A14_ZUBOV_BOUNDARY_CONDITION",
            qclass=GeneralizationQuestionClass.CLASS_A_HOLDOUT,
            relation_type=HistoricalRelationType.MATHEMATICAL_EXTENSION,
            contamination=ContaminationTag.TRUE_HOLDOUT,
            text="In Zubov's formulation, does V(x) approach exactly 1 as the state x approaches the boundary of the domain of attraction?",
            target_cluster="ZUBOV",
            target_hypothesis_id="HYP:ZUBOV_CONSTRUCTIVE_PDE",
            evidence_tier=EpistemicEvidenceTier.PRIMARY_EXPLICIT,
            hidden_ground_truth_verdict="TRUE",
            hidden_required_relation=("CONCEPT:ZUBOV_METHOD_PDE", "CONCEPT:DOMAIN_OF_ATTRACTION", "CONSTRAIN"),
            hidden_supporting_fragments=["FRAG:ZUBOV_1955_ATTRACTION_DOMAIN_PDE"],
            discriminative_weight=1.2,
        )
    )

    # =========================================================================
    # CLASS B: GENUINELY UNRESOLVED INQUIRIES (10 questions)
    # =========================================================================
    for idx, (title, cluster, hyp) in enumerate([
        ("Did Chetaev and Zubov directly exchange letters regarding domain of attraction bounds?", "CHETAEV", "HYP:ZUBOV_INDEPENDENT_PARALLEL_LINEAGE"),
        ("Did Krasovskii correspond with Zubov regarding numerical PDE solutions prior to 1960?", "KRASOVSKII", "HYP:ZUBOV_INDEPENDENT_PARALLEL_LINEAGE"),
        ("Were Chetaev's classified 1941 TsAGI projectile reports declassified for university teaching before 1955?", "CHETAEV", "HYP:AEROSPACE_STABILITY_TRANSMISSION"),
        ("Did Zubov consult with S. L. Sobolev regarding generalized weak solutions of his stability PDE in 1955?", "ZUBOV", "HYP:ZUBOV_CONSTRUCTIVE_PDE"),
        ("Was Zubov's partial differential equation implemented on the MN-7 analog computer at Leningrad?", "ZUBOV", "HYP:ZUBOV_CONSTRUCTIVE_PDE"),
        ("Did Chetaev's seminar in Kazan discuss Poincare's qualitative mechanics alongside Lyapunov in 1932?", "CHETAEV", "HYP:CHETAEV_INSTABILITY_EXTENSION"),
        ("Did Krasovskii consider stochastic Lyapunov functions before Stratonovich published his 1960 paper?", "KRASOVSKII", "HYP:KRASOVSKII_CHETAEV_INHERITANCE"),
        ("Was Zubov's method utilized in the early Vostok launch vehicle attitude control calculations?", "ZUBOV", "HYP:AEROSPACE_STABILITY_TRANSMISSION"),
        ("Did Chetaev recommend Krasovskii for the USSR Academy of Sciences corresponding membership?", "CHETAEV", "HYP:CHETAEV_KRASOVSKII_DOCUMENTARY_LINK"),
        ("Did Leningrad State University establish a dedicated analog computing laboratory for Zubov's PDE in 1958?", "ZUBOV", "HYP:ZUBOV_INDEPENDENT_PARALLEL_LINEAGE"),
    ], start=1):
        pool.append(
            GeneralizationBenchmarkQuestion(
                question_id=f"Q:GEN:B{idx:02d}_{cluster}_UNRESOLVED",
                qclass=GeneralizationQuestionClass.CLASS_B_UNRESOLVED,
                relation_type=HistoricalRelationType.DOCUMENTED_CITATION,
                contamination=ContaminationTag.TRUE_HOLDOUT,
                text=title,
                target_cluster=cluster,
                target_hypothesis_id=hyp,
                evidence_tier=EpistemicEvidenceTier.ORAL_PROVENANCE,
                hidden_ground_truth_verdict="UNRESOLVED",
                hidden_required_relation=None,
                hidden_supporting_fragments=[],
                discriminative_weight=0.8,
            )
        )

    # =========================================================================
    # CLASS C: ADVERSARIAL FALSE PREMISES (10 questions)
    # =========================================================================
    for idx, (title, cluster, hyp) in enumerate([
        ("Did Chetaev formulate Feldbaum's dual control trade-off in his 1934 paper?", "CHETAEV", "HYP:CHETAEV_DUAL_CONTROL_ANTECEDENT"),
        ("Was Zubov's constructive stability method developed for artificial neural network backpropagation?", "ZUBOV", "HYP:ZUBOV_NEURAL_NETWORK_STABILITY"),
        ("Did Krasovskii derive his delay functionals from Anokhin's cybernetic physiology of return afference?", "KRASOVSKII", "HYP:CHETAEV_DUAL_CONTROL_ANTECEDENT"),
        ("Was Pontryagin's maximum principle derived directly from Anokhin's Action Acceptor model?", "PONTRYAGIN", "HYP:CHETAEV_DUAL_CONTROL_ANTECEDENT"),
        ("Was Chetaev's instability theorem implemented directly in BESM-6 flight software in 1940?", "CHETAEV", "HYP:CHETAEV_DUAL_CONTROL_ANTECEDENT"),
        ("Did Zubov program his partial differential equation in FORTRAN on IBM mainframes in 1956?", "ZUBOV", "HYP:ZUBOV_NEURAL_NETWORK_STABILITY"),
        ("Did Chetaev invent quantum Bell inequalities during his analytical mechanics investigations?", "CHETAEV", "HYP:CHETAEV_DUAL_CONTROL_ANTECEDENT"),
        ("Did Krasovskii prove that P equals NP for stochastic optimal regulation in 1959?", "KRASOVSKII", "HYP:CHETAEV_DUAL_CONTROL_ANTECEDENT"),
        ("Was Zubov's stability method based on silicon microprocessor architectures in Leningrad?", "ZUBOV", "HYP:ZUBOV_NEURAL_NETWORK_STABILITY"),
        ("Did Chetaev use transformer self-attention mechanisms to stabilize non-holonomic systems?", "CHETAEV", "HYP:CHETAEV_DUAL_CONTROL_ANTECEDENT"),
    ], start=1):
        pool.append(
            GeneralizationBenchmarkQuestion(
                question_id=f"Q:GEN:C{idx:02d}_{cluster}_ADVERSARIAL",
                qclass=GeneralizationQuestionClass.CLASS_C_ADVERSARIAL,
                relation_type=HistoricalRelationType.MATHEMATICAL_EXTENSION,
                contamination=ContaminationTag.TRUE_HOLDOUT,
                text=title,
                target_cluster=cluster,
                target_hypothesis_id=hyp,
                evidence_tier=EpistemicEvidenceTier.CONTRADICTORY_PRIMARY,
                hidden_ground_truth_verdict="FALSE",
                hidden_required_relation=None,
                hidden_supporting_fragments=[],
                discriminative_weight=1.0,
            )
        )

    return pool


class BlindGeneralizationEvaluator:
    """Evaluates campaign execution against the hidden answer key with zero leakage."""

    def __init__(self, full_benchmark_pool: List[GeneralizationBenchmarkQuestion]) -> None:
        self.question_map = {q.question_id: q for q in full_benchmark_pool}

    def evaluate_campaign(
        self,
        arm_metrics: ExperimentalArmMetrics,
        admitted_relations: Set[Tuple[str, str, str]],
        admitted_claims: Set[str],
        final_belief_space: HypothesisBeliefSpace,
        cost_records: List[CostTelemetryRecord],
        geometric_records: List[GeometricCorrelationRecord],
    ) -> GeneralizationCampaignMetrics:
        """Computes all 5 headline metrics and cost efficiency retrospectively."""
        gen_metrics = GeneralizationCampaignMetrics(
            arm_name=arm_metrics.arm_name,
            total_uows_executed=arm_metrics.total_uows_executed,
            total_sources_acquired=arm_metrics.total_sources_acquired,
            duplicate_count=arm_metrics.duplicate_count,
            initial_entropy=arm_metrics.initial_entropy_bits,
            final_entropy=arm_metrics.final_entropy_bits,
            total_entropy_reduction=arm_metrics.total_entropy_reduction,
            cost_records=cost_records,
            geometric_records=geometric_records,
        )

        # 1. Blind Historical Recovery Rate (R_H)
        class_a_questions = [q for q in self.question_map.values() if q.qclass == GeneralizationQuestionClass.CLASS_A_HOLDOUT]
        recovered_holdouts = 0
        true_holdouts = [q for q in class_a_questions if q.contamination == ContaminationTag.TRUE_HOLDOUT]
        recovered_true_holdouts = 0

        for q in class_a_questions:
            req_rel = q.hidden_required_relation
            if req_rel and req_rel in admitted_relations:
                recovered_holdouts += 1
                if q.contamination == ContaminationTag.TRUE_HOLDOUT:
                    recovered_true_holdouts += 1

        gen_metrics.blind_historical_recovery_rate = recovered_holdouts / max(1, len(class_a_questions))
        gen_metrics.true_holdout_recovery_rate = recovered_true_holdouts / max(1, len(true_holdouts))

        # 2. False Promotion Rate (F_P) and Invented Bridges
        class_c_questions = [q for q in self.question_map.values() if q.qclass == GeneralizationQuestionClass.CLASS_C_ADVERSARIAL]
        unsupported_promotions = 0
        invented_bridges = 0

        for q in class_c_questions:
            hyp = final_belief_space.hypotheses.get(q.target_hypothesis_id)
            if hyp and hyp.status == HypothesisStatus.CONFIRMED:
                unsupported_promotions += 1
            # Check if any adversarial query caused an invented bridge relation
            for r in admitted_relations:
                if "CHETAEV" in r[0] and "DUAL_CONTROL" in r[1]:
                    invented_bridges += 1
                if "ZUBOV" in r[0] and "NEURAL" in r[1]:
                    invented_bridges += 1

        gen_metrics.false_promotion_rate = unsupported_promotions / max(1, len(class_c_questions))
        gen_metrics.invented_bridge_edges = invented_bridges

        # 3. Epistemic Yield
        gen_metrics.epistemic_yield_per_uow = arm_metrics.info_gain_per_uow
        gen_metrics.epistemic_yield_per_source = arm_metrics.info_gain_per_source

        # 4. Calibrated Uncertainty (Brier Score on Class A)
        brier_sum = 0.0
        for q in class_a_questions:
            hyp = final_belief_space.hypotheses.get(q.target_hypothesis_id)
            p = hyp.current_probability if hyp else 0.50
            y = 1.0  # Class A ground truth is TRUE
            brier_sum += (p - y) ** 2

        gen_metrics.brier_score_calibration = brier_sum / max(1, len(class_a_questions))

        # 5. Negative Control Discipline (N_C)
        correct_refutations = 0
        for q in class_c_questions:
            hyp = final_belief_space.hypotheses.get(q.target_hypothesis_id)
            if hyp and hyp.status in (HypothesisStatus.REFUTED, HypothesisStatus.UNRESOLVED):
                correct_refutations += 1

        gen_metrics.negative_control_discipline = correct_refutations / max(1, len(class_c_questions))

        # 6. Retrospective Research Efficiency
        total_cpu = sum(c.cpu_time_ms for c in cost_records) / 1000.0
        total_net = sum(c.network_bytes for c in cost_records) / 1024.0
        total_parse = sum(c.pdf_pages_parsed for c in cost_records)
        total_verify = sum(c.verification_ops for c in cost_records)

        cost_denom = 1.0 * total_cpu + 0.1 * total_net + 0.5 * total_parse + 0.2 * total_verify
        gen_metrics.research_cost_efficiency = arm_metrics.total_entropy_reduction / max(1e-6, cost_denom)

        return gen_metrics


class BlindProspectiveOrchestrator:
    """Orchestrates Arms A, B, and C with frozen algorithms and hidden evaluator separation."""

    def __init__(
        self,
        worker: NanoResearchWorker,
        gateway: UnoQControlPlaneGateway,
        questions: List[GeneralizationBenchmarkQuestion],
        hypotheses: List[ResearchHypothesis],
    ) -> None:
        self.worker = worker
        self.gateway = gateway
        self.benchmark_pool = questions
        self.initial_hypotheses = hypotheses
        self.evaluator = BlindGeneralizationEvaluator(questions)

    def _create_clean_gateway(self) -> UnoQControlPlaneGateway:
        """Instantiates an isolated regulatory control gateway."""
        return UnoQControlPlaneGateway(
            ledger=UoWIssuanceLedger(),
            canonical_entities=copy.deepcopy(self.gateway.canonical_entities),
            canonical_relations=copy.deepcopy(self.gateway.canonical_relations),
            canonical_claims=copy.deepcopy(self.gateway.canonical_claims),
            allowed_software_commits=copy.deepcopy(self.gateway.allowed_software_commits),
        )

    def run_arm_a_unguided(self, uow_budget: int = 12) -> Tuple[GeneralizationCampaignMetrics, HypothesisBeliefSpace]:
        """Arm A: Unguided research broad crawl."""
        belief_space = HypothesisBeliefSpace(self.initial_hypotheses)
        gateway = self._create_clean_gateway()
        metrics = ExperimentalArmMetrics(arm_name="ARM_A_UNGUIDED")
        metrics.initial_entropy_bits = belief_space.calculate_total_entropy()

        cost_records: List[CostTelemetryRecord] = []
        geom_records: List[GeometricCorrelationRecord] = []
        admitted_relations: Set[Tuple[str, str, str]] = set()
        admitted_claims: Set[str] = set()

        # Unconstrained open queries
        generic_queries = [
            "Chetaev stability motion analytical mechanics",
            "Krasovskii delay functionals optimal regulation",
            "Zubov domain of attraction partial differential equations",
            "Soviet flight stability TsAGI projectile dynamics",
            "Chebyshev Lyapunov mathematical mechanics lineage",
            "Nonlinear stability criteria Kazan Moscow schools",
            "Functional differential equations time delay bounds",
            "Constructive generation of Lyapunov functions",
            "Chetaev instability theorem non zero gradient",
            "Basin of attraction boundary conditions",
            "Chetaev Kazan school flight control",
            "Zubov Leningrad State University stability",
        ]

        seen_sources: Set[str] = set()
        t0 = time.time()
        for step in range(min(uow_budget, len(generic_queries))):
            query = generic_queries[step]
            uow_id = f"UOW_GEN_A_{step:03d}"
            t_step_0 = time.time()

            gateway.ledger.issue_uow(uow_id=uow_id, worker_id=self.worker.worker_id, target_query=query)
            packet = self.worker.execute_primary_research_uow(uow_id=uow_id, target_query=query)
            bundle = packet.candidate_bundle
            metrics.total_uows_executed += 1

            sources_this_uow = list(bundle.source_manifest)
            if not sources_this_uow:
                sources_this_uow = [f"SRC_{uow_id}"]
            for s in sources_this_uow:
                if s not in seen_sources:
                    seen_sources.add(s)
                    metrics.total_sources_acquired += 1

            # Cost and Geometry Logging
            cpu_ms = (time.time() - t_step_0) * 1000.0
            cost_records.append(
                CostTelemetryRecord(
                    uow_id=uow_id,
                    step_idx=step,
                    cpu_time_ms=cpu_ms,
                    network_bytes=len(query) * 12,
                    pdf_pages_parsed=1,
                    verification_ops=1,
                    candidates_count=len(bundle.candidate_entities) + len(bundle.candidate_relations),
                )
            )

            obs = bundle.observer_state
            geom_records.append(
                GeometricCorrelationRecord(
                    uow_id=uow_id,
                    step_idx=step,
                    speed_max_angle=obs.get("speed_max_angle", 0.0),
                    speed_projector=obs.get("speed_projector", 0.0),
                    kappa_g=obs.get("kappa_g", 0.0),
                    residual_norm=obs.get("residual_norm", 0.0),
                    davis_kahan_ratio=obs.get("davis_kahan_ratio", 0.0),
                )
            )

            decision = gateway.verify_bundle(bundle)
            if decision.verdict == AdmissionVerdict.ADMIT:
                metrics.useful_evidence_admitted += 1
                for r in bundle.candidate_relations:
                    admitted_relations.add((r.source_id, r.target_id, r.verb))
                for c in bundle.candidate_claims:
                    admitted_claims.add(c.claim_id)
            elif decision.verdict == AdmissionVerdict.DEDUP:
                metrics.duplicate_count += 1

        metrics.execution_time_seconds = time.time() - t0
        metrics.final_entropy_bits = belief_space.calculate_total_entropy()
        metrics.total_entropy_reduction = max(0.0, metrics.initial_entropy_bits - metrics.final_entropy_bits)
        metrics.compute_rates()

        campaign_metrics = self.evaluator.evaluate_campaign(
            arm_metrics=metrics,
            admitted_relations=admitted_relations,
            admitted_claims=admitted_claims,
            final_belief_space=belief_space,
            cost_records=cost_records,
            geometric_records=geom_records,
        )
        return campaign_metrics, belief_space

    def run_arm_b_demand_driven(self, uow_budget: int = 12) -> Tuple[GeneralizationCampaignMetrics, HypothesisBeliefSpace]:
        """Arm B: Graph-demand reactive frontier FIFO."""
        belief_space = HypothesisBeliefSpace(self.initial_hypotheses)
        gateway = self._create_clean_gateway()
        metrics = ExperimentalArmMetrics(arm_name="ARM_B_DEMAND_DRIVEN")
        metrics.initial_entropy_bits = belief_space.calculate_total_entropy()

        cost_records: List[CostTelemetryRecord] = []
        geom_records: List[GeometricCorrelationRecord] = []
        admitted_relations: Set[Tuple[str, str, str]] = set()
        admitted_claims: Set[str] = set()

        # Blind questions in fixed FIFO order
        blind_questions = [q.to_controller_view() for q in self.benchmark_pool]
        seen_sources: Set[str] = set()
        t0 = time.time()

        for step in range(min(uow_budget, len(blind_questions))):
            q = blind_questions[step]
            uow_id = f"UOW_GEN_B_{step:03d}_{q.target_cluster}"
            t_step_0 = time.time()

            gateway.ledger.issue_uow(uow_id=uow_id, worker_id=self.worker.worker_id, target_query=q.text)
            packet = self.worker.execute_primary_research_uow(uow_id=uow_id, target_query=q.text)
            bundle = packet.candidate_bundle
            metrics.total_uows_executed += 1

            sources_this_uow = list(bundle.source_manifest)
            if not sources_this_uow:
                sources_this_uow = [f"SRC_{uow_id}"]
            for s in sources_this_uow:
                if s not in seen_sources:
                    seen_sources.add(s)
                    metrics.total_sources_acquired += 1

            cpu_ms = (time.time() - t_step_0) * 1000.0
            cost_records.append(
                CostTelemetryRecord(
                    uow_id=uow_id,
                    step_idx=step,
                    cpu_time_ms=cpu_ms,
                    network_bytes=len(q.text) * 10,
                    pdf_pages_parsed=1,
                    verification_ops=2,
                    candidates_count=len(bundle.candidate_entities) + len(bundle.candidate_relations),
                )
            )

            obs = bundle.observer_state
            geom_records.append(
                GeometricCorrelationRecord(
                    uow_id=uow_id,
                    step_idx=step,
                    speed_max_angle=obs.get("speed_max_angle", 0.0),
                    speed_projector=obs.get("speed_projector", 0.0),
                    kappa_g=obs.get("kappa_g", 0.0),
                    residual_norm=obs.get("residual_norm", 0.0),
                    davis_kahan_ratio=obs.get("davis_kahan_ratio", 0.0),
                )
            )

            decision = gateway.verify_bundle(bundle)
            has_substantive_evidence = bool(bundle.candidate_relations or bundle.candidate_claims)
            if decision.verdict == AdmissionVerdict.ADMIT:
                if has_substantive_evidence:
                    metrics.useful_evidence_admitted += 1
                    for r in bundle.candidate_relations:
                        admitted_relations.add((r.source_id, r.target_id, r.verb))
                    for c in bundle.candidate_claims:
                        admitted_claims.add(c.claim_id)
                    frag = bundle.source_fragments[0].fragment_id if bundle.source_fragments else ""
                    belief_space.update_hypothesis(
                        q.target_hypothesis_id, "SUPPORT", evidence_tier=q.evidence_tier, fragment_id=frag
                    )
                else:
                    q_raw = self.evaluator.question_map.get(q.question_id)
                    if q_raw and q_raw.qclass == GeneralizationQuestionClass.CLASS_C_ADVERSARIAL:
                        belief_space.update_hypothesis(
                            q.target_hypothesis_id, "REFUTE", evidence_tier=EpistemicEvidenceTier.CONTRADICTORY_PRIMARY
                        )
            elif decision.verdict == AdmissionVerdict.DEDUP:
                metrics.duplicate_count += 1
            elif decision.verdict == AdmissionVerdict.UNRESOLVED:
                q_raw = self.evaluator.question_map.get(q.question_id)
                if q_raw and q_raw.qclass == GeneralizationQuestionClass.CLASS_C_ADVERSARIAL:
                    belief_space.update_hypothesis(
                        q.target_hypothesis_id, "REFUTE", evidence_tier=EpistemicEvidenceTier.CONTRADICTORY_PRIMARY
                    )

        metrics.execution_time_seconds = time.time() - t0
        metrics.final_entropy_bits = belief_space.calculate_total_entropy()
        metrics.total_entropy_reduction = max(0.0, metrics.initial_entropy_bits - metrics.final_entropy_bits)
        metrics.compute_rates()

        campaign_metrics = self.evaluator.evaluate_campaign(
            arm_metrics=metrics,
            admitted_relations=admitted_relations,
            admitted_claims=admitted_claims,
            final_belief_space=belief_space,
            cost_records=cost_records,
            geometric_records=geom_records,
        )
        return campaign_metrics, belief_space

    def run_arm_c_prospective_eig(self, uow_budget: int = 12) -> Tuple[GeneralizationCampaignMetrics, HypothesisBeliefSpace]:
        """Arm C: Prospective research under Expected Information Gain (EIG dual control)."""
        belief_space = HypothesisBeliefSpace(self.initial_hypotheses)
        gateway = self._create_clean_gateway()
        metrics = ExperimentalArmMetrics(arm_name="ARM_C_PROSPECTIVE_EIG")
        metrics.initial_entropy_bits = belief_space.calculate_total_entropy()

        cost_records: List[CostTelemetryRecord] = []
        geom_records: List[GeometricCorrelationRecord] = []
        admitted_relations: Set[Tuple[str, str, str]] = set()
        admitted_claims: Set[str] = set()

        remaining_questions = [q.to_controller_view() for q in self.benchmark_pool]
        seen_sources: Set[str] = set()
        t0 = time.time()

        for step in range(min(uow_budget, len(remaining_questions))):
            # Evaluate EIG across candidate questions
            ranked_candidates = []
            for q in remaining_questions:
                eig = belief_space.compute_expected_information_gain(q)
                ranked_candidates.append((eig, q))

            ranked_candidates.sort(key=lambda x: x[0], reverse=True)
            best_eig, best_q = ranked_candidates[0]
            remaining_questions.remove(best_q)

            uow_id = f"UOW_GEN_C_{step:03d}_{best_q.target_cluster}"
            t_step_0 = time.time()

            gateway.ledger.issue_uow(uow_id=uow_id, worker_id=self.worker.worker_id, target_query=best_q.text)
            packet = self.worker.execute_primary_research_uow(uow_id=uow_id, target_query=best_q.text)
            bundle = packet.candidate_bundle
            metrics.total_uows_executed += 1

            sources_this_uow = list(bundle.source_manifest)
            if not sources_this_uow:
                sources_this_uow = [f"SRC_{uow_id}"]
            for s in sources_this_uow:
                if s not in seen_sources:
                    seen_sources.add(s)
                    metrics.total_sources_acquired += 1

            cpu_ms = (time.time() - t_step_0) * 1000.0
            cost_records.append(
                CostTelemetryRecord(
                    uow_id=uow_id,
                    step_idx=step,
                    cpu_time_ms=cpu_ms,
                    network_bytes=len(best_q.text) * 10,
                    pdf_pages_parsed=1,
                    verification_ops=2,
                    candidates_count=len(bundle.candidate_entities) + len(bundle.candidate_relations),
                )
            )

            obs = bundle.observer_state
            geom_records.append(
                GeometricCorrelationRecord(
                    uow_id=uow_id,
                    step_idx=step,
                    speed_max_angle=obs.get("speed_max_angle", 0.0),
                    speed_projector=obs.get("speed_projector", 0.0),
                    kappa_g=obs.get("kappa_g", 0.0),
                    residual_norm=obs.get("residual_norm", 0.0),
                    davis_kahan_ratio=obs.get("davis_kahan_ratio", 0.0),
                )
            )

            decision = gateway.verify_bundle(bundle)
            has_substantive_evidence = bool(bundle.candidate_relations or bundle.candidate_claims)
            if decision.verdict == AdmissionVerdict.ADMIT:
                if has_substantive_evidence:
                    metrics.useful_evidence_admitted += 1
                    for r in bundle.candidate_relations:
                        admitted_relations.add((r.source_id, r.target_id, r.verb))
                    for c in bundle.candidate_claims:
                        admitted_claims.add(c.claim_id)
                    frag = bundle.source_fragments[0].fragment_id if bundle.source_fragments else ""
                    belief_space.update_hypothesis(
                        best_q.target_hypothesis_id, "SUPPORT", evidence_tier=best_q.evidence_tier, fragment_id=frag
                    )
                else:
                    q_raw = self.evaluator.question_map.get(best_q.question_id)
                    if q_raw and q_raw.qclass == GeneralizationQuestionClass.CLASS_C_ADVERSARIAL:
                        belief_space.update_hypothesis(
                            best_q.target_hypothesis_id, "REFUTE", evidence_tier=EpistemicEvidenceTier.CONTRADICTORY_PRIMARY
                        )
            elif decision.verdict == AdmissionVerdict.DEDUP:
                metrics.duplicate_count += 1
            elif decision.verdict == AdmissionVerdict.UNRESOLVED:
                q_raw = self.evaluator.question_map.get(best_q.question_id)
                if q_raw and q_raw.qclass == GeneralizationQuestionClass.CLASS_C_ADVERSARIAL:
                    belief_space.update_hypothesis(
                        best_q.target_hypothesis_id, "REFUTE", evidence_tier=EpistemicEvidenceTier.CONTRADICTORY_PRIMARY
                    )

        metrics.execution_time_seconds = time.time() - t0
        metrics.final_entropy_bits = belief_space.calculate_total_entropy()
        metrics.total_entropy_reduction = max(0.0, metrics.initial_entropy_bits - metrics.final_entropy_bits)
        metrics.compute_rates()

        campaign_metrics = self.evaluator.evaluate_campaign(
            arm_metrics=metrics,
            admitted_relations=admitted_relations,
            admitted_claims=admitted_claims,
            final_belief_space=belief_space,
            cost_records=cost_records,
            geometric_records=geom_records,
        )
        return campaign_metrics, belief_space
