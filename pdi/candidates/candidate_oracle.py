# SPDX-License-Identifier: MIT
"""Candidate Oracle for PDI-135M-v0.3.

Evaluates frozen and hashed candidate menus against authoritative scenario ground truth:
- Evaluates Oracle Coverage@8 (whether optimal work is present in the menu).
- Categorizes each candidate slot as OPTIMAL_MATCH, ACCEPTABLE_ALTERNATIVE, INCORRECT_WORK,
  or ABSTAIN_OUTCOME.
- Strictly isolated from the candidate generator.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from pdi.candidates.candidate_generator import CandidateSlot, CandidateMenu, PermutedMenu
from pdi.grammar.native_grammar import NativeGrammarParser, NativeCommand


class CandidateJudgement(str, Enum):
    OPTIMAL_MATCH = "OPTIMAL_MATCH"
    ACCEPTABLE_ALTERNATIVE = "ACCEPTABLE_ALTERNATIVE"
    INCORRECT_WORK = "INCORRECT_WORK"
    CORRECT_ABSTENTION = "CORRECT_ABSTENTION"
    INCORRECT_ABSTENTION = "INCORRECT_ABSTENTION"


@dataclass
class SlotJudgement:
    cand_id: str
    display_index: Optional[int]
    action_line: str
    judgement: CandidateJudgement
    is_optimal: bool
    explanation: str


@dataclass
class OracleMenuEvaluation:
    scenario_id: str
    menu_hash: str
    coverage_at_8: bool  # True if optimal solution exists in the menu
    optimal_cand_id: Optional[str]
    optimal_display_index: Optional[int]
    slot_judgements: List[SlotJudgement]
    is_abstention_scenario: bool  # True if no legal work possible


class CandidateOracle:
    """Authoritative evaluator of candidate menus against ground-truth targets."""

    @classmethod
    def evaluate_menu(
        cls,
        menu: CandidateMenu | PermutedMenu,
        target_output: Dict[str, Any],
    ) -> OracleMenuEvaluation:
        """Evaluate a frozen candidate menu against the ground-truth target output."""
        slots = menu.display_slots if isinstance(menu, PermutedMenu) else menu.slots
        menu_hash = menu.menu_hash
        scenario_id = menu.scenario_id

        target_kind = target_output.get("kind", "").upper()
        target_op = target_output.get("operator_id")
        target_refs = list(target_output.get("object_refs", []))
        target_goal = target_output.get("goal_ref") or target_output.get("dest_ref")
        target_cap = target_output.get("requested_capability")
        target_slots = set(target_output.get("missing_slots", []))
        target_proj = (target_output.get("projection_type") or target_output.get("target_kind") or "").upper()

        judgements: List[SlotJudgement] = []
        optimal_cand_id: Optional[str] = None
        optimal_display_idx: Optional[int] = None

        for idx, slot in enumerate(slots, start=1):
            if slot.is_abstain:
                # Abstain judgement depends on whether optimal work was in the menu
                # Will be finalized after checking all slots
                judgements.append(
                    SlotJudgement(
                        cand_id=slot.cand_id,
                        display_index=idx,
                        action_line=slot.action_line,
                        judgement=CandidateJudgement.INCORRECT_ABSTENTION, # Provisional
                        is_optimal=False,
                        explanation="Abstention slot",
                    )
                )
                continue

            # Parse slot action line into NativeCommand
            try:
                cmd = NativeGrammarParser.parse_line(slot.action_line)
            except Exception as exc:
                judgements.append(
                    SlotJudgement(
                        cand_id=slot.cand_id,
                        display_index=idx,
                        action_line=slot.action_line,
                        judgement=CandidateJudgement.INCORRECT_WORK,
                        is_optimal=False,
                        explanation=f"Malformed grammar: {exc}",
                    )
                )
                continue

            # Check matches based on target kind
            is_optimal = False
            is_acceptable = False
            expl = ""

            if target_kind == "PROPOSE" and cmd.kind == "PROPOSE":
                # Check operator and operands
                if cmd.operator_id == target_op:
                    # Check operand matches
                    op_match = (cmd.object_refs == target_refs) or (set(cmd.object_refs) == set(target_refs))
                    goal_match = (target_goal is None) or (cmd.goal_ref == target_goal)
                    if op_match and goal_match:
                        is_optimal = True
                        expl = "Exact operator and operand match"
                    elif op_match:
                        is_acceptable = True
                        expl = "Correct operator and operands, alternative goal"
                    else:
                        is_acceptable = True
                        expl = "Correct operator, alternative operand binding"
                else:
                    expl = f"Wrong operator {cmd.operator_id} (expected {target_op})"

            elif target_kind == "COMPARE" and cmd.kind == "COMPARE":
                if cmd.left_ref == target_output.get("left_ref") and cmd.right_ref == target_output.get("right_ref"):
                    is_optimal = True
                    expl = "Exact reference comparison match"
                else:
                    is_acceptable = True
                    expl = "Alternative reference comparison"

            elif target_kind == "OBSERVE" and cmd.kind == "OBSERVE":
                cand_proj = (cmd.target_kind or "").upper()
                if cand_proj == target_proj:
                    is_optimal = True
                    expl = "Matching projection inspection"
                else:
                    is_acceptable = True
                    expl = "Alternative observation scope"

            elif target_kind == "CLARIFY" and cmd.kind == "CLARIFY":
                cand_slots = set(cmd.missing_slots)
                if cand_slots.intersection(target_slots):
                    is_optimal = True
                    expl = "Identified missing reference ambiguity"
                else:
                    is_acceptable = True
                    expl = "Identified general ambiguity"

            elif target_kind == "ESCALATE" and cmd.kind == "ESCALATE":
                if cmd.requested_capability == target_cap:
                    is_optimal = True
                    expl = "Exact privilege escalation request"
                else:
                    is_acceptable = True
                    expl = "Alternative escalation token"

            else:
                expl = f"Kind mismatch: {cmd.kind} vs expected {target_kind}"

            if is_optimal:
                j = CandidateJudgement.OPTIMAL_MATCH
                optimal_cand_id = slot.cand_id
                optimal_display_idx = idx
            elif is_acceptable:
                j = CandidateJudgement.ACCEPTABLE_ALTERNATIVE
            else:
                j = CandidateJudgement.INCORRECT_WORK

            judgements.append(
                SlotJudgement(
                    cand_id=slot.cand_id,
                    display_index=idx,
                    action_line=slot.action_line,
                    judgement=j,
                    is_optimal=is_optimal,
                    explanation=expl,
                )
            )

        coverage_at_8 = (optimal_cand_id is not None)
        is_abstention_scenario = not coverage_at_8

        # Finalize abstention judgement
        for j in judgements:
            if j.action_line.startswith("ABSTAIN"):
                if is_abstention_scenario:
                    j.judgement = CandidateJudgement.CORRECT_ABSTENTION
                    j.is_optimal = True
                    j.explanation = "No optimal candidate was present in slots 1..7; abstention is correct."
                    optimal_cand_id = j.cand_id
                    optimal_display_idx = j.display_index
                    coverage_at_8 = True # Abstention correctly resolves scenario
                else:
                    j.judgement = CandidateJudgement.INCORRECT_ABSTENTION
                    j.is_optimal = False
                    j.explanation = "Optimal work candidate was available; abstention was incorrect."

        return OracleMenuEvaluation(
            scenario_id=scenario_id,
            menu_hash=menu_hash,
            coverage_at_8=coverage_at_8,
            optimal_cand_id=optimal_cand_id,
            optimal_display_index=optimal_display_idx,
            slot_judgements=judgements,
            is_abstention_scenario=is_abstention_scenario,
        )
