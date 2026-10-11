from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sovctx.node.acquire import AcquisitionDaemon
from sovctx.node.config import load_config
from sovctx.node.work_db import QueueItem, utc_now_iso


def main() -> int:
    parser = argparse.ArgumentParser(description="SOVCTX Content-Addressed Acquisition Daemon")
    parser.add_argument("--config", type=Path, default=None, help="Path to config.yaml")
    parser.add_argument("--batch", type=int, default=None, help="Process a batch of N queued items")
    parser.add_argument("--url", type=str, default=None, help="Acquire a single URL immediately for testing")
    parser.add_argument("--priority", type=str, default="P0", help="Priority when enqueueing single URL")
    args = parser.parse_args()

    config = load_config(args.config)
    daemon = AcquisitionDaemon(config)

    if args.url:
        print(f"Acquiring single URL: {args.url}")
        queue_id = daemon.db.enqueue(url=args.url, priority=args.priority, goal="CLI direct test fetch")
        item = QueueItem(
            id=queue_id,
            source_id=None,
            url=args.url,
            priority=args.priority,
            status="IN_PROGRESS",
            goal="CLI direct test fetch",
            etag=None,
            last_modified=None,
            depth=0,
            nominated_by="cli:direct",
            created_at=utc_now_iso(),
            updated_at=utc_now_iso(),
        )
        res = daemon.fetch_single(item)
        print(json.dumps(res.__dict__, indent=2))
        return 0 if res.status in ("SUCCESS", "NOT_MODIFIED") else 1

    # Batch run
    batch_size = args.batch or config.batch.source_documents
    print(f"Running acquisition batch (target={batch_size} items)...")
    res = daemon.run_batch(max_items=batch_size)
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
