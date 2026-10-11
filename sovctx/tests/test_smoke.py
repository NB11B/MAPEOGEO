from __future__ import annotations

import http.server
import json
import socketserver
import tempfile
import threading
from pathlib import Path
from typing import Any

import pytest

from sovctx.node.config import NanoConfig
from sovctx.node.smoke import SmokeQualification


class MockSmokeHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        pass

    def do_GET(self) -> None:
        content = b"%PDF-1.4 Simulated Russian Academic Source\n%%EOF"
        self.send_response(200)
        self.send_header("Content-Type", "application/pdf")
        self.send_header("ETag", f'"{hash(self.path)}"')
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


@pytest.fixture(scope="module")
def smoke_server():
    server = socketserver.TCPServer(("127.0.0.1", 0), MockSmokeHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
    server.server_close()


def test_smoke_qualification_harness(smoke_server: str) -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        data_root = Path(tmp_dir) / "data"
        repo_root = Path(__file__).resolve().parents[1]

        config = NanoConfig(root=repo_root, data_root=data_root)
        runner = SmokeQualification(config=config, batch_size=3)

        # Enqueue mock server items
        runner.db.init_db()
        for i in range(3):
            runner.db.enqueue(f"{smoke_server}/paper_{i}.pdf", priority="P0", goal="Test paper")

        receipt = runner.run()

        assert receipt.verdict == "PASS"
        assert receipt.measurements["successful_fetches"] >= 3
        assert receipt.measurements["isolation_violations"] == 0
        assert receipt.measurements["cas_checksum_failures"] == 0
        assert receipt.measurements["sha256_verification"] == "PASS"

        # Manifest and Markdown report verification
        manifest_file = Path(receipt.manifest_path)
        assert manifest_file.exists()
        manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
        assert manifest_data["verdict"] == "PASS"

        report_file = data_root / "evidence" / "runs" / "n05_smoke_report.md"
        assert report_file.exists()
        assert "N0.5_SMOKE" in report_file.read_text(encoding="utf-8")
