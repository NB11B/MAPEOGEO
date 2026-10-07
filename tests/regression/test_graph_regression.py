"""Semantic regression tests reproducing historical graph behavior
from e32 and joint-layer-v0.21.
"""

from __future__ import annotations

from mapeogeo.graph.decision_graph import DecisionGraph
from mapeogeo.graph.edge import Edge, EdgeContract
from mapeogeo.graph.node import Node, NodeKind, NodeRole
from mapeogeo.graph.relation import RelationType


def test_historical_decision_dag_reconstruction() -> None:
    """Reconstructs the normative e32 decision DAG:
    QUERY(q1) -> GUARD(g1) -> COMPOSE(c1) -> DECIDE(d1)
    """
    g = DecisionGraph(graph_id="e32_regression_dag")
    tx = g.begin_transaction()

    q1 = Node(node_id="q1", kind=NodeKind.QUERY, role=NodeRole.ATOMIC_JUDGMENT)
    g1 = Node(node_id="g1", kind=NodeKind.GUARD, role=NodeRole.CONTROL_GUARD)
    c1 = Node(node_id="c1", kind=NodeKind.COMPOSE, role=NodeRole.DETERMINISTIC_COMPOSE)
    d1 = Node(node_id="d1", kind=NodeKind.DECIDE, role=NodeRole.POLICY_DECISION)

    for n in [q1, g1, c1, d1]:
        tx.add_node(n)

    tx.add_edge(Edge(source_id="q1", target_id="g1", relation=RelationType.REPRESENTS))
    tx.add_edge(Edge(source_id="g1", target_id="c1", relation=RelationType.REPRESENTS))
    tx.add_edge(Edge(source_id="c1", target_id="d1", relation=RelationType.REPRESENTS))

    cert = tx.validate()
    snap = tx.commit(cert)
    g.apply_snapshot(snap)

    assert g.topological_sort() == ["q1", "g1", "c1", "d1"]
    assert g.parents("d1") == ["c1"]
    assert g.children("q1") == ["g1"]


def test_joint_layer_relation_boundary_regression() -> None:
    """Reproduces v0.21 invariant: mechanism joint candidate cannot masquerade as equivalent."""
    contract = EdgeContract(
        contract_id="perelman_joint_contract",
        required_relation=RelationType.EQUIVALENT_TO,
        is_certified=False,
    )

    # Candidate represents cannot satisfy equivalent
    assert not contract.validate_assertion(RelationType.CANDIDATE_REPRESENTS)
    # Scoped overlap cannot satisfy equivalent
    assert not contract.validate_assertion(RelationType.SCOPED_OVERLAP)
    # Represents cannot satisfy equivalent
    assert not contract.validate_assertion(RelationType.REPRESENTS)
    # Even uncertified equivalent cannot satisfy uncertified contract
    assert not contract.validate_assertion(RelationType.EQUIVALENT_TO)
