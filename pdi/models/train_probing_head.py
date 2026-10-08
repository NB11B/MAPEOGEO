# SPDX-License-Identifier: MIT
"""Train Linear Probing Head on Frozen SmolLM2-135M Embeddings for PDI-135M-v0.4.

Trains a lightweight projection head on frozen transformer representations
using Pairwise Ranking Loss:
    L_rank = log(1 + exp(-(s(a+) - s(a-))))

Isolates representation quality from full LoRA fine-tuning.
"""

from __future__ import annotations

import json
from pathlib import Path
import random
import sys
import time
from typing import Any, Dict, List, Tuple

import torch
import torch.nn as nn
from transformers import AutoModelForCausalLM, AutoTokenizer

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from pdi.candidates.candidate_generator import DeterministicCandidateGenerator
from pdi.candidates.observable_state import ObservableStateExtractor
from pdi.models.candidate_scorer import LinearProbingScorer
from pdi.postcondition.goal_postcondition_engine import (
    GoalPredicate,
    PostconditionEvaluator,
    TriStateLabel,
)
from pdi.postcondition.state_transition_oracle import (
    Cl20Multivector,
    NumericalGoalProperty,
    StateTransitionOracle,
)
from pdi.projection.work_relation_encoder import PSMSLWorkRelationEncoder


def extract_embedding(model, tok, prompt: str, action_line: str, dev: str) -> torch.Tensor:
    full_text = f"Goal Context: {prompt.strip()}\nProposed Work: {action_line.strip()}"
    enc = tok(full_text, return_tensors="pt", truncation=True, max_length=512).to(dev)
    with torch.no_grad():
        out = model(**enc, output_hidden_states=True)
        # Use mean pooling over the sequence
        h = out.hidden_states[-1][0].mean(dim=0)  # [576]
    return h


def train_probing_head():
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Initializing Frozen SmolLM2-135M on {dev}...")
    base_id = "HuggingFaceTB/SmolLM2-135M-Instruct"
    rev = "12fd25f77366fa6b3b4b768ec3050bf629380bac"

    tok = AutoTokenizer.from_pretrained(base_id, revision=rev)
    if tok.pad_token_id is None:
        tok.pad_token_id = tok.eos_token_id

    dtype = torch.float16 if dev == "cuda" else torch.float32
    base_model = AutoModelForCausalLM.from_pretrained(
        base_id,
        revision=rev,
        dtype=dtype,
        device_map=dev,
    )
    base_model.eval()

    # Load 256 training corpus
    corpus_path = PACKAGE_ROOT / "pdi" / "data" / "pdi_v04_prospective_corpus.json"
    with open(corpus_path, "r", encoding="utf-8") as f:
        records = json.load(f)["records"]

    gen = DeterministicCandidateGenerator()
    print("Extracting candidate embeddings and pairwise ranking pairs...")

    pairs: List[Tuple[torch.Tensor, torch.Tensor]] = []
    # Build pairs (h_pos, h_neg) from prospective corpus
    for idx, r in enumerate(records[:160]):  # First 160 scenarios
        prompt = r["input_prompt"]
        ctx = ObservableStateExtractor.extract_from_prompt(prompt, default_version=r["assumed_state_version"])
        menu = gen.generate_menu(r["scenario_id"], ctx, prompt)

        tgt = r["target_output"]
        pred = GoalPredicate(
            goal_id=r["scenario_id"],
            target_addr=tgt.get("dest_ref"),
            expected_opcode=tgt.get("operator_id"),
            is_abstention_goal=r["is_abstention_scenario"],
            expected_predicate_type="OBSERVATION" if r["category"] == "OBSERVATION"
            else ("COMPARISON" if r["category"] == "COMPARISON"
                  else ("CLARIFICATION" if r["category"] == "CLARIFICATION" else "STATE_MUTATION")),
        )

        h_pos_list = []
        h_neg_list = []
        for s in menu.slots:
            res = PostconditionEvaluator.evaluate_candidate(s.cand_id, s.action_line, {}, pred)
            h = extract_embedding(base_model, tok, prompt, s.action_line, dev)
            if res.label == TriStateLabel.USEFUL_WORK:
                h_pos_list.append(h)
            elif res.label == TriStateLabel.INCORRECT_WORK:
                h_neg_list.append(h)

        if h_pos_list and h_neg_list:
            for hp in h_pos_list:
                for hn in h_neg_list[:2]:  # Take up to 2 hard negatives
                    pairs.append((hp.float(), hn.float()))

    print(f"Constructed {len(pairs)} pairwise training pairs.")

    # Initialize probing head
    hidden_dim = base_model.config.hidden_size  # 576
    head = LinearProbingScorer(hidden_dim=hidden_dim).to(dev)
    optimizer = torch.optim.AdamW(head.parameters(), lr=1e-3, weight_decay=1e-2)

    # Train probing head for 15 epochs
    head.train()
    print("Training probing head with Pairwise Ranking Loss...")
    for epoch in range(15):
        random.shuffle(pairs)
        total_loss = 0.0
        for hp, hn in pairs:
            optimizer.zero_grad()
            s_pos = head(hp.unsqueeze(0))
            s_neg = head(hn.unsqueeze(0))
            # Pairwise ranking loss: log(1 + exp(-(s+ - s-)))
            loss = torch.log1p(torch.exp(-(s_pos - s_neg))).mean()
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        if (epoch + 1) % 5 == 0 or epoch == 0:
            print(f"Epoch {epoch+1:2d}/15 | Mean Loss: {total_loss/len(pairs):.4f}")

    head.eval()
    ckpt_path = PACKAGE_ROOT / "pdi" / "checkpoints" / "probing_head_v04.pt"
    ckpt_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(head.state_dict(), ckpt_path)
    print(f"Saved trained probing head to: {ckpt_path}")

    # Now evaluate on the 64-scenario Hard Ambiguity Challenge Suite!
    challenge_path = PACKAGE_ROOT / "pdi" / "data" / "pdi_v04_hard_ambiguity_challenge.json"
    with open(challenge_path, "r", encoding="utf-8") as f:
        challenge_records = json.load(f)["records"]

    print("\nEvaluating Frozen Model + Trained Probing Head on Hard Ambiguity Challenge (64 scenarios)...")
    cat_scores = {
        "NON_COMMUTATIVE_DISCRIMINATOR": [0, 0],
        "PARTIALLY_OBSERVABLE_UNDERSPECIFIED": [0, 0],
        "CONTEXTUAL_AMBIGUITY": [0, 0],
    }

    t0 = time.perf_counter()
    for r in challenge_records:
        cat = r["challenge_category"]
        cat_scores[cat][1] += 1
        prompt = r["input_prompt"]
        ctx = ObservableStateExtractor.extract_from_prompt(prompt, default_version=r["assumed_state_version"])
        menu = gen.generate_menu(r["scenario_id"], ctx, prompt)

        # Score candidates with trained probing head
        scored = []
        with torch.no_grad():
            for slot in menu.slots:
                h = extract_embedding(base_model, tok, prompt, slot.action_line, dev)
                score = head(h.float().unsqueeze(0)).item()
                scored.append((score, slot.cand_id, slot))

        # Select argmax with stable tie-breaking
        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        best_slot = scored[0][2]

        # Authoritative Numerical Verification
        pre_state = {int(k): Cl20Multivector(**v) for k, v in r["pre_state"].items()}
        exp_mv = Cl20Multivector(**r["expected_multivector"]) if r["expected_multivector"] else Cl20Multivector()
        goal = NumericalGoalProperty(
            goal_id=r["scenario_id"],
            target_addr=r["dest_ref"] or 0,
            expected_multivector=exp_mv,
            is_abstention_required=r["requires_abstention"],
        )
        verdict = StateTransitionOracle.execute_and_verify(best_slot.cand_id, best_slot.action_line, pre_state, goal)
        if verdict.label == TriStateLabel.USEFUL_WORK:
            cat_scores[cat][0] += 1

    total_time = (time.perf_counter() - t0) * 1000.0
    mean_lat = total_time / len(challenge_records)

    print("\n" + "=" * 76)
    print("FROZEN TRANSFORMER + TRAINED PROBING HEAD (Hard Ambiguity Challenge)")
    print("=" * 76)
    total_c = sum(c[0] for c in cat_scores.values())
    total_t = sum(c[1] for c in cat_scores.values())
    print(f"Overall Useful Selection: {total_c}/{total_t} ({total_c/total_t*100:6.2f}%) | Latency mean: {mean_lat:6.2f} ms")
    for cat, (c, t) in cat_scores.items():
        print(f"    - {cat:36s}: {c:2d}/{t:2d} ({c/t*100:6.2f}%)")

    report_path = PACKAGE_ROOT / "pdi" / "qualification" / "pdi_v04_probing_head_benchmark.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "model": "Frozen SmolLM2-135M + Trained Probing Head",
            "overall_useful_pct": round((total_c / total_t) * 100.0, 2),
            "latency_mean_ms": round(mean_lat, 2),
            "by_category": {
                cat: {"correct": c, "total": t, "pct": round((c / t) * 100.0, 2)}
                for cat, (c, t) in cat_scores.items()
            }
        }, f, indent=2)

    print(f"Saved probing head evaluation report to: {report_path}")


if __name__ == "__main__":
    train_probing_head()
