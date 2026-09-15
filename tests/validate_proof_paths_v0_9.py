#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

REQUIRED_FILES = (
    "proof_path_v0_9_report.json",
    "proof_path_kernel_certificates_v0_9.json",
    "pinch_quartet_v0_9.json",
    "wounds_v0_9.json",
    "mapeogeo_s5_v0_9_graph.json.gz",
    "V0_9_SUMMARY.md",
)
FORBIDDEN_PERSISTED_KEYS = {"statement_text", "proof_text", "source_prose", "page_image"}
SUPPORT_IDS = {
    "srcdecl:proposition:6_15",
    "srcdecl:proposition:6_11",
    "srcdecl:proposition:6_7",
    "srcdecl:proposition:3_15",
    "srcdecl:theorem:3_7",
    "srcdecl:lemma:3_6",
}


def walk_keys(value):
    if isinstance(value, dict):
        for k, v in value.items():
            yield k
            yield from walk_keys(v)
    elif isinstance(value, list):
        for v in value:
            yield from walk_keys(v)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("artifact_dir", type=Path)
    args = ap.parse_args()
    root = args.artifact_dir

    for name in REQUIRED_FILES:
        assert (root / name).is_file(), f"missing artifact: {name}"

    report = json.loads((root / "proof_path_v0_9_report.json").read_text(encoding="utf-8"))
    certs = json.loads((root / "proof_path_kernel_certificates_v0_9.json").read_text(encoding="utf-8"))
    quartet = json.loads((root / "pinch_quartet_v0_9.json").read_text(encoding="utf-8"))
    wounds = json.loads((root / "wounds_v0_9.json").read_text(encoding="utf-8"))
    with gzip.open(root / "mapeogeo_s5_v0_9_graph.json.gz", "rt", encoding="utf-8") as f:
        graph = json.load(f)

    assert report["status"] == "PASS"
    assert all(report["gates"].values()), report["gates"]
    assert len(certs) == 6
    assert {x["source_id"] for x in certs} == SUPPORT_IDS
    assert all(x["certificate_class"] == "KERNEL_VERIFIED" and x["status"] == "PASS" for x in certs)

    path = {x["source_id"]: x for x in report["path_results"]}
    assert path["srcdecl:theorem:6_16"]["status"].startswith("KERNEL_ACCEPTED")
    assert path["srcdecl:theorem:47_9"]["status"] == "WOUND_NO_PARSED_SOURCE_PROOF_PATH"
    assert path["srcdecl:definition:44_6"]["status"] == "LEAF_NO_CITED_PROOF_PATH"
    assert path["srcdecl:definition:53_4"]["status"] == "LEAF_NO_CITED_PROOF_PATH"

    repaired = [x for x in wounds if x.get("wound_id") == "wound:v09:proposition_6_11_ref_3_15"]
    assert len(repaired) == 1
    assert repaired[0]["status"] == "REPAIRED_VISIBLE"
    assert repaired[0]["legacy_resolved_target"] == "srcdecl:proposition:3_18"
    assert repaired[0]["audited_target"] == "srcdecl:proposition:3_15"

    assert len(quartet) == 4
    assert len({x["source_id"] for x in quartet}) == 4
    assert not ({x["source_id"] for x in quartet} & SUPPORT_IDS)
    assert all(x["pinch_score"] >= 0 and 0 <= x["view_shear"] <= 1 for x in quartet)

    node_ids = [n["id"] for n in graph["nodes"]]
    edge_ids = [e["id"] for e in graph["edges"]]
    node_set = set(node_ids)
    assert len(node_ids) == len(node_set)
    assert len(edge_ids) == len(set(edge_ids))
    assert all(e["source"] in node_set and e["target"] in node_set for e in graph["edges"])
    assert len(graph["nodes"]) >= 2234
    assert len(graph["edges"]) >= 23321

    # Source copyright boundary: the persistent graph may carry identity, hashes,
    # locators, derived structure, and verifier results, but not source prose/images.
    keys = set(walk_keys(graph))
    assert not (keys & FORBIDDEN_PERSISTED_KEYS), keys & FORBIDDEN_PERSISTED_KEYS

    metrics = report["batch_metrics"]
    assert metrics["source_intake"]["declarations_added"] == 0
    assert metrics["source_intake"]["proof_blocks_added"] == 0
    assert metrics["dependency_recovery"]["fallback_required"] is True
    assert metrics["certificates_added"]["KERNEL_VERIFIED_SUPPORT"] == 6
    assert metrics["certificates_added"]["KERNEL_ACCEPTED_PATH"] == 1

    print(
        "MAPEOGEO_V0_9_ARTIFACT_VALIDATION: PASS "
        f"certs={len(certs)} pinch={','.join(x['source_id'] for x in quartet)} "
        f"graph={len(graph['nodes'])}/{len(graph['edges'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
