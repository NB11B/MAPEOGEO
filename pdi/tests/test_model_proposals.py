# SPDX-License-Identifier: MIT
"""Unit tests for model proposal ingestion and conversion into hardware candidate packets."""

import json
from pathlib import Path
import pytest

from pdi.adapter.schema_validator import PDISchemaValidator
from pdi.adapter.host_transport import PDIHostSession
from pdi.adapter.packet_codec import PDIPacketCodec, PacketType


@pytest.fixture
def session():
    return PDIHostSession()


def test_positive_proposal_to_packet(session):
    model_json = {
        "schema_version": 1,
        "kind": "PROPOSE",
        "operator_id": 5,  # OP_CL20_PRODUCT
        "object_refs": [40, 41],
        "dest_ref": 42,
        "assumed_state_version": 1050,
    }

    pkt, raw_bytes = session.prepare_proposal(model_json, dest_addr=42, capability_token=0x01)
    assert len(raw_bytes) == 64
    assert pkt.opcode == 5
    assert pkt.dest_addr == 42
    assert pkt.src_a_addr == 40
    assert pkt.src_b_addr == 41
    assert pkt.assumed_state_version == 1050
    assert pkt.auth_token == 0x01


def test_parameterized_proposal_immediate_operand(session):
    model_json = {
        "schema_version": 1,
        "kind": "PROPOSE",
        "operator_id": 3,  # OP_MUL
        "object_refs": [20],
        "dest_ref": 22,
        "parameters": [
            {
                "type": "fixed_q16_16",
                "value": 2.5
            }
        ],
        "assumed_state_version": 200,
    }

    pkt, raw_bytes = session.prepare_proposal(model_json)
    assert pkt.use_immediate is True
    # 2.5 in Q16.16 is 2.5 * 65536 = 163840
    assert pkt.imm_s == 163840


def test_malformed_model_proposal_rejected_before_encoding(session):
    bad_model_json = {
        "schema_version": 1,
        "kind": "PROPOSE",
        "operator_id": 999,  # Invalid
        "object_refs": [1, 2],
        "assumed_state_version": 10,
    }

    with pytest.raises(ValueError, match="out of bounds"):
        session.prepare_proposal(bad_model_json)


def test_unauthorized_escalation_intent_captured(session):
    escalate_json = {
        "schema_version": 1,
        "kind": "ESCALATE",
        "requested_capability": 0x00000004,
        "reason": "Matrix bridge instruction requires elevated permission",
    }
    val = session.validator.validate_dict(escalate_json)
    assert val.is_valid
    assert val.normalized["kind"] == "ESCALATE"

    # Verify that ESCALATE is intercepted and NOT converted to hardware candidate UoW
    with pytest.raises(ValueError, match="Only PROPOSE operations map directly"):
        session.prepare_proposal(escalate_json)
