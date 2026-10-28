import json
import pytest
from experiments.mapeogeo_llm.contracts import ACTION_SCHEMA, ContractError
from experiments.mapeogeo_llm.parser import parse_action, parse_actions


def test_parser_accepts_canonical_json_only():
    payload = {"schema": ACTION_SCHEMA, "op": "XOR", "src": [
        {"kind": "input", "id": "a"}, {"kind": "literal", "value": 7}], "dst": "r0"}
    assert parse_action(json.dumps(payload)).op == "XOR"
    assert parse_actions(json.dumps([payload]))[0].dst == "r0"


@pytest.mark.parametrize("payload", [
    "not json", "__import__('os').system('echo unsafe')", "[]", "null",
    '{"schema":"mapeogeo.llm.action.v1","op":"ADD","src":{},"dst":"r0"}',
])
def test_parser_rejects_malformed_or_unsafe_input(payload):
    with pytest.raises(ContractError):
        parse_action(payload)


def test_parser_rejects_duplicate_json_keys():
    with pytest.raises(ContractError):
        parse_action('{"schema":"mapeogeo.llm.action.v1","op":"ADD","op":"XOR","src":[],"dst":"r0"}')


def test_parser_enforces_input_size():
    with pytest.raises(ContractError):
        parse_action(" " * 70000)
