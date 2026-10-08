# SPDX-License-Identifier: MIT
"""Deterministic PSMSL Work-Relation Scorer s_rule(R_i) for PDI-135M-v0.4.

Evaluates candidates purely from their PSMSL work-relation signature R_i:
    s_rule(R_i) in R
    a* = argmax_{a_i in A_8} s_rule(Phi_PSMSL(G, S, a_i))

Properties:
- Non-neural baseline operating directly on geometric and causal relation features.
- Permutation-equivariant by construction with stable cryptographic cand_id tie-breaking.
- Evaluates whether structural and constraint representations suffice without neural inference.
"""

from __future__ import annotations

import re
from typing import List, Tuple

from pdi.projection.work_relation_encoder import WorkRelationSignature


class DeterministicRelationScorer:
    """Scores work-relation signatures deterministically without learned weights."""

    @classmethod
    def score_relation(
        cls,
        rel: WorkRelationSignature,
        input_prompt: str,
    ) -> float:
        prompt_lower = input_prompt.lower()

        # Hard refusal constraint
        if rel.constraints.has_safety_violation:
            return -100.0

        # Abstention evaluation
        if rel.constraints.is_abstention:
            is_refusal_prompt = bool(
                re.search(r"\b(unauthorized|without capability|missing|ambiguity|unspecified|conflict|refuse)\b", prompt_lower)
            )
            return 50.0 if is_refusal_prompt else -10.0

        score = 0.0

        # Structural & Goal alignment
        if rel.structural.dest_matches_goal:
            score += 25.0

        if rel.structural.opcode is not None:
            # Check if opcode mnemonic or description keywords appear in prompt
            act_words = rel.action_line.lower().split()
            for w in act_words:
                if len(w) > 3 and w in prompt_lower:
                    score += 10.0

        if rel.geometric.grade_compatible:
            score += 5.0

        if rel.causal.is_version_current:
            score += 5.0

        return score

    @classmethod
    def select_candidate(
        cls,
        signatures: List[WorkRelationSignature],
        input_prompt: str,
    ) -> WorkRelationSignature:
        """Select best candidate using independent scoring and stable cand_id tie-breaking."""
        scored: List[Tuple[float, str, WorkRelationSignature]] = []

        for sig in signatures:
            s = cls.score_relation(sig, input_prompt)
            # Tuple: (score, negative cand_id for deterministic max selection)
            scored.append((s, sig.cand_id, sig))

        # Sort by score descending, then by cand_id ascending for stable tie-breaking
        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return scored[0][2]
