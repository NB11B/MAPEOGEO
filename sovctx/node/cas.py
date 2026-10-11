from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO


class PayloadTooLargeError(Exception):
    """Raised when an acquisition payload exceeds the maximum allowed byte limit."""


class BlobCorruptError(Exception):
    """Raised when a blob checksum does not match its expected digest."""


class BlobStore:
    """Content-Addressed Storage (CAS) for immutable raw source artifacts.

    Blobs are stored at:
        {cas_root}/{sha256[:2]}/{sha256}
    """

    def __init__(
        self,
        cas_root: Path | str,
        max_payload_bytes: int = 100 * 1024 * 1024,
        quarantine_dir: Path | str | None = None,
    ) -> None:
        self.cas_root = Path(cas_root)
        self.max_payload_bytes = max_payload_bytes
        self.quarantine_dir = Path(quarantine_dir) if quarantine_dir else self.cas_root.parent / "quarantine"
        self.tmp_dir = self.cas_root / ".tmp"
        self.cas_root.mkdir(parents=True, exist_ok=True)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)

    def blob_rel_path(self, sha256: str) -> Path:
        sha_clean = sha256.strip().lower()
        return Path(sha_clean[:2]) / sha_clean

    def blob_abs_path(self, sha256: str) -> Path:
        return self.cas_root / self.blob_rel_path(sha256)

    def has_blob(self, sha256: str) -> bool:
        path = self.blob_abs_path(sha256)
        return path.exists() and path.is_file()

    def store_bytes(
        self,
        data: bytes,
        expected_sha: str | None = None,
    ) -> tuple[str, Path, int, bool]:
        if len(data) > self.max_payload_bytes:
            raise PayloadTooLargeError(
                f"Payload size {len(data)} exceeds maximum {self.max_payload_bytes} bytes"
            )

        sha = hashlib.sha256(data).hexdigest()
        if expected_sha and sha.lower() != expected_sha.lower():
            raise BlobCorruptError(
                f"Checksum mismatch: expected {expected_sha}, calculated {sha}"
            )

        dest = self.blob_abs_path(sha)
        if dest.exists() and dest.is_file():
            return (sha, dest, len(data), False)

        with tempfile.NamedTemporaryFile(dir=self.tmp_dir, delete=False) as tmp:
            tmp.write(data)
            tmp_path = Path(tmp.name)
        # File is closed now after exiting with-block

        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(tmp_path), str(dest))
        return (sha, dest, len(data), True)

    def store_stream(
        self,
        stream: BinaryIO,
        expected_sha: str | None = None,
        chunk_size: int = 65536,
    ) -> tuple[str, Path, int, bool]:
        hasher = hashlib.sha256()
        bytes_written = 0

        tmp = tempfile.NamedTemporaryFile(dir=self.tmp_dir, delete=False)
        tmp_path = Path(tmp.name)
        try:
            while True:
                chunk = stream.read(chunk_size)
                if not chunk:
                    break
                bytes_written += len(chunk)
                if bytes_written > self.max_payload_bytes:
                    raise PayloadTooLargeError(
                        f"Streaming payload exceeded limit of {self.max_payload_bytes} bytes"
                    )
                hasher.update(chunk)
                tmp.write(chunk)
            tmp.flush()
        except Exception:
            tmp.close()
            if tmp_path.exists():
                tmp_path.unlink()
            raise
        finally:
            if not tmp.closed:
                tmp.close()

        sha = hasher.hexdigest()
        if expected_sha and sha.lower() != expected_sha.lower():
            if tmp_path.exists():
                tmp_path.unlink()
            raise BlobCorruptError(
                f"Checksum mismatch: expected {expected_sha}, calculated {sha}"
            )

        dest = self.blob_abs_path(sha)
        if dest.exists() and dest.is_file():
            if tmp_path.exists():
                tmp_path.unlink()
            return (sha, dest, bytes_written, False)

        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(tmp_path), str(dest))
        return (sha, dest, bytes_written, True)

    def read_blob(self, sha256: str) -> bytes:
        dest = self.blob_abs_path(sha256)
        if not dest.exists():
            raise FileNotFoundError(f"Blob {sha256} not found in CAS store")
        return dest.read_bytes()

    def verify_blob(self, sha256: str) -> bool:
        dest = self.blob_abs_path(sha256)
        if not dest.exists():
            return False
        calculated = hashlib.sha256(dest.read_bytes()).hexdigest()
        return calculated.lower() == sha256.lower()

    def quarantine_payload(
        self,
        data: bytes | Path,
        reason: str,
        metadata: dict | None = None,
    ) -> Path:
        now_str = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        prefix = f"quarantine_{now_str}"

        if isinstance(data, Path):
            q_file = self.quarantine_dir / f"{prefix}_{data.name}"
            shutil.copy2(str(data), str(q_file))
        else:
            q_file = self.quarantine_dir / f"{prefix}.bin"
            q_file.write_bytes(data)

        meta_file = self.quarantine_dir / f"{prefix}.meta.json"
        meta_payload = {
            "quarantined_at": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
            "target_file": str(q_file.name),
            "metadata": metadata or {},
        }
        meta_file.write_text(json.dumps(meta_payload, indent=2), encoding="utf-8")
        return q_file
