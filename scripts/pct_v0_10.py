#!/usr/bin/env python3
"""CLI runner for MAPEOGEO PCT v0.10 experiment execution and artifact sealing."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mapeogeo.pct.artifacts import write_run_artifacts
from mapeogeo.pct.experiment import run_pct_experiment


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MAPEOGEO PCT v0.10 reference experiment.")
    parser.add_argument(
        "--manifest",
        type=str,
        default="evidence/v0_10_pct_preregistration.json",
        help="Path to preregistration JSON manifest",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="artifacts/pct_v0_10",
        help="Output directory for sealed artifacts",
    )
    parser.add_argument(
        "--repository-commit",
        type=str,
        default="UNKNOWN",
        help="Repository commit SHA for provenance recording",
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.is_file():
        print(f"ERROR: Manifest not found at {manifest_path}", file=sys.stderr)
        return 1

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    print(f"Executing MAPEOGEO PCT v0.10 stage from manifest: {manifest_path}")
    result = run_pct_experiment(manifest, repository_commit=args.repository_commit)

    print(f"Engine Validity: {result['engine_validity']}")
    print(f"Scientific Result: {result['scientific_result']}")

    out_dir = Path(args.out_dir)
    hashes = write_run_artifacts(result, out_dir, manifest)
    print(f"Sealed {len(hashes)} artifacts to {out_dir}")

    if result["engine_validity"] != "PASS":
        print("ERROR: Engine validity checks failed.", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
