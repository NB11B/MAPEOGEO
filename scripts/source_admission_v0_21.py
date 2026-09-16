#!/usr/bin/env python3
"""Pinned, fail-closed source admission for MAPEOGEO v0.21."""

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.source_registry_v0_21 import SourceSpec, load_source_registry
from scripts.structured_source_parsers_v0_21 import (
    FORBIDDEN_PERSISTED_KEYS,
    extract_latex_declarations,
    extract_pretext_declarations,
)

_REQUIRED_METADATA = {
    "node_id",
    "node_type",
    "source_id",
    "repository",
    "revision",
    "structured_id",
    "decl_type",
    "source_path",
    "line_start",
    "line_end",
    "statement_sha256",
    "char_count",
    "extraction_method",
    "parser_version",
    "canonical_status",
    "formal_status",
    "executable_status",
}


@dataclass(frozen=True)
class AdmissionResult:
    sources: tuple[SourceSpec, ...]
    metadata: tuple[dict, ...]

    def counts_by_source(self) -> dict[str, int]:
        counts = {spec.source_id: 0 for spec in self.sources}
        for row in self.metadata:
            counts[row["source_id"]] = counts.get(row["source_id"], 0) + 1
        return dict(sorted(counts.items()))

    def report(self) -> dict:
        return {
            "schema_version": "v0.21",
            "source_count": len(self.sources),
            "admitted_declaration_count": len(self.metadata),
            "counts_by_source": self.counts_by_source(),
            "sources": [
                {
                    "source_id": spec.source_id,
                    "repository": spec.repository,
                    "revision": spec.revision,
                    "parser": spec.parser,
                    "license": spec.license,
                    "scope": spec.scope,
                }
                for spec in self.sources
            ],
            "declarations": list(self.metadata),
        }


def _run_git(cwd: Path, *args: str) -> str:
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    proc = subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
        env=env,
    )
    if proc.returncode != 0:
        command = " ".join(("git", "-C", str(cwd), *args))
        detail = proc.stderr.strip() or proc.stdout.strip() or f"exit {proc.returncode}"
        raise RuntimeError(f"git command failed: {command}: {detail}")
    return proc.stdout.strip()


def checkout_pinned_source(spec: SourceSpec, workspace: Path) -> Path:
    workspace.mkdir(parents=True, exist_ok=True)
    target = workspace / spec.source_id.lower()
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)

    _run_git(target, "init")
    _run_git(target, "remote", "add", "origin", f"https://github.com/{spec.repository}.git")
    _run_git(target, "fetch", "--depth=1", "origin", spec.revision)
    _run_git(target, "checkout", "--detach", "FETCH_HEAD")
    actual = _run_git(target, "rev-parse", "HEAD").strip().lower()
    if actual != spec.revision.lower():
        raise ValueError(
            f"{spec.source_id}: revision mismatch: expected {spec.revision}, got {actual}"
        )
    return target


def _extract_for_spec(source_root: Path, spec: SourceSpec):
    if spec.parser == "pretext":
        return extract_pretext_declarations(source_root, spec)
    if spec.parser == "latex":
        return extract_latex_declarations(source_root, spec)
    raise ValueError(f"{spec.source_id}: unsupported parser {spec.parser!r}")


def sort_admitted_metadata(rows: list[dict]) -> list[dict]:
    return sorted(
        rows,
        key=lambda row: (
            row.get("source_id", ""),
            row.get("source_path", ""),
            int(row.get("line_start", 0)),
            row.get("structured_id", ""),
            row.get("node_id", ""),
        ),
    )


def validate_admitted_metadata(rows: list[dict]) -> None:
    node_ids: set[str] = set()
    source_identities: set[tuple[str, str]] = set()
    for row in rows:
        forbidden = FORBIDDEN_PERSISTED_KEYS.intersection(row)
        if forbidden:
            raise ValueError(
                f"forbidden persisted source prose keys: {sorted(forbidden)}"
            )
        missing = _REQUIRED_METADATA - set(row)
        if missing:
            raise ValueError(f"admitted declaration missing keys: {sorted(missing)}")
        node_id = row["node_id"]
        if node_id in node_ids:
            raise ValueError(f"duplicate node_id in admitted declarations: {node_id}")
        node_ids.add(node_id)
        identity = (row["source_id"], row["structured_id"])
        if identity in source_identities:
            raise ValueError(
                "duplicate source declaration identity: "
                f"{row['source_id']} / {row['structured_id']}"
            )
        source_identities.add(identity)
        if row["node_type"] != "SOURCE_DECLARATION":
            raise ValueError(f"{node_id}: admitted record must be SOURCE_DECLARATION")
        if row["canonical_status"] != "UNRESOLVED":
            raise ValueError(f"{node_id}: source admission cannot auto-promote canonical status")
        if row["formal_status"] != "UNFORMALIZED":
            raise ValueError(f"{node_id}: source admission cannot auto-promote formal status")
        if row["executable_status"] != "UNTESTED":
            raise ValueError(f"{node_id}: source admission cannot auto-promote executable status")
        digest = row["statement_sha256"]
        if not isinstance(digest, str) or len(digest) != 64:
            raise ValueError(f"{node_id}: invalid statement SHA-256")


def admit_sources(registry_path: Path, workspace: Path) -> AdmissionResult:
    specs = load_source_registry(registry_path)
    all_rows: list[dict] = []
    for spec in specs:
        source_root = checkout_pinned_source(spec, workspace)
        declarations = _extract_for_spec(source_root, spec)
        all_rows.extend(decl.to_metadata() for decl in declarations)
    ordered = sort_admitted_metadata(all_rows)
    validate_admitted_metadata(ordered)
    return AdmissionResult(tuple(specs), tuple(ordered))


def main() -> int:
    parser = argparse.ArgumentParser(description="Admit exact pinned v0.21 mathematics sources")
    parser.add_argument(
        "--registry",
        type=Path,
        default=ROOT / "formal" / "source_registry_v0_21.json",
    )
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    result = admit_sources(args.registry, args.workspace)
    report = result.report()
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(report, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )
    print(json.dumps({"counts_by_source": result.counts_by_source(), "total": len(result.metadata)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
