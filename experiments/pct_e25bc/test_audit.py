from experiments.pct_e25bc.audit import (
    load_trust_projection,
    run_e25b,
    run_e25c,
    run_synthetic_layer_attacks,
)


def test_e25b_projection_is_bound_to_original_v09_artifact():
    p = load_trust_projection()
    src = p["source_artifact"]
    assert src["commit_sha"] == "9420f19953f56198630f86eb25fa5d6eb0828ea7"
    assert src["artifact_id"] == 10382242654
    assert src["artifact_digest"] == "sha256:d487602dd3c0b3a3c5302edde108758eda2b11975f5e0c2c4e659db63da2aabc"


def test_e25b_enumerates_every_multipath_pair_in_trust_projection():
    r = run_e25b()
    assert r["status"] == "PASS"
    assert r["trust_components"] == 24
    assert r["component_size_histogram"] == {"3": 20, "4": 4}
    assert r["independent_cycle_rank"] == 32
    assert r["endpoint_pairs"] == 84
    assert r["multipath_endpoint_pairs"] == 84
    assert r["single_path_endpoint_pairs"] == 0
    assert r["distinct_path_pair_comparisons"] == 300
    assert r["bridges"] == 0
    assert r["max_simple_paths_between_one_endpoint_pair"] == 5
    assert r["identity_path_conflicts"] == 0
    assert r["certificate_path_conflicts"] == 0


def test_e25b_refines_the_equivalence_only_cycle_count():
    r = run_e25b()
    assert r["equivalence_only_cycles"] == 4
    assert r["trust_projection_cyclic_components"] == 24
    assert r["anchor_representation_pairs"] == 52
    assert r["anchor_representation_pairs_with_alternate_path"] == 52


def test_e25c_executes_all_four_real_source_bound_cycles():
    r = run_e25c()
    assert r["status"] == "PASS"
    assert r["cycle_count"] == 4
    assert r["total_exact_inputs"] == 3419
    assert r["total_pairwise_path_equalities"] == 10257
    assert all(x["all_paths_agree"] for x in r["cycles"])
    checks = {x["contract"]: x["exact_inputs"] for x in r["cycles"]}
    assert checks == {"rank": 682, "convex": 279, "lp": 2457, "gauss": 1}


def test_e25c_preserves_actual_formal_scopes():
    r = run_e25c()
    scopes = {x["contract"]: x["formal_scope"] for x in r["cycles"]}
    assert scopes == {
        "rank": "GENERAL_FINITE_DIMENSIONAL_DIVISION_RING",
        "convex": "TWO_POINT_REAL_CONVEX_COMBINATION",
        "lp": "POSITIVE_ONE_DIMENSIONAL_LINEAR_PROGRAM",
        "gauss": "SCALAR_REAL_GAUSSIAN_EXPONENT_IDENTITY",
    }


def test_layered_synthetic_attacks_are_caught_at_the_first_capable_layer():
    r = run_synthetic_layer_attacks()
    assert r["anchor_swap"] == {"C0_identity": "FAIL", "C1_certificate": "NOT_REACHED", "C2_executable": "NOT_REACHED"}
    assert r["certificate_flip"] == {"C0_identity": "PASS", "C1_certificate": "FAIL", "C2_executable": "NOT_REACHED"}
    assert r["executable_mutation"] == {"C0_identity": "PASS", "C1_certificate": "PASS", "C2_executable": "FAIL"}


def test_e25b_e25c_do_not_overclaim_chain_or_homology_levels():
    b = run_e25b()
    c = run_e25c()
    assert b["maximum_persisted_closure_level"] == "C1_CERTIFICATE"
    assert c["maximum_executed_closure_level"] == "C2_EXECUTABLE_CONTRACT"
    assert c["C3_chain_map"] == "NOT_APPLICABLE_TO_THESE_FOUR_CONTRACTS"
    assert c["C4_induced_homology"] == "NOT_APPLICABLE_TO_THESE_FOUR_CONTRACTS"
    assert c["C5_exact_morphism_provenance"] == "NOT_ESTABLISHED"


def test_frozen_e25b_e25c_evidence_matches_fresh_execution():
    from pathlib import Path
    import json
    root = Path(__file__).resolve().parents[2]
    frozen_b = json.loads((root / "evidence" / "pct_e25b_multipath_audit.json").read_text(encoding="utf-8"))
    frozen_c = json.loads((root / "evidence" / "pct_e25c_executable_cycle_audit.json").read_text(encoding="utf-8"))
    assert frozen_b == run_e25b()
    assert frozen_c == run_e25c()
