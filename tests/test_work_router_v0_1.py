from mapeogeo.work_router import (
    Outcome,
    RouteEdge,
    WorkRequest,
    WorkRouter,
    qualified_v01_edges,
)


def router():
    return WorkRouter(qualified_v01_edges())


def test_uncertified_shortcut_never_beats_certified_route():
    decision = router().decide(
        WorkRequest("work.area_expanding"),
        available={"psmsl.directional_scales"},
    )
    assert decision.outcome == Outcome.EXECUTE
    assert decision.route is not None
    assert [e.edge_id for e in decision.route.edges] == [
        "wr.area.sum",
        "wr.area.sign",
    ]
    assert decision.route.cost == 2.0
    assert decision.route.certified


def test_discovery_route_returns_certify_when_no_certified_route_exists():
    r = WorkRouter(
        [RouteEdge("candidate", "a", "target", 0.1, False, "candidate")]
    )
    decision = r.decide(WorkRequest("target"), available={"a"})
    assert decision.outcome == Outcome.CERTIFY
    assert decision.route is not None
    assert not decision.route.certified


def test_missing_required_information_returns_observe():
    decision = router().decide(
        WorkRequest("work.amplitude_above_threshold"),
        available={"psmsl.scale_n"},
    )
    assert decision.outcome == Outcome.OBSERVE
    assert decision.missing == ("work.amplitude_threshold_n",)


def test_available_threshold_executes_minimal_route():
    decision = router().decide(
        WorkRequest("work.amplitude_above_threshold"),
        available={"psmsl.scale_n", "work.amplitude_threshold_n"},
    )
    assert decision.outcome == Outcome.EXECUTE
    assert decision.route is not None
    assert [e.edge_id for e in decision.route.edges] == ["wr.amplitude.threshold"]


def test_class_invariant_answers_orientation_without_numeric_state():
    decision = router().decide(
        WorkRequest("work.orientation_preserving"),
        available={"psmsl.positive_scale_proper_rotation"},
    )
    assert decision.outcome == Outcome.EXECUTE
    assert decision.route is not None
    assert decision.route.cost == 0.1


def test_known_answer_does_not_recompute():
    decision = router().decide(
        WorkRequest("work.stable"),
        available=set(),
        known_answers={"work.stable"},
    )
    assert decision.outcome == Outcome.ANSWER
    assert decision.route is not None
    assert decision.route.cost == 0.0


def test_materialization_is_distinct_from_observation():
    decision = router().decide(
        WorkRequest("work.area_expanding", require_materialized=True),
        available={"psmsl.directional_scales"},
    )
    assert decision.outcome == Outcome.MATERIALIZE
    assert decision.route is not None
    assert decision.route.certified


def test_no_route_is_unresolvable():
    decision = router().decide(WorkRequest("work.unknown_target"), available={"psmsl.scale_n"})
    assert decision.outcome == Outcome.UNRESOLVABLE


def test_route_certificate_rejects_unresolved_decision():
    decision = router().decide(
        WorkRequest("work.amplitude_above_threshold"),
        available={"psmsl.scale_n"},
    )
    try:
        router().certificate(decision, input_nodes={"psmsl.scale_n"})
    except ValueError:
        pass
    else:
        raise AssertionError("OBSERVE decision must not emit execution certificate")


def test_route_certificate_binds_exact_edge_ids_and_cost():
    r = router()
    decision = r.decide(
        WorkRequest("work.area_expanding"),
        available={"psmsl.directional_scales"},
    )
    cert = r.certificate(decision, input_nodes={"psmsl.directional_scales"})
    assert cert.certified
    assert cert.route_edge_ids == ("wr.area.sum", "wr.area.sign")
    assert cert.total_cost == 2.0
    assert cert.output_node == "work.area_expanding"


def test_negative_cost_fails_closed():
    try:
        RouteEdge("bad", "a", "b", -1.0, True, "bad")
    except ValueError:
        pass
    else:
        raise AssertionError("negative cost must be rejected")
