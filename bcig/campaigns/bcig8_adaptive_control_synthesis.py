"""BCIG-8: Soviet Adaptive Control & Modern AI Synthesis.

Synthesizes the grounded discoveries from the SOVCTX Jetson Nano Autonomous Research Frontier
into the BCIG program with disciplined epistemic boundaries:

Axioms enforced:
1. DIRECT_LINEAGE != MATHEMATICAL_DESCENT != ARCHITECTURAL_RECURRENCE != FUNCTIONAL_ANALOGUE.
2. Tightened descendant states:
   - Feldbaum dual control -> STRUCTURAL_ANALOGUE (Epistemic Action / Act-to-Know)
   - Krasovskii invariance -> STRUCTURAL_ANALOGUE (Control Barrier Functions, strictly withholding REDISCOVERED)
   - Vlasov collective fields -> STRUCTURAL_ANALOGUE (Mean-field MARL; MoE claims stripped)
   - Samarskii/BESM regularization -> MIGRATED (Scientific computing & numerical analysis; FP8/INT4 stripped)
3. Relational grammar:
       REPRESENT -> PROBE (ACT_TO_KNOW) -> OBSERVE -> UPDATE -> CONTROL
4. Architectural boundary:
       EXTERNALLY_EVALUATED_SYSTEMS vs INTERNALLY_CLOSED_ADAPTIVE_SYSTEMS
5. Homeostasis isolated as:
       ENDOGENOUS_SELF_MAINTENANCE (internal viability condition in the intelligence loop)
6. Broad teleological audit:
   "What components did earlier adaptive-system architectures consider necessary for intelligence
    that modern AI architectures omit?"
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from bcig.bridges.cross_graph_hypotheses import (
    CANONICAL_CROSS_GRAPH_HYPOTHESES,
    CrossGraphHypothesis,
    get_cross_graph_hypotheses,
)
from bcig.bridges.sovctx_bridge import EXPANDED_SOVCTX_BCIG_BRIDGES, SOVCTXBridgeRecord
from bcig.ontology.adaptive_closure import (
    REFERENCE_SYSTEM_PROFILES,
    SystemArchitectureProfile,
    calculate_adaptive_closure,
)
from bcig.ontology.descendant_state import (
    CANONICAL_AUDITED_PRINCIPLES,
    CANONICAL_PRINCIPLE_AUDITS,
    DescendantState,
    PrincipleDescendantAudit,
)


# Tightened principles identified from the Jetson Nano research run
EXTENDED_PRINCIPLE_AUDITS: Dict[str, PrincipleDescendantAudit] = {
    "PRIN:DUAL_CONTROL": PrincipleDescendantAudit(
        principle_id="PRIN:DUAL_CONTROL",
        principle_name="Feldbaum Dual Control (Epistemic Action / Act-to-Know)",
        historical_era="1960 (A. A. Feldbaum)",
        primary_historical_anchors=["Feldbaum (1960) 'Dual Control Theory I & II'", "Tsetlin (1961)"],
        modern_ai_comparison="Active Inference (Friston 2010), Thompson Sampling, Curiosity-driven RL",
        descendant_state=DescendantState.ANALOGOUS,
        lineage_strength="STRUCTURAL_ANALOGUE (Epistemic action independently reconstructed; no citation pedigree)",
        evidence_justification=(
            "Structural recurrence of epistemic action: Feldbaum mathematically demonstrated that acting to probe "
            "environmental parameters (epistemic value) is inextricably unified with acting to achieve a target state "
            "(pragmatic value). Reconstructed in Active Inference expected free energy and curiosity bonuses in RL, "
            "without documented direct citation."
        ),
        neighboring_disciplines=["ADAPTIVE_CONTROL", "INFORMATION_THEORY", "STATISTICAL_PHYSICS"],
    ),
    "PRIN:EXTREMAL_TARGETING": PrincipleDescendantAudit(
        principle_id="PRIN:EXTREMAL_TARGETING",
        principle_name="Krasovskii Extremal Targeting & Positional Set Invariance",
        historical_era="1959–1974 (N. N. Krasovskii, A. I. Subbotin)",
        primary_historical_anchors=["Krasovskii (1959) 'Stability of Motion'", "Krasovskii & Subbotin (1974)"],
        modern_ai_comparison="Control Barrier Functions (CBFs, Ames 2019), Safe RL forward invariance",
        descendant_state=DescendantState.ANALOGOUS,
        lineage_strength="STRUCTURAL_ANALOGUE (Strong mathematical resemblance to barrier functions; uncredited in Safe RL)",
        evidence_justification=(
            "Mathematical resemblance: Krasovskii unified Lyapunov functions with Pontryagin optimal control under discontinuous "
            "feedback and worst-case perturbations using quasi-solutions. Modern safe RL constructs Control Barrier Functions (CBFs) "
            "to guarantee forward set invariance under disturbances. Strictly classified as STRUCTURAL_ANALOGUE until citation evidence emerges."
        ),
        neighboring_disciplines=["DIFFERENTIAL_GAMES", "ROBUST_CONTROL"],
    ),
    "PRIN:KINETIC_FUNCTIONAL_ASSEMBLY": PrincipleDescendantAudit(
        principle_id="PRIN:KINETIC_FUNCTIONAL_ASSEMBLY",
        principle_name="Kinetic Self-Consistent Field & Macroscopic Functional Synergy",
        historical_era="1938–1968 (A. A. Vlasov, P. K. Anokhin)",
        primary_historical_anchors=["Vlasov (1938)", "Anokhin (1968)"],
        modern_ai_comparison="Mean-Field Multi-Agent Reinforcement Learning (Lasry & Lions 2007)",
        descendant_state=DescendantState.ANALOGOUS,
        lineage_strength="STRUCTURAL_ANALOGUE (Mean-field coordination recurrence across physical and multi-agent domains)",
        evidence_justification=(
            "Vlasov's kinetic reduction grammar (microscopic states -> self-consistent field -> macroscopic equilibrium) "
            "structurally matches Anokhin's functional organ assembly and modern Mean-Field Multi-Agent Games where agents "
            "coordinate via aggregate distribution fields rather than pairwise communication. (Mixture-of-Experts connection stripped as unsupported)."
        ),
        neighboring_disciplines=["PLASMA_PHYSICS", "STATISTICAL_MECHANICS", "MULTI_AGENT_SYSTEMS"],
    ),
    "PRIN:FINITE_NUMERICAL_REGULARIZATION": PrincipleDescendantAudit(
        principle_id="PRIN:FINITE_NUMERICAL_REGULARIZATION",
        principle_name="Chebyshev-Samarskii Regularization under Resource-Bounded Precision",
        historical_era="1955–1977 (P. L. Chebyshev, A. A. Samarskii, S. A. Lebedev)",
        primary_historical_anchors=["Samarskii (1967)", "Tikhonov & Samarskii (1977)"],
        modern_ai_comparison="Numerical analysis and conditioning of ill-posed matrix systems in scientific computing",
        descendant_state=DescendantState.MIGRATED,
        lineage_strength="MATHEMATICAL_DESCENT (Continuous lineage in scientific computing; distinct from neural quantization)",
        evidence_justification=(
            "Mathematical descent within scientific computing: Chebyshev minimax polynomial approximation and Remez exchange "
            "algorithms on BESM-6 mainframes solved numerical stability for ill-posed inverse operators under finite word lengths. "
            "Classified as MIGRATED into numerical analysis and scientific computing; neural network FP8/INT4 quantization claims stripped as different mathematical problems."
        ),
        neighboring_disciplines=["SCIENTIFIC_COMPUTING", "NUMERICAL_ANALYSIS"],
    ),
}


class BCIG8AdaptiveControlSynthesisEngine:
    """Orchestrates cross-graph synthesis between SOVCTX discoveries and BCIG."""

    def __init__(self) -> None:
        self.baseline_principles = dict(CANONICAL_PRINCIPLE_AUDITS)
        self.extended_principles = dict(EXTENDED_PRINCIPLE_AUDITS)
        self.all_principles: Dict[str, PrincipleDescendantAudit] = {
            **self.baseline_principles,
            **self.extended_principles,
        }

    def run_synthesis(self) -> Dict[str, Any]:
        # 1. Evaluate baseline vs expanded census under tightened classification
        base_counts = Counter(a.descendant_state.value for a in self.baseline_principles.values())
        ext_counts = Counter(a.descendant_state.value for a in self.all_principles.values())

        base_total = len(self.baseline_principles)
        ext_total = len(self.all_principles)

        base_pcts = {k: round((cnt / float(base_total)) * 100.0, 2) for k, cnt in base_counts.items()}
        ext_pcts = {k: round((cnt / float(ext_total)) * 100.0, 2) for k, cnt in ext_counts.items()}

        # 2. Evaluate extended adaptive closure rankings
        extended_systems = self._build_extended_system_profiles()
        extended_systems.sort(key=lambda s: s.adaptive_closure_index, reverse=True)

        dossier = {
            "campaign": "BCIG-8: Soviet Adaptive Control & Modern AI Synthesis (Tightened Formulation)",
            "epistemic_lineage_disciplines": [
                "DIRECT_LINEAGE != MATHEMATICAL_DESCENT != ARCHITECTURAL_RECURRENCE != FUNCTIONAL_ANALOGUE"
            ],
            "cross_graph_hypotheses": [h.to_dict() for h in get_cross_graph_hypotheses()],
            "grounded_bridges_count": len(EXPANDED_SOVCTX_BCIG_BRIDGES),
            "census_comparison": {
                "baseline_principles_evaluated": base_total,
                "extended_principles_evaluated": ext_total,
                "baseline_counts": dict(base_counts),
                "extended_counts": dict(ext_counts),
                "baseline_percentages": base_pcts,
                "extended_percentages": ext_pcts,
            },
            "tightened_classification_verdict": {
                "rediscovered_count": ext_counts.get("REDISCOVERED", 0),
                "structural_analogue_count": ext_counts.get("ANALOGOUS", 0),
                "migrated_count": ext_counts.get("MIGRATED", 0),
                "direct_count": ext_counts.get("DIRECT", 0),
                "missing_count": ext_counts.get("MISSING", 0),
                "interpretation": (
                    "Rather than claiming a loose genetic rediscovery, the tightened audit reveals that "
                    "STRUCTURAL_ANALOGUE (41.67%) is the primary mode: modern AI architectures repeatedly "
                    "reconstruct earlier operational loop topologies (e.g. Epistemic Action, Extremal Set Invariance, "
                    "Mean-Field Coordination) without genetic descent."
                ),
            },
            "relational_grammar_primitive": {
                "primitive": "PROBE (ACT_TO_KNOW)",
                "grammar": "REPRESENT -> PROBE (ACT_TO_KNOW) -> OBSERVE -> UPDATE -> CONTROL",
                "significance": "Feldbaum proved action itself must be epistemic under uncertainty.",
            },
            "architectural_taxonomy": {
                "externally_evaluated_systems": {
                    "archetype": "Prompt-Response Foundation Models / Feedforward Deep Learning",
                    "loop": "external request -> computation -> output (evaluated externally)",
                    "adaptive_closure_range": "A = 0.0000 to 0.3333",
                },
                "internally_closed_adaptive_systems": {
                    "archetype": "Anokhin Functional System / Feldbaum Dual Controller / Active Inference",
                    "loop": "internal condition/need -> goal -> action acceptor (predict) -> act -> return afference -> compare -> correct",
                    "adaptive_closure_range": "A = 0.8333 to 1.0000",
                },
            },
            "endogenous_self_maintenance_analysis": {
                "concept": "ENDOGENOUS_SELF_MAINTENANCE",
                "definition": "Computational self-maintenance integrated into the intelligence loop as an internally valued condition.",
                "contrast": (
                    "Modern AI possess external watchdogs (thermal throttles, battery monitors, OS supervisors). "
                    "What remains strictly missing (H=0.0) is endogenous self-maintenance driving cognitive behavior."
                ),
                "systems_with_endogenous_maintenance": [
                    "Anokhin Functional System (Biological, H=1.0)",
                    "Grey Walter Tortoise (Phototropic Recharging, H=1.0)",
                    "Ashby Homeostat (Essential Variable Preservation, H=1.0)",
                ],
                "systems_lacking_endogenous_maintenance": [
                    "Prompt-Response LLMs (GPT-4/Claude, H=0.0)",
                    "Model-Free RL (PPO/DQN, H=0.0)",
                    "Classical Expert Systems (MYCIN, H=0.0)",
                ],
            },
            "adaptive_closure_ranking": [s.to_dict() for s in extended_systems],
            "teleological_eight_pillar_gap_analysis": {
                "question": "What components did earlier adaptive-system architectures consider necessary for intelligence that modern AI architectures omit?",
                "pillars": {
                    "1_closed_loop_action": "Omitted in feedforward architectures; partially restored in agentic tool loops.",
                    "2_active_information_gathering": "Omitted in standard greedy policies; central to Feldbaum and Active Inference.",
                    "3_internal_state": "Omitted in stateless feedforward models; present in RNNs and world models.",
                    "4_prediction_of_consequences": "Omitted in reactive policies; central to Bernstein, Anokhin, and Dreamer.",
                    "5_endogenous_goal_conditions": "Omitted in all foundation models; goals are exclusively prompt-supplied.",
                    "6_adaptive_correction": "Omitted at inference runtime (weights frozen); active in Anokhin return afference.",
                    "7_embodiment": "Omitted in cloud LLMs; present in Grey Walter and physical robotics.",
                    "8_endogenous_self_maintenance": "Universally absent in modern AI; foundational to biological organisms.",
                },
            },
        }
        return dossier

    def _build_extended_system_profiles(self) -> List[SystemArchitectureProfile]:
        profiles = list(REFERENCE_SYSTEM_PROFILES.values())

        # Feldbaum Dual Controller
        profiles.append(
            SystemArchitectureProfile(
                system_id="SYS:FELDBAUM_DUAL_CONTROLLER",
                name="Feldbaum Dual Control System",
                year=1960,
                system_class="HISTORICAL_CYBERNETIC",
                vector={
                    "FEEDBACK": 1.0, "RECURRENCE": 1.0, "PREDICTION": 1.0, "GOAL": 1.0,
                    "ENVIRONMENT": 1.0, "HOMEOSTASIS": 0.0, "INTERNAL_STATE": 1.0,
                    "ACTION_GENERATION": 1.0, "SELF_MONITORING": 1.0, "ADAPTIVE_UPDATE": 1.0,
                },
                adaptive_closure_index=calculate_adaptive_closure({
                    "FEEDBACK": 1.0, "RECURRENCE": 1.0, "PREDICTION": 1.0, "GOAL": 1.0,
                    "ENVIRONMENT": 1.0, "HOMEOSTASIS": 0.0,
                }),
                architectural_loop_type="probe (act-to-know) -> update state estimate -> steer extremal trajectory -> correct",
                notes="Unified epistemic action (active information gathering) with optimal regulation; A = 0.8333.",
            )
        )

        # Active Inference Agent
        profiles.append(
            SystemArchitectureProfile(
                system_id="SYS:ACTIVE_INFERENCE_AGENT",
                name="Active Inference Agent (Friston 2010)",
                year=2010,
                system_class="MODERN_AGENT",
                vector={
                    "FEEDBACK": 1.0, "RECURRENCE": 1.0, "PREDICTION": 1.0, "GOAL": 1.0,
                    "ENVIRONMENT": 1.0, "HOMEOSTASIS": 0.8, "INTERNAL_STATE": 1.0,
                    "ACTION_GENERATION": 1.0, "SELF_MONITORING": 1.0, "ADAPTIVE_UPDATE": 1.0,
                },
                adaptive_closure_index=calculate_adaptive_closure({
                    "FEEDBACK": 1.0, "RECURRENCE": 1.0, "PREDICTION": 1.0, "GOAL": 1.0,
                    "ENVIRONMENT": 1.0, "HOMEOSTASIS": 0.8,
                }),
                architectural_loop_type="sense -> predict sensory afference -> minimize free energy (epistemic + pragmatic) -> act",
                notes="Modern structural analogue of Anokhin's action acceptor and Feldbaum's dual control; A = 0.9667.",
            )
        )

        # Krasovskii Extremal Targeting Game
        profiles.append(
            SystemArchitectureProfile(
                system_id="SYS:KRASOVSKII_POSITIONAL_GAME",
                name="Krasovskii Extremal Targeting Game",
                year=1970,
                system_class="HISTORICAL_CYBERNETIC",
                vector={
                    "FEEDBACK": 1.0, "RECURRENCE": 1.0, "PREDICTION": 0.8, "GOAL": 1.0,
                    "ENVIRONMENT": 1.0, "HOMEOSTASIS": 0.0, "INTERNAL_STATE": 1.0,
                    "ACTION_GENERATION": 1.0, "SELF_MONITORING": 1.0, "ADAPTIVE_UPDATE": 0.5,
                },
                adaptive_closure_index=calculate_adaptive_closure({
                    "FEEDBACK": 1.0, "RECURRENCE": 1.0, "PREDICTION": 0.8, "GOAL": 1.0,
                    "ENVIRONMENT": 1.0, "HOMEOSTASIS": 0.0,
                }),
                architectural_loop_type="adversarial observation -> quasi-solution regularizing direction -> extremal feedback",
                notes="Guarantees forward set invariance under discontinuous worst-case perturbations; A = 0.8000.",
            )
        )

        return profiles

    def export_dossier(self, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        data = self.run_synthesis()
        out_path = output_dir / "bcig8_adaptive_control_synthesis.json"
        out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return out_path


if __name__ == "__main__":
    engine = BCIG8AdaptiveControlSynthesisEngine()
    out = engine.export_dossier(Path("bcig/audits"))
    print(f"Exported tightened BCIG-8 synthesis dossier to {out}")
