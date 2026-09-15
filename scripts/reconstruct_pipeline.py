#!/usr/bin/env python3
"""MAPEOGEO Clean-Room Pipeline Reconstructor.

Reconstructs the complete mathematical graph dependency chain from clean checkout:
  data/gallier_quaintance_graph_v0_3.json.gz
  -> v0.12 (Cross-Source: Axler LADR4e)
  -> v0.13 (Tri-Source: Boyd & Vandenberghe VMLS)
  -> v0.14 (Quad-Source: Boyd & Vandenberghe CVX)
  -> v0.15.2 (Confirmatory Quad-Source: Real Analysis & Multivariable Differential Calculus)

Ensures zero dependency on dirty local workspace artifacts and provides 100% clean-room reproducibility.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_stage(name: str, cmd: list[str]) -> None:
    print(f"\n[Pipeline] === Executing Stage: {name} ===")
    t0 = time.time()
    res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    dt = time.time() - t0
    if res.returncode != 0:
        print(f"[Pipeline] ERROR: Stage {name} failed with return code {res.returncode}:")
        print(res.stdout)
        print(res.stderr, file=sys.stderr)
        sys.exit(res.returncode)
    print(f"[Pipeline] Completed {name} in {dt:.2f}s")
    for line in res.stdout.strip().splitlines()[-6:]:
        print(f"  {line}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Reconstruct MAPEOGEO mathematical graph chain from scratch")
    parser.add_argument("--target-stage", choices=["v0.12", "v0.13", "v0.14", "v0.15.1", "v0.15.2"], default="v0.15.2")
    args = parser.parse_args()

    print("==========================================================")
    print("  MAPEOGEO Clean-Room Dependency Chain Reconstructor")
    print("==========================================================")

    t_start = time.time()

    # Stage v0.12
    run_stage(
        "v0.12 Cross-Source Expansion (Axler LADR4e)",
        [sys.executable, str(ROOT / "scripts" / "cross_source_intake_v0_12.py")]
    )
    if args.target_stage == "v0.12":
        return 0

    # Stage v0.13
    run_stage(
        "v0.13 Tri-Source Expansion (Boyd & Vandenberghe VMLS)",
        [sys.executable, str(ROOT / "scripts" / "tri_source_intake_v0_13.py")]
    )
    if args.target_stage == "v0.13":
        return 0

    # Stage v0.14
    run_stage(
        "v0.14 Convex Optimization Expansion (Boyd & Vandenberghe CVX)",
        [sys.executable, str(ROOT / "scripts" / "convex_intake_v0_14.py")]
    )
    if args.target_stage == "v0.14":
        return 0

    if args.target_stage == "v0.15.1":
        run_stage(
            "v0.15.1 Confirmatory Real Analysis & Calculus Expansion",
            [sys.executable, str(ROOT / "scripts" / "analysis_intake_v0_15_1.py")]
        )
        return 0

    # Stage v0.15.2
    run_stage(
        "v0.15.2 Confirmatory Real Analysis & Calculus Expansion",
        [sys.executable, str(ROOT / "scripts" / "analysis_intake_v0_15_2.py")]
    )

    total_time = time.time() - t_start
    print("==========================================================")
    print(f"  Clean-room reconstruction SUCCESS! Total time: {total_time:.2f}s")
    print("==========================================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())
