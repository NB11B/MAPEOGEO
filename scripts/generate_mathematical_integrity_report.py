#!/usr/bin/env python3
"""Regenerate the active v0.20 mathematical-integrity evidence.

The report deliberately binds content rather than a Git commit.  A report that
contains the commit which contains that report is self-referential; raw file,
registry, and producer-tree SHA-256 identities give a replayable boundary
without making such an impossible claim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.foundation_contracts import (  # noqa: E402
    build_foundation_contract_evidence,
    validate_contract_evidence,
)
from scripts.import_foundation_backfill import (  # noqa: E402
    generate_foundation_declarations,
)


REPORT_PATH = ROOT / "evidence" / "v0_20_mathematical_integrity_report.json"
FOUNDATION_AMENDMENTS_PATH = (
    ROOT / "formal" / "foundation_mathematical_amendments_v0_20.json"
)
COMPLEX_AMENDMENTS_PATH = (
    ROOT / "formal" / "mathematical_integrity_amendments_v0_20.json"
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SCIENTIFIC_BODY_SHA256 = (
    "9b79db407dfc3a4588c348a8f1899ee22131bd4e0c4a160def3d3e75f20a92e2"
)
SEALED_INPUT_PATHS = {
    "v0_11_graph_sha256": Path("data/mapeogeo_v0_11_graph.json.gz"),
    "v0_19_alignments_sha256": Path("formal/cross_source_alignments_v0_19.json"),
    "v0_19_scientific_results_sha256": Path(
        "evidence/v0_19_scientific_results.json"
    ),
}


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_nonfinite(token: str) -> None:
    raise ValueError(f"non-finite JSON value: {token}")


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_reject_duplicate_keys,
        parse_constant=_reject_nonfinite,
    )
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def _raw_sha256(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"provenance input must be a regular file: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_sha256(value: Any, *, domain: str) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(domain.encode("ascii") + b"\0" + payload).hexdigest()


def _producer_paths(root: Path) -> tuple[Path, ...]:
    candidates: list[Path] = list((root / "scripts").rglob("*.py"))
    formal_root = root / "MAPEOGEOFormal"
    if formal_root.is_dir():
        candidates.extend(formal_root.rglob("*.lean"))
    candidates.extend(
        path
        for path in (
            root / "MAPEOGEOFormal.lean",
            root / "lakefile.lean",
            root / "lake-manifest.json",
            root / "lean-toolchain",
        )
        if path.exists()
    )
    paths = tuple(sorted(set(candidates), key=lambda item: item.relative_to(root).as_posix()))
    if not paths:
        raise ValueError("producer source tree is empty")
    return paths


def _file_digest_map(root: Path, paths: Iterable[Path]) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in paths:
        resolved = path.resolve()
        try:
            relative = resolved.relative_to(root.resolve()).as_posix()
        except ValueError as exc:
            raise ValueError(f"provenance path escapes repository root: {path}") from exc
        if relative in result:
            raise ValueError(f"duplicate producer path: {relative}")
        result[relative] = _raw_sha256(path)
    return result


def build_provenance(root: Path = ROOT) -> dict[str, Any]:
    foundation_path = root / "formal" / FOUNDATION_AMENDMENTS_PATH.name
    complex_path = root / "formal" / COMPLEX_AMENDMENTS_PATH.name
    dependency_lock_path = root / "requirements-math-rigor-v0-20.lock"
    foundation_manifest = _load_json(foundation_path)
    complex_manifest = _load_json(complex_path)

    if foundation_manifest.get("schema_version") != "1.0.0":
        raise ValueError("unsupported foundation amendment schema")
    if foundation_manifest.get("claim_boundary") != "STATEMENT_CORRECTION_ONLY_NOT_PROOF":
        raise ValueError("invalid foundation amendment claim boundary")
    historical_rows = foundation_manifest.get("historical_rows")
    amendments = foundation_manifest.get("amendments")
    if not isinstance(historical_rows, dict) or not isinstance(amendments, list):
        raise ValueError("foundation amendment registry is malformed")
    if complex_manifest.get("schema_version") != (
        "v0.20-mathematical-integrity-amendments"
    ):
        raise ValueError("unsupported complex amendment schema")
    complex_amendments = complex_manifest.get("amendments")
    if not isinstance(complex_amendments, list):
        raise ValueError("complex amendment registry is malformed")

    declarations = generate_foundation_declarations()
    declaration_rows = [declaration.to_dict() for declaration in declarations]
    if len(declaration_rows) != 176:
        raise ValueError(
            f"foundation declaration registry cardinality drifted: {len(declaration_rows)}"
        )
    contracts = build_foundation_contract_evidence(declarations)
    contract_summary = validate_contract_evidence(contracts, declarations)
    contract_rows = [contract.to_dict() for contract in contracts]

    producer_files = _file_digest_map(root, _producer_paths(root))
    producer_tree_digest = _canonical_sha256(
        producer_files,
        domain="mapeogeo-v0.20-producer-source-tree-v1",
    )
    declaration_digest = _canonical_sha256(
        declaration_rows,
        domain="mapeogeo-v0.20-foundation-declaration-registry-v1",
    )
    contract_digest = _canonical_sha256(
        contract_rows,
        domain="mapeogeo-v0.20-foundation-contract-registry-v1",
    )

    for digest in (producer_tree_digest, declaration_digest, contract_digest):
        if not SHA256_RE.fullmatch(digest):
            raise AssertionError("internal SHA-256 formatting error")

    return {
        "identity_policy": {
            "algorithm": "SHA-256",
            "git_commit_claimed": False,
            "raw_file_hashes_cover_exact_bytes": True,
            "registry_hashes_are_domain_separated_canonical_json": True,
        },
        "foundation_amendment_manifest": {
            "path": foundation_path.relative_to(root).as_posix(),
            "raw_sha256": _raw_sha256(foundation_path),
            "historical_row_count": len(historical_rows),
            "amendment_count": len(amendments),
        },
        "complex_amendment_manifest": {
            "path": complex_path.relative_to(root).as_posix(),
            "raw_sha256": _raw_sha256(complex_path),
            "amendment_count": len(complex_amendments),
        },
        "runtime_dependency_lock": {
            "path": dependency_lock_path.relative_to(root).as_posix(),
            "raw_sha256": _raw_sha256(dependency_lock_path),
        },
        "foundation_declaration_registry": {
            "entry_count": len(declaration_rows),
            "sha256": declaration_digest,
        },
        "foundation_contract_registry": {
            "entry_count": len(contract_rows),
            "verified_subject_count": contract_summary["verified_declarations"],
            "kernel_verified_subject_count": contract_summary[
                "kernel_verified_declarations"
            ],
            "sha256": contract_digest,
        },
        "producer_source_tree": {
            "file_count": len(producer_files),
            "files": producer_files,
            "sha256": producer_tree_digest,
        },
    }


def build_report(base_report: Path, *, root: Path = ROOT) -> dict[str, Any]:
    report = _load_json(base_report)
    if report.get("schema_version") != "v0.20-mathematical-integrity-report":
        raise ValueError("unsupported mathematical-integrity report schema")
    if report.get("overall_status") != "AMENDED_PARTIAL":
        raise ValueError("integrity report must retain its truthful AMENDED_PARTIAL status")

    scientific_body = dict(report)
    scientific_body.pop("provenance", None)
    scientific_body_digest = _canonical_sha256(
        scientific_body,
        domain="mapeogeo-v0.20-mathematical-integrity-scientific-body-v1",
    )
    if scientific_body_digest != SCIENTIFIC_BODY_SHA256:
        raise ValueError(
            "scientific report body differs from the reviewed v0.20 claim boundary"
        )

    sealed_inputs = report.get("sealed_inputs")
    if not isinstance(sealed_inputs, dict):
        raise ValueError("sealed input registry is malformed")
    for field, relative_path in SEALED_INPUT_PATHS.items():
        actual_digest = _raw_sha256(root / relative_path)
        if sealed_inputs.get(field) != actual_digest:
            raise ValueError(f"sealed input digest mismatch: {relative_path}")

    provenance = build_provenance(root)
    if report.get("amendment_manifest_sha256") != provenance[
        "complex_amendment_manifest"
    ]["raw_sha256"]:
        raise ValueError("complex amendment digest mismatch")

    foundation_evidence = report.get("foundation_evidence")
    if not isinstance(foundation_evidence, dict):
        raise ValueError("foundation evidence summary is malformed")
    expected_foundation_counts = {
        "curated_declarations": provenance["foundation_declaration_registry"][
            "entry_count"
        ],
        "executable_verified_declarations": provenance[
            "foundation_contract_registry"
        ]["verified_subject_count"],
        "kernel_verified_declarations": provenance["foundation_contract_registry"][
            "kernel_verified_subject_count"
        ],
    }
    for field, expected in expected_foundation_counts.items():
        if foundation_evidence.get(field) != expected:
            raise ValueError(f"foundation evidence count mismatch: {field}")

    report["provenance"] = provenance
    return report


def _canonical_report_bytes(report: dict[str, Any]) -> bytes:
    return (
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def generate_report(base_report: Path, output: Path, *, root: Path = ROOT) -> dict[str, Any]:
    report = build_report(base_report, root=root)
    _atomic_write(output, _canonical_report_bytes(report))
    return report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Regenerate deterministic v0.20 mathematical-integrity evidence"
    )
    parser.add_argument("--base-report", type=Path, default=REPORT_PATH)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        generate_report(args.base_report.resolve(), args.out.resolve())
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"mathematical-integrity report generation failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
