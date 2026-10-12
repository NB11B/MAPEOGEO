"""SOVCTX Autonomous Research Frontier 2-Hour Shakedown Runner.

Executes a 2-hour (7,200s) autonomous research campaign across 12 ten-minute epochs (600s each)
on the Jetson Nano:
- Enforces strict 50% Spines / 30% Bridges / 20% Anomalies attention budget
- Evaluates live question probing against graph topology and grounded literature
- Evaluates autonomous evidence-driven branching into new thread families (T10+)
- Evaluates thread saturation (Delta new relations -> 0)
- Enforces fail-closed resource checks (RAM, Swap, Thermal, Disk)
- Emits epoch checkpoints to evidence/n5/checkpoints/epoch_XX.json
- Emits live telemetry heartbeat to evidence/n5/research_shakedown_live.json
- Generates discovery-oriented markdown and JSON reports
"""

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sovctx.node.research_frontier import ResearchFrontierCoordinator
from sovctx.node.research_probing import ResearchShakedownSupervisor


def main() -> int:
    parser = argparse.ArgumentParser(description="SOVCTX Autonomous Research Shakedown Runner")
    parser.add_argument(
        "--duration",
        type=int,
        default=7200,
        help="Campaign duration in seconds (default: 7200s / 2 hours)",
    )
    parser.add_argument(
        "--epoch-duration",
        type=int,
        default=600,
        help="Epoch duration in seconds (default: 600s / 10 minutes)",
    )
    parser.add_argument(
        "--pace-seconds",
        type=float,
        default=6.0,
        help="Pacing delay in seconds between question probes (default: 6.0s)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("/home/uow/sovctx-kg/evidence/n5"),
        help="Output directory for checkpoints, live state, and reports",
    )
    args = parser.parse_args()

    coord = ResearchFrontierCoordinator()
    supervisor = ResearchShakedownSupervisor(
        coordinator=coord,
        duration_seconds=args.duration,
        epoch_duration_seconds=args.epoch_duration,
        pace_seconds=args.pace_seconds,
        output_dir=args.output_dir,
    )

    receipt = supervisor.run_campaign()
    return 0 if receipt["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
