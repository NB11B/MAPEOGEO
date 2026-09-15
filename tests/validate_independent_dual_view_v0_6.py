#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

FORBIDDEN={"text","excerpt","statement_text","proof_text","source_text","body","segment_text"}

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("artifact_dir",type=Path); a=ap.parse_args()
    report=json.loads((a.artifact_dir/"independent_dual_view_report.json").read_text())
    profiles=json.loads((a.artifact_dir/"independent_statement_profiles.json").read_text())
    graph=json.loads((a.artifact_dir/"mapeogeo_independent_graph.json").read_text())
    assert report["status"]=="PASS", report.get("gates")
    assert all(report["gates"].values())
    assert report["source"]["redistributed"] is False
    assert report["source"]["copyright_payload_policy"]=="INDEPENDENT_METADATA_ONLY"
    assert report["fixture_recovery"]=={"total":20,"recovered":20,"missing":[]}
    assert profiles
    for p in profiles:
        assert "source_segment_sha256" in p
        ip=p["independent_profile"]
        assert isinstance(ip["eo_direct_families"],list)
        assert isinstance(ip["geo_direct_families"],list)
    nodes,edges=graph["nodes"],graph["edges"]
    by={n["id"]:n for n in nodes}
    assert len(by)==len(nodes)
    assert len({e["id"] for e in edges})==len(edges)
    assert all(e["source"] in by and e["target"] in by for e in edges)
    for n in nodes:
        assert not FORBIDDEN.intersection(n.get("attributes",{})), (n["id"],FORBIDDEN.intersection(n.get("attributes",{})))
    print(
        "MAPEOGEO_V0_6_ARTIFACT_VALIDATION: PASS "
        f"declarations={report['extraction']['deduplicated_declarations']} "
        f"eo_direct={report['coverage']['eo_direct_coverage']:.4f} "
        f"geo_direct={report['coverage']['geo_direct_coverage']:.4f} "
        f"dual_direct={report['coverage']['independent_dual_direct_coverage']:.4f} "
        f"eo_p={report['dependency_alignment']['eo']['permutation_p_one_sided']:.4g} "
        f"geo_p={report['dependency_alignment']['geo']['permutation_p_one_sided']:.4g}"
    )
    return 0

if __name__=="__main__": raise SystemExit(main())
