from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

from graph_io import ROOT, canonical_digest, load_records, split_records


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE nodes (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    namespace TEXT NOT NULL,
    label TEXT NOT NULL,
    verification_status TEXT,
    publication_date TEXT,
    payload_json TEXT NOT NULL
);

CREATE TABLE edges (
    id TEXT PRIMARY KEY,
    edge_type TEXT NOT NULL,
    source TEXT NOT NULL,
    target TEXT NOT NULL,
    namespace TEXT NOT NULL,
    label TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    FOREIGN KEY(source) REFERENCES nodes(id),
    FOREIGN KEY(target) REFERENCES nodes(id)
);

CREATE TABLE source_fragments (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    locator TEXT NOT NULL,
    verification_status TEXT NOT NULL,
    evidence_basis TEXT NOT NULL,
    normalized_summary TEXT,
    payload_json TEXT NOT NULL,
    FOREIGN KEY(id) REFERENCES nodes(id),
    FOREIGN KEY(source_id) REFERENCES nodes(id)
);

CREATE TABLE claim_fragments (
    claim_id TEXT NOT NULL,
    fragment_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    PRIMARY KEY (claim_id, fragment_id),
    FOREIGN KEY(claim_id) REFERENCES nodes(id),
    FOREIGN KEY(fragment_id) REFERENCES nodes(id),
    FOREIGN KEY(source_id) REFERENCES nodes(id)
);

CREATE INDEX idx_nodes_type ON nodes(type);
CREATE INDEX idx_nodes_namespace ON nodes(namespace);
CREATE INDEX idx_edges_source ON edges(source);
CREATE INDEX idx_edges_target ON edges(target);
CREATE INDEX idx_edges_type ON edges(edge_type);
CREATE INDEX idx_fragments_source ON source_fragments(source_id);
CREATE INDEX idx_claim_fragments_source ON claim_fragments(source_id);
"""


def build_database(output: Path) -> dict[str, int | str]:
    records = load_records()
    nodes, edges = split_records(records)
    node_by_id = {node["id"]: node for node in nodes}

    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()

    con = sqlite3.connect(output)
    try:
        con.executescript(SCHEMA)
        con.execute(
            "INSERT INTO metadata(key, value) VALUES (?, ?)",
            ("canonical_sha256", canonical_digest()),
        )
        con.execute(
            "INSERT INTO metadata(key, value) VALUES (?, ?)",
            ("schema_version", "0.1"),
        )

        for node in sorted(nodes, key=lambda item: item["id"]):
            con.execute(
                """
                INSERT INTO nodes(
                    id, type, namespace, label, verification_status,
                    publication_date, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    node["id"],
                    node["type"],
                    node["namespace"],
                    node["label"],
                    node.get("verification_status"),
                    node.get("publication_date"),
                    json.dumps(node, ensure_ascii=False, sort_keys=True),
                ),
            )

        for edge in sorted(edges, key=lambda item: item["id"]):
            if edge["source"] not in node_by_id or edge["target"] not in node_by_id:
                raise ValueError(f"edge {edge['id']} references unknown endpoint")
            con.execute(
                """
                INSERT INTO edges(
                    id, edge_type, source, target, namespace, label, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    edge["id"],
                    edge["edge_type"],
                    edge["source"],
                    edge["target"],
                    edge["namespace"],
                    edge["label"],
                    json.dumps(edge, ensure_ascii=False, sort_keys=True),
                ),
            )

        fragments = [node for node in nodes if node["type"] == "SOURCE_FRAGMENT"]
        for fragment in sorted(fragments, key=lambda item: item["id"]):
            con.execute(
                """
                INSERT INTO source_fragments(
                    id, source_id, locator, verification_status,
                    evidence_basis, normalized_summary, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    fragment["id"],
                    fragment["source_id"],
                    fragment["locator"],
                    fragment["verification_status"],
                    fragment["evidence_basis"],
                    fragment.get("normalized_summary"),
                    json.dumps(fragment, ensure_ascii=False, sort_keys=True),
                ),
            )

        claims = [node for node in nodes if node["type"] == "CLAIM"]
        for claim in sorted(claims, key=lambda item: item["id"]):
            for fragment_id in sorted(claim.get("source_fragment_ids", [])):
                fragment = node_by_id[fragment_id]
                con.execute(
                    """
                    INSERT INTO claim_fragments(claim_id, fragment_id, source_id)
                    VALUES (?, ?, ?)
                    """,
                    (claim["id"], fragment_id, fragment["source_id"]),
                )

        con.commit()
    finally:
        con.close()

    return {
        "nodes": len(nodes),
        "edges": len(edges),
        "source_fragments": len(fragments),
        "canonical_sha256": canonical_digest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Materialize canonical SOVCTX JSONL as SQLite.")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / ".build" / "sovctx.sqlite",
        help="Output SQLite path.",
    )
    args = parser.parse_args()
    stats = build_database(args.output)
    print(json.dumps({"output": str(args.output), **stats}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
