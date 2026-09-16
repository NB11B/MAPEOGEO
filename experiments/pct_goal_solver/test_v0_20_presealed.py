from __future__ import annotations

from dataclasses import replace

from experiments.pct_goal_solver.v0_20_goals import (
    ALL_V0_20_FAMILIES,
    CONTROL_SPLIT,
    CORE_SPLITS,
    CROSS_CLASS_FAMILIES,
    NEW_V0_20_FAMILIES,
    REQUIRED_CONTROL_KINDS,
    V0_20_EXPECTED_COUNTS,
    V0_20_TERMINAL_CONTROL_COUNT,
    build_case_oracle,
    build_v0_20_corpus,
    build_v0_20_terminal_controls,
    case_content_fingerprint,
    case_signatures,
    control_kind_for_goal,
    prove_no_same_class_shortcut,
)
from experiments.pct_goal_solver.v0_20_operators import build_v0_20_operator_registry


def test_v0_20_corpus_has_frozen_positive_counts() -> None:
    corpus = build_v0_20_corpus()
    assert tuple(corpus) == CORE_SPLITS
    assert len(ALL_V0_20_FAMILIES) == 19
    assert len(NEW_V0_20_FAMILIES) == 7
    assert {split: len(goals) for split, goals in corpus.items()} == V0_20_EXPECTED_COUNTS
    for split in CORE_SPLITS:
        assert {goal.family for goal in corpus[split]} == set(ALL_V0_20_FAMILIES)
    assert CONTROL_SPLIT not in corpus


def test_problem_content_is_disjoint_across_every_partition() -> None:
    corpus = build_v0_20_corpus()
    fingerprints = [
        case_content_fingerprint(goal)
        for split in corpus.values()
        for goal in split
    ]
    assert all(len(fingerprint) == 64 for fingerprint in fingerprints)
    assert len(fingerprints) == len(set(fingerprints))


def test_content_fingerprint_does_not_treat_identifiers_as_problem_content() -> None:
    goal = build_v0_20_corpus()["SEALED_V0_20"][0]
    renamed = replace(
        goal,
        goal_id="renamed-goal",
        inputs={
            key: replace(artifact, artifact_id=f"renamed:{key}")
            for key, artifact in goal.inputs.items()
        },
        target=replace(goal.target, target_id="renamed-target"),
    )
    assert case_content_fingerprint(renamed) == case_content_fingerprint(goal)


def test_content_fingerprint_binds_search_and_lineage_protocol() -> None:
    goals = [goal for rows in build_v0_20_corpus().values() for goal in rows]
    goal = next(goal for goal in goals if goal.lineage_obligation is not None)
    baseline = case_content_fingerprint(goal)
    assert case_content_fingerprint(replace(goal, search_budget=goal.search_budget + 1)) != baseline
    assert case_content_fingerprint(replace(goal, lineage_obligation=None)) != baseline


def test_terminal_controls_are_intentional_not_a_vacuous_family_cross_product() -> None:
    controls = build_v0_20_terminal_controls()
    assert len(controls) == V0_20_TERMINAL_CONTROL_COUNT == 22
    by_kind = {
        kind: [control for control in controls if control_kind_for_goal(control) == kind]
        for kind in REQUIRED_CONTROL_KINDS
    }
    assert {kind: len(rows) for kind, rows in by_kind.items()} == {
        "DOMAIN_REFUSAL": 7,
        "VALID_NEGATIVE_RESULT": 5,
        "INVALID_TERMINAL_CERTIFICATE": 7,
        "EXTERNAL_VALID_CERTIFICATE": 3,
    }
    assert {control.family for control in by_kind["DOMAIN_REFUSAL"]} == set(NEW_V0_20_FAMILIES)
    assert {control.family for control in by_kind["EXTERNAL_VALID_CERTIFICATE"]} == {"F2", "F3", "X1"}
    assert all("corrupted_candidate" not in control.goal.inputs for control in controls)


def test_oracles_are_external_to_solver_visible_contracts() -> None:
    corpus = build_v0_20_corpus()
    for split in corpus.values():
        for goal in split:
            oracle = build_case_oracle(goal)
            visible = goal.solver_visible()
            assert oracle["goal_id"] == goal.goal_id
            assert oracle["content_fingerprint"] == case_content_fingerprint(goal)
            assert "expected" not in visible.__dict__
            assert "oracle" not in dict(visible.constraints)
            assert "control_kind" not in dict(visible.constraints)


def test_new_family_oracles_recompute_sources_instead_of_trusting_answer_labels() -> None:
    corpus = build_v0_20_corpus()
    new_goals = [
        goal
        for goal in corpus["SEALED_V0_20"]
        if goal.family in NEW_V0_20_FAMILIES and goal.family != "X2"
    ]
    for goal in new_goals:
        original = build_case_oracle(goal)
        poisoned = build_case_oracle(replace(goal, sealed_expected_result={"forged": True}))
        assert poisoned == original
        assert original["authoritative"] is True
        assert original["oracle_method"].startswith("EXACT_")


def test_x2_positive_cases_do_not_claim_an_independent_oracle() -> None:
    x2_goals = [goal for goal in build_v0_20_corpus()["SEALED_V0_20"] if goal.family == "X2"]
    assert len(x2_goals) == 2
    for goal in x2_goals:
        oracle = build_case_oracle(goal)
        assert oracle["authoritative"] is False
        assert oracle["oracle_availability"] == "UNAVAILABLE"
        assert oracle["reason"] == "NO_INDEPENDENT_X2_ORACLE"


def test_exact_signature_never_hides_known_nuisance_equivalence() -> None:
    g2_goals = [goal for split in build_v0_20_corpus().values() for goal in split if goal.family == "G2"]
    signatures = [case_signatures(goal) for goal in g2_goals]
    assert len({signature.exact_sha256 for signature in signatures}) == len(signatures)
    assert all(signature.nuisance_relation == "G2_NONZERO_RATIONAL_SCALAR" for signature in signatures)


def test_shortcut_adapter_never_invents_a_proof() -> None:
    corpus = build_v0_20_corpus()
    registry = build_v0_20_operator_registry()
    cross_class = [
        goal
        for goal in corpus["SEALED_V0_20"]
        if goal.family in CROSS_CLASS_FAMILIES
    ]
    assert len(cross_class) == 4
    for goal in cross_class:
        proof = prove_no_same_class_shortcut(goal, registry)
        assert proof["status"] in {"PROVED", "REFUTED", "UNREACHABLE", "UNAVAILABLE", "ERROR"}
        assert proof["proven_no_shortcut"] is (proof["status"] == "PROVED")
        if proof["proven_no_shortcut"]:
            assert len(proof["proof_digest"]) == 64
            assert proof["witness"]


def test_v0_20_operator_registry_surface_remains_available() -> None:
    registry = build_v0_20_operator_registry()
    required_ops = {
        "CERTIFY_SQRT2_CUT",
        "CERTIFY_QUADRATIC_MEAN_VALUE",
        "CERTIFY_BEZOUT",
        "CERTIFY_CAUCHY_RIEMANN",
        "CERTIFY_RATIONAL_RESIDUE",
        "EXACT_TO_SYMBOLIC_POLYNOMIAL",
        "SYMBOLIC_TO_NUMERICAL_EVALUATION",
        "CERTIFY_GRID_EVALUATION",
        "EXACT_INVARIANTS_TO_SYMBOLIC_CURVE",
        "CERTIFY_RECTANGULAR_PERIODS",
    }
    assert required_ops <= set(registry)
