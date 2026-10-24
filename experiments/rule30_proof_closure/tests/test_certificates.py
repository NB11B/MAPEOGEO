"""Tests for contradiction certificates, Nullstellensatz ideal normalizer, and Lean 4.35.0 verification."""

from __future__ import annotations

import json
from pathlib import Path

from experiments.rule30_proof_closure.certificates import (
    build_nullstellensatz_certificate,
    build_psmsl_sideways_ideal_and_verify,
    reconstruct_primitive_contradiction_provenance,
    run_adversarial_counterexample_stress_tests,
    run_diagonal_ablation_experiment,
    run_proof_closure_campaign,
    verify_closure_certificates_and_lean_modules,
)
from experiments.rule30_proof_closure.left import (
    analyze_right_coupled_characteristic_flux,
    analyze_spatiotemporal_relation_algebra,
    trace_spatial_relation_transport,
)


def test_proof_closure_campaign_and_obligation_auditor():
    # Fast CI check with write_evidence=False so canonical 180-hypothesis closure_verdict.json is preserved
    report = run_proof_closure_campaign(max_period=3, transients=(0, 1, 2, 3), write_evidence=False)
    assert report.checkpoint_01_reconstruction_completeness is True
    assert report.checkpoint_02_bilateral_soundness is True
    assert report.conditional_closure_claims_automatically_rejected is True
    assert report.surviving_models_count == 0
    assert report.hypotheses_tested == 56
    assert report.hypotheses_unsat_count == 56

    ev_dir = Path(__file__).resolve().parent.parent / "evidence"
    assert (ev_dir / "hypothesis_results.jsonl").exists()
    assert (ev_dir / "counterexamples.jsonl").exists()
    assert (ev_dir / "failed_claims.jsonl").exists()
    assert (ev_dir / "nullstellensatz_certificates.jsonl").exists()
    assert (ev_dir / "closure_verdict.json").exists()

    persisted = json.loads((ev_dir / "closure_verdict.json").read_text(encoding="utf-8"))
    assert persisted["hypotheses_tested"] == 180
    assert persisted["hypotheses_unsat_count"] == 180
    assert persisted["experiment_scopes"]["ci_fast_scope"]["hypotheses_tested"] == 56
    assert persisted["experiment_scopes"]["canonical_certificate_scope"]["hypotheses_tested"] == 180
    assert persisted["experiment_scopes"]["extended_sweep_scope"]["hypotheses_tested"] == 399


def test_r30_cert_001_psmsl_sideways_ideal_and_nullstellensatz_replay():
    for w in ((0, 1), (1, 0, 1, 0), (1, 1, 0), (0, 0, 1)):
        trans_cert = build_psmsl_sideways_ideal_and_verify(w, horizon=8)
        assert trans_cert.translation_verified is True
        assert trans_cert.max_col_minus1_degree <= 1
        assert trans_cert.max_col_minus2_degree <= 1
        assert trans_cert.single_seed_evaluation_mismatches == 0

    for t_val in range(0, 7):
        ns_cert = build_nullstellensatz_certificate(t_val, (0, 1), max_horizon=14)
        assert ns_cert.polynomial_replay_verified is True
        assert ns_cert.free_left_variables_after_diagonals == 0
        assert ns_cert.mus_size <= 2
        assert ns_cert.max_generator_degree <= 1

    stress_results = run_adversarial_counterexample_stress_tests()
    assert len(stress_results) == 4
    assert all(st.passed for st in stress_results)


def test_r30_transport_001_diagonal_ablation_and_spatial_transport():
    # Deliverable 1: Diagonal ablation & primitive provenance
    ablation = run_diagonal_ablation_experiment(transients=(0, 1, 2, 3), periods=(2, 3), max_horizon=14)
    assert ablation["total_hypotheses_evaluated"] == 32
    sweep = ablation["ablation_sweep_by_max_diagonal_d"]
    assert sweep["D0_to_D5"]["degree_0_mus_1_count"] == 32
    assert sweep["D0_to_D2"]["degree_0_mus_1_count"] == 32
    assert (
        sweep["no_diagonals"]["degree_0_mus_1_count"]
        < sweep["D0_to_D0"]["degree_0_mus_1_count"]
        < sweep["D0_to_D2"]["degree_0_mus_1_count"]
    )

    prov_t3 = reconstruct_primitive_contradiction_provenance(3, (1, 0), max_horizon=14)
    assert prov_t3.dependency_category == "SINGLE_FINITE_DIAGONAL_D0_OR_D1"
    assert prov_t3.min_diagonal_d_for_degree0_mus1 == 0
    assert prov_t3.mus_size_at_d0_only == 1
    assert prov_t3.max_deg_at_d0_only == 0

    # Deliverable 2: Spatial relation transport
    tr_10 = trace_spatial_relation_transport((1, 0), max_depth=6)
    assert tr_10.max_closed_affine_depth == 3
    # Under w=(1,0), depths 1, 2, 3 remain degree<=1 across all steps; depth 4 breaks on odd steps
    assert tr_10.first_non_closed_depth == 4
    assert "time-shifted white-step variables" in tr_10.obstruction_mechanism

    # Deliverable 4: Spatiotemporal relation algebra (R30-SPATIOTEMPORAL-001)
    st_10 = analyze_spatiotemporal_relation_algebra((1, 0), max_depth=6)
    assert st_10.temporal_support_step_law_verified is True
    assert st_10.leading_offset_purely_linear_all_depths is True
    assert st_10.psmsl_and_operator_pruning_ratio > 0.5
    # Verify inter-step quadratic cancellation at depth d=5, phi=0:
    # Even though d=4, phi=1 is quadratic ("u_0*u_2"), d=5, phi=0 collapses back to "1 ^ u_1" (deg 1)!
    by_d_phi = {(r.depth_d, r.phase_phi): r for r in st_10.phase_relations}
    assert by_d_phi[(4, 1)].canonical_offset_anf == "u_0*u_2"
    assert by_d_phi[(4, 1)].polynomial_degree == 2
    assert by_d_phi[(5, 0)].canonical_offset_anf == "1 ^ u_1"
    assert by_d_phi[(5, 0)].polynomial_degree == 1
    assert by_d_phi[(6, 0)].canonical_offset_anf == "u_1 ^ u_3 ^ u_5"
    assert by_d_phi[(6, 0)].polynomial_degree == 1

    # Deliverable 5: Right-coupled characteristic-flux verification (R30-FLUX-CORR-001)
    rc_flux = analyze_right_coupled_characteristic_flux(
        transients=(1, 2, 3), periods=(2, 3), max_depth=6
    )
    assert rc_flux.total_hypotheses_tested == 24
    assert rc_flux.pure_left_onset_unsat_count == 23
    assert rc_flux.right_coupled_flux_unsat_count == 24
    assert rc_flux.white_run_cases_closed_by_right_correlation == (
        "T=3, w=[1, 0, 0] -> refuted at k=3 by right-half correlation (n_right_vars=1)",
    )


def test_formal_lean_modules_and_official_check_lean():
    ver = verify_closure_certificates_and_lean_modules(run_live_lean=True)
    assert ver.formal_files_clean_no_sorry_or_axiom is True
    assert ver.lean_compilation_succeeded is True
    assert ver.check_lean_verdict == "pass"
    assert ver.headlines_verified == 39
    assert ver.replayed_constants == 49
    assert ver.new_axioms == []
