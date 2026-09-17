from __future__ import annotations

from pathlib import Path
import argparse
import json

from experiments.pct_e25gh.morphisms import run_c5a_audit
from experiments.pct_e25gh.provenance import run_c5b_audit
from experiments.pct_e25gh.policies import run_e25h_policy_comparison


def _write(path: Path, value: dict) -> None:
    path.write_text(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def generate(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _write(output_dir / "pct_e25g_exact_morphism_audit.json", run_c5a_audit())
    _write(output_dir / "pct_e25g_provenance_bindings.json", run_c5b_audit())
    _write(output_dir / "pct_e25h_policy_comparison.json", run_e25h_policy_comparison())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    generate(args.out_dir)


if __name__ == "__main__":
    main()
