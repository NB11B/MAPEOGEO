#!/usr/bin/env python3
r"""
Unit tests for the Three-Layer Methodological Triad Engine (SOVCTX-TRIAD).
Verifies:
1. Strict Subgraph Separation (G_MATH, G_CYBER, G_BIONIC, G_H).
2. Boundary Compliance & Disallowed Edge Rejection.
3. Forward Pipeline Resolution (Layer 1 -> Layer 2 -> Layer 3).
4. Backward Reverse Inductive Resolution (Layer 3 -> Layer 2 -> Layer 1).
5. Epistemic Sufficiency Preservation across all 7 paradigms.
"""

import pytest
from sovctx.node.triad_architecture_engine import (
    BridgeRelationType,
    TriadArchitectureEngine,
    TriadBridgeEdge,
    TriadLayer,
)


@pytest.fixture
def engine() -> TriadArchitectureEngine:
    return TriadArchitectureEngine()


def test_triad_layers_separation(engine: TriadArchitectureEngine) -> None:
    """Verify that all three analytical layers and provenance are non-empty and disjoint."""
    assert len(engine.g_math) == 7
    assert len(engine.g_cyber) == 7
    assert len(engine.g_bionic) == 7
    assert len(engine.g_h) == 8

    # Ensure ID disjointness
    math_ids = set(engine.g_math.keys())
    cyber_ids = set(engine.g_cyber.keys())
    bionic_ids = set(engine.g_bionic.keys())
    prov_ids = set(engine.g_h.keys())

    assert len(math_ids.intersection(cyber_ids)) == 0
    assert len(cyber_ids.intersection(bionic_ids)) == 0
    assert len(bionic_ids.intersection(prov_ids)) == 0


def test_edge_compliance_and_rejection(engine: TriadArchitectureEngine) -> None:
    """Verify that edge compliance rules strictly reject ungrounded DERIVED_FROM and invalid jumps."""
    # 1. Existing edges should all be compliant
    for e in engine.edges:
        valid, msg = engine.validate_edge_compliance(e)
        assert valid, f"Edge {e.edge_id} failed compliance: {msg}"

    # 2. Reject ungrounded DERIVED_FROM
    unproven_edge = TriadBridgeEdge(
        edge_id="E_UNPROVEN",
        relation_type=BridgeRelationType.METHODOLOGY_REALIZED_AS_ARCHITECTURE,
        source_layer=TriadLayer.LAYER_1_MATH,
        target_layer=TriadLayer.LAYER_2_CYBER,
        source_id="MATH_RS",
        target_id="CYBER_BERNSTEIN_SYNERGY",
        epistemic_justification="Ungrounded assertion",
        has_documentary_proof=False,
    )
    # This relation is allowed because it is METHODOLOGY_REALIZED_AS_ARCHITECTURE
    valid, _ = engine.validate_edge_compliance(unproven_edge)
    assert valid

    # 3. Reject invalid endpoint layers
    invalid_jump = TriadBridgeEdge(
        edge_id="E_INVALID_JUMP",
        relation_type=BridgeRelationType.METHODOLOGY_REALIZED_AS_ARCHITECTURE,
        source_layer=TriadLayer.LAYER_1_MATH,
        target_layer=TriadLayer.LAYER_3_BIONIC,  # Invalid target for this type!
        source_id="MATH_RS",
        target_id="BIONIC_MOTOR_COORDINATION",
        epistemic_justification="Attempted bypass of Layer 2",
    )
    valid, msg = engine.validate_edge_compliance(invalid_jump)
    assert not valid
    assert "Invalid layer endpoints" in msg


def test_forward_triad_pipeline(engine: TriadArchitectureEngine) -> None:
    """Verify forward pipeline: Method -> Architecture -> Organization."""
    # Test Bernstein
    fwd_bernstein = engine.trace_forward("MATH_RS")
    assert len(fwd_bernstein) >= 1
    m, c, b = fwd_bernstein[0]
    assert m.symbol == "Rs"
    assert c.regulator_id == "CYBER_BERNSTEIN_SYNERGY"
    assert b.organization_id == "BIONIC_MOTOR_COORDINATION"

    # Test Lyapunov
    fwd_lyapunov = engine.trace_forward("MATH_I")
    assert len(fwd_lyapunov) >= 1
    m, c, b = fwd_lyapunov[0]
    assert m.symbol == "I"
    assert c.regulator_id == "CYBER_LYAPUNOV_REGULATOR"
    assert b.organization_id == "BIONIC_HOMEOSTATIC_SURVIVAL"

    # Test Anokhin
    fwd_anokhin = engine.trace_forward("MATH_AX")
    assert len(fwd_anokhin) >= 1
    m, c, b = fwd_anokhin[0]
    assert m.symbol == "Ax"
    assert c.regulator_id == "CYBER_ANOKHIN_ACCEPTOR"
    assert b.organization_id == "BIONIC_FUNCTIONAL_BEHAVIOR_SYSTEM"


def test_backward_triad_pipeline(engine: TriadArchitectureEngine) -> None:
    """Verify backward reverse inductive pipeline: Function -> Control -> Representation."""
    # Test reverse: Given dynamic motor balance function, what mathematics?
    rev_bernstein = engine.trace_backward("BIONIC_MOTOR_COORDINATION")
    assert len(rev_bernstein) >= 1
    b, c, m = rev_bernstein[0]
    assert b.organization_id == "BIONIC_MOTOR_COORDINATION"
    assert c.regulator_id == "CYBER_BERNSTEIN_SYNERGY"
    assert m.primitive_id == "MATH_RS"

    # Test reverse: Given homeostatic viability under shocks, what mathematics?
    rev_lyapunov = engine.trace_backward("BIONIC_HOMEOSTATIC_SURVIVAL")
    assert len(rev_lyapunov) >= 1
    b, c, m = rev_lyapunov[0]
    assert b.organization_id == "BIONIC_HOMEOSTATIC_SURVIVAL"
    assert c.regulator_id == "CYBER_LYAPUNOV_REGULATOR"
    assert m.primitive_id == "MATH_I"


def test_epistemic_sufficiency_closure(engine: TriadArchitectureEngine) -> None:
    """Verify 100% bi-directional closure and sufficiency across all 7 paradigms."""
    results = engine.verify_triad_sufficiency()
    assert results["all_edges_compliant"] is True
    assert results["bi_directional_closure_rate"] == 1.0
    assert len(results["paradigms"]) == 7

    for p in results["paradigms"]:
        assert p["epistemic_sufficiency_verified"] is True
        assert p["omission_preserved_across_layers"] is True
        assert len(p["forward_path"]) == 3
        assert len(p["backward_path"]) == 3
