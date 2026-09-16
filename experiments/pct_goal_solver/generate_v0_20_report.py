from __future__ import annotations

import json
from pathlib import Path

from .v0_20_campaign import execute_v0_20_campaign


def generate_v0_20_report() -> dict:
    result = execute_v0_20_campaign()
    out_dir = Path("evidence")
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "pct_v0_20_cross_class_solver_report.json"
    
    # Clean up serialization
    report_path.write_text(json.dumps(result, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(f"PCT_GOAL_SOLVER_V0_20: {result['scientific_status']} gates={result['gates_passed']}/{result['gates_total']} wrong_positives={result['total_wrong_positives']}")
    print(f"Report saved to {report_path}")
    return result


if __name__ == "__main__":
    generate_v0_20_report()
