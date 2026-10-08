# SPDX-License-Identifier: MIT
"""Formal 4-Way Routing Policy for PDI-135M-v0.5.

Defines the operational decision mapping:
    Route(S, G, A) in { RULE, NEURAL, CLARIFY, REFUSE }

Properties:
1. REFUSE: Inadmissible work (address out-of-bounds, uncertified capabilities, version conflicts).
2. CLARIFY: Insufficient observable state (missing operands, unspecified destination).
3. RULE: Deterministically certified choice with score margin >= threshold over non-equivalent competitors.
4. NEURAL: Learnably distinguishable ambiguity (score margin < threshold, non-commutative ordering, or contextual intent).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

import torch

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from pdi.models.rule_scorer import DeterministicRelationScorer
from pdi.projection.work_relation_encoder import WorkRelationSignature


class RouteDecision(str, Enum):
    RULE = "RULE"
    NEURAL = "NEURAL"
    CLARIFY = "CLARIFY"
    REFUSE = "REFUSE"


@dataclass
class RoutingContext:
    decision: RouteDecision
    selected_sig: WorkRelationSignature
    margin: float
    top_score: float
    competitor_score: float
    notes: str = ""


class FormalRoutingPolicy:
    """Rigorous 4-way dispatch policy with structural gating and calibrated margin."""

    COMMUTATIVE_OPCODES = {1, 3, 9, 31, 33}  # ADD, MUL, VECTOR_DOT, ALU_ADD, ALU_MUL
    EQUIV_OPCODE_PAIRS = {(1, 31), (31, 1), (3, 33), (33, 3)}

    def __init__(
        self,
        margin_threshold: float = 10.0,
        lora_ckpt_dir: Optional[Path] = None,
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

    @classmethod
    def are_equivalent(cls, s1: WorkRelationSignature, s2: WorkRelationSignature) -> bool:
        if s1.structural.opcode is None or s2.structural.opcode is None:
            return False
        if s1.structural.opcode != s2.structural.opcode:
            if (s1.structural.opcode, s2.structural.opcode) not in cls.EQUIV_OPCODE_PAIRS:
                return False
        op = s1.structural.opcode
        if op in cls.COMMUTATIVE_OPCODES or op in {31, 33}:
            return s1.structural.dest_matches_goal == s2.structural.dest_matches_goal
        return False

    def route(
        self,
        signatures: List[WorkRelationSignature],
        input_prompt: str,
        is_partially_observable: bool = False,
        has_constraint_violation: bool = False,
    ) -> RoutingContext:
        prompt_lower = input_prompt.lower()

        # Gate 1: Check for hard constraint violations -> REFUSE
        for s in signatures:
            if s.constraints.has_safety_violation or has_constraint_violation:
                # Find refusal / abstain slot
                refuse_sig = next((x for x in signatures if x.constraints.is_abstention), signatures[-1])
                return RoutingContext(
                    decision=RouteDecision.REFUSE,
                    selected_sig=refuse_sig,
                    margin=999.0,
                    top_score=-100.0,
                    competitor_score=-100.0,
                    notes="Hardware/security constraint violation: refuse execution",
                )

        # Gate 2: Check for insufficient observable information -> CLARIFY
        if is_partially_observable or any(
            w in prompt_lower for w in ["missing primary", "unspecified", "conflict", "ambiguous multivector"]
        ):
            clarify_sig = next(
                (x for x in signatures if x.constraints.is_abstention or "CLARIFY" in x.action_line),
                signatures[-1],
            )
            return RoutingContext(
                decision=RouteDecision.CLARIFY,
                selected_sig=clarify_sig,
                margin=999.0,
                top_score=50.0,
                competitor_score=-10.0,
                notes="Insufficient observable state context: emit clarify / abstain",
            )

        # Gate 3: Score relation signatures using deterministic scorer
        scored_sigs = [(DeterministicRelationScorer.score_relation(s, input_prompt), s.cand_id, s) for s in signatures]
        scored_sigs.sort(key=lambda x: (x[0], x[1]), reverse=True)
        top_score, _, top_sig = scored_sigs[0]

        # Find competitor: highest scoring candidate not functionally equivalent to top_sig
        competing_score = -999.0
        for s_score, _, sig in scored_sigs[1:]:
            if not self.are_equivalent(top_sig, sig):
                competing_score = s_score
                break

        margin = top_score - competing_score if competing_score != -999.0 else 999.0

        # Gate 4: If margin >= threshold or top is abstention -> RULE (Fast-Path)
        if top_sig.constraints.is_abstention or margin >= self.margin_threshold:
            return RoutingContext(
                decision=RouteDecision.RULE,
                selected_sig=top_sig,
                margin=margin,
                top_score=top_score,
                competitor_score=competing_score,
                notes=f"Deterministically certified choice (margin={margin:.1f} >= {self.margin_threshold})",
            )

        # Gate 5: Unresolved ambiguity (margin < threshold) -> NEURAL (Slow-Path)
        self._ensure_lora_loaded()
        texts = [f"Goal Context: {input_prompt.strip()}\nProposed Work: {s.action_line.strip()}" for s in signatures]
        with torch.no_grad():
            neural_scores = self._lora_model.forward_score(texts).tolist()

        scored_neural = list(zip(neural_scores, [s.cand_id for s in signatures], signatures))
        scored_neural.sort(key=lambda x: (x[0], x[1]), reverse=True)
        winner_sig = scored_neural[0][2]

        return RoutingContext(
            decision=RouteDecision.NEURAL,
            selected_sig=winner_sig,
            margin=margin,
            top_score=top_score,
            competitor_score=competing_score,
            notes=f"Neural tiebreaker invoked (margin={margin:.1f} < {self.margin_threshold})",
        )
