from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sovctx.node.config import load_config
from sovctx.node.ingest import IngestionEngine


def main() -> int:
    parser = argparse.ArgumentParser(description="SOVCTX N1 Deterministic Source & Passage Ingestion Engine")
    parser.add_argument("--config", type=Path, default=None, help="Path to config.yaml")
    parser.add_argument("--all", action="store_true", help="Ingest all unextracted CAS blobs")
    parser.add_argument("--sha256", type=str, default=None, help="Ingest specific CAS blob by SHA-256")
    parser.add_argument("--file", type=Path, default=None, help="Ingest local file into CAS and extract passages")
    parser.add_argument("--stats", action="store_true", help="Print N1 extraction statistics")
    args = parser.parse_args()

    config = load_config(args.config)
    engine = IngestionEngine(config)

    if args.file:
        if not args.file.exists():
            print(f"File not found: {args.file}", file=sys.stderr)
            return 1
        data = args.file.read_bytes()
        sha, path, byte_size, is_new = engine.cas.store_bytes(data)
        engine.db.register_blob(
            sha256=sha,
            storage_path=str(engine.cas.blob_rel_path(sha)),
            byte_size=byte_size,
            content_type="application/octet-stream",
            inferred_type="unknown",
            url=f"file://{args.file.name}",
        )
        res = engine.ingest_blob(sha, acquired_url=f"file://{args.file.name}")
        print(f"Ingested {args.file.name}:")
        print(f"  Source ID:  {res.source_id}")
        print(f"  Format:     {res.format}")
        print(f"  Status:     {res.status}")
        print(f"  Passages:   {res.passage_count}")
        print(f"  Equations:  {res.equation_witness_count}")
        return 0

    if args.sha256:
        res = engine.ingest_blob(args.sha256)
        print(f"Ingested {args.sha256}:")
        print(f"  Source ID:  {res.source_id}")
        print(f"  Format:     {res.format}")
        print(f"  Status:     {res.status}")
        print(f"  Passages:   {res.passage_count}")
        print(f"  Equations:  {res.equation_witness_count}")
        return 0

    if args.all:
        with engine.db.get_connection() as con:
            cur = con.execute("SELECT sha256, first_url FROM source_blobs")
            blobs = cur.fetchall()

        print(f"Ingesting {len(blobs)} CAS blobs...")
        total_passages = 0
        total_equations = 0
        ocr_candidates = 0

        for row in blobs:
            sha = row["sha256"]
            url = row["first_url"]
            res = engine.ingest_blob(sha, acquired_url=url)
            total_passages += res.passage_count
            total_equations += res.equation_witness_count
            if res.is_ocr_candidate:
                ocr_candidates += 1

        print(f"Ingestion complete:")
        print(f"  Blobs Processed:  {len(blobs)}")
        print(f"  Total Passages:   {total_passages}")
        print(f"  Equation Witnesses: {total_equations}")
        print(f"  OCR Candidates:   {ocr_candidates}")
        return 0

    # Default: stats
    with engine.db.get_connection() as con:
        source_count = con.execute("SELECT COUNT(*) FROM candidate_sources").fetchone()[0]
        frag_count = con.execute("SELECT COUNT(*) FROM candidate_fragments").fetchone()[0]
        ocr_count = con.execute(
            "SELECT COUNT(*) FROM candidate_sources WHERE status = 'OCR_CANDIDATE'"
        ).fetchone()[0]

    print("SOVCTX N1 Ingestion Engine Statistics:")
    print(f"  Candidate Sources:   {source_count}")
    print(f"  Candidate Passages:  {frag_count}")
    print(f"  OCR Candidates:      {ocr_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
