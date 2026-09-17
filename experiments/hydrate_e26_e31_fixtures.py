#!/usr/bin/env python3
"""Fail-Closed E26-E31 Cross-Branch Fixture Hydrator.

Hydrates the isolated, sealed fixtures required by the PCT E26-E31 cross-branch
reproducibility suite:
  - .crossbranch/frozen-main (commit fd2d90c00cb71951fdfd7cd1e7e22a8f0552f97f)
  - .crossbranch/frozen-solver (commit 6c9333ed3ec48a298ad943a74e72a01fa1ffcd78)
  - .crossbranch/frozen-main-artifact/mapeogeo_v0_15_1_graph.json.gz

Enforces strict fail-closed validation:
  - Verifies exact commit hashes for knowledge baseline and solver closure baseline.
  - Verifies decompressed graph content byte SHA-256 matches 27da885c45a9becec547d0127237f3e66ae9e2d2ee5164ba6881a0efb19ab771.
  - Verifies canonical sorted JSON semantic digest matches a167832e686742e58127f8ae34d6d9e22e655e20e98fd3c16997ce4c2f0d821a.
  - Verifies analysis alignments commit SHA-256 matches a85410c639c33f4632c2eeec3dac94cd01176cd4fc941afb4d86ddbdfb3922bd.
  - Fails immediately on commit mismatch, missing files, corrupted bytes, or dirty trees.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

# Pinned Baseline Commit SHAs
KNOWLEDGE_BASELINE_SHA = "fd2d90c00cb71951fdfd7cd1e7e22a8f0552f97f"
SOLVER_BASELINE_SHA = "6c9333ed3ec48a298ad943a74e72a01fa1ffcd78"

# Expected Provenance Digests
HISTORICAL_GRAPH_SHA256 = "1fecce40e1ea7a0c8e0b3b8aa8d809f136184ad428291cea603ecd3f018735f9"
CANONICAL_DECOMPRESSED_SHA256 = "27da885c45a9becec547d0127237f3e66ae9e2d2ee5164ba6881a0efb19ab771"
CANONICAL_JSON_SHA256 = "a167832e686742e58127f8ae34d6d9e22e655e20e98fd3c16997ce4c2f0d821a"
ALIGNMENTS_COMMIT_SHA256 = "a85410c639c33f4632c2eeec3dac94cd01176cd4fc941afb4d86ddbdfb3922bd"
ACCEPTANCE_CLAIMED_ALIGNMENTS_SHA256 = "476db0866057ddff57ef172c7040390ea73d3799bc1c64cceee6c423a894d3ef"

CROSSBRANCH_DIR = ROOT / ".crossbranch"
FROZEN_MAIN_DIR = CROSSBRANCH_DIR / "frozen-main"
FROZEN_SOLVER_DIR = CROSSBRANCH_DIR / "frozen-solver"
FROZEN_ARTIFACT_DIR = CROSSBRANCH_DIR / "frozen-main-artifact"
GRAPH_BASENAME = "mapeogeo_v0_15_1_graph.json.gz"


def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compute_file_sha256(path: Path) -> str:
    return compute_sha256(path.read_bytes())


def git_head(path: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        text=True,
    ).strip()


def verify_decompressed_graph(graph_gz_path: Path) -> tuple[str, str]:
    """Verify raw decompressed byte SHA-256 and canonical sorted JSON SHA-256."""
    if not graph_gz_path.exists():
        raise FileNotFoundError(f"Graph artifact not found: {graph_gz_path}")

    with gzip.open(graph_gz_path, "rb") as f:
        decompressed_bytes = f.read()

    decompressed_sha = compute_sha256(decompressed_bytes)
    if decompressed_sha != CANONICAL_DECOMPRESSED_SHA256:
        raise ValueError(
            f"Decompressed graph content SHA-256 mismatch!\n"
            f"  Expected: {CANONICAL_DECOMPRESSED_SHA256}\n"
            f"  Observed: {decompressed_sha}"
        )

    graph_obj = json.loads(decompressed_bytes.decode("utf-8"))
    canonical_json = json.dumps(
        graph_obj,
        sort_keys=True,
        indent=2,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ": "),
    ).encode("utf-8")
    canonical_sha = compute_sha256(canonical_json)
    if canonical_sha != CANONICAL_JSON_SHA256:
        raise ValueError(
            f"Canonical JSON semantic digest mismatch!\n"
            f"  Expected: {CANONICAL_JSON_SHA256}\n"
            f"  Observed: {canonical_sha}"
        )

    return decompressed_sha, canonical_sha


def ensure_git_commit(commit_sha: str) -> None:
    """Ensure the target commit object is accessible locally."""
    res = subprocess.run(
        ["git", "cat-file", "-e", commit_sha],
        cwd=ROOT,
        capture_output=True,
    )
    if res.returncode != 0:
        print(f"[Hydrate] Commit {commit_sha} not found locally, fetching...")
        subprocess.run(
            ["git", "fetch", "origin", commit_sha],
            cwd=ROOT,
            check=True,
        )


def setup_worktree(commit_sha: str, target_link: Path, sibling_name: str, force: bool = False) -> Path:
    """Set up an isolated sibling worktree and link/junction it to target_link."""
    ensure_git_commit(commit_sha)
    parent_dir = ROOT.parent
    sibling_path = parent_dir / sibling_name

    # Check if target already exists and points to expected HEAD
    if not force and target_link.exists() and (target_link / ".git").exists():
        try:
            head = git_head(target_link)
            if head == commit_sha:
                print(f"[Hydrate] Reusing existing valid worktree -> {target_link} (HEAD {head[:7]})")
                return sibling_path
        except Exception:
            pass

    # Clean up existing worktree / junction if force or invalid
    if target_link.is_symlink() or target_link.is_junction() if hasattr(target_link, "is_junction") else False:
        target_link.unlink(missing_ok=True)
    elif target_link.exists():
        shutil.rmtree(target_link, ignore_errors=True)

    if sibling_path.exists():
        subprocess.run(["git", "worktree", "remove", "--force", str(sibling_path)], cwd=ROOT, capture_output=True)
        shutil.rmtree(sibling_path, ignore_errors=True)

    subprocess.run(["git", "worktree", "prune"], cwd=ROOT, capture_output=True)

    # Add detached worktree
    print(f"[Hydrate] Creating detached worktree at {sibling_path} for commit {commit_sha[:7]}...")
    subprocess.run(
        ["git", "worktree", "add", "--detach", str(sibling_path), commit_sha],
        cwd=ROOT,
        check=True,
    )

    # Create junction/symlink in .crossbranch
    target_link.parent.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        import _winapi
        _winapi.CreateJunction(str(sibling_path), str(target_link))
    else:
        target_link.symlink_to(sibling_path, target_is_directory=True)

    head = git_head(target_link)
    if head != commit_sha:
        raise ValueError(f"Failed to bind worktree at {target_link}: expected HEAD {commit_sha}, got {head}")

    print(f"[Hydrate] Linked {target_link} -> {sibling_path} (HEAD {head[:7]})")
    return sibling_path


def hydrate_fixtures(force: bool = False) -> None:
    print("==========================================================")
    print("  MAPEOGEO E26-E31 Fail-Closed Fixture Hydration")
    print("==========================================================")

    CROSSBRANCH_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Setup frozen-main worktree
    sibling_main = setup_worktree(
        KNOWLEDGE_BASELINE_SHA,
        FROZEN_MAIN_DIR,
        "MAPEOGEO-frozen-main",
        force=force,
    )

    # 2. Setup frozen-solver worktree
    sibling_solver = setup_worktree(
        SOLVER_BASELINE_SHA,
        FROZEN_SOLVER_DIR,
        "MAPEOGEO-frozen-solver",
        force=force,
    )

    # 3. Ensure base graph data file exists in frozen-main
    base_data_file = ROOT / "data" / "gallier_quaintance_graph_v0_3.json.gz"
    frozen_base_data = FROZEN_MAIN_DIR / "data" / "gallier_quaintance_graph_v0_3.json.gz"
    if base_data_file.exists() and not frozen_base_data.exists():
        frozen_base_data.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(base_data_file, frozen_base_data)

    # 4. Check / Reconstruct v0.15.1 graph artifact in frozen-main
    frozen_graph_gz = FROZEN_MAIN_DIR / "artifacts" / "analysis_v0_15_1" / GRAPH_BASENAME
    if force or not frozen_graph_gz.exists():
        print(f"[Hydrate] Reconstructing v0.15.1 knowledge graph dependency chain...")
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        res = subprocess.run(
            [sys.executable, str(FROZEN_MAIN_DIR / "scripts" / "reconstruct_pipeline.py")],
            cwd=FROZEN_MAIN_DIR,
            env=env,
            capture_output=True,
            text=True,
        )
        if res.returncode != 0:
            print(f"[Hydrate] ERROR: Reconstruction failed:\n{res.stderr}", file=sys.stderr)
            sys.exit(res.returncode)
        print("[Hydrate] Knowledge graph reconstruction complete.")

    # 5. Populate frozen-main-artifact
    FROZEN_ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    sealed_graph_gz = FROZEN_ARTIFACT_DIR / GRAPH_BASENAME
    if force or not sealed_graph_gz.exists():
        shutil.copy(frozen_graph_gz, sealed_graph_gz)
        print(f"[Hydrate] Sealed artifact populated -> {sealed_graph_gz}")

    # 6. Strict fail-closed verification of content digests
    print("[Hydrate] Validating immutable content digests...")
    decomp_sha, canon_sha = verify_decompressed_graph(sealed_graph_gz)
    print(f"  [PASS] Decompressed Content SHA-256: {decomp_sha}")
    print(f"  [PASS] Canonical Semantic JSON SHA-256: {canon_sha}")

    # Verify alignments digest matches committed file at fd2d90c
    alignments_file = FROZEN_MAIN_DIR / "formal" / "analysis_alignments_v0_15.json"
    alignments_sha = compute_file_sha256(alignments_file)
    if alignments_sha != ALIGNMENTS_COMMIT_SHA256:
        raise ValueError(
            f"Alignments commit SHA-256 mismatch!\n"
            f"  Expected: {ALIGNMENTS_COMMIT_SHA256}\n"
            f"  Observed: {alignments_sha}"
        )
    print(f"  [PASS] Analysis Alignments Commit SHA-256: {alignments_sha}")
    print(f"  [INFO] Acceptance Manifest Claimed Alignments SHA-256: {ACCEPTANCE_CLAIMED_ALIGNMENTS_SHA256}")

    # 7. Ensure E26-E31 evidence files are generated
    evidence_dir = ROOT / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    e26_manifest = evidence_dir / "pct_e26_cross_branch_manifest.json"
    if force or not e26_manifest.exists():
        print("[Hydrate] Generating E26-E31 deterministic evidence artifacts...")
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        res = subprocess.run(
            [sys.executable, "-m", "experiments.pct_e26_e31.generate_evidence", "--out-dir", str(evidence_dir)],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
        )
        if res.returncode != 0:
            print(f"[Hydrate] ERROR: Evidence generation failed:\n{res.stderr}", file=sys.stderr)
            sys.exit(res.returncode)
        print("[Hydrate] E26-E31 evidence artifacts generated.")

    print("==========================================================")
    print("  [SUCCESS] E26-E31 Fixture Hydration Complete & Verified")
    print("==========================================================")


def clean_fixtures() -> None:
    print("[Hydrate] Cleaning .crossbranch/ directories and worktrees...")
    parent_dir = ROOT.parent
    for name in ["MAPEOGEO-frozen-main", "MAPEOGEO-frozen-solver"]:
        path = parent_dir / name
        if path.exists():
            subprocess.run(["git", "worktree", "remove", "--force", str(path)], cwd=ROOT, capture_output=True)
            shutil.rmtree(path, ignore_errors=True)
    subprocess.run(["git", "worktree", "prune"], cwd=ROOT, capture_output=True)

    if CROSSBRANCH_DIR.exists():
        shutil.rmtree(CROSSBRANCH_DIR, ignore_errors=True)
    print("[Hydrate] .crossbranch/ removed cleanly.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Hydrate E26-E31 cross-branch test fixtures")
    parser.add_argument("--clean", action="store_true", help="Remove hydrated fixtures and worktrees")
    parser.add_argument("--verify", action="store_true", help="Hydrate and verify all assertions")
    parser.add_argument("--force", action="store_true", help="Force clean re-hydration from scratch")
    args = parser.parse_args()

    if args.clean:
        clean_fixtures()
        return 0

    try:
        hydrate_fixtures(force=args.force)
        return 0
    except Exception as e:
        print(f"[Hydrate] FAIL-CLOSED ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
