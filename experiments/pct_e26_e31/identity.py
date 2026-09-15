from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_head(path: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        text=True,
    ).strip()


def verify_frozen_checkout(path: Path, expected_sha: str) -> None:
    actual = git_head(path)
    if actual != expected_sha:
        raise ValueError(
            f"Frozen checkout mismatch for {path}: expected {expected_sha}, got {actual}"
        )


def compute_harness_sha(repo_root: Path) -> str:
    package = repo_root / "experiments" / "pct_e26_e31"
    production_files = sorted(
        path
        for path in package.glob("*.py")
        if not path.name.startswith("test_")
    )
    if not production_files:
        raise ValueError(f"No E26-E31 production files found under {package}")

    digest = hashlib.sha256()
    for path in production_files:
        relative = path.relative_to(repo_root).as_posix().encode("utf-8")
        payload = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()
