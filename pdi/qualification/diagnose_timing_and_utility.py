# SPDX-License-Identifier: MIT
"""Diagnostic script for PDI-v0.6: Timing calibration and pre-latency utility decomposition."""

import json
from pathlib import Path
import sys
import time
import numpy as np
import torch

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from pdi.candidates.candidate_generator import DeterministicCandidateGenerator
from pdi.candidates.observable_state import ObservableStateExtractor
from pdi.models.formal_routing_policy import FormalRoutingPolicy, RouteDecision
from pdi.models.rule_scorer import DeterministicRelationScorer
from pdi.projection.work_relation_encoder import PSMSLWorkRelationEncoder

def sync_cuda():
    if torch.cuda.is_available():
        torch.cuda.synchronize()

def main():
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Running diagnostic on {dev}...")

    corpus_path = PACKAGE_ROOT / "pdi" / "data" / "pdi_v05_prospective_falsification.json"
    with open(corpus_path, "r", encoding="utf-8") as f:
        records = json.load(f)["records"]

    gen = DeterministicCandidateGenerator()
    enc = PSMSLWorkRelationEncoder()
    policy = FormalRoutingPolicy(margin_threshold=10.0, device=dev)
    policy._ensure_lora_loaded()
    lora_model = policy._lora_model

    # Warmup
    for _ in range(5):
        sample_texts = ["Goal: foo\nProposed: bar"] * 8
        _ = lora_model.forward_score(sample_texts)
        sync_cuda()

    # 1. Investigate Timing Difference: Synthetic 8-cand vs Actual Corpus 8-cand
    synthetic_texts = [
        f"Goal Context: Compute multivector wedge product\nProposed Work: PROPOSE OP_CLIFFORD_WEDGE R1 R2 -> R3"
        for _ in range(8)
    ]
    tok = lora_model.tok
    synth_lens = [len(tok.encode(t)) for t in synthetic_texts]

    times_synth = []
    for _ in range(30):
        sync_cuda()
        t0 = time.perf_counter()
        _ = lora_model.forward_score(synthetic_texts).tolist()
        sync_cuda()
        times_synth.append((time.perf_counter() - t0) * 1000.0)

    # Now evaluate real prompts
    real_prompt_lens = []
    real_prompt_times = []
    
    # Store utility decomposition data
    records_data = []

    for r in records:
        reg = r["regime"]
        prompt = r["input_prompt"]
        ctx = ObservableStateExtractor.extract_from_prompt(prompt, default_version=r["assumed_state_version"])
        menu = gen.generate_menu(r["scenario_id"], ctx, prompt)
        sigs = [enc.encode(s.cand_id, s.action_line, ctx, prompt) for s in menu.slots]
        
        ctx_res = policy.route(
            sigs,
            prompt,
            is_partially_observable=(reg == "INSUFFICIENT_CLARIFICATION"),
            has_constraint_violation=(reg == "INADMISSIBLE_REFUSAL"),
        )
        
        if ctx_res.decision == RouteDecision.NEURAL:
            texts = [f"Goal Context: {prompt.strip()}\nProposed Work: {s.action_line.strip()}" for s in sigs]
            p_lens = [len(tok.encode(t)) for t in texts]
            real_prompt_lens.append(np.mean(p_lens))

            sync_cuda()
            t0 = time.perf_counter()
            _ = lora_model.forward_score(texts).tolist()
            sync_cuda()
            real_prompt_times.append((time.perf_counter() - t0) * 1000.0)

        # Pre-latency and post-latency utility tracking
        sig_b = DeterministicRelationScorer.select_candidate(sigs, prompt) if reg not in ["INADMISSIBLE_REFUSAL", "INSUFFICIENT_CLARIFICATION"] else ctx_res.selected_sig
        sig_c = ctx_res.selected_sig

        # Evaluate Arm B useful
        can = r["canonical_action"].strip()
        is_u_b = (sig_b.action_line.strip() == can) or (r["is_abstention"] and ("ABSTAIN" in sig_b.action_line or "CLARIFY" in sig_b.action_line))
        is_u_c = (sig_c.action_line.strip() == can) or (r["is_abstention"] and ("ABSTAIN" in sig_c.action_line or "CLARIFY" in sig_c.action_line))

        # Check commutative
        for u_val, sig_val in [(is_u_b, sig_b), (is_u_c, sig_c)]:
            parts = sig_val.action_line.split()
            cparts = can.split()
            if len(parts) >= 3 and len(cparts) >= 3 and parts[1] == cparts[1] and parts[-1] == cparts[-1]:
                if parts[1] in ["OP_ADD", "OP_ALU_ADD", "OP_MUL", "OP_ALU_MUL", "OP_VECTOR_DOT"]:
                    if sig_val is sig_b: is_u_b = True
                    if sig_val is sig_c: is_u_c = True

        r_pre_b = 10.0 if is_u_b else -10.0
        r_pre_c = 10.0 if is_u_c else -10.0

        records_data.append({
            "id": r["scenario_id"],
            "regime": reg,
            "decision": ctx_res.decision.value,
            "u_b": is_u_b,
            "u_c": is_u_c,
            "r_pre_b": r_pre_b,
            "r_pre_c": r_pre_c,
            "delta_r_pre": r_pre_c - r_pre_b,
        })

    print("\n--- TIMING COMPARISON ---")
    print(f"Synthetic prompt avg token length: {np.mean(synth_lens):.1f} tokens")
    print(f"Synthetic forward time: mean={np.mean(times_synth):.2f} ms, p50={np.percentile(times_synth, 50):.2f} ms")
    print(f"Real corpus prompt avg token length: {np.mean(real_prompt_lens):.1f} tokens")
    print(f"Real corpus forward time: mean={np.mean(real_prompt_times):.2f} ms, p50={np.percentile(real_prompt_times, 50):.2f} ms")

    print("\n--- PRE-LATENCY UTILITY (REWARD) DECOMPOSITION ---")
    neural_records = [d for d in records_data if d["decision"] == "NEURAL"]
    print(f"Total scenarios routed to NEURAL: {len(neural_records)} / 128")
    
    b_useful = sum(1 for d in neural_records if d["u_b"])
    c_useful = sum(1 for d in neural_records if d["u_c"])
    delta_r_mean = np.mean([d["delta_r_pre"] for d in neural_records])
    
    print(f"On NEURAL-routed scenarios (n={len(neural_records)}):")
    print(f"  Guarded Rule (Arm B) useful: {b_useful}/{len(neural_records)} ({b_useful/len(neural_records)*100:.1f}%)")
    print(f"  Guarded Neural (Arm C) useful: {c_useful}/{len(neural_records)} ({c_useful/len(neural_records)*100:.1f}%)")
    print(f"  Pre-latency mean reward Arm B: {np.mean([d['r_pre_b'] for d in neural_records]):+.2f} points")
    print(f"  Pre-latency mean reward Arm C: {np.mean([d['r_pre_c'] for d in neural_records]):+.2f} points")
    print(f"  Pre-latency Delta R_hard: {delta_r_mean:+.2f} points")

    # Post-latency utility check
    c_lat_ms = 0.05
    lat_neural_mean = np.mean(real_prompt_times)
    lat_penalty = c_lat_ms * lat_neural_mean
    u_net_hard = delta_r_mean - lat_penalty
    print(f"  Inference latency: {lat_neural_mean:.2f} ms -> latency penalty: {lat_penalty:.2f} points")
    print(f"  Post-latency Net Value-of-Inference V_hard: {u_net_hard:+.2f} points")

    # Over the entire 128 suite
    delta_r_overall = np.mean([d["delta_r_pre"] for d in records_data])
    print(f"\nAcross ALL 128 scenarios:")
    print(f"  Overall pre-latency Delta R: {delta_r_overall:+.2f} points")
    print(f"  Overall blended latency penalty: {c_lat_ms * (len(neural_records)/128 * lat_neural_mean):.2f} points")
    print(f"  Overall post-latency Delta U: {delta_r_overall - c_lat_ms * (len(neural_records)/128 * lat_neural_mean):+.2f} points")

if __name__ == "__main__":
    main()
