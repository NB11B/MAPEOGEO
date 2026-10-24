"""Tests for contradiction certificates, Nullstellensatz ideal normalizer, and Lean 4.35.0 verification."""

from __future__ import annotations

import json
from pathlib import Path

from experiments.rule30_proof_closure.certificates import (
    build_nullstellensatz_certificate,
    build_psmsl_sideways_ideal_and_verify,
    run_adversarial_counterexample_stress_tests,
    run_proof_closure_campaign,
    verify_closure_certificates_and_lean_modules,
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


def test_formal_lean_modules_and_official_check_lean():
    ver = verify_closure_certificates_and_lean_modules(run_live_lean=True)
    assert ver.formal_files_clean_no_sorry_or_axiom is True
    assert ver.lean_compilation_succeeded is True
    assert ver.check_lean_verdict == "pass"
    assert ver.headlines_verified == 26
    assert ver.replayed_constants == 28
    assert ver.new_axioms == []
