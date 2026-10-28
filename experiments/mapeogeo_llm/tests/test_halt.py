from experiments.mapeogeo_llm.contracts import Action, Budget, Ref, Task, TypedValue
from experiments.mapeogeo_llm.executor import Engine


def make_engine(budget=Budget()):
    return Engine(Task("halt", {"a": TypedValue("uint8", 1)}, {"kind": "target", "value": 1}, budget))


def test_early_halt_fails_without_mutation():
    engine = make_engine()
    before = engine.observation()
    obs = engine.step(Action("HALT"))
    assert not obs.success and obs.error["code"] == "EARLY_HALT"
    assert engine.observation() == before


def test_explicit_unsolved_halt_is_valid_and_distinct():
    engine = make_engine()
    obs = engine.step(Action("HALT", kwargs={"status": "UNSOLVED"}))
    assert obs.success and obs.status == "UNSOLVED"
    assert engine.result()["status"] == "UNSOLVED"


def test_budget_exhaustion_is_not_successful_halt():
    engine = make_engine(Budget(max_steps=1))
    engine.step(Action("ASSERT", kwargs={"proposition": "open"}))
    before = engine.observation()
    obs = engine.step(Action("HALT", kwargs={"status": "UNSOLVED"}))
    assert not obs.success and obs.status == "BUDGET_EXHAUSTED"
    assert engine.observation() == before


def test_open_assertion_prevents_verified_halt():
    engine = make_engine()
    engine.step(Action("ASSERT", kwargs={"proposition": "open"}))
    engine.step(Action("VERIFY", (Ref("input", "a"),)))
    assert engine.result()["status"] == "UNSOLVED"
    obs = engine.step(Action("HALT"))
    assert not obs.success and obs.error["code"] == "OPEN_OBLIGATIONS"
