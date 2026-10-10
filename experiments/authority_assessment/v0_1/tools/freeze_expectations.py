"""Freeze qualification inputs, direct oracle, reverse domains, and synthetic fixtures for Gate G0a.

Ensures that qualification expectations and catalogs are strictly immutable once frozen.
Refuses to overwrite existing files unless explicitly authorized.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional


class ExistingFreezeError(FileExistsError):
    """Raised when an attempt is made to overwrite an existing frozen expectation file."""


def compute_sha256(data: bytes) -> str:
    """Computes SHA-256 hex digest of byte string."""
    return hashlib.sha256(data).hexdigest()


def compute_canonical_json_digest(payload: Any) -> str:
    """Computes SHA-256 digest of deterministically serialized JSON data."""
    raw = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
    return compute_sha256(raw)


def freeze_qualification_expectations(
    target_file: Path,
    payload: Dict[str, Any],
    allow_overwrite: bool = False,
) -> str:
    """Writes a frozen expectation artifact, refusing to overwrite existing files by default."""
    if target_file.exists() and not allow_overwrite:
        raise ExistingFreezeError(f"Refusing to overwrite existing freeze file: {target_file}")

    target_file.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, indent=2, sort_keys=True)
    target_file.write_text(serialized, encoding="utf-8")
    return compute_sha256(serialized.encode("utf-8"))


def freeze_all_qualification_inputs(
    base_dir: Path,
    output_manifest: Path,
    allow_overwrite: bool = False,
) -> Dict[str, Any]:
    """Scans and freezes all qualification input files into a freeze manifest."""
    files_to_freeze = [
        base_dir / "contracts" / "authority_contracts_v0_1.json",
        base_dir / "qualification" / "authority_cases_v0_1.json",
        base_dir / "qualification" / "direct_oracle_v0_1.json",
        base_dir / "qualification" / "reverse_domains_v0_1.json",
    ]

    # Include all synthetic fixture json files
    synthetic_dir = base_dir / "fixtures" / "synthetic"
    if synthetic_dir.exists():
        for f in sorted(synthetic_dir.glob("*.json")):
            files_to_freeze.append(f)

    manifest_entries: List[Dict[str, Any]] = []
    for f in files_to_freeze:
        if not f.exists():
            continue
        content = f.read_bytes()
        digest = compute_sha256(content)
        manifest_entries.append({
            "path": str(f.relative_to(base_dir).as_posix()),
            "sha256": digest,
            "size_bytes": len(content),
        })

    freeze_record = {
        "freeze_id": "authority_v0_1_qualification_freeze_g0a",
        "status": "frozen_immutable_expectations",
        "declared_files": manifest_entries,
    }

    freeze_qualification_expectations(output_manifest, freeze_record, allow_overwrite=allow_overwrite)
    return freeze_record


def main() -> int:
    parser = argparse.ArgumentParser(description="Freeze qualification expectations for Gate G0a")
    parser.add_argument("--base-dir", type=Path, default=Path.cwd(), help="Path to authority package root")
    parser.add_argument("--output", type=Path, help="Path for freeze manifest output")
    parser.add_argument("--allow-overwrite", action="store_true", help="Force overwrite of existing freeze")
    args = parser.parse_args()

    base = args.base_dir.resolve()
    out = args.output or (base / "qualification" / "frozen_expectations_manifest.json")

    record = freeze_all_qualification_inputs(base, out, allow_overwrite=args.allow_overwrite)
    print(json.dumps({
        "status": record["status"],
        "files_frozen": len(record["declared_files"]),
        "manifest": str(out.resolve()),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
