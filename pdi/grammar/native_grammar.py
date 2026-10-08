# SPDX-License-Identifier: MIT
"""Native Operational Grammar for MAPEOGEO PDI-135M.

Implements the compact, token-efficient native work grammar:
- PROPOSE OP_<id_or_name> REF_<r1> [REF_<r2>] [PARAM_<val>] [GOAL_<g>]
- OBSERVE [TARGET_<kind>] [REF_<r1>...]
- COMPARE REF_<r1> REF_<r2>
- CLARIFY SLOT_<name> REASON_<phrase>
- ESCALATE CAP_<hex> REASON_<phrase>

Decouples the neural model from verbose JSON serialization:
The model selects the operation and references; the deterministic host adapter
inserts schema versions, validated state versions, and packet framing.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from pdi.adapter.packet_codec import (
    PDIPacketCodec,
    ProposalPacket,
    PacketType,
    PDI_MAGIC,
)


# Load operator registry for mnemonic <-> opcode bidirectional lookup
OPERATORS_JSON_PATH = PACKAGE_ROOT / "pdi" / "spec" / "pdi_v0_operators.json"
with open(OPERATORS_JSON_PATH, "r", encoding="utf-8") as f:
    _REGISTRY = json.load(f)

MNEMONIC_TO_OPCODE: Dict[str, int] = {}
OPCODE_TO_MNEMONIC: Dict[int, str] = {}
for op in _REGISTRY["operators"]:
    code = op["opcode"]
    mne = op["mnemonic"].upper()
    MNEMONIC_TO_OPCODE[mne] = code
    OPCODE_TO_MNEMONIC[code] = mne
    # Also support without OP_ prefix
    if mne.startswith("OP_"):
        MNEMONIC_TO_OPCODE[mne[3:]] = code


class NativeCommand:
    """Base class for parsed native operational commands."""
    kind: str

    def to_canonical_json(self, state_version: int) -> Dict[str, Any]:
        raise NotImplementedError


class NativePropose(NativeCommand):
    kind = "PROPOSE"

    def __init__(
        self,
        operator_id: int,
        object_refs: List[int],
        parameters: Optional[List[Dict[str, Any]]] = None,
        goal_ref: Optional[int] = None,
    ):
        self.operator_id = operator_id
        self.object_refs = object_refs
        self.parameters = parameters or []
        self.goal_ref = goal_ref

    def to_line(self) -> str:
        mne = OPCODE_TO_MNEMONIC.get(self.operator_id, f"OP_{self.operator_id}")
        parts = ["PROPOSE", mne]
        for ref in self.object_refs:
            parts.append(f"REF_{ref}")
        for param in self.parameters:
            ptype = param.get("type", "u32")
            pval = param.get("value", 0)
            parts.append(f"PARAM_{ptype}_{pval}")
        if self.goal_ref is not None:
            parts.append(f"GOAL_{self.goal_ref}")
        return " ".join(parts)

    def to_canonical_json(self, state_version: int) -> Dict[str, Any]:
        res: Dict[str, Any] = {
            "schema_version": 1,
            "kind": "PROPOSE",
            "operator_id": self.operator_id,
            "object_refs": list(self.object_refs),
            "parameters": list(self.parameters),
            "assumed_state_version": state_version,
        }
        if self.goal_ref is not None:
            res["goal_ref"] = self.goal_ref
        return res


class NativeObserve(NativeCommand):
    kind = "OBSERVE"

    def __init__(
        self,
        target_kind: Optional[str] = None,
        object_refs: Optional[List[int]] = None,
    ):
        self.target_kind = target_kind
        self.object_refs = object_refs or []

    def to_line(self) -> str:
        parts = ["OBSERVE"]
        if self.target_kind:
            parts.append(f"TARGET_{self.target_kind}")
        for ref in self.object_refs:
            parts.append(f"REF_{ref}")
        return " ".join(parts)

    def to_canonical_json(self, state_version: int) -> Dict[str, Any]:
        pt = self.target_kind.upper() if self.target_kind else "STATE"
        refs = list(self.object_refs) if self.object_refs else [0]
        res: Dict[str, Any] = {
            "schema_version": 1,
            "kind": "OBSERVE",
            "projection_type": pt,
            "target_refs": refs,
        }
        return res


class NativeCompare(NativeCommand):
    kind = "COMPARE"

    def __init__(self, left_ref: int, right_ref: int):
        self.left_ref = left_ref
        self.right_ref = right_ref

    def to_line(self) -> str:
        return f"COMPARE REF_{self.left_ref} REF_{self.right_ref}"

    def to_canonical_json(self, state_version: int) -> Dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "COMPARE",
            "left_ref": self.left_ref,
            "right_ref": self.right_ref,
            "comparator": "EQUAL",
        }


class NativeClarify(NativeCommand):
    kind = "CLARIFY"

    def __init__(self, missing_slots: List[str], ambiguity_reason: str):
        self.missing_slots = missing_slots
        self.ambiguity_reason = ambiguity_reason

    def to_line(self) -> str:
        slots_str = ",".join(self.missing_slots)
        clean_reason = re.sub(r"[^\w\s-]", "", self.ambiguity_reason).strip().replace(" ", "_")
        return f"CLARIFY SLOT_{slots_str} REASON_{clean_reason}"

    def to_canonical_json(self, state_version: int) -> Dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "CLARIFY",
            "missing_slots": list(self.missing_slots),
            "ambiguity_reason": self.ambiguity_reason,
        }


class NativeEscalate(NativeCommand):
    kind = "ESCALATE"

    def __init__(self, requested_capability: int, escalation_reason: str):
        self.requested_capability = requested_capability
        self.escalation_reason = escalation_reason

    def to_line(self) -> str:
        clean_reason = re.sub(r"[^\w\s-]", "", self.escalation_reason).strip().replace(" ", "_")
        return f"ESCALATE CAP_0x{self.requested_capability:08X} REASON_{clean_reason}"

    def to_canonical_json(self, state_version: int) -> Dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "ESCALATE",
            "requested_capability": self.requested_capability,
            "reason": self.escalation_reason,
        }


class NativeGrammarParser:
    """Deterministic parser and compiler for Native Operational Grammar."""

    @staticmethod
    def parse_line(line: str) -> NativeCommand:
        """Parse a single line of native operational grammar."""
        tokens = line.strip().split()
        if not tokens:
            raise ValueError("Empty grammar string")

        kind = tokens[0].upper()
        if kind == "PROPOSE":
            return NativeGrammarParser._parse_propose(tokens[1:])
        elif kind == "OBSERVE":
            return NativeGrammarParser._parse_observe(tokens[1:])
        elif kind == "COMPARE":
            return NativeGrammarParser._parse_compare(tokens[1:])
        elif kind == "CLARIFY":
            return NativeGrammarParser._parse_clarify(tokens[1:])
        elif kind == "ESCALATE":
            return NativeGrammarParser._parse_escalate(tokens[1:])
        else:
            raise ValueError(f"Unknown native operation kind '{kind}'")

    @staticmethod
    def _parse_propose(args: List[str]) -> NativePropose:
        if not args:
            raise ValueError("PROPOSE missing operator argument")

        op_token = args[0].upper()
        if op_token.startswith("OP_"):
            mne_or_id = op_token[3:]
        else:
            mne_or_id = op_token

        if mne_or_id.isdigit():
            op_id = int(mne_or_id)
        elif op_token in MNEMONIC_TO_OPCODE:
            op_id = MNEMONIC_TO_OPCODE[op_token]
        elif mne_or_id in MNEMONIC_TO_OPCODE:
            op_id = MNEMONIC_TO_OPCODE[mne_or_id]
        else:
            raise ValueError(f"Unknown operator identifier '{op_token}'")

        object_refs: List[int] = []
        parameters: List[Dict[str, Any]] = []
        goal_ref: Optional[int] = None

        for tok in args[1:]:
            tok_upper = tok.upper()
            if tok_upper.startswith("REF_"):
                val = int(tok_upper[4:])
                object_refs.append(val)
            elif tok_upper.startswith("GOAL_"):
                goal_ref = int(tok_upper[5:])
            elif tok_upper.startswith("PARAM_"):
                # Format PARAM_<type>_<val>
                parts = tok.split("_", 2)
                if len(parts) == 3:
                    ptype = parts[1].lower()
                    pval = int(parts[2])
                    parameters.append({"type": ptype, "value": pval})
                elif len(parts) == 2:
                    parameters.append({"type": "u32", "value": int(parts[1])})

        return NativePropose(
            operator_id=op_id,
            object_refs=object_refs,
            parameters=parameters,
            goal_ref=goal_ref,
        )

    @staticmethod
    def _parse_observe(args: List[str]) -> NativeObserve:
        target_kind: Optional[str] = None
        object_refs: List[int] = []
        for tok in args:
            tok_upper = tok.upper()
            if tok_upper.startswith("TARGET_"):
                target_kind = tok[7:]
            elif tok_upper.startswith("REF_"):
                object_refs.append(int(tok_upper[4:]))
        return NativeObserve(target_kind=target_kind, object_refs=object_refs)

    @staticmethod
    def _parse_compare(args: List[str]) -> NativeCompare:
        refs = [int(tok[4:]) for tok in args if tok.upper().startswith("REF_")]
        if len(refs) < 2:
            raise ValueError(f"COMPARE requires 2 object refs, got {refs}")
        return NativeCompare(left_ref=refs[0], right_ref=refs[1])

    @staticmethod
    def _parse_clarify(args: List[str]) -> NativeClarify:
        missing_slots: List[str] = []
        reason_parts: List[str] = []
        for tok in args:
            if tok.upper().startswith("SLOT_"):
                slots_raw = tok[5:].split(",")
                missing_slots.extend([s for s in slots_raw if s])
            elif tok.upper().startswith("REASON_"):
                reason_parts.append(tok[7:].replace("_", " "))
            else:
                reason_parts.append(tok)
        reason_str = " ".join(reason_parts) if reason_parts else "unspecified ambiguity"
        if not missing_slots:
            missing_slots = ["unspecified"]
        return NativeClarify(missing_slots=missing_slots, ambiguity_reason=reason_str)

    @staticmethod
    def _parse_escalate(args: List[str]) -> NativeEscalate:
        cap_val = 0
        reason_parts: List[str] = []
        for tok in args:
            if tok.upper().startswith("CAP_"):
                cap_str = tok[4:]
                cap_val = int(cap_str, 16) if cap_str.lower().startswith("0x") else int(cap_str)
            elif tok.upper().startswith("REASON_"):
                reason_parts.append(tok[7:].replace("_", " "))
            else:
                reason_parts.append(tok)
        reason_str = " ".join(reason_parts) if reason_parts else "unspecified escalation"
        return NativeEscalate(requested_capability=cap_val, escalation_reason=reason_str)

    @staticmethod
    def compile_to_packet(
        cmd: NativeCommand,
        assumed_state_version: int,
        sequence_id: int,
        proposal_id: int,
        auth_token: int = 0,
    ) -> ProposalPacket:
        """Compile a parsed NativeCommand directly into an authoritative 64-byte ProposalPacket."""
        if not isinstance(cmd, NativePropose):
            raise ValueError(f"Only PROPOSE commands can be packed into hardware UoW, got {cmd.kind}")

        obj_refs = list(cmd.object_refs)
        src0 = obj_refs[0] if len(obj_refs) > 0 else 0
        src1 = obj_refs[1] if len(obj_refs) > 1 else 0
        dest = cmd.goal_ref if cmd.goal_ref is not None else (obj_refs[2] if len(obj_refs) > 2 else src0)

        imm_val = 0
        if cmd.parameters:
            imm_val = int(cmd.parameters[0].get("value", 0))

        return ProposalPacket(
            seq_id=sequence_id,
            proposal_id=proposal_id,
            assumed_state_version=assumed_state_version,
            opcode=cmd.operator_id,
            dest_addr=dest,
            src_a_addr=src0,
            src_b_addr=src1,
            auth_token=auth_token,
            use_immediate=(imm_val != 0),
            imm_s=imm_val,
        )
