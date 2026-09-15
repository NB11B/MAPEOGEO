#!/usr/bin/env python3
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
graph=json.loads((ROOT/"data"/"gallier_quaintance_graph_v0_3.json").read_text(encoding="utf-8"))
res=json.loads((ROOT/"data"/"gallier_quaintance_results_v0_3.json").read_text(encoding="utf-8"))
nodes=graph["nodes"]; edges=graph["edges"]; by_id={n["id"]:n for n in nodes}
assert len(by_id)==len(nodes)
assert len({e["id"] for e in edges})==len(edges)
assert all(e["source"] in by_id and e["target"] in by_id for e in edges)
views=defaultdict(set)
for n in nodes:
    if n.get("semantic_id") and n.get("view"):
        views[n["semantic_id"]].add(n["view"])
assert views and all(v=={"EO","GEO"} for v in views.values())
for e in edges:
    if e["type"]=="SAME_SEMANTICS":
        a,b=by_id[e["source"]],by_id[e["target"]]
        assert a.get("semantic_id")==b.get("semantic_id")
        assert a.get("view")!=b.get("view")
assert res["overall_status"]=="PASS"
assert all(t["status"]=="PASS" for t in res["tests"])
print(
    "MAPEOGEO_V0_3_VALIDATION: PASS "
    f"nodes={len(nodes)} edges={len(edges)} "
    f"semantic_objects={len(views)} checks={res['total_executable_checks']}"
)
