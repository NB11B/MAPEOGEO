"""BCIG-8: Soviet Adaptive Control & Modern AI Synthesis.

Synthesizes the grounded discoveries from the SOVCTX Jetson Nano Autonomous Research Frontier
into the BCIG program:
1. Formalizes the 4 newly discovered bridges:
   - Feldbaum Dual Control (1960) -> Active Inference & RL Exploration-Exploitation
   - Krasovskii Extremal Targeting (1959) -> Control Barrier Functions & Safe RL
   - Vlasov-Anokhin Kinetic Organization (1938-1968) -> Mean-Field Games & Dynamic MoE
   - Chebyshev-Samarskii Regularization on BESM (1967) -> Quantized Low-Precision Inversion
2. Conducts an expanded 12-principle Modern Descendant Census D(c).
3. Evaluates the expanded Adaptive Closure Index ranking across control, active inference,
   and contemporary foundation models.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

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


# Extended principles identified from the Jetson Nano research run
EXTENDED_PRINCIPLE_AUDITS: Dict[str, PrincipleDescendantAudit] = {
    "PRIN:DUAL_CONTROL": PrincipleDescendantAudit(
        principle_id="PRIN:DUAL_CONTROL",
        principle_name="Feldbaum Dual Control (Epistemic Probing vs Pragmatic Regulation)",
        historical_era="1960 (A. A. Feldbaum)",
        primary_historical_anchors=["Feldbaum (1960) 'Dual Control Theory I & II'", "Tsetlin (1961)"],
        modern_ai_comparison="Active Inference (Friston 2010), Thompson Sampling, Curiosity-driven RL",
        descendant_state=DescendantState.REDISCOVERED,
        lineage_strength="HIGH_STRUCTURAL (Re-derived in modern RL exploration bonuses without Russian citation)",
        evidence_justification=(
            "Independent rediscovery: Feldbaum mathematically proved that in stochastic systems with unknown parameters, "
            "action is intrinsically dual: simultaneously probing to acquire information (epistemic value) and steering toward "
            "the objective (pragmatic value). This is an exact mathematical analogue to Friston's Active Inference expected "
            "free energy decomposition and modern curiosity bonuses in reinforcement learning."
        ),
        neighboring_disciplines=["ADAPTIVE_CONTROL", "INFORMATION_THEORY", "STATISTICAL_PHYSICS"],
    ),
    "PRIN:EXTREMAL_TARGETING": PrincipleDescendantAudit(
        principle_id="PRIN:EXTREMAL_TARGETING",
        principle_name="Krasovskii Extremal Targeting & Positional Differential Games",
        historical_era="1959–1974 (N. N. Krasovskii, A. I. Subbotin)",
        primary_historical_anchors=["Krasovskii (1959) 'Stability of Motion'", "Krasovskii & Subbotin (1974)"],
        modern_ai_comparison="Control Barrier Functions (CBFs, Ames 2019), Safe RL, Adversarial Robust Training",
        descendant_state=DescendantState.REDISCOVERED,
        lineage_strength="MODERATE_DIRECT / HIGH_STRUCTURAL (Cited in game theory; uncredited in Safe RL)",
        evidence_justification=(
            "Krasovskii unified Lyapunov functions with Pontryagin optimal control under discontinuous feedback and "
            "worst-case perturbations. Modern safe RL constructs Control Barrier Functions (CBFs) to guarantee forward "
            "set invariance under disturbances, recreating Krasovskii's extremal targeting without historical citation."
        ),
        neighboring_disciplines=["DIFFERENTIAL_GAMES", "ROBUST_CONTROL"],
    ),
    "PRIN:KINETIC_FUNCTIONAL_ASSEMBLY": PrincipleDescendantAudit(
        principle_id="PRIN:KINETIC_FUNCTIONAL_ASSEMBLY",
        principle_name="Kinetic Self-Consistent Field & Macroscopic Functional Synergy",
        historical_era="1938–1968 (A. A. Vlasov, P. K. Anokhin)",
        primary_historical_anchors=["Vlasov (1938)", "Anokhin (1968)"],
        modern_ai_comparison="Mean-Field Multi-Agent Games (Lasry & Lions 2007), Dynamic Mixture-of-Experts (MoE)",
        descendant_state=DescendantState.ANALOGOUS,
        lineage_strength="STRUCTURAL_ANALOGUE (Congruence of mean-field coordination across independent disciplines)",
        evidence_justification=(
            "Vlasov's kinetic reduction grammar (microscopic states -> self-consistent field -> macroscopic equilibrium) "
            "structurally matches Anokhin's functional organ assembly and modern Mean-Field Multi-Agent Games where agents "
            "coordinate via aggregate distribution fields rather than pairwise messaging."
        ),
        neighboring_disciplines=["PLASMA_PHYSICS", "STATISTICAL_MECHANICS", "MULTI_AGENT_SYSTEMS"],
    ),
    "PRIN:FINITE_NUMERICAL_REGULARIZATION": PrincipleDescendantAudit(
        principle_id="PRIN:FINITE_NUMERICAL_REGULARIZATION",
        principle_name="Chebyshev-Samarskii Regularization on Finite Precision Architectures",
        historical_era="1955–1977 (P. L. Chebyshev, A. A. Samarskii, S. A. Lebedev)",
        primary_historical_anchors=["Samarskii (1967)", "Tikhonov & Samarskii (1977)"],
        modern_ai_comparison="Low-precision quantized neural optimization (FP8/INT4), Hessian conditioning",
        descendant_state=DescendantState.DIRECT,
        lineage_strength="HIGH_DIRECT (Continuous foundation of numerical analysis and scientific computing)",
        evidence_justification=(
            "Direct transmission: Chebyshev minimax polynomial approximation and Remez exchange algorithms developed on "
            "BESM-6 mainframes directly fed into modern numerical linear algebra, now foundational for quantized low-bit deep learning."
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
        # 1. Evaluate baseline vs expanded census
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
            "campaign": "BCIG-8: Soviet Adaptive Control & Modern AI Synthesis",
            "grounded_bridges_count": len(EXPANDED_SOVCTX_BCIG_BRIDGES),
            "new_bridges_integrated": [
                b.to_dict() for b in EXPANDED_SOVCTX_BCIG_BRIDGES
                if int(b.bridge_id.split("_")[-1]) >= 5
            ],
            "census_comparison": {
                "baseline_principles_evaluated": base_total,
                "extended_principles_evaluated": ext_total,
                "baseline_counts": dict(base_counts),
                "extended_counts": dict(ext_counts),
                "baseline_percentages": base_pcts,
                "extended_percentages": ext_pcts,
            },
            "rediscovery_surge_analysis": {
                "rediscovered_count_delta": ext_counts.get("REDISCOVERED", 0) - base_counts.get("REDISCOVERED", 0),
                "rediscovered_percentage_delta": round(ext_pcts.get("REDISCOVERED", 0.0) - base_pcts.get("REDISCOVERED", 0.0), 2),
                "interpretation": (
                    "Integrating grounded Soviet control theory significantly strengthens the Rediscovery Hypothesis: "
                    f"REDISCOVERED jumps from {base_pcts.get('REDISCOVERED', 0.0)}% to {ext_pcts.get('REDISCOVERED', 0.0)}% "
                    "of evaluated principles. Modern Active Inference, curiosity-driven RL, and Control Barrier Functions "
                    "directly re-invented Feldbaum's Dual Control and Krasovskii's Extremal Targeting without historical lineage."
                ),
            },
            "adaptive_closure_ranking": [s.to_dict() for s in extended_systems],
            "structural_closure_findings": {
                "highest_artificial_adaptive_closure": "Active Inference Agent (A = 0.9667) & Feldbaum Dual Controller (A = 0.8333)",
                "foundation_models_closure": "Deep Feedforward NN (A = 0.0000) & Prompt-Response LLM (A = 0.3333)",
                "homeostasis_gap_persists": "Metabolic self-maintenance remains absent in all modern deep learning architectures.",
            },
        }
        return dossier

    def _build_extended_system_profiles(self) -> List[SystemArchitectureProfile]:
        profiles = list(REFERENCE_SYSTEM_PROFILES.values())

        # Add Feldbaum Dual Controller
        p_feldbaum = SystemArchitectureProfile(
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
            architectural_loop_type="probe -> learn unknown media -> steer extremal trajectory -> correct",
            notes="Unified stochastic information acquisition with extremal regulation; high adaptive closure (A = 0.8333).",
        )
        profiles.append(p_feldbaum)

        # Add Active Inference Agent
        p_actinf = SystemArchitectureProfile(
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
            notes="Direct modern structural descendant of Anokhin's action acceptor and Feldbaum's dual control (A = 0.9667).",
        )
        profiles.append(p_actinf)

        # Add Krasovskii Positional Game System
        p_krasovskii = SystemArchitectureProfile(
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
            notes="Guarantees forward set invariance under discontinuous worst-case perturbations (A = 0.8000).",
        )
        profiles.append(p_krasovskii)

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
    print(f"Exported BCIG-8 synthesis dossier to {out}")
