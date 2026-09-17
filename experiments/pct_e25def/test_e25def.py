from __future__ import annotations

import importlib
import json
from pathlib import Path


def _module(name: str):
    return importlib.import_module(f"experiments.pct_e25def.{name}")


def test_real_manifest_contains_only_real_source_bound_cycles():
    model = _module("model")
    manifest = model.load_real_component_manifest()
    assert manifest["source_artifact"]["artifact_id"] == 10382242654
    assert len(manifest["components"]) == 4
    assert {c["provenance_class"] for c in manifest["components"]} == {"REAL_SOURCE_BOUND"}
    assert {c["contract"] for c in manifest["components"]} == {"rank", "convex", "lp", "gauss"}
    assert model.validate_manifest(manifest) == {"status": "PASS", "components": 4}


def test_manifest_has_unique_ids_hashes_and_evidence_bindings():
    model = _module("model")
    manifest = model.load_real_component_manifest()
    ids = [c["component_id"] for c in manifest["components"]]
    assert len(ids) == len(set(ids)) == 4
    for component in manifest["components"]:
        assert len(component["source_statement_sha256"]) == 64
        assert len(component["certificate_ids"]) == 2
        assert len(component["semantic_edge_ids"]) >= 7


def test_e25d_assigns_complete_fail_closed_vectors():
    atlas = _module("atlas")
    result = atlas.run_e25d()
    assert result["status"] == "PASS"
    assert result["real_components"] == 4
    assert result["synthetic_components_counted_as_real"] == 0
    assert all(set(c["closure"]) == {"C0", "C1", "C2", "C3", "C4", "C5"} for c in result["components"])
    assert {c["closure_frontier"] for c in result["components"]} == {"C2"}
    for component in result["components"]:
        assert component["closure"]["C0"]["state"] == "PASS"
        assert component["closure"]["C1"]["state"] == "PASS"
        assert component["closure"]["C2"]["state"] == "PASS"
        assert component["closure"]["C3"]["state"] == "NOT_APPLICABLE"
        assert component["closure"]["C4"]["state"] == "NOT_APPLICABLE"
        assert component["closure"]["C5"]["state"] == "NOT_ESTABLISHED"
        assert all(component["closure"][level].get("evidence_refs") for level in ("C0", "C1", "C2"))
        assert component["closure"]["C3"].get("reason")
        assert component["closure"]["C4"].get("reason")
        assert component["closure"]["C5"].get("reason")


def test_e25e_places_each_real_component_in_exactly_one_queue_class():
    planner = _module("planner")
    result = planner.run_e25e()
    assert result["status"] == "PASS"
    assert len(result["queue"]) == 4
    assert len({x["component_id"] for x in result["queue"]}) == 4
    assert {x["priority_class"] for x in result["queue"]} == {"P4_EXACT_MORPHISM_PROVENANCE_REQUIRED"}
    assert all(x["expected_next_level"] == "C5" for x in result["queue"])
    assert all(x["semantic_promotion"] is False for x in result["queue"])
    assert result["queue"] == sorted(result["queue"], key=lambda x: (x["priority_rank"], x["component_id"]))


def test_e25f_covers_every_first_capable_layer_without_early_false_positive():
    fault_matrix = _module("fault_matrix")
    result = fault_matrix.run_e25f()
    assert result["status"] == "PASS"
    assert {x["expected_first_detector"] for x in result["faults"]} == {"C0", "C1", "C2", "C3", "C4", "C5"}
    assert {x["provenance_class"] for x in result["faults"]} == {"SYNTHETIC_CONTROL"}
    assert all(x["observed_first_detector"] == x["expected_first_detector"] for x in result["faults"])
    assert all(x["false_positive_before_expected"] is False for x in result["faults"])
    assert all(x["missed_at_expected"] is False for x in result["faults"])


def test_e25f_chain_homology_and_provenance_controls_are_distinct():
    fault_matrix = _module("fault_matrix")
    result = fault_matrix.run_e25f()
    by_id = {x["fault_id"]: x for x in result["faults"]}
    assert by_id["chain_map_entry_flip"]["layer_results"]["C3"] == "FAIL"
    assert by_id["wrong_h1_degree_cycle_injection"]["layer_results"]["C3"] == "PASS"
    assert by_id["wrong_h1_degree_cycle_injection"]["layer_results"]["C4"] == "FAIL"
    assert by_id["same_h1_wrong_exact_map"]["layer_results"]["C4"] == "PASS"
    assert by_id["same_h1_wrong_exact_map"]["layer_results"]["C5"] == "FAIL"


def test_frozen_e25def_evidence_matches_fresh_execution():
    root = Path(__file__).resolve().parents[2]
    atlas = _module("atlas")
    planner = _module("planner")
    fault_matrix = _module("fault_matrix")
    frozen_d = json.loads((root / "evidence" / "pct_e25d_closure_atlas.json").read_text(encoding="utf-8"))
    frozen_e = json.loads((root / "evidence" / "pct_e25e_upgrade_plan.json").read_text(encoding="utf-8"))
    frozen_f = json.loads((root / "evidence" / "pct_e25f_fault_coverage.json").read_text(encoding="utf-8"))
    assert frozen_d == atlas.run_e25d()
    assert frozen_e == planner.run_e25e()
    assert frozen_f == fault_matrix.run_e25f()


def test_report_states_real_coverage_and_synthetic_boundary():
    report = _module("report")
    text = report.build_report()
    assert "4 real source-bound components" in text
    assert "synthetic controls do not count as repository closure" in text.lower()
    assert "C0" in text and "C5" in text
    assert "P4_EXACT_MORPHISM_PROVENANCE_REQUIRED" in text
