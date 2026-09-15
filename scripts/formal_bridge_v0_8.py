#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import subprocess
from pathlib import Path

FORBIDDEN_PROOF_ESCAPE = re.compile(r"\b(sorry|admit|axiom|unsafe)\b")


def load_json_or_gz(path: Path):
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-graph", type=Path, required=True)
    ap.add_argument("--bindings", type=Path, required=True)
    ap.add_argument("--lean-file", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    graph = load_json_or_gz(args.base_graph)
    bindings = json.loads(args.bindings.read_text(encoding="utf-8"))
    node_by_id = {n["id"]: n for n in graph["nodes"]}

    hash_checks = []
    for b in bindings:
        node = node_by_id.get(b["source_id"])
        actual = None if node is None else node.get("attributes", {}).get("independent_profile", {}).get("statement_sha256")
        ok = actual == b["statement_sha256"]
        hash_checks.append({"source_id": b["source_id"], "expected": b["statement_sha256"], "actual": actual, "pass": ok})
    hashes_ok = all(x["pass"] for x in hash_checks)

    lean_text = args.lean_file.read_text(encoding="utf-8")
    escape_hits = sorted(set(m.group(0) for m in FORBIDDEN_PROOF_ESCAPE.finditer(lean_text)))
    escape_ok = not escape_hits

    decl_presence = {b["lean_decl"]: b["lean_decl"].split(".")[-1] in lean_text for b in bindings}
    declarations_ok = all(decl_presence.values())

    proc = subprocess.run(
        ["lake", "env", "lean", str(args.lean_file)],
        capture_output=True,
        text=True,
        check=False,
    )
    kernel_ok = proc.returncode == 0
    version_proc = subprocess.run(["lake", "env", "lean", "--version"], capture_output=True, text=True, check=False)
    lean_version = (version_proc.stdout or version_proc.stderr).strip().splitlines()[0] if version_proc.returncode == 0 else "UNKNOWN"

    nodes = graph["nodes"]
    edges = graph["edges"]
    existing_node_ids = {n["id"] for n in nodes}
    existing_edge_ids = {e["id"] for e in edges}

    certificates = []
    if kernel_ok and hashes_ok and escape_ok and declarations_ok:
        for b in bindings:
            slug = b["source_id"].replace("srcdecl:", "").replace(":", "_")
            formal_id = f"formal:lean:{slug}"
            cert_id = f"cert:v08:lean:{slug}"
            formal_node = {
                "id": formal_id,
                "type": "REPRESENTATION",
                "label": f"Lean formal representation — {b['kind']} {b['number']}",
                "view": "FORMAL",
                "attributes": {
                    "verifier": "Lean 4",
                    "lean_decl": b["lean_decl"],
                    "formal_scope": b["formal_scope"],
                    "source_statement_sha256": b["statement_sha256"],
                    "lean_file_sha256": sha256_file(args.lean_file),
                    "mathlib_rev": "v4.33.1",
                },
            }
            cert_node = {
                "id": cert_id,
                "type": "CERTIFICATE",
                "label": f"Lean kernel certificate — {b['kind']} {b['number']}",
                "attributes": {
                    "status": "PASS",
                    "certificate_class": "KERNEL_VERIFIED",
                    "verifier": "Lean 4 kernel",
                    "lean_version": lean_version,
                    "lean_decl": b["lean_decl"],
                    "formal_scope": b["formal_scope"],
                    "source_statement_sha256": b["statement_sha256"],
                    "proof_escape_hatches": [],
                },
            }
            for n in (formal_node, cert_node):
                if n["id"] not in existing_node_ids:
                    nodes.append(n)
                    existing_node_ids.add(n["id"])
            new_edges = [
                {"id": f"e:v08:{slug}:formal-represents", "type": "REPRESENTS", "source": formal_id, "target": b["source_id"]},
                {"id": f"e:v08:{slug}:formal-verified", "type": "VERIFIED_BY", "source": formal_id, "target": cert_id},
            ]
            for view in ("eo", "geo"):
                repr_id = f"repr:{view}:{b['source_id'].split(':', 1)[1]}"
                if repr_id in existing_node_ids:
                    new_edges.append({
                        "id": f"e:v08:{slug}:formal-{view}",
                        "type": "EQUIVALENT_TO",
                        "source": formal_id,
                        "target": repr_id,
                        "attributes": {
                            "scope": b["formal_scope"],
                            "evidence": "LEAN_KERNEL_VERIFIED",
                            "source_statement_sha256": b["statement_sha256"],
                        },
                    })
            for e in new_edges:
                if e["id"] not in existing_edge_ids:
                    edges.append(e)
                    existing_edge_ids.add(e["id"])
            certificates.append({
                "source_id": b["source_id"],
                "kind": b["kind"],
                "number": b["number"],
                "lean_decl": b["lean_decl"],
                "formal_scope": b["formal_scope"],
                "status": "PASS",
                "certificate_class": "KERNEL_VERIFIED",
                "source_statement_sha256": b["statement_sha256"],
            })

    node_ids = [n["id"] for n in nodes]
    edge_ids = [e["id"] for e in edges]
    by = {n["id"]: n for n in nodes}
    graph_checks = {
        "unique_node_ids": len(node_ids) == len(set(node_ids)),
        "unique_edge_ids": len(edge_ids) == len(set(edge_ids)),
        "all_edge_endpoints_exist": all(e["source"] in by and e["target"] in by for e in edges),
        "base_graph_extended": len(nodes) >= 2226 and len(edges) >= 23305,
    }

    gates = {
        "source_hashes_match": hashes_ok,
        "no_proof_escape_hatches": escape_ok,
        "formal_declarations_present": declarations_ok,
        "lean_kernel_check": kernel_ok,
        "four_kernel_certificates": len(certificates) == 4,
        **graph_checks,
    }
    status = "PASS" if all(gates.values()) else "FAIL"

    report = {
        "test_id": "MAPEOGEO-FORMAL-VERIFIER-BRIDGE-V0.8",
        "status": status,
        "overall_goal": "One source-grounded mathematical graph with source topology, EO, GEO, executable certificates, FORMAL representations, and eventual proof-kernel-verified proof paths.",
        "source": {
            "redistributed": False,
            "copyright_payload_policy": "HASHED_LOCATOR_METADATA_ONLY",
        },
        "formal_verifier": {
            "lean_version": lean_version,
            "mathlib_rev": "v4.33.1",
            "lean_file_sha256": sha256_file(args.lean_file),
            "kernel_process_returncode": proc.returncode,
            "kernel_stdout_sha256": hashlib.sha256(proc.stdout.encode()).hexdigest(),
            "kernel_stderr_sha256": hashlib.sha256(proc.stderr.encode()).hexdigest(),
            "proof_escape_hits": escape_hits,
        },
        "source_hash_checks": hash_checks,
        "formal_declaration_presence": decl_presence,
        "kernel_certificates": len(certificates),
        "formal_coverage_of_v07_source_bound_set": len(certificates) / len(bindings),
        "graph": {"nodes": len(nodes), "edges": len(edges)},
        "gates": gates,
        "claim_boundary": "v0.8 demonstrates a working source->EO/GEO->certificate->Lean formal representation->kernel verification bridge for the four v0.7 source-bound declarations. It does not establish whole-corpus autoformalization or universal EO/GEO equivalence.",
    }

    (args.out_dir / "formal_bridge_v0_8_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (args.out_dir / "formal_kernel_certificates_v0_8.json").write_text(json.dumps(certificates, indent=2), encoding="utf-8")
    with gzip.open(args.out_dir / "mapeogeo_formal_v0_8_graph.json.gz", "wt", encoding="utf-8") as f:
        json.dump(graph, f, separators=(",", ":"), sort_keys=True)

    summary = f"""# MAPEOGEO v0.8 — Formal-Verifier Bridge\n\n**Status: {status}**\n\n- Source-bound declarations: {len(bindings)}\n- Source hashes matched: {sum(x['pass'] for x in hash_checks)} / {len(bindings)}\n- Lean kernel check: {'PASS' if kernel_ok else 'FAIL'}\n- Prohibited proof escape hatches: {len(escape_hits)}\n- Kernel-verified certificates: {len(certificates)} / {len(bindings)}\n- Formal coverage of v0.7 source-bound set: {len(certificates)/len(bindings):.2%}\n- Graph: {len(nodes)} nodes / {len(edges)} edges\n- Lean: {lean_version}\n\nThis stage establishes the formal-verifier bridge only. Whole-corpus autoformalization remains the next major problem.\n"""
    (args.out_dir / "V0_8_SUMMARY.md").write_text(summary, encoding="utf-8")

    print(f"MAPEOGEO_V0_8: {status} hashes={sum(x['pass'] for x in hash_checks)}/{len(bindings)} kernel={'PASS' if kernel_ok else 'FAIL'} certs={len(certificates)}/{len(bindings)} graph={len(nodes)}/{len(edges)}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
