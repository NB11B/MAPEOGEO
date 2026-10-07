"""Unit tests for canonical graph primitives, contracts, and transactions."""

from __future__ import annotations

import pytest

from mapeogeo.graph.decision_graph import DecisionGraph
from mapeogeo.graph.edge import Edge, EdgeContract
from mapeogeo.graph.node import Node, NodeKind, NodeRegistry, NodeRole
from mapeogeo.graph.relation import RelationType


def test_node_creation_and_registry() -> None:
    registry = NodeRegistry(namespace="test")
    n1 = Node(node_id="n1", kind=NodeKind.QUERY, role=NodeRole.ATOMIC_JUDGMENT)
    n2 = Node(node_id="n2", kind=NodeKind.COMPOSE, role=NodeRole.DETERMINISTIC_COMPOSE)

    registry.register(n1)
    registry.register(n2)

    assert len(registry) == 2
    assert registry.get("n1") == n1
    assert registry.require("n2") == n2

    # Duplicate registration raises ValueError
    with pytest.raises(ValueError, match="already registered"):
        registry.register(Node(node_id="n1"))

    # Empty node_id raises ValueError
    with pytest.raises(ValueError, match="non-empty string"):
        Node(node_id="")


def test_relation_strength_evidentiary_ordering() -> None:
    # CANDIDATE_REPRESENTS < REPRESENTS < SAME_SEMANTICS
    assert (
        RelationType.CANDIDATE_REPRESENTS.evidentiary_level
        < RelationType.REPRESENTS.evidentiary_level
    )
    assert RelationType.REPRESENTS.evidentiary_level < RelationType.SAME_SEMANTICS.evidentiary_level
    assert (
        RelationType.SCOPED_OVERLAP.evidentiary_level < RelationType.EQUIVALENT_TO.evidentiary_level
    )


def test_fail_closed_relation_contracts() -> None:
    # 1. Candidate cannot satisfy REPRESENTS contract
    contract_rep = EdgeContract(contract_id="c1", required_relation=RelationType.REPRESENTS)
    assert not contract_rep.validate_assertion(RelationType.CANDIDATE_REPRESENTS)
    assert contract_rep.validate_assertion(RelationType.REPRESENTS)

    # 2. Uncertified EQUIVALENT_TO or SAME_SEMANTICS must fail closed
    contract_equiv = EdgeContract(
        contract_id="c2", required_relation=RelationType.EQUIVALENT_TO, is_certified=False
    )
    assert not contract_equiv.validate_assertion(RelationType.EQUIVALENT_TO)

    certified_equiv = EdgeContract(
        contract_id="c3", required_relation=RelationType.EQUIVALENT_TO, is_certified=True
    )
    assert certified_equiv.validate_assertion(RelationType.EQUIVALENT_TO)
    assert certified_equiv.validate_assertion(RelationType.SAME_SEMANTICS)

    # 3. Edge creation fails if contract is violated
    with pytest.raises(ValueError, match="violates contract"):
        Edge(
            source_id="a",
            target_id="b",
            relation=RelationType.CANDIDATE_REPRESENTS,
            contract=contract_rep,
        )


def test_decision_graph_and_transaction_lifecycle() -> None:
    graph = DecisionGraph(graph_id="g1")
    tx = graph.begin_transaction()

    n1 = Node(node_id="q1", kind=NodeKind.QUERY, role=NodeRole.ATOMIC_JUDGMENT)
    n2 = Node(node_id="q2", kind=NodeKind.QUERY, role=NodeRole.ATOMIC_JUDGMENT)
    n3 = Node(node_id="decide1", kind=NodeKind.DECIDE, role=NodeRole.POLICY_DECISION)

    tx.add_node(n1)
    tx.add_node(n2)
    tx.add_node(n3)

    e1 = Edge(source_id="q1", target_id="decide1", relation=RelationType.REPRESENTS)
    e2 = Edge(source_id="q2", target_id="decide1", relation=RelationType.REPRESENTS)

    tx.add_edge(e1)
    tx.add_edge(e2)

    # Cannot commit without validation certificate
    with pytest.raises(PermissionError):
        tx.commit(None)  # type: ignore

    # Validation succeeds and issues certificate
    cert = tx.validate()
    assert "ACYCLIC_INVARIANT" in cert.invariants_passed
    assert "DANGLING_EDGE_INVARIANT" in cert.invariants_passed

    snapshot = tx.commit(cert)
    graph.apply_snapshot(snapshot)

    assert len(graph.nodes) == 3
    assert len(graph.edges) == 2
    assert graph.parents("decide1") == ["q1", "q2"]
    assert graph.children("q1") == ["decide1"]
    assert graph.topological_sort() == ["q1", "q2", "decide1"]


def test_transaction_rejects_cycles() -> None:
    graph = DecisionGraph(graph_id="cyclic_test")
    tx = graph.begin_transaction()

    tx.add_node(Node(node_id="a"))
    tx.add_node(Node(node_id="b"))
    tx.add_edge(Edge(source_id="a", target_id="b"))
    tx.add_edge(Edge(source_id="b", target_id="a"))

    with pytest.raises(ValueError, match="Cycle detected"):
        tx.validate()


def test_transaction_rejects_dangling_edges() -> None:
    graph = DecisionGraph(graph_id="dangling_test")
    tx = graph.begin_transaction()

    tx.add_node(Node(node_id="a"))
    tx.add_edge(Edge(source_id="a", target_id="nonexistent"))

    with pytest.raises(ValueError, match="nonexistent target_id"):
        tx.validate()
