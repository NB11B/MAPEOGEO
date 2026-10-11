from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sovctx.node.config import load_config


def inspect_n5_status(evidence_dir: Path) -> int:
    n5_dir = evidence_dir / "n5"
    if not n5_dir.exists():
        print(f"No N5 endurance campaign found at {n5_dir}")
        return 1

    print("===========================================================")
    print("SOVCTX Gate N5 Autonomous Endurance Inspection")
    print(f"Evidence Directory: {n5_dir}")
    print("===========================================================")

    # 1. Check Circuit Breaker Pause Flags
    res_pause = n5_dir / "RESOURCE_PAUSE"
    epis_pause = n5_dir / "EPISTEMIC_PAUSE"

    if res_pause.exists():
        data = json.loads(res_pause.read_text(encoding="utf-8"))
        print(f"\n[ALERT] RESOURCE_PAUSE ACTIVE:")
        print(f"  Triggered: {data.get('triggered_at')}")
        print(f"  Reason   : {data.get('reason')}")
    elif epis_pause.exists():
        data = json.loads(epis_pause.read_text(encoding="utf-8"))
        print(f"\n[ALERT] EPISTEMIC_PAUSE ACTIVE:")
        print(f"  Triggered: {data.get('triggered_at')}")
        print(f"  Reason   : {data.get('reason')}")
    else:
        print("\n[OK] Circuit Breakers: ALL CLEAR (No pauses active)")

    # 2. Latest Checkpoint
    chk_file = n5_dir / "checkpoints" / "latest_checkpoint.json"
    if chk_file.exists():
        chk = json.loads(chk_file.read_text(encoding="utf-8"))
        print("\n--- Latest Checkpoint ---")
        print(f"  Checkpoint ID      : {chk.get('checkpoint_id')}")
        print(f"  Timestamp          : {chk.get('timestamp')}")
        print(f"  Epoch Index        : {chk.get('epoch_index')}")
        print(f"  Sources Count      : {chk.get('sources_count')}")
        print(f"  Passages Count     : {chk.get('passages_count')}")
        print(f"  Open Frontier      : {chk.get('frontier_open_count')}")
        print(f"  Unresolved Items   : {chk.get('unresolved_count')}")
        print(f"  Dossiers Count     : {chk.get('dossiers_count')}")
        print(f"  Dirty Synthesis    : {chk.get('dirty_synthesis_keys')}")
        print(f"  CAS Blobs Count    : {chk.get('cas_blobs_count')}")

    # 3. Epochs Progression
    epoch_files = sorted((n5_dir / "epochs").glob("epoch_*.json"))
    if epoch_files:
        print(f"\n--- Completed Epochs ({len(epoch_files)} total) ---")
        print(f"  {'Epoch':<10} | {'Duration':<10} | {'Admitted':<10} | {'r_sources':<10} | {'Entropy':<8} | {'RSS (MB)':<10} | {'Temp':<8}")
        print("  " + "-" * 75)
        for ef in epoch_files[-10:]:
            e = json.loads(ef.read_text(encoding="utf-8"))
            rt = e.get("resource_telemetry", {})
            rates = e.get("rates", {})
            temp_str = f"{rt.get('thermal_peak_c')} C" if rt.get("thermal_peak_c") is not None else "N/A"
            print(f"  {e['epoch_id']:<10} | {e['duration_sec']:<10.1f} | {e['sources_admitted']:<10} | {rates.get('r_sources', 0.0):<10.2f} | {e['frontier_entropy']:<8.2f} | {rt.get('worker_rss_mb', 0.0):<10.1f} | {temp_str:<8}")

    # 4. Final Receipt
    receipt_file = n5_dir / "final" / "n5_endurance_receipt.json"
    if receipt_file.exists():
        rec = json.loads(receipt_file.read_text(encoding="utf-8"))
        print("\n--- Final Campaign Receipt ---")
        print(f"  Verdict            : {rec.get('verdict')}")
        print(f"  Termination Reason : {rec.get('termination_reason')}")
        print(f"  Actual Duration    : {rec.get('duration_actual_seconds')} s")
        print(f"  Growth Efficiency  : {rec.get('useful_growth_efficiency', 0.0) * 100:.1f}%")
        print(f"  Epistemic Rate re  : {rec.get('epistemic_error_rate_re_t'):.4f} errors/s")

    print("===========================================================")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="SOVCTX Gate N5 Campaign Inspector")
    parser.add_argument("--config", type=Path, default=None, help="Path to config.yaml")
    args = parser.parse_args()

    config = load_config(args.config)
    return inspect_n5_status(config.evidence_dir)


if __name__ == "__main__":
    raise SystemExit(main())
