from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path

import build_sqlite
import query_graph
import qualify_equations
import validate_graph
from graph_io import canonical_digest, load_records, split_records


def qualify() -> dict[str, object]:
    validate_graph.main()
    equation_result = qualify_equations.qualify()
    assert equation_result["status"] == "PASS", equation_result

    records = load_records()
    nodes, edges = split_records(records)
    node_by_id = {node["id"]: node for node in nodes}

    with tempfile.TemporaryDirectory(prefix="sovctx-") as tmp:
        db_path = Path(tmp) / "sovctx.sqlite"
        materialized = build_sqlite.build_database(db_path)

        con = sqlite3.connect(db_path)
        try:
            db_nodes = con.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
            db_edges = con.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
            db_fragments = con.execute("SELECT COUNT(*) FROM source_fragments").fetchone()[0]
            db_claim_fragments = con.execute("SELECT COUNT(*) FROM claim_fragments").fetchone()[0]
            db_digest = con.execute(
                "SELECT value FROM metadata WHERE key='canonical_sha256'"
            ).fetchone()[0]
        finally:
            con.close()

    expected_fragments = sum(1 for node in nodes if node["type"] == "SOURCE_FRAGMENT")
    expected_claim_fragments = sum(
        len(node.get("source_fragment_ids", []))
        for node in nodes
        if node["type"] == "CLAIM"
    )

    assert db_nodes == len(nodes)
    assert db_edges == len(edges)
    assert db_fragments == expected_fragments
    assert db_claim_fragments == expected_claim_fragments
    assert db_digest == canonical_digest()
    assert materialized["canonical_sha256"] == canonical_digest()

    path = query_graph.shortest_path(
        "PUB:GELFAND_TSETLIN_1961_NONLOCAL",
        "PERSON:BERNSTEIN_NA",
        node_by_id,
        edges,
        max_depth=4,
        documented_only=True,
        source_native_only=True,
    )
    assert path, "documented source-native Gelfand-Tsetlin -> Bernstein path missing"

    ancestry_path = query_graph.shortest_path(
        "PERSON:MARKOV_AA",
        "PERSON:LEIBNIZ_GW",
        node_by_id,
        edges,
        max_depth=5,
        documented_only=True,
        source_native_only=True,
    )
    assert ancestry_path, "documented Markov -> Chebyshev -> Euler -> Leibniz ancestry path missing"

    open_questions = [
        node["id"]
        for node in nodes
        if node["type"] == "OPEN_QUESTION"
    ]
    assert "OPEN:GZ_FORCE_COUPLING" in open_questions

    family_counts: dict[str, int] = {}
    for edge in edges:
        if edge["edge_type"] == "MEMBER_OF_EQUATION_FAMILY":
            family_counts[edge["target"]] = family_counts.get(edge["target"], 0) + 1

    assert family_counts.get("FAMILY:TIKHONOV_REGULARIZATION") == 4
    assert family_counts.get("FAMILY:VLASOV_COLLECTIVE_FIELD") == 4
    assert family_counts.get("FAMILY:LEIBNIZ_DIFFERENTIAL_RULES") == 2
    assert family_counts.get("FAMILY:LYAPUNOV_STABILITY") == 1
    assert family_counts.get("FAMILY:GELFAND_LEVITAN_INVERSE_SPECTRAL") == 3
    assert family_counts.get("FAMILY:PONTRYAGIN_OPTIMAL_CONTROL") == 5
    assert family_counts.get("FAMILY:CHEBYSHEV_MECHANISM_SYNTHESIS") == 3

    return {
        "status": "PASS",
        "canonical_sha256": canonical_digest(),
        "nodes": len(nodes),
        "edges": len(edges),
        "source_fragments": expected_fragments,
        "claim_fragment_links": expected_claim_fragments,
        "documented_gt1961_bernstein_path_length": len(path),
        "documented_markov_leibniz_path_length": len(ancestry_path),
        "open_questions": len(open_questions),
        "equation_family_counts": family_counts,
        "equation_behavior_status": equation_result["status"],
        "equation_behavior_pass_count": equation_result["pass_count"],
        "equation_behavior_fail_count": equation_result["fail_count"],
    }


def main() -> int:
    print(json.dumps(qualify(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
