#!/usr/bin/env python3
from __future__ import annotations
import argparse, gzip, json
from pathlib import Path

FORBIDDEN={"text","excerpt","statement_text","proof_text","source_text","body","segment_text"}

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("artifact_dir",type=Path); a=ap.parse_args()
    report=json.loads((a.artifact_dir/"formal_bridge_v0_8_report.json").read_text(encoding="utf-8"))
    certs=json.loads((a.artifact_dir/"formal_kernel_certificates_v0_8.json").read_text(encoding="utf-8"))
    with gzip.open(a.artifact_dir/"mapeogeo_formal_v0_8_graph.json.gz","rt",encoding="utf-8") as f:
        graph=json.load(f)
    assert report["status"]=="PASS", report["gates"]
    assert all(report["gates"].values())
    assert report["source"]["redistributed"] is False
    assert report["source"]["copyright_payload_policy"]=="HASHED_LOCATOR_METADATA_ONLY"
    assert len(certs)==4 and all(c["status"]=="PASS" and c["certificate_class"]=="KERNEL_VERIFIED" for c in certs)
    nodes,edges=graph["nodes"],graph["edges"]
    by={n["id"]:n for n in nodes}
    assert len(by)==len(nodes)
    assert len({e["id"] for e in edges})==len(edges)
    assert all(e["source"] in by and e["target"] in by for e in edges)
    for n in nodes:
        assert not FORBIDDEN.intersection(n.get("attributes",{}))
    formal=[n for n in nodes if n.get("view")=="FORMAL" and n["id"].startswith("formal:lean:")]
    assert len(formal)>=4
    print(f"MAPEOGEO_V0_8_ARTIFACT_VALIDATION: PASS certs={len(certs)} formal={len(formal)} graph={len(nodes)}/{len(edges)}")
    return 0

if __name__=="__main__": raise SystemExit(main())
