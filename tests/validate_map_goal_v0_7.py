#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path

FORBIDDEN={"text","excerpt","statement_text","proof_text","source_text","body","segment_text"}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("artifact_dir",type=Path); a=ap.parse_args()
    report=json.loads((a.artifact_dir/"map_goal_v0_7_report.json").read_text(encoding="utf-8"))
    graph=json.loads((a.artifact_dir/"mapeogeo_map_goal_v0_7_graph.json").read_text(encoding="utf-8"))
    certs=json.loads((a.artifact_dir/"v0_7_equivalence_certificates.json").read_text(encoding="utf-8"))
    assert report["status"]=="PASS", report["gates"]
    assert all(report["gates"].values())
    assert report["source"]["redistributed"] is False
    assert report["source"]["copyright_payload_policy"]=="HASHED_STATEMENT_METADATA_ONLY"
    assert report["overall_goal"]["statement"]
    assert len(certs)==4 and all(c["status"]=="PASS" for c in certs)
    assert report["same_semantics_promotions"]>=2
    nodes,edges=graph["nodes"],graph["edges"]
    by={n["id"]:n for n in nodes}
    assert len(by)==len(nodes); assert len({e["id"] for e in edges})==len(edges)
    assert all(e["source"] in by and e["target"] in by for e in edges)
    assert all(not (FORBIDDEN & set(n.get("attributes",{}))) for n in nodes)
    print("MAPEOGEO_V0_7_ARTIFACT_VALIDATION: PASS "
          f"holdout={report['holdout']['edges']} dual_mrr={report['retrieval']['dual']['mrr']:.5f} "
          f"recall={report['candidate_filter']['recall']:.4f} reduction={report['candidate_filter']['mean_candidate_reduction']:.4f} "
          f"same={report['same_semantics_promotions']} graph={len(nodes)}/{len(edges)}")
    return 0
if __name__=="__main__": raise SystemExit(main())
