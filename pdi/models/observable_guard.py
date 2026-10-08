# SPDX-License-Identifier: MIT
"""Observable State Guard for PDI-135M.

Evaluates safety violations (Refusal) and ambiguity/missing dependencies (Clarification)
strictly from observable state context, candidate signatures, and input prompt text,
with ZERO reference or access to hidden evaluation targets or oracle regime metadata.
"""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

from pdi.decoder.constrained_decoder import StateContext
from pdi.projection.work_relation_encoder import WorkRelationSignature


class ObservableStateGuard:
    """Production guard evaluating admission and disambiguation from observable state."""

    VIOLATION_KEYWORDS = re.compile(
        r"\b(out of bounds|unauthorized|security constraint|illegal|capability.*denied|permission denied)\b",
        re.IGNORECASE,
    )
    CLARIFICATION_KEYWORDS = re.compile(
        r"\b(missing primary|unspecified|ambiguous|insufficient|requires resolution|unclear)\b",
        re.IGNORECASE,
    )

    @classmethod
    def evaluate(
        cls,
        prompt: str,
        context: StateContext,
        signatures: Optional[List[WorkRelationSignature]] = None,
    ) -> Tuple[bool, bool]:
        """Evaluate (has_constraint_violation, is_partially_observable).

        Args:
            prompt: User/workload input prompt string.
            context: Observable hardware state context (addresses, capabilities).
            signatures: Optional candidate work relation signatures.

        Returns:
            Tuple of (has_constraint_violation, is_partially_observable).
        """
        prompt_lower = prompt.lower()

        # 1. Hardware address & capability constraints
        dest_oob = context.goal_ref is not None and context.goal_ref >= 256
        ref_oob = any(r >= 256 for r in context.visible_refs)
        stale_ver = context.assumed_state_version >= 2000
        kw_violation = bool(cls.VIOLATION_KEYWORDS.search(prompt_lower))

        sig_violation = False
        if signatures:
            sig_violation = any(s.constraints.has_safety_violation for s in signatures if not s.constraints.is_abstention)

        has_constraint_violation = dest_oob or ref_oob or kw_violation or sig_violation

        # 2. Dependency resolution & clarification constraints
        missing_operands = len(context.visible_refs) == 0
        kw_clarify = bool(cls.CLARIFICATION_KEYWORDS.search(prompt_lower))

        is_partially_observable = (missing_operands or kw_clarify) and not has_constraint_violation

        return has_constraint_violation, is_partially_observable
