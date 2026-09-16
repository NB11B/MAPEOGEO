#!/usr/bin/env python3
"""Freeze a successful live v0.21 admission into deterministic zero-prose manifests."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from scripts.io_utils import atomic_write_deterministic_json_gzip
from scripts.source_admission_v0_21 import validate_admitted_metadata

ROOT = Path(__file__).resolve().parents[1]


def _canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _atomic_write_json(path: Path, value: Any) -> None:
    payload = (
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False)
        + "\n"
    ).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _duplicate_stats(rows: list[dict]) -> dict[str, int]:
    counts = Counter(row["statement_sha256"] for row in rows)
    duplicate_groups = sum(1 for count in counts.values() if count > 1)
    duplicate_occurrences = sum(count - 1 for count in counts.values() if count > 1)
    return {
        "admitted_source_occurrences": len(rows),
        "unique_statement_bodies": len(counts),
        "duplicate_statement_hash_groups": duplicate_groups,
        "duplicate_statement_occurrences": duplicate_occurrences,
    }


def freeze_admission_report(
    report_path: Path,
    declarations_path: Path,
    evidence_path: Path,
) -> dict:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("schema_version") != "v0.21":
        raise ValueError("live source admission report schema must be v0.21")
    rows = report.get("declarations")
    sources = report.get("sources")
    if not isinstance(rows, list) or not isinstance(sources, list):
        raise ValueError("live source admission report must contain source/declaration lists")
    validate_admitted_metadata(rows)

    ordered_rows = sorted(
        rows,
        key=lambda row: (
            row["source_id"],
            row["source_path"],
            row["line_start"],
            row["structured_id"],
            row["node_id"],
        ),
    )
    declaration_payload = {
        "schema_version": "v0.21",
        "claim_boundary": "SOURCE_OCCURRENCES_ONLY_NO_SEMANTIC_PROMOTION",
        "declarations": ordered_rows,
    }
    atomic_write_deterministic_json_gzip(declarations_path, declaration_payload)

    by_source: dict[str, list[dict]] = defaultdict(list)
    for row in ordered_rows:
        by_source[row["source_id"]].append(row)

    source_specs = {source["source_id"]: source for source in sources}
    if set(source_specs) != set(by_source):
        raise ValueError("live source report source/declaration partition mismatch")

    per_source: dict[str, dict] = {}
    for source_id in sorted(by_source):
        source_rows = by_source[source_id]
        stats = _duplicate_stats(source_rows)
        per_source[source_id] = {
            "repository": source_specs[source_id]["repository"],
            "revision": source_specs[source_id]["revision"],
            "parser": source_specs[source_id]["parser"],
            "license": source_specs[source_id]["license"],
            "scope": source_specs[source_id]["scope"],
            **stats,
            "declaration_metadata_sha256": _sha(source_rows),
        }

    total_stats = _duplicate_stats(ordered_rows)
    manifest = {
        "schema_version": "v0.21",
        "claim_boundary": "PINNED_SOURCE_DECLARATIONS_NOT_CANONICAL_EQUIVALENCE_OR_PROOF",
        **total_stats,
        "source_count": len(source_specs),
        "source_registry_projection_sha256": _sha(
            [source_specs[source_id] for source_id in sorted(source_specs)]
        ),
        "declaration_metadata_sha256": _sha(ordered_rows),
        "frozen_declaration_payload_sha256": _sha(declaration_payload),
        "frozen_declaration_gzip_sha256": hashlib.sha256(
            declarations_path.read_bytes()
        ).hexdigest(),
        "status_counts": {
            "canonical": dict(sorted(Counter(row["canonical_status"] for row in ordered_rows).items())),
            "formal": dict(sorted(Counter(row["formal_status"] for row in ordered_rows).items())),
            "executable": dict(sorted(Counter(row["executable_status"] for row in ordered_rows).items())),
        },
        "per_source": per_source,
    }
    _atomic_write_json(evidence_path, manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Freeze exact v0.21 live source admission")
    parser.add_argument("report", type=Path)
    parser.add_argument(
        "--declarations-out",
        type=Path,
        default=ROOT / "formal" / "source_declarations_v0_21.json.gz",
    )
    parser.add_argument(
        "--evidence-out",
        type=Path,
        default=ROOT / "evidence" / "v0_21_source_admission_manifest.json",
    )
    args = parser.parse_args()
    manifest = freeze_admission_report(args.report, args.declarations_out, args.evidence_out)
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
