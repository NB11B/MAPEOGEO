#!/usr/bin/env python3
"""MAPEOGEO Foundation Backfill Intake Runner.

Constructs the comprehensive foundational mathematical substrate across 8 layers:
  1. Logic & Proofs
  2. Set Theory
  3. Relations & Functions
  4. Number Systems
  5. Elementary Arithmetic & Algebra
  6. Order, Metrics & Sequences
  7. Euclidean Geometry & Trigonometry
  8. Elementary Calculus

Ingests 176 curated source declarations from Source 0 (FOUNDATION_MATHEMATICS_BASE),
29 foundation canonical objects, builds unverified structural dependency candidates to
235 advanced canonical objects, replays the closed executable-evidence registry, and
reports raw topology separately from proof-eligible grounding.
"""

from __future__ import annotations

import argparse
import copy
from functools import lru_cache
import gzip
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.import_foundation_backfill import (
    FORBIDDEN_PERSISTED_KEYS,
    FoundationDeclaration,
    generate_foundation_declarations,
)
from scripts.foundation_contracts import (
    ContractEvidence,
    build_foundation_contract_evidence,
    validate_contract_evidence,
)
from scripts.compute_foundation_depth import compute_foundation_metrics

STAGE = "foundation"
FOUNDATION_SOURCE_ID = "FOUNDATION_MATHEMATICS_BASE"
GALLIER_SOURCE_ID = "GALLIER_QUAINTANCE_2020"
AXLER_SOURCE_ID = "AXLER_LADR4E_2026_08_16"
VMLS_SOURCE_ID = "BOYD_VANDENBERGHE_VMLS_2018"
CVX_SOURCE_ID = "BOYD_VANDENBERGHE_CVX_2004"
BILLINGSLEY_SOURCE_ID = "BILLINGSLEY_PROB_MEASURE_1995"
LEE_SOURCE_ID = "LEE_SMOOTH_MANIFOLDS_2013"
AHLFORS_SOURCE_ID = "AHLFORS_KRANTZ_COMPLEX_ANALYSIS_1979"

SOURCE_BUCKETS = {
    "FOUNDATION_MATHEMATICS_BASE": "foundation_base_S0",
    "GALLIER_QUAINTANCE_MATH_DEEP": "gallier_quaintance_SA",
    "GALLIER_QUAINTANCE_2020": "gallier_quaintance_SA",
    AXLER_SOURCE_ID: "axler_ladr4e_SB",
    VMLS_SOURCE_ID: "boyd_vmls_SC",
    CVX_SOURCE_ID: "boyd_cvx_SD",
    BILLINGSLEY_SOURCE_ID: "billingsley_SE",
    LEE_SOURCE_ID: "lee_diffgeom_SF",
    AHLFORS_SOURCE_ID: "ahlfors_krantz_SG",
}


def _source_identity(node: dict[str, Any]) -> str | None:
    attrs = node.get("attributes", {})
    return attrs.get("source_id") or attrs.get("source")


@lru_cache(maxsize=1)
def foundation_source_registry() -> dict[str, dict[str, str]]:
    """Return the closed declaration registry used for active source accounting."""
    from scripts.complex_analysis_intake_v0_19 import authoritative_source_registry

    registry = copy.deepcopy(authoritative_source_registry())
    for declaration in generate_foundation_declarations():
        record = {
            "source_id": FOUNDATION_SOURCE_ID,
            "corpus": "FOUNDATION",
            "statement_sha256": declaration.statement_sha256,
            "count_status": "ADMISSIBLE_SOURCE_DECLARATION",
        }
        previous = registry.get(declaration.node_id)
        if previous is not None and previous != record:
            raise ValueError(
                f"conflicting authoritative foundation source identity: {declaration.node_id}"
            )
        registry[declaration.node_id] = record
    return registry


def _registered_source_record(node: dict[str, Any]) -> dict[str, str]:
    node_id = node.get("id")
    record = foundation_source_registry().get(node_id)
    if record is None:
        raise ValueError(f"source identity is absent from authoritative source registry: {node_id}")

    attrs = node.get("attributes", {})
    source_id = _source_identity(node)
    if source_id == "GALLIER_QUAINTANCE_MATH_DEEP":
        source_id = GALLIER_SOURCE_ID
    statement_sha256 = attrs.get("statement_sha256")
    if node.get("type") == "STATEMENT":
        statement_sha256 = attrs.get("independent_profile", {}).get("statement_sha256")
    corpus = attrs.get("corpus")
    if (
        source_id != record["source_id"]
        or statement_sha256 != record["statement_sha256"]
        or (corpus is not None and corpus != record["corpus"])
    ):
        raise ValueError(f"authoritative source identity mismatch: {node_id}")
    return record


def partition_source_declarations(nodes: list[dict[str, Any]]) -> dict[str, int]:
    """Partition only exact, admissible identities from the closed source registry."""
    counts = {bucket: 0 for bucket in sorted(set(SOURCE_BUCKETS.values()))}
    for node in nodes:
        if node.get("type") not in {
            "SOURCE_DECLARATION",
            "STATEMENT",
            "SOURCE_SECTION_ANCHOR",
        }:
            raise ValueError(f"partition member is not a source record: {node.get('id')}")
        record = _registered_source_record(node)
        if record["count_status"] != "ADMISSIBLE_SOURCE_DECLARATION":
            continue
        bucket = SOURCE_BUCKETS.get(record["source_id"])
        if bucket is None:
            raise ValueError(
                f"Unregistered source identity for declaration {node.get('id')}: "
                f"{record['source_id']!r}"
            )
        counts[bucket] += 1
    counts["disjoint_partition_sum"] = sum(counts.values())
    return counts


def load_json_or_gz(path: Path) -> dict[str, Any]:
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return json.load(f)
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_foundation_evidence_path(out_dir: Path, requested: Path | None) -> Path:
    """Keep replay evidence additive and local to the requested output by default."""
    return requested or (out_dir / "foundation_backfill_scientific_results.json")


def save_graph_gz(graph: dict[str, Any], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    for node in graph.get("nodes", []):
        attrs = node.get("attributes", {})
        for forbidden in FORBIDDEN_PERSISTED_KEYS:
            if forbidden in node or forbidden in attrs:
                raise ValueError(f"Zero-prose violation in node {node.get('id')}: found key '{forbidden}'")

    payload = (
        json.dumps(
            graph,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w+b",
            prefix=f".{out_path.name}.",
            suffix=".tmp",
            dir=out_path.parent,
            delete=False,
        ) as raw:
            temporary_path = Path(raw.name)
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
                compressed.write(payload)
            raw.flush()
            os.fsync(raw.fileno())
        os.replace(temporary_path, out_path)
    except Exception:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise


def add_node(nodes: list[dict], by_id: dict[str, dict], node: dict) -> bool:
    nid = node["id"]
    if nid not in by_id:
        nodes.append(node)
        by_id[nid] = node
        return True
    else:
        existing = by_id[nid]
        if "attributes" in node:
            existing.setdefault("attributes", {}).update(node["attributes"])
        return False


def add_edge(edges: list[dict], edge_ids: set[str], edge: dict) -> bool:
    eid = edge["id"]
    if eid not in edge_ids:
        edges.append(edge)
        edge_ids.add(eid)
        return True
    existing = next((item for item in edges if item.get("id") == eid), None)
    if existing != edge:
        raise ValueError(f"edge ID collision with different payload: {eid}")
    return False


def ingest_foundation_declarations(
    graph: dict[str, Any],
    declarations: list[FoundationDeclaration],
    evidence_by_subject: dict[str, ContractEvidence] | None = None,
) -> dict[str, Any]:
    evidence_by_subject = evidence_by_subject or {}
    if evidence_by_subject:
        evidence_by_contract: dict[str, ContractEvidence] = {}
        for subject_id, evidence in evidence_by_subject.items():
            previous = evidence_by_contract.get(evidence.contract_id)
            if previous is not None and previous != evidence:
                raise ValueError(f"conflicting evidence records for {evidence.contract_id}")
            evidence_by_contract[evidence.contract_id] = evidence
            if subject_id not in evidence.subject_ids:
                raise ValueError(f"evidence subject binding mismatch for {subject_id}")
        validate_contract_evidence(tuple(evidence_by_contract.values()), declarations)
        registered_subjects = {
            subject_id
            for evidence in evidence_by_contract.values()
            for subject_id in evidence.subject_ids
        }
        if set(evidence_by_subject) != registered_subjects:
            raise ValueError("evidence subject registry is incomplete or overbroad")
    nodes: list[dict] = graph.setdefault("nodes", [])
    edges: list[dict] = graph.setdefault("edges", [])
    by_id = {n["id"]: n for n in nodes}
    edge_ids = {e["id"] for e in edges if "id" in e}

    for decl in declarations:
        evidence = evidence_by_subject.get(decl.node_id)
        verification_attrs: dict[str, Any] = {
            "declaration_verification_status": "UNVERIFIED",
        }
        amendment_attrs: dict[str, Any] = {}
        if decl.amendment_id is not None:
            if decl.amendment_status != "ACTIVE_STATEMENT_AMENDMENT_UNVERIFIED":
                raise ValueError(f"invalid active statement amendment: {decl.node_id}")
            amendment_attrs = {
                "statement_amendment_id": decl.amendment_id,
                "statement_amendment_status": decl.amendment_status,
                "statement_amendment_claim_boundary": "CORRECTION_NOT_PROOF",
            }
        if evidence is not None:
            bound_hashes = dict(evidence.subject_hashes)
            if (
                decl.node_id not in evidence.subject_ids
                or bound_hashes.get(decl.node_id) != decl.statement_sha256
            ):
                raise ValueError(
                    f"evidence subject binding mismatch for {decl.node_id}"
                )
            verification_attrs = {
                "declaration_verification_status": "EXECUTABLE_VERIFIED",
                "evidence_contract_id": evidence.contract_id,
                "evidence_digest": evidence.evidence_digest,
                "certificate_class": evidence.certificate_class,
                "verification_scope": evidence.scope,
            }
        node_dict = {
            "id": decl.node_id,
            "type": "SOURCE_DECLARATION",
            "label": decl.label,
            "attributes": {
                "source_id": decl.source_id,
                "corpus": "FOUNDATION",
                "decl_type": decl.decl_type,
                "chapter_section": decl.chapter_section,
                "statement_sha256": decl.statement_sha256,
                "statement_chars": decl.char_count,
                "layer": decl.layer,
                "direct_status": decl.representation_profile.get("direct_status", "THEORETIC_DIRECT"),
                "eo_tags": decl.representation_profile.get("eo_tags", []),
                "geo_tags": decl.representation_profile.get("geo_tags", []),
                "representation_kinds": decl.representation_profile.get("representation_kinds", []),
                "diversity_count": decl.representation_profile.get("diversity_count", 1),
                "stage": STAGE,
                **amendment_attrs,
                **verification_attrs,
            },
        }
        add_node(nodes, by_id, node_dict)

        # Structural references are unverified semantic candidates.  They are
        # never proof edges merely because a curator listed them.
        for target_id in decl.structural_refs:
            edge_id = f"e:ref:{decl.node_id}:{target_id}"
            add_edge(
                edges,
                edge_ids,
                {
                    "id": edge_id,
                    "type": "STRUCTURAL_REFERENCE",
                    "source": decl.node_id,
                    "target": target_id,
                    "attributes": {
                        "reference_kind": "DECLARED_PREREQUISITE_CANDIDATE",
                        "relation_status": "UNVERIFIED_CANDIDATE",
                        "evidence_status": "UNVERIFIED",
                        "stage": STAGE,
                    },
                },
            )

    return graph


def ingest_foundation_canonical_alignments(
    graph: dict[str, Any],
    alignments_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    nodes: list[dict] = graph.setdefault("nodes", [])
    edges: list[dict] = graph.setdefault("edges", [])
    by_id = {n["id"]: n for n in nodes}
    edge_ids = {e["id"] for e in edges if "id" in e}

    alignments_data = json.loads(alignments_path.read_text(encoding="utf-8"))
    canonical_objects = alignments_data.get("canonical_objects", [])

    summary = {
        "total_foundation_canonical_objects": len(canonical_objects),
        "total_alignments": 0,
        "upward_dependency_links": 0,
        "representation_diversity": {
            "abstract": 0,
            "algebraic": 0,
            "geometric": 0,
            "computational": 0,
            "applied": 0,
            "formal": 0,
        },
    }

    for co in canonical_objects:
        cid = co["id"]
        cname = co["name"]
        domain = co.get("domain", "Mathematical Foundations")
        desc = co.get("description", "")
        rep_diversity = co.get("representation_kinds", ["abstract"])
        diversity_count = len(rep_diversity)

        for rk in rep_diversity:
            if rk in summary["representation_diversity"]:
                summary["representation_diversity"][rk] += 1

        # Add foundation canonical object node
        add_node(
            nodes,
            by_id,
            {
                "id": cid,
                "type": "CANONICAL_OBJECT",
                "label": cname,
                "attributes": {
                    "domain": domain,
                    "description": desc,
                    "is_foundation": True,
                    "representation_diversity": rep_diversity,
                    "diversity_count": diversity_count,
                    "stage": STAGE,
                },
            },
        )

        # Ingest REPRESENTS edges from source declarations
        for al in co.get("alignments", []):
            src_id = al["source"]
            corpus = al["corpus"]
            status = al.get("status", "CROSS_SOURCE_SAME")

            if src_id not in by_id:
                raise ValueError(
                    f"Fail-closed provenance error: Source declaration '{src_id}' in canonical object '{cid}' not in graph!"
                )

            source_hash = by_id[src_id].get("attributes", {}).get("statement_sha256")

            summary["total_alignments"] += 1
            rep_edge_id = f"e:rep:{src_id}:{cid}"
            add_edge(
                edges,
                edge_ids,
                {
                    "id": rep_edge_id,
                    "type": "REPRESENTS",
                    "source": src_id,
                    "target": cid,
                    "attributes": {
                        "corpus": corpus,
                        "cross_source_status": status,
                        "source_statement_sha256": source_hash,
                        "stage": STAGE,
                        "evidence_status": "UNVERIFIED",
                    },
                },
            )

        # Ingest UPWARD_FOUNDATION_DEPENDENCY edges
        for target_cid in co.get("upward_dependencies", []):
            if target_cid not in by_id:
                raise ValueError(
                    f"Upward target {target_cid} not found in graph for {cid}"
                )

            summary["upward_dependency_links"] += 1
            up_edge_id = f"e:upward_dep:{cid}:{target_cid}"
            add_edge(
                edges,
                edge_ids,
                {
                    "id": up_edge_id,
                    "type": "UPWARD_FOUNDATION_DEPENDENCY",
                    "source": cid,
                    "target": target_cid,
                    "attributes": {
                        "relation": "FOUNDATION_GROUNDS_ADVANCED",
                        "relation_status": "STRUCTURAL_CANDIDATE",
                        "evidence_status": "UNVERIFIED",
                        "stage": STAGE,
                    },
                },
            )

    return graph, summary


def compute_foundation_dashboard(
    graph: dict[str, Any],
    summary: dict[str, Any],
    depth_metrics: dict[str, Any],
    contract_summary: dict[str, Any],
) -> dict[str, Any]:
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    source_records = [
        n for n in nodes
        if n.get("type") in ("SOURCE_DECLARATION", "STATEMENT", "SOURCE_SECTION_ANCHOR")
    ]
    records_by_status: dict[str, list[dict[str, Any]]] = {
        "ADMISSIBLE_SOURCE_DECLARATION": [],
        "EXCLUDED_HISTORICAL_COUNT_ARTIFACT": [],
        "SECTION_ANCHOR": [],
    }
    for node in source_records:
        record = _registered_source_record(node)
        try:
            records_by_status[record["count_status"]].append(node)
        except KeyError as exc:
            raise ValueError(
                f"unknown authoritative count status for {node.get('id')}: "
                f"{record['count_status']!r}"
            ) from exc
    source_decls = records_by_status["ADMISSIBLE_SOURCE_DECLARATION"]
    excluded_source_records = records_by_status["EXCLUDED_HISTORICAL_COUNT_ARTIFACT"]
    sec_anchors = records_by_status["SECTION_ANCHOR"]
    canonical_objs = [n for n in nodes if n.get("type") == "CANONICAL_OBJECT"]

    partition = partition_source_declarations(source_records)
    total_partitioned = partition["disjoint_partition_sum"]

    if total_partitioned != len(source_decls):
        raise ValueError(
            f"Disjoint partition violation: partition sum ({total_partitioned}) != total source decls ({len(source_decls)})"
        )

    # Layer breakdown for foundation declarations
    layer_counts: dict[str, int] = {}
    for d in source_decls:
        if _source_identity(d) != FOUNDATION_SOURCE_ID:
            continue
        layer = d.get("attributes", {}).get("layer", "unknown")
        layer_counts[layer] = layer_counts.get(layer, 0) + 1

    # Distinct domains across all canonical objects
    domains = set()
    total_diversity = 0
    for co in canonical_objs:
        attrs = co.get("attributes", {})
        dom = attrs.get("domain")
        if dom:
            domains.add(dom)
        div = attrs.get("representation_diversity", [])
        total_diversity += len(div) if div else 1

    r_bar = round(total_diversity / max(1, len(canonical_objs)), 3)

    # Edge classification
    bridge_same = [e for e in edges if e.get("type") == "SAME_SEMANTICS"]
    bridge_scoped = [e for e in edges if e.get("type") == "SCOPED_OVERLAP"]
    bridge_related = [e for e in edges if e.get("type") == "RELATED_TO"]
    upward_deps = [e for e in edges if e.get("type") == "UPWARD_FOUNDATION_DEPENDENCY"]
    represents = [e for e in edges if e.get("type") == "REPRESENTS"]
    proof_deps = [e for e in edges if e.get("type") == "PROOF_DEPENDENCY"]

    dashboard = {
        "stage": STAGE,
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "N_source_total": len(source_decls),
        "N_source_records_raw": len(source_records),
        "N_source_records_excluded": len(excluded_source_records),
        "N_source_breakdown": {
            **partition,
            "disjoint_partition_status": "EXACT_EQUALITY",
        },
        "foundation_layers_breakdown": layer_counts,
        "N_section_anchors_total": len(sec_anchors),
        "N_canonical_total": len(canonical_objs),
        "canonical_breakdown": {
            "foundation_canonical_objects": summary["total_foundation_canonical_objects"],
            "advanced_canonical_objects": len(canonical_objs) - summary["total_foundation_canonical_objects"],
        },
        "foundation_metrics": depth_metrics,
        "contracts_verification": contract_summary,
        "representation_diversity": {
            "average_richness_r_bar": r_bar,
            "modalities_distribution": summary["representation_diversity"],
        },
        "domains_count": len(domains),
        "domains_list": sorted(list(domains)),
        "edges_summary": {
            "UPWARD_FOUNDATION_DEPENDENCY": len(upward_deps),
            "SAME_SEMANTICS": len(bridge_same),
            "SCOPED_OVERLAP": len(bridge_scoped),
            "RELATED_TO": len(bridge_related),
            "total_typed_cross_bridges": len(bridge_same) + len(bridge_scoped) + len(bridge_related),
            "REPRESENTS": len(represents),
            "PROOF_DEPENDENCY": len(proof_deps),
            "other_edges": len([
                e for e in edges
                if e.get("type") not in (
                    "UPWARD_FOUNDATION_DEPENDENCY",
                    "SAME_SEMANTICS",
                    "SCOPED_OVERLAP",
                    "RELATED_TO",
                    "REPRESENTS",
                    "PROOF_DEPENDENCY",
                )
            ]),
        },
    }
    return dashboard


def run_foundation_intake(
    base_graph_path: Path,
    alignments_path: Path,
    out_dir: Path,
    evidence_path: Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    graph = load_json_or_gz(base_graph_path)

    decls = generate_foundation_declarations()
    contract_evidence = build_foundation_contract_evidence(decls)
    contract_summary = validate_contract_evidence(contract_evidence, decls)
    evidence_by_subject = {
        subject_id: item
        for item in contract_evidence
        for subject_id in item.subject_ids
    }

    # 1. Ingest declarations with evidence attached only to exact subjects.
    graph = ingest_foundation_declarations(
        graph,
        decls,
        evidence_by_subject=evidence_by_subject,
    )

    # 2. Ingest foundation canonical objects & upward dependency links
    graph, summary = ingest_foundation_canonical_alignments(
        graph,
        alignments_path,
    )

    # 3. Compute foundation depth & reachability metrics
    depth_metrics = compute_foundation_metrics(graph)

    # 4. Compute dashboard without promoting unbound declarations.
    dashboard = compute_foundation_dashboard(graph, summary, depth_metrics, contract_summary)

    # 6. Save outputs
    out_graph_path = out_dir / "mapeogeo_foundation_graph.json.gz"
    save_graph_gz(graph, out_graph_path)

    dash_path = out_dir / "foundation_backfill_dashboard.json"
    dash_path.write_text(
        json.dumps(dashboard, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    resolved_evidence_path = resolve_foundation_evidence_path(out_dir, evidence_path)
    resolved_evidence_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_evidence_path.write_text(
        json.dumps(dashboard, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return graph, dashboard, summary


def main() -> int:
    parser = argparse.ArgumentParser(description="MAPEOGEO Foundation Backfill Intake Runner")
    parser.add_argument(
        "--base-graph",
        type=Path,
        default=ROOT / "artifacts" / "diffgeom_v0_18" / "mapeogeo_v0_18_graph.json.gz",
        help="Base v0.18 graph checkpoint",
    )
    parser.add_argument(
        "--alignments",
        type=Path,
        default=ROOT / "formal" / "foundation_alignments.json",
        help="Foundation alignments JSON file",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "artifacts" / "foundation_backfill",
        help="Output directory for Foundation Backfill artifacts",
    )
    parser.add_argument(
        "--evidence-out",
        type=Path,
        default=None,
        help="Optional additive evidence output path",
    )
    args = parser.parse_args()

    print(f"[Foundation Intake] Loading base graph from: {args.base_graph}")
    print(f"[Foundation Intake] Generating curated Source 0 (Foundation) declarations...")
    print(f"[Foundation Intake] Ingesting canonical alignments from: {args.alignments}")

    graph, dashboard, summary = run_foundation_intake(
        base_graph_path=args.base_graph,
        alignments_path=args.alignments,
        out_dir=args.out_dir,
        evidence_path=args.evidence_out,
    )

    print("==========================================================")
    print("  MAPEOGEO Foundation Backfill Expansion SUCCESS")
    print("==========================================================")
    print(f"  Source Declarations:        {dashboard['N_source_total']}")
    print(f"    - Foundation Base (S_0):  {dashboard['N_source_breakdown']['foundation_base_S0']}")
    print(f"    - Gallier (S_A):          {dashboard['N_source_breakdown']['gallier_quaintance_SA']}")
    print(f"    - Axler (S_B):            {dashboard['N_source_breakdown']['axler_ladr4e_SB']}")
    print(f"    - VMLS (S_C):             {dashboard['N_source_breakdown']['boyd_vmls_SC']}")
    print(f"    - CVX (S_D):              {dashboard['N_source_breakdown']['boyd_cvx_SD']}")
    print(f"    - Billingsley (S_E):      {dashboard['N_source_breakdown']['billingsley_SE']}")
    print(f"    - Lee DiffGeom (S_F):     {dashboard['N_source_breakdown']['lee_diffgeom_SF']}")
    print(f"  Disjoint Partition Sum:     {dashboard['N_source_breakdown']['disjoint_partition_sum']} ({dashboard['N_source_breakdown']['disjoint_partition_status']})")
    print(f"  Canonical Objects Total:    {dashboard['N_canonical_total']}")
    print(f"    - Foundation Objects:     {dashboard['canonical_breakdown']['foundation_canonical_objects']}")
    print(f"    - Advanced Objects:       {dashboard['canonical_breakdown']['advanced_canonical_objects']}")
    raw_metrics = dashboard['foundation_metrics']['raw_topology_reachability']
    proof_metrics = dashboard['foundation_metrics']['proof_eligible_grounding']
    print(f"  Raw Topology Reachability:   {raw_metrics['foundation_reachability_pct']}% ({raw_metrics['advanced_canonical_objects_reachable']}/{raw_metrics['advanced_canonical_objects_total']})")
    print(f"  Proof-Eligible Grounding:    {proof_metrics['foundation_reachability_pct']}% ({proof_metrics['advanced_canonical_objects_reachable']}/{proof_metrics['advanced_canonical_objects_total']})")
    print(f"  Upward Foundation Bridges:  {dashboard['edges_summary']['UPWARD_FOUNDATION_DEPENDENCY']}")
    print(f"  Typed Semantic Bridges:     {dashboard['edges_summary']['total_typed_cross_bridges']}")
    print(f"  Declaration Evidence:       {dashboard['contracts_verification']['verified_declarations']}/{dashboard['contracts_verification']['verified_declarations'] + dashboard['contracts_verification']['unverified_declarations']} verified; 0 kernel-verified")
    print(f"  Total Graph Nodes:          {dashboard['total_nodes']}")
    print(f"  Total Graph Edges:          {dashboard['total_edges']}")
    print("==========================================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())
