"""SHA-256 Manifest and Tree Hashing Utilities.

Computes repeatable cryptographic digests for files and directory trees
to enforce scientific immutability and provenance tracking.
"""

from __future__ import annotations

import hashlib
from pathlib import Path


def compute_file_sha256(path: Path | str) -> str:
    """Compute SHA-256 hex digest for a single file."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"File not found: {p}")
    hasher = hashlib.sha256()
    with p.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_directory_tree_sha256(
    root_dir: Path | str,
    pattern: str = "*.py",
    exclude_dirs: list[str] | None = None,
) -> str:
    """Compute deterministic combined SHA-256 hash of all matching files in a directory tree.

    Files are sorted lexicographically by relative POSIX path.
    Each file's relative path and content hash are chained into the aggregate digest.
    """
    root = Path(root_dir)
    if not root.is_dir():
        raise NotADirectoryError(f"Directory not found: {root}")

    excludes = exclude_dirs or ["__pycache__", ".pytest_cache", ".mypy_cache"]
    matching_files: list[Path] = []

    for path in root.rglob(pattern):
        if any(ex in path.parts for ex in excludes):
            continue
        if path.is_file():
            matching_files.append(path)

    # Sort deterministically by relative POSIX path
    matching_files.sort(key=lambda p: p.relative_to(root).as_posix())

    aggregate_hasher = hashlib.sha256()
    for file_path in matching_files:
        rel_posix = file_path.relative_to(root).as_posix()
        file_hash = compute_file_sha256(file_path)
        aggregate_hasher.update(f"{rel_posix}:{file_hash}\n".encode())

    return aggregate_hasher.hexdigest()
