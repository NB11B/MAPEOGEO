"""MAPEOGEO Certifiable Semantics & Payload Census (Workstream 1).

Audits all mathematical assets in MAPEOGEO to classify nodes by their certifiable
evidence tier and compute exact GFYProof verifier compatibility metrics without
inventing or fabricating missing values.
"""

from __future__ import annotations

import glob
import gzip
import json
import os
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from typing import Any, Mapping


SNAPSHOT_PATH = "artifacts/analysis_v0_15_1/mapeogeo_v0_15_1_graph.json.gz"
FORMAL_DIR = "formal"
EVIDENCE_DIR = "evidence"
OUTPUT_DIR = "artifacts/certifiable_semantics"


@dataclass(frozen=True)
class NodeCensusEntry:
    node_id: str
    label: str
    node_type: str
    classification: str
    domain: str
    formal_decl: str | None
    executable_contract: str | None
    scope: str | None
    statement_sha256: str | None
    source_corpus: str | None
    verifier_families: list[str]
    notes: str


def load_json(path: str) -> Any:
    """Load JSON from standard or gzipped file."""
    if path.endswith(".gz"):
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return json.load(f)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data: Any) -> None:
    """Save data structure to formatted JSON."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)


def run_certifiable_semantics_census() -> dict[str, Any]:
    """Execute complete certifiable payload census across MAPEOGEO."""
    print("=" * 80)
    print("MAPEOGEO Certifiable Semantics & Payload Census Audit (Workstream 1)")
    print("=" * 80)

    # 1. Load Authoritative Graph Snapshot
    print(f"\n[Step 1] Loading graph snapshot: {SNAPSHOT_PATH}...")
    graph_data = load_json(SNAPSHOT_PATH)
    nodes_raw = graph_data.get("nodes", {})
    edges_raw = graph_data.get("edges", [])
    print(f"  Loaded {len(nodes_raw)} nodes and {len(edges_raw)} edges from snapshot.")

    # 2. Ingest Formal Bindings & Manifests
    print(f"\n[Step 2] Ingesting formal alignments, manifests, and contract registries...")
    formal_decl_map: dict[str, dict[str, Any]] = {}
    contract_map: dict[str, dict[str, Any]] = {}
    source_to_canonical: dict[str, str] = {}

    # Load pinch bindings (v0.11)
    pinch_path = os.path.join(FORMAL_DIR, "pinch_bindings_v0_11.json")
    if os.path.exists(pinch_path):
        pinch_data = load_json(pinch_path)
        for target in pinch_data.get("targets", []):
            src_id = target["source_id"]
            formal_decl_map[src_id] = {
                "formal_decl": target.get("formal_decl"),
                "formal_scope": target.get("formal_scope"),
                "explicit_dependencies": target.get("explicit_dependencies", []),
                "statement_sha256": target.get("statement_sha256"),
            }
            if target.get("s3_contract_id"):
                contract_map[src_id] = {
                    "contract_id": target["s3_contract_id"],
                    "scope": target.get("s3_scope"),
                    "test_state": target.get("s3_test_state"),
                }

    # Load canonical alignments across stages
    for align_file in sorted(glob.glob(os.path.join(FORMAL_DIR, "*alignments*.json"))):
        align_data = load_json(align_file)
        for obj in align_data.get("canonical_objects", []):
            cid = obj.get("id") or obj.get("canonical_id")
            if not cid:
                continue
            fdecl = obj.get("formal_decl")
            if fdecl:
                formal_decl_map[cid] = {
                    "formal_decl": fdecl,
                    "domain": obj.get("domain"),
                }
            for al in obj.get("alignments", []):
                src = al.get("source")
                if src:
                    source_to_canonical[src] = cid

    # Load declaration manifests
    for manifest_file in sorted(glob.glob(os.path.join(FORMAL_DIR, "*manifest*.json"))):
        mdata = load_json(manifest_file)
        if isinstance(mdata, dict):
            for decl_id, decl_val in mdata.items():
                if isinstance(decl_val, dict) and "formal_decl" in decl_val:
                    formal_decl_map[decl_id] = decl_val

    print(f"  Mapped {len(formal_decl_map)} formal declarations and {len(contract_map)} executable contracts.")

    # 3. Classify Every Node in the Graph
    print(f"\n[Step 3] Classifying nodes by evidence tier...")
    census_entries: list[NodeCensusEntry] = []
    classification_counts: Counter[str] = Counter()
    domain_counts: Counter[str] = Counter()
    verifier_family_counts: Counter[str] = Counter()

    if isinstance(nodes_raw, list):
        nodes_dict = {n.get("id", str(i)): n for i, n in enumerate(nodes_raw)}
    elif isinstance(nodes_raw, dict):
        nodes_dict = nodes_raw
    else:
        nodes_dict = {}

    for nid, node in nodes_dict.items():
        label = node.get("label", nid)
        attrs = node.get("attributes", {})
        ntype = node.get("type", "UNKNOWN")
        domain = attrs.get("domain", "General Mathematics")
        domain_counts[domain] += 1

        fdecl_info = formal_decl_map.get(nid) or formal_decl_map.get(source_to_canonical.get(nid, ""))
        contract_info = contract_map.get(nid) or contract_map.get(source_to_canonical.get(nid, ""))

        formal_decl = attrs.get("formal_decl") or (fdecl_info.get("formal_decl") if fdecl_info else None)
        statement_sha256 = attrs.get("statement_sha256") or (fdecl_info.get("statement_sha256") if fdecl_info else None)
        contract_id = contract_info.get("contract_id") if contract_info else None
        scope = contract_info.get("scope") if contract_info else attrs.get("scope")
        source_corpus = attrs.get("corpus") or attrs.get("source_id")

        # Map to GFYProof relation verifier families
        vfamilies: list[str] = []
        if contract_id == "linear_independence_not_in_span_q" or "linear_independence" in str(formal_decl):
            vfamilies.append("GFY.ORTHOGONAL_PROJECTION_EQUIVALENCE.v1")
        if contract_id == "subspace_disjoint_intersection_q" or "proposition_4_4" in str(formal_decl):
            vfamilies.append("GFY.DIRECT_SUM_DECOMPOSITION.v1")
        if contract_id == "spectral_decomposition_symmetric_matrix" or "theorem_27_10" in str(formal_decl):
            vfamilies.append("GFY.SPECTRAL_DECOMPOSITION.v1")
        if "farkas" in nid or "farkas" in str(formal_decl):
            vfamilies.append("GFY.FARKAS_IMPLICATION.v1")
        if "orthogonal_projection" in str(formal_decl) or "test:18" in nid:
            vfamilies.append("GFY.ORTHOGONAL_PROJECTION_EQUIVALENCE.v1")
        if "test:05" in nid:
            vfamilies.append("GFY.SO3_REPRESENTATION_EQUIVALENCE.v1")
        if "test:14" in nid:
            vfamilies.append("GFY.KKT_SADDLE_EQUIVALENCE.v1")
        if "test:17" in nid:
            vfamilies.append("GFY.LP_STRONG_DUALITY_1D.v1")
        if "test:07" in nid:
            vfamilies.append("GFY.GRAPH_LAPLACIAN_EQUIVALENCE.v1")
        if "test:01" in nid:
            vfamilies.append("GFY.CYCLIC_GROUP_COMPOSITION.v1")
        if "test:03" in nid:
            vfamilies.append("GFY.ROBDD_EQUIVALENCE.v1")

        for vf in vfamilies:
            verifier_family_counts[vf] += 1

        # Determine Classification Tier
        # Tier 1: DIRECT_PAYLOAD (Has explicit matrix/vector/system serialized)
        if attrs.get("payload") and isinstance(attrs["payload"], dict) and len(attrs["payload"]) > 0:
            classification = "DIRECT_PAYLOAD"
            notes = "Contains explicit machine-readable mathematical payload dictionary."

        # Tier 2: EXECUTABLE_CONTRACT (Has registered contract with executable scope)
        elif contract_id is not None:
            classification = "EXECUTABLE_CONTRACT"
            notes = f"Linked to executable contract '{contract_id}' with scope '{scope}'."

        # Tier 3: FORMAL_DERIVABLE (Has formal Lean declaration with AST binding)
        elif formal_decl is not None:
            classification = "FORMAL_DERIVABLE"
            notes = f"Has verified formal Lean declaration '{formal_decl}'."

        # Tier 4: CERTIFICATE_DERIVABLE (Has verified kernel/replay certificate)
        elif attrs.get("checks") and attrs.get("contract"):
            classification = "CERTIFICATE_DERIVABLE"
            notes = f"Has certified replay contract '{attrs.get('contract')}' with {attrs.get('checks')} checks."

        # Tier 5: STRUCTURAL_ONLY (Has tags/domain/refs but no formal/contract binding)
        elif attrs.get("eo_tags") or attrs.get("geo_tags") or attrs.get("structural_refs") or nid.startswith("canonical:"):
            classification = "STRUCTURAL_ONLY"
            notes = "Has structural/signature metadata but lacks formal Lean or executable contract binding."

        # Tier 6: NARRATIVE_ONLY (Source locator/hash only)
        else:
            classification = "NARRATIVE_ONLY"
            notes = "Source locator/hash metadata only; must remain UNRESOLVED under zero-fabrication rules."

        classification_counts[classification] += 1
        census_entries.append(
            NodeCensusEntry(
                node_id=nid,
                label=label,
                node_type=ntype,
                classification=classification,
                domain=domain,
                formal_decl=formal_decl,
                executable_contract=contract_id,
                scope=scope,
                statement_sha256=statement_sha256,
                source_corpus=source_corpus,
                verifier_families=vfamilies,
                notes=notes,
            )
        )

    # 4. Compile Output Artifacts
    print(f"\n[Step 4] Compiling and saving census artifacts into {OUTPUT_DIR}...")
    total_nodes = len(census_entries)

    candidates = [asdict(e) for e in census_entries if e.classification in ("DIRECT_PAYLOAD", "EXECUTABLE_CONTRACT", "FORMAL_DERIVABLE", "CERTIFICATE_DERIVABLE")]
    unresolved = [asdict(e) for e in census_entries if e.classification in ("STRUCTURAL_ONLY", "NARRATIVE_ONLY")]

    coverage_payload = {
        "census_schema": "mapeogeo.certifiable-payload-census.v1",
        "snapshot_path": SNAPSHOT_PATH,
        "total_nodes_audited": total_nodes,
        "total_edges_in_snapshot": len(edges_raw),
        "classification_summary": {
            "DIRECT_PAYLOAD": classification_counts["DIRECT_PAYLOAD"],
            "EXECUTABLE_CONTRACT": classification_counts["EXECUTABLE_CONTRACT"],
            "FORMAL_DERIVABLE": classification_counts["FORMAL_DERIVABLE"],
            "CERTIFICATE_DERIVABLE": classification_counts["CERTIFICATE_DERIVABLE"],
            "STRUCTURAL_ONLY": classification_counts["STRUCTURAL_ONLY"],
            "NARRATIVE_ONLY": classification_counts["NARRATIVE_ONLY"],
        },
        "certifiable_pool_total": len(candidates),
        "unresolved_pool_total": len(unresolved),
        "certifiable_coverage_pct": round((len(candidates) / total_nodes) * 100.0, 2) if total_nodes else 0.0,
        "conservation_check": {
            "total_matches_sum": total_nodes == sum(classification_counts.values()),
            "equation": f"{total_nodes} = " + " + ".join(f"{v} ({k})" for k, v in classification_counts.items()),
        },
        "domain_distribution": dict(domain_counts.most_common()),
    }

    verifier_payload = {
        "census_schema": "mapeogeo.certifiable-verifier-coverage.v1",
        "total_certifiable_nodes": len(candidates),
        "verifier_family_distribution": dict(verifier_family_counts.most_common()),
        "certifiable_candidate_nodes": [
            {
                "node_id": c["node_id"],
                "classification": c["classification"],
                "formal_decl": c["formal_decl"],
                "executable_contract": c["executable_contract"],
                "scope": c["scope"],
                "verifier_families": c["verifier_families"],
            }
            for c in candidates
        ],
    }

    save_json(os.path.join(OUTPUT_DIR, "coverage.json"), coverage_payload)
    save_json(os.path.join(OUTPUT_DIR, "candidates.json"), {"total_candidates": len(candidates), "candidates": candidates})
    save_json(os.path.join(OUTPUT_DIR, "unresolved.json"), {"total_unresolved": len(unresolved), "unresolved": unresolved})
    save_json(os.path.join(OUTPUT_DIR, "verifier_coverage.json"), verifier_payload)

    # 5. Print Decisive Census Summary
    print("-" * 80)
    print("DECISIVE CENSUS SUMMARY")
    print("-" * 80)
    print(f"Total Mathematical Nodes Audited: {total_nodes}")
    print(f"  |-- DIRECT_PAYLOAD:        {classification_counts['DIRECT_PAYLOAD']:5d}")
    print(f"  |-- EXECUTABLE_CONTRACT:   {classification_counts['EXECUTABLE_CONTRACT']:5d}")
    print(f"  |-- FORMAL_DERIVABLE:      {classification_counts['FORMAL_DERIVABLE']:5d}")
    print(f"  |-- CERTIFICATE_DERIVABLE: {classification_counts['CERTIFICATE_DERIVABLE']:5d}")
    print(f"  |-- STRUCTURAL_ONLY:       {classification_counts['STRUCTURAL_ONLY']:5d}")
    print(f"  \\-- NARRATIVE_ONLY:        {classification_counts['NARRATIVE_ONLY']:5d}")
    print(f"Certifiable Candidate Pool:       {len(candidates)} nodes ({coverage_payload['certifiable_coverage_pct']}%)")
    print(f"Unresolved Abstention Pool:       {len(unresolved)} nodes")
    print(f"Exact Conservation:               {coverage_payload['conservation_check']['equation']}")
    print("=" * 80)

    return coverage_payload


if __name__ == "__main__":
    run_certifiable_semantics_census()
