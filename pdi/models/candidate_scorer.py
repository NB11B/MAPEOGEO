# SPDX-License-Identifier: MIT
"""Permutation-Equivariant Candidate-Wise Neural Scorer for PDI-135M-v0.4.

Implements two neural scoring formulations:
1. SequenceLikelihoodScorer (Arm B: Zero-Training Neural Representation):
   Evaluates candidate a_i via normalized token log-likelihood under frozen SmolLM2-135M:
       s(G, S, a_i) = (1 / |a_i|) * sum_{t=1}^{|a_i|} log P_theta(tok_t | Prompt, tok_<t)
   Strictly permutation-equivariant by construction.

2. LinearProbingScorer (Arm C: Representation Quality):
   Extracts last-hidden-state embeddings from frozen transformer and projects
   through a trained linear head:
       s(G, S, a_i) = w^T h(Prompt, a_i) + b

3. HybridSelector (Arm D: Operational System Value):
   - Fast-path: Dispatches deterministically if s_rule margin >= threshold.
   - Ambiguity-path: Invokes neural scorer only on tied/ambiguous candidate sets.
"""

from __future__ import annotations

import math
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import torch
import torch.nn as nn
from transformers import AutoModelForCausalLM, AutoTokenizer

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from pdi.projection.work_relation_encoder import WorkRelationSignature


class SequenceLikelihoodScorer:
    """Evaluates candidates using normalized token log-likelihood under frozen SmolLM2."""

    def __init__(
        self,
        base_model_id: str = "HuggingFaceTB/SmolLM2-135M-Instruct",
        base_revision: str = "12fd25f77366fa6b3b4b768ec3050bf629380bac",
        device: Optional[str] = None,
    ):
        self.dev = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.tok = AutoTokenizer.from_pretrained(base_model_id, revision=base_revision)
        if self.tok.pad_token_id is None:
            self.tok.pad_token_id = self.tok.eos_token_id

        dtype = torch.float16 if self.dev == "cuda" else torch.float32
        self.model = AutoModelForCausalLM.from_pretrained(
            base_model_id,
            revision=base_revision,
            dtype=dtype,
            device_map=self.dev,
        )
        self.model.eval()

    def score_candidate(self, prompt: str, action_line: str) -> float:
        """Compute normalized log-likelihood of action_line given prompt."""
        full_text = f"Goal Context: {prompt.strip()}\nProposed Work: {action_line.strip()}"
        prefix_text = f"Goal Context: {prompt.strip()}\nProposed Work:"

        enc_full = self.tok(full_text, return_tensors="pt").to(self.dev)
        enc_prefix = self.tok(prefix_text, return_tensors="pt").to(self.dev)

        prefix_len = enc_prefix["input_ids"].shape[1]
        full_len = enc_full["input_ids"].shape[1]

        if full_len <= prefix_len:
            return -100.0

        with torch.no_grad():
            outputs = self.model(**enc_full)
            logits = outputs.logits  # [1, seq_len, vocab_size]

        # Shift logits and compute log probabilities of the action tokens
        action_token_count = full_len - prefix_len
        log_probs = torch.log_softmax(logits, dim=-1)

        total_log_prob = 0.0
        for pos in range(prefix_len - 1, full_len - 1):
            target_token_id = enc_full["input_ids"][0, pos + 1]
            token_lp = log_probs[0, pos, target_token_id].item()
            total_log_prob += token_lp

        normalized_lp = total_log_prob / max(1, action_token_count)
        return float(normalized_lp)

    def select_best(
        self,
        signatures: List[WorkRelationSignature],
        input_prompt: str,
    ) -> Tuple[WorkRelationSignature, Dict[str, float]]:
        """Score each candidate independently and select the argmax with stable tie-breaking."""
        scored: List[Tuple[float, str, WorkRelationSignature]] = []
        score_dict: Dict[str, float] = {}

        for sig in signatures:
            lp = self.score_candidate(input_prompt, sig.action_line)
            score_dict[sig.cand_id] = lp
            scored.append((lp, sig.cand_id, sig))

        # Sort by score descending, then cand_id ascending for stable tie-breaking
        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return scored[0][2], score_dict


class LinearProbingScorer(nn.Module):
    """Linear probing head trained on frozen transformer hidden states."""

    def __init__(self, hidden_dim: int = 576):
        super().__init__()
        self.scorer = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.scorer(features).squeeze(-1)


class TwoStageHybridSelector:
    """Production Two-Stage Permutation-Equivariant Hybrid Work Selector.

    - Stage 1 (Fast-Path, 0.01 ms):
      Evaluates candidates using DeterministicRelationScorer s_rule(R_i).
      If candidate with top score is an abstention or margin >= threshold,
      dispatches deterministically without neural invocation.

    - Stage 2 (Slow-Path / Tiebreaker, ~30-40 ms):
      If top candidates have tied or near-tied scores (margin < threshold)
      representing non-commutative or contextual ambiguity, invokes
      fine-tuned SmolLM2-135M LoRA candidate-wise scorer.
    """

    def __init__(
        self,
        lora_ckpt_dir: Optional[Path] = None,
        margin_threshold: float = 10.0,
        device: Optional[str] = None,
    ):
        self.margin_threshold = margin_threshold
        self.dev = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.lora_ckpt_dir = lora_ckpt_dir or (PACKAGE_ROOT / "pdi" / "checkpoints" / "lora_scorer_v04")
        self._lora_model = None

    def _ensure_lora_loaded(self):
        if self._lora_model is None:
            from pdi.models.train_lora_scorer import SmolLM2LoRAScorer
            model = SmolLM2LoRAScorer(device=self.dev)
            if (self.lora_ckpt_dir / "adapter").exists() and (self.lora_ckpt_dir / "score_head.pt").exists():
                model.backbone.load_adapter(str(self.lora_ckpt_dir / "adapter"), adapter_name="default")
                model.score_head.load_state_dict(
                    torch.load(self.lora_ckpt_dir / "score_head.pt", map_location=self.dev, weights_only=True)
                )
            model.eval()
            self._lora_model = model

    COMMUTATIVE_OPCODES = {1, 3, 9, 31, 33}  # ADD, MUL, VECTOR_DOT, ALU_ADD, ALU_MUL

    @classmethod
    def are_equivalent(cls, s1: WorkRelationSignature, s2: WorkRelationSignature) -> bool:
        if s1.structural.opcode is None or s2.structural.opcode is None:
            return False
        if s1.structural.opcode != s2.structural.opcode:
            equiv_pairs = {(1, 31), (31, 1), (3, 33), (33, 3)}
            if (s1.structural.opcode, s2.structural.opcode) not in equiv_pairs:
                return False
        op = s1.structural.opcode
        if op in cls.COMMUTATIVE_OPCODES or op in {31, 33}:
            return s1.structural.dest_matches_goal == s2.structural.dest_matches_goal
        return False

    def select(
        self,
        signatures: List[WorkRelationSignature],
        input_prompt: str,
    ) -> Tuple[WorkRelationSignature, str]:
        """Selects candidate and returns (selected_signature, routing_path: 'FAST_PATH' | 'NEURAL_PATH')."""
        from pdi.models.rule_scorer import DeterministicRelationScorer

        scored_sigs = [(DeterministicRelationScorer.score_relation(s, input_prompt), s.cand_id, s) for s in signatures]
        scored_sigs.sort(key=lambda x: (x[0], x[1]), reverse=True)
        top_score, _, top_sig = scored_sigs[0]

        # Find competitor: highest scoring candidate that is not functionally equivalent to top_sig
        competing_score = -999.0
        for s_score, _, sig in scored_sigs[1:]:
            if not self.are_equivalent(top_sig, sig):
                competing_score = s_score
                break

        margin = top_score - competing_score if competing_score != -999.0 else 999.0

        if top_sig.constraints.is_abstention or margin >= self.margin_threshold:
            return top_sig, "FAST_PATH"

        # Stage 2: Ambiguous candidates, invoke LoRA scorer
        self._ensure_lora_loaded()
        texts = [f"Goal Context: {input_prompt.strip()}\nProposed Work: {s.action_line.strip()}" for s in signatures]
        with torch.no_grad():
            scores = self._lora_model.forward_score(texts).tolist()

        scored = list(zip(scores, [s.cand_id for s in signatures], signatures))
        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return scored[0][2], "NEURAL_PATH"

