from experiments.pct_goal_solver.goals import build_goal_corpus


def test_sealed_answers_are_not_solver_visible():
    corpus = build_goal_corpus()
    goal = corpus["SEALED"][0]
    visible = goal.solver_visible()
    assert not hasattr(visible, "sealed_expected_result")
    assert not hasattr(visible, "sealed_reference_path")
    assert goal.sealed_expected_result is not None
    assert goal.sealed_reference_path


def test_corpus_covers_all_goal_families_and_exactness_classes():
    corpus = build_goal_corpus()
    families = {g.family for split in corpus.values() for g in split}
    assert families == {f"G{i}" for i in range(1, 13)}
    classes = {
        artifact.exactness_class
        for split in corpus.values()
        for goal in split
        for artifact in goal.inputs.values()
    }
    assert {"EXACT", "SYMBOLIC", "NUMERICAL"} <= classes


def test_split_sizes_are_frozen_per_family():
    corpus = build_goal_corpus()
    for family in {f"G{i}" for i in range(1, 13)}:
        assert sum(g.family == family for g in corpus["CALIBRATION"]) >= 3
        assert sum(g.family == family for g in corpus["VALIDATION"]) >= 1
        assert sum(g.family == family for g in corpus["SEALED"]) >= 2


def test_goal_ids_are_unique_and_deterministic():
    first = build_goal_corpus()
    second = build_goal_corpus()
    first_ids = [g.goal_id for split in ("CALIBRATION", "VALIDATION", "SEALED") for g in first[split]]
    second_ids = [g.goal_id for split in ("CALIBRATION", "VALIDATION", "SEALED") for g in second[split]]
    assert first_ids == second_ids
    assert len(first_ids) == len(set(first_ids))
