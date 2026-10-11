from __future__ import annotations

import http.server
import json
import socketserver
import tempfile
import threading
from pathlib import Path
from typing import Any

import pytest

from sovctx.node.acquire import AcquisitionDaemon
from sovctx.node.cas import BlobStore
from sovctx.node.config import CrawlerSettings, IsolationConfig, NanoConfig, ResourceLimits
from sovctx.node.guard import ResourceGuard
from sovctx.node.work_db import WorkDatabase


class MockHTTPHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        pass  # Quiet logging

    def do_GET(self) -> None:
        if self.path.startswith("/source.html"):
            if self.headers.get("If-None-Match") == '"test-etag-1"':
                self.send_response(304)
                self.end_headers()
                return
            content = b"<!DOCTYPE html><html><body>Soviet Cybernetics 1961</body></html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("ETag", '"test-etag-1"')
            self.send_header("Last-Modified", "Wed, 21 Oct 2026 07:28:00 GMT")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        elif self.path == "/paper.pdf":
            content = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
            self.send_response(200)
            self.send_header("Content-Type", "application/pdf")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        elif self.path == "/oversized.bin":
            content = b"A" * (2 * 1024 * 1024)  # 2 MB
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        elif self.path == "/rate_limit":
            self.send_response(429)
            self.end_headers()

        elif self.path == "/not_found":
            self.send_response(404)
            self.end_headers()

        else:
            self.send_response(404)
            self.end_headers()


@pytest.fixture(scope="module")
def mock_server():
    server = socketserver.TCPServer(("127.0.0.1", 0), MockHTTPHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
    server.server_close()


def test_acquisition_html_and_pdf(mock_server: str) -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        data_root = Path(tmp_dir)
        config = NanoConfig(root=data_root, data_root=data_root)
        daemon = AcquisitionDaemon(config)

        # 1. Fetch HTML source
        qid_html = daemon.db.enqueue(f"{mock_server}/source.html", priority="P0")
        item_html = daemon.db.get_next_queue_item()
        assert item_html is not None
        assert item_html.id == qid_html

        res_html = daemon.fetch_single(item_html)
        assert res_html.status == "SUCCESS"
        assert res_html.status_code == 200
        assert res_html.inferred_type == "html"
        assert res_html.is_new_blob is True
        assert daemon.cas.has_blob(res_html.sha256)

        # 2. Fetch with 304 Not Modified
        item_304 = daemon.db.get_next_queue_item()  # Should be None since it was acquired
        assert item_304 is None
        # Re-fetch the same item with etag
        item_recheck = daemon.db.get_next_queue_item(mark_in_progress=False)
        assert item_recheck is None
        with daemon.db.get_connection() as con:
            row = con.execute("SELECT * FROM fetch_queue WHERE id=?", (qid_html,)).fetchone()
            assert row["status"] == "ACQUIRED"
            assert row["etag"] == '"test-etag-1"'

        # 3. Fetch PDF source
        daemon.db.enqueue(f"{mock_server}/paper.pdf", priority="P0")
        item_pdf = daemon.db.get_next_queue_item()
        res_pdf = daemon.fetch_single(item_pdf)
        assert res_pdf.status == "SUCCESS"
        assert res_pdf.status_code == 200
        assert res_pdf.inferred_type == "pdf"


def test_acquisition_fault_handling(mock_server: str) -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        data_root = Path(tmp_dir)
        config = NanoConfig(root=data_root, data_root=data_root)
        daemon = AcquisitionDaemon(config)

        # 1. 404 Not Found
        daemon.db.enqueue(f"{mock_server}/not_found", priority="P1")
        item_404 = daemon.db.get_next_queue_item()
        res_404 = daemon.fetch_single(item_404)
        assert res_404.status == "FAILED"
        assert res_404.status_code == 404

        # 2. 429 Rate Limit
        daemon.db.enqueue(f"{mock_server}/rate_limit", priority="P1")
        item_429 = daemon.db.get_next_queue_item()
        res_429 = daemon.fetch_single(item_429)
        assert res_429.status == "RETRY_WAIT"
        assert res_429.status_code == 429


def test_acquisition_oversized_payload_quarantine(mock_server: str) -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        data_root = Path(tmp_dir)
        # Configure max payload size to 1 MB so the 2 MB test file triggers oversized rejection
        crawler = CrawlerSettings(max_payload_mb=1)
        config = NanoConfig(root=data_root, data_root=data_root, crawler=crawler)
        daemon = AcquisitionDaemon(config)

        daemon.db.enqueue(f"{mock_server}/oversized.bin", priority="P0")
        item = daemon.db.get_next_queue_item()
        res = daemon.fetch_single(item)

        assert res.status == "QUARANTINED"
        with daemon.db.get_connection() as con:
            row = con.execute("SELECT * FROM quarantine").fetchone()
            assert row is not None
            assert "OVERSIZED_PAYLOAD" in row["quarantine_reason"]


def test_acquisition_governor_backpressure(mock_server: str) -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        data_root = Path(tmp_dir)
        config = NanoConfig(root=data_root, data_root=data_root)
        daemon = AcquisitionDaemon(config)

        daemon.db.enqueue(f"{mock_server}/source.html", priority="P0")
        item = daemon.db.get_next_queue_item()

        # Artificially trigger guard pause
        daemon.guard.set_pause(["Thermal limit exceeded 78C >= 77C"])

        res = daemon.fetch_single(item)
        assert res.status == "PAUSED"

        # Item should be reverted to QUEUED
        with daemon.db.get_connection() as con:
            row = con.execute("SELECT * FROM fetch_queue WHERE id=?", (item.id,)).fetchone()
            assert row["status"] == "QUEUED"


def test_acquisition_batch_run(mock_server: str) -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        data_root = Path(tmp_dir)
        config = NanoConfig(root=data_root, data_root=data_root)
        daemon = AcquisitionDaemon(config)

        # Enqueue 5 items
        for i in range(5):
            daemon.db.enqueue(f"{mock_server}/source.html?idx={i}", priority="P0")

        summary = daemon.run_batch(max_items=3)
        assert summary["status"] == "COMPLETED"
        assert summary["items_processed"] == 3
        assert summary["items_succeeded"] == 3

        # Remaining in queue should be 2
        stats = daemon.db.get_queue_stats()
        assert stats.get("QUEUED") == 2
        assert stats.get("ACQUIRED") == 3
