from __future__ import annotations

from collections import Counter
from copy import deepcopy
from fractions import Fraction
from itertools import combinations, product
from pathlib import Path
import json
import math

import networkx as nx
import sympy as sp

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence"

_EQ_TYPES = {"SAME_SEMANTICS", "EQUIVALENT_TO"}
_TRUST_TYPES = _EQ_TYPES | {"REPRESENTS"}

_CYCLES = (
    {
        "contract": "rank",
        "anchor": "srcdecl:theorem:6_16",
        "eo": "repr:eo:theorem:6_16",
        "geo": "repr:geo:theorem:6_16",
        "formal": "formal:lean:theorem_6_16",
    },
    {
        "contract": "convex",
        "anchor": "srcdecl:definition:44_6",
        "eo": "repr:eo:definition:44_6",
        "geo": "repr:geo:definition:44_6",
        "formal": "formal:lean:definition_44_6",
    },
    {
        "contract": "lp",
        "anchor": "srcdecl:theorem:47_9",
        "eo": "repr:eo:theorem:47_9",
        "geo": "repr:geo:theorem:47_9",
        "formal": "formal:lean:theorem_47_9",
    },
    {
        "contract": "gauss",
        "anchor": "srcdecl:definition:53_4",
        "eo": "repr:eo:definition:53_4",
        "geo": "repr:geo:definition:53_4",
        "formal": "formal:lean:definition_53_4",
    },
)


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


def _gf2_rank(rows: list[int], n: int) -> int:
    rows = list(rows)
    rank = 0
    col = 0
    while col < n and rank < len(rows):
        pivot = next((i for i in range(rank9 len(rows)) if (rows[i] >> col) & 1), None)
        if pivot is None:
            col += 1
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        for i in range(len(rows)):
            if i != rank and ((rows[i] >> col) & 1):
                rows[i] ^= rows[rank]
        rank += 1
        col += 1
    return rank


def _rank_contract(mutate_view: str | None = None) -> tuple[int, int, bool]:
    checks = equalities = 0
    all_ok = True
    mutated = False
    for m in range(1, 4):
        for n in range(1, 4):
            for bits in range(1 << (m * n)):
                rows = [sum(((bits >> (i*n+j)) & 1) << j for j in range(n)) for i in range(m)]
                rank = _gf2_rank(rows, n)
                kernel = [x for x in range(1 << n) if all((row & x).bit_count() % 2 == 0 for row in rows)]
                eo = rank + int(math.log2(len(kernel)))

                image = set()
                kernel_count = 0
                for x in range(1 << n):
                    y = tuple((row & x).bit_count() % 2 for row in rows)
                    image.add(y)
                    kernel_count += all(v == 0 for v in y)
                geo = int(math.log2(len(image))) + int(math.log2(kernel_count))
                formal = n
                if mutate_view == "GEO" and not mutated:
                    geo += 1
                    mutated = True
                values = (eo, geo, formal)
                checks += 1
                for a, b in combinations(values, 2):
                    equalities += 1
                    all_ok &= a == b
    return checks, equalities, all_ok


def _convex_contract(mutate_view: str | None = None) -> tuple[int, int, bool]:
    vals = [Fraction(i) for i in range(-2, 3)]
    queries = [Fraction(i, 2) for i in range(-4, 5)]
    checks = equalities = 0
    all_ok = True
    mutated = False
    for mask in range(1, 1 << 5):
        pts = [vals[i] for i in range(5) if (mask >> i) & 1]
        lo, hi = min(pts), max(pts)
        for x in queries:
            if lo == hi:
                eo = x == lo
                formal = x == lo
            else:
                lam = (x - lo) / (hi - lo)
                eo = 0 <= lam <= 1 and (1 - lam) * lo + lam * hi == x
                formal = (x - lo) >= 0 and (hi - x) >= 0
            geo = lo <= x <= hi
            if mutate_view == "GEO" and not mutated:
                geo = not geo
                mutated = True
            values = (eo, geo, formal)
            checks += 1
            for a, b in combinations(values, 2):
                equalities += 1
                all_ok &= a == b
    return checks, equalities, all_ok


def _tuples(values: tuple[int, ...], length: int):
    yield from product(values, repeat=length)


def _lp_contract(mutate_view: str | None = None) -> tuple[int, int, bool]:
    vals = (1, 2, 3)
    checks = equalities = 0
    all_ok = True
    mutated = False
    for m in (1, 2, 3):
        for a in _tuples(vals, m):
            for b in _tuples(vals, m):
                for c in vals:
                    ratios = [Fraction(bi, ai) for ai, bi in zip(a, b)]
                    eo = Fraction(c) * min(ratios)
                    active = min(range(m), key=ratios.__getitem__)
                    geo = Fraction(b[active]) * Fraction(c, a[active])
                    formal = sorted(Fraction(c) * r for r in ratios)[0]
                    if mutate_view == "GEO" and not mutated:
                        geo += 1
                        mutated = True
                    values = (eo, geo, formal)
                    checks += 1
                    for x, y in combinations(values, 2):
                        equalities += 1
                        all_ok &= x == y
    return checks, equalities, all_ok


def _gauss_contract(mutate_view: str | None = None) -> tuple[int, int, bool]:
    nx_, ny_, dot, s2 = sp.symbols("nx ny dot s2", nonzero=True)
    eo = sp.expand(dot/s2 - nx_/(2*s2) - ny_/(2*s2))
    geo = sp.expand(-(nx_ + ny_ - 2*dot)/(2*s2))
    formal = sp.expand((-nx_ - ny_ + 2*dot)/(2*s2))
    if mutate_view == "GEO":
        geo = sp.expand(geo + 1/s2)
    values = (eo, geo, formal)
    equalities = 0
    all_ok = True
    for x, y in combinations(values, 2):
        equalities += 1
        all_ok &= sp.simplify(x - y) == 0
    return 1, equalities, all_ok


_EXECUTORS = {
    "rank": _rank_contract,
    "convex": _convex_contract,
    "lp": _lp_contract,
    "gauss": _gauss_contract,
}


def run_e25c(mutate_contract: str | None = None, mutate_view: str | None = None) -> dict:
    projection = load_trust_projection()
    nodes, _ = _index(projection)
    cycles = []
    total_inputs = 0
    total_equalities = 0
    for config in _CYCLES:
        for key in ("anchor", "eo", "geo", "formal"):
            if config[key] not in nodes:
                raise KeyError(f"missing E25C node: {config[key]}")
        eo_contract = nodes[config["eo"]].get("attributes", {}).get("contract")
        geo_contract = nodes[config["geo"]].get("attributes", {}).get("contract")
        if eo_contract != config["contract"] or geo_contract != config["contract"]:
            raise ValueError(f"contract mismatch for {config['contract']}")
        formal_scope = nodes[config["formal"]].get("attributes", {}).get("formal_scope")
        source_hashes = {
            _source_hash(nodes[nid])
            for nid in (config["anchor"], config["eo"], config["geo"], config["formal"])
            if _source_hash(nodes[nid])
        }
        if len(source_hashes) != 1:
            raise ValueError(f"source-hash inconsistency in executable cycle {config['contract']}")

        mutation = mutate_view if mutate_contract == config["contract"] else None
        exact_inputs, pairwise_equalities, all_paths_agree = _EXECUTORS[config["contract"]](mutation)
        total_inputs += exact_inputs
        total_equalities += pairwise_equalities
        cycles.append({
            **config,
            "formal_scope": formal_scope,
            "source_statement_sha256": next(iter(source_hashes)),
            "exact_inputs": exact_inputs,
            "pairwise_path_equalities": pairwise_equalities,
            "all_paths_agree": bool(all_paths_agree),
        })

    status = "PASS" if all(c["all_paths_agree"] for c in cycles) else "FAIL"
    return {
        "experiment_id": "E25C_EXECUTABLE_CYCLE_CONSISTENCY",
        "status": status,
        "cycle_count": len(cycles),
        "total_exact_inputs": total_inputs,
        "total_pairwise_path_equalities": total_equalities,
        "cycles": cycles,
        "maximum_executed_closure_level": "C2_EXECUTABLE_CONTRACT",
        "C3_chain_map": "NOT_APPLICABLE_TO_THESE_FOUR_CONTRACTS",
        "C4_induced_homology": "NOT_APPLICABLE_TO_THESE_FOUR_CONTRACTS",
        "C5_exact_morphism_provenance": "NOT_ESTABLISHED",
        "claim_boundary": (
            "E25C attaches executable contract adapters to the four existing source-bound EO/GEO/FORMAL cycles. "
            "The adapters instantiate the persisted v0.7 contracts and v0.8 formal scopes; they do not assert that "
            "all repository edges already contained executable morphisms or promote C3-C5 evidence."
        ),
    }


def run_synthetic_layer_attacks() -> dict:
    base = load_trust_projection()

    anchor_swap = deepcopy(base)
    for edge in anchor_swap["edges"]:
        if edge["type"] == "REPRESENTS" and edge["source"] == "repr:eo:theorem:6_16":
            edge["target"] = "srcdecl:definition:44_6"
            break
    a0 = _identity_audit(anchor_swap)["pass"]

    certificate_flip = deepcopy(base)
    for node in certificate_flip["nodes"]:
        if node["id"] == "cert:v07:theorem:6_16":
            node.setdefault("attributes", {})["status"] = "FAIL"
            break
    c0 = _identity_audit(certificate_flip)["pass"]
    c1 = _certificate_audit(certificate_flip)["pass"] if c0 else False

    e0 = _identity_audit(base)["pass"]
    e1 = _certificate_audit(base)["pass"] if e0 else False
    e2 = run_e25c(mutate_contract="rank", mutate_view="GEO")["status"] == "PASS" if e1 else False

    return {
        "anchor_swap": {
            "C0_identity": "PASS" if a0 else "FAIL",
            "C1_certificate": "NOT_REACHED" if not a0 else ("PASS" if _certificate_audit(anchor_swap)["pass"] else "FAIL"),
            "C2_executable": "NOT_REACHED" if not a0 else "UNTESTED",
        },
        "certificate_flip": {
            "C0_identity": "PASS" if c0 else "FAIL",
            "C1_certificate": "PASS" if c1 else "FAIL",
            "C2_executable": "NOT_REACHED" if not c1 else "UNTESTED",
        },
        "executable_mutation": {
            "C0_identity": "PASS" if e0 else "FAIL",
            "C1_certificate": "PASS" if e1 else "FAIL",
            "C2_executable": "PASS" if e2 else "FAIL",
        },
    }
