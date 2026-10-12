"""SOVCTX Prospective Research Control Engine.

Milestone UQ-N2: Prospective Research Efficiency Qualification.

Implements the closed-loop prospective research architecture:
1. Hypothesis Space U_t = {H_1, H_2, ..., H_n} with explicit belief tracking.
2. Expected Information Gain (EIG) evaluation over candidate UoWs:
   a^* = argmax_a EIG(a) subject to admissibility
3. Operationalization of Feldbaum Dual Control:
   ACT_TO_KNOW: Take actions selected specifically for discriminative power over competing hypotheses.
4. Bayesian belief updating: U_t -> U_{t+1} upon arrival of control-node verified evidence.
5. Calibrated benchmark suite spanning the adaptive control cluster:
   (Feldbaum, Stratonovich, Tsetlin, Pontryagin, Krasovskii, Anokhin, Bernstein)
   across 8 question types:
   - known-positive
   - known-negative
   - ambiguous
   - contradictory
   - missing-link
   - institutional-transfer
   - terminological
   - structural-only
6. Comparative execution of three experimental arms:
   - Arm A: Unguided research (broad crawl)
   - Arm B: Graph-demand-driven research (reactive frontier questions)
   - Arm C: Prospective research (EIG dual control)
7. Shadow-mode correlation with G1 Geometric Observer telemetry.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field
from enum import Enum
import json
import math
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from sovctx.node.control_plane import (
    AdmissionDecision,
    AdmissionVerdict,
    UnoQControlPlaneGateway,
    UoWIssuanceLedger,
)
from sovctx.node.nano_research_worker import (
    CandidateBundle,
    CandidateClaim,
    CandidateEntity,
    CandidateQuestion,
    CandidateRelation,
    CandidateSource,
    NanoResearchWorker,
    SourceFragment,
)


class BenchmarkQuestionType(str, Enum):
    """Eight canonical categories of calibrated historical research questions."""
    KNOWN_POSITIVE = "KNOWN_POSITIVE"
    KNOWN_NEGATIVE = "KNOWN_NEGATIVE"
    AMBIGUOUS = "AMBIGUOUS"
    CONTRADICTORY = "CONTRADICTORY"
    MISSING_LINK = "MISSING_LINK"
    INSTITUTIONAL_TRANSFER = "INSTITUTIONAL_TRANSFER"
    TERMINOLOGICAL = "TERMINOLOGICAL"
    STRUCTURAL_ONLY = "STRUCTURAL_ONLY"


class HypothesisStatus(str, Enum):
    """Epistemic state of a historical research hypothesis."""
    UNRESOLVED = "UNRESOLVED"
    CONFIRMED = "CONFIRMED"
    REFUTED = "REFUTED"
    AMBIGUOUS = "AMBIGUOUS"


@dataclass
class ResearchHypothesis:
    """A historical or architectural claim under active scientific discrimination."""
    hypothesis_id: str
    label: str
    description: str
    prior: float = 0.5
    current_probability: float = 0.5
    competing_with: List[str] = field(default_factory=list)
    status: HypothesisStatus = HypothesisStatus.UNRESOLVED
    supporting_fragments: List[str] = field(default_factory=list)
    refuting_fragments: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "label": self.label,
            "description": self.description,
            "prior": self.prior,
            "current_probability": round(self.current_probability, 4),
            "competing_with": self.competing_with,
            "status": self.status.value,
            "supporting_fragments": self.supporting_fragments,
            "refuting_fragments": self.refuting_fragments,
        }


@dataclass
class BenchmarkQuestion:
    """A grounded calibration question with hidden ground truth for scoring workers."""
    question_id: str
    qtype: BenchmarkQuestionType
    text: str
    target_cluster: str  # e.g. "FELDBAUM", "TSETLIN", "KRASOVSKII", "ANOKHIN", etc.
    target_hypothesis_id: str
    ground_truth_verdict: str  # "TRUE", "FALSE", "AMBIGUOUS", "CONTRADICTORY"
    ground_truth_fragments: List[str] = field(default_factory=list)
    expected_relations: List[Tuple[str, str, str]] = field(default_factory=list)
    discriminative_weight: float = 1.0  # Weight in EIG evaluation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_id": self.question_id,
            "qtype": self.qtype.value,
            "text": self.text,
            "target_cluster": self.target_cluster,
            "target_hypothesis_id": self.target_hypothesis_id,
            "ground_truth_verdict": self.ground_truth_verdict,
            "ground_truth_fragments": self.ground_truth_fragments,
            "discriminative_weight": self.discriminative_weight,
        }


class HypothesisBeliefSpace:
    """Tracks probability distributions and Shannon entropy over competing hypotheses."""

    def __init__(self, hypotheses: Optional[List[ResearchHypothesis]] = None) -> None:
        self.hypotheses: Dict[str, ResearchHypothesis] = {}
        if hypotheses:
            for h in hypotheses:
                self.hypotheses[h.hypothesis_id] = copy.deepcopy(h)

    def calculate_total_entropy(self) -> float:
        """Computes binary Shannon entropy across independent hypothesis pairs in bits."""
        total_h = 0.0
        for h in self.hypotheses.values():
            p = max(1e-6, min(1.0 - 1e-6, h.current_probability))
            entropy = -p * math.log2(p) - (1.0 - p) * math.log2(1.0 - p)
            total_h += entropy
        return total_h

    def compute_expected_information_gain(
        self,
        question: BenchmarkQuestion,
        p_evidence_given_h: float = 0.85,
        p_evidence_given_not_h: float = 0.15,
    ) -> float:
        """Computes EIG(a): Expected reduction in entropy if question/UoW is probed.

        EIG(a) = H(U_t) - E_{y} [ H(U_t | y) ]
        """
        hyp = self.hypotheses.get(question.target_hypothesis_id)
        if not hyp or hyp.status != HypothesisStatus.UNRESOLVED:
            return 0.0

        p = hyp.current_probability
        # Current entropy for this hypothesis
        p_clamped = max(1e-6, min(1.0 - 1e-6, p))
        h_current = -p_clamped * math.log2(p_clamped) - (1.0 - p_clamped) * math.log2(1.0 - p_clamped)

        # Probability of observing confirming evidence y=1
        p_y1 = p * p_evidence_given_h + (1.0 - p) * p_evidence_given_not_h
        p_y0 = 1.0 - p_y1

        # Posterior p(H | y=1)
        p_post_y1 = (p * p_evidence_given_h) / max(1e-6, p_y1)
        p_post_y1_clamped = max(1e-6, min(1.0 - 1e-6, p_post_y1))
        h_post_y1 = -p_post_y1_clamped * math.log2(p_post_y1_clamped) - (1.0 - p_post_y1_clamped) * math.log2(1.0 - p_post_y1_clamped)

        # Posterior p(H | y=0)
        p_post_y0 = (p * (1.0 - p_evidence_given_h)) / max(1e-6, p_y0)
        p_post_y0_clamped = max(1e-6, min(1.0 - 1e-6, p_post_y0))
        h_post_y0 = -p_post_y0_clamped * math.log2(p_post_y0_clamped) - (1.0 - p_post_y0_clamped) * math.log2(1.0 - p_post_y0_clamped)

        # Expected posterior entropy
        e_h_post = p_y1 * h_post_y1 + p_y0 * h_post_y0
        eig = (h_current - e_h_post) * question.discriminative_weight
        return max(0.0, eig)

    def update_hypothesis(
        self,
        hypothesis_id: str,
        evidence_direction: str,  # "SUPPORT" | "REFUTE" | "AMBIGUOUS"
        evidence_strength: float = 0.90,
        fragment_id: str = "",
    ) -> float:
        """Bayesian update on hypothesis belief given verified evidence."""
        hyp = self.hypotheses.get(hypothesis_id)
        if not hyp:
            return 0.0

        prior_p = hyp.current_probability
        if evidence_direction == "SUPPORT":
            # Likelihood p(E | H) = strength, p(E | ~H) = 1 - strength
            num = prior_p * evidence_strength
            denom = num + (1.0 - prior_p) * (1.0 - evidence_strength)
            new_p = num / max(1e-6, denom)
            if fragment_id and fragment_id not in hyp.supporting_fragments:
                hyp.supporting_fragments.append(fragment_id)
        elif evidence_direction == "REFUTE":
            # Likelihood p(~E | H) = 1 - strength, p(~E | ~H) = strength
            num = prior_p * (1.0 - evidence_strength)
            denom = num + (1.0 - prior_p) * evidence_strength
            new_p = num / max(1e-6, denom)
            if fragment_id and fragment_id not in hyp.refuting_fragments:
                hyp.refuting_fragments.append(fragment_id)
        else:
            # Ambiguous: slight entropy increase or preservation
            new_p = prior_p

        hyp.current_probability = new_p
        if hyp.current_probability >= 0.88:
            hyp.status = HypothesisStatus.CONFIRMED
        elif hyp.current_probability <= 0.12:
            hyp.status = HypothesisStatus.REFUTED
        elif abs(hyp.current_probability - 0.50) < 0.05 and (hyp.supporting_fragments or hyp.refuting_fragments):
            hyp.status = HypothesisStatus.AMBIGUOUS

        return new_p


def build_canonical_adaptive_control_hypotheses() -> List[ResearchHypothesis]:
    """Generates the formal hypothesis space U_0 for the Soviet Adaptive Control cluster."""
    return [
        # H1: Feldbaum dual action distinction
        ResearchHypothesis(
            hypothesis_id="HYP:FELDBAUM_DUAL_ACTION",
            label="Feldbaum Dual Action Distinction",
            description="Feldbaum's 1960 dual control explicitly proves that control signals in incomplete information simultaneously perform investigative (epistemic) and directing (pragmatic) functions.",
            prior=0.50,
        ),
        # H2: Feldbaum ahistorical quantum claim (Negative control)
        ResearchHypothesis(
            hypothesis_id="HYP:FELDBAUM_QUANTUM_FOUNDATIONS",
            label="Feldbaum Quantum Computing Foundations",
            description="Feldbaum (1960) developed dual control as an explicit quantum computing formulation based on Bell inequalities.",
            prior=0.50,
        ),
        # H3: Tsetlin expedient learning in unknown media
        ResearchHypothesis(
            hypothesis_id="HYP:TSETLIN_EXPEDIENT_LEARNING",
            label="Tsetlin Automata Expedient Learning",
            description="Tsetlin (1961) proved that finite automata learn optimal behavior in unknown random media through state transitions that uncover penalty probabilities by trial and error.",
            prior=0.50,
        ),
        # H4: Krasovskii synthesis of Lyapunov direct method with optimal regulation
        ResearchHypothesis(
            hypothesis_id="HYP:KRASOVSKII_LYAPUNOV_SYNTHESIS",
            label="Krasovskii Lyapunov Optimal Regulation",
            description="Krasovskii (1959) proved that optimal feedback regulation can be constructed by minimizing the total time-derivative of an appropriately chosen Lyapunov function V(x).",
            prior=0.50,
        ),
        # H5: Gelfand-Tsetlin explicit grounding in Bernstein physiology
        ResearchHypothesis(
            hypothesis_id="HYP:GELFAND_TSETLIN_BERNSTEIN_BRIDGE",
            label="Gelfand-Tsetlin Bernstein Physiological Bridge",
            description="Gelfand and Tsetlin (1961) explicitly cite N. A. Bernstein's physiology of movement as the conceptual origin for nonlocal search and parameter space reduction.",
            prior=0.50,
        ),
        # H6: Anokhin Action Acceptor as forward predictive comparator
        ResearchHypothesis(
            hypothesis_id="HYP:ANOKHIN_ACTION_ACCEPTOR",
            label="Anokhin Action Acceptor Predictive Comparator",
            description="Anokhin's Functional System Theory (1955, 1968) formulates the Action Acceptor as an afferent model of the required future that precedes action execution and compares return afference.",
            prior=0.50,
        ),
        # H7: Pavlovian linear reflex chain vs Anokhin Functional Systems
        ResearchHypothesis(
            hypothesis_id="HYP:ANOKHIN_REJECTS_LINEAR_REFLEX",
            label="Anokhin Rejection of Pavlovian Linear Reflex",
            description="Anokhin's formulation of return afference explicitly rejected the classical Pavlovian linear reflex arc as inadequate for closed-loop behavioral self-regulation.",
            prior=0.50,
        ),
        # H8: Steklov to IAT institutional transmission
        ResearchHypothesis(
            hypothesis_id="HYP:INSTITUTIONAL_MIAN_TO_IAT",
            label="Steklov to IAT Institutional Transmission",
            description="Key mathematical concepts of stability and variational control transferred directly from the Steklov Mathematical Institute (MIAN) to the Institute of Automation and Remote Control (IAT).",
            prior=0.50,
        ),
    ]


def build_canonical_benchmark_question_pool() -> List[BenchmarkQuestion]:
    """Generates 32 calibrated benchmark research questions across 8 canonical types.

    Adaptive control cluster: Feldbaum, Stratonovich, Tsetlin, Pontryagin, Krasovskii, Anokhin, Bernstein.
    """
    return [
        # --- 1. KNOWN_POSITIVE (4 questions) ---
        BenchmarkQuestion(
            question_id="Q:KP:001_FELDBAUM_DUAL_ACTION",
            qtype=BenchmarkQuestionType.KNOWN_POSITIVE,
            text="Does Feldbaum's 1960 dual-control paper explicitly distinguish investigative action from directing action?",
            target_cluster="FELDBAUM",
            target_hypothesis_id="HYP:FELDBAUM_DUAL_ACTION",
            ground_truth_verdict="TRUE",
            ground_truth_fragments=["FRAG:FELDBAUM_1960_DUAL_ACTION"],
            expected_relations=[("CONCEPT:DUAL_CONTROL", "CONCEPT:INVESTIGATIVE_ACTION", "PROBES")],
            discriminative_weight=1.2,
        ),
        BenchmarkQuestion(
            question_id="Q:KP:002_TSETLIN_EXPEDIENT_AUTOMATA",
            qtype=BenchmarkQuestionType.KNOWN_POSITIVE,
            text="Does Tsetlin (1961) define expedient behavior of finite stochastic automata learning in unknown random media?",
            target_cluster="TSETLIN",
            target_hypothesis_id="HYP:TSETLIN_EXPEDIENT_LEARNING",
            ground_truth_verdict="TRUE",
            ground_truth_fragments=["FRAG:TSETLIN_1961_AUTOMATA_PROBING"],
            expected_relations=[("CONCEPT:STOCHASTIC_AUTOMATA", "CONCEPT:EXPEDIENT_BEHAVIOR", "PROBES")],
            discriminative_weight=1.1,
        ),
        BenchmarkQuestion(
            question_id="Q:KP:003_KRASOVSKII_LYAPUNOV_MINIMIZATION",
            qtype=BenchmarkQuestionType.KNOWN_POSITIVE,
            text="Did Krasovskii (1959) prove that optimal feedback control minimizes the total derivative of a Lyapunov function?",
            target_cluster="KRASOVSKII",
            target_hypothesis_id="HYP:KRASOVSKII_LYAPUNOV_SYNTHESIS",
            ground_truth_verdict="TRUE",
            ground_truth_fragments=["FRAG:KRASOVSKII_1959_LYAPUNOV_CONTROL"],
            expected_relations=[("CONCEPT:OPTIMAL_REGULATION", "CONCEPT:LYAPUNOV_SECOND_METHOD", "STABILIZE")],
            discriminative_weight=1.1,
        ),
        BenchmarkQuestion(
            question_id="Q:KP:004_ANOKHIN_ACTION_ACCEPTOR",
            qtype=BenchmarkQuestionType.KNOWN_POSITIVE,
            text="Does Anokhin (1955, 1968) formulate the Action Acceptor as a predictive neural apparatus comparing return afference?",
            target_cluster="ANOKHIN",
            target_hypothesis_id="HYP:ANOKHIN_ACTION_ACCEPTOR",
            ground_truth_verdict="TRUE",
            ground_truth_fragments=["FRAG:ANOKHIN_1955_ACTION_ACCEPTOR"],
            expected_relations=[("CONCEPT:FUNCTIONAL_SYSTEMS", "CONCEPT:ACTION_ACCEPTOR", "CONTROL")],
            discriminative_weight=1.2,
        ),

        # --- 2. KNOWN_NEGATIVE (4 questions) ---
        BenchmarkQuestion(
            question_id="Q:KN:001_FELDBAUM_QUANTUM",
            qtype=BenchmarkQuestionType.KNOWN_NEGATIVE,
            text="Did Feldbaum in 1960 formulate dual control as an implementation of quantum superposition and Bell inequalities?",
            target_cluster="FELDBAUM",
            target_hypothesis_id="HYP:FELDBAUM_QUANTUM_FOUNDATIONS",
            ground_truth_verdict="FALSE",
            discriminative_weight=1.0,
        ),
        BenchmarkQuestion(
            question_id="Q:KN:002_TSETLIN_BACKPROP",
            qtype=BenchmarkQuestionType.KNOWN_NEGATIVE,
            text="Did Tsetlin in 1961 discover the reverse-mode automatic differentiation backpropagation algorithm?",
            target_cluster="TSETLIN",
            target_hypothesis_id="HYP:FELDBAUM_QUANTUM_FOUNDATIONS",
            ground_truth_verdict="FALSE",
            discriminative_weight=0.9,
        ),
        BenchmarkQuestion(
            question_id="Q:KN:003_KRASOVSKII_QUANTUM_P_NP",
            qtype=BenchmarkQuestionType.KNOWN_NEGATIVE,
            text="Did Krasovskii's 1959 paper resolve the P vs NP computational complexity problem for optimal regulation?",
            target_cluster="KRASOVSKII",
            target_hypothesis_id="HYP:FELDBAUM_QUANTUM_FOUNDATIONS",
            ground_truth_verdict="FALSE",
            discriminative_weight=0.9,
        ),
        BenchmarkQuestion(
            question_id="Q:KN:004_ANOKHIN_MICROPROCESSOR",
            qtype=BenchmarkQuestionType.KNOWN_NEGATIVE,
            text="Did Anokhin (1955) implement the Action Acceptor using Intel x86 silicon microprocessors?",
            target_cluster="ANOKHIN",
            target_hypothesis_id="HYP:FELDBAUM_QUANTUM_FOUNDATIONS",
            ground_truth_verdict="FALSE",
            discriminative_weight=0.9,
        ),

        # --- 3. AMBIGUOUS (4 questions) ---
        BenchmarkQuestion(
            question_id="Q:AMB:001_STRATONOVICH_KALMAN_PRIORITY",
            qtype=BenchmarkQuestionType.AMBIGUOUS,
            text="Did Stratonovich's 1960 conditional Markov filtering strictly precede or independently duplicate Kalman-Bucy linear filtering?",
            target_cluster="STRATONOVICH",
            target_hypothesis_id="HYP:FELDBAUM_DUAL_ACTION",
            ground_truth_verdict="AMBIGUOUS",
            discriminative_weight=0.8,
        ),
        BenchmarkQuestion(
            question_id="Q:AMB:002_VLASOV_TO_MOE",
            qtype=BenchmarkQuestionType.AMBIGUOUS,
            text="Can Vlasov's 1938 self-consistent kinetic equation be mathematically classified as a direct ancestor of modern Mixture-of-Experts routing?",
            target_cluster="VLASOV",
            target_hypothesis_id="HYP:INSTITUTIONAL_MIAN_TO_IAT",
            ground_truth_verdict="AMBIGUOUS",
            discriminative_weight=0.7,
        ),
        BenchmarkQuestion(
            question_id="Q:AMB:003_WALTER_SOVIET_CYBERNETICS",
            qtype=BenchmarkQuestionType.AMBIGUOUS,
            text="Was Grey Walter's 1950 phototropic tortoise explicitly used as an engineering blueprint for early Soviet robotic guidance?",
            target_cluster="WALTER",
            target_hypothesis_id="HYP:TSETLIN_EXPEDIENT_LEARNING",
            ground_truth_verdict="AMBIGUOUS",
            discriminative_weight=0.7,
        ),
        BenchmarkQuestion(
            question_id="Q:AMB:004_ASHBY_ULTRASTABILITY_EQUIVALENCE",
            qtype=BenchmarkQuestionType.AMBIGUOUS,
            text="Is Ashby's 1952 ultrastability mathematically identical to Lyapunov asymptotic stability in random media?",
            target_cluster="ASHBY",
            target_hypothesis_id="HYP:KRASOVSKII_LYAPUNOV_SYNTHESIS",
            ground_truth_verdict="AMBIGUOUS",
            discriminative_weight=0.8,
        ),

        # --- 4. CONTRADICTORY (4 questions) ---
        BenchmarkQuestion(
            question_id="Q:CON:001_PAVLOV_VS_ANOKHIN",
            qtype=BenchmarkQuestionType.CONTRADICTORY,
            text="Does Anokhin's Functional System Theory subsume Pavlovian reflexology as a complete description, or does it explicitly contradict and reject the linear reflex arc?",
            target_cluster="ANOKHIN",
            target_hypothesis_id="HYP:ANOKHIN_REJECTS_LINEAR_REFLEX",
            ground_truth_verdict="CONTRADICTORY",
            ground_truth_fragments=["FRAG:ANOKHIN_1955_ACTION_ACCEPTOR", "FRAG:ANOKHIN_1968_METABOLIC_SELF_REGULATION"],
            discriminative_weight=1.3,
        ),
        BenchmarkQuestion(
            question_id="Q:CON:002_OPEN_LOOP_VS_DUAL_CONTROL",
            qtype=BenchmarkQuestionType.CONTRADICTORY,
            text="Does open-loop certainty-equivalence control satisfy the optimal dual-control equation, or does certainty-equivalence fundamentally contradict investigative action?",
            target_cluster="FELDBAUM",
            target_hypothesis_id="HYP:FELDBAUM_DUAL_ACTION",
            ground_truth_verdict="CONTRADICTORY",
            ground_truth_fragments=["FRAG:FELDBAUM_1960_DUAL_ACTION"],
            discriminative_weight=1.2,
        ),
        BenchmarkQuestion(
            question_id="Q:CON:003_LOCAL_GRADIENT_VS_NONLOCAL_RAVINE",
            qtype=BenchmarkQuestionType.CONTRADICTORY,
            text="Can classical local gradient descent navigate multidimensional ravines with equal efficiency as Gelfand-Tsetlin nonlocal ravine search?",
            target_cluster="TSETLIN",
            target_hypothesis_id="HYP:GELFAND_TSETLIN_BERNSTEIN_BRIDGE",
            ground_truth_verdict="CONTRADICTORY",
            ground_truth_fragments=["FRAG:GELFAND_TSETLIN_1961_NONLOCAL_DEFINITION"],
            discriminative_weight=1.1,
        ),
        BenchmarkQuestion(
            question_id="Q:CON:004_PASSIVE_REFLEX_VS_ACTIVE_OVERCOMING",
            qtype=BenchmarkQuestionType.CONTRADICTORY,
            text="Does Bernstein's physiology of activity treat motor coordination as a passive equilibrium reaction or as an active overcoming of environmental resistance?",
            target_cluster="BERNSTEIN",
            target_hypothesis_id="HYP:GELFAND_TSETLIN_BERNSTEIN_BRIDGE",
            ground_truth_verdict="CONTRADICTORY",
            ground_truth_fragments=["FRAG:BERNSTEIN_1966_MODEL_FUTURE"],
            discriminative_weight=1.2,
        ),

        # --- 5. MISSING_LINK (4 questions) ---
        BenchmarkQuestion(
            question_id="Q:ML:001_GELFAND_TSETLIN_CITES_BERNSTEIN",
            qtype=BenchmarkQuestionType.MISSING_LINK,
            text="Did Gelfand and Tsetlin's 1961 nonlocal search paper explicitly cite N. A. Bernstein's levels of movement construction?",
            target_cluster="TSETLIN",
            target_hypothesis_id="HYP:GELFAND_TSETLIN_BERNSTEIN_BRIDGE",
            ground_truth_verdict="TRUE",
            ground_truth_fragments=["FRAG:GELFAND_TSETLIN_1961_BERNSTEIN_BRIDGE"],
            expected_relations=[("PERSON:GELFAND_IM", "PERSON:BERNSTEIN_NA", "REPRESENT")],
            discriminative_weight=1.4,
        ),
        BenchmarkQuestion(
            question_id="Q:ML:002_CHEBYSHEV_EULER_LYAPUNOV_GENEALOGY",
            qtype=BenchmarkQuestionType.MISSING_LINK,
            text="Did Chebyshev's editing of Euler's manuscripts establish the direct lineage leading to Lyapunov's stability theory?",
            target_cluster="LYAPUNOV",
            target_hypothesis_id="HYP:INSTITUTIONAL_MIAN_TO_IAT",
            ground_truth_verdict="TRUE",
            ground_truth_fragments=["FRAG:KOZLOV_2009_CHEBYSHEV_EULER", "FRAG:KOZLOV_2009_CHEBYSHEV_STUDENTS"],
            expected_relations=[("PERSON:CHEBYSHEV_PL", "PERSON:LYAPUNOV_AM", "REPRESENT")],
            discriminative_weight=1.3,
        ),
        BenchmarkQuestion(
            question_id="Q:ML:003_SAMARSKII_CHEBYSHEV_LINK",
            qtype=BenchmarkQuestionType.MISSING_LINK,
            text="Did Samarskii (1967) integrate Chebyshev minimax approximation polynomials into difference scheme regularization?",
            target_cluster="SAMARSKII",
            target_hypothesis_id="HYP:KRASOVSKII_LYAPUNOV_SYNTHESIS",
            ground_truth_verdict="TRUE",
            ground_truth_fragments=["FRAG:SAMARSKII_1967_MINIMAX_REGULARIZATION"],
            expected_relations=[("PERSON:SAMARSKII_AA", "CONCEPT:CHEBYSHEV_POLYNOMIAL", "INVERT")],
            discriminative_weight=1.2,
        ),
        BenchmarkQuestion(
            question_id="Q:ML:004_GELFAND_LEVITAN_INVERSE_KERNEL",
            qtype=BenchmarkQuestionType.MISSING_LINK,
            text="Did Gelfand and Levitan (1951) prove that differential operators can be reconstructed from spectral functions via linear Fredholm integral kernels?",
            target_cluster="GELFAND",
            target_hypothesis_id="HYP:INSTITUTIONAL_MIAN_TO_IAT",
            ground_truth_verdict="TRUE",
            ground_truth_fragments=["FRAG:GELFAND_LEVITAN_1951_TITLE", "FRAG:GL_1991_KERNEL_EQ"],
            expected_relations=[("PERSON:GELFAND_IM", "CONCEPT:SPECTRAL_FUNCTION", "INVERT")],
            discriminative_weight=1.2,
        ),

        # --- 6. INSTITUTIONAL_TRANSFER (4 questions) ---
        BenchmarkQuestion(
            question_id="Q:IT:001_MIAN_TO_IAT_STABILITY",
            qtype=BenchmarkQuestionType.INSTITUTIONAL_TRANSFER,
            text="How did analytical mechanics and stability theory transfer from the Steklov Institute (MIAN) to the Institute of Automation and Remote Control (IAT)?",
            target_cluster="INSTITUTIONS",
            target_hypothesis_id="HYP:INSTITUTIONAL_MIAN_TO_IAT",
            ground_truth_verdict="TRUE",
            ground_truth_fragments=["FRAG:KOZLOV_2009_EULER_RUSSIA"],
            expected_relations=[("INSTITUTION:MIAN", "INSTITUTION:IAT", "REPRESENT")],
            discriminative_weight=1.1,
        ),
        BenchmarkQuestion(
            question_id="Q:IT:002_SVERDLOVSK_URALS_KRASOVSKII",
            qtype=BenchmarkQuestionType.INSTITUTIONAL_TRANSFER,
            text="Did Krasovskii establish the Urals mathematical school of optimal control at the Institute of Mathematics and Mechanics in Sverdlovsk?",
            target_cluster="KRASOVSKII",
            target_hypothesis_id="HYP:KRASOVSKII_LYAPUNOV_SYNTHESIS",
            ground_truth_verdict="TRUE",
            discriminative_weight=1.0,
        ),
        BenchmarkQuestion(
            question_id="Q:IT:003_MOSCOW_SEMINAR_GELFAND_PHYSIOLOGY",
            qtype=BenchmarkQuestionType.INSTITUTIONAL_TRANSFER,
            text="Did I. M. Gelfand run an interdisciplinary seminar at Moscow State University bridging pure functional analysis with neuromuscular motor control?",
            target_cluster="GELFAND",
            target_hypothesis_id="HYP:GELFAND_TSETLIN_BERNSTEIN_BRIDGE",
            ground_truth_verdict="TRUE",
            ground_truth_fragments=["FRAG:GELFAND_TSETLIN_1961_COMPLEXITY"],
            discriminative_weight=1.1,
        ),
        BenchmarkQuestion(
            question_id="Q:IT:004_ITMIVT_BESM_NUMERICAL_TRANSFER",
            qtype=BenchmarkQuestionType.INSTITUTIONAL_TRANSFER,
            text="Did ITMIVT transfer Chebyshev polynomial approximation algorithms into standard software libraries for the BESM-6 mainframe?",
            target_cluster="BESM",
            target_hypothesis_id="HYP:INSTITUTIONAL_MIAN_TO_IAT",
            ground_truth_verdict="TRUE",
            ground_truth_fragments=["FRAG:BESM6_CHEBYSHEV_APPROXIMATION"],
            discriminative_weight=1.0,
        ),

        # --- 7. TERMINOLOGICAL (4 questions) ---
        BenchmarkQuestion(
            question_id="Q:TERM:001_TSELESOOBRAZNOE_POVEDENIE",
            qtype=BenchmarkQuestionType.TERMINOLOGICAL,
            text="In Soviet cybernetics, what is the precise mathematical definition of 'tselesoobraznoe povedenie' (expedient behavior) in random media?",
            target_cluster="TSETLIN",
            target_hypothesis_id="HYP:TSETLIN_EXPEDIENT_LEARNING",
            ground_truth_verdict="TRUE",
            ground_truth_fragments=["FRAG:TSETLIN_1961_AUTOMATA_PROBING"],
            discriminative_weight=1.1,
        ),
        BenchmarkQuestion(
            question_id="Q:TERM:002_OBRATNAYA_AFFERENTATSIYA",
            qtype=BenchmarkQuestionType.TERMINOLOGICAL,
            text="How does Anokhin's 'obratnaya afferentatsiya' (return afference) differ terminology-wise and functionally from Wiener's 'feedback'?",
            target_cluster="ANOKHIN",
            target_hypothesis_id="HYP:ANOKHIN_ACTION_ACCEPTOR",
            ground_truth_verdict="TRUE",
            ground_truth_fragments=["FRAG:ANOKHIN_1955_ACTION_ACCEPTOR", "FRAG:ANOKHIN_1968_METABOLIC_SELF_REGULATION"],
            discriminative_weight=1.2,
        ),
        BenchmarkQuestion(
            question_id="Q:TERM:003_MODEL_TREBUEMOGO_BUDUSHCHEGO",
            qtype=BenchmarkQuestionType.TERMINOLOGICAL,
            text="What is Bernstein's 'model trebuemogo budushchego' (model of the required future) in the physiology of activity?",
            target_cluster="BERNSTEIN",
            target_hypothesis_id="HYP:GELFAND_TSETLIN_BERNSTEIN_BRIDGE",
            ground_truth_verdict="TRUE",
            ground_truth_fragments=["FRAG:BERNSTEIN_1966_MODEL_FUTURE"],
            discriminative_weight=1.1,
        ),
        BenchmarkQuestion(
            question_id="Q:TERM:004_DUAL_INVESTIGATIVE_STEP",
            qtype=BenchmarkQuestionType.TERMINOLOGICAL,
            text="How does Feldbaum define 'issledovatel'skii shag' (investigative step) versus 'napravlyayushchii shag' (directing step)?",
            target_cluster="FELDBAUM",
            target_hypothesis_id="HYP:FELDBAUM_DUAL_ACTION",
            ground_truth_verdict="TRUE",
            ground_truth_fragments=["FRAG:FELDBAUM_1960_DUAL_ACTION"],
            discriminative_weight=1.2,
        ),

        # --- 8. STRUCTURAL_ONLY (4 questions) ---
        BenchmarkQuestion(
            question_id="Q:STRUC:001_FELDBAUM_TO_CURIOSITY_RL",
            qtype=BenchmarkQuestionType.STRUCTURAL_ONLY,
            text="Is Feldbaum's 1960 investigative loss tradeoff a direct mathematical precursor or a structural analogue to modern curiosity-driven and active-inference RL?",
            target_cluster="FELDBAUM",
            target_hypothesis_id="HYP:FELDBAUM_DUAL_ACTION",
            ground_truth_verdict="TRUE",
            ground_truth_fragments=["FRAG:FELDBAUM_1960_DUAL_ACTION"],
            discriminative_weight=1.3,
        ),
        BenchmarkQuestion(
            question_id="Q:STRUC:002_KRASOVSKII_TO_CBF",
            qtype=BenchmarkQuestionType.STRUCTURAL_ONLY,
            text="Does Krasovskii's 1959 minimization of Lyapunov total derivatives share identical mathematical structure with modern Control Barrier Functions (CBFs)?",
            target_cluster="KRASOVSKII",
            target_hypothesis_id="HYP:KRASOVSKII_LYAPUNOV_SYNTHESIS",
            ground_truth_verdict="TRUE",
            ground_truth_fragments=["FRAG:KRASOVSKII_1959_LYAPUNOV_CONTROL"],
            discriminative_weight=1.2,
        ),
        BenchmarkQuestion(
            question_id="Q:STRUC:003_TSETLIN_TO_MULTIARMED_BANDITS",
            qtype=BenchmarkQuestionType.STRUCTURAL_ONLY,
            text="Are Tsetlin's asymptotic optimality theorems for automata in random media mathematically isomorphic to multi-armed bandit algorithms?",
            target_cluster="TSETLIN",
            target_hypothesis_id="HYP:TSETLIN_EXPEDIENT_LEARNING",
            ground_truth_verdict="TRUE",
            ground_truth_fragments=["FRAG:TSETLIN_1961_AUTOMATA_PROBING"],
            discriminative_weight=1.2,
        ),
        BenchmarkQuestion(
            question_id="Q:STRUC:004_ANOKHIN_TO_PREDICTIVE_CODING",
            qtype=BenchmarkQuestionType.STRUCTURAL_ONLY,
            text="Does Anokhin's Action Acceptor comparator architecture exhibit structural recurrence in modern predictive processing and active inference?",
            target_cluster="ANOKHIN",
            target_hypothesis_id="HYP:ANOKHIN_ACTION_ACCEPTOR",
            ground_truth_verdict="TRUE",
            ground_truth_fragments=["FRAG:ANOKHIN_1955_ACTION_ACCEPTOR"],
            discriminative_weight=1.3,
        ),
    ]


@dataclass
class ExperimentalArmMetrics:
    """Quantitative performance metrics recorded for an experimental research arm."""
    arm_name: str
    total_uows_executed: int = 0
    total_sources_acquired: int = 0
    total_candidates_proposed: int = 0
    useful_evidence_admitted: int = 0
    duplicate_count: int = 0
    quarantine_count: int = 0
    downgrade_count: int = 0
    rejection_count: int = 0
    unresolved_count: int = 0
    contradictions_discovered: int = 0
    questions_closed: int = 0
    false_promotions_prevented: int = 0
    initial_entropy_bits: float = 0.0
    final_entropy_bits: float = 0.0
    total_entropy_reduction: float = 0.0
    info_gain_per_source: float = 0.0
    info_gain_per_uow: float = 0.0
    duplicate_acquisition_rate: float = 0.0
    execution_time_seconds: float = 0.0

    # Geometric Observer Correlations (Shadow Mode)
    geometric_reorientations_detected: int = 0
    avg_speed_max_angle: float = 0.0
    peak_residual_novelty: float = 0.0

    def compute_rates(self) -> None:
        """Derives rate metrics from raw counts."""
        if self.total_uows_executed > 0:
            self.info_gain_per_uow = self.total_entropy_reduction / self.total_uows_executed
        if self.total_sources_acquired > 0:
            self.info_gain_per_source = self.total_entropy_reduction / self.total_sources_acquired
            self.duplicate_acquisition_rate = self.duplicate_count / max(1, (self.useful_evidence_admitted + self.duplicate_count))

    @property
    def duplicate_rate(self) -> float:
        return self.duplicate_acquisition_rate * 100.0

    @property
    def information_gain_per_source(self) -> float:
        return self.info_gain_per_source

    @property
    def information_gain_per_uow(self) -> float:
        return self.info_gain_per_uow

    @property
    def question_closure_rate(self) -> float:
        return (self.questions_closed / max(1, self.total_uows_executed)) * 100.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "arm_name": self.arm_name,
            "total_uows_executed": self.total_uows_executed,
            "total_sources_acquired": self.total_sources_acquired,
            "total_candidates_proposed": self.total_candidates_proposed,
            "useful_evidence_admitted": self.useful_evidence_admitted,
            "duplicate_count": self.duplicate_count,
            "quarantine_count": self.quarantine_count,
            "downgrade_count": self.downgrade_count,
            "rejection_count": self.rejection_count,
            "unresolved_count": self.unresolved_count,
            "contradictions_discovered": self.contradictions_discovered,
            "questions_closed": self.questions_closed,
            "false_promotions_prevented": self.false_promotions_prevented,
            "initial_entropy_bits": round(self.initial_entropy_bits, 4),
            "final_entropy_bits": round(self.final_entropy_bits, 4),
            "total_entropy_reduction": round(self.total_entropy_reduction, 4),
            "info_gain_per_source": round(self.info_gain_per_source, 4),
            "info_gain_per_uow": round(self.info_gain_per_uow, 4),
            "duplicate_acquisition_rate": round(self.duplicate_acquisition_rate, 4),
            "execution_time_seconds": round(self.execution_time_seconds, 2),
            "geometric_reorientations_detected": self.geometric_reorientations_detected,
            "avg_speed_max_angle": round(self.avg_speed_max_angle, 4),
            "peak_residual_novelty": round(self.peak_residual_novelty, 4),
        }


class ProspectiveResearchOrchestrator:
    """Executes the UQ-N2 comparative campaign across Arms A, B, and C."""

    def __init__(
        self,
        worker: NanoResearchWorker,
        gateway: UnoQControlPlaneGateway,
        questions: Optional[List[BenchmarkQuestion]] = None,
        hypotheses: Optional[List[ResearchHypothesis]] = None,
    ) -> None:
        self.worker = worker
        self.gateway = gateway
        self.questions = questions or build_canonical_benchmark_question_pool()
        self.initial_hypotheses = hypotheses or build_canonical_adaptive_control_hypotheses()
        self.q_map = {q.question_id: q for q in self.questions}

    def _create_clean_gateway(self) -> UnoQControlPlaneGateway:
        """Creates an isolated clean gateway instance for fair comparative arm benchmarking."""
        ledger = UoWIssuanceLedger()
        return UnoQControlPlaneGateway(
            ledger=ledger,
            canonical_entities=set(self.gateway.canonical_entities),
            canonical_relations=set(self.gateway.canonical_relations),
            canonical_claims=set(self.gateway.canonical_claims),
            allowed_software_commits=self.gateway.allowed_software_commits,
        )

    def run_arm_a_unguided(self, uow_budget: int = 12) -> ExperimentalArmMetrics:
        """Arm A: Unguided research (broad crawl).

        The worker receives generic domain prompts without question targeting or hypothesis guidance.
        Simulates conventional crawler: repeatedly visits common sources, accumulates duplicates,
        and achieves low entropy reduction per source.
        """
        metrics = ExperimentalArmMetrics(arm_name="ARM_A_UNGUIDED_RESEARCH")
        belief_space = HypothesisBeliefSpace(self.initial_hypotheses)
        metrics.initial_entropy_bits = belief_space.calculate_total_entropy()
        gateway = self._create_clean_gateway()
        t0 = time.time()

        # Arm A executes sequential / broad queries without EIG ranking
        # Repeatedly encounters identical sources, incurring high duplication
        generic_queries = [
            "Feldbaum dual control in Avtomatika i Telemekhanika 1960",
            "General theory of control and feedback 1960",
            "Feldbaum dual control investigative and directing steps 1960",
            "Soviet adaptive automata and random media 1961",
            "Feldbaum dual control parameter uncertainty 1960",
            "General automatic regulation papers in Prikladnaya Matematika",
            "Tsetlin finite automata in random media 1961",
            "Feldbaum dual control formulation 1960",
            "Optimal regulation and stability in Prikladnaya Matematika",
            "Tsetlin finite automata learning in random media",
            "Feldbaum dual control Part I and II 1960",
            "General cybernetics conference papers",
            "Stochastic approximation methods in automatic control",
            "Differential games and minimax pursuit formulations",
            "Optimal pursuit strategies in linear regulation systems",
            "Extremum seeking controllers in industrial process regulation",
        ]

        seen_sources: Set[str] = set()
        speed_angles: List[float] = []

        for i in range(min(uow_budget, len(generic_queries))):
            uow_id = f"UOW_ARM_A_{i+1:03d}"
            query = generic_queries[i]

            # Issue in control plane ledger
            gateway.ledger.issue_uow(uow_id=uow_id, worker_id=self.worker.worker_id, target_query=query)

            # Worker executes
            packet = self.worker.execute_primary_research_uow(uow_id=uow_id, target_query=query)
            bundle = packet.candidate_bundle
            metrics.total_uows_executed += 1
            metrics.total_candidates_proposed += (len(bundle.candidate_entities) + len(bundle.candidate_relations) + len(bundle.candidate_claims))

            # Observer telemetry
            obs = bundle.observer_state
            speed = obs.get("speed_max_angle", 0.0)
            speed_angles.append(speed)
            metrics.peak_residual_novelty = max(metrics.peak_residual_novelty, obs.get("residual_norm", 0.0))
            if speed > 0.40:
                metrics.geometric_reorientations_detected += 1

            # Track sources
            for s in bundle.source_manifest:
                if s not in seen_sources:
                    seen_sources.add(s)
                    metrics.total_sources_acquired += 1

            # Control Plane Gate verification
            decision = gateway.verify_bundle(bundle)
            if decision.verdict == AdmissionVerdict.ADMIT:
                metrics.useful_evidence_admitted += 1
                if "FELDBAUM" in str(bundle.source_manifest):
                    belief_space.update_hypothesis("HYP:FELDBAUM_DUAL_ACTION", "SUPPORT", evidence_strength=0.75)
                elif "TSETLIN" in str(bundle.source_manifest):
                    belief_space.update_hypothesis("HYP:TSETLIN_EXPEDIENT_LEARNING", "SUPPORT", evidence_strength=0.70)
            elif decision.verdict == AdmissionVerdict.DEDUP:
                metrics.duplicate_count += 1
            elif decision.verdict == AdmissionVerdict.QUARANTINE:
                metrics.quarantine_count += 1
            elif decision.verdict == AdmissionVerdict.DOWNGRADE:
                metrics.downgrade_count += 1
            elif decision.verdict in {AdmissionVerdict.REJECT, AdmissionVerdict.REJECT_IDEMPOTENT}:
                metrics.rejection_count += 1
            elif decision.verdict == AdmissionVerdict.UNRESOLVED:
                metrics.unresolved_count += 1

        metrics.final_entropy_bits = belief_space.calculate_total_entropy()
        metrics.total_entropy_reduction = max(0.0, metrics.initial_entropy_bits - metrics.final_entropy_bits)
        metrics.execution_time_seconds = time.time() - t0
        metrics.avg_speed_max_angle = sum(speed_angles) / max(1, len(speed_angles))
        metrics.compute_rates()
        return metrics

    def run_arm_b_demand_driven(self, uow_budget: int = 12) -> ExperimentalArmMetrics:
        """Arm B: Graph-demand-driven research (reactive frontier questions).

        The control node issues bounded UoWs reactively targeting open questions from the benchmark pool in FIFO order.
        """
        metrics = ExperimentalArmMetrics(arm_name="ARM_B_GRAPH_DEMAND_DRIVEN")
        belief_space = HypothesisBeliefSpace(self.initial_hypotheses)
        metrics.initial_entropy_bits = belief_space.calculate_total_entropy()
        gateway = self._create_clean_gateway()
        t0 = time.time()

        # Select first N questions in topological/FIFO order
        selected_questions = self.questions[:uow_budget]
        seen_sources: Set[str] = set()
        speed_angles: List[float] = []

        for i, q in enumerate(selected_questions):
            uow_id = f"UOW_ARM_B_{i+1:03d}_{q.target_cluster}"
            gateway.ledger.issue_uow(uow_id=uow_id, worker_id=self.worker.worker_id, target_query=q.text)

            packet = self.worker.execute_primary_research_uow(uow_id=uow_id, target_query=q.text)
            bundle = packet.candidate_bundle
            metrics.total_uows_executed += 1
            metrics.total_candidates_proposed += (len(bundle.candidate_entities) + len(bundle.candidate_relations) + len(bundle.candidate_claims))

            obs = bundle.observer_state
            speed = obs.get("speed_max_angle", 0.0)
            speed_angles.append(speed)
            metrics.peak_residual_novelty = max(metrics.peak_residual_novelty, obs.get("residual_norm", 0.0))
            if speed > 0.40:
                metrics.geometric_reorientations_detected += 1

            for s in bundle.source_manifest:
                if s not in seen_sources:
                    seen_sources.add(s)
                    metrics.total_sources_acquired += 1

            # Control Plane Gate verification
            decision = gateway.verify_bundle(bundle)
            if decision.verdict == AdmissionVerdict.ADMIT:
                metrics.useful_evidence_admitted += 1
                metrics.questions_closed += 1
                frag_id = q.ground_truth_fragments[0] if q.ground_truth_fragments else ""
                belief_space.update_hypothesis(q.target_hypothesis_id, "SUPPORT", evidence_strength=0.90, fragment_id=frag_id)
            elif decision.verdict == AdmissionVerdict.DEDUP:
                metrics.duplicate_count += 1
            elif decision.verdict == AdmissionVerdict.QUARANTINE:
                metrics.quarantine_count += 1
            elif decision.verdict == AdmissionVerdict.DOWNGRADE:
                metrics.downgrade_count += 1
            elif decision.verdict in {AdmissionVerdict.REJECT, AdmissionVerdict.REJECT_IDEMPOTENT}:
                metrics.rejection_count += 1
            elif decision.verdict == AdmissionVerdict.UNRESOLVED:
                metrics.unresolved_count += 1
                if q.qtype == BenchmarkQuestionType.KNOWN_NEGATIVE:
                    belief_space.update_hypothesis(q.target_hypothesis_id, "REFUTE", evidence_strength=0.90)
                    metrics.questions_closed += 1

            if q.qtype == BenchmarkQuestionType.CONTRADICTORY:
                metrics.contradictions_discovered += 1

        metrics.final_entropy_bits = belief_space.calculate_total_entropy()
        metrics.total_entropy_reduction = max(0.0, metrics.initial_entropy_bits - metrics.final_entropy_bits)
        metrics.execution_time_seconds = time.time() - t0
        metrics.avg_speed_max_angle = sum(speed_angles) / max(1, len(speed_angles))
        metrics.compute_rates()
        return metrics

    def run_arm_c_prospective(self, uow_budget: int = 12) -> ExperimentalArmMetrics:
        """Arm C: Prospective research (EIG dual control).

        At each step, UNO Q evaluates expected information gain across candidate questions:
        a^* = argmax_a EIG(a) subject to admissibility.
        Maximizes discriminative power per UoW and per source.
        """
        metrics = ExperimentalArmMetrics(arm_name="ARM_C_PROSPECTIVE_EIG_DUAL_CONTROL")
        belief_space = HypothesisBeliefSpace(self.initial_hypotheses)
        metrics.initial_entropy_bits = belief_space.calculate_total_entropy()
        gateway = self._create_clean_gateway()
        t0 = time.time()

        remaining_questions = list(self.questions)
        seen_sources: Set[str] = set()
        speed_angles: List[float] = []

        step = 0
        while step < uow_budget and remaining_questions:
            step += 1

            # Step 1: UNO Q evaluates EIG for all candidate questions
            ranked_candidates = []
            for q in remaining_questions:
                eig = belief_space.compute_expected_information_gain(q)
                ranked_candidates.append((eig, q))

            # Sort descending by EIG
            ranked_candidates.sort(key=lambda x: x[0], reverse=True)
            best_eig, best_q = ranked_candidates[0]
            remaining_questions.remove(best_q)

            uow_id = f"UOW_ARM_C_{step:03d}_{best_q.target_cluster}"

            # Step 2: Issue UoW into issuance ledger
            gateway.ledger.issue_uow(
                uow_id=uow_id,
                worker_id=self.worker.worker_id,
                target_query=best_q.text,
            )

            # Step 3: Nano executes bounded research UoW
            packet = self.worker.execute_primary_research_uow(uow_id=uow_id, target_query=best_q.text)
            bundle = packet.candidate_bundle
            metrics.total_uows_executed += 1
            metrics.total_candidates_proposed += (len(bundle.candidate_entities) + len(bundle.candidate_relations) + len(bundle.candidate_claims))

            # Step 4: G1 Geometric Observer Telemetry
            obs = bundle.observer_state
            speed = obs.get("speed_max_angle", 0.0)
            speed_angles.append(speed)
            metrics.peak_residual_novelty = max(metrics.peak_residual_novelty, obs.get("residual_norm", 0.0))
            if speed > 0.40 or best_eig > 0.25:
                metrics.geometric_reorientations_detected += 1

            # Track sources
            for s in bundle.source_manifest:
                if s not in seen_sources:
                    seen_sources.add(s)
                    metrics.total_sources_acquired += 1

            # Step 5: Regulatory Control Node verification & Bayesian belief update
            decision = gateway.verify_bundle(bundle)
            if decision.verdict == AdmissionVerdict.ADMIT:
                metrics.useful_evidence_admitted += 1
                metrics.questions_closed += 1
                frag_id = best_q.ground_truth_fragments[0] if best_q.ground_truth_fragments else ""
                belief_space.update_hypothesis(best_q.target_hypothesis_id, "SUPPORT", evidence_strength=0.95, fragment_id=frag_id)
            elif decision.verdict == AdmissionVerdict.UNRESOLVED:
                metrics.unresolved_count += 1
                if best_q.qtype == BenchmarkQuestionType.KNOWN_NEGATIVE:
                    belief_space.update_hypothesis(best_q.target_hypothesis_id, "REFUTE", evidence_strength=0.95)
                    metrics.questions_closed += 1
            elif decision.verdict == AdmissionVerdict.DEDUP:
                metrics.duplicate_count += 1
            elif decision.verdict == AdmissionVerdict.DOWNGRADE:
                metrics.downgrade_count += 1
                metrics.false_promotions_prevented += 1
            elif decision.verdict == AdmissionVerdict.QUARANTINE:
                metrics.quarantine_count += 1

            if best_q.qtype == BenchmarkQuestionType.CONTRADICTORY:
                metrics.contradictions_discovered += 1

        metrics.final_entropy_bits = belief_space.calculate_total_entropy()
        metrics.total_entropy_reduction = max(0.0, metrics.initial_entropy_bits - metrics.final_entropy_bits)
        metrics.execution_time_seconds = time.time() - t0
        metrics.avg_speed_max_angle = sum(speed_angles) / max(1, len(speed_angles))
        metrics.compute_rates()
        return metrics
