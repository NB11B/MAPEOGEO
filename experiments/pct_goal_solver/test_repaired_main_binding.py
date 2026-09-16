from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from experiments.pct_goal_solver import v0_20_campaign as campaign


EXPECTED_REPOSITORY = "NB11B/MAPEOGEO"
EXPECTED_BRANCH = "agent/main-math-rigor-v0-20"
EXPECTED_COMMIT = "c52d61f5ab85bad85f3d49b51a811e609a52e1c0"
EXPECTED_TREE = "429c723a5fe1ad327819719ece6ac44ea6d47e21"
EXPECTED_FILES = {
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


def _file_manifest_digest(files: dict[str, str]) -> str:
    payload = json.dumps(
        [{"path": path, "sha256": digest} for path, digest in sorted(files.items())],
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _valid_manifest() -> dict[str, object]:
    return {
        "schema": "PCT_V0_20_REPAIRED_MAIN_BINDING_V1",
        "repository": EXPECTED_REPOSITORY,
        "branch": EXPECTED_BRANCH,
        "commit_sha": EXPECTED_COMMIT,
        "tree_sha": EXPECTED_TREE,
        "files": [
            {"path": path, "sha256": digest}
            for path, digest in sorted(EXPECTED_FILES.items())
        ],
        "file_manifest_sha256": _file_manifest_digest(EXPECTED_FILES),
    }


def test_committed_repaired_main_binding_is_exact_and_bound() -> None:
    binding = campaign.build_repaired_main_binding()
    assert binding["status"] == "BOUND"
    assert binding["repository"] == EXPECTED_REPOSITORY
    assert binding["branch"] == EXPECTED_BRANCH
    assert binding["commit_sha"] == EXPECTED_COMMIT
    assert binding["tree_sha"] == EXPECTED_TREE
    assert binding["file_manifest_sha256"] == _file_manifest_digest(EXPECTED_FILES)
    assert {row["path"]: row["sha256"] for row in binding["files"]} == EXPECTED_FILES
    assert binding["reason"] == ""


def test_missing_repaired_main_manifest_is_unbound(tmp_path: Path) -> None:
    binding = campaign.build_repaired_main_binding(tmp_path / "missing.json")
    assert binding["status"] == "UNBOUND"
    assert binding["reason"] == "REPAIRED_MAIN_BINDING_MANIFEST_MISSING"


@pytest.mark.parametrize(
    ("field", "replacement", "reason"),
    (
        ("repository", "somewhere/else", "REPAIRED_MAIN_REPOSITORY_MISMATCH"),
        ("branch", "main", "REPAIRED_MAIN_BRANCH_MISMATCH"),
        ("commit_sha", "0" * 40, "REPAIRED_MAIN_COMMIT_MISMATCH"),
        ("tree_sha", "1" * 40, "REPAIRED_MAIN_TREE_MISMATCH"),
    ),
)
def test_repaired_main_identity_tampering_is_unbound(
    field: str,
    replacement: str,
    reason: str,
) -> None:
    validator = getattr(campaign, "validate_repaired_main_binding_manifest", None)
    assert callable(validator)
    manifest = _valid_manifest()
    manifest[field] = replacement
    binding = validator(manifest)
    assert binding["status"] == "UNBOUND"
    assert binding["reason"] == reason


def test_repaired_main_file_tampering_is_unbound_even_with_recomputed_digest() -> None:
    validator = getattr(campaign, "validate_repaired_main_binding_manifest", None)
    assert callable(validator)
    manifest = _valid_manifest()
    files = {
        row["path"]: row["sha256"]
        for row in manifest["files"]
    }
    files["MAPEOGEOFormal.lean"] = "2" * 64
    manifest["files"] = [
        {"path": path, "sha256": digest}
        for path, digest in sorted(files.items())
    ]
    manifest["file_manifest_sha256"] = _file_manifest_digest(files)

    binding = validator(manifest)
    assert binding["status"] == "UNBOUND"
    assert binding["reason"] == "REPAIRED_MAIN_FILE_HASH_MISMATCH"


def test_repaired_main_file_manifest_digest_tampering_is_unbound() -> None:
    validator = getattr(campaign, "validate_repaired_main_binding_manifest", None)
    assert callable(validator)
    manifest = _valid_manifest()
    manifest["file_manifest_sha256"] = "3" * 64
    binding = validator(manifest)
    assert binding["status"] == "UNBOUND"
    assert binding["reason"] == "REPAIRED_MAIN_FILE_MANIFEST_DIGEST_MISMATCH"


def test_checkout_verifier_rejects_a_different_git_commit() -> None:
    verifier = getattr(campaign, "verify_repaired_main_checkout", None)
    assert callable(verifier)
    feature_checkout = Path(__file__).resolve().parents[2]
    with pytest.raises(RuntimeError, match="REPAIRED_MAIN_CHECKOUT_COMMIT_MISMATCH"):
        verifier(feature_checkout)


def test_feature_dependency_lock_is_hash_locked_and_bound() -> None:
    binding = campaign.build_dependency_lock_binding()
    assert binding["status"] == "BOUND"
    assert binding["reason"] == ""
    assert [row["path"] for row in binding["files"]] == [
        "requirements-v0.20-lock.txt"
    ]
    assert len(binding["lock_manifest_sha256"]) == 64
