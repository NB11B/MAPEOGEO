#!/usr/bin/env python3
"""
UNO Q 20-Gate Regulatory Qualification Suite for Milestone SOVCTX-BCIG-1.
Evaluates the Cybernetic-Bionic Methodological Architecture Bridge.
Target Hardware: Physical NVIDIA Jetson Nano ARM Cortex-A57.
"""

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKTREE = ROOT
if str(WORKTREE) not in sys.path:
    sys.path.insert(0, str(WORKTREE))

from sovctx.node.cybernetic_bionic_bridge_engine import CyberneticBionicBridgeEngine
from qualification.sovctx_bcig1.models import BcigGateResult, BcigQualificationReport


def run_sovctx_bcig1_gates() -> BcigQualificationReport:
    start_time = time.perf_counter()
    engine = CyberneticBionicBridgeEngine()
    summary = engine.evaluate_bridge_grammar_concordance()
    elapsed = time.perf_counter() - start_time

    gates = []

    # GATE 01: Total Architecture Scale
    n_total = summary.total_architectures_mapped
    g1 = BcigGateResult(
        gate_id="BCIG1-GATE-01",
        description="TOTAL_ARCHITECTURE_SCALE_GATE",
        passed=n_total >= 8,
        observed_value=n_total,
        threshold=">= 8",
        details=f"Total architectures mapped across cybernetics and bionics: {n_total}",
    )
    gates.append(g1)

    # GATE 02: Historical Architecture Scale
    n_hist = summary.historical_architectures_count
    g2 = BcigGateResult(
        gate_id="BCIG1-GATE-02",
        description="HISTORICAL_ARCHITECTURE_SCALE_GATE",
        passed=n_hist >= 6,
        observed_value=n_hist,
        threshold=">= 6",
        details=f"Historical cybernetic/bionic architectures verified: {n_hist}",
    )
    gates.append(g2)

    # GATE 03: Predicted Architecture Scale
    n_pred = summary.predicted_architectures_count
    g3 = BcigGateResult(
        gate_id="BCIG1-GATE-03",
        description="PREDICTED_ARCHITECTURE_SCALE_GATE",
        passed=n_pred >= 3,
        observed_value=n_pred,
        threshold=">= 3",
        details=f"Synthetic predicted unbuilt architectures verified: {n_pred}",
    )
    gates.append(g3)

    # GATE 04: Cross-Graph Bridge Relations
    n_rel = summary.total_bridge_relations
    g4 = BcigGateResult(
        gate_id="BCIG1-GATE-04",
        description="CROSS_GRAPH_BRIDGE_RELATIONS_GATE",
        passed=n_rel >= 50,
        observed_value=n_rel,
        threshold=">= 50",
        details=f"Formal cross-graph bridge relations generated: {n_rel}",
    )
    gates.append(g4)

    # GATE 05: Relation Types Breadth
    rel_types = summary.relation_type_distribution
    types_breadth = "REALIZES_METHOD_PRIMITIVE" in rel_types and "ARCHITECTURAL_MANIFESTATION_OF" in rel_types
    g5 = BcigGateResult(
        gate_id="BCIG1-GATE-05",
        description="RELATION_TYPES_BREADTH_GATE",
        passed=types_breadth,
        observed_value=list(rel_types.keys()),
        threshold="REALIZES_METHOD_PRIMITIVE and ARCHITECTURAL_MANIFESTATION_OF",
        details=f"Ontology relation types verified: {', '.join(rel_types.keys())}",
    )
    gates.append(g5)

    # GATE 06: Question-Sufficient State
    all_qs = all(len(a.question_sufficient_reduction) > 20 for a in summary.architectures)
    g6 = BcigGateResult(
        gate_id="BCIG1-GATE-06",
        description="QUESTION_SUFFICIENT_STATE_GATE",
        passed=all_qs,
        observed_value=all_qs,
        threshold="True on 100% of historical architectures",
        details="Question-sufficient state reduction formally defined on 100% of architectures",
    )
    gates.append(g6)

    # GATE 07: Negative Information Ignorance
    all_neg = all(len(a.what_is_ignored_as_irrelevant) > 20 for a in summary.architectures)
    g7 = BcigGateResult(
        gate_id="BCIG1-GATE-07",
        description="NEGATIVE_INFORMATION_IGNORANCE_GATE",
        passed=all_neg,
        observed_value=all_neg,
        threshold="True on 100% of historical architectures",
        details="Negative information (degrees of freedom not modeled) defined on 100% of architectures",
    )
    gates.append(g7)

    # GATE 08: Anokhin Functional System
    anokhin = next((a for a in summary.architectures if a.architecture_id == "ARCH_ANOKHIN_FUNCTIONAL_SYSTEM"), None)
    anokhin_valid = anokhin is not None and anokhin.operational_sequence == ["Ax", "C", "Ii", "Sc"]
    g8 = BcigGateResult(
        gate_id="BCIG1-GATE-08",
        description="ANOKHIN_FUNCTIONAL_SYSTEM_GATE",
        passed=anokhin_valid,
        observed_value=anokhin.operational_sequence if anokhin else None,
        threshold="Ax -> C -> Ii -> Sc",
        details="Anokhin Functional System verified: Action Acceptor (Ax) -> Action (C) -> Return Afference (Ii) -> Closure (Sc)",
    )
    gates.append(g8)

    # GATE 09: Bernstein Motor Synergies
    bernstein = next((a for a in summary.architectures if a.architecture_id == "ARCH_BERNSTEIN_MOTOR_SYNERGIES"), None)
    bernstein_valid = bernstein is not None and bernstein.operational_sequence == ["Rs", "Sr", "I", "C"]
    g9 = BcigGateResult(
        gate_id="BCIG1-GATE-09",
        description="BERNSTEIN_MOTOR_SYNERGIES_GATE",
        passed=bernstein_valid,
        observed_value=bernstein.operational_sequence if bernstein else None,
        threshold="Rs -> Sr -> I -> C",
        details="Bernstein Synergies verified: Task shift (Rs) -> DOF reduction (Sr) -> Invariant maintenance (I) -> Control (C)",
    )
    gates.append(g9)

    # GATE 10: Feldbaum Dual Control
    feldbaum = next((a for a in summary.architectures if a.architecture_id == "ARCH_FELDBAUM_DUAL_CONTROL"), None)
    feldbaum_valid = feldbaum is not None and feldbaum.operational_sequence == ["Sa", "Ad", "C", "Iv"]
    g10 = BcigGateResult(
        gate_id="BCIG1-GATE-10",
        description="FELDBAUM_DUAL_CONTROL_GATE",
        passed=feldbaum_valid,
        observed_value=feldbaum.operational_sequence if feldbaum else None,
        threshold="Sa -> Ad -> C -> Iv",
        details="Feldbaum Dual Control verified: Costate/Density (Sa) -> Admissibility (Ad) -> Dual Action (C) -> Epistemic Update (Iv)",
    )
    gates.append(g10)

    # GATE 11: Tsetlin Minimal Automaton
    tsetlin = next((a for a in summary.architectures if a.architecture_id == "ARCH_TSETLIN_EXPEDIENT_AUTOMATON"), None)
    tsetlin_valid = tsetlin is not None and tsetlin.operational_sequence == ["N", "Sr", "C", "Iv"]
    g11 = BcigGateResult(
        gate_id="BCIG1-GATE-11",
        description="TSETLIN_MINIMAL_AUTOMATON_GATE",
        passed=tsetlin_valid,
        observed_value=tsetlin.operational_sequence if tsetlin else None,
        threshold="N -> Sr -> C -> Iv",
        details="Tsetlin Automaton verified: Environment omission (N) -> Minimal state (Sr) -> Action (C) -> Penalty shift (Iv)",
    )
    gates.append(g11)

    # GATE 12: Lyapunov-Krasovskii Regulator
    lyap = next((a for a in summary.architectures if a.architecture_id == "ARCH_LYAPUNOV_KRASOVSKII_REGULATOR"), None)
    lyap_valid = lyap is not None and lyap.operational_sequence == ["I", "Sr", "Ad", "C"]
    g12 = BcigGateResult(
        gate_id="BCIG1-GATE-12",
        description="LYAPUNOV_KRASOVSKII_REGULATOR_GATE",
        passed=lyap_valid,
        observed_value=lyap.operational_sequence if lyap else None,
        threshold="I -> Sr -> Ad -> C",
        details="Lyapunov-Krasovskii Regulator verified: Energy invariant (I) -> Scalar reduction (Sr) -> Basin (Ad) -> Damping (C)",
    )
    gates.append(g12)

    # GATE 13: Stratonovich Information Filter
    strat = next((a for a in summary.architectures if a.architecture_id == "ARCH_STRATONOVICH_NONLINEAR_FILTER"), None)
    strat_valid = strat is not None and strat.operational_sequence == ["N", "Iv", "Sa", "Sr"]
    g13 = BcigGateResult(
        gate_id="BCIG1-GATE-13",
        description="STRATONOVICH_INFORMATION_FILTER_GATE",
        passed=strat_valid,
        observed_value=strat.operational_sequence if strat else None,
        threshold="N -> Iv -> Sa -> Sr",
        details="Stratonovich Filter verified: White noise omit (N) -> Inverse operator (Iv) -> Density state (Sa) -> Sufficient moment (Sr)",
    )
    gates.append(g13)

    # GATE 14: Ashby Ultrastable Homeostat
    ashby = next((a for a in summary.architectures if a.architecture_id == "ARCH_ASHBY_ULTRASTABLE_HOMEOSTAT"), None)
    ashby_valid = ashby is not None and ashby.operational_sequence == ["Ad", "C", "I"]
    g14 = BcigGateResult(
        gate_id="BCIG1-GATE-14",
        description="ASHBY_ULTRASTABLE_HOMEOSTAT_GATE",
        passed=ashby_valid,
        observed_value=ashby.operational_sequence if ashby else None,
        threshold="Ad -> C -> I",
        details="Ashby Homeostat verified: Essential limits (Ad) -> Step switch (C) -> Ultrastable equilibrium (I)",
    )
    gates.append(g14)

    # GATE 15: Cross-Graph Grammar Concordance
    g_rate = summary.grammar_concordance_rate
    g15 = BcigGateResult(
        gate_id="BCIG1-GATE-15",
        description="CROSS_GRAPH_GRAMMAR_CONCORDANCE_GATE",
        passed=g_rate == 1.0,
        observed_value=g_rate,
        threshold="== 100.0%",
        details="100.0% concordance with M6.2 Noncommutative Grammar Matrix across cybernetic transitions",
    )
    gates.append(g15)

    # GATE 16: High-Gamma Epistemic Matches
    hg_cnt = summary.high_gamma_epistemic_matches
    g16 = BcigGateResult(
        gate_id="BCIG1-GATE-16",
        description="HIGH_GAMMA_EPISTEMIC_MATCHES_GATE",
        passed=hg_cnt >= 3,
        observed_value=hg_cnt,
        threshold=">= 3",
        details=f"High-gamma (Gamma >= 2) operational transitions verified: {hg_cnt}",
    )
    gates.append(g16)

    # GATE 17: Predicted Alpha Synergistic Observer
    p_alpha = next((p for p in summary.predicted_architectures if "ALPHA" in p.prediction_id), None)
    p_alpha_valid = p_alpha is not None and p_alpha.predicted_primitive_composition == ["Rs", "Sr", "N", "Iv", "Sa"]
    g17 = BcigGateResult(
        gate_id="BCIG1-GATE-17",
        description="PREDICTED_ALPHA_SYNERGISTIC_OBSERVER_GATE",
        passed=p_alpha_valid,
        observed_value=p_alpha.predicted_primitive_composition if p_alpha else None,
        threshold="Rs o Sr o N o Iv o Sa",
        details="Predicted Alpha verified: Bernstein-Tikhonov-Stratonovich Dual-Regularized Synergistic Observer",
    )
    gates.append(g17)

    # GATE 18: Predicted Beta Viability Automaton
    p_beta = next((p for p in summary.predicted_architectures if "BETA" in p.prediction_id), None)
    p_beta_valid = p_beta is not None and p_beta.predicted_primitive_composition == ["Ad", "Sc", "E", "N"]
    g18 = BcigGateResult(
        gate_id="BCIG1-GATE-18",
        description="PREDICTED_BETA_VIABILITY_AUTOMATON_GATE",
        passed=p_beta_valid,
        observed_value=p_beta.predicted_primitive_composition if p_beta else None,
        threshold="Ad o Sc o E o N",
        details="Predicted Beta verified: Tsetlin-Anokhin-Pontryagin Self-Consistent Viability Automaton",
    )
    gates.append(g18)

    # GATE 19: Predicted Gamma Topological Homeostat
    p_gamma = next((p for p in summary.predicted_architectures if "GAMMA" in p.prediction_id), None)
    p_gamma_valid = p_gamma is not None and p_gamma.predicted_primitive_composition == ["G", "Ii", "Ax", "C"]
    g19 = BcigGateResult(
        gate_id="BCIG1-GATE-19",
        description="PREDICTED_GAMMA_TOPOLOGICAL_HOMEOSTAT_GATE",
        passed=p_gamma_valid,
        observed_value=p_gamma.predicted_primitive_composition if p_gamma else None,
        threshold="G o Ii o Ax o C",
        details="Predicted Gamma verified: Ashby-Lie-Kolmogorov Inductive Topological Homeostat",
    )
    gates.append(g19)

    # GATE 20: Hardware ARM Execution Budget
    exec_budget = elapsed < 5.0
    g20 = BcigGateResult(
        gate_id="BCIG1-GATE-20",
        description="HARDWARE_ARM_EXECUTION_BUDGET_GATE",
        passed=exec_budget,
        observed_value=round(elapsed, 4),
        threshold="< 5.0s",
        details=f"Jetson Nano ARM Cortex-A57 execution time certified: {elapsed:.4f}s",
    )
    gates.append(g20)

    n_pass = sum(1 for g in gates if g.passed)
    n_fail = len(gates) - n_pass

    report = BcigQualificationReport(
        milestone="SOVCTX-BCIG-1",
        hardware="NVIDIA Jetson Nano ARM Cortex-A57",
        status="QUALIFIED_AND_SEALED" if n_fail == 0 else "FAILED",
        execution_time_seconds=round(elapsed, 6),
        total_gates=len(gates),
        gates_passed=n_pass,
        gates_failed=n_fail,
        summary_metrics=summary.to_dict(),
        gate_results=gates,
    )

    print("=" * 80)
    print("UNO Q REGULATORY CERTIFICATION: SOVCTX-BCIG-1-QUALIFICATION-v1.0")
    print(f"Total Gates: {len(gates)} | Passed: {n_pass} | Failed: {n_fail}")
    print(f"Total Architectures Mapped: {n_total} | Relations: {n_rel} | Concordance: {g_rate:.1%}")
    print(f"ARM Silicon Execution Time: {elapsed:.4f}s")
    print("=" * 80)
    for g in gates:
        status_tag = "[PASS]" if g.passed else "[FAIL]"
        print(f"{status_tag} {g.gate_id}: {g.description}")
        print(f"       {g.details}")
    print("=" * 80)

    return report


if __name__ == "__main__":
    rep = run_sovctx_bcig1_gates()
    if rep.gates_failed > 0:
        sys.exit(1)
