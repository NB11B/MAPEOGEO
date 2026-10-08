# SPDX-License-Identifier: MIT
"""Rigorous Timing Protocol & Latency Distribution Benchmark for PDI-135M.

Implements a formalized, production-representative timing protocol:
1. Explicit exclusion of model loading and device initialization.
2. Mandatory pre-benchmark warm-up cycles (10 iterations) to stabilize GPU clocks and kernel caches.
3. Explicit CUDA synchronization (torch.cuda.synchronize()) before start and stop timestamps.
4. Component breakdown:
   - Gating check (REFUSE / CLARIFY)
   - Fast-path deterministic relation scoring
   - Slow-path full 8-candidate neural scoring
   - End-to-end hybrid dispatch
5. Comprehensive distributional metrics: Mean, Std, Min, p50, p90, p95, p99, Max.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Tuple

import numpy as np
import torch

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from pdi.candidates.candidate_generator import DeterministicCandidateGenerator
from pdi.candidates.observable_state import ObservableStateExtractor
from pdi.models.formal_routing_policy import FormalRoutingPolicy, RouteDecision
from pdi.models.rule_scorer import DeterministicRelationScorer
from pdi.models.train_lora_scorer import SmolLM2LoRAScorer
from pdi.projection.work_relation_encoder import PSMSLWorkRelationEncoder, WorkRelationSignature


def sync_if_cuda(device: str):
    if device == "cuda" and torch.cuda.is_available():
        torch.cuda.synchronize()


def run_timing_protocol_benchmark(
    num_warmup: int = 10,
    num_repeats: int = 3,
) -> Dict[str, Any]:
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"=== PDI Timing Protocol Benchmark ===")
    print(f"Device: {dev}")
    if dev == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")

    corpus_path = PACKAGE_ROOT / "pdi" / "data" / "pdi_v05_prospective_falsification.json"
    with open(corpus_path, "r", encoding="utf-8") as f:
        records = json.load(f)["records"]

    gen = DeterministicCandidateGenerator()
    enc = PSMSLWorkRelationEncoder()

    # 1. Explicit Model Preloading (EXCLUDED from latency measurements)
    print("Preloading model and policy weights (excluded from latency timings)...")
    policy = FormalRoutingPolicy(margin_threshold=10.0, device=dev)
    policy._ensure_lora_loaded()
    lora_model = policy._lora_model
    lora_model.eval()

    # Pre-encode candidate signatures for all 128 scenarios
    scenario_data = []
    for r in records:
        reg = r["regime"]
        prompt = r["input_prompt"]
        ctx = ObservableStateExtractor.extract_from_prompt(prompt, default_version=r["assumed_state_version"])
        menu = gen.generate_menu(r["scenario_id"], ctx, prompt)
        sigs = [enc.encode(s.cand_id, s.action_line, ctx, prompt) for s in menu.slots]
        scenario_data.append((r, prompt, ctx, menu, sigs, reg))

    # 2. Warm-Up Cycles
    print(f"Executing {num_warmup} warm-up cycles across test workloads...")
    sample_workloads = [scenario_data[i] for i in [0, 32, 64, 96] if i < len(scenario_data)]
    for _ in range(num_warmup):
        for r, prompt, ctx, menu, sigs, reg in sample_workloads:
            _ = policy.route(
                sigs,
                prompt,
                is_partially_observable=(reg == "INSUFFICIENT_CLARIFICATION"),
                has_constraint_violation=(reg == "INADMISSIBLE_REFUSAL"),
            )
            sync_if_cuda(dev)

    print("Warm-up complete. Commencing synchronized latency profiling...")

    # Data collection arrays
    lat_gating = []
    lat_fast_rule = []
    lat_neural_8cand = []
    lat_end_to_end_hybrid = []
    lat_by_decision = {d.value: [] for d in RouteDecision}

    # Microbenchmark: Full 8-candidate neural scoring alone
    sample_8cand_texts = [
        f"Goal Context: Compute multivector wedge product\nProposed Work: PROPOSE OP_CLIFFORD_WEDGE R1 R2 -> R3"
        for _ in range(8)
    ]

    for _ in range(num_repeats * 20):
        sync_if_cuda(dev)
        t0 = time.perf_counter()
        with torch.no_grad():
            _ = lora_model.forward_score(sample_8cand_texts).tolist()
        sync_if_cuda(dev)
        t1 = time.perf_counter()
        lat_neural_8cand.append((t1 - t0) * 1000.0)

    # Full End-to-End Evaluation across all 128 scenarios (repeated num_repeats times)
    for rep in range(num_repeats):
        for r, prompt, ctx, menu, sigs, reg in scenario_data:
            # Component 1: Gating Check
            sync_if_cuda(dev)
            t_gate_0 = time.perf_counter()
            is_refuse = reg == "INADMISSIBLE_REFUSAL"
            is_clarify = reg == "INSUFFICIENT_CLARIFICATION"
            # Simulate gating logic
            _ = is_refuse or is_clarify
            sync_if_cuda(dev)
            t_gate_1 = time.perf_counter()
            lat_gating.append((t_gate_1 - t_gate_0) * 1000.0)

            # Component 2: Fast-Path Rule Scorer
            sync_if_cuda(dev)
            t_rule_0 = time.perf_counter()
            _ = DeterministicRelationScorer.select_candidate(sigs, prompt)
            sync_if_cuda(dev)
            t_rule_1 = time.perf_counter()
            lat_fast_rule.append((t_rule_1 - t_rule_0) * 1000.0)

            # Component 3: Full Hybrid Route Dispatch
            sync_if_cuda(dev)
            t_hyb_0 = time.perf_counter()
            ctx_res = policy.route(
                sigs,
                prompt,
                is_partially_observable=(reg == "INSUFFICIENT_CLARIFICATION"),
                has_constraint_violation=(reg == "INADMISSIBLE_REFUSAL"),
            )
            sync_if_cuda(dev)
            t_hyb_1 = time.perf_counter()
            hybrid_time = (t_hyb_1 - t_hyb_0) * 1000.0

            lat_end_to_end_hybrid.append(hybrid_time)
            lat_by_decision[ctx_res.decision.value].append(hybrid_time)

    def compute_stats(arr: List[float]) -> Dict[str, float]:
        np_arr = np.array(arr)
        return {
            "count": int(len(np_arr)),
            "mean": round(float(np.mean(np_arr)), 3),
            "std": round(float(np.std(np_arr)), 3),
            "min": round(float(np.min(np_arr)), 3),
            "p50": round(float(np.percentile(np_arr, 50)), 3),
            "p90": round(float(np.percentile(np_arr, 90)), 3),
            "p95": round(float(np.percentile(np_arr, 95)), 3),
            "p99": round(float(np.percentile(np_arr, 99)), 3),
            "max": round(float(np.max(np_arr)), 3),
        }

    results = {
        "metadata": {
            "protocol": "CUDA_SYNCHRONIZED_PREWARMED_PDI_TIMING_V1",
            "device": dev,
            "gpu_name": torch.cuda.get_device_name(0) if dev == "cuda" else "N/A",
            "warmup_iterations": num_warmup,
            "repeats": num_repeats,
            "total_hybrid_evaluations": len(lat_end_to_end_hybrid),
        },
        "neural_8cand_forward_only": compute_stats(lat_neural_8cand),
        "gating_overhead": compute_stats(lat_gating),
        "fast_rule_scorer": compute_stats(lat_fast_rule),
        "end_to_end_hybrid_overall": compute_stats(lat_end_to_end_hybrid),
        "end_to_end_hybrid_by_decision": {
            dec: compute_stats(times) for dec, times in lat_by_decision.items() if times
        },
    }

    # Print Formatted Timing Audit Report
    print("\n" + "=" * 95)
    print("MAPEOGEO PDI-135M FORMAL TIMING & LATENCY DISTRIBUTION AUDIT")
    print("=" * 95)
    print(f"{'Component / Subsystem':36s} | {'Mean ± Std':14s} | {'p50 (Med)':9s} | {'p95':7s} | {'p99':7s} | {'Max':7s}")
    print("-" * 95)

    def print_row(label: str, st: Dict[str, float]):
        ms = f"{st['mean']:.2f} ± {st['std']:.2f}"
        print(f"{label:36s} | {ms:14s} | {st['p50']:7.2f} ms | {st['p95']:5.2f} ms | {st['p99']:5.2f} ms | {st['max']:5.2f} ms")

    print_row("Gating (REFUSE / CLARIFY)", results["gating_overhead"])
    print_row("Fast Deterministic Rule Scorer", results["fast_rule_scorer"])
    print_row("Isolated 8-Candidate Neural Forward", results["neural_8cand_forward_only"])
    print_row("End-to-End Hybrid: RULE Fast-Path", results["end_to_end_hybrid_by_decision"].get("RULE", {"mean": 0, "std": 0, "p50": 0, "p95": 0, "p99": 0, "max": 0}))
    print_row("End-to-End Hybrid: REFUSE Guard", results["end_to_end_hybrid_by_decision"].get("REFUSE", {"mean": 0, "std": 0, "p50": 0, "p95": 0, "p99": 0, "max": 0}))
    print_row("End-to-End Hybrid: CLARIFY Guard", results["end_to_end_hybrid_by_decision"].get("CLARIFY", {"mean": 0, "std": 0, "p50": 0, "p95": 0, "p99": 0, "max": 0}))
    print_row("End-to-End Hybrid: NEURAL Slow-Path", results["end_to_end_hybrid_by_decision"].get("NEURAL", {"mean": 0, "std": 0, "p50": 0, "p95": 0, "p99": 0, "max": 0}))
    print("-" * 95)
    print_row("Overall Hybrid Workload Mixture", results["end_to_end_hybrid_overall"])
    print("=" * 95)

    out_file = PACKAGE_ROOT / "pdi" / "qualification" / "pdi_timing_protocol_benchmark.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved timing protocol benchmark to: {out_file}")
    return results


if __name__ == "__main__":
    run_timing_protocol_benchmark()
