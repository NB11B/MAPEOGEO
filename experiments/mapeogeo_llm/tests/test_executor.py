import json
import random

from experiments.mapeogeo_llm.contracts import Action, Budget, Ref, Task, TypedValue
from experiments.mapeogeo_llm.datasets.oracle import integer_operator
from experiments.mapeogeo_llm.executor import Engine


def ref(kind, ident=None, value=None):
    return Ref(kind, ident, value)


def task(goal=None, budget=None):
    return Task("test", {"a": TypedValue("uint8", 250), "b": TypedValue("uint8", 10),
                         "c": TypedValue("uint8", 7)},
                goal or {"kind": "expression", "expression": "((a + b) & 255) ^ c"},
                budget or Budget())


def test_dag_reuse_overflow_and_independent_verification():
    engine = Engine(task())
    assert engine.step(Action("ADD", (ref("input", "a"), ref("input", "b")), "r0")).output.value == 4
    assert engine.step(Action("XOR", (ref("reg", "r0"), ref("input", "c")), "r1")).output.value == 3
    assert engine.step(Action("AND", (ref("reg", "r0"), ref("reg", "r1")), "r2")).output.value == 0
    assert engine.step(Action("VERIFY", (ref("reg", "r1"),))).verification.status == "VERIFIED"
    assert engine.step(Action("HALT")).status == "VERIFIED"
    assert engine.result()["output"] == {"kind": "uint8", "value": 3}


def test_wrong_chosen_action_cannot_verify_itself():
    engine = Engine(task())
    engine.step(Action("AND", (ref("input", "a"), ref("input", "b")), "r0"))
    obs = engine.step(Action("VERIFY", (ref("reg", "r0"),)))
    assert obs.verification.status == "REFUTED"
    assert engine.step(Action("HALT")).status == "REFUTED"


def test_failed_action_is_fully_immutable():
    engine = Engine(task())
    before = engine.observation()
    failed = engine.step(Action("ADD", (ref("reg", "missing"), ref("input", "b")), "r0"))
    assert not failed.success and failed.status == "INVALID_INPUT"
    assert engine.observation() == before


def test_invalid_type_and_register_bounds_fail_closed():
    bad = Task("bad", {"a": TypedValue("integer", 3), "b": TypedValue("uint8", 2)},
               {"kind": "target", "value": 5}, Budget(max_registers=1))
    engine = Engine(bad)
    assert not engine.step(Action("ADD", (ref("input", "a"), ref("input", "b")), "r0")).success
    assert not engine.step(Action("ADD", (ref("literal", value=1), ref("literal", value=2)), "r1")).success


def test_deterministic_random_state_machine_matches_plain_oracle():
    rng = random.Random(1701)
    for _ in range(40):
        inputs = {k: TypedValue("uint8", rng.randrange(256)) for k in ("a", "b", "c")}
        eng = Engine(Task("fuzz", inputs, {"kind": "target", "value": 0}, Budget(max_steps=40)))
        plain = {k: v.value for k, v in inputs.items()}
        names = list(plain)
        for i in range(20):
            op = rng.choice(["ADD", "SUB", "XOR", "AND", "OR", "EQ"])
            x, y = rng.choice(names), rng.choice(names)
            dst = f"r{i}"
            got = eng.step(Action(op, (ref("input" if x in inputs else "reg", x),
                                        ref("input" if y in inputs else "reg", y)), dst))
            plain[dst] = integer_operator(op, plain[x], plain[y])
            names.append(dst)
            assert got.success and got.output.value == plain[dst]


def test_success_observation_digest_is_current_and_irrelevant_kwargs_rejected():
    engine = Engine(task())
    obs = engine.step(Action("ADD", (ref("input", "a"), ref("input", "b")), "r0"))
    assert obs.state_digest == engine.observation()["state_digest"]
    before = engine.observation()
    failed = engine.step(Action("XOR", (ref("input", "a"), ref("input", "b")), "r1",
                                {"unexpected": True}))
    assert not failed.success and engine.observation() == before


def test_post_timeout_action_cannot_mutate_state(monkeypatch):
    clock = iter([10.0, 12.0])
    monkeypatch.setattr("experiments.mapeogeo_llm.executor.time.monotonic", lambda: next(clock))
    engine = Engine(task(budget=Budget(wall_time_seconds=1.0)))
    before = engine.observation()
    obs = engine.step(Action("ADD", (ref("input", "a"), ref("input", "b")), "r0"))
    assert not obs.success and obs.status == "BUDGET_EXHAUSTED"
    assert engine.observation() == before


def test_tool_returning_after_deadline_cannot_commit(monkeypatch):
    clock = iter([10.0, 10.5, 12.0])
    monkeypatch.setattr("experiments.mapeogeo_llm.executor.time.monotonic", lambda: next(clock))

    class SlowGeo:
        def gp(self, a, b, signature):
            return [1.0, 0.0]

        def metadata(self):
            return {"backend": "fake"}

    task_ = Task("late", {"a": TypedValue("float_multivector", [1, 0]),
                           "b": TypedValue("float_multivector", [1, 0])},
                 {"kind": "geo_expression", "op": "gp", "operands": ["a", "b"],
                  "signature": [1]}, Budget(wall_time_seconds=1.0))
    engine = Engine(task_, geo=SlowGeo())
    before = engine.observation()
    obs = engine.step(Action("GEO_GP", (ref("input", "a"), ref("input", "b")),
                             "r0", {"signature": [1]}))
    assert not obs.success and obs.status == "BUDGET_EXHAUSTED"
    assert obs.error["code"] == "WALL_TIME"
    assert engine.observation() == before


def test_target_goal_enforces_allowed_ops_and_program_op_budget():
    goal = {"kind": "target", "value": 3, "allowed_ops": ["ADD"], "max_ops": 1}
    engine = Engine(Task("bounded", {"a": TypedValue("uint8", 1), "b": TypedValue("uint8", 2)}, goal))
    before = engine.observation()
    denied = engine.step(Action("XOR", (ref("input", "a"), ref("input", "b")), "r0"))
    assert not denied.success and denied.error["code"] == "DISALLOWED_OPERATOR"
    assert engine.observation() == before
    assert engine.step(Action("ADD", (ref("input", "a"), ref("input", "b")), "r0")).success
    after_program = engine.observation()
    assert after_program["program_ops_used"] == 1
    assert engine.step(Action("VERIFY", (ref("reg", "r0"),))).success
    assert engine.observation()["program_ops_used"] == 1
    exhausted = engine.step(Action("ADD", (ref("input", "a"), ref("input", "b")), "r1"))
    assert not exhausted.success and exhausted.error["code"] == "OP_BUDGET"


def test_task_specific_action_and_tool_result_size_limits_are_transactional():
    limited = Task("x", {"a": TypedValue("uint8", 1)}, {"kind": "target", "value": 1},
                   Budget(max_input_bytes=300, max_token_count=500))
    engine = Engine(limited)
    before = engine.observation()
    too_large = Action("ASSERT", kwargs={"proposition": "x" * 400}, reason_code="r" * 400)
    assert engine.step(too_large).error["code"] == "ACTION_SIZE"
    assert engine.observation() == before
    padded_json = json.dumps(Action("HALT", kwargs={"status": "UNSOLVED"}).to_dict()) + " " * 400
    assert engine.step(padded_json).error["code"] == "ACTION_SIZE"
    assert engine.observation() == before

    class HugeGraph:
        def query(self, node_id, relation=None, max_results=32):
            return {"node": node_id, "payload": "x" * 1000}

    graph_task = Task("g", {}, {"kind": "graph", "node_id": "n"},
                      Budget(max_input_bytes=300, max_token_count=500))
    graph_engine = Engine(graph_task, graph=HugeGraph())
    graph_before = graph_engine.observation()
    obs = graph_engine.step(Action("GRAPH_QUERY", (ref("node", "n"),), "r0"))
    assert not obs.success and obs.error["code"] == "RESULT_SIZE"
    assert graph_engine.observation() == graph_before
