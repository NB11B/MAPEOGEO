import sys
import time
from pathlib import Path

# Ensure workspace root is in sys.path
root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from sovctx.node.graph_controls import GraphControlsEngine


def main() -> None:
    t0 = time.time()
    engine = GraphControlsEngine(seed=42)
    output_dir = Path("sovctx/audits/r1")
    dossier = engine.export_controls_dossier(output_dir, iterations=100)
    elapsed = time.time() - t0
    print(f"Completed 100 iterations of all 4 controls in {elapsed:.2f}s")
    for c in dossier["controls"]:
        print(f"== {c['control_id']}: {c['control_name']} ==")
        for s in c["statistics"]:
            print(
                f"  {s['metric_name']}: obs={s['observed_value']}, "
                f"null_mean={s['control_mean']}, null_std={s['control_std']}, "
                f"Z={s['z_score']}, p={s['p_value']}"
            )


if __name__ == "__main__":
    main()
