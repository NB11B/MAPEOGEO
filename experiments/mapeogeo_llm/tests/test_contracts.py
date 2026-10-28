import dataclasses
import json

import pytest

from experiments.mapeogeo_llm.contracts import (
    ACTION_SCHEMA, Action, Budget, ContractError, Episode, Observation,
    ProofObligation, Ref, Task, TypedValue, VerificationResult,
)


def test_contract_round_trip_is_canonical_and_deeply_snapshotted():
    raw = {"nested": [1, {"x": 2}]}
    task = Task("p", {"a": TypedValue("symbolic_expression", raw)}, {"kind": "target", "value": 3})
    raw["nested"][1]["x"] = 99
    restored = Task.from_dict(json.loads(json.dumps(task.to_dict())))
    assert restored == task
    assert task.inputs["a"].to_dict()["value"] == {"nested": [1, {"x": 2}]}
    assert restored.canonical_digest() == task.canonical_digest()
    with pytest.raises(dataclasses.FrozenInstanceError):
        task.problem = "changed"


def test_action_schema_and_digest_are_order_independent():
    left = Action("ADD", (Ref("input", "a"), Ref("literal", value=2)), "r0", {"z": 1, "a": 2})
    right = Action.from_dict({"schema": ACTION_SCHEMA, "op": "ADD", "src": [
        {"kind": "input", "id": "a"}, {"kind": "literal", "value": 2}],
        "dst": "r0", "kwargs": {"a": 2, "z": 1}, "reason_code": None})
    assert left.to_dict() == right.to_dict()
    assert left.canonical_digest() == right.canonical_digest()


@pytest.mark.parametrize("payload", [
    {"schema": "wrong", "op": "ADD", "src": [], "dst": "r0"},
    {"schema": ACTION_SCHEMA, "op": "ADD", "src": [], "dst": "r0", "extra": 1},
    {"schema": ACTION_SCHEMA, "op": 3, "src": [], "dst": "r0"},
])
def test_action_rejects_malformed_payloads(payload):
    with pytest.raises(ContractError):
        Action.from_dict(payload)


@pytest.mark.parametrize("kwargs", [
    {"max_steps": 0}, {"max_registers": 0}, {"wall_time_seconds": float("nan")},
])
def test_budget_rejects_invalid_limits(kwargs):
    with pytest.raises(ContractError):
        Budget(**kwargs)


def test_non_finite_values_fail_closed():
    with pytest.raises(ContractError):
        TypedValue("float_multivector", [float("nan")])


@pytest.mark.parametrize("kind,value", [("uint8", 256), ("uint8", True),
                                          ("boolean", 1), ("unknown", 1)])
def test_typed_values_reject_wrong_kind_or_shape(kind, value):
    with pytest.raises(ContractError):
        TypedValue(kind, value)


def test_episode_and_nested_observation_round_trip():
    task = Task("p", {}, {"kind": "target", "value": 1})
    digest = "a" * 64
    verification = VerificationResult("VERIFIED", TypedValue("uint8", 1), digest, {"checker": "x"})
    observation = Observation(True, "VERIFIED", Action("VERIFY", (Ref("literal", value=1),)),
                              TypedValue("uint8", 1), obligations=(ProofObligation("1=1"),),
                              verification=verification, state_digest=digest)
    episode = Episode(task, (observation,))
    assert Episode.from_dict(json.loads(json.dumps(episode.to_dict()))) == episode


@pytest.mark.parametrize("goal", [
    {"kind": "target", "value": 1, "allowed_ops": ["BOGUS"], "max_ops": 1},
    {"kind": "target", "value": 1, "allowed_ops": ["ADD", "ADD"], "max_ops": 1},
    {"kind": "target", "value": 1, "allowed_ops": ["ADD"], "max_ops": 0},
    {"kind": "target", "value": 1, "allowed_ops": ["ADD"]},
])
def test_target_goal_rejects_invalid_operator_constraints(goal):
    with pytest.raises(ContractError):
        Task("bad", {}, goal)


def test_task_enforces_public_lexical_token_budget():
    with pytest.raises(ContractError):
        Task("one two three", {}, {"kind": "target", "value": 1},
             Budget(max_token_count=2))


@pytest.mark.parametrize("payload", [
    {"proposition": 1, "status": "OPEN", "evidence": {}},
    {"proposition": "p", "status": "BOGUS", "evidence": {}},
])
def test_proof_obligation_replay_rejects_wrong_types(payload):
    with pytest.raises(ContractError):
        ProofObligation.from_dict(payload)


def test_nested_replay_rejects_wrong_booleans_digests_and_nested_types():
    digest = "0" * 64
    with pytest.raises(ContractError):
        VerificationResult.from_dict({"status": "VERIFIED", "output": None,
                                      "state_digest": "not-a-digest", "evidence": {}})
    with pytest.raises(ContractError):
        Observation.from_dict({"success": "yes", "status": "VERIFIED", "state_digest": digest})
    with pytest.raises(ContractError):
        Observation.from_dict({"success": True, "status": "VERIFIED", "state_digest": digest,
                               "obligations": {}})
    with pytest.raises(ContractError):
        Episode.from_dict({"task": Task("p", {}, {"kind": "target", "value": 1}).to_dict(),
                           "trace": ["not-an-observation"]})
