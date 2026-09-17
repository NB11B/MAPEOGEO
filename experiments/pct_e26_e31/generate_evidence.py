from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .corpus import build_e26_manifest, load_knowledge_corpus
from .e27 import run_e27
from .e28 import run_e28
from .e29 import run_e29
from .e30 import run_e30
from .e31 import run_e31


EVIDENCE_FILENAMES = (
    "pct_e26_cross_branch_manifest.json",
    "pct_e27_heldout_relational_recovery.json",
    "pct_e28_minimal_evidence_nullspace.json",
    "pct_e29_rule_discovery_falsification.json",
    "pct_e30_main_pct_adversarial_replay.json",
    "pct_e31_bidirectional_closure.json",
)


def _write(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def generate(output_dir: Path, repo_root: Path, frozen_main: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    corpus = load_knowledge_corpus(frozen_main, repo_root)
    e26 = build_e26_manifest(frozen_main, repo_root)
    e27 = run_e27(corpus, repo_root)
    e28 = run_e28(e27, corpus, repo_root, max_exact_bank=8)
    e29 = run_e29(corpus, e27, repo_root)
    e30 = run_e30(repo_root, frozen_main)
    e31 = run_e31(corpus, e27, e30, repo_root)

    payloads = {
        "pct_e26_cross_branch_manifest.json": e26,
        "pct_e27_heldout_relational_recovery.json": e27,
        "pct_e28_minimal_evidence_nullspace.json": e28,
        "pct_e29_rule_discovery_falsification.json": e29,
        "pct_e30_main_pct_adversarial_replay.json": e30,
        "pct_e31_bidirectional_closure.json": e31,
    }
    if tuple(payloads) != EVIDENCE_FILENAMES:
        raise AssertionError("E26-E31 evidence filename order drifted")
    for filename in EVIDENCE_FILENAMES:
        _write(output_dir / filename, payloads[filename])


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Generate deterministic E26-E31 candidate evidence.")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=repo_root)
    parser.add_argument(
        "--frozen-main",
        type=Path,
        default=repo_root / ".crossbranch" / "frozen-main",
    )
    args = parser.parse_args()
    generate(args.out_dir, args.repo_root.resolve(), args.frozen_main.resolve())


if __name__ == "__main__":
    main()
