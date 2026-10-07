# SPDX-License-Identifier: MIT
"""Canonical Binary Packet Codec for PDI-135M.

Encodes and decodes 16-word (64-byte) little-endian frames with IEEE 802.3 CRC-32
for the streaming 32-bit hardware interface.
"""

from __future__ import annotations

import binascii
from dataclasses import dataclass
from enum import IntEnum
import struct
from typing import List, Tuple


PDI_MAGIC: int = 0x50444930  # "PDI0"
PDI_VERSION: int = 1
PACKET_WORD_COUNT: int = 16
PACKET_BYTE_COUNT: int = PACKET_WORD_COUNT * 4


class PacketType(IntEnum):
    PROPOSAL = 1
    DISPOSITION = 2
    OBSERVE_REQ = 3
    OBSERVE_RESP = 4
    ERROR_ALERT = 5


class CommitOutcome(IntEnum):
    COMMIT = 0
    REJECT = 1
    REFUSE = 2
    FAULT = 3


class ReasonCode(IntEnum):
    REASON_COMMITTED = 0
    ERR_BAD_MAGIC = 1
    ERR_BAD_CRC = 2
    ERR_BAD_LENGTH = 3
    ERR_UNKNOWN_OPERATOR = 4
    ERR_OUT_OF_BOUNDS_REF = 5
    ERR_STALE_STATE_VERSION = 6
    ERR_UNAUTHORIZED_CAPABILITY = 7
    ERR_UNSATISFIED_DEPENDENCY = 8
    ERR_RESOURCE_EXHAUSTION = 9
    ERR_REPLAY_DUPLICATE = 10
    ERR_ARITHMETIC_FAULT = 11
    ERR_CONDITION_REJECT = 12


@dataclass
class ProposalPacket:
    seq_id: int
    proposal_id: int
    assumed_state_version: int
    opcode: int
    dest_addr: int = 0
    src_a_addr: int = 0
    src_b_addr: int = 0
    auth_token: int = 0
    use_immediate: bool = False
    has_graph_mut: bool = False
    dep_cond: int = 0
    imm_s: int = 0
    imm_e1: int = 0
    imm_e2: int = 0
    imm_e12: int = 0
    graph_start_node: int = 0
    graph_rel_filter: int = 0
    graph_type_filter: int = 0
    graph_radius: int = 0
    graph_mut_cmd: int = 0
    graph_mut_target: int = 0
    graph_mut_rel: int = 0
    graph_mut_flags: int = 0


@dataclass
class DispositionPacket:
    outcome: CommitOutcome
    seq_id: int
    proposal_id: int
    reason_code: ReasonCode
    dest_addr: int = 0
    dest_version: int = 0
    failed_check_mask: int = 0
    result_s: int = 0
    result_e1: int = 0
    result_e2: int = 0
    result_e12: int = 0
    evidence_root: int = 0
    telemetry_cycles: int = 0
    telemetry_ops: int = 0
    cert_id: int = 0


class PDIPacketCodec:
    """Canonical serializer and deserializer for PDI binary packets."""

    @staticmethod
    def compute_crc32(payload: bytes) -> int:
        """Standard IEEE 802.3 32-bit CRC."""
        return binascii.crc32(payload) & 0xFFFFFFFF

    @classmethod
    def encode_proposal(cls, pkt: ProposalPacket) -> bytes:
        """Encode a proposal packet into 64 bytes (16 words)."""
        # Word 0: Magic
        w0 = PDI_MAGIC

        # Word 1: type(8), ver(8), total_words(16)
        w1 = (PacketType.PROPOSAL & 0xFF) | ((PDI_VERSION & 0xFF) << 8) | ((PACKET_WORD_COUNT & 0xFFFF) << 16)

        # Word 2: seq_id
        w2 = pkt.seq_id & 0xFFFFFFFF

        # Word 3: proposal_id
        w3 = pkt.proposal_id & 0xFFFFFFFF

        # Word 4: assumed_state_version
        w4 = pkt.assumed_state_version & 0xFFFFFFFF

        # Word 5: opcode(6), res(2), dest_addr(8), src_a_addr(8), src_b_addr(8)
        w5 = (
            (pkt.opcode & 0x3F)
            | ((pkt.dest_addr & 0xFF) << 8)
            | ((pkt.src_a_addr & 0xFF) << 16)
            | ((pkt.src_b_addr & 0xFF) << 24)
        )

        # Word 6: auth_token
        w6 = pkt.auth_token & 0xFFFFFFFF

        # Word 7: use_immediate(1), has_graph_mut(1), dep_cond(3)
        w7 = (
            (1 if pkt.use_immediate else 0)
            | ((1 if pkt.has_graph_mut else 0) << 1)
            | ((pkt.dep_cond & 0x7) << 2)
        )

        # Words 8-11: imm_s, imm_e1, imm_e2, imm_e12 (signed 32-bit as uint32)
        w8 = pkt.imm_s & 0xFFFFFFFF
        w9 = pkt.imm_e1 & 0xFFFFFFFF
        w10 = pkt.imm_e2 & 0xFFFFFFFF
        w11 = pkt.imm_e12 & 0xFFFFFFFF

        # Word 12: graph_start_node(16), graph_rel_filter(8), graph_type_filter(8)
        w12 = (
            (pkt.graph_start_node & 0xFFFF)
            | ((pkt.graph_rel_filter & 0xFF) << 16)
            | ((pkt.graph_type_filter & 0xFF) << 24)
        )

        # Word 13: graph_radius(2), graph_mut_cmd(2), graph_mut_target(16), graph_mut_rel(8), graph_mut_flags(4)
        w13 = (
            (pkt.graph_radius & 0x3)
            | ((pkt.graph_mut_cmd & 0x3) << 2)
            | ((pkt.graph_mut_target & 0xFFFF) << 4)
            | ((pkt.graph_mut_rel & 0xFF) << 20)
            | ((pkt.graph_mut_flags & 0xF) << 28)
        )

        # Word 14: Reserved
        w14 = 0

        # Pack words 0..14 into bytes (little-endian)
        raw_words = [w0, w1, w2, w3, w4, w5, w6, w7, w8, w9, w10, w11, w12, w13, w14]
        body = struct.pack("<15I", *raw_words)

        # Word 15: CRC32
        crc = cls.compute_crc32(body)
        return body + struct.pack("<I", crc)

    @classmethod
    def decode_proposal(cls, raw: bytes) -> ProposalPacket:
        """Decode a 64-byte buffer into a ProposalPacket."""
        if len(raw) != PACKET_BYTE_COUNT:
            raise ValueError(f"Invalid packet length {len(raw)}, expected {PACKET_BYTE_COUNT} bytes")

        words = struct.unpack("<16I", raw)
        w0, w1, w2, w3, w4, w5, w6, w7, w8, w9, w10, w11, w12, w13, w14, w15 = words

        # Validate magic
        if w0 != PDI_MAGIC:
            raise ValueError(f"Magic mismatch: expected {hex(PDI_MAGIC)}, got {hex(w0)}")

        # Validate CRC
        expected_crc = cls.compute_crc32(raw[:60])
        if w15 != expected_crc:
            raise ValueError(f"CRC mismatch: expected {hex(expected_crc)}, got {hex(w15)}")

        # Check packet type and version
        pkt_type = w1 & 0xFF
        proto_ver = (w1 >> 8) & 0xFF
        if pkt_type != PacketType.PROPOSAL:
            raise ValueError(f"Unexpected packet type {pkt_type}, expected {PacketType.PROPOSAL}")
        if proto_ver != PDI_VERSION:
            raise ValueError(f"Unsupported protocol version {proto_ver}, expected {PDI_VERSION}")

        # Unpack fields
        seq_id = w2
        proposal_id = w3
        assumed_ver = w4
        opcode = w5 & 0x3F
        dest_addr = (w5 >> 8) & 0xFF
        src_a_addr = (w5 >> 16) & 0xFF
        src_b_addr = (w5 >> 24) & 0xFF
        auth_token = w6
        use_immediate = bool(w7 & 0x1)
        has_graph_mut = bool(w7 & 0x2)
        dep_cond = (w7 >> 2) & 0x7

        # Convert uint32 to signed int32 for multivector components
        def to_signed(val: int) -> int:
            return struct.unpack("<i", struct.pack("<I", val & 0xFFFFFFFF))[0]

        imm_s = to_signed(w8)
        imm_e1 = to_signed(w9)
        imm_e2 = to_signed(w10)
        imm_e12 = to_signed(w11)

        graph_start_node = w12 & 0xFFFF
        graph_rel_filter = (w12 >> 16) & 0xFF
        graph_type_filter = (w12 >> 24) & 0xFF

        graph_radius = w13 & 0x3
        graph_mut_cmd = (w13 >> 2) & 0x3
        graph_mut_target = (w13 >> 4) & 0xFFFF
        graph_mut_rel = (w13 >> 20) & 0xFF
        graph_mut_flags = (w13 >> 28) & 0xF

        return ProposalPacket(
            seq_id=seq_id,
            proposal_id=proposal_id,
            assumed_state_version=assumed_ver,
            opcode=opcode,
            dest_addr=dest_addr,
            src_a_addr=src_a_addr,
            src_b_addr=src_b_addr,
            auth_token=auth_token,
            use_immediate=use_immediate,
            has_graph_mut=has_graph_mut,
            dep_cond=dep_cond,
            imm_s=imm_s,
            imm_e1=imm_e1,
            imm_e2=imm_e2,
            imm_e12=imm_e12,
            graph_start_node=graph_start_node,
            graph_rel_filter=graph_rel_filter,
            graph_type_filter=graph_type_filter,
            graph_radius=graph_radius,
            graph_mut_cmd=graph_mut_cmd,
            graph_mut_target=graph_mut_target,
            graph_mut_rel=graph_mut_rel,
            graph_mut_flags=graph_mut_flags,
        )

    @classmethod
    def encode_disposition(cls, pkt: DispositionPacket) -> bytes:
        """Encode a disposition packet into 64 bytes (16 words)."""
        w0 = PDI_MAGIC
        w1 = (
            (PacketType.DISPOSITION & 0xFF)
            | ((PDI_VERSION & 0xFF) << 8)
            | ((int(pkt.outcome) & 0xFF) << 16)
        )
        w2 = pkt.seq_id & 0xFFFFFFFF
        w3 = pkt.proposal_id & 0xFFFFFFFF
        w4 = int(pkt.reason_code) & 0xFFFFFFFF
        w5 = (
            (pkt.dest_addr & 0xFF)
            | ((pkt.dest_version & 0xFFFF) << 8)
            | ((pkt.failed_check_mask & 0xFF) << 24)
        )
        w6 = pkt.result_s & 0xFFFFFFFF
        w7 = pkt.result_e1 & 0xFFFFFFFF
        w8 = pkt.result_e2 & 0xFFFFFFFF
        w9 = pkt.result_e12 & 0xFFFFFFFF
        w10 = pkt.evidence_root & 0xFFFFFFFF
        w11 = (pkt.evidence_root >> 32) & 0xFFFFFFFF
        w12 = pkt.telemetry_cycles & 0xFFFFFFFF
        w13 = pkt.telemetry_ops & 0xFFFFFFFF
        w14 = pkt.cert_id & 0xFFFFFFFF

        raw_words = [w0, w1, w2, w3, w4, w5, w6, w7, w8, w9, w10, w11, w12, w13, w14]
        body = struct.pack("<15I", *raw_words)
        crc = cls.compute_crc32(body)
        return body + struct.pack("<I", crc)

    @classmethod
    def decode_disposition(cls, raw: bytes) -> DispositionPacket:
        """Decode a 64-byte buffer into a DispositionPacket."""
        if len(raw) != PACKET_BYTE_COUNT:
            raise ValueError(f"Invalid packet length {len(raw)}, expected {PACKET_BYTE_COUNT} bytes")

        words = struct.unpack("<16I", raw)
        w0, w1, w2, w3, w4, w5, w6, w7, w8, w9, w10, w11, w12, w13, w14, w15 = words

        if w0 != PDI_MAGIC:
            raise ValueError(f"Magic mismatch: expected {hex(PDI_MAGIC)}, got {hex(w0)}")

        expected_crc = cls.compute_crc32(raw[:60])
        if w15 != expected_crc:
            raise ValueError(f"CRC mismatch: expected {hex(expected_crc)}, got {hex(w15)}")

        pkt_type = w1 & 0xFF
        if pkt_type != PacketType.DISPOSITION:
            raise ValueError(f"Unexpected packet type {pkt_type}, expected {PacketType.DISPOSITION}")

        outcome = CommitOutcome((w1 >> 16) & 0xFF)
        seq_id = w2
        proposal_id = w3
        reason_code = ReasonCode(w4)
        dest_addr = w5 & 0xFF
        dest_ver = (w5 >> 8) & 0xFFFF
        failed_mask = (w5 >> 24) & 0xFF

        def to_signed(val: int) -> int:
            return struct.unpack("<i", struct.pack("<I", val & 0xFFFFFFFF))[0]

        result_s = to_signed(w6)
        result_e1 = to_signed(w7)
        result_e2 = to_signed(w8)
        result_e12 = to_signed(w9)

        evidence_root = (w11 << 32) | w10
        telemetry_cycles = w12
        telemetry_ops = w13
        cert_id = w14

        return DispositionPacket(
            outcome=outcome,
            seq_id=seq_id,
            proposal_id=proposal_id,
            reason_code=reason_code,
            dest_addr=dest_addr,
            dest_version=dest_ver,
            failed_check_mask=failed_mask,
            result_s=result_s,
            result_e1=result_e1,
            result_e2=result_e2,
            result_e12=result_e12,
            evidence_root=evidence_root,
            telemetry_cycles=telemetry_cycles,
            telemetry_ops=telemetry_ops,
            cert_id=cert_id,
        )

    @staticmethod
    def to_32bit_words(raw: bytes) -> list[int]:
        """Convert a byte stream into a list of 32-bit unsigned words."""
        if len(raw) % 4 != 0:
            raise ValueError(f"Byte buffer length ({len(raw)}) not a multiple of 4")
        count = len(raw) // 4
        return list(struct.unpack(f"<{count}I", raw))

    @staticmethod
    def from_32bit_words(words: list[int]) -> bytes:
        """Convert a list of 32-bit unsigned words into little-endian bytes."""
        return struct.pack(f"<{len(words)}I", *[w & 0xFFFFFFFF for w in words])
