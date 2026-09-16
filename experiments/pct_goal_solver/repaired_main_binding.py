"""Fail-closed binding to the separately repaired main branch.

The feature branch does not merge repaired main.  Instead, this module binds
the campaign to one published commit, its Git tree, and a frozen set of
mathematical-integrity files.  CI checks the binding against a second checkout
and reruns the repaired-main integrity generator there.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from typing import Any, Mapping


BINDING_SCHEMA = "PCT_V0_20_REPAIRED_MAIN_BINDING_V1"
EXPECTED_REPOSITORY = "NB11B/MAPEOGEO"
EXPECTED_BRANCH = "agent/main-math-rigor-v0-20"
EXPECTED_COMMIT_SHA = "c52d61f5ab85bad85f3d49b51a811e609a52e1c0"
EXPECTED_TREE_SHA = "429c723a5fe1ad327819719ece6ac44ea6d47e21"
DEFAULT_MANIFEST_PATH = (
    Path(__file__).resolve().parents[2]
    / "evidence"
    / "pct_v0_20_repaired_main_binding.json"
)
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


EXPECTED_FILES: dict[str, str] = {
    "MAPEOGEOFormal.lean": "f8b644abf6a9da022be42db30f19c5b0e9f4a8fde45dd36d5fa5b8d9644859fa",
    "evidence/v0_20_mathematical_integrity_report.json": "f894d2cbe0581d76302b755e421d9832f4a5b97a8fee555f864291e7632ab020",
    "formal/foundation_mathematical_amendments_v0_20.json": "ffa3cbbc4b6a2b1f580df71d61ad24522d5aafcc1e5062de6cb559e28b16adae",
    "formal/mathematical_integrity_amendments_v0_20.json": "17f1d7f839d96c98aa0a31f8f8972afa695533aea1b512c4723e901021b479d8",
    "lake-manifest.json": "b4382094843ee7d4262530eedc7bba4aa6057a03a75911ba5580ad085efc1073",
    "lakefile.lean": "10d866aa705d815b2d546ebf169f780cd1c433ad5ae17070f0499701363fc2d0",
    "lean-toolchain": "3aac669c7a910ec2389f4e4f921b605adf6ebf2d1e0c9b9cd0be4d33f3f5db71",
    "requirements-math-rigor-v0-20.lock": "d04d5fc31fd029919377fd445048e3911bebb984e4fddec3e63eaaad268023f9",
    "scripts/compute_foundation_depth.py": "edb0a644aebbfcc671dd0f4090d3fb31055638c002baf40196913fb7032a3384",
    "scripts/foundation_contracts.py": "51ab90eb134525d8ee9c7d467d418742140fc659c832d5195e871444f87b451d",
    "scripts/foundation_intake.py": "a5f6168d7b851a06c7cec303d2c176a0835ab8566f4473c6429c047b3d83a700",
    "scripts/generate_mathematical_integrity_report.py": "3b97eac63c76a2b5265354b8087b567584dc118b3eda88664e670ddcf96c18e2",
    "scripts/import_foundation_backfill.py": "0900a8c1e298015568804fb46e422090b9db319b07516cd2ff435362e72e94b6",
}


class RepairedMainVerificationError(RuntimeError):
    """A repaired-main manifest or checkout did not match the frozen identity."""


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _expected_file_rows() -> list[dict[str, str]]:
    return [
        {"path": path, "sha256": digest}
        for path, digest in sorted(EXPECTED_FILES.items())
    ]


def file_manifest_sha256(files: list[dict[str, str]]) -> str:
    return hashlib.sha256(_canonical_json_bytes(files)).hexdigest()


EXPECTED_FILE_MANIFEST_SHA256 = (
    "59663ccf442143af97ad7c2d865d5da3bffb3adf6d05d7b9b3d8a795b1abfed0"
)
if file_manifest_sha256(_expected_file_rows()) != EXPECTED_FILE_MANIFEST_SHA256:
    raise AssertionError("repaired-main file trust anchor drifted")


def _unbound(reason: str) -> dict[str, Any]:
    return {
        "status": "UNBOUND",
        "repository": EXPECTED_REPOSITORY,
        "branch": EXPECTED_BRANCH,
        "commit_sha": EXPECTED_COMMIT_SHA,
        "tree_sha": EXPECTED_TREE_SHA,
        "file_manifest_sha256": EXPECTED_FILE_MANIFEST_SHA256,
        "files": _expected_file_rows(),
        "reason": reason,
    }


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _reject_nonfinite(token: str) -> None:
    raise ValueError(f"non-finite JSON value: {token}")


def _load_json_object(path: Path) -> dict[str, Any]:
    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_reject_duplicate_keys,
        parse_constant=_reject_nonfinite,
    )
    if type(value) is not dict:
        raise ValueError("JSON root must be an object")
    return value


def _valid_relative_path(value: str) -> bool:
    pure = PurePosixPath(value)
    return bool(
        value
        and not pure.is_absolute()
        and "\\" not in value
        and all(part not in {"", ".", ".."} for part in pure.parts)
        and pure.as_posix() == value
    )


def validate_repaired_main_binding_manifest(
    manifest: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate an in-memory manifest against the immutable trust anchor."""

    required_keys = {
        "schema",
        "repository",
        "branch",
        "commit_sha",
        "tree_sha",
        "files",
        "file_manifest_sha256",
    }
    if type(manifest) is not dict or set(manifest) != required_keys:
        return _unbound("REPAIRED_MAIN_BINDING_SCHEMA_MISMATCH")
    if manifest.get("schema") != BINDING_SCHEMA:
        return _unbound("REPAIRED_MAIN_BINDING_SCHEMA_MISMATCH")
    if manifest.get("repository") != EXPECTED_REPOSITORY:
        return _unbound("REPAIRED_MAIN_REPOSITORY_MISMATCH")
    if manifest.get("branch") != EXPECTED_BRANCH:
        return _unbound("REPAIRED_MAIN_BRANCH_MISMATCH")
    commit_sha = manifest.get("commit_sha")
    if (
        type(commit_sha) is not str
        or not SHA1_RE.fullmatch(commit_sha)
        or commit_sha != EXPECTED_COMMIT_SHA
    ):
        return _unbound("REPAIRED_MAIN_COMMIT_MISMATCH")
    tree_sha = manifest.get("tree_sha")
    if (
        type(tree_sha) is not str
        or not SHA1_RE.fullmatch(tree_sha)
        or tree_sha != EXPECTED_TREE_SHA
    ):
        return _unbound("REPAIRED_MAIN_TREE_MISMATCH")

    raw_files = manifest.get("files")
    if type(raw_files) is not list:
        return _unbound("REPAIRED_MAIN_FILE_MANIFEST_MALFORMED")
    files: dict[str, str] = {}
    normalized_rows: list[dict[str, str]] = []
    for raw_row in raw_files:
        if type(raw_row) is not dict or set(raw_row) != {"path", "sha256"}:
            return _unbound("REPAIRED_MAIN_FILE_MANIFEST_MALFORMED")
        path = raw_row.get("path")
        digest = raw_row.get("sha256")
        if (
            type(path) is not str
            or not _valid_relative_path(path)
            or path in files
            or type(digest) is not str
            or not SHA256_RE.fullmatch(digest)
        ):
            return _unbound("REPAIRED_MAIN_FILE_MANIFEST_MALFORMED")
        files[path] = digest
        normalized_rows.append({"path": path, "sha256": digest})
    if normalized_rows != sorted(normalized_rows, key=lambda row: row["path"]):
        return _unbound("REPAIRED_MAIN_FILE_MANIFEST_MALFORMED")

    observed_manifest_digest = manifest.get("file_manifest_sha256")
    computed_manifest_digest = file_manifest_sha256(normalized_rows)
    if (
        type(observed_manifest_digest) is not str
        or not SHA256_RE.fullmatch(observed_manifest_digest)
        or observed_manifest_digest != computed_manifest_digest
    ):
        return _unbound("REPAIRED_MAIN_FILE_MANIFEST_DIGEST_MISMATCH")
    if files != EXPECTED_FILES:
        return _unbound("REPAIRED_MAIN_FILE_HASH_MISMATCH")
    if observed_manifest_digest != EXPECTED_FILE_MANIFEST_SHA256:
        return _unbound("REPAIRED_MAIN_FILE_MANIFEST_DIGEST_MISMATCH")

    return {
        "status": "BOUND",
        "repository": EXPECTED_REPOSITORY,
        "branch": EXPECTED_BRANCH,
        "commit_sha": EXPECTED_COMMIT_SHA,
        "tree_sha": EXPECTED_TREE_SHA,
        "file_manifest_sha256": EXPECTED_FILE_MANIFEST_SHA256,
        "files": normalized_rows,
        "reason": "",
    }


def build_repaired_main_binding(
    manifest_path: str | Path | None = None,
) -> dict[str, Any]:
    """Load and validate the committed repaired-main binding manifest."""

    path = DEFAULT_MANIFEST_PATH if manifest_path is None else Path(manifest_path)
    if not path.is_file():
        return _unbound("REPAIRED_MAIN_BINDING_MANIFEST_MISSING")
    if path.is_symlink():
        return _unbound("REPAIRED_MAIN_BINDING_MANIFEST_UNSAFE")
    try:
        manifest = _load_json_object(path)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
        return _unbound("REPAIRED_MAIN_BINDING_MANIFEST_MALFORMED")
    return validate_repaired_main_binding_manifest(manifest)


def _raw_sha256(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise RepairedMainVerificationError(
            f"REPAIRED_MAIN_CHECKOUT_FILE_UNSAFE: {path}"
        )
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git_revision(checkout: Path, revision: str) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "--verify", revision],
        cwd=checkout,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RepairedMainVerificationError(
            "REPAIRED_MAIN_CHECKOUT_GIT_IDENTITY_UNAVAILABLE"
        )
    return completed.stdout.strip()


def _verify_embedded_producer_tree(checkout: Path) -> int:
    report_path = checkout / "evidence" / "v0_20_mathematical_integrity_report.json"
    try:
        report = _load_json_object(report_path)
        producer_tree = report["provenance"]["producer_source_tree"]
        producer_files = producer_tree["files"]
        producer_digest = producer_tree["sha256"]
    except (KeyError, OSError, UnicodeError, ValueError, TypeError) as exc:
        raise RepairedMainVerificationError(
            "REPAIRED_MAIN_INTEGRITY_REPORT_MALFORMED"
        ) from exc
    if type(producer_files) is not dict or not producer_files:
        raise RepairedMainVerificationError(
            "REPAIRED_MAIN_PRODUCER_FILE_MANIFEST_MALFORMED"
        )
    normalized: dict[str, str] = {}
    for relative, expected_digest in producer_files.items():
        if (
            type(relative) is not str
            or not _valid_relative_path(relative)
            or type(expected_digest) is not str
            or not SHA256_RE.fullmatch(expected_digest)
        ):
            raise RepairedMainVerificationError(
                "REPAIRED_MAIN_PRODUCER_FILE_MANIFEST_MALFORMED"
            )
        if _raw_sha256(checkout / relative) != expected_digest:
            raise RepairedMainVerificationError(
                f"REPAIRED_MAIN_PRODUCER_FILE_HASH_MISMATCH: {relative}"
            )
        normalized[relative] = expected_digest
    computed_digest = hashlib.sha256(
        b"mapeogeo-v0.20-producer-source-tree-v1\0"
        + _canonical_json_bytes(normalized)
    ).hexdigest()
    if computed_digest != producer_digest:
        raise RepairedMainVerificationError(
            "REPAIRED_MAIN_PRODUCER_TREE_DIGEST_MISMATCH"
        )
    return len(normalized)


def verify_repaired_main_checkout(
    checkout_root: str | Path,
    manifest_path: str | Path | None = None,
) -> dict[str, Any]:
    """Verify Git identity, frozen files, and the report's producer tree."""

    binding = build_repaired_main_binding(manifest_path)
    if binding["status"] != "BOUND":
        raise RepairedMainVerificationError(str(binding["reason"]))
    checkout = Path(checkout_root)
    if not checkout.is_dir() or checkout.is_symlink():
        raise RepairedMainVerificationError("REPAIRED_MAIN_CHECKOUT_MISSING_OR_UNSAFE")
    if _git_revision(checkout, "HEAD") != EXPECTED_COMMIT_SHA:
        raise RepairedMainVerificationError(
            "REPAIRED_MAIN_CHECKOUT_COMMIT_MISMATCH"
        )
    if _git_revision(checkout, "HEAD^{tree}") != EXPECTED_TREE_SHA:
        raise RepairedMainVerificationError("REPAIRED_MAIN_CHECKOUT_TREE_MISMATCH")

    checkout_resolved = checkout.resolve()
    for relative, expected_digest in EXPECTED_FILES.items():
        candidate = checkout / relative
        try:
            candidate.resolve().relative_to(checkout_resolved)
        except ValueError as exc:
            raise RepairedMainVerificationError(
                f"REPAIRED_MAIN_CHECKOUT_PATH_ESCAPE: {relative}"
            ) from exc
        if _raw_sha256(candidate) != expected_digest:
            raise RepairedMainVerificationError(
                f"REPAIRED_MAIN_CHECKOUT_FILE_HASH_MISMATCH: {relative}"
            )
    producer_file_count = _verify_embedded_producer_tree(checkout)
    return {
        "status": "VERIFIED",
        "commit_sha": EXPECTED_COMMIT_SHA,
        "tree_sha": EXPECTED_TREE_SHA,
        "bound_file_count": len(EXPECTED_FILES),
        "producer_file_count": producer_file_count,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify an exact checkout of the separately repaired main branch"
    )
    parser.add_argument("--checkout", required=True)
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST_PATH))
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        receipt = verify_repaired_main_checkout(args.checkout, args.manifest)
    except RepairedMainVerificationError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
