#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

FORBIDDEN = {"text","excerpt","statement_text","proof_text","source_text","body","segment_text"}

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("artifact_dir",type=Path); a=ap.parse_args()
    report=json.loads((a.artifact_dir/"corpus_dualization_report.json").read_text(encoding="utf-8"))
    profiles=json.loads((a.artifact_dir/"semantic_profiles.json").read_text(encoding="utf-8"))
    graph=json.loads((a.artifact_dir/"mapeogeo_corpus_graph.json").read_text(encoding="utf-8"))
    assert report["status"]=="PASS", report.get("gates")
    assert all(report["gates"].values())
    assert report["source"]["redistributed"] is False
    assert report["source"]["copyright_payload_policy"]=="CONTROLLED_METADATA_ONLY"
    assert report["extraction"]["declarations_by_kind"].get("Definition",0)>0
    assert report["dualization"]["v0_3_fixture_ontology_recovery"]=={"total":20,"recovered":20,"missing":[]}
    assert profiles
    for p in profiles:
        assert "source_segment_sha256" in p
        sp=p["semantic_profile"]
        assert sp["dualization_status"] in {"DUAL_CANDIDATE","EO_ONLY_CANDIDATE","GEO_ONLY_CANDIDATE","UNCLASSIFIED"}
    nodes,edges=graph["nodes"],graph["edges"]
    by={n["id"]:n for n in nodes}
    assert len(by)==len(nodes)
    assert len({e["id"] for e in edges})==len(edges)
    assert all(e["source"] in by and e["target"] in by for e in edges)
    for n in nodes:
        assert not FORBIDDEN.intersection(n.get("attributes",{})), (n["id"], FORBIDDEN.intersection(n.get("attributes",{})))
    print(
        "MAPEOGEO_V0_5_ARTIFACT_VALIDATION: PASS "
        f"declarations={report['extraction']['deduplicated_declarations']} "
        f"definitions={report['extraction']['declarations_by_kind'].get('Definition',0)} "
        f"direct_tag_coverage={report['dualization']['direct_tag_coverage']:.4f} "
        f"dual_candidate_coverage={report['dualization']['dual_candidate_coverage']:.4f} "
        f"graph={report['graph']['nodes']}/{report['graph']['edges']}"
    )
    return 0

if __name__=="__main__": raise SystemExit(main())
