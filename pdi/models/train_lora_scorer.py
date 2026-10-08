# SPDX-License-Identifier: MIT
"""Targeted LoRA Fine-Tuning for Candidate-Wise Work Selection in PDI-135M-v0.4.

Trains a lightweight LoRA adapter on SmolLM2-135M specifically using
Pairwise Ranking Loss on work-selection relations:
1. Geometric distinction:
   - "symmetric scalar projection metric" -> OP_VECTOR_DOT > OP_VECTOR_WEDGE
   - "oriented planar bivector span" -> OP_VECTOR_WEDGE > OP_VECTOR_DOT
2. Non-commutative operand order:
   - "state A by state B" -> REF_A REF_B > REF_B REF_A
3. Calibrated abstention:
   - Underspecified / uncertified / conflict -> ABSTAIN > PROPOSE
   - Clear executable goal -> PROPOSE > ABSTAIN

Architecture:
- Base: SmolLM2-135M-Instruct (frozen)
- LoRA: q_proj, v_proj (r=8, alpha=16)
- Score Head: Linear(576, 1)
- Loss: L_rank = log(1 + exp(-(s(a+) - s(a-))))
"""

from __future__ import annotations

import json
from pathlib import Path
import random
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer
from peft import LoraConfig, get_peft_model, TaskType

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from pdi.candidates.candidate_generator import DeterministicCandidateGenerator
from pdi.candidates.observable_state import ObservableStateExtractor
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


class SmolLM2LoRAScorer(nn.Module):
    """Candidate-wise scoring model with SmolLM2-135M backbone and LoRA adapter."""

    def __init__(
        self,
        base_model_id: str = "HuggingFaceTB/SmolLM2-135M-Instruct",
        base_revision: str = "12fd25f77366fa6b3b4b768ec3050bf629380bac",
        lora_r: int = 8,
        lora_alpha: int = 16,
        device: Optional[str] = None,
    ):
        super().__init__()
        self.dev = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.tok = AutoTokenizer.from_pretrained(base_model_id, revision=base_revision)
        if self.tok.pad_token_id is None:
            self.tok.pad_token_id = self.tok.eos_token_id

        dtype = torch.float16 if self.dev == "cuda" else torch.float32
        base_backbone = AutoModel.from_pretrained(
            base_model_id,
            revision=base_revision,
            torch_dtype=dtype,
        )

        lora_config = LoraConfig(
            r=lora_r,
            lora_alpha=lora_alpha,
            target_modules=["q_proj", "v_proj"],
            lora_dropout=0.05,
            bias="none",
        )
        self.backbone = get_peft_model(base_backbone, lora_config)
        hidden_dim = base_backbone.config.hidden_size  # 576
        self.score_head = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
        )
        self.to(self.dev)

    def forward_score(self, texts: List[str]) -> torch.Tensor:
        """Computes scalar scores for a batch of input prompt+candidate strings."""
        enc = self.tok(
            texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        ).to(self.dev)

        outputs = self.backbone(**enc)
        # Attention mask mean pooling
        mask = enc["attention_mask"].unsqueeze(-1).to(outputs.last_hidden_state.dtype)
        h = (outputs.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-6)
        scores = self.score_head(h.float()).squeeze(-1)
        return scores

    def score_single(self, prompt: str, action_line: str) -> float:
        text = f"Goal Context: {prompt.strip()}\nProposed Work: {action_line.strip()}"
        with torch.no_grad():
            score = self.forward_score([text])
        return float(score.item())


def build_training_pairs() -> List[Tuple[str, str]]:
    """Builds balanced pairwise ranking training pairs (text_pos, text_neg)."""
    pairs: List[Tuple[str, str]] = []

    # 1. Pairs from prospective corpus (executable vs incorrect, abstention vs unsafe proposal)
    corpus_path = PACKAGE_ROOT / "pdi" / "data" / "pdi_v04_prospective_corpus.json"
    with open(corpus_path, "r", encoding="utf-8") as f:
        records = json.load(f)["records"]

    gen = DeterministicCandidateGenerator()
    for r in records[:180]:
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

        pos_actions = []
        neg_actions = []
        for s in menu.slots:
            ev = PostconditionEvaluator.evaluate_candidate(s.cand_id, s.action_line, {}, pred)
            if ev.label == TriStateLabel.USEFUL_WORK:
                pos_actions.append(s.action_line)
            elif ev.label == TriStateLabel.INCORRECT_WORK:
                neg_actions.append(s.action_line)

        for pa in pos_actions:
            for na in neg_actions[:2]:
                text_pos = f"Goal Context: {prompt.strip()}\nProposed Work: {pa.strip()}"
                text_neg = f"Goal Context: {prompt.strip()}\nProposed Work: {na.strip()}"
                pairs.append((text_pos, text_neg))

    # 2. Geometric distinction pairs (training set distinct from evaluation holdouts)
    # Generate training examples for symmetric dot vs oriented wedge
    for i in range(40):
        src_a = 50 + i * 2
        src_b = 51 + i * 2
        dest = 120 + i
        ver = 2000 + i * 5

        # Symmetric dot example
        p_dot = f"Context: Dest address {dest}, version {ver}. Pre-state: @{src_a} = 2s + 1e1, @{src_b} = 1s + 2e2. Task intent: Extract symmetric scalar projection metric between state {src_a} and state {src_b} into destination state {dest}."
        act_dot = f"PROPOSE OP_VECTOR_DOT REF_{src_a} REF_{src_b} GOAL_{dest}"
        act_wedge = f"PROPOSE OP_VECTOR_WEDGE REF_{src_a} REF_{src_b} GOAL_{dest}"
        pairs.append((
            f"Goal Context: {p_dot}\nProposed Work: {act_dot}",
            f"Goal Context: {p_dot}\nProposed Work: {act_wedge}",
        ))

        # Oriented wedge example
        p_wedge = f"Context: Dest address {dest}, version {ver}. Pre-state: @{src_a} = 2s + 1e1, @{src_b} = 1s + 2e2. Task intent: Construct oriented planar bivector span spanned by state {src_a} and state {src_b} into destination state {dest}."
        pairs.append((
            f"Goal Context: {p_wedge}\nProposed Work: {act_wedge}",
            f"Goal Context: {p_wedge}\nProposed Work: {act_dot}",
        ))

        # Non-commutative ordering example
        p_order = f"Context: Dest address {dest}, pre-state version {ver}. Pre-state: @{src_a} = 1s + 2e1, @{src_b} = 2e1 + 1.5e2. Goal: Compute oriented geometric Clifford product of state {src_a} by state {src_b} into destination state {dest}."
        act_order_pos = f"PROPOSE OP_CL20_PRODUCT REF_{src_a} REF_{src_b} GOAL_{dest}"
        act_order_neg = f"PROPOSE OP_CL20_PRODUCT REF_{src_b} REF_{src_a} GOAL_{dest}"
        pairs.append((
            f"Goal Context: {p_order}\nProposed Work: {act_order_pos}",
            f"Goal Context: {p_order}\nProposed Work: {act_order_neg}",
        ))

    return pairs


def train_lora_scorer():
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Building training pairs for LoRA fine-tuning...")
    pairs = build_training_pairs()
    print(f"Total training pairs: {len(pairs)}")

    print(f"Initializing SmolLM2-135M with LoRA on {dev}...")
    model = SmolLM2LoRAScorer(device=dev)

    # Trainable parameters: LoRA adapter + score head
    trainable_params = [p for p in model.parameters() if p.requires_grad]
    trainable_count = sum(p.numel() for p in trainable_params)
    print(f"Trainable parameters: {trainable_count:,}")

    optimizer = torch.optim.AdamW(trainable_params, lr=2e-4, weight_decay=1e-2)

    batch_size = 16
    epochs = 8
    ckpt_dir = PACKAGE_ROOT / "pdi" / "checkpoints" / "lora_scorer_v04"
    if (ckpt_dir / "score_head.pt").exists() and (ckpt_dir / "adapter").exists() and "--force-train" not in sys.argv:
        print(f"Loading existing fine-tuned LoRA checkpoint from {ckpt_dir}...")
        from peft import PeftModel
        # Load adapter weights into backbone
        model.backbone.load_adapter(str(ckpt_dir / "adapter"), adapter_name="default")
        model.score_head.load_state_dict(torch.load(ckpt_dir / "score_head.pt", map_location=dev, weights_only=True))
    else:
        print(f"Starting LoRA training ({epochs} epochs, batch_size={batch_size})...")
        model.train()
        for ep in range(epochs):
            random.shuffle(pairs)
            total_loss = 0.0
            n_batches = 0

            for i in range(0, len(pairs), batch_size):
                batch = pairs[i : i + batch_size]
                pos_texts = [p[0] for p in batch]
                neg_texts = [p[1] for p in batch]

                optimizer.zero_grad()
                scores_pos = model.forward_score(pos_texts)
                scores_neg = model.forward_score(neg_texts)

                # Pairwise ranking loss: log(1 + exp(-(s+ - s-)))
                diff = scores_pos - scores_neg
                loss = torch.log1p(torch.exp(-diff)).mean()

                loss.backward()
                torch.nn.utils.clip_grad_norm_(trainable_params, 1.0)
                optimizer.step()

                total_loss += loss.item()
                n_batches += 1

            mean_loss = total_loss / max(1, n_batches)
            print(f"Epoch {ep+1:2d}/{epochs:2d} | Mean Ranking Loss: {mean_loss:.4f}")

        model.eval()
        ckpt_dir.mkdir(parents=True, exist_ok=True)
        torch.save(model.score_head.state_dict(), ckpt_dir / "score_head.pt")
        model.backbone.save_pretrained(ckpt_dir / "adapter")
        print(f"Saved LoRA adapter and score head to: {ckpt_dir}")

    # Evaluate on the 64 Hard Ambiguity Challenge Suite
    challenge_path = PACKAGE_ROOT / "pdi" / "data" / "pdi_v04_hard_ambiguity_challenge.json"
    with open(challenge_path, "r", encoding="utf-8") as f:
        records = json.load(f)["records"]

    gen = DeterministicCandidateGenerator()
    cat_scores = {
        "NON_COMMUTATIVE_DISCRIMINATOR": [0, 0],
        "PARTIALLY_OBSERVABLE_UNDERSPECIFIED": [0, 0],
        "CONTEXTUAL_AMBIGUITY": [0, 0],
    }

    print("\nEvaluating Fine-Tuned SmolLM2-135M LoRA Scorer on Hard Challenge (64 scenarios)...")
    t0 = time.perf_counter()
    for r in records:
        cat = r["challenge_category"]
        cat_scores[cat][1] += 1
        prompt = r["input_prompt"]
        ctx = ObservableStateExtractor.extract_from_prompt(prompt, default_version=r["assumed_state_version"])
        menu = gen.generate_menu(r["scenario_id"], ctx, prompt)

        # Score all 8 candidates independently
        scored = []
        texts = [f"Goal Context: {prompt.strip()}\nProposed Work: {s.action_line.strip()}" for s in menu.slots]
        with torch.no_grad():
            scores = model.forward_score(texts).tolist()

        for s, score in zip(menu.slots, scores):
            scored.append((score, s.cand_id, s))

        # Select argmax with stable tie-breaking
        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        best_slot = scored[0][2]

        # Authoritative numerical verification
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
    mean_lat = total_time / len(records)

    total_c = sum(c[0] for c in cat_scores.values())
    total_t = sum(c[1] for c in cat_scores.values())

    print("\n" + "=" * 76)
    print("FINE-TUNED SMOLLM2-135M LORA SCORER (Hard Ambiguity Challenge)")
    print("=" * 76)
    print(f"Overall Useful Selection: {total_c}/{total_t} ({total_c/total_t*100:6.2f}%) | Latency mean: {mean_lat:6.2f} ms")
    for cat, (c, t) in cat_scores.items():
        print(f"    - {cat:36s}: {c:2d}/{t:2d} ({c/t*100:6.2f}%)")

    report_path = PACKAGE_ROOT / "pdi" / "qualification" / "pdi_v04_lora_scorer_benchmark.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "model": "SmolLM2-135M + LoRA Candidate-Wise Scorer",
            "trainable_parameters": trainable_count,
            "overall_useful_pct": round((total_c / total_t) * 100.0, 2),
            "latency_mean_ms": round(mean_lat, 2),
            "by_category": {
                cat: {"correct": c, "total": t, "pct": round((c / t) * 100.0, 2)}
                for cat, (c, t) in cat_scores.items()
            }
        }, f, indent=2)

    print(f"Saved LoRA evaluation report to: {report_path}")


if __name__ == "__main__":
    train_lora_scorer()
