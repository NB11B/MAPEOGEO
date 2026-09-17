from __future__ import annotations

from collections import Counter
from itertools import combinations
from pathlib import Path
import json
import math

import networkx as nx

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence"

_EQ_TYPES = {"SAME_SEMANTICS", "EQUIVALENT_TO"}
_TRUST_TYPES = _EQ_TYPES | {"REPRESENTS"}

def load_trust_projection() -> dict:
    return json.loads((EVIDENCE / "pct_e25b_trust_projection.json").read_text(encoding="utf-8"))


def _index(projection: dict):
    nodes = {n["id"]: n for n in projection["nodes"]}
    edges = projection["edges"]
    return nodes, edges


def _trust_graph(projection: dict) -> nx.Graph:
    graph = nx.Graph()
    for edge in projection["edges"]:
        if edge["type"] in _TRUST_TYPES:
            graph.add_edge(edge["source"], edge["target"], edge_id=edge["id"], edge_type=edge["type"])
    return graph


def _equivalence_graph(projection: dict) -> nx.Graph:
    graph = nx.Graph()
    for edge in projection["edges"]:
        if edge["type"] in _EQ_TYPES:
            graph.add_edge(edge["source"], edge["target"], edge_id=edge["id"], edge_type=edge["type"])
    return graph


def _source_hash(node: dict) -> str | None:
    return node.get("attributes", {}).get("source_statement_sha256")


def _component_anchor(component: set[str], edges: list[dict]) -> set[str]:
    return {
        e["target"]
        for e in edges
        if e["type"] == "REPRESENTS" and e["source"] in component and e["target"] in component
    }


def _identity_audit(projection: dict) -> dict:
    nodes, edges = _index(projection)
    graph = _trust_graph(projection)
    conflicts = []
    for component in nx.connected_components(graph):
        anchors = _component_anchor(component, edges)
        hashes = {_source_hash(nodes[nid]) for nid in component if _source_hash(nodes[nid])}
        if len(anchors) != 1 or len(hashes) > 1:
            conflicts.append({
                "nodes": sorted(component),
                "anchors": sorted(anchors),
                "source_hashes": sorted(hashes),
            })
    return {"pass": not conflicts, "conflicts": conflicts}


def _certificate_audit(projection: dict) -> dict:
    nodes, edges = _index(projection)
    identity = _identity_audit(projection)
    if not identity["pass"]:
        return {"pass": False, "conflicts": [{"kind": "IDENTITY_PRECONDITION"}]}

    conflicts = []
    explicit_refs = []
    for edge in edges:
        if edge["type"] in _EQ_TYPES:
            attrs = edge.get("attributes", {})
            cert = attrs.get("certificate")
            if cert:
                explicit_refs.append((edge["id"], cert))
                if cert not in nodes or nodes[cert].get("attributes", {}).get("status") != "PASS":
                    conflicts.append({"kind": "EQUIVALENCE_CERTIFICATE", "edge": edge["id"], "certificate": cert})
            if attrs.get("evidence") == "LEAN_KERNEL_VERIFIED":
                source = edge["source"]
                verified = [
                    e["target"] for e in edges
                    if e["type"] == "VERIFIED_BY" and e["source"] == source
                ]
                if not any(
                    cid in nodes
                    and nodes[cid].get("attributes", {}).get("status") == "PASS"
                    and nodes[cid].get("attributes", {}).get("certificate_class") == "KERNEL_VERIFIED"
                    for cid in verified
                ):
                    conflicts.append({"kind": "FORMAL_KERNEL_CERTIFICATE", "representation": source})

    graph = _trust_graph(projection)
    for component in nx.connected_components(graph):
        anchors = _component_anchor(component, edges)
        for anchor in anchors:
            verified = [
                e["target"] for e in edges
                if e["type"] == "VERIFIED_BY" and e["source"] == anchor
            ]
            if not verified or not all(
                cid in nodes and nodes[cid].get("attributes", {}).get("status") == "PASS"
                for cid in verified
            ):
                conflicts.append({"kind": "ANCHOR_CERTIFICATE", "anchor": anchor, "certificates": verified})

    return {"pass": not conflicts, "conflicts": conflicts, "explicit_equivalence_refs": len(explicit_refs)}


def run_e25b() -> dict:
    projection = load_trust_projection()
    graph = _trust_graph(projection)
    eq_graph = _equivalence_graph(projection)
    components = list(nx.connected_components(graph))
    edges = projection["edges"]

    endpoint_pairs = 0
    multipath_endpoint_pairs = 0
    single_path_endpoint_pairs = 0
    distinct_path_pair_comparisons = 0
    max_paths = 0

    identity = _identity_audit(projection)
    certificate = _certificate_audit(projection)

    for component in components:
        sub = graph.subgraph(component)
        for source, target in combinations(sorted(component), 2):
            paths = list(nx.all_simple_paths(sub, source, target))
            endpoint_pairs += 1
            max_paths = max(max_paths, len(paths))
            if len(paths) >= 2:
                multipath_endpoint_pairs += 1
                distinct_path_pair_comparisons += math.comb(len(paths), 2)
            else:
                single_path_endpoint_pairs += 1

    eq_nodes = set(eq_graph.nodes)
    anchors = {
        e["target"] for e in edges
        if e["type"] == "REPRESENTS" and e["source"] in eq_nodes
    }
    anchor_representation_pairs = 0
    anchor_representation_pairs_with_alternate_path = 0
    for component in components:
        sub = graph.subgraph(component)
        comp_anchors = sorted(set(component) & anchors)
        reps = sorted(set(component) & eq_nodes)
        for anchor in comp_anchors:
            for rep in reps:
                anchor_representation_pairs += 1
                if len(list(nx.all_simple_paths(sub, anchor, rep))) >= 2:
                    anchor_representation_pairs_with_alternate_path += 1

    independent_cycle_rank = sum(
        graph.subgraph(c).number_of_edges() - graph.subgraph(c).number_of_nodes() + 1
        for c in components
    )
    size_histogram = Counter(str(len(c)) for c in components)
    cyclic_components = sum(
        graph.subgraph(c).number_of_edges() - graph.subgraph(c).number_of_nodes() + 1 > 0
        for c in components
    )

    status = "PASS" if identity["pass"] and certificate["pass"] and single_path_endpoint_pairs == 0 else "FAIL"
    return {
        "experiment_id": "E25B_FULL_MULTIPATH_CONSISTENCY_AUDIT",
        "status": status,
        "trust_components": len(components),
        "component_size_histogram": dict(sorted(size_histogram.items())),
        "equivalence_only_cycles": len(nx.cycle_basis(eq_graph)),
        "trust_projection_cyclic_components": cyclic_components,
        "independent_cycle_rank": independent_cycle_rank,
        "endpoint_pairs": endpoint_pairs,
        "multipath_endpoint_pairs": multipath_endpoint_pairs,
        "single_path_endpoint_pairs": single_path_endpoint_pairs,
        "distinct_path_pair_comparisons": distinct_path_pair_comparisons,
        "max_simple_paths_between_one_endpoint_pair": max_paths,
        "bridges": len(list(nx.bridges(graph))),
        "anchor_representation_pairs": anchor_representation_pairs,
        "anchor_representation_pairs_with_alternate_path": anchor_representation_pairs_with_alternate_path,
        "identity_path_conflicts": len(identity["conflicts"]),
        "certificate_path_conflicts": len(certificate["conflicts"]),
        "maximum_persisted_closure_level": "C1_CERTIFICATE",
        "claim_boundary": (
            "E25B is exhaustive over the frozen trust projection consisting of SAME_SEMANTICS, "
            "EQUIVALENT_TO, REPRESENTS, and associated VERIFIED_BY evidence from the audited v0.9 artifact. "
            "It does not treat concept, proof-dependency, or candidate edges as semantic identity morphisms."
        ),
    }


