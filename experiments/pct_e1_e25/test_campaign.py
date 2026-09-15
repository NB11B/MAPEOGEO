from experiments.pct_e1_e25.campaign import (
    load_frozen_campaign, run_e4, run_e5, run_e6, run_e7, run_e8, run_e9,
    run_e10, run_e11, run_e12, run_e13, run_e14, run_e15, run_e16, run_e17,
    run_e18, run_e19, run_e20, run_e21, run_e22, run_e23, run_e24, validate_e25_evidence,
)


def test_e1_e3_frozen_exact_campaign_evidence():
    c = load_frozen_campaign()
    by = {r["experiment"]: r for r in c["results"]}
    assert "7,625" in by["E1"]["highlight"]
    assert "global minimum of 2 directions" in by["E2"]["highlight"]
    assert "2,4,6,...,16" in by["E3"]["highlight"]


def test_e4_noise_stability():
    r = run_e4()
    assert r["status"] == "PASS"
    assert r["trials"] == 1500


def test_e5_adversarial_chain_maps():
    r = run_e5()
    assert r["single_entry_detected"] == 36
    assert r["cycle_injection_chain_maps_valid"] == 26
    assert r["wrong_induced_degree"] == 20


def test_e6_lefschetz_history():
    r = run_e6()
    assert r["reflection_L"] == 2
    assert r["degree2_L"] == -1


def test_e7_monodromy():
    assert run_e7()["monodromy"] == "transposition"


def test_e8_scale_events():
    r = run_e8()
    assert r["recovered"] == 6
    assert r["tested"] == 6


def test_e9_applicability_boundary():
    r = run_e9()
    assert r["convex_pass"] == 3
    assert r["not_applicable"] == 3


def test_e10_euler_radon_inversion():
    r = run_e10()
    assert r["probe_count"] == 20
    assert r["full_rank"] == 6
    assert r["incomplete_nullity"] >= 1


def test_e11_nullspace_atlas():
    r = run_e11()
    assert r["axis_lines_nullity"] == 9
    assert r["point_probes_nullity"] == 0


def test_e12_nerve_reconstruction():
    r = run_e12()
    assert r["good_cover_b1"] == 1
    assert r["bad_cover_b1"] == 0


def test_e13_mobius_inversion():
    assert run_e13()["exact"] is True


def test_e14_persistence_information_loss():
    r = run_e14()
    assert r["barcode_count"] == 1770
    assert r["euler_collision_pairs"] > r["betti_collision_pairs"] > 0


def test_e15_restricted_yoneda():
    r = run_e15()
    assert [x["minimum_probes"] for x in r] == [1, 2, 3, 4, 5]


def test_e16_cross_view_commutation():
    assert run_e16()["wrong_pairings_rejected"] == 56


def test_e17_exact_vs_float_rank():
    r = run_e17()
    assert r["first_float32_loss"] == 6
    assert r["first_float64_loss"] == 11


def test_e18_cancellation_localization():
    r = run_e18()
    assert r["tested"] == 24
    assert r["detected"] == 24
    assert r["localized"] == 24


def test_e19_support_spectrum():
    r = run_e19()
    assert r["status"] == "PASS"
    assert r["triangle_square_first_common_harmonic"] == 12


def test_e20_mixed_volume_relative_geometry():
    r = run_e20()
    assert r["diagonal_zero"] is True
    assert r["cross_positive"] is True


def test_e21_nilpotent_intrinsic_volume_ladder():
    r = run_e21()
    assert r["G2_nilpotency_index"] == 3
    assert r["G3_nilpotency_index"] == 4
    assert r["invariants_conserved"] is True


def test_e22_conservation_law_discovery():
    r = run_e22()
    assert abs(r["coefficient"] + 4 * r["pi"]) < 1e-10


def test_e23_counterexample_search():
    r = run_e23()
    assert r["counterexamples"] == 4


def test_e24_cross_domain_graph_chain():
    r = run_e24()
    assert r["atlas_objects"] == 1252
    assert r["G0_collision_pairs"] == 74789
    assert r["G4_collision_pairs"] == 0
    assert r["subdivision_chain_map_commutes"] is True


def test_e25_frozen_remote_graph_audit_evidence():
    r = validate_e25_evidence()
    assert r["status"] == "PASS"
    assert r["nodes"] == 2250
    assert r["edges"] == 23338
    assert r["equivalence_cycles"] == 4
    assert r["conflicts"] == 0
