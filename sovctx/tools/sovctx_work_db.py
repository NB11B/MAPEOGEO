from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sovctx.node.config import load_config
from sovctx.node.work_db import WorkDatabase


def main() -> int:
    parser = argparse.ArgumentParser(description="SOVCTX Work Database Manager")
    parser.add_argument("--config", type=Path, default=None, help="Path to config.yaml")
    parser.add_argument("--init", action="store_true", help="Initialize schema and metadata")
    parser.add_argument("--import-canonical", action="store_true", help="Import canonical ingestion queue into work db")
    parser.add_argument("--stats", action="store_true", help="Show queue and database statistics")
    parser.add_argument("--checkpoint", action="store_true", help="Execute WAL checkpoint")
    parser.add_argument("--enqueue", type=str, default=None, help="Enqueue a single URL")
    parser.add_argument("--priority", type=str, default="P1", help="Queue priority (P0, P1, P2)")
    parser.add_argument("--goal", type=str, default=None, help="Goal description for enqueued URL")
    args = parser.parse_args()

    config = load_config(args.config)
    config.ensure_directories()
    db = WorkDatabase(config.work_db_path, config.sqlite)

    if args.init:
        db.init_db()
        print(f"Work database initialized at {config.work_db_path}")

    if args.enqueue:
        qid = db.enqueue(url=args.enqueue, priority=args.priority, goal=args.goal)
        print(f"Enqueued {args.enqueue} as {qid} ({args.priority})")

    if args.import_canonical:
        q_path = (
            config.root / "sovctx" / "corpus" / "ingestion_queue.jsonl"
            if (config.root / "sovctx" / "corpus" / "ingestion_queue.jsonl").exists()
            else config.root / "corpus" / "ingestion_queue.jsonl"
        )
        s_path = (
            config.root / "sovctx" / "corpus" / "sources.jsonl"
            if (config.root / "sovctx" / "corpus" / "sources.jsonl").exists()
            else config.root / "corpus" / "sources.jsonl"
        )
        count = db.import_canonical_queue(q_path, s_path)
        print(f"Imported {count} items from canonical ingestion queue into {config.work_db_path}")

    if args.checkpoint:
        busy, log, ckpt = db.checkpoint_wal(mode="TRUNCATE")
        print(f"WAL Checkpoint (TRUNCATE): busy={busy}, log={log}, checkpointed={ckpt}")

    if args.stats or (not args.init and not args.enqueue and not args.import_canonical and not args.checkpoint):
        db.init_db()
        stats = db.get_queue_stats()
        with db.connect() as con:
            blob_count = con.execute("SELECT COUNT(*) FROM source_blobs").fetchone()[0]
            attempt_count = con.execute("SELECT COUNT(*) FROM fetch_attempts").fetchone()[0]
            cand_src_count = con.execute("SELECT COUNT(*) FROM candidate_sources").fetchone()[0]
            quarantine_count = con.execute("SELECT COUNT(*) FROM quarantine").fetchone()[0]
            samples_count = con.execute("SELECT COUNT(*) FROM resource_samples").fetchone()[0]

        summary = {
            "database_path": str(config.work_db_path),
            "queue_by_status": stats,
            "total_queued": sum(stats.values()),
            "source_blobs": blob_count,
            "fetch_attempts": attempt_count,
            "candidate_sources": cand_src_count,
            "quarantined_items": quarantine_count,
            "resource_samples": samples_count,
        }
        print(json.dumps(summary, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
