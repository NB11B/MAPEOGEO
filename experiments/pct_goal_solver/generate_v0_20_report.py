from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .v0_20_campaign import execute_v0_20_campaign


REPORT_FILENAME = "pct_v0_20_cross_class_solver_report.json"


def canonical_report_bytes(report: Mapping[str, Any]) -> bytes:
    """Serialize campaign evidence without coercing unsupported objects."""

    return (
        json.dumps(
            report,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )


def write_v0_20_report(report: Mapping[str, Any], out_dir: str | Path) -> tuple[Path, Path]:
    directory = Path(out_dir)
    directory.mkdir(parents=True, exist_ok=True)
    report_path = directory / REPORT_FILENAME
    digest_path = directory / f"{REPORT_FILENAME}.sha256"
    payload = canonical_report_bytes(report)
    digest = hashlib.sha256(payload).hexdigest()

    temporary_report = directory / f".{REPORT_FILENAME}.tmp"
    temporary_digest = directory / f".{REPORT_FILENAME}.sha256.tmp"
    temporary_report.write_bytes(payload)
    temporary_digest.write_text(f"{digest}  {REPORT_FILENAME}\n", encoding="ascii")
    temporary_report.replace(report_path)
    temporary_digest.replace(digest_path)
    return report_path, digest_path


def generate_v0_20_report(out_dir: str | Path) -> dict[str, Any]:
    result = execute_v0_20_campaign()
    report_path, digest_path = write_v0_20_report(result, out_dir)
    print(
        "PCT_GOAL_SOLVER_V0_20: "
        f"{result['scientific_status']} "
        f"gates={result['gates_passed']}/{result['gates_total']} "
        f"wrong_positives={result['total_wrong_positives']}"
    )
    print(f"Report saved to {report_path}")
    print(f"Digest saved to {digest_path}")
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate deterministic v0.20 campaign evidence")
    parser.add_argument("--out-dir", required=True, help="explicit report output directory")
    parser.add_argument(
        "--require-supported",
        action="store_true",
        help="exit nonzero unless every frozen scientific gate passes",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    result = generate_v0_20_report(args.out_dir)
    return 0 if not args.require_supported or result["scientific_status"] == "SUPPORTED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
