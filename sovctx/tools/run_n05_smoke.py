from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sovctx.node.config import load_config
from sovctx.node.smoke import SmokeQualification


def main() -> int:
    parser = argparse.ArgumentParser(
        description="SOVCTX Gate N0.5 Physical Smoke Qualification Runner"
    )
    parser.add_argument("--config", type=Path, default=None, help="Path to config.yaml")
    parser.add_argument("--batch", type=int, default=10, help="Batch acquisition count (default: 10)")
    parser.add_argument("--json", action="store_true", help="Print JSON receipt to stdout")
    args = parser.parse_args()

    config = load_config(args.config)
    runner = SmokeQualification(config=config, batch_size=args.batch)
    receipt = runner.run()

    if args.json:
        print(json.dumps(receipt.__dict__, indent=2))
    else:
        m = receipt.measurements
        print(f"===========================================================")
        print(f"SOVCTX Gate N0.5 Physical Smoke Qualification: {receipt.verdict}")
        print(f"Campaign: {receipt.campaign_id}")
        print(f"Node:     {receipt.target_node}")
        print(f"===========================================================")
        print(f"N0.5_SMOKE")
        print(f"├── queue_before:           {m['queue_before']}")
        print(f"├── queue_after:            {m['queue_after']}")
        print(f"├── successful_fetches:     {m['successful_fetches']}")
        print(f"├── retry_wait:             {m['retry_wait']}")
        print(f"├── terminal_failures:      {m['terminal_failures']}")
        print(f"├── quarantined:            {m['quarantined']}")
        print(f"├── deduplicated:           {m['deduplicated']}")
        print(f"├── CAS blobs:              {m['cas_blobs']}")
        print(f"├── CAS bytes:              {m['cas_bytes']} bytes")
        print(f"├── SHA256 verification:    {m['sha256_verification']}")
        print(f"├── WAL size:               {m['wal_size_bytes']} bytes")
        print(f"├── RAM available:          {m['ram_available_mb']} MB (peak avail: {m['ram_peak_available_mb']} MB)")
        print(f"├── swap delta:             {m['swap_delta_gb']} GB")
        print(f"├── load peak:              {m['load_peak']}")
        print(f"├── thermal peak:           {m['thermal_peak_c']} °C")
        print(f"├── disk delta:             {m['disk_delta_gb']} GB (free: {m['disk_free_gb']} GB)")
        print(f"└── isolation violations:   {m['isolation_violations']}")
        print(f"===========================================================")
        print(f"Receipt written to: {receipt.manifest_path}")

    return 0 if receipt.verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
