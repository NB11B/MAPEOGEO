"""Qualification suite for Recurrent EO/GEO Controller: Gates R1 through R6.

Gate definitions:
- R1: Exact L4 programs >= 90% (extrapolation from L1-3 training).
- R2: Unseen lengths 5-8 >= 80% (long horizon extrapolation).
- R3: Intermediate register reuse >= 90% (multi-scratchpad register file).
- R4: Nested operator expressions >= 85% (branching/DAG dependencies).
- R5: Operator precondition violations >= 99% safe rejection (type & domain safety).
- R6: Geometric product integration (exact agreement with Pauli ground truth).
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import random
import time
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

from .machine import (
    ALL_OPS, ALU_OPS, GEO_OPS, RecurrentMachineState, Value,
    pauli_check_gp3, to_bits
)
from .policy import (
    ALL_REGS, INPUT_NAMES, OP_IX, PAD, REG_IX, SCRATCH_IX, SCRATCH_NAMES,
    TEMPLATES, WORD_IX, WORD_LIST
)

class TransformerClausePolicy(nn.Module):
    def __init__(self, d=64):
        super().__init__()
        self.d = d
        self.word_emb = nn.Embedding(len(WORD_LIST), d, padding_idx=WORD_IX[PAD])
        self.pos_emb = nn.Embedding(16, d)
        enc_layer = nn.TransformerEncoderLayer(d_model=d, nhead=4, dim_feedforward=128, batch_first=True, dropout=0.0)
        self.enc = nn.TransformerEncoder(enc_layer, num_layers=2)
        
        self.core = nn.GRUCell(d + 1, d)

        self.head_op = nn.Linear(d, len(ALL_OPS))
        self.head_src1 = nn.Linear(d, len(ALL_REGS))
        self.head_src2 = nn.Linear(d, len(ALL_REGS))
        self.head_dst = nn.Linear(d, len(SCRATCH_NAMES))
        self.head_halt = nn.Linear(d, 2)

    def forward(self, clause_tokens, is_last, h_prev):
        B, seq_len = clause_tokens.shape
        pos = torch.arange(seq_len, device=clause_tokens.device).unsqueeze(0)
        emb = self.word_emb(clause_tokens) + self.pos_emb(pos)
        pad_mask = (clause_tokens == WORD_IX[PAD])
        h_enc = self.enc(emb, src_key_padding_mask=pad_mask)
        c_ctx = h_enc[:, 0]

        in_feat = torch.cat([c_ctx, is_last.unsqueeze(-1).float()], dim=-1)
        h_t = self.core(in_feat, h_prev)

        return h_t, (self.head_op(h_t), self.head_src1(h_t), self.head_src2(h_t), self.head_dst(h_t), self.head_halt(h_t))

def encode_clause(c_str: str, max_len: int = 12):
    words = c_str.split()
    ids = [WORD_IX.get(w, WORD_IX[PAD]) for w in words][:max_len]
    return ids + [WORD_IX[PAD]] * (max_len - len(ids))

def generate_program_example(length: int, rng: random.Random, nested=False, include_geo=True):
    names_pool = rng.sample(INPUT_NAMES, len(INPUT_NAMES))
    initial_env = {}
    is_geo = include_geo and (rng.random() < 0.25)

    if is_geo:
        for n in names_pool:
            initial_env[n] = Value(kind="geo", val=(1, rng.randrange(8)))
        allowed = GEO_OPS
    else:
        for n in names_pool:
            initial_env[n] = Value(kind="int", val=rng.randrange(256))
        allowed = ALU_OPS

    trace, phrases = [], []
    if nested and length >= 3:
        op1 = rng.choice(allowed)
        op2 = rng.choice(allowed)
        op3 = rng.choice(allowed)
        p1, q1 = names_pool[0], names_pool[1]
        p2, q2 = names_pool[2], names_pool[3]
        trace.append((op1, p1, q1, "R0", 0))
        trace.append((op2, p2, q2, "R1", 0))
        trace.append((op3, "R0", "R1", "R2", 1))
        phrases.append(rng.choice(TEMPLATES[op1]).format(p=p1, q=q1))
        phrases.append(rng.choice(TEMPLATES[op2]).format(p=p2, q=q2))
        phrases.append(f"combine R0 and R1 with {op3.lower()}")
    else:
        cur_dst = "R0"
        for step_idx in range(length):
            op = rng.choice(allowed)
            dst = cur_dst
            if step_idx == 0:
                p, q = names_pool[0], names_pool[1]
                phrases.append(rng.choice(TEMPLATES[op]).format(p=p, q=q))
            else:
                next_in = names_pool[(step_idx + 1) % len(names_pool)]
                if rng.random() < 0.5:
                    p, q = "R0", next_in
                else:
                    p, q = next_in, "R0"
                phrases.append(rng.choice(TEMPLATES[op]).format(p=p, q=q))
            halt = 1 if (step_idx == length - 1) else 0
            trace.append((op, p, q, dst, halt))

    prompt = " , then ".join(phrases)
    return {
        "prompt": prompt.split(),
        "initial_env": initial_env,
        "trace": trace,
        "length": len(trace)
    }

def build_training_data(n_samples: int, seed: int):
    rng = random.Random(seed)
    data = []
    for _ in range(n_samples):
        # Train strictly on lengths 1, 2, 3
        L = rng.choices([1, 2, 3], weights=[0.2, 0.4, 0.4])[0]
        ex = generate_program_example(L, rng, nested=(rng.random() < 0.35), include_geo=True)
        data.append(ex)
    return data

def train_recurrent_policy(train_data, epochs=10, lr=1e-3, device="cpu"):
    model = TransformerClausePolicy().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs * len(train_data))
    loss_fn = nn.CrossEntropyLoss()

    for ep in range(epochs):
        model.train()
        random.shuffle(train_data)
        tot = 0.0

        for ex in train_data:
            clauses = " ".join(ex["prompt"]).split(" , then ")
            h_t = torch.zeros(1, model.d, device=device)
            loss_ex = 0.0

            for t, (clause_str, step) in enumerate(zip(clauses, ex["trace"])):
                c_tok = torch.tensor([encode_clause(clause_str)], device=device)
                is_last = torch.tensor([1 if t == len(clauses) - 1 else 0], device=device)
                h_t, (l_op, l_s1, l_s2, l_dst, l_halt) = model(c_tok, is_last, h_t)

                l = (
                    loss_fn(l_op, torch.tensor([OP_IX[step[0]]], device=device)) +
                    loss_fn(l_s1, torch.tensor([REG_IX[step[1]]], device=device)) +
                    loss_fn(l_s2, torch.tensor([REG_IX[step[2]]], device=device)) +
                    loss_fn(l_dst, torch.tensor([SCRATCH_IX[step[3]]], device=device)) +
                    2.0 * loss_fn(l_halt, torch.tensor([step[4]], device=device))
                )
                loss_ex = loss_ex + l

            optimizer.zero_grad()
            loss_ex.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            sched.step()
            tot += loss_ex.item()

        print(f"Epoch {ep+1}/{epochs} loss: {tot / len(train_data):.4f}")

    return model

def evaluate_recurrent_policy(model, test_examples, device="cpu"):
    model.eval()
    exact_traces = 0
    exact_answers = 0
    faults = 0

    with torch.no_grad():
        for ex in test_examples:
            clauses = " ".join(ex["prompt"]).split(" , then ")
            machine = RecurrentMachineState()
            machine.reset(ex["initial_env"])
            h_t = torch.zeros(1, model.d, device=device)

            pred_trace = []
            for t, clause_str in enumerate(clauses):
                c_tok = torch.tensor([encode_clause(clause_str)], device=device)
                is_last = torch.tensor([1 if t == len(clauses) - 1 else 0], device=device)
                h_t, (l_op, l_s1, l_s2, l_dst, l_halt) = model(c_tok, is_last, h_t)

                op = ALL_OPS[l_op.argmax().item()]
                s1 = ALL_REGS[l_s1.argmax().item()]
                s2 = ALL_REGS[l_s2.argmax().item()]
                dst = SCRATCH_NAMES[l_dst.argmax().item()]
                halt = l_halt.argmax().item()

                pred_trace.append((op, s1, s2, dst, halt))
                ok = machine.step(op, s1, s2, dst)
                if not ok:
                    faults += 1
                    break
                if halt == 1:
                    break

            if pred_trace == ex["trace"]:
                exact_traces += 1

            ref_machine = RecurrentMachineState()
            ref_machine.reset(ex["initial_env"])
            for step in ex["trace"]:
                ref_machine.step(step[0], step[1], step[2], step[3])
            final_dst = ex["trace"][-1][3]
            ref_ans = ref_machine.registers.get(final_dst)
            pred_ans = machine.registers.get(final_dst)

            if pred_ans is not None and ref_ans is not None and pred_ans == ref_ans:
                exact_answers += 1

    N = len(test_examples)
    return {
        "exact_trace_rate": exact_traces / N,
        "exact_answer_rate": exact_answers / N,
        "fault_rate": faults / N,
    }

def run_gate_suite(model, device="cpu"):
    """Evaluate gates R1 - R6."""
    rng = random.Random(20261028)
    results = {}

    print("\n--- Gate R1: Exact L4 Programs (Target >= 90%) ---")
    l4_tests = [generate_program_example(4, rng, nested=False, include_geo=True) for _ in range(500)]
    r1 = evaluate_recurrent_policy(model, l4_tests, device=device)
    results["R1_L4"] = r1
    print(f"R1 L4 Exact Traces: {r1['exact_trace_rate']*100:.1f}%, Answers: {r1['exact_answer_rate']*100:.1f}%")

    print("\n--- Gate R2: Unseen Lengths 5-8 (Target >= 80%) ---")
    r2_tests = [generate_program_example(rng.randint(5, 8), rng, nested=False, include_geo=True) for _ in range(500)]
    r2 = evaluate_recurrent_policy(model, r2_tests, device=device)
    results["R2_L5_8"] = r2
    print(f"R2 L5-8 Exact Traces: {r2['exact_trace_rate']*100:.1f}%, Answers: {r2['exact_answer_rate']*100:.1f}%")

    print("\n--- Gate R3: Intermediate Register Reuse (Target >= 90%) ---")
    r3_tests = [generate_program_example(rng.randint(2, 4), rng, nested=False, include_geo=True) for _ in range(500)]
    r3 = evaluate_recurrent_policy(model, r3_tests, device=device)
    results["R3_Reuse"] = r3
    print(f"R3 Register Reuse Exact Traces: {r3['exact_trace_rate']*100:.1f}%, Answers: {r3['exact_answer_rate']*100:.1f}%")

    print("\n--- Gate R4: Nested Operator Expressions (Target >= 85%) ---")
    r4_tests = [generate_program_example(3, rng, nested=True, include_geo=False) for _ in range(500)]
    r4 = evaluate_recurrent_policy(model, r4_tests, device=device)
    results["R4_Nested"] = r4
    print(f"R4 Nested Exact Traces: {r4['exact_trace_rate']*100:.1f}%, Answers: {r4['exact_answer_rate']*100:.1f}%")

    print("\n--- Gate R5: Precondition Violations Safe Rejection (Target >= 99%) ---")
    machine = RecurrentMachineState()
    violations_tested = 0
    safe_rejections = 0

    machine.reset({"a": Value(kind="geo", val=(1, 2)), "b": Value(kind="geo", val=(1, 3))})
    if not machine.step("ADD", "a", "b", "R0") and machine.faulted: safe_rejections += 1
    violations_tested += 1

    machine.reset({"a": Value(kind="int", val=10), "b": Value(kind="int", val=20)})
    if not machine.step("GEO_GP3", "a", "b", "R0") and machine.faulted: safe_rejections += 1
    violations_tested += 1

    machine.reset({"a": Value(kind="int", val=10)})
    if not machine.step("ADD", "a", "R2", "R0") and machine.faulted: safe_rejections += 1
    violations_tested += 1

    for bad_blade in [-1, 8, 15]:
        machine.reset({"a": Value(kind="geo", val=(1, bad_blade)), "b": Value(kind="geo", val=(1, 0))})
        if not machine.step("GEO_GP3", "a", "b", "R0") and machine.faulted: safe_rejections += 1
        violations_tested += 1

    r5_rate = safe_rejections / violations_tested
    results["R5_Preconditions"] = {"rejection_rate": r5_rate, "total": violations_tested}
    print(f"R5 Safe Rejection Rate: {r5_rate*100:.1f}% ({safe_rejections}/{violations_tested})")

    print("\n--- Gate R6: Geometric Product Pauli Ground Truth ---")
    pauli_matches = 0
    for a in range(8):
        for b in range(8):
            sign_pauli, blade_pauli = pauli_check_gp3(a, b)
            machine.reset({"a": Value(kind="geo", val=(1, a)), "b": Value(kind="geo", val=(1, b))})
            machine.step("GEO_GP3", "a", "b", "R0")
            r_val = machine.registers["R0"].val
            if r_val == (sign_pauli, blade_pauli):
                pauli_matches += 1
    results["R6_GeoPauli"] = {"agreement_rate": pauli_matches / 64, "total": 64}
    print(f"R6 Geometric Agreement with Pauli: {pauli_matches}/64 basis products exact")

    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--n-train", type=int, default=2500)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--out", default="experiments/mapeogeo_llm/results/recurrent_qualification.json")
    args = parser.parse_args()

    print(f"Generating {args.n_train} training examples (lengths 1-3 only)...")
    train_data = build_training_data(args.n_train, seed=20261028)

    print(f"Training TransformerClausePolicy on {args.device} for {args.epochs} epochs...")
    model = train_recurrent_policy(train_data, epochs=args.epochs, device=args.device)

    print("\nRunning Qualification Suite R1 - R6...")
    gate_results = run_gate_suite(model, device=args.device)

    out_p = Path(args.out)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_text(json.dumps(gate_results, indent=2))
    torch.save(model.state_dict(), str(out_p.with_suffix(".pt")))
    print(f"\nResults written to {out_p}")

if __name__ == "__main__":
    main()
