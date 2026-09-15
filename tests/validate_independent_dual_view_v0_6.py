#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

FORBIDDEN={"text","excerpt","statement_text","proof_text","source_text","body","segment_text"}

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("artifact_dir",type=Path); a=ap.parse_args()
    report=json.loads((a.artifact_dir/"independent_dual_view_report.json").read_text(encoding="utf-8"))
    profiles=json.loads((a.artifact_dir/"independent_statement_profiles.json").read_text(encoding="utf-8"))
    graph=json.loads((a.artifact_dir/"mapeogeo_independent_graph.json").read_text(encoding="utf-8"))
    assert report["status"]=="PASS", report.get("gates")
    assert all(report["gates"].values())
    assert report["source"]["redistributed"] is False
    assert report["source"]["copyright_payload_policy"]=="HASHED_STATEMENT_METADATA_ONLY"
    assert report["independent_views"]["fixture_recovery"]=={"total":20,"recovered":20,"missing":[]}
    assert profiles
    for p in profiles:
        assert "source_segment_sha256" in p
        assert "statement_sha256" in p
        assert isinstance(p["eo_direct_families"],list)
        assert isinstance(p["geo_direct_families"],list)
        assert p["direct_status"] in {"DUAL_DIRECT","EO_ONLY_DIRECT","GEO_ONLY_DIRECT","NO_DIRECT_VIEW"}
    nodes,edges=graph["nodes"],graph["edges"]
    by={n["id"]:n for n in nodes}
    assert len(by)==len(nodes)
    assert len({e["id"] for e in edges})==len(edges)
    assert all(e["source"] in by and e["target"] in by for e in edges)
    for n in nodes:
        assert not FORBIDDEN.intersection(n.get("attributes",{})), (n["id"],FORBIDDEN.intersection(n.get("attributes",{})))
    print(
        "MAPEOGEO_V0_6_ARTIFACT_VALIDATION: PASS "
        f"declarations={report['extraction']['declarations']} "
        f"eo_direct={report['independent_views']['eo_direct_coverage']:.4f} "
        f"geo_direct={report['independent_views']['geo_direct_coverage']:.4f} "
        f"dual_direct={report['independent_views']['dual_direct_coverage']:.4f} "
        f"eo_p={report['dependency_alignment']['eo']['one_sided_permutation_p']:.4g} "
        f"geo_p={report['dependency_alignment']['geo']['one_sided_permutation_p']:.4g}"
    )
    return 0

if __name__=="__main__": raise SystemExit(main())
