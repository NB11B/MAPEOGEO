from experiments.pct_goal_solver.v2_campaign import V2_MODE_NAMES, run_v2_campaign


def test_v2_campaign_scores_frozen_six_modes_without_burying_family_results():
    report = run_v2_campaign()
    assert report["experiment_id"] == "PCT_GOAL_SOLVER_V2_COMPOSITION_STRESS"
    assert report["protocol"] == "V2_CALIBRATION_VALIDATION_FREEZE_THEN_SEALED_NO_RETUNING"
    assert set(report["modes"]) == set(V2_MODE_NAMES)
    assert report["corpus_counts"] == {
        "CALIBRATION_V2": 36,
        "VALIDATION_V2": 12,
        "SEALED_V2": 24,
    }
    for mode in report["modes"].values():
        assert len(mode["cases"]) == 24
        assert {case["family"] for case in mode["cases"]} == {f"G{i}" for i in range(1, 13)}
        assert "wrong_positive_count" in mode
        assert "by_family" in mode


def test_v2_campaign_reports_each_scientific_conclusion_separately():
    report = run_v2_campaign()
    assert set(report["conclusions"]) == {
        "COMPOSITION_DEPTH",
        "CROSS_REPRESENTATION_COMPOSITION",
        "TYPE_BLIND_ROUTING",
        "MACRO_PRESERVATION",
    }
    assert set(report["gates"]) == {
        "explicit_zero_wrong_positives",
        "explicit_ten_multistep_families",
        "three_cross_class_families",
        "g6_g8_g9_cross_class",
        "all_positive_results_independently_verified",
        "inferred_all_12_families_type_blind",
        "inferred_zero_control_wrong_positives",
        "hybrid_preserves_controls_and_family_coverage",
        "macro_preserves_correct_primitive_semantics",
        "macro_reduces_search_on_correct_cases",
    }


def test_v2_macro_credit_never_comes_from_an_incorrect_primitive_baseline():
    report = run_v2_campaign()
    for row in report["macro_comparison"]["credited_reductions"]:
        assert row["primitive_correct"] is True
        assert row["synthesized_correct"] is True
        assert row["same_semantics"] is True
        assert row["reduced_work"] is True
        assert row["macro_ids"]


def test_v2_inferred_and_hybrid_cases_are_marked_type_blind():
    report = run_v2_campaign()
    for mode_name, mode in report["modes"].items():
        expected = not mode_name.startswith("EXPLICIT/")
        assert all(case["input_semantic_types_blinded"] is expected for case in mode["cases"])
