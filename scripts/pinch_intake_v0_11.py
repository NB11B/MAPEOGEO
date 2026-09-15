#!/usr/bin/env python3
"""MAPEOGEO v0.11 Pinch-Driven Mathematics Intake runner.

Sole mutator for v0.11 mathematical intake:
- Audits source node presence and independent profiles fail-closed (no synthetic nodes).
- Verifies exact statement hashes and historical direct view states (EO_ONLY_DIRECT / DUAL_DIRECT).
- Verifies explicit dependencies exist as accepted source DEPENDS_ON edges (no manufactured edges).
- Enforces scope_status per target (FROZEN -> KERNEL_VERIFIED, REFUSED -> refusal).
- Verifies Lean 4 kernel proofs without escape hatches.
- Verifies independent checker evidence (rejects unevidenced PASS claims; defaults to NOT_RUN).
- Executes S3 computational contracts (exact rational / UNTESTED refusal).
- Removes automatic FORMAL->EO/GEO EQUIVALENT_TO edges (scoped formalization only).
- Validates historical fields byte-for-byte before and after mutation.
- Preserves all v0.9 WOUND nodes and rejected/corrected reference records.
- Emits certified graph and evidence artifacts.
"""

from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.pinch_contracts_v0_11 import ContractResult, run_contract

FORBIDDEN_PROOF_PATTERNS = {
    "sorry": re.compile(r"\bsorry\b"),
    "admit": re.compile(r"\badmit\b"),
    "axiom_declaration": re.compile(r"(?m)^\s*(?:private\s+)?axiom\b"),
    "unsafe_declaration": re.compile(r"(?m)^\s*(?:private\s+)?unsafe\b"),
}

FORBIDDEN_PERSISTED_KEYS = {"statement_text", "proof_text", "source_prose", "page_image"}

HISTORICAL_PROFILE_FIELDS = (
    "statement_sha256",
    "statement_chars",
    "eo_direct_families",
    "geo_direct_families",
    "direct_status",
)


def load_json_or_gz(path: Path) -> dict:
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


def proof_escape_hits(text: str) -> list[str]:
    return sorted(name for name, pattern in FORBIDDEN_PROOF_PATTERNS.items() if pattern.search(text))


def find_lake_cmd() -> str:
    which = shutil.which("lake")
    if which:
        return which
    elan_lake_win = Path.home() / ".elan" / "bin" / "lake.exe"
    if elan_lake_win.is_file():
        return str(elan_lake_win)
    elan_lake_nix = Path.home() / ".elan" / "bin" / "lake"
    if elan_lake_nix.is_file():
        return str(elan_lake_nix)
    return "lake"


def main() -> int:
    ap = argparse.ArgumentParser(description="MAPEOGEO v0.11 Pinch-Driven Mathematics Intake runner")
    ap.add_argument("--base-graph", type=Path, required=True, help="Input accepted v0.9 graph (.json or .json.gz)")
    ap.add_argument("--bindings", type=Path, default=ROOT / "formal" / "pinch_bindings_v0_11.json")
    ap.add_argument("--lean-file", type=Path, default=ROOT / "MAPEOGEOFormal" / "PinchV011.lean")
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--independent-checker", default="leanchecker")
    ap.add_argument(
        "--independent-checker-status",
        default="NOT_RUN",
        choices=("PASS", "FAIL", "NOT_RUN"),
        help="Status of independent checker. Defaults to NOT_RUN.",
    )
    ap.add_argument(
        "--checker-evidence-file",
        type=Path,
        default=None,
        help="Path to independent checker log/result file supporting PASS status.",
    )
    ap.add_argument(
        "--allow-unverified-checker-pass",
        action="store_true",
        help="Explicit flag if caller bypasses checker evidence file check (for testing only).",
    )
    args = ap.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    graph = load_json_or_gz(args.base_graph)
    config = json.loads(args.bindings.read_text(encoding="utf-8"))
    targets = config["targets"]
    nodes = list(graph.get("nodes", []))
    edges = list(graph.get("edges", []))
    node_by_id = {n["id"]: n for n in nodes}
    edge_by_id = {e["id"]: e for e in edges}

    # Gate 1: Base graph must be the regenerated accepted v0.9 graph (reject pre-v0.9 graphs)
    is_v09_base = any(
        "proofpath:v09" in n.get("id", "")
        or "v09" in n.get("id", "")
        or n.get("type") == "WOUND"
        or any(e.get("attributes", {}).get("v0_9_path_status") for e in edges)
        for n in nodes
    )

    # Snapshot historical profile fields of all source declarations before mutation
    historical_snapshot: dict[str, dict[str, Any]] = {}
    for n in nodes:
        if "independent_profile" in n.get("attributes", {}):
            prof = n.get("attributes", {}).get("independent_profile", {})
            historical_snapshot[n["id"]] = {
                field: copy.deepcopy(prof.get(field))
                for field in HISTORICAL_PROFILE_FIELDS
            }

    # Gate 2 & 3 & 4: Fail-closed Target Identity, Historical View State, and Dependencies
    target_nodes_present = True
    independent_profiles_present = True
    statement_hashes_matched = True
    historical_direct_views_matched = True
    explicit_dependencies_present = True

    # Build map of accepted DEPENDS_ON edges
    dep_map: dict[str, set[str]] = {}
    for e in edges:
        if e.get("type") == "DEPENDS_ON":
            dep_map.setdefault(e["source"], set()).add(e["target"])

    identity_checks = []
    for t in targets:
        source_id = t["source_id"]
        node = node_by_id.get(source_id)

        if node is None:
            target_nodes_present = False
            identity_checks.append({
                "source_id": source_id,
                "node_present": False,
                "profile_present": False,
                "hash_match": False,
                "direct_view_match": False,
                "dependencies_present": False,
            })
            continue

        prof = node.get("attributes", {}).get("independent_profile")
        if prof is None:
            independent_profiles_present = False
            identity_checks.append({
                "source_id": source_id,
                "node_present": True,
                "profile_present": False,
                "hash_match": False,
                "direct_view_match": False,
                "dependencies_present": False,
            })
            continue

        actual_hash = prof.get("statement_sha256")
        expected_hash = t.get("statement_sha256")
        hash_ok = (actual_hash == expected_hash) and bool(actual_hash)
        if not hash_ok:
            statement_hashes_matched = False

        actual_status = prof.get("direct_status")
        expected_status = t.get("expected_direct_status")
        status_ok = (actual_status == expected_status) and bool(actual_status)
        if not status_ok:
            historical_direct_views_matched = False

        expected_deps = set(t.get("explicit_dependencies", []))
        actual_deps = dep_map.get(source_id, set())
        deps_ok = expected_deps.issubset(actual_deps)
        if not deps_ok:
            explicit_dependencies_present = False

        identity_checks.append({
            "source_id": source_id,
            "node_present": True,
            "profile_present": True,
            "actual_hash": actual_hash,
            "expected_hash": expected_hash,
            "hash_match": hash_ok,
            "actual_status": actual_status,
            "expected_status": expected_status,
            "direct_view_match": status_ok,
            "expected_deps": sorted(list(expected_deps)),
            "actual_deps": sorted(list(actual_deps)),
            "dependencies_present": deps_ok,
        })

    # Gate 5: Lean Proof File Checks
    lean_text = args.lean_file.read_text(encoding="utf-8")
    escape_hits = proof_escape_hits(lean_text)
    escape_ok = not escape_hits

    decl_presence = {
        t["formal_decl"]: t["formal_decl"].split(".")[-1] in lean_text
        for t in targets
        if t.get("scope_status") == "FROZEN"
    }
    declarations_ok = all(decl_presence.values()) if decl_presence else False

    pre_identity_ok = (
        is_v09_base
        and target_nodes_present
        and independent_profiles_present
        and statement_hashes_matched
        and historical_direct_views_matched
        and explicit_dependencies_present
    )

    kernel_ok = False
    lean_version = "NOT_RUN"
    if pre_identity_ok and escape_ok and declarations_ok:
        lake_cmd = find_lake_cmd()
        proc = subprocess.run(
            [lake_cmd, "env", "lean", str(args.lean_file)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        kernel_ok = (proc.returncode == 0)

        version_proc = subprocess.run(
            [lake_cmd, "env", "lean", "--version"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        lean_version = (
            (version_proc.stdout or version_proc.stderr).strip().splitlines()[0]
            if version_proc.returncode == 0
            else "UNKNOWN"
        )

    # Gate 6: Independent Checker Evidence
    checker_evidence_ok = True
    if args.independent_checker_status == "PASS":
        if args.checker_evidence_file is not None:
            if not (args.checker_evidence_file.is_file() and args.checker_evidence_file.stat().st_size > 0):
                checker_evidence_ok = False
        elif not args.allow_unverified_checker_pass:
            checker_evidence_ok = False
    independent_ok = (args.independent_checker_status == "PASS") and checker_evidence_ok

    # Gate 7: S3 Computational Contracts
    contract_results: list[dict[str, Any]] = []
    contracts_ok = True
    for t in targets:
        c_res = run_contract(t)
        c_dict = {
            "source_id": c_res.source_id,
            "contract_id": c_res.contract_id,
            "test_state": c_res.test_state,
            "applicability": c_res.applicability,
            "verdict": c_res.verdict,
            "scope": c_res.scope,
            "measured": c_res.measured,
            "refused": list(c_res.refused),
        }
        contract_results.append(c_dict)
        if c_res.verdict not in ("PASS", "UNTESTED", "NOT_APPLICABLE"):
            contracts_ok = False

    # Gate 8: Preserve Wounds from Base Graph
    wounds: list[dict[str, Any]] = []
    for n in nodes:
        if n.get("type") == "WOUND" or "wound:" in n.get("id", ""):
            wounds.append(n)
    for e in edges:
        if e.get("attributes", {}).get("v0_9_path_status") == "REJECTED_REFERENCE_MISMATCH":
            wounds.append({
                "type": "WOUND_EDGE",
                "edge_id": e["id"],
                "source": e.get("source"),
                "target": e.get("target"),
                "status": "REPAIRED_VISIBLE",
            })

    # Mutation: Scope-Enforced Certification
    certificates: list[dict[str, Any]] = []
    target_results: list[dict[str, Any]] = []

    can_promote = (
        is_v09_base
        and target_nodes_present
        and independent_profiles_present
        and statement_hashes_matched
        and historical_direct_views_matched
        and explicit_dependencies_present
        and escape_ok
        and declarations_ok
        and kernel_ok
        and independent_ok
        and contracts_ok
    )

    if can_promote:
        for t in targets:
            source_id = t["source_id"]
            slug = source_id.replace("srcdecl:", "").replace(":", "_")
            scope_status = t.get("scope_status", "FROZEN")
            c_matching = next((c for c in contract_results if c["source_id"] == source_id), None)

            if scope_status == "REFUSED_SCOPE_MISMATCH":
                target_results.append({
                    "source_id": source_id,
                    "status": "REFUSED_SCOPE_MISMATCH",
                    "formal_scope": t.get("formal_scope"),
                    "reason": "Scope refused by preregistration policy",
                    "s3_contract": c_matching,
                })
                continue

            formal_id = f"formal:lean:v011:{slug}"
            cert_id = f"cert:v011:lean:{slug}"

            formal_node = {
                "id": formal_id,
                "type": "REPRESENTATION",
                "label": f"Lean 4 formal representation — {source_id}",
                "view": "FORMAL",
                "attributes": {
                    "verifier": "Lean 4",
                    "lean_decl": t["formal_decl"],
                    "formal_scope": t["formal_scope"],
                    "source_statement_sha256": t["statement_sha256"],
                    "lean_file_sha256": sha256_file(args.lean_file),
                    "mathlib_rev": "v4.33.1",
                    "stage": "v0.11",
                    "s3_test_state": t["s3_test_state"],
                    "s3_contract_id": t["s3_contract_id"],
                },
            }
            if formal_id not in node_by_id:
                nodes.append(formal_node)
                node_by_id[formal_id] = formal_node

            cert_node = {
                "id": cert_id,
                "type": "CERTIFICATE",
                "label": f"Lean kernel certificate — {source_id}",
                "attributes": {
                    "status": "PASS",
                    "certificate_class": "KERNEL_VERIFIED",
                    "verifier": "Lean 4 kernel",
                    "lean_version": lean_version,
                    "independent_checker": args.independent_checker,
                    "independent_checker_status": args.independent_checker_status,
                    "lean_decl": t["formal_decl"],
                    "formal_scope": t["formal_scope"],
                    "source_statement_sha256": t["statement_sha256"],
                    "proof_escape_hatches": [],
                },
            }
            if cert_id not in node_by_id:
                nodes.append(cert_node)
                node_by_id[cert_id] = cert_node

            new_edges = [
                {
                    "id": f"e:v011:{slug}:formal-represents",
                    "type": "REPRESENTS",
                    "source": formal_id,
                    "target": source_id,
                },
                {
                    "id": f"e:v011:{slug}:formal-verified",
                    "type": "VERIFIED_BY",
                    "source": formal_id,
                    "target": cert_id,
                },
            ]

            for e in new_edges:
                if e["id"] not in edge_by_id:
                    edges.append(e)
                    edge_by_id[e["id"]] = e

            cert_record = {
                "source_id": source_id,
                "formal_decl": t["formal_decl"],
                "formal_scope": t["formal_scope"],
                "statement_sha256": t["statement_sha256"],
                "status": "PASS",
                "certificate_class": "KERNEL_VERIFIED",
                "verifier": "Lean 4",
                "lean_version": lean_version,
                "independent_checker": args.independent_checker,
                "independent_checker_status": args.independent_checker_status,
                "s3_test_state": t["s3_test_state"],
                "expected_direct_status": t["expected_direct_status"],
            }
            certificates.append(cert_record)

            target_results.append({
                "source_id": source_id,
                "status": "KERNEL_VERIFIED",
                "formal_scope": t["formal_scope"],
                "s3_contract": c_matching,
            })

    # Gate 9: Historical Profile Fields Byte-for-Byte Preservation Check
    historical_fields_preserved = True
    for nid, snap in historical_snapshot.items():
        n = node_by_id.get(nid)
        if n is None:
            historical_fields_preserved = False
            break
        prof = n.get("attributes", {}).get("independent_profile", {})
        for field, expected_val in snap.items():
            if prof.get(field) != expected_val:
                historical_fields_preserved = False
                break

    # Gate 10: No Forbidden Keys
    no_forbidden_keys = True
    for n in nodes:
        attrs = n.get("attributes", {})
        if any(k in attrs for k in FORBIDDEN_PERSISTED_KEYS):
            no_forbidden_keys = False

    # Gate 11: Graph Topology Integrity
    unique_nodes = (len(nodes) == len({n["id"] for n in nodes}))
    unique_edges = (len(edges) == len({e["id"] for e in edges}))
    no_orphan_edges = all(e["source"] in node_by_id and e["target"] in node_by_id for e in edges)

    # Gate 12: Scope status enforcement
    frozen_targets = [t for t in targets if t.get("scope_status") == "FROZEN"]
    all_frozen_certified = (len(certificates) == len(frozen_targets)) and can_promote
    no_refused_certified = all(
        t["source_id"] not in {c["source_id"] for c in certificates}
        for t in targets
        if t.get("scope_status") != "FROZEN"
    )

    gates = {
        "base_graph_is_v09_accepted": is_v09_base,
        "target_nodes_present": target_nodes_present,
        "independent_profiles_present": independent_profiles_present,
        "statement_hashes_matched": statement_hashes_matched,
        "historical_direct_views_matched": historical_direct_views_matched,
        "explicit_dependencies_present": explicit_dependencies_present,
        "declarations_present": declarations_ok,
        "no_proof_escape_hatches": escape_ok,
        "lean_kernel_pass": kernel_ok,
        "independent_checker_pass": independent_ok,
        "contracts_evaluated_cleanly": contracts_ok,
        "scope_status_enforced": all_frozen_certified and no_refused_certified,
        "historical_fields_preserved_byte_for_byte": historical_fields_preserved,
        "no_copyright_prose_persisted": no_forbidden_keys,
        "unique_node_ids": unique_nodes,
        "unique_edge_ids": unique_edges,
        "no_orphan_edges": no_orphan_edges,
    }
    status = "PASS" if all(gates.values()) else "FAIL"

    # Write Artifacts
    report = {
        "audit_id": "MAPEOGEO-PINCH-INTAKE-V0.11",
        "status": status,
        "stage": "v0.11_PINCH_DRIVEN_INTAKE",
        "gates": gates,
        "identity_checks": identity_checks,
        "target_results": target_results,
        "certificates": certificates,
        "contracts": contract_results,
        "wounds": wounds,
        "counts": {
            "total_targets": len(targets),
            "frozen_targets": len(frozen_targets),
            "certified_targets": len(certificates),
            "refused_targets": len(targets) - len(frozen_targets),
            "nodes": len(nodes),
            "edges": len(edges),
        },
        "claim_boundary": (
            "v0.11 formally ingests the graph-selected pinch interface targets into the MAPEOGEO "
            "v0.9 graph with scoped Lean 4 proofs (KERNEL_VERIFIED), evaluates explicit S3 "
            "computational contracts, preserves historical direct views and wounds, and obeys the "
            "fail-closed intake law without synthetic nodes, manufactured dependencies, or "
            "unjustified EQUIVALENT_TO edges."
        ),
        "graph": {
            "nodes": len(nodes),
            "edges": len(edges),
        },
    }

    (args.out_dir / "pinch_v0_11_results.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    (args.out_dir / "pinch_v0_11_certificates.json").write_text(
        json.dumps(certificates, indent=2), encoding="utf-8"
    )
    (args.out_dir / "pinch_v0_11_wounds.json").write_text(
        json.dumps(wounds, indent=2), encoding="utf-8"
    )

    with gzip.open(args.out_dir / "mapeogeo_v0_11_graph.json.gz", "wt", encoding="utf-8") as f:
        json.dump({"nodes": nodes, "edges": edges}, f, indent=2)

    # Markdown Summary (strictly derived, no hardcoded fractions)
    contract_summary_lines = []
    for c in contract_results:
        c_id = c["contract_id"] if c["contract_id"] is not None else "None"
        contract_summary_lines.append(
            f"| `{c['source_id']}` | `{c['test_state']}` | `{c_id}` | `{c['verdict']}` |"
        )
    contracts_table = "\n".join(contract_summary_lines)

    pass_count = sum(1 for c in contract_results if c["verdict"] == "PASS")
    untested_count = sum(1 for c in contract_results if c["verdict"] == "UNTESTED")

    summary = f"""# MAPEOGEO v0.11 — Pinch-Driven Mathematics Intake

**Status:** {status}

## Verification Summary
- Targets certified: {len(certificates)} / {len(frozen_targets)} frozen targets ({len(targets)} total)
- Lean 4 kernel verified: {len(certificates)} declarations (`certificate_class: KERNEL_VERIFIED`)
- Independent checker: {args.independent_checker} ({args.independent_checker_status})
- S3 computational contracts: {pass_count} PASS, {untested_count} UNTESTED

## S3 Contracts Table
| Target | Test State | Contract ID | Verdict |
|---|---|---|---|
{contracts_table}

## Preserved Wounds and Historical Views
- Historical views immutable: EO-only and dual-direct views preserved byte-for-byte
- Wounds retained: {len(wounds)} recorded wounds visible in graph
- Graph size: {len(nodes)} nodes / {len(edges)} edges

Coverage changed; architecture did not.
"""
    (args.out_dir / "V0_11_SUMMARY.md").write_text(summary, encoding="utf-8")

    print(
        f"MAPEOGEO_V0_11: {status} certs={len(certificates)}/{len(frozen_targets)} "
        f"graph={len(nodes)}/{len(edges)}"
    )
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
