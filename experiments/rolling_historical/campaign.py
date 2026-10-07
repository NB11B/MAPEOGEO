"""Master Orchestration Runner for Campaign H2 (Rolling Historical Replications)."""

import json
from pathlib import Path
from typing import Dict, Any

from experiments.rolling_historical.historical_epochs import ROLLING_ORIGINS
from experiments.rolling_historical.epoch_replay import execute_epoch_replay
from experiments.rolling_historical.meta_analysis import (
    run_random_effects_meta_analysis,
    evaluate_gate_criteria
)
from experiments.rolling_historical.frontier_2026 import generate_live_2026_frontier
from experiments.rolling_historical.report import generate_h2_report

DEFAULT_OUTPUT_DIR = Path("artifacts/rolling_historical_h2")

def run_campaign_h2(output_dir: Path = DEFAULT_OUTPUT_DIR) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    print("=" * 70)
    print("CAMPAIGN H2: ROLLING HISTORICAL DISCOVERY REPLICATIONS (1900-2010)")
    print("=" * 70)

    # 1. Execute Isolated Epoch Replays across all 12 origins
    epoch_summaries = []
    for year in ROLLING_ORIGINS:
        print(f"Replaying Origin t = {year}...")
        res = execute_epoch_replay(year, output_dir)
        epoch_summaries.append(res)

    # 2. Random-Effects Meta-Analysis
    print("Computing DerSimonian-Laird Random-Effects Meta-Analysis...")
    meta_results = run_random_effects_meta_analysis(epoch_summaries)
    with open(output_dir / "meta_analysis_results.json", "w", encoding="utf-8") as f:
        json.dump(meta_results, f, indent=2)

    # 3. Evaluate Preregistered 6 Gates
    print("Evaluating Preregistered Gates for Live 2026 Prospective Frontier...")
    gate_results = evaluate_gate_criteria(epoch_summaries, meta_results)
    with open(output_dir / "gate_evaluation_results.json", "w", encoding="utf-8") as f:
        json.dump(gate_results, f, indent=2)

    # 4. If Gates Pass: Generate Live 2026 Frontier and Freeze
    frontier_2026_data = {}
    if gate_results["live_2026_frontier_unlocked"]:
        print("All 6 Gates PASSED! Generating and Freezing Live 2026 Prospective Frontier...")
        frontier_2026_data = generate_live_2026_frontier(output_dir / "frontier_2026")

    # 5. Generate Campaign Closure Report
    print("Generating ROLLING_HISTORICAL_H2_REPORT.md...")
    report_content = generate_h2_report(
        output_dir=output_dir,
        epoch_summaries=epoch_summaries,
        meta_results=meta_results,
        gate_results=gate_results,
        frontier_2026_data=frontier_2026_data
    )

    print("Campaign H2 completed successfully.")
    return {
        "status": gate_results["campaign_status"],
        "meta_results": meta_results,
        "gate_results": gate_results,
        "frontier_2026": frontier_2026_data,
        "report": report_content
    }

if __name__ == "__main__":
    run_campaign_h2()
