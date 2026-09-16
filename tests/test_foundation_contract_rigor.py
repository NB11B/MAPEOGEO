"""Adversarial tests for declaration-bound foundation evidence."""

from __future__ import annotations

from dataclasses import replace
import math

import pytest

from scripts.foundation_contracts import (
    ContractEvidence,
    build_foundation_contract_evidence,
    dedekind_cut_sqrt2,
    euclidean_distance,
    is_equivalence_relation,
    validate_contract_evidence,
    verify_angle_sum_formulas,
    verify_bijective_inverse,
    verify_binomial_theorem,
    verify_chain_rule_derivative,
    verify_cauchy_schwarz,
    verify_indicator_algebra,
    verify_implication_truth_table,
    verify_fundamental_theorem_of_calculus,
    verify_product_rule_derivative,
    verify_pythagorean_theorem,
    verify_pythagorean_trig_identity,
    verify_power_rule_derivative,
    verify_sequence_window,
    verify_triangle_inequality_reals,
)
from scripts.import_foundation_backfill import generate_foundation_declarations
from scripts.foundation_intake import ingest_foundation_declarations


DE_MORGAN_ID = "srcdecl:foundation:logic:de_morgan_logic"
DE_MORGAN_SHA256 = "a45048e4567c3a6ba39ca5ed4674f68d2d1aef830429319c6e3754c7ab245152"


def test_broken_implication_evaluator_is_detected() -> None:
    assert verify_implication_truth_table(lambda _p, _q: True) is False


def test_relation_pairs_must_lie_in_declared_domain() -> None:
    assert is_equivalence_relation({(1, 1), (2, 2), (3, 3)}, {1, 2}) is False


def test_inverse_samples_are_nonempty_two_sided_and_finite() -> None:
    assert verify_bijective_inverse(lambda x: x, lambda x: x, [], []) is False
    assert verify_bijective_inverse(math.exp, math.log, [0.0], [-1.0, 1.0]) is False
    assert verify_bijective_inverse(lambda _x: math.nan, lambda x: x, [0.0], [0.0]) is False


def test_dedekind_cut_uses_exact_integer_arithmetic() -> None:
    # 318281039^2 - 2*225058681^2 = -1; float division rounds this case away.
    assert dedekind_cut_sqrt2(318281039, 225058681) == (True, False)
    with pytest.raises((TypeError, ValueError)):
        dedekind_cut_sqrt2(7.0, 5)
    with pytest.raises(ValueError):
        dedekind_cut_sqrt2(7, 0)


def test_vectors_require_equal_nonzero_finite_dimensions() -> None:
    with pytest.raises(ValueError):
        euclidean_distance([0.0], [0.0, 5.0])
    with pytest.raises(ValueError):
        euclidean_distance([], [])
    with pytest.raises(ValueError):
        euclidean_distance([math.inf], [0.0])


def test_sequence_checker_is_explicitly_a_finite_window() -> None:
    assert verify_sequence_window(lambda n: 1.0 / n, 0.0, 0.01, 101, 5)
    assert not verify_sequence_window(lambda _n: math.nan, 0.0, 0.01, 1, 5)
    assert not verify_sequence_window(lambda n: 0.0, 0.0, 0.01, 1, 0)


def test_power_rule_handles_zero_power_at_zero() -> None:
    assert verify_power_rule_derivative(0, 0.0)


def test_only_de_morgan_receives_exhaustive_executable_evidence() -> None:
    declarations = generate_foundation_declarations()
    evidence = build_foundation_contract_evidence(declarations)
    assert len(evidence) == 1
    item = evidence[0]
    assert item.subject_ids == (DE_MORGAN_ID,)
    assert item.subject_hashes == ((DE_MORGAN_ID, DE_MORGAN_SHA256),)
    assert item.certificate_class == "EXECUTABLE_EXHAUSTIVE_FINITE"
    assert item.status == "PASS"
    assert item.certificate_class != "KERNEL_VERIFIED"
    summary = validate_contract_evidence(evidence, declarations)
    assert summary["verified_declarations"] == 1
    assert summary["unverified_declarations"] == 175
    assert summary["kernel_verified_declarations"] == 0


def test_empty_or_forged_evidence_fails_closed() -> None:
    declarations = generate_foundation_declarations()
    with pytest.raises(ValueError, match="empty"):
        validate_contract_evidence((), declarations)

    item = build_foundation_contract_evidence(declarations)[0]
    forged = replace(
        item,
        subject_hashes=((DE_MORGAN_ID, "0" * 64),),
    )
    with pytest.raises(ValueError, match="hash"):
        validate_contract_evidence((forged,), declarations)


def test_recomputed_but_semantically_forged_evidence_fails_closed() -> None:
    declarations = generate_foundation_declarations()
    genuine = build_foundation_contract_evidence(declarations)[0]
    forged = ContractEvidence.create(
        contract_id=genuine.contract_id,
        contract_version=genuine.contract_version,
        subject_ids=genuine.subject_ids,
        subject_hashes=genuine.subject_hashes,
        verifier_id="python:not-a-registered-verifier",
        certificate_class=genuine.certificate_class,
        scope="ONE_INVENTED_CASE",
        witnesses=({"p": True, "q": False, "passed": True},),
        status="PASS",
    )
    with pytest.raises(ValueError, match="contract definition|verifier|witness"):
        validate_contract_evidence((forged,), declarations)


def test_evidence_cannot_be_attached_to_a_different_subject() -> None:
    declarations = generate_foundation_declarations()
    genuine = build_foundation_contract_evidence(declarations)[0]
    wrong_subject = next(item for item in declarations if item.node_id != DE_MORGAN_ID)
    with pytest.raises(ValueError, match="subject"):
        ingest_foundation_declarations(
            {"nodes": [], "edges": []},
            declarations,
            evidence_by_subject={wrong_subject.node_id: genuine},
        )


def test_ingestion_replays_the_closed_contract_registry_before_promotion() -> None:
    declarations = generate_foundation_declarations()
    genuine = build_foundation_contract_evidence(declarations)[0]
    forged = ContractEvidence.create(
        contract_id=genuine.contract_id,
        contract_version=genuine.contract_version,
        subject_ids=genuine.subject_ids,
        subject_hashes=genuine.subject_hashes,
        verifier_id=genuine.verifier_id,
        certificate_class=genuine.certificate_class,
        scope=genuine.scope,
        witnesses=({"p": False, "q": False, "passed": True},),
        status="PASS",
    )
    with pytest.raises(ValueError, match="contract definition|witness"):
        ingest_foundation_declarations(
            {"nodes": [], "edges": []},
            declarations,
            evidence_by_subject={DE_MORGAN_ID: forged},
        )


def test_evidence_digest_binds_subject_hash_and_witnesses() -> None:
    item = build_foundation_contract_evidence(generate_foundation_declarations())[0]
    mutated = ContractEvidence.create(
        contract_id=item.contract_id,
        contract_version=item.contract_version,
        subject_ids=item.subject_ids,
        subject_hashes=item.subject_hashes,
        verifier_id=item.verifier_id,
        certificate_class=item.certificate_class,
        scope=item.scope,
        witnesses=item.witnesses + ({"p": True, "q": True, "duplicate": True},),
        status=item.status,
    )
    assert mutated.evidence_digest != item.evidence_digest


def test_only_exact_subject_node_is_promoted_and_never_to_kernel_status() -> None:
    declarations = generate_foundation_declarations()
    item = build_foundation_contract_evidence(declarations)[0]
    graph = ingest_foundation_declarations(
        {"nodes": [], "edges": []},
        declarations,
        evidence_by_subject={DE_MORGAN_ID: item},
    )
    promoted = [
        node
        for node in graph["nodes"]
        if node["attributes"]["declaration_verification_status"] == "EXECUTABLE_VERIFIED"
    ]
    assert [node["id"] for node in promoted] == [DE_MORGAN_ID]
    assert promoted[0]["attributes"]["certificate_class"] == "EXECUTABLE_EXHAUSTIVE_FINITE"
    assert all(
        node["attributes"].get("certificate_class") != "KERNEL_VERIFIED"
        for node in graph["nodes"]
    )


def test_all_public_numeric_helpers_fail_closed_on_nonfinite_or_empty_evidence() -> None:
    assert not verify_triangle_inequality_reals(math.inf, 1.0)
    assert not verify_cauchy_schwarz([1e308], [1e308])
    assert not verify_indicator_algebra(set(), set(), set(), [])
    assert not verify_power_rule_derivative(0, 0.0, math.nan)
    assert not verify_sequence_window(lambda _n: 0.0, "not-a-real", 0.1, 1, 1)
    assert not verify_bijective_inverse(
        lambda x: x,
        lambda x: x,
        [0.0],
        [0.0],
        tol="not-a-real",
    )
    assert not verify_binomial_theorem(math.inf, 1.0, 2)
    assert not verify_pythagorean_theorem([1.0], [0.0, 1.0])
    assert not verify_pythagorean_trig_identity(math.inf)
    assert not verify_angle_sum_formulas(0.0, math.nan)
    assert not verify_product_rule_derivative(
        lambda x: x,
        lambda _x: 1.0,
        lambda x: x,
        lambda _x: 1.0,
        "not-a-real",
    )
    assert not verify_chain_rule_derivative(
        lambda x: x,
        lambda _x: 1.0,
        lambda x: x,
        lambda _x: 1.0,
        math.inf,
    )
    assert not verify_fundamental_theorem_of_calculus(
        lambda _x: math.nan,
        lambda x: x,
        0.0,
        1.0,
    )
