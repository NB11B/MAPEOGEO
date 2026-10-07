# SPDX-License-Identifier: MIT
"""Host-side Transport and Session Controller enforcing the PDI Trust Boundary."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from pdi.adapter.schema_validator import PDISchemaValidator, ValidationResult
from pdi.adapter.packet_codec import (
    PDIPacketCodec,
    ProposalPacket,
    DispositionPacket,
    CommitOutcome,
    ReasonCode,
)


@dataclass
class PDIHostSession:
    """Deterministic host session managing packet sequence IDs and authority checks.
    
    CRITICAL INVARIANT: The host adapter does not grant execution authority.
    It formats untrusted candidate work into bounded packets and tracks
    authoritative dispositions returned by the deterministic FPGA fabric.
    """

    session_id: int = 1
    next_seq_id: int = 1
    next_proposal_id: int = 1000
    authorized_capability_mask: int = 0xFFFFFFFF
    known_state_versions: dict[int, int] = field(default_factory=dict)
    committed_history: list[DispositionPacket] = field(default_factory=list)
    validator: PDISchemaValidator = field(default_factory=PDISchemaValidator)

    def prepare_proposal(
        self,
        raw_model_json: str | dict[str, Any],
        dest_addr: Optional[int] = None,
        capability_token: Optional[int] = None,
    ) -> Tuple[ProposalPacket, bytes]:
        """Validate model output, assign transport framing, and encode into 64-byte packet."""
        if isinstance(raw_model_json, str):
            val_res = self.validator.validate_json_string(raw_model_json)
        else:
            val_res = self.validator.validate_dict(raw_model_json)

        val_res.raise_for_errors()
        data = val_res.normalized
        assert data is not None

        kind = data["kind"]
        if kind != "PROPOSE":
            raise ValueError(f"Only PROPOSE operations map directly to hardware candidate UoWs (got '{kind}')")

        # Assign unique transport IDs
        seq = self.next_seq_id
        self.next_seq_id += 1

        prop_id = self.next_proposal_id
        self.next_proposal_id += 1

        opcode = data["operator_id"]
        obj_refs = data.get("object_refs", [])
        src_a = obj_refs[0] if len(obj_refs) > 0 else 0
        src_b = obj_refs[1] if len(obj_refs) > 1 else 0

        target_dest = dest_addr if dest_addr is not None else data.get("dest_ref", 0)
        assumed_ver = data.get("assumed_state_version", 0)

        # Immediate multivector / scalar parameters
        use_imm = False
        imm_s, imm_e1, imm_e2, imm_e12 = 0, 0, 0, 0
        params = data.get("parameters", [])
        if params:
            use_imm = True
            p0 = params[0]
            val = p0["value"]
            p_type = p0["type"]
            if p_type in ("u32", "i32", "addr8"):
                imm_s = int(val)
            elif p_type == "fixed_q16_16":
                imm_s = int(round(float(val) * 65536.0))
            elif p_type == "cl20_mv" and isinstance(val, (list, tuple)) and len(val) == 4:
                imm_s = int(round(float(val[0]) * 65536.0))
                imm_e1 = int(round(float(val[1]) * 65536.0))
                imm_e2 = int(round(float(val[2]) * 65536.0))
                imm_e12 = int(round(float(val[3]) * 65536.0))

        # Authority token: model confidence is discarded; host applies authorized capability grant
        token = capability_token if capability_token is not None else 0x00000001

        pkt = ProposalPacket(
            seq_id=seq,
            proposal_id=prop_id,
            assumed_state_version=assumed_ver,
            opcode=opcode,
            dest_addr=target_dest,
            src_a_addr=src_a,
            src_b_addr=src_b,
            auth_token=token,
            use_immediate=use_imm,
            imm_s=imm_s,
            imm_e1=imm_e1,
            imm_e2=imm_e2,
            imm_e12=imm_e12,
        )

        raw_bytes = PDIPacketCodec.encode_proposal(pkt)
        return pkt, raw_bytes

    def record_disposition(self, disp: DispositionPacket) -> None:
        """Update local tracking with authoritative outcome from FPGA fabric."""
        self.committed_history.append(disp)
        if disp.outcome == CommitOutcome.COMMIT:
            self.known_state_versions[disp.dest_addr] = disp.dest_version
