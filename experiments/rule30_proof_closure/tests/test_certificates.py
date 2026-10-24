"""Tests for contradiction certificates, obligation graph auditing, and live Lean 4.35.0 verification."""

from __future__ import annotations

from pathlib import Path

from experiments.rule30_proof_closure.certificates import (
    run_proof_closure_campaign,
    verify_closure_certificates_and_lean_modules,
)


def test_proof_closure_campaign_and_obligation_auditor():
    report = run_proof_closure_campaign(max_period=3, transients=(0, 1, 2, 3), write_evidence=True)
    assert report.checkpoint_01_reconstruction_completeness is True
    assert report.checkpoint_02_bilateral_soundness is True
    assert report.conditional_closure_claims_automatically_rejected is True
    assert report.surviving_models_count == 0
    assert report.hypotheses_unsat_count == report.hypotheses_tested

    ev_dir = Path(__file__).resolve().parent.parent / "evidence"
    assert (ev_dir / "hypothesis_results.jsonl").exists()
    assert (ev_dir / "counterexamples.jsonl").exists()
    assert (ev_dir / "failed_claims.jsonl").exists()
    assert (ev_dir / "closure_verdict.json").exists()


def test_formal_lean_modules_and_official_check_lean():
    ver = verify_closure_certificates_and_lean_modules(run_live_lean=True)
    assert ver.formal_files_clean_no_sorry_or_axiom is True
    assert ver.lean_compilation_succeeded is True
    assert ver.check_lean_verdict == "pass"
    assert ver.headlines_verified == 20
    assert ver.replayed_constants == 21
    assert ver.new_axioms == []
