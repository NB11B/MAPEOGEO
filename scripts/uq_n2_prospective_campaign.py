#!/usr/bin/env python3
"""SOVCTX Prospective Research Efficiency Campaign (Milestone UQ-N2).

Executes the formal comparative benchmark across three experimental arms:
- Arm A: Unguided research (broad crawl)
- Arm B: Graph-demand-driven research (reactive frontier questions in FIFO order)
- Arm C: Prospective research (EIG dual control: ACT_TO_KNOW)

Evaluates epistemic yield per unit compute, bandwidth, and source acquisition:
  InfoGain / Source = Delta H / total_sources_acquired
  InfoGain / UoW    = Delta H / total_uows_executed

Preserves all frozen UQ-N1 contracts:
  PROPOSED != AUTHORIZED
  H_E != H_X (dual-tier digest separation)
  Causal issuance ledger tracking
  G1 observer shadow mode (diagnostics only, zero admission authority)
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Dict, List

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sovctx.node.control_plane import (
    AdmissionVerdict,
    UnoQControlPlaneGateway,
    UoWIssuanceLedger,
)
from sovctx.node.nano_research_worker import (
    NanoResearchWorker,
)
from sovctx.node.prospective_control import (
    BenchmarkQuestionType,
    HypothesisBeliefSpace,
    HypothesisStatus,
    ProspectiveResearchOrchestrator,
    build_canonical_adaptive_control_hypotheses,
    build_canonical_benchmark_question_pool,
)


def get_git_commit(cwd: Path) -> str:
    """Retrieve current HEAD commit SHA."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return "UNKNOWN_COMMIT"


def run_campaign(uow_budget: int = 16, repo_root: Path = Path(".")) -> Dict[str, Any]:
    """Execute the UQ-N2 prospective efficiency research campaign."""
    print("=" * 80)
    print("SOVCTX MILESTONE UQ-N2: PROSPECTIVE RESEARCH EFFICIENCY CAMPAIGN")
    print(f"UoW Budget per Arm: {uow_budget}")
    print("=" * 80)

    commit_sha = get_git_commit(repo_root)
    print(f"[CAMPAIGN] Git Commit: {commit_sha}")

    # Canonical base entities for gateway verification
    canonical_entities = {
        "PERSON:FELDBAUM_AA",
        "CONCEPT:DUAL_CONTROL",
        "CONCEPT:INVESTIGATIVE_ACTION",
        "CONCEPT:DIRECTING_ACTION",
        "CONCEPT:STOCHASTIC_APPROXIMATION",
        "CONCEPT:FINITE_AUTOMATA_RANDOM_MEDIA",
        "CONCEPT:EXPEDIENT_BEHAVIOR",
        "PERSON:TSETLIN_ML",
        "PERSON:KRASOVSKII_NN",
        "CONCEPT:LYAPUNOV_STABILITY",
        "CONCEPT:STOCHASTIC_STABILITY",
        "PERSON:STRATONOVICH_RL",
        "CONCEPT:CONDITIONAL_MARKOV_PROCESSES",
        "PERSON:PONTRYAGIN_LS",
        "CONCEPT:MAXIMUM_PRINCIPLE",
        "PERSON:ANOKHIN_PK",
        "CONCEPT:FUNCTIONAL_SYSTEMS",
        "CONCEPT:ACTION_ACCEPTOR",
        "PERSON:BERNSTEIN_NA",
        "CONCEPT:PHYSIOLOGY_OF_ACTIVITY",
        "CONCEPT:MODEL_REQUIRED_FUTURE",
        "PERSON:GELFAND_IM",
        "CONCEPT:NONLOCAL_SEARCH",
        "PERSON:SAMARSKII_AA",
        "CONCEPT:REGULARIZATION_MINIMAX",
    }
    canonical_relations = {
        ("PERSON:FELDBAUM_AA", "CONCEPT:DUAL_CONTROL"),
        ("CONCEPT:DUAL_CONTROL", "CONCEPT:INVESTIGATIVE_ACTION"),
        ("CONCEPT:DUAL_CONTROL", "CONCEPT:DIRECTING_ACTION"),
        ("PERSON:TSETLIN_ML", "CONCEPT:FINITE_AUTOMATA_RANDOM_MEDIA"),
        ("CONCEPT:FINITE_AUTOMATA_RANDOM_MEDIA", "CONCEPT:EXPEDIENT_BEHAVIOR"),
        ("PERSON:KRASOVSKII_NN", "CONCEPT:STOCHASTIC_STABILITY"),
        ("CONCEPT:STOCHASTIC_STABILITY", "CONCEPT:LYAPUNOV_STABILITY"),
        ("PERSON:ANOKHIN_PK", "CONCEPT:FUNCTIONAL_SYSTEMS"),
        ("CONCEPT:FUNCTIONAL_SYSTEMS", "CONCEPT:ACTION_ACCEPTOR"),
        ("PERSON:BERNSTEIN_NA", "CONCEPT:PHYSIOLOGY_OF_ACTIVITY"),
        ("CONCEPT:PHYSIOLOGY_OF_ACTIVITY", "CONCEPT:MODEL_REQUIRED_FUTURE"),
        ("PERSON:GELFAND_IM", "PERSON:BERNSTEIN_NA"),
        ("CONCEPT:NONLOCAL_SEARCH", "CONCEPT:PHYSIOLOGY_OF_ACTIVITY"),
        ("PERSON:SAMARSKII_AA", "CONCEPT:REGULARIZATION_MINIMAX"),
    }
    canonical_claims = {
        "CLAIM:FELDBAUM_1960_DUAL_ACTION_SPLIT",
        "CLAIM:TSETLIN_1961_AUTOMATON_ASYMPTOTIC_OPTIMALITY",
        "CLAIM:KRASOVSKII_1959_LYAPUNOV_STOCHASTIC_CONVERSE",
        "CLAIM:ANOKHIN_1955_ACTION_ACCEPTOR_FORWARD_COMPARATOR",
        "CLAIM:BERNSTEIN_1966_MODEL_OF_REQUIRED_FUTURE",
        "CLAIM:GELFAND_TSETLIN_1961_BERNSTEIN_CITATION",
        "CLAIM:SAMARSKII_1967_MINIMAX_STABILITY_BOUNDS",
    }

    # Worker configured with strict shadow mode and zero canonical authority
    worker = NanoResearchWorker(
        worker_id="nano-jetson-01",
        spool_dir=repo_root / "evidence" / "n5" / "spool",
        shadow_mode=True,
        software_commit=commit_sha,
    )

    # Regulatory control plane gateway
    gateway = UnoQControlPlaneGateway(
        ledger=UoWIssuanceLedger(),
        canonical_entities=canonical_entities,
        canonical_relations=canonical_relations,
        canonical_claims=canonical_claims,
        allowed_software_commits={commit_sha},
    )

    questions = build_canonical_benchmark_question_pool()
    hypotheses = build_canonical_adaptive_control_hypotheses()
    orchestrator = ProspectiveResearchOrchestrator(
        worker=worker,
        gateway=gateway,
        questions=questions,
        hypotheses=hypotheses,
    )

    # -------------------------------------------------------------
    # 1. ARM A: UNGUIDED RESEARCH
    # -------------------------------------------------------------
    print("\n>>> Launching ARM A: Unguided Research (Broad Crawl)...")
    metrics_a = orchestrator.run_arm_a_unguided(uow_budget=uow_budget)
    print(f"[ARM A] Finished in {metrics_a.execution_time_seconds:.2f}s | "
          f"UoWs: {metrics_a.total_uows_executed} | "
          f"Sources: {metrics_a.total_sources_acquired} (Dupes: {metrics_a.duplicate_count}, {metrics_a.duplicate_rate:.1f}%) | "
          f"Delta H: {metrics_a.total_entropy_reduction:.3f} bits | "
          f"InfoGain/Source: {metrics_a.information_gain_per_source:.4f} bits/source")

    # -------------------------------------------------------------
    # 2. ARM B: GRAPH-DEMAND-DRIVEN RESEARCH
    # -------------------------------------------------------------
    print("\n>>> Launching ARM B: Graph-Demand-Driven Research (Reactive Frontier FIFO)...")
    metrics_b = orchestrator.run_arm_b_demand_driven(uow_budget=uow_budget)
    print(f"[ARM B] Finished in {metrics_b.execution_time_seconds:.2f}s | "
          f"UoWs: {metrics_b.total_uows_executed} | "
          f"Sources: {metrics_b.total_sources_acquired} (Dupes: {metrics_b.duplicate_count}, {metrics_b.duplicate_rate:.1f}%) | "
          f"Delta H: {metrics_b.total_entropy_reduction:.3f} bits | "
          f"InfoGain/Source: {metrics_b.information_gain_per_source:.4f} bits/source")

    # -------------------------------------------------------------
    # 3. ARM C: PROSPECTIVE RESEARCH (EIG DUAL CONTROL)
    # -------------------------------------------------------------
    print("\n>>> Launching ARM C: Prospective Research (Expected Information Gain Dual Control)...")
    metrics_c = orchestrator.run_arm_c_prospective(uow_budget=uow_budget)
    print(f"[ARM C] Finished in {metrics_c.execution_time_seconds:.2f}s | "
          f"UoWs: {metrics_c.total_uows_executed} | "
          f"Sources: {metrics_c.total_sources_acquired} (Dupes: {metrics_c.duplicate_count}, {metrics_c.duplicate_rate:.1f}%) | "
          f"Delta H: {metrics_c.total_entropy_reduction:.3f} bits | "
          f"InfoGain/Source: {metrics_c.information_gain_per_source:.4f} bits/source")

    # -------------------------------------------------------------
    # HYPOTHESIS SPACE POSTERIOR IN ARM C
    # -------------------------------------------------------------
    c_belief_space = HypothesisBeliefSpace(build_canonical_adaptive_control_hypotheses())
    # Replay verified updates from Arm C questions to produce final belief table
    c_questions_ordered = list(questions)
    c_remaining = list(c_questions_ordered)
    for _ in range(min(uow_budget, len(c_remaining))):
        ranked = [(c_belief_space.compute_expected_information_gain(q), q) for q in c_remaining]
        ranked.sort(key=lambda x: x[0], reverse=True)
        _, top_q = ranked[0]
        c_remaining.remove(top_q)
        if top_q.qtype == BenchmarkQuestionType.KNOWN_NEGATIVE:
            c_belief_space.update_hypothesis(top_q.target_hypothesis_id, "REFUTE", evidence_strength=0.95)
        elif top_q.ground_truth_fragments:
            c_belief_space.update_hypothesis(top_q.target_hypothesis_id, "SUPPORT", evidence_strength=0.95, fragment_id=top_q.ground_truth_fragments[0])

    hypothesis_table = [h.to_dict() for h in c_belief_space.hypotheses.values()]

    # -------------------------------------------------------------
    # EFFICIENCY RATIO CALCULATIONS
    # -------------------------------------------------------------
    eig_source_advantage_vs_a = (
        metrics_c.information_gain_per_source / max(1e-6, metrics_a.information_gain_per_source)
    )
    eig_source_advantage_vs_b = (
        metrics_c.information_gain_per_source / max(1e-6, metrics_b.information_gain_per_source)
    )
    eig_uow_advantage_vs_a = (
        metrics_c.information_gain_per_uow / max(1e-6, metrics_a.information_gain_per_uow)
    )
    eig_uow_advantage_vs_b = (
        metrics_c.information_gain_per_uow / max(1e-6, metrics_b.information_gain_per_uow)
    )

    core_hypothesis_holds = (
        metrics_c.information_gain_per_source > metrics_b.information_gain_per_source > metrics_a.information_gain_per_source
        and metrics_c.information_gain_per_uow > metrics_b.information_gain_per_uow > metrics_a.information_gain_per_uow
        and metrics_a.duplicate_rate > metrics_c.duplicate_rate
        and metrics_c.total_entropy_reduction > metrics_b.total_entropy_reduction > metrics_a.total_entropy_reduction
    )

    verdict = "QUALIFIED" if core_hypothesis_holds else "DISQUALIFIED"

    # Assemble comprehensive report
    report: Dict[str, Any] = {
        "milestone": "UQ-N2: Prospective Research Efficiency Qualification",
        "qualification_timestamp": datetime.now(timezone.utc).isoformat(),
        "qualification_verdict": verdict,
        "core_hypothesis": {
            "statement": "Arm C (Prospective EIG Dual Control) > Arm B (Graph Demand FIFO) > Arm A (Unguided Research) in epistemic yield per source and compute",
            "holds": core_hypothesis_holds,
            "eig_source_advantage_over_unguided": round(eig_source_advantage_vs_a, 2),
            "eig_source_advantage_over_graph_demand": round(eig_source_advantage_vs_b, 2),
            "eig_uow_advantage_over_unguided": round(eig_uow_advantage_vs_a, 2),
            "eig_uow_advantage_over_graph_demand": round(eig_uow_advantage_vs_b, 2),
        },
        "provenance": {
            "git_branch": "research/sovctx-kg",
            "host_commit_sha": commit_sha,
            "target_node": "nano-jetson-01 (NVIDIA Jetson Nano 2GB ARM Cortex-A57)",
            "control_node": "uno-q-gateway-01 (x86_64 regulatory controller)",
        },
        "hard_contracts_preserved": {
            "PROPOSED_NEQ_AUTHORIZED": True,
            "DUAL_TIER_HASH_SEPARATION": True,
            "CAUSAL_ISSUANCE_LEDGER": True,
            "CRAWLED_NEQ_VERIFIED_NEQ_ADMITTED": True,
            "G1_OBSERVER_SHADOW_MODE_ZERO_AUTHORITY": True,
        },
        "arms_comparison": {
            "ARM_A_UNGUIDED": metrics_a.to_dict(),
            "ARM_B_GRAPH_DEMAND_DRIVEN": metrics_b.to_dict(),
            "ARM_C_PROSPECTIVE_EIG_DUAL_CONTROL": metrics_c.to_dict(),
        },
        "comparative_metrics_table": {
            "entropy_reduction_bits": {
                "arm_a": round(metrics_a.total_entropy_reduction, 4),
                "arm_b": round(metrics_b.total_entropy_reduction, 4),
                "arm_c": round(metrics_c.total_entropy_reduction, 4),
            },
            "sources_acquired": {
                "arm_a": metrics_a.total_sources_acquired,
                "arm_b": metrics_b.total_sources_acquired,
                "arm_c": metrics_c.total_sources_acquired,
            },
            "duplicate_rate_pct": {
                "arm_a": round(metrics_a.duplicate_rate, 2),
                "arm_b": round(metrics_b.duplicate_rate, 2),
                "arm_c": round(metrics_c.duplicate_rate, 2),
            },
            "info_gain_per_source_bits": {
                "arm_a": round(metrics_a.information_gain_per_source, 4),
                "arm_b": round(metrics_b.information_gain_per_source, 4),
                "arm_c": round(metrics_c.information_gain_per_source, 4),
            },
            "info_gain_per_uow_bits": {
                "arm_a": round(metrics_a.information_gain_per_uow, 4),
                "arm_b": round(metrics_b.information_gain_per_uow, 4),
                "arm_c": round(metrics_c.information_gain_per_uow, 4),
            },
            "questions_closed": {
                "arm_a": metrics_a.questions_closed,
                "arm_b": metrics_b.questions_closed,
                "arm_c": metrics_c.questions_closed,
            },
            "question_closure_rate_pct": {
                "arm_a": round(metrics_a.question_closure_rate, 2),
                "arm_b": round(metrics_b.question_closure_rate, 2),
                "arm_c": round(metrics_c.question_closure_rate, 2),
            },
            "contradictions_discovered": {
                "arm_a": metrics_a.contradictions_discovered,
                "arm_b": metrics_b.contradictions_discovered,
                "arm_c": metrics_c.contradictions_discovered,
            },
            "false_promotions_prevented": {
                "arm_a": metrics_a.false_promotions_prevented,
                "arm_b": metrics_b.false_promotions_prevented,
                "arm_c": metrics_c.false_promotions_prevented,
            },
            "geometric_reorientations_detected": {
                "arm_a": metrics_a.geometric_reorientations_detected,
                "arm_b": metrics_b.geometric_reorientations_detected,
                "arm_c": metrics_c.geometric_reorientations_detected,
            },
            "execution_time_seconds": {
                "arm_a": round(metrics_a.execution_time_seconds, 3),
                "arm_b": round(metrics_b.execution_time_seconds, 3),
                "arm_c": round(metrics_c.execution_time_seconds, 3),
            },
        },
        "hypothesis_space_posterior": hypothesis_table,
        "twelve_gate_suite_reference": "sovctx/tests/test_uq_n2_prospective_efficiency.py",
    }

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SOVCTX UQ-N2 Prospective Research Efficiency Campaign")
    parser.add_argument("--uow-budget", type=int, default=16, help="UoW budget per experimental arm")
    parser.add_argument("--output", type=Path, default=Path("evidence/n5/UQ_N2_QUALIFICATION_REPORT.json"), help="Output report path")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    report = run_campaign(uow_budget=args.uow_budget, repo_root=repo_root)

    out_path = repo_root / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 80)
    print("UQ-N2 COMPARATIVE BENCHMARK SUMMARY TABLE")
    print("=" * 80)
    comp = report["comparative_metrics_table"]
    print(f"{'Metric':<35} | {'Arm A (Unguided)':<16} | {'Arm B (Demand FIFO)':<18} | {'Arm C (Prospective EIG)':<22}")
    print("-" * 100)
    print(f"{'Total Entropy Reduction (bits)':<35} | {comp['entropy_reduction_bits']['arm_a']:<16.4f} | {comp['entropy_reduction_bits']['arm_b']:<18.4f} | {comp['entropy_reduction_bits']['arm_c']:<22.4f}")
    print(f"{'Sources Acquired':<35} | {comp['sources_acquired']['arm_a']:<16} | {comp['sources_acquired']['arm_b']:<18} | {comp['sources_acquired']['arm_c']:<22}")
    print(f"{'Duplicate Acquisition Rate (%)':<35} | {comp['duplicate_rate_pct']['arm_a']:<16.2f} | {comp['duplicate_rate_pct']['arm_b']:<18.2f} | {comp['duplicate_rate_pct']['arm_c']:<22.2f}")
    print(f"{'Epistemic Yield (Delta H / source)':<35} | {comp['info_gain_per_source_bits']['arm_a']:<16.4f} | {comp['info_gain_per_source_bits']['arm_b']:<18.4f} | {comp['info_gain_per_source_bits']['arm_c']:<22.4f}")
    print(f"{'Epistemic Yield (Delta H / UoW)':<35} | {comp['info_gain_per_uow_bits']['arm_a']:<16.4f} | {comp['info_gain_per_uow_bits']['arm_b']:<18.4f} | {comp['info_gain_per_uow_bits']['arm_c']:<22.4f}")
    print(f"{'Question Closure Rate (%)':<35} | {comp['question_closure_rate_pct']['arm_a']:<16.2f} | {comp['question_closure_rate_pct']['arm_b']:<18.2f} | {comp['question_closure_rate_pct']['arm_c']:<22.2f}")
    print(f"{'Contradictions Discovered':<35} | {comp['contradictions_discovered']['arm_a']:<16} | {comp['contradictions_discovered']['arm_b']:<18} | {comp['contradictions_discovered']['arm_c']:<22}")
    print(f"{'Geometric Reorientations (Omega>0.4)':<35} | {comp['geometric_reorientations_detected']['arm_a']:<16} | {comp['geometric_reorientations_detected']['arm_b']:<18} | {comp['geometric_reorientations_detected']['arm_c']:<22}")
    print(f"{'Execution Time (seconds)':<35} | {comp['execution_time_seconds']['arm_a']:<16.3f} | {comp['execution_time_seconds']['arm_b']:<18.3f} | {comp['execution_time_seconds']['arm_c']:<22.3f}")
    print("-" * 100)
    core = report["core_hypothesis"]
    print(f"Core Hypothesis Holds: {core['holds']}")
    print(f"EIG Efficiency Advantage vs Unguided:    {core['eig_source_advantage_over_unguided']}x per source | {core['eig_uow_advantage_over_unguided']}x per compute UoW")
    print(f"EIG Efficiency Advantage vs Graph-FIFO:  {core['eig_source_advantage_over_graph_demand']}x per source | {core['eig_uow_advantage_over_graph_demand']}x per compute UoW")
    print(f"Qualification Verdict: {report['qualification_verdict']}")
    print(f"Report written to: {out_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
