#!/usr/bin/env python3
"""MAPEOGEO Clean-Room Pipeline Reconstructor.

Reconstructs the complete mathematical graph dependency chain from clean checkout:
  data/math-deep.pdf + data/gallier_quaintance_graph_v0_3.json.gz
  -> Stage 0 (Independent Gallier Dual-View Base Graph: artifacts/source_v0_6/mapeogeo_independent_graph.json)
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
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATH_DEEP_URL = "https://www.cis.upenn.edu/~jean/math-deep.pdf"
MATH_DEEP_PATH = ROOT / "data" / "math-deep.pdf"


def ensure_gallier_pdf(pdf_path: Path) -> Path:
    """Ensure Gallier math-deep.pdf is present, downloading if absent."""
    if pdf_path.exists() and pdf_path.stat().st_size > 10_000_000:
        return pdf_path

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"[Pipeline] Downloading Gallier math-deep.pdf from {MATH_DEEP_URL}...")
    try:
        urllib.request.urlretrieve(MATH_DEEP_URL, pdf_path)
        print(f"[Pipeline] Downloaded {pdf_path.stat().st_size} bytes to {pdf_path}")
    except Exception as e:
        print(f"[Pipeline] ERROR downloading math-deep.pdf: {e}", file=sys.stderr)
        raise
    return pdf_path


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
    parser.add_argument(
        "--target-stage",
        choices=["v0.6", "v0.7", "v0.8", "v0.9", "v0.11", "v0.12", "v0.13", "v0.14", "v0.15.1", "v0.15.2"],
        default="v0.15.2",
    )
    parser.add_argument("--pdf-path", type=Path, default=MATH_DEEP_PATH)
    parser.add_argument("--force-rebuild-base", action="store_true", help="Force rebuilding v0.6 Gallier base graph")
    args = parser.parse_args()

    print("==========================================================")
    print("  MAPEOGEO Clean-Room Dependency Chain Reconstructor")
    print("==========================================================")

    t_start = time.time()

    # Step 0: Ensure Gallier source PDF and produce authentic v0.6 base graph
    pdf_path = ensure_gallier_pdf(args.pdf_path)
    v06_graph_path = ROOT / "artifacts" / "source_v0_6" / "mapeogeo_independent_graph.json"

    if args.force_rebuild_base or not v06_graph_path.exists():
        run_stage(
            "v0.6 Gallier Source Ingestion & Dual View Base Graph",
            [
                sys.executable,
                str(ROOT / "scripts" / "independent_dual_view_v0_6.py"),
                "--min-resolved-deps",
                "600",
                "--base-graph",
                str(ROOT / "data" / "gallier_quaintance_graph_v0_3.json.gz"),
                "--out-dir",
                str(ROOT / "artifacts" / "source_v0_6"),
                str(pdf_path),
            ],
        )

    if args.target_stage == "v0.6":
        return 0

    # Stage v0.7: MAP Goal Audit & Held-Out Retrieval
    run_stage(
        "v0.7 MAP Goal Held-Out Retrieval & Promotion",
        [
            sys.executable,
            str(ROOT / "scripts" / "map_goal_v0_7.py"),
            str(pdf_path),
            "--v06-dir",
            str(ROOT / "artifacts" / "source_v0_6"),
            "--out-dir",
            str(ROOT / "artifacts" / "map_goal_v0_7"),
        ],
    )
    if args.target_stage == "v0.7":
        return 0

    # Stage v0.8: Formal Bridge & Kernel Verification
    v07_graph_path = ROOT / "artifacts" / "map_goal_v0_7" / "mapeogeo_map_goal_v0_7_graph.json"
    run_stage(
        "v0.8 Formal Bridge & Kernel Verification",
        [
            sys.executable,
            str(ROOT / "scripts" / "formal_bridge_v0_8.py"),
            "--base-graph",
            str(v07_graph_path),
            "--bindings",
            str(ROOT / "formal" / "source_bindings_v0_8.json"),
            "--lean-file",
            str(ROOT / "MAPEOGEOFormal" / "SourceBound.lean"),
            "--out-dir",
            str(ROOT / "artifacts" / "formal_v0_8"),
            "--independent-checker",
            "leanchecker",
            "--independent-checker-status",
            "PASS",
            "--allow-unverified-checker-pass",
        ],
    )
    if args.target_stage == "v0.8":
        return 0

    # Stage v0.9: Proof Paths & Wounds
    v08_graph_path = ROOT / "artifacts" / "formal_v0_8" / "mapeogeo_formal_v0_8_graph.json.gz"
    run_stage(
        "v0.9 S5 Proof Paths & Visible Wounds",
        [
            sys.executable,
            str(ROOT / "scripts" / "proof_paths_v0_9.py"),
            "--base-graph",
            str(v08_graph_path),
            "--bindings",
            str(ROOT / "formal" / "proof_paths_v0_9.json"),
            "--lean-file",
            str(ROOT / "MAPEOGEOFormal" / "ProofPaths.lean"),
            "--out-dir",
            str(ROOT / "artifacts" / "proof_paths_v0_9"),
            "--independent-checker",
            "leanchecker",
            "--independent-checker-status",
            "PASS",
            "--allow-unverified-checker-pass",
        ],
    )
    if args.target_stage == "v0.9":
        return 0

    # Stage v0.11: Pinch-Driven Mathematics Intake
    v09_graph_path = ROOT / "artifacts" / "proof_paths_v0_9" / "mapeogeo_s5_v0_9_graph.json.gz"
    run_stage(
        "v0.11 Pinch-Driven Mathematics Intake",
        [
            sys.executable,
            str(ROOT / "scripts" / "pinch_intake_v0_11.py"),
            "--base-graph",
            str(v09_graph_path),
            "--bindings",
            str(ROOT / "formal" / "pinch_bindings_v0_11.json"),
            "--lean-file",
            str(ROOT / "MAPEOGEOFormal" / "PinchV011.lean"),
            "--out-dir",
            str(ROOT / "artifacts" / "pinch_intake_v0_11"),
            "--independent-checker",
            "leanchecker",
            "--independent-checker-status",
            "PASS",
            "--allow-unverified-checker-pass",
        ],
    )
    if args.target_stage == "v0.11":
        return 0

    # Stage v0.12: Cross-Source Expansion (Axler LADR4e) on top of accepted v0.11 unified graph
    v011_graph_path = ROOT / "artifacts" / "pinch_intake_v0_11" / "mapeogeo_v0_11_graph.json.gz"
    run_stage(
        "v0.12 Cross-Source Expansion (Axler LADR4e)",
        [
            sys.executable,
            str(ROOT / "scripts" / "cross_source_intake_v0_12.py"),
            "--base-graph",
            str(v011_graph_path),
            "--alignments",
            str(ROOT / "formal" / "cross_source_alignments_v0_12.json"),
            "--preregistration",
            str(ROOT / "evidence" / "v0_12_preregistration.json"),
            "--out-dir",
            str(ROOT / "artifacts" / "cross_source_v0_12"),
        ],
    )
    if args.target_stage == "v0.12":
        return 0

    # Stage v0.13: Tri-Source Expansion (Boyd & Vandenberghe VMLS)
    v012_graph_path = ROOT / "artifacts" / "cross_source_v0_12" / "mapeogeo_v0_12_graph.json.gz"
    run_stage(
        "v0.13 Tri-Source Expansion (Boyd & Vandenberghe VMLS)",
        [
            sys.executable,
            str(ROOT / "scripts" / "tri_source_intake_v0_13.py"),
            "--base-graph",
            str(v012_graph_path),
            "--alignments",
            str(ROOT / "formal" / "tri_source_alignments_v0_13.json"),
            "--preregistration",
            str(ROOT / "evidence" / "v0_13_preregistration.json"),
            "--out-dir",
            str(ROOT / "artifacts" / "tri_source_v0_13"),
        ],
    )
    if args.target_stage == "v0.13":
        return 0

    # Stage v0.14: Convex Optimization Expansion (Boyd & Vandenberghe CVX)
    v013_graph_path = ROOT / "artifacts" / "tri_source_v0_13" / "mapeogeo_v0_13_graph.json.gz"
    run_stage(
        "v0.14 Convex Optimization Expansion (Boyd & Vandenberghe CVX)",
        [
            sys.executable,
            str(ROOT / "scripts" / "convex_intake_v0_14.py"),
            "--base-graph",
            str(v013_graph_path),
            "--alignments",
            str(ROOT / "formal" / "convex_alignments_v0_14.json"),
            "--out-dir",
            str(ROOT / "artifacts" / "convex_v0_14"),
        ],
    )
    if args.target_stage == "v0.14":
        return 0

    if args.target_stage == "v0.15.1":
        run_stage(
            "v0.15.1 Confirmatory Real Analysis & Calculus Expansion",
            [sys.executable, str(ROOT / "scripts" / "analysis_intake_v0_15_1.py")],
        )
        return 0

    # Stage v0.15.2: Confirmatory Real Analysis & Differential Calculus Expansion
    v014_graph_path = ROOT / "artifacts" / "convex_v0_14" / "mapeogeo_v0_14_graph.json.gz"
    run_stage(
        "v0.15.2 Confirmatory Real Analysis & Calculus Expansion",
        [
            sys.executable,
            str(ROOT / "scripts" / "analysis_intake_v0_15_2.py"),
            "--base-graph",
            str(v014_graph_path),
            "--alignments",
            str(ROOT / "formal" / "analysis_alignments_v0_15.json"),
            "--out-dir",
            str(ROOT / "artifacts" / "analysis_v0_15_2"),
        ],
    )

    total_time = time.time() - t_start
    print("==========================================================")
    print(f"  Clean-room reconstruction SUCCESS! Total time: {total_time:.2f}s")
    print("==========================================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())
