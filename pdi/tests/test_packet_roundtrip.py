# SPDX-License-Identifier: MIT
"""Unit tests for binary packet codec and CRC roundtrip."""

import pytest
from pdi.adapter.packet_codec import (
    PDIPacketCodec,
    ProposalPacket,
    DispositionPacket,
    CommitOutcome,
    ReasonCode,
)


def test_proposal_packet_roundtrip():
    original = ProposalPacket(
        seq_id=42,
        proposal_id=1001,
        assumed_state_version=9938,
        opcode=12,
        dest_addr=15,
        src_a_addr=10,
        src_b_addr=11,
        auth_token=0xDEADBEEF,
        use_immediate=True,
        has_graph_mut=False,
        dep_cond=1,
        imm_s=65536,  # 1.0 in Q16.16
        imm_e1=-32768,
        imm_e2=0,
        imm_e12=131072,
        graph_start_node=105,
        graph_rel_filter=3,
        graph_type_filter=7,
        graph_radius=2,
    )

    encoded = PDIPacketCodec.encode_proposal(original)
    assert len(encoded) == 64, f"Packet length {len(encoded)} != 64"

    decoded = PDIPacketCodec.decode_proposal(encoded)
    assert decoded.seq_id == original.seq_id
    assert decoded.proposal_id == original.proposal_id
    assert decoded.assumed_state_version == original.assumed_state_version
    assert decoded.opcode == original.opcode
    assert decoded.dest_addr == original.dest_addr
    assert decoded.src_a_addr == original.src_a_addr
    assert decoded.src_b_addr == original.src_b_addr
    assert decoded.auth_token == original.auth_token
    assert decoded.use_immediate == original.use_immediate
    assert decoded.imm_s == original.imm_s
    assert decoded.imm_e1 == original.imm_e1
    assert decoded.imm_e2 == original.imm_e2
    assert decoded.imm_e12 == original.imm_e12
    assert decoded.graph_start_node == original.graph_start_node


def test_disposition_packet_roundtrip():
    original = DispositionPacket(
        outcome=CommitOutcome.COMMIT,
        seq_id=42,
        proposal_id=1001,
        reason_code=ReasonCode.REASON_COMMITTED,
        dest_addr=15,
        dest_version=9939,
        failed_check_mask=0,
        result_s=131072,
        result_e1=0,
        result_e2=65536,
        result_e12=-65536,
        evidence_root=0x1122334455667788,
        telemetry_cycles=128,
        telemetry_ops=4,
        cert_id=77,
    )

    encoded = PDIPacketCodec.encode_disposition(original)
    assert len(encoded) == 64

    decoded = PDIPacketCodec.decode_disposition(encoded)
    assert decoded.outcome == original.outcome
    assert decoded.seq_id == original.seq_id
    assert decoded.proposal_id == original.proposal_id
    assert decoded.reason_code == original.reason_code
    assert decoded.dest_addr == original.dest_addr
    assert decoded.dest_version == original.dest_version
    assert decoded.result_s == original.result_s
    assert decoded.result_e1 == original.result_e1
    assert decoded.result_e2 == original.result_e2
    assert decoded.result_e12 == original.result_e12
    assert decoded.evidence_root == original.evidence_root
    assert decoded.cert_id == original.cert_id


def test_corrupted_crc_rejected():
    pkt = ProposalPacket(
        seq_id=1,
        proposal_id=10,
        assumed_state_version=1,
        opcode=1,
    )
    encoded = bytearray(PDIPacketCodec.encode_proposal(pkt))
    # Flip a single bit in the payload
    encoded[20] ^= 0x01

    with pytest.raises(ValueError, match="CRC mismatch"):
        PDIPacketCodec.decode_proposal(bytes(encoded))


def test_bad_magic_rejected():
    pkt = ProposalPacket(
        seq_id=1,
        proposal_id=10,
        assumed_state_version=1,
        opcode=1,
    )
    encoded = bytearray(PDIPacketCodec.encode_proposal(pkt))
    # Alter magic
    encoded[0] = 0xFF
    # Recompute CRC to bypass CRC check and trigger magic check
    body = bytes(encoded[:60])
    new_crc = PDIPacketCodec.compute_crc32(body)
    import struct
    encoded[60:64] = struct.pack("<I", new_crc)

    with pytest.raises(ValueError, match="Magic mismatch"):
        PDIPacketCodec.decode_proposal(bytes(encoded))
