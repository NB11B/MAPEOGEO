from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .cas import BlobStore, PayloadTooLargeError
from .config import NanoConfig, load_config
from .guard import IsolationViolationError, ResourceGuard, ResourcePressurePause
from .work_db import QueueItem, WorkDatabase


@dataclass
class FetchResult:
    queue_id: str
    url: str
    status: str  # "SUCCESS", "NOT_MODIFIED", "FAILED", "QUARANTINED", "RETRY_WAIT", "PAUSED"
    status_code: Optional[int] = None
    sha256: Optional[str] = None
    byte_size: int = 0
    is_new_blob: bool = False
    elapsed_sec: float = 0.0
    error_message: Optional[str] = None
    content_type: Optional[str] = None
    inferred_type: Optional[str] = None


def infer_content_type(header_type: Optional[str], sample_bytes: bytes) -> str:
    if sample_bytes.startswith(b"%PDF-"):
        return "pdf"
    lower_sample = sample_bytes[:512].lower()
    if b"<!doctype html" in lower_sample or b"<html" in lower_sample:
        return "html"
    if header_type:
        header_lower = header_type.lower()
        if "pdf" in header_lower:
            return "pdf"
        if "html" in header_lower:
            return "html"
        if "xml" in header_lower:
            return "xml"
        if "text" in header_lower:
            return "text"
        if "image" in header_lower:
            return "image"
    return "binary"


class AcquisitionDaemon:
    """Content-addressed acquisition daemon for SOVCTX-KG.

    Acquires sources strictly according to:
      - Resource governance backpressure
      - Physical isolation boundaries
      - Content-addressed deduplication
      - Payload size capping (100 MB max)
      - HTTP metadata preservation (ETag, Last-Modified, Content-Type)
      - Batch commits and WAL checkpointing
    """

    def __init__(
        self,
        config: Optional[NanoConfig] = None,
        db: Optional[WorkDatabase] = None,
        cas: Optional[BlobStore] = None,
        guard: Optional[ResourceGuard] = None,
    ) -> None:
        self.config = config or load_config()
        self.config.ensure_directories()
        self.guard = guard or ResourceGuard(self.config)
        self.db = db or WorkDatabase(self.config.work_db_path, self.config.sqlite)
        self.db.init_db()
        self.cas = cas or BlobStore(
            cas_root=self.config.raw_dir,
            max_payload_bytes=self.config.crawler.max_payload_mb * 1024 * 1024,
            quarantine_dir=self.config.quarantine_dir,
        )

    def fetch_single(self, item: QueueItem) -> FetchResult:
        start_time = time.monotonic()
        attempt_number = self.db.get_attempt_count(item.id) + 1

        # 1. Physical isolation check
        try:
            self.guard.assert_isolation(item.url, is_write=False)
        except IsolationViolationError as exc:
            elapsed = time.monotonic() - start_time
            self.db.record_fetch_attempt(
                queue_id=item.id,
                url=item.url,
                attempt_number=attempt_number,
                status_code=None,
                headers=None,
                bytes_downloaded=0,
                sha256=None,
                elapsed_sec=elapsed,
                error_message=str(exc),
            )
            self.db.record_quarantine(
                quarantine_reason="ISOLATION_VIOLATION_FORBIDDEN_PATH",
                url=item.url,
                metadata={"error": str(exc)},
            )
            self.db.update_queue_status(item.id, "QUARANTINED")
            return FetchResult(
                queue_id=item.id,
                url=item.url,
                status="QUARANTINED",
                elapsed_sec=elapsed,
                error_message=str(exc),
            )

        # 2. Resource governor check
        try:
            self.guard.assert_not_paused()
            sample = self.guard.sample(db=self.db)
            if sample.verdict == "STOP":
                raise ResourcePressurePause("; ".join(sample.reasons))
        except ResourcePressurePause as exc:
            # Revert queue item to QUEUED so it can be retried when pressure subsides
            self.db.update_queue_status(item.id, "QUEUED")
            return FetchResult(
                queue_id=item.id,
                url=item.url,
                status="PAUSED",
                elapsed_sec=time.monotonic() - start_time,
                error_message=str(exc),
            )

        # 3. Build HTTP request
        req = urllib.request.Request(item.url)
        req.add_header("User-Agent", self.config.crawler.user_agent)
        if item.etag:
            req.add_header("If-None-Match", item.etag)
        if item.last_modified:
            req.add_header("If-Modified-Since", item.last_modified)

        # 4. Execute HTTP fetch
        try:
            with urllib.request.urlopen(
                req,
                timeout=self.config.crawler.request_timeout_sec,
            ) as resp:
                elapsed = time.monotonic() - start_time
                status_code = resp.status if hasattr(resp, "status") else 200
                headers = dict(resp.headers)
                content_type = headers.get("Content-Type")
                new_etag = headers.get("ETag")
                new_last_modified = headers.get("Last-Modified")

                # Handle 304 Not Modified
                if status_code == 304:
                    self.db.record_fetch_attempt(
                        queue_id=item.id,
                        url=item.url,
                        attempt_number=attempt_number,
                        status_code=304,
                        headers=headers,
                        bytes_downloaded=0,
                        sha256=None,
                        elapsed_sec=elapsed,
                        error_message=None,
                    )
                    self.db.update_queue_status(
                        item.id, "ACQUIRED", etag=new_etag, last_modified=new_last_modified
                    )
                    return FetchResult(
                        queue_id=item.id,
                        url=item.url,
                        status="NOT_MODIFIED",
                        status_code=304,
                        elapsed_sec=elapsed,
                        content_type=content_type,
                    )

                # Store into CAS stream
                sha256, path, byte_size, is_new = self.cas.store_stream(resp)

                # Infer content type from sample bytes of stored blob
                sample_bytes = self.cas.read_blob(sha256)[:512]
                inferred = infer_content_type(content_type, sample_bytes)

                # Register in database CAS table
                rel_path = str(self.cas.blob_rel_path(sha256))
                self.db.register_blob(
                    sha256=sha256,
                    storage_path=rel_path,
                    byte_size=byte_size,
                    content_type=content_type,
                    inferred_type=inferred,
                    url=item.url,
                )

                # Record attempt
                self.db.record_fetch_attempt(
                    queue_id=item.id,
                    url=item.url,
                    attempt_number=attempt_number,
                    status_code=status_code,
                    headers=headers,
                    bytes_downloaded=byte_size,
                    sha256=sha256,
                    elapsed_sec=elapsed,
                    error_message=None,
                )

                # Mark queue item ACQUIRED
                self.db.update_queue_status(
                    item.id,
                    "ACQUIRED",
                    etag=new_etag,
                    last_modified=new_last_modified,
                )

                return FetchResult(
                    queue_id=item.id,
                    url=item.url,
                    status="SUCCESS",
                    status_code=status_code,
                    sha256=sha256,
                    byte_size=byte_size,
                    is_new_blob=is_new,
                    elapsed_sec=elapsed,
                    content_type=content_type,
                    inferred_type=inferred,
                )

        except urllib.error.HTTPError as err:
            elapsed = time.monotonic() - start_time
            headers = dict(err.headers) if hasattr(err, "headers") else {}
            status_code = err.code

            self.db.record_fetch_attempt(
                queue_id=item.id,
                url=item.url,
                attempt_number=attempt_number,
                status_code=status_code,
                headers=headers,
                bytes_downloaded=0,
                sha256=None,
                elapsed_sec=elapsed,
                error_message=str(err),
            )

            if status_code == 304:
                self.db.update_queue_status(item.id, "ACQUIRED")
                return FetchResult(
                    queue_id=item.id,
                    url=item.url,
                    status="NOT_MODIFIED",
                    status_code=304,
                    elapsed_sec=elapsed,
                )

            # Retry on rate limiting (429) or transient 5xx
            if status_code in (429, 502, 503, 504):
                self.db.update_queue_status(item.id, "RETRY_WAIT")
                return FetchResult(
                    queue_id=item.id,
                    url=item.url,
                    status="RETRY_WAIT",
                    status_code=status_code,
                    elapsed_sec=elapsed,
                    error_message=str(err),
                )

            # Fail closed on 404, 403, 410, etc.
            self.db.update_queue_status(item.id, "FAILED")
            return FetchResult(
                queue_id=item.id,
                url=item.url,
                status="FAILED",
                status_code=status_code,
                elapsed_sec=elapsed,
                error_message=str(err),
            )

        except PayloadTooLargeError as err:
            elapsed = time.monotonic() - start_time
            self.db.record_fetch_attempt(
                queue_id=item.id,
                url=item.url,
                attempt_number=attempt_number,
                status_code=None,
                headers=None,
                bytes_downloaded=0,
                sha256=None,
                elapsed_sec=elapsed,
                error_message=str(err),
            )
            self.db.record_quarantine(
                quarantine_reason="OVERSIZED_PAYLOAD_EXCEEDS_100MB",
                url=item.url,
                metadata={"error": str(err)},
            )
            self.db.update_queue_status(item.id, "QUARANTINED")
            return FetchResult(
                queue_id=item.id,
                url=item.url,
                status="QUARANTINED",
                elapsed_sec=elapsed,
                error_message=str(err),
            )

        except Exception as err:
            elapsed = time.monotonic() - start_time
            self.db.record_fetch_attempt(
                queue_id=item.id,
                url=item.url,
                attempt_number=attempt_number,
                status_code=None,
                headers=None,
                bytes_downloaded=0,
                sha256=None,
                elapsed_sec=elapsed,
                error_message=str(err),
            )
            # Transient connection or socket error -> retry wait
            self.db.update_queue_status(item.id, "RETRY_WAIT")
            return FetchResult(
                queue_id=item.id,
                url=item.url,
                status="RETRY_WAIT",
                elapsed_sec=elapsed,
                error_message=str(err),
            )

    def run_batch(self, max_items: Optional[int] = None) -> dict[str, Any]:
        run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        self.db.start_daemon_run("sovctx-acquire", run_id)

        target_count = max_items or self.config.batch.source_documents
        processed = 0
        succeeded = 0
        failed = 0
        quarantined = 0
        paused = False

        while processed < target_count:
            # Check resource governor
            if self.guard.is_paused():
                paused = True
                break

            item = self.db.get_next_queue_item(mark_in_progress=True)
            if not item:
                # No more queued items
                break

            result = self.fetch_single(item)
            processed += 1

            if result.status in ("SUCCESS", "NOT_MODIFIED"):
                succeeded += 1
            elif result.status == "QUARANTINED":
                quarantined += 1
            elif result.status == "PAUSED":
                paused = True
                break
            else:
                failed += 1

        # Checkpoint WAL after batch completes
        wal_stats = self.db.checkpoint_wal(mode="PASSIVE")

        run_status = "PAUSED_BY_GUARD" if paused else "COMPLETED"
        metrics = {
            "processed": processed,
            "succeeded": succeeded,
            "failed": failed,
            "quarantined": quarantined,
            "wal_checkpoint": wal_stats,
        }
        self.db.finish_daemon_run(run_id, status=run_status, metrics=metrics)

        return {
            "run_id": run_id,
            "status": run_status,
            "items_processed": processed,
            "items_succeeded": succeeded,
            "items_failed": failed,
            "items_quarantined": quarantined,
            "wal_checkpoint": wal_stats,
        }
