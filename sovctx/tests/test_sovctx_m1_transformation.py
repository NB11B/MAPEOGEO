#!/usr/bin/env python3
"""
Unit tests for SOVCTX-M1: Equation Transformation & Operator Closure.
Tests EquationTransformationWorker on Jetson Nano work plane.
"""

from pathlib import Path
from sovctx.node.equation_transformation_worker import (
    EquationTransformationWorker,
    TRANSFORMATION_RELATIONS,
)


def test_worker_discovers_12_transformation_proposals() -> None:
    worker = EquationTransformationWorker()
    proposals = worker.discover_transformations()

    assert len(proposals) == 12
    p_ids = {p.proposal_id for p in proposals}
    assert "PROP:M1_01_VLASOV_LINEARIZATION" in p_ids
    assert "PROP:M1_02_VLASOV_OSCILLATOR_REDUCTION" in p_ids
    assert "PROP:M1_03_VLASOV_MOMENT_CLOSURE" in p_ids
    assert "PROP:M1_04_PONTRYAGIN_SPECIAL_CASE" in p_ids
    assert "PROP:M1_05_PONTRYAGIN_STATE_ADJOINT_DUALITY" in p_ids
    assert "PROP:M1_06_PONTRYAGIN_VARIATIONAL_FORM" in p_ids
    assert "PROP:M1_07_TIKHONOV_REGULARIZATION" in p_ids
    assert "PROP:M1_08_GELFAND_LEVITAN_INVERSE" in p_ids
    assert "PROP:M1_09_CHEBYSHEV_APPROXIMATION" in p_ids
    assert "PROP:M1_10_LEIBNIZ_BOCKER_DISCRETIZATION" in p_ids
    assert "PROP:M1_11_LEIBNIZ_BOCKER_STREAMING_OJA" in p_ids
    assert "PROP:M1_12_LYAPUNOV_STABILITY_CERTIFICATE" in p_ids


def test_all_proposals_have_mathematical_realm() -> None:
    worker = EquationTransformationWorker()
    proposals = worker.discover_transformations()

    for p in proposals:
        assert p.relation_realm == "MATHEMATICAL"
        assert p.relation_type in TRANSFORMATION_RELATIONS


def test_proposals_conserve_work_plane_authority_boundary() -> None:
    worker = EquationTransformationWorker()
    proposals = worker.discover_transformations()

    for p in proposals:
        assert p.status == "PROPOSED"
        assert p.authority == "WORK_PLANE"
        assert 0.90 <= p.work_plane_confidence <= 1.0


def test_proposals_ground_in_operator_atlas() -> None:
    worker = EquationTransformationWorker()
    proposals = worker.discover_transformations()

    for p in proposals:
        assert p.operator_id in worker.operators
        op = worker.operators[p.operator_id]
        assert op["type"] == "OPERATOR"


def test_vlasov_oscillator_reduction_assumptions() -> None:
    worker = EquationTransformationWorker()
    proposals = worker.discover_transformations()
    p2 = [p for p in proposals if p.proposal_id == "PROP:M1_02_VLASOV_OSCILLATOR_REDUCTION"][0]

    assert p2.relation_type == "REDUCES_TO"
    assert "ASSUMPTION:VLASOV_POSITIVE_DENSITY_MASS" in p2.required_assumptions
    assert "INVARIANT:VLASOV_FREQUENCY_CHARGE_SIGN" in p2.preserved_invariants


def test_pontryagin_special_case_mayer() -> None:
    worker = EquationTransformationWorker()
    proposals = worker.discover_transformations()
    p4 = [p for p in proposals if p.proposal_id == "PROP:M1_04_PONTRYAGIN_SPECIAL_CASE"][0]

    assert p4.relation_type == "SPECIAL_CASE_OF"
    assert "psi_0 = 0" in p4.morphism_signature
    assert "ASSUMPTION:PON_FIXED_CONTROL_SET" in p4.required_assumptions


def test_tikhonov_regularization_assumptions() -> None:
    worker = EquationTransformationWorker()
    proposals = worker.discover_transformations()
    p7 = [p for p in proposals if p.proposal_id == "PROP:M1_07_TIKHONOV_REGULARIZATION"][0]

    assert p7.relation_type == "REGULARIZES"
    assert "ASSUMPTION:TIKH_ALPHA_POSITIVE" in p7.required_assumptions
    assert "ASSUMPTION:TIKH_POSITIVE_WEIGHTS" in p7.required_assumptions
    assert "INVARIANT:TIKH_FORWARD_LINEARITY" in p7.preserved_invariants


def test_7stage_composable_pipeline_construction() -> None:
    worker = EquationTransformationWorker()
    pipe = worker.build_composable_pipeline()

    assert pipe["pipeline_id"] == "PIPE:SOVCTX_M1_7STAGE"
    assert pipe["composable"] is True
    assert pipe["information_loss_ratio"] <= 0.20
    assert len(pipe["stages"]) == 7

    stage_names = [s["stage"] for s in pipe["stages"]]
    assert stage_names == [
        "EVOLVE",
        "CONSTRAIN",
        "STABILIZE",
        "OPTIMIZE",
        "INVERT",
        "APPROXIMATE",
        "RECONSTRUCT",
    ]
