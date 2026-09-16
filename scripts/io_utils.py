"""Deterministic, atomic writers shared by active reconstruction stages."""

from __future__ import annotations

import gzip
import json
import os
from pathlib import Path
import tempfile
from typing import Any


def _indented_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        indent=2,
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def atomic_write_deterministic_json_gzip(path: Path, value: Any) -> None:
    """Write indented JSON in a reproducible gzip envelope.

    Serialization completes before any destination-side effect.  The gzip
    header has no filename and a zero modification time, and replacement is
    atomic within the destination directory.
    """

    payload = _indented_json_bytes(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as raw:
            temporary = Path(raw.name)
            with gzip.GzipFile(
                filename="",
                mode="wb",
                fileobj=raw,
                mtime=0,
            ) as compressed:
                compressed.write(payload)
            raw.flush()
            os.fsync(raw.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
