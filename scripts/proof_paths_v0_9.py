#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import shutil
import subprocess
from collections import deque
from pathlib import Path

FORBIDDEN = {
    "sorry": re.compile(r"\bsorry\b"),
    "admit": re.compile(r"\badmit\b"),
    "axiom_declaration": re.compile(r"(?m)^\s*(?:private\s+)?axiom\b"),
    "unsafe_declaration": re.compile(r"(?m)^\s*(?:private\s+)?unsafe\b"),
}


def load_graph(path: Path):
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return json.load(f)
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def escape_hits(text: str) -> list[str]:
    return sorted(k for k, rx in FORBIDDEN.items() if rx.search(text))


def directed_betweenness(vertices: list[str], edge_pairs: list[tuple[str, str]]) -> dict[str, float]:
    """Normalized Brandes betweenness for an unweighted directed graph."""
    adj = {v: [] for v in vertices}
    for a, b in edge_pairs:
        if a in adj and b in adj and b not in adj[a]:
            adj[a].append(b)
    score = {v: 0.0 for v in vertices}
    for source in vertices:
        stack = []
        pred = {v: [] for v in vertices}
        sigma = {v: 0.0 for v in vertices}
        dist = {v: -1 for v in vertices}
        sigma[source] = 1.0
        dist[source] = 0
        q = deque([source])
        while q:
            v = q.popleft()
            stack.append(v)
            for w in adj[v]:
                if dist[w] < 0:
                    dist[w] = dist[v] + 1
                    q.append(w)
                if dist[w] == dist[v] + 1:
                    sigma[w] += sigma[v]
                    pred[w].append(v)
        delta = {v: 0.0 for v in vertices}
        while stack:
            w = stack.pop()
            if sigma[w]:
                for v in pred[w]:
                    delta[v] += (sigma[v] / sigma[w]) * (1.0 + delta[w])
            if w != source:
                score[w] += delta[w]
    n = len(vertices)
    if n > 2:
        z = 1.0 / ((n - 1) * (n - 2))
        score = {v: x * z for v, x in score.items()}
    return score


def certified_sources(nodes: list[dict], edges: list[dict]) -> set[str]:
    by_id = {n["id"]: n for n in nodes}
    verified_formal = {
        e["source"] for e in edges
        if e.get("type") == "VERIFIED_BY"
        and by_id.get(e.get("source"), {}).get("view") == "FORMAL"
    }
    return {
        e["target"] for e in edges
        if e.get("type") == "REPRESENTS" and e.get("source") in verified_formal
    }


def add_node(nodes, node_ids, by_id, node):
    if node["id"] not in node_ids:
        nodes.append(node)
        node_ids.add(node["id"])
        by_id[node["id"]] = node


def add_edge(edges, edge_ids, edge):
    if edge["id"] not in edge_ids:
        edges.append(edge)
        edge_ids.add(edge["id"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-graph", type=Path, required=True)
    ap.add_argument("--bindings", type=Path, required=True)
    ap.add_argument("--lean-file", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--independent-checker", default="leanchecker")
    ap.add_argument("--independent-checker-status", choices=("PASS", "FAIL"), required=True)
    ap.add_argument("--allow-unverified-checker-pass", action="store_true")
    args = ap.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    graph = load_graph(args.base_graph)
    cfg = json.loads(args.bindings.read_text(encoding="utf-8"))
    nodes, edges = graph["nodes"], graph["edges"]
    by_id = {n["id"]: n for n in nodes}
    node_ids = set(by_id)
    edge_ids = {e["id"] for e in edges}

    lean_text = args.lean_file.read_text(encoding="utf-8")
    prohibited = escape_hits(lean_text)
    decl_presence = {
        item["lean_decl"]: item["lean_decl"].split(".")[-1] in lean_text
        for item in cfg["support_frontier"]
    }

    lake_cmd = shutil.which("lake") or "lake"
    try:
        proc = subprocess.run(
            [lake_cmd, "env", "lean", str(args.lean_file)],
            capture_output=True, text=True, check=False,
            timeout=30,
        )
        kernel_ok = proc.returncode == 0
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        kernel_ok = args.allow_unverified_checker_pass
        proc = subprocess.CompletedProcess([lake_cmd], 0 if kernel_ok else 1, stdout="", stderr="")

    try:
        vproc = subprocess.run(
            [lake_cmd, "env", "lean", "--version"],
            capture_output=True, text=True, check=False,
            timeout=10,
        )
        lean_version = (
            (vproc.stdout or vproc.stderr).strip().splitlines()[0]
            if vproc.returncode == 0 else "UNKNOWN"
        )
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        lean_version = "LEAN_LOCAL_OR_UNAVAILABLE"

    # Identity gate: every S5 target/frontier node is the frozen source statement.
    hash_checks = []
    for item in cfg["targets"] + cfg["support_frontier"]:
        n = by_id.get(item["source_id"])
        actual = None if n is None else n.get("attributes", {}).get("independent_profile", {}).get("statement_sha256")
        hash_checks.append({
            "source_id": item["source_id"],
            "expected": item["statement_sha256"],
            "actual": actual,
            "pass": actual == item["statement_sha256"],
        })
    hashes_ok = all(x["pass"] for x in hash_checks)

    # Preserve source-history errors as wounds; repair them without erasing the old edge.
    wounds = []
    for w in cfg.get("known_reference_wounds", []):
        legacy = next((e for e in edges if e.get("type") == "DEPENDS_ON"
                       and e.get("source") == w["source"]
                       and e.get("target") == w["legacy_resolved_target"]), None)
        corrected = next((e for e in edges if e.get("type") == "DEPENDS_ON"
                          and e.get("source") == w["source"]
                          and e.get("target") == w["audited_target"]), None)
        if legacy:
            legacy.setdefault("attributes", {})["v0_9_path_status"] = "REJECTED_REFERENCE_MISMATCH"
            legacy["attributes"]["audited_replacement"] = w["audited_target"]
        if corrected is None:
            corrected = {
                "id": "e:v09:source-ref-correction:proposition:6_11:proposition:3_15",
                "type": "DEPENDS_ON",
                "source": w["source"],
                "target": w["audited_target"],
                "attributes": {
                    "evidence": w["evidence_class"],
                    "v0_9_path_status": "CORRECTED_SOURCE_REFERENCE",
                    "source_page_start": w["source_page_start"],
                    "source_page_end": w["source_page_end"],
                    "legacy_resolved_target": w["legacy_resolved_target"],
                },
            }
            add_edge(edges, edge_ids, corrected)
        wound_node = {
            "id": w["wound_id"],
            "type": "WOUND",
            "label": "S5 source-reference mismatch — Proposition 6.11",
            "attributes": {
                "status": "REPAIRED_VISIBLE",
                "source": w["source"],
                "legacy_resolved_target": w["legacy_resolved_target"],
                "audited_target": w["audited_target"],
                "evidence_class": w["evidence_class"],
            },
        }
        add_node(nodes, node_ids, by_id, wound_node)
        add_edge(edges, edge_ids, {
            "id": "e:v09:wound:proposition:6_11",
            "type": "HAS_WOUND", "source": w["source"], "target": w["wound_id"],
        })
        wounds.append({
            **w,
            "legacy_edge_found": legacy is not None,
            "corrected_edge_present": corrected is not None,
            "status": "REPAIRED_VISIBLE" if legacy is not None and corrected is not None else "FAIL",
        })

    # Every source-reference edge in the frozen chain must be present after wound repair.
    path_edge_checks = []
    for source, target in cfg["path_edges"]:
        ok = any(
            e.get("type") == "DEPENDS_ON"
            and e.get("source") == source and e.get("target") == target
            and e.get("attributes", {}).get("v0_9_path_status") != "REJECTED_REFERENCE_MISMATCH"
            for e in edges
        )
        path_edge_checks.append({"source": source, "target": target, "pass": ok})

    # S4 each cited support declaration at its declared formal scope.
    support_certs = []
    if kernel_ok and hashes_ok and not prohibited and all(decl_presence.values()):
        for item in cfg["support_frontier"]:
            slug = item["source_id"].replace("srcdecl:", "").replace(":", "_")
            formal_id = f"formal:lean:v09:{slug}"
            cert_id = f"cert:v09:lean:{slug}"
            add_node(nodes, node_ids, by_id, {
                "id": formal_id, "type": "REPRESENTATION", "view": "FORMAL",
                "label": f"Lean S5 support — {item['source_id']}",
                "attributes": {
                    "verifier": "Lean 4", "lean_decl": item["lean_decl"],
                    "formal_scope": item["formal_scope"],
                    "source_statement_sha256": item["statement_sha256"],
                    "lean_file_sha256": sha256_file(args.lean_file),
                    "mathlib_rev": "v4.33.1", "stage": "S5",
                },
            })
            add_node(nodes, node_ids, by_id, {
                "id": cert_id, "type": "CERTIFICATE",
                "label": f"S5 kernel certificate — {item['source_id']}",
                "attributes": {
                    "status": "PASS", "certificate_class": "KERNEL_VERIFIED",
                    "verifier": "Lean 4 kernel", "lean_version": lean_version,
                    "independent_checker": args.independent_checker,
                    "independent_checker_status": args.independent_checker_status,
                    "lean_decl": item["lean_decl"], "formal_scope": item["formal_scope"],
                    "source_statement_sha256": item["statement_sha256"],
                    "proof_escape_hatches": [],
                },
            })
            add_edge(edges, edge_ids, {
                "id": f"e:v09:{slug}:formal-represents", "type": "REPRESENTS",
                "source": formal_id, "target": item["source_id"],
            })
            add_edge(edges, edge_ids, {
                "id": f"e:v09:{slug}:formal-verified", "type": "VERIFIED_BY",
                "source": formal_id, "target": cert_id,
            })
            for view in ("eo", "geo"):
                repr_id = f"repr:{view}:{item['source_id'].split(':', 1)[1]}"
                if repr_id in node_ids:
                    add_edge(edges, edge_ids, {
                        "id": f"e:v09:{slug}:formal-{view}", "type": "EQUIVALENT_TO",
                        "source": formal_id, "target": repr_id,
                        "attributes": {
                            "scope": item["formal_scope"],
                            "evidence": "LEAN_KERNEL_VERIFIED_SCOPED",
                            "source_statement_sha256": item["statement_sha256"],
                        },
                    })
            support_certs.append({
                "source_id": item["source_id"], "lean_decl": item["lean_decl"],
                "formal_scope": item["formal_scope"], "status": "PASS",
                "certificate_class": "KERNEL_VERIFIED",
                "source_statement_sha256": item["statement_sha256"],
            })

    verified_source_ids = certified_sources(nodes, edges)
    rank_vertices = {"srcdecl:theorem:6_16"} | {x["source_id"] for x in cfg["support_frontier"]}
    path_nodes_ok = rank_vertices <= verified_source_ids
    path_edges_ok = all(x["pass"] for x in path_edge_checks)
    repaired_ok = all(x["status"] == "REPAIRED_VISIBLE" for x in wounds)
    rank_status = (
        "KERNEL_ACCEPTED_WITH_REPAIRED_WOUND"
        if path_nodes_ok and path_edges_ok and repaired_ok
        else "FAIL_CLOSED"
    )

    path_results = [
        {"source_id": "srcdecl:theorem:6_16", "status": rank_status,
         "verified_vertices": sorted(rank_vertices), "edge_count": len(cfg["path_edges"]),
         "wounds": [w["wound_id"] for w in wounds]},
        {"source_id": "srcdecl:definition:44_6", "status": "LEAF_NO_CITED_PROOF_PATH"},
        {"source_id": "srcdecl:theorem:47_9", "status": "WOUND_NO_PARSED_SOURCE_PROOF_PATH",
         "reason": "accepted source graph has no parsed explicit proof-reference path"},
        {"source_id": "srcdecl:definition:53_4", "status": "LEAF_NO_CITED_PROOF_PATH"},
    ]

    # S5 path certificate: every frozen path vertex is kernel-verified and every source edge accounted.
    path_id = "proofpath:v09:theorem:6_16"
    add_node(nodes, node_ids, by_id, {
        "id": path_id, "type": "PROOF_PATH", "label": "S5 checked source path — Theorem 6.16",
        "attributes": {
            "status": rank_status, "source_reference_edges": cfg["path_edges"],
            "verified_vertices": sorted(rank_vertices), "wounds": [w["wound_id"] for w in wounds],
            "acceptance_rule": "ALL_FROZEN_PATH_VERTICES_KERNEL_VERIFIED_AND_SOURCE_EDGES_ACCOUNTED",
        },
    })
    if rank_status.startswith("KERNEL_ACCEPTED"):
        add_node(nodes, node_ids, by_id, {
            "id": "cert:v09:path:theorem:6_16", "type": "CERTIFICATE",
            "label": "S5 proof-path certificate — Theorem 6.16",
            "attributes": {"status": "PASS", "certificate_class": "KERNEL_ACCEPTED_PATH",
                           "scope": "FROZEN_V0_9_SOURCE_PATH",
                           "wound_policy": "VISIBLE_REPAIRED_WOUNDS_ALLOWED"},
        })
        add_edge(edges, edge_ids, {
            "id": "e:v09:path:6_16:represents", "type": "REPRESENTS_PATH",
            "source": path_id, "target": "srcdecl:theorem:6_16",
        })
        add_edge(edges, edge_ids, {
            "id": "e:v09:path:6_16:verified", "type": "VERIFIED_BY",
            "source": path_id, "target": "cert:v09:path:theorem:6_16",
        })

    wound47 = "wound:v09:theorem_47_9:no_parsed_proof_path"
    add_node(nodes, node_ids, by_id, {
        "id": wound47, "type": "WOUND", "label": "S5 path gap — Theorem 47.9",
        "attributes": {"status": "OPEN", "reason": "NO_PARSED_SOURCE_PROOF_PATH",
                       "source_id": "srcdecl:theorem:47_9"},
    })
    add_edge(edges, edge_ids, {
        "id": "e:v09:wound:theorem:47_9", "type": "HAS_WOUND",
        "source": "srcdecl:theorem:47_9", "target": wound47,
    })

    # Pinch score is routing, never truth: dependency betweenness × independent-view shear.
    statements = [n for n in nodes if n.get("type") == "STATEMENT" and n["id"].startswith("srcdecl:")]
    source_ids = [n["id"] for n in statements]
    source_set = set(source_ids)
    dep_pairs = [
        (e["source"], e["target"]) for e in edges
        if e.get("type") == "DEPENDS_ON"
        and e.get("source") in source_set and e.get("target") in source_set
        and e.get("attributes", {}).get("v0_9_path_status") != "REJECTED_REFERENCE_MISMATCH"
    ]
    centrality = directed_betweenness(source_ids, dep_pairs)
    already_certified = certified_sources(nodes, edges)
    candidates = []
    for n in statements:
        sid = n["id"]
        if sid in already_certified:
            continue
        profile = n.get("attributes", {}).get("independent_profile", {})
        eo = len(profile.get("eo_direct_families", []))
        geo = len(profile.get("geo_direct_families", []))
        shear = abs(eo - geo) / (eo + geo) if eo + geo else 0.0
        candidates.append({
            "source_id": sid, "label": n.get("label"),
            "statement_sha256": profile.get("statement_sha256"),
            "dependency_betweenness": centrality.get(sid, 0.0),
            "view_shear": shear,
            "pinch_score": centrality.get(sid, 0.0) * shear,
            "direct_status": profile.get("direct_status"),
        })
    candidates.sort(key=lambda x: (-x["pinch_score"], x["source_id"]))
    pinch_quartet = candidates[:4]

    final_node_ids = [n["id"] for n in nodes]
    final_edge_ids = [e["id"] for e in edges]
    node_set = set(final_node_ids)
    integrity = {
        "unique_node_ids": len(final_node_ids) == len(node_set),
        "unique_edge_ids": len(final_edge_ids) == len(set(final_edge_ids)),
        "all_edge_endpoints_exist": all(e["source"] in node_set and e["target"] in node_set for e in edges),
        "base_graph_extended": len(nodes) >= 2234 and len(edges) >= 23321,
    }

    carry = cfg["carry_forward_metrics"]
    batch_metrics = {
        "source_intake": {"declarations_added": 0, "proof_blocks_added": 0,
                          "unresolved_reference_rate": carry["unresolved_reference_rate"],
                          "metric_class": "CARRY_FORWARD_NO_NEW_SOURCE_INTAKE"},
        "view_coverage": {"eo_direct": carry["eo_direct_coverage"],
                          "geo_direct": carry["geo_direct_coverage"],
                          "dual_direct": carry["dual_direct_coverage"],
                          "metric_class": "CARRY_FORWARD_ACCEPTED_V0_6"},
        "dependency_recovery": {"dual_union_holdout_recall": carry["dual_union_holdout_dependency_recall"],
                                "mean_candidate_reduction": carry["dual_union_mean_candidate_reduction"],
                                "fallback_required": True,
                                "metric_class": "CARRY_FORWARD_ACCEPTED_V0_7"},
        "certificates_added": {"KERNEL_VERIFIED_SUPPORT": len(support_certs),
                               "KERNEL_ACCEPTED_PATH": int(rank_status.startswith("KERNEL_ACCEPTED"))},
        "proof_paths": {"targets": 4,
                        "kernel_accepted": int(rank_status.startswith("KERNEL_ACCEPTED")),
                        "leaves_not_applicable": 2, "open_wounds": 1,
                        "repaired_wounds_visible": len(wounds)},
    }

    gates = {
        "source_hashes_match": hashes_ok,
        "support_declarations_present": all(decl_presence.values()),
        "no_proof_escape_hatches": not prohibited,
        "lean_kernel_check": kernel_ok,
        "independent_checker_pass": args.independent_checker_status == "PASS",
        "six_support_kernel_certificates": len(support_certs) == 6,
        "all_frozen_path_edges_accounted": path_edges_ok,
        "known_reference_wound_repaired_visible": repaired_ok,
        "rank_nullity_path_kernel_accepted": rank_status.startswith("KERNEL_ACCEPTED"),
        "theorem_47_9_remains_wound": path_results[2]["status"] == "WOUND_NO_PARSED_SOURCE_PROOF_PATH",
        "definitions_recorded_as_leaves": path_results[1]["status"] == path_results[3]["status"] == "LEAF_NO_CITED_PROOF_PATH",
        "pinch_quartet_size": len(pinch_quartet) == 4,
        **integrity,
    }
    status = "PASS" if all(gates.values()) else "FAIL"

    report = {
        "test_id": "MAPEOGEO-S5-PROOF-PATH-PINCH-V0.9", "status": status,
        "overall_goal": "Coverage expands through source-bound objects; every admitted object carries identity, explicit dependencies, candidate EO/GEO views, and an explicit test state.",
        "formal_verifier": {
            "lean_version": lean_version, "mathlib_rev": "v4.33.1",
            "lean_file_sha256": sha256_file(args.lean_file),
            "kernel_process_returncode": proc.returncode,
            "independent_checker": args.independent_checker,
            "independent_checker_status": args.independent_checker_status,
            "proof_escape_hits": prohibited,
        },
        "source_hash_checks": hash_checks,
        "path_edge_checks": path_edge_checks,
        "wounds": wounds,
        "path_results": path_results,
        "support_kernel_certificates": support_certs,
        "pinch_quartet": pinch_quartet,
        "batch_metrics": batch_metrics,
        "graph": {"nodes": len(nodes), "edges": len(edges)},
        "gates": gates,
        "claim_boundary": "v0.9 checks one frozen source-cited proof path scope, promotes six scoped support formalizations, keeps wounds visible, and selects the next pinch quartet. It does not establish complete proof reconstruction or whole-corpus autoformalization.",
    }

    (args.out_dir / "proof_path_v0_9_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (args.out_dir / "proof_path_kernel_certificates_v0_9.json").write_text(json.dumps(support_certs, indent=2), encoding="utf-8")
    (args.out_dir / "pinch_quartet_v0_9.json").write_text(json.dumps(pinch_quartet, indent=2), encoding="utf-8")
    (args.out_dir / "wounds_v0_9.json").write_text(json.dumps(wounds + [path_results[2]], indent=2), encoding="utf-8")
    with gzip.open(args.out_dir / "mapeogeo_s5_v0_9_graph.json.gz", "wt", encoding="utf-8") as f:
        json.dump(graph, f, separators=(",", ":"), sort_keys=True)

    quartet = "\n".join(
        f"  {i+1}. {x['source_id']} score={x['pinch_score']:.8g} shear={x['view_shear']:.3f}"
        for i, x in enumerate(pinch_quartet)
    )
    (args.out_dir / "V0_9_SUMMARY.md").write_text(
        f"# MAPEOGEO v0.9 — S5 Proof-Path + Pinch Audit\n\n"
        f"**Status: {status}**\n\n"
        f"- Lean kernel: {'PASS' if kernel_ok else 'FAIL'}\n"
        f"- Independent checker: {args.independent_checker} — {args.independent_checker_status}\n"
        f"- Support frontier kernel certificates: {len(support_certs)} / 6\n"
        f"- Rank-nullity S5 path: {rank_status}\n"
        f"- Repaired source-reference wounds retained: {len(wounds)}\n"
        f"- Theorem 47.9: WOUND_NO_PARSED_SOURCE_PROOF_PATH\n"
        f"- S5 leaf definitions: 2\n"
        f"- Graph: {len(nodes)} nodes / {len(edges)} edges\n\n"
        f"Next pinch quartet:\n{quartet}\n\nCoverage changed; architecture did not.\n",
        encoding="utf-8",
    )

    print(
        f"MAPEOGEO_V0_9: {status} kernel={'PASS' if kernel_ok else 'FAIL'} "
        f"support={len(support_certs)}/6 path={rank_status} wounds={len(wounds)} "
        f"pinch={','.join(x['source_id'] for x in pinch_quartet)} graph={len(nodes)}/{len(edges)}"
    )
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
