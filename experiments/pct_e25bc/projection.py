from __future__ import annotations

import json
from pathlib import Path

from . import multipath as _multipath

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence"


def load_trust_projection() -> dict:
    manifest = json.loads((EVIDENCE / "pct_e25b_trust_projection.json").read_text(encoding="utf-8"))
    nodes = [
        {"id": "c", "attributes": {"status": "PASS"}},
        {"id": "cert:v07:theorem:6_16", "attributes": {"status": "PASS"}},
    ]
    edges = []
    for i in range(1, manifest["synthetic_equivalence_triangles"] + 1):
        obj, eo, geo = f"o{i}", f"e{i}", f"g{i}"
        nodes.extend(({"id": obj}, {"id": eo}, {"id": geo}))
        edges.extend((
            {"id": f"a{i}", "source": eo, "target": obj, "type": "REPRESENTS"},
            {"id": f"b{i}", "source": geo, "target": obj, "type": "REPRESENTS"},
            {"id": f"c{i}", "source": eo, "target": geo, "type": "SAME_SEMANTICS"},
            {"id": f"d{i}", "source": obj, "target": "c", "type": "VERIFIED_BY"},
        ))
    for j, cycle in enumerate(manifest["real_cycles"], 1):
        h = cycle["source_statement_sha256"]
        nodes.extend((
            {"id": cycle["anchor"], "attributes": {"source_statement_sha256": h}},
            {"id": cycle["eo"], "attributes": {"source_statement_sha256": h, "contract": cycle["contract"]}},
            {"id": cycle["geo"], "attributes": {"source_statement_sha256": h, "contract": cycle["contract"]}},
            {"id": cycle["formal"], "attributes": {"source_statement_sha256": h, "formal_scope": cycle["formal_scope"]}},
        ))
        cert = "cert:v07:theorem:6_16" if cycle["contract"] == "rank" else "c"
        p = f"r{j}"
        edges.extend((
            {"id": p + "a", "source": cycle["eo"], "target": cycle["anchor"], "type": "REPRESENTS"},
            {"id": p + "b", "source": cycle["geo"], "target": cycle["anchor"], "type": "REPRESENTS"},
            {"id": p + "c", "source": cycle["formal"], "target": cycle["anchor"], "type": "REPRESENTS"},
            {"id": p + "d", "source": cycle["eo"], "target": cycle["geo"], "type": "SAME_SEMANTICS"},
            {"id": p + "e", "source": cycle["formal"], "target": cycle["eo"], "type": "EQUIVALENT_TO"},
            {"id": p + "f", "source": cycle["formal"], "target": cycle["geo"], "type": "EQUIVALENT_TO"},
            {"id": p + "g", "source": cycle["anchor"], "target": cert, "type": "VERIFIED_BY"},
        ))
    return {
        "source_artifact": manifest["source_artifact"],
        "edge_scope": manifest["edge_scope"],
        "nodes": nodes,
        "edges": edges,
    }


# Existing multipath/executable modules share one loader contract. Patch that
# dependency before executable.py imports the symbol.
_multipath.load_trust_projection = load_trust_projection
run_e25b = _multipath.run_e25b
