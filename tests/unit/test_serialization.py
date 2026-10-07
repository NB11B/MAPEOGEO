"""Unit tests for deterministic serialization and deserialization of graph and PSMSL objects."""

from __future__ import annotations

import json

from mapeogeo.graph.decision_graph import DecisionGraph
from mapeogeo.graph.edge import Edge, EdgeContract
from mapeogeo.graph.node import Node, NodeKind, NodeRole
from mapeogeo.graph.relation import RelationType
from mapeogeo.graph.serialization import (
    deserialize_edge,
    deserialize_node,
    deserialize_snapshot,
    serialize_edge,
    serialize_node,
    serialize_snapshot,
)
from mapeogeo.psmsl.latent import LatentGenerator, ObservableSignature, Observation
from mapeogeo.psmsl.operator import OperatorWord, TransformationOperator
from mapeogeo.psmsl.serialization import (
    deserialize_latent_generator,
    deserialize_observable_signature,
    deserialize_observation,
    deserialize_operator_word,
    serialize_latent_generator,
    serialize_observable_signature,
    serialize_observation,
    serialize_operator_word,
)


def test_node_deterministic_serialization_and_roundtrip() -> None:
    node = Node(node_id="q1", kind=NodeKind.QUERY, role=NodeRole.ATOMIC_JUDGMENT, scope_hash="abc")
    s1 = serialize_node(node)
    s2 = serialize_node(node)
    assert s1 == s2
    assert s1.endswith("\n")

    loaded = json.loads(s1)
    assert loaded["schema"] == "mapeogeo.graph.node"
    assert loaded["schema_version"] == 1

    node_rt = deserialize_node(s1)
    assert node_rt == node


def test_edge_deterministic_serialization_and_roundtrip() -> None:
    contract = EdgeContract(
        contract_id="c1", required_relation=RelationType.REPRESENTS, is_certified=True
    )
    edge = Edge(source_id="n1", target_id="n2", relation=RelationType.REPRESENTS, contract=contract)

    s1 = serialize_edge(edge)
    s2 = serialize_edge(edge)
    assert s1 == s2

    loaded = json.loads(s1)
    assert loaded["schema"] == "mapeogeo.graph.edge"
    assert loaded["schema_version"] == 1

    edge_rt = deserialize_edge(s1)
    assert edge_rt == edge


def test_snapshot_deterministic_serialization_and_roundtrip() -> None:
    g = DecisionGraph(graph_id="test_g")
    tx = g.begin_transaction()
    tx.add_node(Node(node_id="a"))
    tx.add_node(Node(node_id="b"))
    tx.add_edge(Edge(source_id="a", target_id="b"))
    cert = tx.validate()
    snap = tx.commit(cert)

    s1 = serialize_snapshot(snap)
    s2 = serialize_snapshot(snap)
    assert s1 == s2

    snap_rt = deserialize_snapshot(s1)
    assert snap_rt.snapshot_id == snap.snapshot_id
    assert snap_rt.state_hash == snap.state_hash
    assert len(snap_rt.nodes) == len(snap.nodes)
    assert len(snap_rt.edges) == len(snap.edges)


def test_operator_word_deterministic_serialization() -> None:
    t1 = TransformationOperator(operator_id="t1", matrix=((1.0, 0.0), (0.0, 1.0)))
    t2 = TransformationOperator(operator_id="t2", matrix=((2.0, 0.0), (0.0, 2.0)))
    word = OperatorWord(word_id="w1", operators=(t1, t2))

    s1 = serialize_operator_word(word)
    s2 = serialize_operator_word(word)
    assert s1 == s2

    word_rt = deserialize_operator_word(s1)
    assert word_rt.word_id == word.word_id
    assert len(word_rt.operators) == 2


def test_latent_generator_and_signature_serialization() -> None:
    obs1 = Observation(observation_id="o1", values=(1.0, 2.0))
    obs2 = Observation(observation_id="o2", values=(3.0, 4.0))

    s_obs = serialize_observation(obs1)
    obs_rt = deserialize_observation(s_obs)
    assert obs_rt == obs1

    sig = ObservableSignature(signature_id="sig1", observations=(obs1, obs2))

    s_sig = serialize_observable_signature(sig)
    sig_rt = deserialize_observable_signature(s_sig)
    assert sig_rt.signature_id == sig.signature_id
    assert len(sig_rt.observations) == 2

    gen = LatentGenerator(
        generator_id="g1", status="unknown", nullity=3, evidence_observations=("o1", "o2")
    )
    s_gen = serialize_latent_generator(gen)
    gen_rt = deserialize_latent_generator(s_gen)
    assert gen_rt.generator_id == gen.generator_id
    assert gen_rt.status == "unknown"
    assert gen_rt.nullity == 3
