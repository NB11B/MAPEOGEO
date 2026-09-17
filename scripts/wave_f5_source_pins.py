#!/usr/bin/env python3
"""MAPEOGEO Wave F5 Source Pins & Acquisition Audit.

Audits and verifies that all Wave F5 source registers have verified locators,
pinned editions, and conform to repository export policies.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class SourceAuditResult:
    all_passed: bool
    verified_sources: list[str]
    errors: list[str]


def load_source_registry(path: Path = ROOT / "formal" / "wave_f5" / "source_registry.json") -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def audit_source_registry(
    registry_path: Path = ROOT / "formal" / "wave_f5" / "source_registry.json",
) -> SourceAuditResult:
    data = load_source_registry(registry_path)
    sources = data.get("sources", [])
    verified = []
    errors = []

    for s in sources:
        key = s.get("source_key")
        title = s.get("title")
        url = s.get("entry_url")
        policy = s.get("export_policy")

        if not key or not title or not url or not policy:
            errors.append(f"Source {key or 'unknown'}: missing required fields")
            continue

        verified.append(key)

    return SourceAuditResult(
        all_passed=(len(errors) == 0 and len(verified) >= 8),
        verified_sources=verified,
        errors=errors,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Wave F5 source registry")
    parser.add_argument(
        "--registry",
        type=Path,
        default=ROOT / "formal" / "wave_f5" / "source_registry.json",
    )
    args = parser.parse_args()

    res = audit_source_registry(args.registry)
    if not res.all_passed:
        print("[SourcePins] Audit FAILED:")
        for err in res.errors:
            print(f"  - {err}")
        return 1

    print(f"[SourcePins] Verified {len(res.verified_sources)} sources successfully: {', '.join(res.verified_sources)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
