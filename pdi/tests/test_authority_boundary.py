# SPDX-License-Identifier: MIT
"""Unit tests verifying the PDI authority isolation boundary."""

import pytest
from pdi.adapter.host_transport import PDIHostSession
from pdi.adapter.packet_codec import PDIPacketCodec, CommitOutcome, ReasonCode


def test_confidence_never_confers_authority():
    session = PDIHostSession()
    # Malicious or overconfident proposal asserting 1.0 confidence
    raw_input = {
        "schema_version": 1,
        "kind": "PROPOSE",
        "operator_id": 1,
        "object_refs": [5, 6],
        "assumed_state_version": 100,
        "confidence": 1.0,  # Asserting certainty
    }

    pkt, raw_bytes = session.prepare_proposal(raw_input, dest_addr=7, capability_token=0x01)
    decoded = PDIPacketCodec.decode_proposal(raw_bytes)

    # Decoded packet contains only granted auth_token, not confidence
    assert decoded.auth_token == 0x01
    assert not hasattr(decoded, "confidence")


def test_host_assigns_proposal_and_sequence_id():
    session = PDIHostSession()
    raw_1 = {
        "schema_version": 1,
        "kind": "PROPOSE",
        "operator_id": 1,
        "object_refs": [1, 2],
        "assumed_state_version": 10,
    }
    pkt1, _ = session.prepare_proposal(raw_1)
    pkt2, _ = session.prepare_proposal(raw_1)

    assert pkt2.seq_id == pkt1.seq_id + 1
    assert pkt2.proposal_id == pkt1.proposal_id + 1


def test_non_propose_cannot_be_encoded_as_uow():
    session = PDIHostSession()
    raw_observe = {
        "schema_version": 1,
        "kind": "OBSERVE",
        "projection_type": "STATE",
        "target_refs": [1],
    }

    with pytest.raises(ValueError, match="Only PROPOSE operations map directly to hardware candidate UoWs"):
        session.prepare_proposal(raw_observe)
