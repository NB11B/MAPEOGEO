from experiments.mapeogeo_llm.contracts import Action, Ref, Task, TypedValue
from experiments.mapeogeo_llm.executor import Engine


def test_register_overwrite_is_allowed_but_invalidates_prior_verification():
    task = Task("overwrite", {"a": TypedValue("uint8", 1), "b": TypedValue("uint8", 2)},
                {"kind": "target", "value": 3})
    engine = Engine(task)
    engine.step(Action("ADD", (Ref("input", "a"), Ref("input", "b")), "r0"))
    engine.step(Action("VERIFY", (Ref("reg", "r0"),)))
    assert engine.result()["status"] == "VERIFIED"
    engine.step(Action("XOR", (Ref("input", "a"), Ref("input", "b")), "r0"))
    failed = engine.step(Action("HALT"))
    assert not failed.success and failed.error["code"] == "STALE_VERIFICATION"


def test_trace_and_state_digests_replay_deterministically():
    task = Task("replay", {"a": TypedValue("uint8", 4), "b": TypedValue("uint8", 5)},
                {"kind": "target", "value": 9})
    actions = [Action("ADD", (Ref("input", "a"), Ref("input", "b")), "r0"),
               Action("VERIFY", (Ref("reg", "r0"),)), Action("HALT")]
    engines = [Engine(task), Engine(Task.from_dict(task.to_dict()))]
    for engine in engines:
        for action in actions:
            engine.step(Action.from_dict(action.to_dict()))
    assert engines[0].result()["state_digest"] == engines[1].result()["state_digest"]
    assert engines[0].result()["trace_digest"] == engines[1].result()["trace_digest"]
