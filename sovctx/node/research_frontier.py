"""SOVCTX Autonomous Research Frontier: Coordinator & Attention Engine.

Orchestrates:
1. 50% Established Research Spines / 30% Cross-Thread Bridges / 20% Anomalous Frontier budget.
2. Cross-thread bridge intersection matrix (T2xT3, T4xT6, T5xT3, T1xT8, etc.).
3. Seed generation across T1 through T9.
4. Autonomous nomination generation addressing open relationships.
5. Discovery-oriented reporting (reporting discoveries, bridges, anomalies, and hypotheses).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .research_question import (
    AutonomousBranchingEngine,
    BranchingTrigger,
    CANONICAL_THREAD_FAMILIES,
    InstitutionalChannelType,
    OpenQuestionLedger,
    PriorityComponents,
    QuestionStatus,
    ResearchQuestion,
    ThreadFamily,
    ThreadSaturationDetector,
    ThreadSaturationState,
    utc_now_iso,
)


@dataclass
class CrossThreadBridge:
    """An intersection between two independent thread families probing compound structures."""
    bridge_id: str
    thread_a: str
    thread_b: str
    intersection_concept: str
    target_relational_motif: str
    exploratory_hypothesis: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


CANONICAL_CROSS_THREAD_BRIDGES: List[CrossThreadBridge] = [
    CrossThreadBridge(
        bridge_id="XBRIDGE:T2_T3",
        thread_a="T2",
        thread_b="T3",
        intersection_concept="State Estimation under Unbounded Perturbation",
        target_relational_motif="OBSERVE -> INVERT -> CONSTRAIN -> STABILIZE -> CONTROL",
        exploratory_hypothesis="Inverse reconstruction of unobservable state provides the feedback coordinate necessary for Lyapunov/Pontryagin closed-loop control.",
    ),
    CrossThreadBridge(
        bridge_id="XBRIDGE:T4_T6",
        thread_a="T4",
        thread_b="T6",
        intersection_concept="Collective Adaptation & Macroscopic Self-Organization",
        target_relational_motif="DISTRIBUTE -> REDUCE -> FEEDBACK -> ADAPT",
        exploratory_hypothesis="Bogolyubov-style hierarchy reduction and Tsetlin collective automata share identical structural mechanics of low-dimensional emergent order.",
    ),
    CrossThreadBridge(
        bridge_id="XBRIDGE:T5_T3",
        thread_a="T5",
        thread_b="T3",
        intersection_concept="Finite Computational Inversion & Regularized Algorithms",
        target_relational_motif="INVERT -> REGULARIZE -> APPROXIMATE -> COMPUTE",
        exploratory_hypothesis="Chebyshev minimax approximation was adapted to bound regularization parameter choice in discrete ill-posed radar/gravimetry inversion.",
    ),
    CrossThreadBridge(
        bridge_id="XBRIDGE:T1_T8",
        thread_a="T1",
        thread_b="T8",
        intersection_concept="Persistence of Relational Vocabulary across Eras",
        target_relational_motif="ETYMOLOGY -> CO_OCCURRENCE -> OPERATOR_GRAMMAR",
        exploratory_hypothesis="Euler-Chebyshev operator terminology in Russian directly grounded the 20th-century emphasis on stability and transformation over objects.",
    ),
    CrossThreadBridge(
        bridge_id="XBRIDGE:T7_T2",
        thread_a="T7",
        thread_b="T2",
        intersection_concept="Institutional Conduit of Stability Mathematics into Control",
        target_relational_motif="MIAN_SEMINAR -> PERSONNEL_TRANSFER -> DESIGN_BUREAU",
        exploratory_hypothesis="Krasovskii and Pontryagin students transferred Lyapunov methods into TsAGI and OKB design bureaus through specialized inter-departmental seminars.",
    ),
    CrossThreadBridge(
        bridge_id="XBRIDGE:T6_T2",
        thread_a="T6",
        thread_b="T2",
        intersection_concept="Stochastic Automata Adaptation vs Extremal Control",
        target_relational_motif="EXPEDIENT_ACTION -> ADAPTIVE_STEP -> EXTREMAL_REGULATION",
        exploratory_hypothesis="Tsetlin automata games in random media represent a model-free discrete analogue to Pontryagin continuous optimal control.",
    ),
]


@dataclass
class FrontierCycleAllocation:
    """The 50/30/20 budget allocation for an autonomous acquisition cycle."""
    total_slots: int
    spines_quota: int     # 50%
    bridges_quota: int    # 30%
    anomalies_quota: int  # 20%
    selected_spines: List[ResearchQuestion] = field(default_factory=list)
    selected_bridges: List[ResearchQuestion] = field(default_factory=list)
    selected_anomalies: List[ResearchQuestion] = field(default_factory=list)

    def all_selected(self) -> List[ResearchQuestion]:
        return self.selected_spines + self.selected_bridges + self.selected_anomalies

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_slots": self.total_slots,
            "quotas": {
                "spines_50pct": self.spines_quota,
                "bridges_30pct": self.bridges_quota,
                "anomalies_20pct": self.anomalies_quota,
            },
            "selected_counts": {
                "spines": len(self.selected_spines),
                "bridges": len(self.selected_bridges),
                "anomalies": len(self.selected_anomalies),
            },
            "selected_questions": [q.to_dict() for q in self.all_selected()],
        }


@dataclass
class DiscoveryReport:
    """The discovery-oriented autonomous output report."""
    cycle_timestamp: str
    new_relationships_discovered: List[Dict[str, Any]] = field(default_factory=list)
    new_threads_spawned: List[Dict[str, Any]] = field(default_factory=list)
    threads_saturated: List[Dict[str, Any]] = field(default_factory=list)
    cross_thread_bridges: List[Dict[str, Any]] = field(default_factory=list)
    new_contradictions: List[Dict[str, Any]] = field(default_factory=list)
    new_institutions: List[str] = field(default_factory=list)
    new_native_concepts: List[str] = field(default_factory=list)
    unexplained_anomalies: List[Dict[str, Any]] = field(default_factory=list)
    hypotheses_strengthened: List[str] = field(default_factory=list)
    hypotheses_weakened: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_markdown(self) -> str:
        lines = [
            "# SOVCTX Autonomous Research Frontier Report",
            f"*Generated at: {self.cycle_timestamp}*",
            "",
            "## 1. New Relationships Discovered",
        ]
        if self.new_relationships_discovered:
            for r in self.new_relationships_discovered:
                lines.append(f"- **{r.get('relation')}**: {r.get('endpoints')} (Source: {r.get('source')})")
        else:
            lines.append("- *No novel relations verified in this cycle.*")

        lines.extend(["", "## 2. New Threads Spawned"])
        if self.new_threads_spawned:
            for t in self.new_threads_spawned:
                trig = t.get('spawn_trigger') or t.get('trigger', 'UNSPECIFIED')
                rat = t.get('spawn_rationale') or t.get('rationale', '')
                lines.append(f"- **{t.get('thread_id')}**: {t.get('name')} (Trigger: {trig}) - {rat}")
        else:
            lines.append("- *No branching triggers exceeded activation threshold.*")

        lines.extend(["", "## 3. Threads Saturated"])
        if self.threads_saturated:
            for s in self.threads_saturated:
                lines.append(f"- **{s.get('thread_id')}**: {s.get('recommendation')}")
        else:
            lines.append("- *All active threads remain in productive discovery window.*")

        lines.extend(["", "## 4. Cross-Thread Bridges"])
        if self.cross_thread_bridges:
            for b in self.cross_thread_bridges:
                th_pair = f"{b.get('thread_a', '')} × {b.get('thread_b', '')}" if b.get('thread_a') else b.get('threads', '')
                concept = b.get('intersection_concept') or b.get('intersection', '')
                hyp = b.get('exploratory_hypothesis') or b.get('hypothesis', '')
                lines.append(f"- **{b.get('bridge_id')}** ({th_pair}): {concept} -> *{hyp}*")
        else:
            lines.append("- *No cross-thread bridges evaluated in this cycle.*")

        lines.extend(["", "## 5. New Contradictions & Anomalies"])
        if self.new_contradictions or self.unexplained_anomalies:
            for c in self.new_contradictions:
                lines.append(f"- **CONTRADICTION**: {c.get('description')}")
            for a in self.unexplained_anomalies:
                lines.append(f"- **ANOMALY**: {a.get('description')}")
        else:
            lines.append("- *Zero unclassified anomalies or structural contradictions detected.*")

        lines.extend(["", "## 6. Hypotheses Strengthened / Weakened"])
        for h in self.hypotheses_strengthened:
            lines.append(f"- **[STRENGTHENED]** {h}")
        for h in self.hypotheses_weakened:
            lines.append(f"- **[WEAKENED]** {h}")

        return "\n".join(lines)


class ResearchFrontierCoordinator:
    """Coordinates research question selection, attention budgeting (50/30/20), and reporting."""

    def __init__(self, ledger: Optional[OpenQuestionLedger] = None) -> None:
        self.ledger = ledger or OpenQuestionLedger()
        self.branching_engine = AutonomousBranchingEngine(self.ledger)
        self.cross_bridges = list(CANONICAL_CROSS_THREAD_BRIDGES)
        self._ensure_seed_spines()

    def _ensure_seed_spines(self) -> None:
        """Injects foundational research questions across T1 through T9."""
        seed_questions = [
            ResearchQuestion(
                question_id="RQ:T1:0001",
                thread_id="T1",
                originating_evidence="SOVCTX R1/R2 Relational Analysis",
                question_text="What formal mathematical transmission lines connect Leibniz's dyadic and relational operator conceptions through Euler to the St. Petersburg school of Chebyshev and Lyapunov?",
                relation_under_test="RELATION_FIRST_MAPPING -> OPERATOR_INVARIANT",
                known_endpoints=["Leibniz", "Euler", "Chebyshev"],
                unknown_endpoint=True,
                temporal_window="1750-1895",
                priority_components=PriorityComponents(
                    novelty=0.8, bridge_potential=0.7, evidentiary_quality=0.8,
                    corroboration_potential=0.6, historical_gap_value=0.9, duplication_penalty=0.0
                ),
                generation=0,
                target_channel=InstitutionalChannelType.STRUCTURAL_MATHEMATICAL_CONTINUITY,
            ),
            ResearchQuestion(
                question_id="RQ:T2:0001",
                thread_id="T2",
                originating_evidence="SOVCTX R2 Control Spine",
                question_text="How did stability mathematics move from Lyapunov phase-space analysis through Andronov's structural stability (roughness) into Pontryagin's maximum principle and Krasovskii's feedback regulation?",
                relation_under_test="STABILIZE -> CONTROL",
                known_endpoints=["Lyapunov", "Pontryagin", "Krasovskii"],
                unknown_endpoint=True,
                temporal_window="1892-1965",
                priority_components=PriorityComponents(
                    novelty=0.7, bridge_potential=0.9, evidentiary_quality=0.9,
                    corroboration_potential=0.8, historical_gap_value=0.8, duplication_penalty=0.0
                ),
                generation=0,
                target_channel=InstitutionalChannelType.PERSONNEL_TRANSFER,
            ),
            ResearchQuestion(
                question_id="RQ:T3:0001",
                thread_id="T3",
                originating_evidence="SOVCTX R2 Inverse Spine",
                question_text="Where else was conditional stabilization of an ill-posed inverse problem used before 1970 beyond Tikhonov's geophysical sounding and Zelkin's antenna synthesis?",
                relation_under_test="INVERT -> CONSTRAIN -> STABILIZE",
                known_endpoints=["Tikhonov", "Zelkin"],
                unknown_endpoint=True,
                temporal_window="1943-1970",
                priority_components=PriorityComponents(
                    novelty=0.9, bridge_potential=0.8, evidentiary_quality=0.9,
                    corroboration_potential=0.7, historical_gap_value=0.9, duplication_penalty=0.0
                ),
                generation=0,
                target_channel=InstitutionalChannelType.DOCUMENTED_CITATION_TRANSFER,
            ),
            ResearchQuestion(
                question_id="RQ:T4:0001",
                thread_id="T4",
                originating_evidence="SOVCTX R2 Kinetic Spine",
                question_text="How did Bogolyubov's BBGKY hierarchy reduction formally adapt Vlasov's self-consistent field to describe collective equilibrium in non-plasma systems?",
                relation_under_test="DISTRIBUTE -> REDUCE -> EVOLVE",
                known_endpoints=["Vlasov", "Bogolyubov"],
                unknown_endpoint=True,
                temporal_window="1938-1960",
                priority_components=PriorityComponents(
                    novelty=0.7, bridge_potential=0.7, evidentiary_quality=0.8,
                    corroboration_potential=0.6, historical_gap_value=0.7, duplication_penalty=0.0
                ),
                generation=0,
                target_channel=InstitutionalChannelType.STRUCTURAL_MATHEMATICAL_CONTINUITY,
            ),
            ResearchQuestion(
                question_id="RQ:T5:0001",
                thread_id="T5",
                originating_evidence="SOVCTX Approximation Corpus",
                question_text="How did Chebyshev's minimax polynomial approximation theory transfer into finite numerical algorithms for the early BESM computers?",
                relation_under_test="APPROXIMATE -> BOUND -> COMPUTE",
                known_endpoints=["Chebyshev", "Markov", "Lebedev"],
                unknown_endpoint=True,
                temporal_window="1930-1965",
                priority_components=PriorityComponents(
                    novelty=0.8, bridge_potential=0.8, evidentiary_quality=0.8,
                    corroboration_potential=0.7, historical_gap_value=0.8, duplication_penalty=0.0
                ),
                generation=0,
                target_channel=InstitutionalChannelType.INSTITUTIONAL_CONTINUITY,
            ),
            ResearchQuestion(
                question_id="RQ:T6:0001",
                thread_id="T6",
                originating_evidence="BCIG / SOVCTX Adaptive Transfer",
                question_text="How did Bernstein's model of the required future and Anokhin's Action Acceptor influence Tsetlin's stochastic automata and Gelfand's nonlocal search?",
                relation_under_test="PREDICT -> OBSERVE -> COMPARE -> ADAPT",
                known_endpoints=["Bernstein", "Anokhin", "Tsetlin", "Gelfand"],
                unknown_endpoint=True,
                temporal_window="1947-1968",
                priority_components=PriorityComponents(
                    novelty=0.8, bridge_potential=0.9, evidentiary_quality=0.9,
                    corroboration_potential=0.8, historical_gap_value=0.8, duplication_penalty=0.0
                ),
                generation=0,
                target_channel=InstitutionalChannelType.PERSONNEL_TRANSFER,
            ),
            ResearchQuestion(
                question_id="RQ:T7:0001",
                thread_id="T7",
                originating_evidence="SOVCTX Institutional Audit",
                question_text="What specific institutional conduits (MIAN, IPM, LOMI, Kyiv Cybernetics) facilitated the transfer of pure operator methods into applied engineering design institutes?",
                relation_under_test="SEMINAR -> PERSONNEL_TRANSFER -> LAB -> DESIGN_BUREAU",
                known_endpoints=["MIAN", "IPM", "TsAGI"],
                unknown_endpoint=True,
                temporal_window="1945-1975",
                priority_components=PriorityComponents(
                    novelty=0.8, bridge_potential=0.8, evidentiary_quality=0.7,
                    corroboration_potential=0.8, historical_gap_value=0.9, duplication_penalty=0.0
                ),
                generation=0,
                target_channel=InstitutionalChannelType.INSTITUTIONAL_CONTINUITY,
            ),
            ResearchQuestion(
                question_id="RQ:T8:0001",
                thread_id="T8",
                originating_evidence="SOVCTX 13 Native Concepts",
                question_text="How did the semantic scope of native terms (устойчивость, грубость, допустимость, регуляризация) shift as they migrated from pure differential equations into applied engineering control?",
                relation_under_test="TERM_DEFINITION -> CO_OCCURRENCE -> SEMANTIC_DRIFT",
                known_endpoints=["устойчивость", "грубость", "регуляризация"],
                unknown_endpoint=True,
                temporal_window="1935-1970",
                priority_components=PriorityComponents(
                    novelty=0.8, bridge_potential=0.8, evidentiary_quality=0.8,
                    corroboration_potential=0.7, historical_gap_value=0.8, duplication_penalty=0.0
                ),
                generation=0,
                target_channel=InstitutionalChannelType.STRUCTURAL_MATHEMATICAL_CONTINUITY,
            ),
            ResearchQuestion(
                question_id="RQ:T9:0001",
                thread_id="T9",
                originating_evidence="SOVCTX Anomaly Frontier Reserve",
                question_text="What recurring relational patterns in the corpus fail to map into our current 8 school clusters or 17 operator verbs?",
                relation_under_test="ANOMALOUS_RELATION -> UNCLASSIFIED_HUB",
                known_endpoints=["UNKNOWN"],
                unknown_endpoint=True,
                temporal_window="1920-1980",
                priority_components=PriorityComponents(
                    novelty=1.0, bridge_potential=0.9, evidentiary_quality=0.6,
                    corroboration_potential=0.5, historical_gap_value=1.0, duplication_penalty=0.0
                ),
                generation=0,
                target_channel=InstitutionalChannelType.STRUCTURAL_MATHEMATICAL_CONTINUITY,
            ),
            # --- Pre-Seeded Specific Cross-Thread Bridges ---
            ResearchQuestion(
                question_id="RQ:XBRIDGE:T2_T3:0001",
                thread_id="T2",
                originating_evidence="SOVCTX Control & Inverse Spines",
                question_text="Where did conditional stabilization of ill-posed inverse operators (Tikhonov regularization) first couple directly with closed-loop feedback regulation (Pontryagin/Krasovskii) to govern systems with unobservable or partially corrupted state coordinates?",
                relation_under_test="OBSERVE -> INVERT -> CONSTRAIN -> STABILIZE -> CONTROL",
                known_endpoints=["Tikhonov", "Pontryagin", "Krasovskii"],
                unknown_endpoint=True,
                temporal_window="1955-1970",
                priority_components=PriorityComponents(
                    novelty=0.9, bridge_potential=1.0, evidentiary_quality=0.9,
                    corroboration_potential=0.8, historical_gap_value=0.9, duplication_penalty=0.0
                ),
                generation=0,
                metadata={"bridge_id": "XBRIDGE:T2_T3", "intersection_concept": "State Estimation under Unbounded Perturbation"},
                target_channel=InstitutionalChannelType.STRUCTURAL_MATHEMATICAL_CONTINUITY,
            ),
            ResearchQuestion(
                question_id="RQ:XBRIDGE:T2_T3:0002",
                thread_id="T3",
                originating_evidence="Zelkin (1950s) & Tikhonov (1943)",
                question_text="Did Zelkin's 1950s antenna synthesis phase-amplitude inverse problem utilize Lyapunov stability criteria to bound the sensitivity of beamforming patterns to physical component perturbations?",
                relation_under_test="INVERT_PATTERN -> BOUND_SENSITIVITY -> STABILIZE_BEAM",
                known_endpoints=["Zelkin", "Tikhonov"],
                unknown_endpoint=True,
                temporal_window="1950-1965",
                priority_components=PriorityComponents(
                    novelty=0.85, bridge_potential=0.95, evidentiary_quality=0.9,
                    corroboration_potential=0.75, historical_gap_value=0.9, duplication_penalty=0.0
                ),
                generation=0,
                metadata={"bridge_id": "XBRIDGE:T2_T3", "intersection_concept": "Inverse Antenna Synthesis & Lyapunov Sensitivity"},
                target_channel=InstitutionalChannelType.DOCUMENTED_CITATION_TRANSFER,
            ),
            ResearchQuestion(
                question_id="RQ:XBRIDGE:T4_T6:0001",
                thread_id="T4",
                originating_evidence="Bogolyubov (1946) & Tsetlin (1961)",
                question_text="Did Bogolyubov's BBGKY distribution hierarchy reduction share formal mathematical machinery with Tsetlin's macroscopic automata collectives playing zero-sum and non-zero-sum games?",
                relation_under_test="DISTRIBUTE_STATE -> REDUCE_DEGREES -> EMERGENT_EQUILIBRIUM",
                known_endpoints=["Bogolyubov", "Tsetlin", "Gelfand"],
                unknown_endpoint=True,
                temporal_window="1958-1966",
                priority_components=PriorityComponents(
                    novelty=0.9, bridge_potential=1.0, evidentiary_quality=0.8,
                    corroboration_potential=0.8, historical_gap_value=0.9, duplication_penalty=0.0
                ),
                generation=0,
                metadata={"bridge_id": "XBRIDGE:T4_T6", "intersection_concept": "Collective Adaptation & Macroscopic Self-Organization"},
                target_channel=InstitutionalChannelType.PERSONNEL_TRANSFER,
            ),
            ResearchQuestion(
                question_id="RQ:XBRIDGE:T4_T6:0002",
                thread_id="T6",
                originating_evidence="Vlasov (1938) & Anokhin (1968)",
                question_text="How did Anokhin's Functional System dynamic organ assembly relate to self-consistent fields in collective plasma mechanics (Vlasov)?",
                relation_under_test="FIELD_CONFINEMENT -> DYNAMIC_ASSEMBLY -> HOMEOSTATIC_RESULT",
                known_endpoints=["Vlasov", "Anokhin"],
                unknown_endpoint=True,
                temporal_window="1950-1970",
                priority_components=PriorityComponents(
                    novelty=0.95, bridge_potential=0.9, evidentiary_quality=0.7,
                    corroboration_potential=0.6, historical_gap_value=1.0, duplication_penalty=0.0
                ),
                generation=0,
                metadata={"bridge_id": "XBRIDGE:T4_T6", "intersection_concept": "Self-Consistent Dynamics & Functional Systems"},
                target_channel=InstitutionalChannelType.STRUCTURAL_MATHEMATICAL_CONTINUITY,
            ),
            ResearchQuestion(
                question_id="RQ:XBRIDGE:T5_T3:0001",
                thread_id="T5",
                originating_evidence="Chebyshev (1854) & Tikhonov (1943, 1963)",
                question_text="How did Chebyshev minimax polynomial approximation theory and Remez exchange algorithms get integrated into numerical regularization solvers on BESM computers for ill-posed Fredholm integral equations of the first kind?",
                relation_under_test="INVERT -> DISCRETIZE -> MINIMAX_APPROXIMATE -> NUMERICAL_REGULARIZE",
                known_endpoints=["Chebyshev", "Tikhonov", "Samarskii", "Lebedev"],
                unknown_endpoint=True,
                temporal_window="1955-1972",
                priority_components=PriorityComponents(
                    novelty=0.85, bridge_potential=0.95, evidentiary_quality=0.85,
                    corroboration_potential=0.85, historical_gap_value=0.8, duplication_penalty=0.0
                ),
                generation=0,
                metadata={"bridge_id": "XBRIDGE:T5_T3", "intersection_concept": "Finite Computational Inversion & Regularized Algorithms"},
                target_channel=InstitutionalChannelType.INSTITUTIONAL_CONTINUITY,
            ),
            ResearchQuestion(
                question_id="RQ:XBRIDGE:T1_T8:0001",
                thread_id="T1",
                originating_evidence="Euler Academy Texts & Chebyshev Operator Formulations",
                question_text="Did Euler's Russian-language texts at the St. Petersburg Academy establish the native operator terminology (оператор, отображение, преобразование) that later biased Chebyshev, Markov, and Lyapunov toward relationship-first rather than object-first mathematical formulation?",
                relation_under_test="ACADEMY_TRANSLATION -> SEMANTIC_MINTING -> RELATIONAL_GRAMMAR",
                known_endpoints=["Euler", "Chebyshev", "Lyapunov"],
                unknown_endpoint=True,
                temporal_window="1740-1895",
                priority_components=PriorityComponents(
                    novelty=0.9, bridge_potential=0.9, evidentiary_quality=0.8,
                    corroboration_potential=0.7, historical_gap_value=0.9, duplication_penalty=0.0
                ),
                generation=0,
                metadata={"bridge_id": "XBRIDGE:T1_T8", "intersection_concept": "Persistence of Relational Vocabulary across Eras"},
                target_channel=InstitutionalChannelType.DOCUMENTED_CITATION_TRANSFER,
            ),
            ResearchQuestion(
                question_id="RQ:XBRIDGE:T7_T2:0001",
                thread_id="T7",
                originating_evidence="MIAN & Ural State Seminars on Control",
                question_text="Through which specific seminars (e.g. MIAN Steklov, MSU Mechanics-Mathematics, or Ural State University) did Krasovskii and Pontryagin students transfer optimal feedback regulation into TsAGI, NII-88, and Korolev's OKB-1?",
                relation_under_test="MIAN_SEMINAR -> STUDENT_DEFENSE -> LAB_TRANSFER -> OKB_DEPLOYMENT",
                known_endpoints=["Pontryagin", "Krasovskii", "TsAGI", "OKB-1"],
                unknown_endpoint=True,
                temporal_window="1953-1966",
                priority_components=PriorityComponents(
                    novelty=0.85, bridge_potential=0.95, evidentiary_quality=0.85,
                    corroboration_potential=0.9, historical_gap_value=0.9, duplication_penalty=0.0
                ),
                generation=0,
                metadata={"bridge_id": "XBRIDGE:T7_T2", "intersection_concept": "Institutional Conduit of Stability Mathematics into Control"},
                target_channel=InstitutionalChannelType.PERSONNEL_TRANSFER,
            ),
            ResearchQuestion(
                question_id="RQ:XBRIDGE:T6_T2:0001",
                thread_id="T6",
                originating_evidence="Tsetlin (1961) & Feldbaum (1960)",
                question_text="How did Tsetlin's stochastic automata interacting with unknown random media converge with Pontryagin's maximum principle in extremum-seeking and dual adaptive control systems (Feldbaum 1960)?",
                relation_under_test="UNKNOWN_MEDIA -> PROBE_STEP -> ESTIMATE_EXTREMUM -> CONTROL",
                known_endpoints=["Tsetlin", "Pontryagin", "Feldbaum"],
                unknown_endpoint=True,
                temporal_window="1959-1965",
                priority_components=PriorityComponents(
                    novelty=0.9, bridge_potential=1.0, evidentiary_quality=0.9,
                    corroboration_potential=0.85, historical_gap_value=0.85, duplication_penalty=0.0
                ),
                generation=0,
                metadata={"bridge_id": "XBRIDGE:T6_T2", "intersection_concept": "Stochastic Automata Adaptation vs Extremal Control"},
                target_channel=InstitutionalChannelType.DOCUMENTED_CITATION_TRANSFER,
            ),
            # --- 4 Core Cross-Graph (SOVCTX -> BCIG) Research Frontier Questions ---
            ResearchQuestion(
                question_id="RQ:BCIG_XGRAPH:0001",
                thread_id="T10",
                originating_evidence="Feldbaum (1960) Dual Control & Tsetlin (1961) Automata",
                question_text="When does acting to reduce uncertainty first become an explicit mathematical principle, and how does it propagate through Soviet control and cybernetics?",
                relation_under_test="REPRESENT -> PROBE (ACT_TO_KNOW) -> OBSERVE -> UPDATE -> CONTROL",
                known_endpoints=["Feldbaum", "Tsetlin", "Pontryagin", "Stratonovich"],
                unknown_endpoint=True,
                temporal_window="1955-1970",
                priority_components=PriorityComponents(
                    novelty=1.0, bridge_potential=1.0, evidentiary_quality=0.95,
                    corroboration_potential=0.9, historical_gap_value=1.0, duplication_penalty=0.0
                ),
                generation=0,
                metadata={"cross_graph_target": "BCIG:Epistemic Action (ACT_TO_KNOW)", "research_theme": "Epistemic Action"},
                target_channel=InstitutionalChannelType.STRUCTURAL_MATHEMATICAL_CONTINUITY,
            ),
            ResearchQuestion(
                question_id="RQ:BCIG_XGRAPH:0002",
                thread_id="T11",
                originating_evidence="Bernstein (1966), Anokhin (1968), Feldbaum (1960), Tsetlin (1961)",
                question_text="How do Bernstein's model of the future, Anokhin's action-result acceptor, Feldbaum's uncertainty reduction, and Tsetlin's adaptive automata relate historically and structurally?",
                relation_under_test="FUTURE_MODEL -> ACTION_ACCEPTOR -> PROBE_STEP -> CONVERGENCE",
                known_endpoints=["Bernstein", "Anokhin", "Feldbaum", "Tsetlin"],
                unknown_endpoint=True,
                temporal_window="1945-1970",
                priority_components=PriorityComponents(
                    novelty=0.95, bridge_potential=1.0, evidentiary_quality=0.9,
                    corroboration_potential=0.9, historical_gap_value=0.95, duplication_penalty=0.0
                ),
                generation=0,
                metadata={"cross_graph_target": "BCIG:Closed Adaptive Intelligence", "research_theme": "Internal Result Models"},
                target_channel=InstitutionalChannelType.STRUCTURAL_MATHEMATICAL_CONTINUITY,
            ),
            ResearchQuestion(
                question_id="RQ:BCIG_XGRAPH:0003",
                thread_id="T11",
                originating_evidence="Ashby (1952), Grey Walter (1950), Anokhin (1968)",
                question_text="Which cybernetic and bionic systems actually possess internally generated viability constraints (endogenous self-maintenance) integrated into the intelligence loop rather than externally supplied objectives?",
                relation_under_test="INTERNAL_DEFICIT -> ENDOGENOUS_GOAL -> ACTION -> VIABILITY_RESTORED",
                known_endpoints=["Anokhin", "Ashby", "Walter", "Bernstein"],
                unknown_endpoint=True,
                temporal_window="1948-1972",
                priority_components=PriorityComponents(
                    novelty=1.0, bridge_potential=1.0, evidentiary_quality=0.85,
                    corroboration_potential=0.85, historical_gap_value=1.0, duplication_penalty=0.0
                ),
                generation=0,
                metadata={"cross_graph_target": "BCIG:Endogenous Self-Maintenance", "research_theme": "Endogenous Self-Maintenance"},
                target_channel=InstitutionalChannelType.STRUCTURAL_MATHEMATICAL_CONTINUITY,
            ),
            ResearchQuestion(
                question_id="RQ:BCIG_XGRAPH:0004",
                thread_id="T12",
                originating_evidence="Chebyshev (1854), Samarskii (1967), Lebedev (1968)",
                question_text="How were bounded computation, approximation, uncertainty, limited memory, and real-time control treated as intrinsic mathematical parts of intelligent-system design?",
                relation_under_test="BOUNDED_MEMORY -> MINIMAX_APPROXIMATION -> INVERSE_REGULARIZATION -> REAL_TIME_CONTROL",
                known_endpoints=["Chebyshev", "Samarskii", "Lebedev", "Tikhonov"],
                unknown_endpoint=True,
                temporal_window="1955-1975",
                priority_components=PriorityComponents(
                    novelty=0.9, bridge_potential=0.95, evidentiary_quality=0.9,
                    corroboration_potential=0.85, historical_gap_value=0.9, duplication_penalty=0.0
                ),
                generation=0,
                metadata={"cross_graph_target": "BCIG:Resource-Bounded Intelligence", "research_theme": "Finite Intelligence"},
                target_channel=InstitutionalChannelType.INSTITUTIONAL_CONTINUITY,
            ),
        ]

        for q in seed_questions:
            if q.question_id not in self.ledger.questions:
                self.ledger.add_question(q)

    def allocate_cycle(self, total_slots: int = 10) -> FrontierCycleAllocation:
        """Divides cycle attention: 50% Established Spines (T1-T6), 30% Bridges, 20% Anomalies (T9)."""
        spines_quota = max(1, round(total_slots * 0.50))
        bridges_quota = max(1, round(total_slots * 0.30))
        anomalies_quota = max(1, total_slots - spines_quota - bridges_quota)

        # 1. Spines: T1 through T6 open questions that are NOT explicit cross-bridges or cross-graph
        spines_candidates = [
            q for q in self.ledger.get_open_questions()
            if q.thread_id in ("T1", "T2", "T3", "T4", "T5", "T6") and "XBRIDGE" not in q.question_id and "BCIG_XGRAPH" not in q.question_id
        ]
        spines_candidates.sort(key=lambda x: x.priority, reverse=True)
        selected_spines = spines_candidates[:spines_quota]

        # 2. Bridges: T7, T8, cross-bridge questions, or cross-graph questions
        bridges_candidates = [
            q for q in self.ledger.get_open_questions()
            if q.thread_id in ("T7", "T8") or "XBRIDGE" in q.question_id or "BCIG_XGRAPH" in q.question_id or "XBRIDGE" in q.metadata.get("bridge_id", "")
        ]
        bridges_candidates.sort(key=lambda x: x.priority, reverse=True)
        selected_bridges = bridges_candidates[:bridges_quota]

        # 3. Anomalies: T9 (pure discovery reserve)
        anomaly_candidates = [
            q for q in self.ledger.get_open_questions()
            if q.thread_id == "T9" or q.thread_id.startswith("T10_")
        ]
        anomaly_candidates.sort(key=lambda x: x.priority, reverse=True)
        selected_anomalies = anomaly_candidates[:anomalies_quota]

        return FrontierCycleAllocation(
            total_slots=total_slots,
            spines_quota=spines_quota,
            bridges_quota=bridges_quota,
            anomalies_quota=anomalies_quota,
            selected_spines=selected_spines,
            selected_bridges=selected_bridges,
            selected_anomalies=selected_anomalies,
        )

    def generate_discovery_report(
        self,
        new_relations: Optional[List[Dict[str, Any]]] = None,
        new_threads: Optional[List[Dict[str, Any]]] = None,
        saturated_threads: Optional[List[Dict[str, Any]]] = None,
        contradictions: Optional[List[Dict[str, Any]]] = None,
        anomalies: Optional[List[Dict[str, Any]]] = None,
    ) -> DiscoveryReport:
        """Builds a structured discovery-oriented autonomous report."""
        report = DiscoveryReport(
            cycle_timestamp=utc_now_iso(),
            new_relationships_discovered=new_relations or [],
            new_threads_spawned=new_threads or [],
            threads_saturated=saturated_threads or [],
            cross_thread_bridges=[b.to_dict() for b in self.cross_bridges],
            new_contradictions=contradictions or [],
            unexplained_anomalies=anomalies or [],
            hypotheses_strengthened=[
                "Relational duality: Russian/Soviet mathematical continuity is structured by operator transformations rather than isolated objects.",
                "Stability-to-control transfer: Krasovskii's feedback formulation directly connects Lyapunov stability with Pontryagin extremal regulation.",
            ],
            hypotheses_weakened=[
                "Binary East-West split: The corpus indicates international cross-currents (Leibniz, Euler, Wiener) rather than absolute isolation.",
            ],
        )
        return report
