import shutil
import pytest
from experiments.mapeogeo_llm.contracts import Action, Ref, Task, TypedValue
from experiments.mapeogeo_llm.executor import Engine
from experiments.mapeogeo_llm.lean_adapter import LeanAdapter


@pytest.mark.parametrize("expr", [
    "__import__('os').system('echo bad')", "a.__class__", "(lambda: 1)()", "a / 0", "a ** 1000",
])
def test_unsafe_or_invalid_goal_expression_fails_closed(expr):
    engine = Engine(Task("unsafe", {"a": TypedValue("uint8", 1)},
                         {"kind": "expression", "expression": expr}))
    engine.step(Action("ADD", (Ref("input", "a"), Ref("literal", value=0)), "r0"))
    obs = engine.step(Action("VERIFY", (Ref("reg", "r0"),)))
    assert not obs.success and obs.status == "INVALID_INPUT"


def test_unsupported_goal_fails_closed():
    engine = Engine(Task("unsupported", {}, {"kind": "magic"}))
    obs = engine.step(Action("VERIFY", (Ref("literal", value=1),)))
    assert not obs.success and obs.status == "INVALID_INPUT"


def test_assert_creates_open_obligation_but_not_proof():
    engine = Engine(Task("assert", {}, {"kind": "target", "value": 1}))
    obs = engine.step(Action("ASSERT", kwargs={"proposition": "1 = 1"}))
    assert obs.success and obs.obligations[0].status == "OPEN"
    assert engine.result()["status"] == "UNSOLVED"


class CandidateGraph:
    def query(self, node_id, relation=None, max_results=32):
        return {"node": node_id, "edges": [], "status": "certified"}


def test_graph_metadata_cannot_be_promoted_to_verification():
    task = Task("graph", {}, {"kind": "graph", "node_id": "n1"})
    engine = Engine(task, graph=CandidateGraph())
    engine.step(Action("GRAPH_QUERY", (Ref("node", "n1"),), "r0"))
    obs = engine.step(Action("VERIFY", (Ref("reg", "r0"),)))
    assert not obs.success and obs.status == "INVALID_INPUT"


def test_canonical_nested_function_expression_is_independently_evaluated():
    task = Task("nested", {"a": TypedValue("uint8", 250), "b": TypedValue("uint8", 10),
                           "c": TypedValue("uint8", 7)},
                {"kind": "expression", "expression": "XOR(ADD(a,b),c)"})
    engine = Engine(task)
    engine.step(Action("ADD", (Ref("input", "a"), Ref("input", "b")), "r0"))
    engine.step(Action("XOR", (Ref("reg", "r0"), Ref("input", "c")), "r1"))
    obs = engine.step(Action("VERIFY", (Ref("reg", "r1"),)))
    assert obs.success and obs.status == "VERIFIED"


def test_target_comparison_requires_matching_type_not_python_bool_equality():
    engine = Engine(Task("typed", {}, {"kind": "target", "value": 1}))
    obs = engine.step(Action("VERIFY", (Ref("literal", value=True),)))
    assert obs.verification.status == "REFUTED"
    assert obs.verification.evidence["scope"] == "candidate_vs_goal"


class RejectingLean:
    def verify(self, proposition, proof, timeout_seconds=10):
        return {"status": "INVALID_INPUT",
                "evidence": {"kernel_checked": False, "axioms": None, "error": "kernel rejected"}}


def test_lean_rejection_does_not_claim_proposition_refuted():
    task = Task("lean", {}, {"kind": "lean", "proposition": "1 = 2"})
    obs = Engine(task, lean=RejectingLean()).step(
        Action("VERIFY", (Ref("literal", value="certificate"),), kwargs={"proof": "by decide"}))
    assert obs.success and obs.status == "UNSOLVED"
    assert obs.verification.status == "UNSOLVED"


@pytest.mark.parametrize("result", [
    {"status": "VERIFIED", "evidence": {"kernel_checked": False, "axioms": []}},
    {"status": "VERIFIED", "evidence": {"kernel_checked": True, "axioms": ["Classical.choice"]}},
    {"status": "VERIFIED", "evidence": {}},
])
def test_lean_status_alone_or_bad_nested_evidence_never_verifies(result):
    class FakeLean:
        def verify(self, proposition, proof, timeout_seconds=10):
            return result

    task = Task("lean", {}, {"kind": "lean", "proposition": "2 = 2"})
    obs = Engine(task, lean=FakeLean()).step(
        Action("VERIFY", (Ref("literal", value="certificate"),), kwargs={"proof": "by decide"}))
    assert obs.verification is None or obs.verification.status != "VERIFIED"


@pytest.mark.parametrize(("proposition", "proof", "timeout", "expected"), [
    ("2 + 2 = 4", "by decide", 10.0, "VERIFIED"),
    ("2 + 2 = 5", "by decide", 10.0, "UNSOLVED"),
    ("2 + = 4", "by decide", 10.0, "UNSOLVED"),
    ("2 + 2 = 4", "by decide", 1e-9, "UNSOLVED"),
])
def test_engine_with_real_lean_adapter_respects_nested_kernel_evidence(
        proposition, proof, timeout, expected):
    executable = shutil.which("lean")
    if executable is None:
        pytest.fail("Lean is required for runtime integration verification")
    engine = Engine(Task("lean integration", {}, {"kind": "lean", "proposition": proposition}),
                    lean=LeanAdapter(executable))
    obs = engine.step(Action("VERIFY", (Ref("literal", value="certificate"),),
                             kwargs={"proof": proof, "timeout_seconds": timeout}))
    assert obs.success and obs.status == expected
    if expected == "VERIFIED":
        assert obs.verification.evidence["evidence"]["kernel_checked"] is True
        assert obs.verification.to_dict()["evidence"]["evidence"]["axioms"] == []


def test_geo_goal_uses_independent_expression_not_public_expected_answer():
    task = Task("geo", {"e1": TypedValue("float_multivector", [0, 1, 0, 0]),
                         "e2": TypedValue("float_multivector", [0, 0, 1, 0])},
                {"kind": "geo_expression", "op": "gp", "operands": ["e1", "e2"],
                 "signature": [1, 1]})
    engine = Engine(task)
    obs = engine.step(Action("VERIFY", (Ref("literal", value=[0, 0, 0, 1]),)))
    assert obs.success and obs.status == "VERIFIED"
