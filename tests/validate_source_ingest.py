#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("artifact_dir", type=Path)
    args = ap.parse_args()

    report = json.loads((args.artifact_dir / "source_ingest_report.json").read_text(encoding="utf-8"))
    graph = json.loads((args.artifact_dir / "mapeogeo_source_graph.json").read_text(encoding="utf-8"))
    declarations = json.loads((args.artifact_dir / "source_declarations.json").read_text(encoding="utf-8"))

    assert report["status"] == "PASS", report
    assert report["source"]["redistributed"] is False
    assert report["source"]["copyright_payload_policy"] == "METADATA_HASHES_ONLY"
    assert declarations
    assert all("source_segment_sha256" in d for d in declarations)

    nodes = graph["nodes"]
    edges = graph["edges"]
    by_id = {n["id"]: n for n in nodes}
    assert len(by_id) == len(nodes)
    assert len({e["id"] for e in edges}) == len(edges)
    assert all(e["source"] in by_id and e["target"] in by_id for e in edges)

    forbidden = {"text", "excerpt", "statement_text", "proof_text", "source_text", "body"}
    for n in nodes:
        attrs = n.get("attributes", {})
        assert not forbidden.intersection(attrs), (n["id"], forbidden.intersection(attrs))

    print(
        "MAPEOGEO_SOURCE_ARTIFACT_VALIDATION: PASS "
        f"declarations={report['extraction']['deduplicated_declarations']} "
        f"proofs={report['extraction']['proof_blocks_detected']} "
        f"resolved_dependencies={report['dependencies']['resolved_dependency_references']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
