"""CLI entry point for Wave F5 cumulative graph intake and assembly."""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mapeogeo.wave_f5.intake import build_wave_f5_graph


def main() -> int:
    parser = argparse.ArgumentParser(description="Assemble Wave F5 cumulative active graph")
    parser.add_argument("--output", "-o", type=Path, default=None, help="Output path for wave_f5_graph.json")
    args = parser.parse_args()

    graph = build_wave_f5_graph()

    output_path = args.output
    if output_path is None:
        artifacts_dir = REPO_ROOT / "artifacts" / "wave_f5_v0_22"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        output_path = artifacts_dir / "wave_f5_graph.json"
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)

    print(f"Wave F5 graph assembled successfully: {output_path}")
    print(f"  Nodes: {len(graph['nodes'])}, Edges: {len(graph['edges'])}, Joints: {len(graph['joints'])}, Views: {len(graph['visualizations'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
