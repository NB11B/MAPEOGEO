# SPDX-License-Identifier: MIT
"""Unit tests for Native Operational Grammar parser, AST, and token decoders."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import pytest

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from pdi.grammar.native_grammar import (
    NativeGrammarParser,
    NativePropose,
    NativeObserve,
    NativeCompare,
    NativeClarify,
    NativeEscalate,
    MNEMONIC_TO_OPCODE,
)
from pdi.decoder.constrained_decoder import (
    TokenTrie,
    StateContext,
)
from pdi.adapter.schema_validator import PDISchemaValidator
from pdi.adapter.packet_codec import PDIPacketCodec


def test_native_propose_parse_and_canonical_json():
    line = "PROPOSE OP_ADD REF_10 REF_11 GOAL_12"
    cmd = NativeGrammarParser.parse_line(line)
    assert isinstance(cmd, NativePropose)
    assert cmd.operator_id == 1
    assert cmd.object_refs == [10, 11]
    assert cmd.goal_ref == 12

    json_dict = cmd.to_canonical_json(state_version=1000)
    validator = PDISchemaValidator()
    val = validator.validate_dict(json_dict)
    assert val.is_valid, f"Validation errors: {val.errors}"
    assert json_dict["kind"] == "PROPOSE"
    assert json_dict["operator_id"] == 1


def test_native_propose_with_parameters():
    line = "PROPOSE OP_3 REF_20 REF_21 PARAM_u32_500 GOAL_25"
    cmd = NativeGrammarParser.parse_line(line)
    assert isinstance(cmd, NativePropose)
    assert cmd.operator_id == 3
    assert cmd.parameters == [{"type": "u32", "value": 500}]

    json_dict = cmd.to_canonical_json(state_version=1050)
    validator = PDISchemaValidator()
    val = validator.validate_dict(json_dict)
    assert val.is_valid, f"Validation errors: {val.errors}"


def test_native_observe_canonical_schema():
    line = "OBSERVE TARGET_STATE REF_10 REF_11"
    cmd = NativeGrammarParser.parse_line(line)
    assert isinstance(cmd, NativeObserve)
    assert cmd.target_kind == "STATE"
    assert cmd.object_refs == [10, 11]

    json_dict = cmd.to_canonical_json(state_version=1000)
    validator = PDISchemaValidator()
    val = validator.validate_dict(json_dict)
    assert val.is_valid, f"Validation errors: {val.errors}"
    assert json_dict["projection_type"] == "STATE"
    assert json_dict["target_refs"] == [10, 11]


def test_native_compare_canonical_schema():
    line = "COMPARE REF_15 REF_16"
    cmd = NativeGrammarParser.parse_line(line)
    assert isinstance(cmd, NativeCompare)
    assert cmd.left_ref == 15
    assert cmd.right_ref == 16

    json_dict = cmd.to_canonical_json(state_version=1000)
    validator = PDISchemaValidator()
    val = validator.validate_dict(json_dict)
    assert val.is_valid, f"Validation errors: {val.errors}"


def test_native_clarify_canonical_schema():
    line = "CLARIFY SLOT_operator_id,object_refs REASON_missing_required_reference"
    cmd = NativeGrammarParser.parse_line(line)
    assert isinstance(cmd, NativeClarify)
    assert "operator_id" in cmd.missing_slots
    assert "object_refs" in cmd.missing_slots

    json_dict = cmd.to_canonical_json(state_version=1000)
    validator = PDISchemaValidator()
    val = validator.validate_dict(json_dict)
    assert val.is_valid, f"Validation errors: {val.errors}"


def test_native_escalate_canonical_schema():
    line = "ESCALATE CAP_0x80000000 REASON_unauthorized_root_write"
    cmd = NativeGrammarParser.parse_line(line)
    assert isinstance(cmd, NativeEscalate)
    assert cmd.requested_capability == 0x80000000

    json_dict = cmd.to_canonical_json(state_version=1000)
    validator = PDISchemaValidator()
    val = validator.validate_dict(json_dict)
    assert val.is_valid, f"Validation errors: {val.errors}"


def test_native_compile_to_packet():
    line = "PROPOSE OP_CL20_PRODUCT REF_10 REF_11 GOAL_12"
    cmd = NativeGrammarParser.parse_line(line)
    pkt = NativeGrammarParser.compile_to_packet(
        cmd=cmd,
        assumed_state_version=1000,
        sequence_id=42,
        proposal_id=1001,
        auth_token=0x00000001,
    )
    assert pkt.opcode == 5
    assert pkt.src_a_addr == 10
    assert pkt.src_b_addr == 11
    assert pkt.dest_addr == 12
    assert pkt.seq_id == 42
    assert pkt.proposal_id == 1001

    raw = PDIPacketCodec.encode_proposal(pkt)
    assert len(raw) == 64
    dec = PDIPacketCodec.decode_proposal(raw)
    assert dec.opcode == 5
    assert dec.seq_id == 42


def test_token_trie_prefix_filtering():
    trie = TokenTrie(eos_token_id=0)
    trie.insert([10, 20, 30])
    trie.insert([10, 25, 35])

    # Prefix [] -> tokens 10
    assert trie.get_allowed_tokens([]) == {10}
    # Prefix [10] -> tokens 20, 25
    assert trie.get_allowed_tokens([10]) == {20, 25}
    # Prefix [10, 20] -> tokens 30
    assert trie.get_allowed_tokens([10, 20]) == {30}
    # Prefix [10, 20, 30] -> EOS
    assert trie.get_allowed_tokens([10, 20, 30]) == {0}
    # Prefix [99] -> departed from trie, returns EOS
    assert trie.get_allowed_tokens([99]) == {0}
