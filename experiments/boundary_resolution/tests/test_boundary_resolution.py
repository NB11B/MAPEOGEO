"""Unit test suite for B5 Boundary Resolution Experiment."""

import pytest
from pathlib import Path
import json

from experiments.boundary_resolution import ALLOWED_TERMINAL_STATUSES
from experiments.boundary_resolution.boundary_ledger import BoundaryLedger
from experiments.boundary_resolution.deficiency_extractor import extract_deficiency
from experiments.boundary_resolution.deficiency_clustering import cluster_deficiencies
from experiments.boundary_resolution.collision_adjudicator import adjudicate_persistent_collisions
from experiments.boundary_resolution.long_composition_search import search_long_factorization
from experiments.boundary_resolution.candidate_falsifier import falsify_candidate_repair

def test_deficiency_extraction():
    rec = {
        "boundary_id": "B5_0001",
        "domain": "topology",
        "failure_projection": "DUAL_INVERSION_ASYMMETRY",
        "failure_mechanism": "non_abelian_higher_gauge_coherence",
        "m5_signature": {"Delta": "mod", "I": "top", "W": "hom", "sigma": "EQUIV", "Pi": "co"}
    }
    d = extract_deficiency(rec)
    assert d["boundary_id"] == "B5_0001"
    assert d["missing_work"] == "higher_gerbe_gauge_coherence"
    assert d["candidate_resolution_type"] == "ALPHABET_WITNESS"

def test_clustering_and_two_holdout_split():
    items = []
    for i in range(20):
        items.append({
            "boundary_id": f"B5_{i:04d}",
            "missing_work": "work_alpha",
            "candidate_resolution_type": "ALPHABET_WITNESS",
            "domain": "algebra"
        })
    clustered = cluster_deficiencies(items)
    assert len(clustered["clusters"]) == 1
    c = list(clustered["clusters"].values())[0]
    assert c["total_count"] == 20
    assert c["screen_set_A_count"] == 10
    assert c["confirm_set_B_count"] == 10
    # Confirm mutual exclusivity
    assert set(c["screen_ids"]).isdisjoint(set(c["confirm_ids"]))

def test_collision_adjudication_12():
    collisions = [{"boundary_id": f"B5_coll_{i:02d}", "domain": "diffgeom"} for i in range(12)]
    res = adjudicate_persistent_collisions(collisions)
    assert res["total_persistent_collisions"] == 12
    for item in res["adjudications"]:
        assert item["status"] in ALLOWED_TERMINAL_STATUSES

def test_long_composition_search():
    transitions = [
        {"boundary_id": "B5_01", "missing_work": "conormal_sheaf_microlocalization"},
        {"boundary_id": "B5_02", "missing_work": "unknown_other"}
    ]
    table = {"P_RESTRICT": {"P_EMBED": "DEFINED"}}
    res = search_long_factorization(transitions, table)
    assert res["resolved_as_long_composition"] == 1
    assert res["unresolvable_count"] == 1

def test_candidate_falsification_penalty():
    # Survived candidate
    res_clean = falsify_candidate_repair(
        candidate_name="cand_clean",
        delta_h_b5=1.5,
        false_splits=0,
        false_merges=0,
        composition_violations=0,
        lambda_penalty=100.0
    )
    assert res_clean["survived_falsification"]
    assert res_clean["verdict"] == "FALSIFICATION_SURVIVED"

    # Falsified candidate with regressions
    res_regressed = falsify_candidate_repair(
        candidate_name="cand_bad",
        delta_h_b5=1.5,
        false_splits=1,
        false_merges=0,
        composition_violations=0,
        lambda_penalty=100.0
    )
    assert not res_regressed["survived_falsification"]
    assert res_regressed["net_utility"] < 0
    assert res_regressed["verdict"] == "FALSIFIED_BY_REGRESSION"

def test_boundary_ledger_conservation_and_unresolved_check(tmp_path: Path):
    ledger = BoundaryLedger(expected_total=2)
    dummy_b5 = tmp_path / "dummy_b5.jsonl"
    with open(dummy_b5, "w", encoding="utf-8") as f:
        f.write(json.dumps({"boundary_id": "B5_01", "domain": "dom", "failure_projection": "proj", "failure_mechanism": "mech"}) + "\n")
        f.write(json.dumps({"boundary_id": "B5_02", "domain": "dom", "failure_projection": "proj", "failure_mechanism": "mech"}) + "\n")

    ledger.load_b5_boundary(dummy_b5)

    # Violates conservation if unadjudicated
    with pytest.raises(ValueError, match="records remained UNRESOLVED"):
        ledger.verify_conservation()

    # Adjudicate both
    ledger.record_adjudication("B5_01", "RESOLVED_COMPOSITION", "TEST", "details")
    ledger.record_adjudication("B5_02", "RESOLVED_COORDINATE_VALUE", "TEST", "details")

    res = ledger.verify_conservation()
    assert res["conservation_satisfied"]
    assert res["total_records"] == 2

    # Attempt invalid status
    with pytest.raises(ValueError, match="not in ALLOWED_TERMINAL_STATUSES"):
        ledger.record_adjudication("B5_01", "INVALID_STATUS_XYZ", "TEST", "details")
