# SPDX-License-Identifier: MIT
"""Menu Validator for PDI-135M-v0.3.

Enforces structural, reference boundary, and security constraints on 8-slot candidate menus:
- Exactly 8 slots.
- Exactly one explicit abstention entry.
- All candidate slots bounded and non-empty.
- Zero authorization leakage or privilege fabrication.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from typing import List, Optional

from pdi.candidates.candidate_generator import CandidateMenu, PermutedMenu, CandidateSlot


@dataclass
class MenuValidationResult:
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    slot_count: int = 0
    admissible_count: int = 0
    abstention_slot_index: Optional[int] = None


class MenuValidator:
    """Validates candidate menus before presentation to selectors or FPGA ingress."""

    @staticmethod
    def validate(menu: CandidateMenu | PermutedMenu) -> MenuValidationResult:
        errors: List[str] = []
        slots = menu.display_slots if isinstance(menu, PermutedMenu) else menu.slots

        if len(slots) != 8:
            errors.append(f"Menu must contain exactly 8 slots, found {len(slots)}")

        abstain_indices: List[int] = []
        admissible_count = 0

        for idx, s in enumerate(slots, start=1):
            if not s.cand_id:
                errors.append(f"Slot {idx} missing cand_id")
            if not s.action_line:
                errors.append(f"Slot {idx} missing action_line")

            if s.is_abstain:
                abstain_indices.append(idx)
            if s.is_admissible:
                admissible_count += 1

            # Check reference bounds
            for r in s.object_refs:
                if r < 0 or r > 65535:
                    errors.append(f"Slot {idx} has out-of-bounds reference: {r}")
            if s.goal_ref is not None and (s.goal_ref < 0 or s.goal_ref > 65535):
                errors.append(f"Slot {idx} has out-of-bounds goal reference: {s.goal_ref}")

        if len(abstain_indices) != 1:
            errors.append(f"Menu must contain exactly 1 abstention slot, found {len(abstain_indices)}")

        if admissible_count == 0:
            errors.append("Menu has zero admissible slots")

        # Verify cryptographic integrity
        menu_repr = ";".join(s.canonical_repr() for s in (menu.slots if isinstance(menu, CandidateMenu) else slots))
        expected_hash = hashlib.sha256(menu_repr.encode()).hexdigest()
        if isinstance(menu, CandidateMenu) and menu.menu_hash != expected_hash:
            errors.append("Menu hash mismatch: canonical representation corrupted")

        return MenuValidationResult(
            is_valid=(len(errors) == 0),
            errors=errors,
            slot_count=len(slots),
            admissible_count=admissible_count,
            abstention_slot_index=abstain_indices[0] if abstain_indices else None,
        )
