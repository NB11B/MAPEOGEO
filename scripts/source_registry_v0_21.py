#!/usr/bin/env python3
"""Pinned-source registry validation for MAPEOGEO v0.21."""

import json
import re
from dataclasses import dataclass
from pathlib import Path

_ALLOWED_PARSERS = {"latex", "pretext"}
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


@dataclass(frozen=True)
class SourceSpec:
    source_id: str
    repository: str
    revision: str
    parser: str
    license: str
    status: str
    scope: str
    include_globs: tuple[str, ...]
    exclude_globs: tuple[str, ...]


def _source_spec(row: dict) -> SourceSpec:
    required = {
        "source_id",
        "repository",
        "revision",
        "parser",
        "license",
        "status",
        "scope",
        "include_globs",
        "exclude_globs",
    }
    missing = required - set(row)
    if missing:
        raise ValueError(f"source registry row missing required keys: {sorted(missing)}")

    source_id = row["source_id"]
    repository = row["repository"]
    revision = row["revision"]
    parser = row["parser"]
    license_name = row["license"]
    status = row["status"]
    scope = row["scope"]
    include_globs = row["include_globs"]
    exclude_globs = row["exclude_globs"]

    if not isinstance(source_id, str) or not source_id:
        raise ValueError("source_id must be a non-empty string")
    if not isinstance(repository, str) or not _REPO_RE.fullmatch(repository):
        raise ValueError(f"invalid GitHub repository identifier for {source_id}")
    if not isinstance(revision, str) or not _SHA_RE.fullmatch(revision):
        raise ValueError(f"{source_id}: revision must be an exact 40-character commit SHA")
    if parser not in _ALLOWED_PARSERS:
        raise ValueError(f"{source_id}: unsupported parser {parser!r}")
    if not isinstance(license_name, str) or not license_name.strip():
        raise ValueError(f"{source_id}: license must be explicit")
    if status != "ACTIVE":
        raise ValueError(f"{source_id}: only ACTIVE sources are admissible in v0.21")
    if not isinstance(scope, str) or not scope.strip():
        raise ValueError(f"{source_id}: scope must be explicit")
    if not isinstance(include_globs, list) or not include_globs or not all(
        isinstance(item, str) and item for item in include_globs
    ):
        raise ValueError(f"{source_id}: include_globs must be a non-empty string list")
    if not isinstance(exclude_globs, list) or not all(
        isinstance(item, str) and item for item in exclude_globs
    ):
        raise ValueError(f"{source_id}: exclude_globs must be a string list")

    return SourceSpec(
        source_id=source_id,
        repository=repository,
        revision=revision,
        parser=parser,
        license=license_name,
        status=status,
        scope=scope,
        include_globs=tuple(include_globs),
        exclude_globs=tuple(exclude_globs),
    )


def validate_source_registry(specs: list[SourceSpec]) -> None:
    if not specs:
        raise ValueError("source registry must contain at least one source")
    source_ids = [spec.source_id for spec in specs]
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("duplicate source_id in source registry")
    repo_revisions = [(spec.repository, spec.revision) for spec in specs]
    if len(repo_revisions) != len(set(repo_revisions)):
        raise ValueError("duplicate repository/revision identity in source registry")


def load_source_registry(path: Path) -> list[SourceSpec]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != "v0.21":
        raise ValueError("source registry schema_version must be v0.21")
    rows = data.get("sources")
    if not isinstance(rows, list):
        raise ValueError("source registry sources must be a list")
    specs = [_source_spec(row) for row in rows]
    validate_source_registry(specs)
    return specs


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    specs = load_source_registry(root / "formal" / "source_registry_v0_21.json")
    print(f"Validated {len(specs)} pinned v0.21 sources")
