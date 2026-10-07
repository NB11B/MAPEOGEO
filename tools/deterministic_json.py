"""Deterministic JSON serialization utilities for MAPEOGEOv2.

Ensures byte-level determinism across platforms, runtimes, and invocations:
- Keys sorted recursively.
- 2-space indentation.
- Strict rejection of non-compliant floats (NaN, Infinity).
- Explicit UTF-8 encoding with single trailing newline.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def serialize_deterministic(obj: Any) -> str:
    """Serialize a Python data structure into deterministic canonical JSON string."""
    return (
        json.dumps(
            obj,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ": "),
        )
        + "\n"
    )


def write_deterministic_json(path: Path | str, obj: Any) -> None:
    """Write an object to a JSON file deterministically."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    serialized = serialize_deterministic(obj)
    target.write_text(serialized, encoding="utf-8")


def read_json(path: Path | str) -> Any:
    """Read a JSON file."""
    target = Path(path)
    return json.loads(target.read_text(encoding="utf-8"))
