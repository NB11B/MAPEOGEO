# SPDX-License-Identifier: MIT
"""Deterministic Candidate Work Generator for PDI-135M-v0.3.

Synthesizes fixed eight-slot candidate menus (K=8) strictly from observable state:
- Slots 1..7: Admissible candidate work proposals.
- Slot 8: Explicit abstention (ABSTAIN / NONE_OF_THE_ABOVE).

Requirements:
- Generates candidates independently from oracle ground-truth labels.
- Preserves candidate identity under menu permutations.
- Produces validity masks and cryptographic menu hashes prior to oracle scoring.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import random
import sys
from typing import Any, Dict, List, Optional, Tuple

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from pdi.grammar.native_grammar import (
    OPCODE_TO_MNEMONIC,
    MNEMONIC_TO_OPCODE,
    NativeCommand,
    NativeGrammarParser,
    NativePropose,
    NativeObserve,
    NativeCompare,
    NativeClarify,
    NativeEscalate,
)
from pdi.decoder.constrained_decoder import StateContext


@dataclass
class CandidateSlot:
    """A discrete candidate work slot in the menu."""
    cand_id: str
    action_line: str
    is_abstain: bool = False
    is_admissible: bool = True
    operator_id: Optional[int] = None
    object_refs: List[int] = field(default_factory=list)
    goal_ref: Optional[int] = None
    notes: str = ""

    def canonical_repr(self) -> str:
        return f"{self.cand_id}:{self.action_line}:{int(self.is_abstain)}:{int(self.is_admissible)}"


@dataclass
class PermutedMenu:
    """A fixed candidate menu permuted under an independent seed."""
    scenario_id: str
    seed: int
    display_slots: List[CandidateSlot]  # Length 8
    # Map from 1-based display index (1..8) to original cand_id
    index_to_cand_id: Dict[int, str]
    menu_hash: str
    validity_mask: int  # 8-bit mask of admissible slots

    def format_prompt_menu(self) -> str:
        lines = []
        for idx, slot in enumerate(self.display_slots, start=1):
            adm_marker = "" if slot.is_admissible else " [INELIGIBLE]"
            lines.append(f"[{idx}] {slot.action_line}{adm_marker}")
        return "\n".join(lines)


@dataclass
class CandidateMenu:
    """Frozen eight-slot candidate menu before permutation."""
    scenario_id: str
    state_snapshot_version: int
    slots: List[CandidateSlot]  # Exactly 8 slots
    validity_mask: int
    menu_hash: str
    failure_reasons: List[str] = field(default_factory=list)

    def permute(self, seed: int) -> PermutedMenu:
        """Create a deterministically permuted view using seed."""
        rng = random.Random(seed)
        permuted = list(self.slots)
        rng.shuffle(permuted)

        index_to_cand: Dict[int, str] = {}
        mask = 0
        for i, slot in enumerate(permuted, start=1):
            index_to_cand[i] = slot.cand_id
            if slot.is_admissible:
                mask |= (1 << (i - 1))

        return PermutedMenu(
            scenario_id=self.scenario_id,
            seed=seed,
            display_slots=permuted,
            index_to_cand_id=index_to_cand,
            menu_hash=self.menu_hash,
            validity_mask=mask,
        )


class DeterministicCandidateGenerator:
    """Generates K=8 candidate menus from observable state and goal prompts without oracle knowledge."""

    def __init__(self, operators_path: Optional[Path] = None):
        base_dir = Path(__file__).resolve().parent.parent / "spec"
        op_path = operators_path or (base_dir / "pdi_v0_operators.json")
        with open(op_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.operators = {op["opcode"]: op for op in data["operators"]}

    def generate_menu(
        self,
        scenario_id: str,
        context: StateContext,
        input_prompt: str,
    ) -> CandidateMenu:
        """Construct exactly 8 candidate slots from state context and input prompt."""
        slots: List[CandidateSlot] = []
        failures: List[str] = []

        refs = list(context.visible_refs)
        ver = context.assumed_state_version
        goal = context.goal_ref

        prompt_lower = input_prompt.lower()

        # Heuristic detection of candidate families matching context without seeing target label
        detected_opcodes: List[int] = []

        if "add" in prompt_lower or "+" in prompt_lower or "addition" in prompt_lower:
            detected_opcodes.extend([1, 31]) # OP_ADD, OP_ALU_ADD
        if "sub" in prompt_lower or "-" in prompt_lower or "subtract" in prompt_lower:
            detected_opcodes.extend([2, 32]) # OP_SUB, OP_ALU_SUB
        if "mul" in prompt_lower or "*" in prompt_lower or "multiply" in prompt_lower:
            detected_opcodes.extend([3, 33]) # OP_MUL, OP_ALU_MUL
        if "clifford" in prompt_lower or "geometric product" in prompt_lower:
            detected_opcodes.extend([5, 17]) # OP_CL20_PRODUCT, OP_COMPOSE
        if "reverse" in prompt_lower or "reversion" in prompt_lower:
            detected_opcodes.append(6)       # OP_REVERSE
        if "involution" in prompt_lower:
            detected_opcodes.append(7)       # OP_GRADE_INVOLUTION
        if "conjugate" in prompt_lower:
            detected_opcodes.append(8)       # OP_CLIFFORD_CONJUGATE
        if "dot" in prompt_lower:
            detected_opcodes.append(9)       # OP_VECTOR_DOT
        if "wedge" in prompt_lower:
            detected_opcodes.append(10)      # OP_VECTOR_WEDGE
        if "commutator" in prompt_lower and "anticommutator" not in prompt_lower:
            detected_opcodes.append(11)      # OP_COMMUTATOR
        if "anticommutator" in prompt_lower:
            detected_opcodes.append(12)      # OP_ANTICOMMUTATOR
        if "scalar" in prompt_lower and "projection" in prompt_lower:
            detected_opcodes.append(13)      # OP_SCALAR_PROJECTION
        if "vector" in prompt_lower and "projection" in prompt_lower:
            detected_opcodes.append(14)      # OP_VECTOR_PROJECTION
        if "bivector" in prompt_lower and "projection" in prompt_lower:
            detected_opcodes.append(15)      # OP_BIVECTOR_PROJECTION
        if "norm" in prompt_lower:
            detected_opcodes.append(16)      # OP_NORM_SQUARED
        if "matrix" in prompt_lower:
            detected_opcodes.extend([18, 19])# OP_MATRIX_TO_CL20, OP_CL20_TO_MATRIX

        # If no specific operator detected, fallback to standard basis operators
        if not detected_opcodes:
            detected_opcodes = [1, 2, 4, 5, 9, 10]

        # Deduplicate detected opcodes while preserving order
        unique_opcodes: List[int] = []
        for op in detected_opcodes:
            if op not in unique_opcodes:
                unique_opcodes.append(op)

        # 1. Synthesize candidate work units for slots 1..7
        # Strategy:
        # Candidate A: Detected operator with first 2 visible refs and goal
        r0 = refs[0] if len(refs) > 0 else 10
        r1 = refs[1] if len(refs) > 1 else (refs[0] if len(refs) > 0 else 11)

        candidate_actions: List[Tuple[str, Optional[int], List[int], Optional[int]]] = []

        # Generate action variations
        for op in unique_opcodes[:4]:
            mne = OPCODE_TO_MNEMONIC.get(op, f"OP_{op}")
            # Two operands if arity >= 2
            arity = self.operators.get(op, {}).get("arity", 2)
            if arity >= 2:
                action = f"PROPOSE {mne} REF_{r0} REF_{r1}"
                if goal is not None:
                    action += f" GOAL_{goal}"
                candidate_actions.append((action, op, [r0, r1], goal))

                # Reverse operand permutation
                action_rev = f"PROPOSE {mne} REF_{r1} REF_{r0}"
                if goal is not None:
                    action_rev += f" GOAL_{goal}"
                candidate_actions.append((action_rev, op, [r1, r0], goal))
            else:
                action = f"PROPOSE {mne} REF_{r0}"
                if goal is not None:
                    action += f" GOAL_{goal}"
                candidate_actions.append((action, op, [r0], goal))

        # Add COMPARE alternative
        if len(refs) >= 2:
            candidate_actions.append((f"COMPARE REF_{r0} REF_{r1}", 4, [r0, r1], None))

        # Add OBSERVE alternative
        candidate_actions.append(("OBSERVE TARGET_STATE REF_0", None, [0], None))
        candidate_actions.append(("OBSERVE TARGET_TELEMETRY REF_0", None, [0], None))
        candidate_actions.append(("OBSERVE TARGET_EVIDENCE REF_0", None, [0], None))

        # Add CLARIFY alternative
        candidate_actions.append(("CLARIFY SLOT_operator_id REASON_unspecified_ambiguity", None, [], None))
        candidate_actions.append(("CLARIFY SLOT_object_refs REASON_missing_required_reference", None, [], None))

        # Add ESCALATE alternative
        candidate_actions.append(("ESCALATE CAP_0x80000000 REASON_unauthorized_capability_required", None, [], None))

        # Take up to 7 distinct candidate actions
        seen_lines: set[str] = set()
        for act, op_id, o_refs, g_ref in candidate_actions:
            if act in seen_lines:
                continue
            seen_lines.add(act)
            cid = hashlib.sha256(act.encode()).hexdigest()[:12]
            slots.append(
                CandidateSlot(
                    cand_id=cid,
                    action_line=act,
                    is_abstain=False,
                    is_admissible=True,
                    operator_id=op_id,
                    object_refs=o_refs,
                    goal_ref=g_ref,
                    notes="Deterministic candidate",
                )
            )
            if len(slots) == 7:
                break

        # If fewer than 7 slots produced, pad with valid no-op / observe slots
        pad_idx = 0
        while len(slots) < 7:
            pad_act = f"OBSERVE TARGET_STATE REF_{pad_idx}"
            cid = hashlib.sha256(pad_act.encode()).hexdigest()[:12]
            slots.append(
                CandidateSlot(
                    cand_id=cid,
                    action_line=pad_act,
                    is_abstain=False,
                    is_admissible=True,
                    notes="Padded candidate",
                )
            )
            pad_idx += 1

        # Slot 8: Explicit Abstention
        abstain_act = "ABSTAIN / NONE_OF_THE_ABOVE"
        abstain_cid = hashlib.sha256(f"ABSTAIN:{scenario_id}".encode()).hexdigest()[:12]
        slots.append(
            CandidateSlot(
                cand_id=abstain_cid,
                action_line=abstain_act,
                is_abstain=True,
                is_admissible=True,
                notes="Explicit Abstention Slot",
            )
        )

        assert len(slots) == 8, f"Menu must contain exactly 8 slots, got {len(slots)}"

        # Compute validity mask
        validity_mask = 0
        for i, s in enumerate(slots):
            if s.is_admissible:
                validity_mask |= (1 << i)

        # Compute canonical menu hash
        menu_repr = ";".join(s.canonical_repr() for s in slots)
        menu_hash = hashlib.sha256(menu_repr.encode()).hexdigest()

        return CandidateMenu(
            scenario_id=scenario_id,
            state_snapshot_version=ver,
            slots=slots,
            validity_mask=validity_mask,
            menu_hash=menu_hash,
            failure_reasons=failures,
        )
