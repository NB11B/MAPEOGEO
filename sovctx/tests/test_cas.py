from __future__ import annotations

import io
import tempfile
from pathlib import Path

import pytest

from sovctx.node.cas import BlobCorruptError, BlobStore, PayloadTooLargeError


def test_cas_store_and_deduplicate() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        cas_root = Path(tmp_dir) / "raw"
        store = BlobStore(cas_root=cas_root)

        data = b"Soviet Mathematics: Gelfand-Levitan 1951"
        sha, path, byte_size, is_new = store.store_bytes(data)

        assert is_new is True
        assert byte_size == len(data)
        assert path.exists()
        assert path.read_bytes() == data
        assert store.has_blob(sha)
        assert store.verify_blob(sha)

        # Storing identical bytes again should deduplicate
        sha2, path2, byte_size2, is_new2 = store.store_bytes(data)
        assert sha2 == sha
        assert path2 == path
        assert is_new2 is False


def test_cas_streaming_store() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        cas_root = Path(tmp_dir) / "raw"
        store = BlobStore(cas_root=cas_root)

        content = b"Streamed PDF payload bytes" * 1000
        stream = io.BytesIO(content)

        sha, path, byte_size, is_new = store.store_stream(stream)
        assert is_new is True
        assert byte_size == len(content)
        assert store.verify_blob(sha)


def test_cas_payload_too_large_rejection() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        cas_root = Path(tmp_dir) / "raw"
        # Set limit to 1 KB for test
        store = BlobStore(cas_root=cas_root, max_payload_bytes=1024)

        oversized_data = b"X" * 2048
        with pytest.raises(PayloadTooLargeError):
            store.store_bytes(oversized_data)

        oversized_stream = io.BytesIO(oversized_data)
        with pytest.raises(PayloadTooLargeError):
            store.store_stream(oversized_stream)

        # Ensure no residual temp files
        tmp_files = list((cas_root / ".tmp").glob("*"))
        assert len(tmp_files) == 0


def test_cas_checksum_mismatch() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        cas_root = Path(tmp_dir) / "raw"
        store = BlobStore(cas_root=cas_root)

        data = b"Integrity check payload"
        bad_sha = "0000000000000000000000000000000000000000000000000000000000000000"

        with pytest.raises(BlobCorruptError):
            store.store_bytes(data, expected_sha=bad_sha)

        with pytest.raises(BlobCorruptError):
            store.store_stream(io.BytesIO(data), expected_sha=bad_sha)


def test_cas_quarantine() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        cas_root = Path(tmp_dir) / "raw"
        q_dir = Path(tmp_dir) / "quarantine"
        store = BlobStore(cas_root=cas_root, quarantine_dir=q_dir)

        payload = b"Suspicious/oversized payload"
        q_path = store.quarantine_payload(
            payload,
            reason="OVERSIZED_PAYLOAD_EXCEEDS_100MB",
            metadata={"simulated_url": "https://example.org/oversized.bin"},
        )

        assert q_path.exists()
        assert q_path.read_bytes() == payload

        meta_files = list(q_dir.glob("*.meta.json"))
        assert len(meta_files) == 1
