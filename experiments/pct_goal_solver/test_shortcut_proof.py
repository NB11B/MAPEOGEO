from __future__ import annotations

from dataclasses import dataclass, replace

import pytest

from .shortcut_proof import (
    LineageObligation,
    ProofStatus,
    TypeNode,
    prove_lineage_obligation,
    validate_lineage_proof,
    validate_lineage_witness,
)


@dataclass(frozen=True)
class Port:
    port_id: str
    artifact_type: TypeNode


@dataclass(frozen=True)
class Edge:
    operator_id: str
    input_ports: tuple[Port, ...]
    output: TypeNode
    implementation_digest: str
    execution_kind: str = "PRIMITIVE"


EXACT_COEFF = TypeNode("POLYNOMIAL_COEFFICIENTS_EXACT", "RATIONAL_VECTOR", "EXACT")
GRID = TypeNode("NUMERICAL_EVAL_GRID", "RATIONAL_GRID", "EXACT")
SYMBOLIC_POLY = TypeNode("SYMBOLIC_POLYNOMIAL", "SYMBOLIC_EXPRESSION", "SYMBOLIC")
NUMERIC_SERIES = TypeNode("NUMERICAL_EVALUATION_SERIES", "INTERVAL_SERIES", "NUMERICAL")
CERTIFICATE = TypeNode("BOUNDED_RESIDUAL_CERTIFICATE", "VERIFICATION_CERTIFICATE", "NUMERICAL")
UNRELATED = TypeNode("UNRELATED_EVIDENCE", "TOKEN", "EXACT")


def _edge(operator_id: str, inputs: tuple[tuple[str, TypeNode], ...], output: TypeNode) -> Edge:
    return Edge(
        operator_id,
        tuple(Port(port_id, artifact_type) for port_id, artifact_type in inputs),
        output,
        implementation_digest=f"sha256:{operator_id.lower()}",
    )


def _registry() -> dict[str, Edge]:
    return {
        "LIFT": _edge("LIFT", (("coefficients", EXACT_COEFF),), SYMBOLIC_POLY),
        "EVALUATE": _edge(
            "EVALUATE",
            (("polynomial", SYMBOLIC_POLY), ("grid", GRID)),
            NUMERIC_SERIES,
        ),
        "CERTIFY": _edge("CERTIFY", (("series", NUMERIC_SERIES),), CERTIFICATE),
    }


def _obligation() -> LineageObligation:
    return LineageObligation(
        required_input_keys=frozenset({"coefficients", "grid"}),
        ordered_stage_types=(SYMBOLIC_POLY, NUMERIC_SERIES, CERTIFICATE),
        stage_required_input_keys=(
            frozenset({"coefficients"}),
            frozenset({"coefficients", "grid"}),
            frozenset({"coefficients", "grid"}),
        ),
    )


def _prove(registry: dict[str, Edge] | None = None):
    return prove_lineage_obligation(
        root_types={"coefficients": EXACT_COEFF, "grid": GRID},
        target_type=CERTIFICATE,
        obligation=_obligation(),
        registry=registry or _registry(),
        goal_contract={"family": "X1", "objective": "CERTIFY_RESIDUAL"},
    )


def test_complete_cross_class_hypergraph_is_proved_and_replayable() -> None:
    proof = _prove()
    assert proof.status is ProofStatus.PROVED
    assert proof.safe_witness is not None
    assert proof.counterexample is None
    assert proof.safe_witness.operator_path == ("LIFT", "EVALUATE", "CERTIFY")
    assert proof.safe_witness.final_root_keys == frozenset({"coefficients", "grid"})
    assert proof.safe_witness.final_stage_progress == 3
    assert validate_lineage_witness(
        proof.safe_witness,
        root_types={"coefficients": EXACT_COEFF, "grid": GRID},
        target_type=CERTIFICATE,
        obligation=_obligation(),
        registry=_registry(),
        expect_safe=True,
    )
    assert validate_lineage_proof(
        proof,
        root_types={"grid": GRID, "coefficients": EXACT_COEFF},
        target_type=CERTIFICATE,
        obligation=_obligation(),
        registry=dict(reversed(tuple(_registry().items()))),
        goal_contract={"objective": "CERTIFY_RESIDUAL", "family": "X1"},
    )


def test_direct_target_shortcut_refutes_with_counterexample() -> None:
    registry = _registry()
    registry["DIRECT"] = _edge("DIRECT", (("coefficients", EXACT_COEFF),), CERTIFICATE)
    proof = _prove(registry)
    assert proof.status is ProofStatus.REFUTED
    assert proof.counterexample is not None
    assert proof.counterexample.operator_path == ("DIRECT",)
    assert proof.counterexample.final_root_keys == frozenset({"coefficients"})
    assert proof.counterexample.final_stage_progress < 3
    assert validate_lineage_witness(
        proof.counterexample,
        root_types={"coefficients": EXACT_COEFF, "grid": GRID},
        target_type=CERTIFICATE,
        obligation=_obligation(),
        registry=registry,
        expect_safe=False,
    )


def test_witness_replay_rejects_mutated_lineage_fields() -> None:
    proof = _prove()
    assert proof.safe_witness is not None
    terminal = proof.safe_witness.nodes[-1]
    forged_terminal = replace(terminal, root_keys=frozenset({"coefficients", "grid", "forged"}))
    forged = replace(
        proof.safe_witness,
        nodes=proof.safe_witness.nodes[:-1] + (forged_terminal,),
        final_root_keys=forged_terminal.root_keys,
    )
    assert not validate_lineage_witness(
        forged,
        root_types={"coefficients": EXACT_COEFF, "grid": GRID},
        target_type=CERTIFICATE,
        obligation=_obligation(),
        registry=_registry(),
        expect_safe=True,
    )


@pytest.mark.parametrize("removed", ["LIFT", "EVALUATE", "CERTIFY"])
def test_removing_any_required_bridge_is_unreachable(removed: str) -> None:
    registry = _registry()
    del registry[removed]
    proof = _prove(registry)
    assert proof.status is ProofStatus.UNREACHABLE
    assert proof.safe_witness is None
    assert proof.counterexample is None


def test_unrelated_stage_evidence_does_not_satisfy_required_root_lineage() -> None:
    registry = _registry()
    registry.update(
        {
            "UNRELATED_LIFT": _edge("UNRELATED_LIFT", (("token", UNRELATED),), SYMBOLIC_POLY),
            "UNRELATED_EVAL": _edge(
                "UNRELATED_EVAL",
                (("polynomial", SYMBOLIC_POLY), ("grid", GRID)),
                NUMERIC_SERIES,
            ),
        }
    )
    proof = prove_lineage_obligation(
        root_types={"coefficients": EXACT_COEFF, "grid": GRID, "token": UNRELATED},
        target_type=CERTIFICATE,
        obligation=_obligation(),
        registry=registry,
        goal_contract={"family": "X1", "objective": "CERTIFY_RESIDUAL"},
    )
    assert proof.status is ProofStatus.REFUTED
    assert proof.counterexample is not None
    assert "token" in proof.counterexample.final_root_keys
    assert "coefficients" not in proof.counterexample.final_root_keys


def test_required_root_joined_only_at_terminal_does_not_backfill_stage_lineage() -> None:
    registry = {
        "UNRELATED_LIFT": _edge("UNRELATED_LIFT", (("token", UNRELATED),), SYMBOLIC_POLY),
        "UNRELATED_EVAL": _edge(
            "UNRELATED_EVAL",
            (("polynomial", SYMBOLIC_POLY), ("grid", GRID)),
            NUMERIC_SERIES,
        ),
        "LATE_JOIN_CERTIFY": _edge(
            "LATE_JOIN_CERTIFY",
            (("series", NUMERIC_SERIES), ("coefficients", EXACT_COEFF)),
            CERTIFICATE,
        ),
    }
    proof = prove_lineage_obligation(
        root_types={"coefficients": EXACT_COEFF, "grid": GRID, "token": UNRELATED},
        target_type=CERTIFICATE,
        obligation=_obligation(),
        registry=registry,
        goal_contract={"family": "X1", "objective": "CERTIFY_RESIDUAL"},
    )
    assert proof.status is ProofStatus.REFUTED
    assert proof.counterexample is not None
    assert proof.counterexample.final_root_keys >= frozenset({"coefficients", "grid"})
    assert proof.counterexample.final_stage_progress == 0


def test_complete_target_contract_includes_representation_and_exactness() -> None:
    wrong_representation = replace(CERTIFICATE, representation_class="UNSAFE_BOOLEAN")
    registry = _registry()
    registry["WRONG_TARGET"] = _edge(
        "WRONG_TARGET",
        (("coefficients", EXACT_COEFF),),
        wrong_representation,
    )
    assert _prove(registry).status is ProofStatus.PROVED

    wrong_exactness = replace(CERTIFICATE, exactness_class="EXACT")
    registry["WRONG_EXACTNESS"] = _edge(
        "WRONG_EXACTNESS",
        (("coefficients", EXACT_COEFF),),
        wrong_exactness,
    )
    assert _prove(registry).status is ProofStatus.PROVED


def test_registry_implementation_mutation_invalidates_old_proof() -> None:
    registry = _registry()
    proof = _prove(registry)
    registry["LIFT"] = replace(registry["LIFT"], implementation_digest="sha256:mutated")
    assert not validate_lineage_proof(
        proof,
        root_types={"coefficients": EXACT_COEFF, "grid": GRID},
        target_type=CERTIFICATE,
        obligation=_obligation(),
        registry=registry,
        goal_contract={"family": "X1", "objective": "CERTIFY_RESIDUAL"},
    )


def test_meta_edge_is_not_silently_ignored() -> None:
    registry = _registry()
    registry["META_TARGET"] = replace(
        _edge("META_TARGET", (), CERTIFICATE),
        execution_kind="META",
    )
    proof = _prove(registry)
    assert proof.status is ProofStatus.REFUTED
    assert proof.counterexample is not None
    assert proof.counterexample.operator_path == ("META_TARGET",)


@pytest.mark.parametrize(
    "bad_registry",
    [
        {"MISMATCH": _edge("ACTUAL", (), CERTIFICATE)},
        {"NO_DIGEST": replace(_edge("NO_DIGEST", (), CERTIFICATE), implementation_digest="")},
    ],
)
def test_incomplete_or_mismatched_registry_fails_closed(bad_registry: dict[str, Edge]) -> None:
    with pytest.raises(ValueError):
        _prove(bad_registry)


def test_missing_required_root_fails_closed() -> None:
    with pytest.raises(ValueError, match="missing required root"):
        prove_lineage_obligation(
            root_types={"coefficients": EXACT_COEFF},
            target_type=CERTIFICATE,
            obligation=_obligation(),
            registry=_registry(),
            goal_contract={"family": "X1"},
        )


def test_permuting_registry_and_roots_is_byte_deterministic() -> None:
    left = _prove()
    right = prove_lineage_obligation(
        root_types={"grid": GRID, "coefficients": EXACT_COEFF},
        target_type=CERTIFICATE,
        obligation=_obligation(),
        registry=dict(reversed(tuple(_registry().items()))),
        goal_contract={"objective": "CERTIFY_RESIDUAL", "family": "X1"},
    )
    assert left == right
    assert left.proof_digest == right.proof_digest


def test_single_artifact_cannot_fill_two_injective_ports() -> None:
    source = TypeNode("A", "R", "EXACT")
    joined = TypeNode("JOINED", "R", "SYMBOLIC")
    target = TypeNode("TARGET", "R", "NUMERICAL")
    registry = {
        "DOUBLE": _edge("DOUBLE", (("left", source), ("right", source)), joined),
        "FINISH": _edge("FINISH", (("joined", joined),), target),
    }
    obligation = LineageObligation(
        frozenset({"a"}),
        (joined, target),
        (frozenset({"a"}), frozenset({"a"})),
    )
    proof = prove_lineage_obligation(
        root_types={"a": source},
        target_type=target,
        obligation=obligation,
        registry=registry,
        goal_contract={"family": "INJECTIVE"},
    )
    assert proof.status is ProofStatus.UNREACHABLE


def test_distinct_same_state_derivations_can_fill_repeated_ports() -> None:
    source = TypeNode("A", "R", "EXACT")
    intermediate = TypeNode("S", "R", "SYMBOLIC")
    joined = TypeNode("JOINED", "R", "SYMBOLIC")
    target = TypeNode("TARGET", "R", "NUMERICAL")
    registry = {
        "LEFT": _edge("LEFT", (("source", source),), intermediate),
        "RIGHT": _edge("RIGHT", (("source", source),), intermediate),
        "JOIN": _edge("JOIN", (("left", intermediate), ("right", intermediate)), joined),
        "FINISH": _edge("FINISH", (("joined", joined),), target),
    }
    obligation = LineageObligation(
        frozenset({"a"}),
        (joined, target),
        (frozenset({"a"}), frozenset({"a"})),
    )
    proof = prove_lineage_obligation(
        root_types={"a": source},
        target_type=target,
        obligation=obligation,
        registry=registry,
        goal_contract={"family": "INJECTIVE"},
    )
    assert proof.status is ProofStatus.PROVED
    assert proof.safe_witness is not None
    join_node = next(node for node in proof.safe_witness.nodes if node.operator_id == "JOIN")
    assert len(set(join_node.input_node_ids)) == 2


def test_cycle_closure_is_finite_and_can_supply_one_distinct_derived_instance() -> None:
    source = TypeNode("A", "R", "EXACT")
    joined = TypeNode("JOINED", "R", "SYMBOLIC")
    target = TypeNode("TARGET", "R", "NUMERICAL")
    registry = {
        "CYCLE": _edge("CYCLE", (("source", source),), source),
        "JOIN": _edge("JOIN", (("left", source), ("right", source)), joined),
        "FINISH": _edge("FINISH", (("joined", joined),), target),
    }
    obligation = LineageObligation(
        frozenset({"a"}),
        (joined, target),
        (frozenset({"a"}), frozenset({"a"})),
    )
    proof = prove_lineage_obligation(
        root_types={"a": source},
        target_type=target,
        obligation=obligation,
        registry=registry,
        goal_contract={"family": "FINITE_CYCLE"},
    )
    assert proof.status is ProofStatus.PROVED
    assert proof.explored_state_count < 20


def test_malformed_witness_objects_fail_closed_without_raising() -> None:
    proof = _prove()
    assert proof.safe_witness is not None
    malformed_nodes = replace(proof.safe_witness, nodes=None)  # type: ignore[arg-type]
    assert not validate_lineage_witness(
        malformed_nodes,
        root_types={"coefficients": EXACT_COEFF, "grid": GRID},
        target_type=CERTIFICATE,
        obligation=_obligation(),
        registry=_registry(),
        expect_safe=True,
    )
    malformed_node = replace(proof.safe_witness.nodes[0], node_id=[])  # type: ignore[arg-type]
    malformed_id = replace(
        proof.safe_witness,
        nodes=(malformed_node,) + proof.safe_witness.nodes[1:],
    )
    assert not validate_lineage_witness(
        malformed_id,
        root_types={"coefficients": EXACT_COEFF, "grid": GRID},
        target_type=CERTIFICATE,
        obligation=_obligation(),
        registry=_registry(),
        expect_safe=True,
    )


def test_top_level_proof_schema_uses_exact_types_and_recomputed_payload_digest() -> None:
    proof = _prove()
    common = {
        "root_types": {"coefficients": EXACT_COEFF, "grid": GRID},
        "target_type": CERTIFICATE,
        "obligation": _obligation(),
        "registry": _registry(),
        "goal_contract": {"family": "X1", "objective": "CERTIFY_RESIDUAL"},
    }
    assert not validate_lineage_proof(
        replace(proof, explored_state_count=float(proof.explored_state_count)),  # type: ignore[arg-type]
        **common,
    )
    assert not validate_lineage_proof(
        replace(proof, status="PROVED"),  # type: ignore[arg-type]
        **common,
    )
    assert not validate_lineage_proof(
        replace(proof, reason=proof.reason + " forged"),
        **common,
    )
    assert not validate_lineage_proof(
        replace(proof, proof_digest="0" * 64),
        **common,
    )
    assert proof.safe_witness is not None
    malformed_witness = replace(proof.safe_witness, nodes=None)  # type: ignore[arg-type]
    assert not validate_lineage_proof(
        replace(proof, safe_witness=malformed_witness),
        **common,
    )
    malformed_node_tuple = replace(proof.safe_witness, nodes=(None,))  # type: ignore[arg-type]
    assert not validate_lineage_proof(
        replace(proof, safe_witness=malformed_node_tuple),
        **common,
    )
