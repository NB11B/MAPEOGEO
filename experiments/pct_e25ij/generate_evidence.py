from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from experiments.pct_e25ij.lifecycle import run_e25i_audit
from experiments.pct_e25ij.scenarios import run_e25j_scenarios


def _write(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def generate(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    e25i = run_e25i_audit()
    e25j = run_e25j_scenarios()
    _write(output_dir / "pct_e25i_closure_receipt_ledger.json", e25i["ledger"])
    _write(output_dir / "pct_e25i_derived_closure_snapshot.json", e25i["snapshot"])
    _write(output_dir / "pct_e25j_revocation_staleness.json", e25j)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic E25I/E25J candidate evidence.")
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    generate(args.out_dir)


if __name__ == "__main__":
    main()
