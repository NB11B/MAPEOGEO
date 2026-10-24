"""Contradiction certificate generation, canonical ideal normalization, and independent verification."""

from .proof_certificate import (
    ClosureCampaignReport,
    run_proof_closure_campaign,
)
from .certificate_verifier import (
    IndependentVerificationResult,
    verify_closure_certificates_and_lean_modules,
)
from .ideal_normalizer import (
    CounterexampleStressTestResult,
    GRAMMAR_CLUSTERS,
    NullstellensatzContradictionCertificate,
    PSMSLSidewaysTranslationCertificate,
    build_nullstellensatz_certificate,
    build_psmsl_sideways_ideal_and_verify,
    classify_word_operator_grammar,
    run_adversarial_counterexample_stress_tests,
)

__all__ = [
    "ClosureCampaignReport",
    "CounterexampleStressTestResult",
    "GRAMMAR_CLUSTERS",
    "IndependentVerificationResult",
    "NullstellensatzContradictionCertificate",
    "PSMSLSidewaysTranslationCertificate",
    "build_nullstellensatz_certificate",
    "build_psmsl_sideways_ideal_and_verify",
    "classify_word_operator_grammar",
    "run_adversarial_counterexample_stress_tests",
    "run_proof_closure_campaign",
    "verify_closure_certificates_and_lean_modules",
]
