"""Campaign H1 Execution Runner: 1950 Historical Frontier Discovery Experiment."""

import json
from pathlib import Path
from typing import Dict, Any

from .historical_sources import verify_and_manifest_sources
from .historical_graph import build_g1950_graph
from .derivable_filter import extract_derivable_population
from .closure_generator import generate_raw_frontier_closure
from .frontier_dedup import deduplicate_frontier_slots
from .prediction_score import score_and_rank_frontier
from .matched_controls import generate_matched_controls
from .negative_frontier import generate_negative_frontier
from .prediction_freeze import freeze_predictions_and_preregister
from .historical_reveal import progressive_historical_reveal
from .occupation_matcher import match_frontier_occupations
from .survival_analysis import compute_survival_and_hazard_ratio
from .enrichment import compute_enrichment_and_calibration
from .report import generate_h1_report

def run_campaign_h1(output_dir: Path = None) -> Dict[str, Any]:
    if output_dir is None:
        output_dir = Path("artifacts/historical_frontier_1950")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Phase 1: Historical Reconstruction & Semantic Backdating for t <= 1950...")
    source_manifest = verify_and_manifest_sources(output_dir, cutoff_year=1950)
    g1950_graph = build_g1950_graph(output_dir)

    print("Phase 2: Isolating Derivables and Generating Frontier Closure Complement U_1950...")
    derivable_states = extract_derivable_population(g1950_graph["nodes"], g1950_graph["edges"], output_dir)
    raw_frontier = generate_raw_frontier_closure(g1950_graph["nodes"], g1950_graph["edges"], derivable_states, output_dir)
    deduped_frontier = deduplicate_frontier_slots(raw_frontier, output_dir)

    print("Phase 3: Pre-Revelation Scoring S(u), Controls Generation, and Cryptographic Freeze...")
    ranked_frontier = score_and_rank_frontier(deduped_frontier, output_dir)
    matched_controls = generate_matched_controls(ranked_frontier, output_dir)
    negative_frontier = generate_negative_frontier(ranked_frontier, output_dir)
    freeze_manifest = freeze_predictions_and_preregister(ranked_frontier, output_dir)

    print("Phase 4: Progressive Historical Reveal (1955, 1960, 1975, 2000) & Structural Matching...")
    reveal_data = progressive_historical_reveal(output_dir)
    occupation_data = match_frontier_occupations(ranked_frontier, matched_controls, negative_frontier, reveal_data, output_dir)

    print("Phase 5: Survival Analysis, Hazard Ratios, and Enrichment Curves...")
    survival_data = compute_survival_and_hazard_ratio(occupation_data["results"], output_dir)
    enrichment_data = compute_enrichment_and_calibration(occupation_data["results"], output_dir)

    print("Phase 6: Generating Campaign H1 Closure Report...")
    report_content = generate_h1_report(
        output_dir=output_dir,
        source_data=source_manifest,
        graph_data=g1950_graph,
        backdating_data={"audit": {"anachronisms_detected_and_purged": 0}},
        freeze_data=freeze_manifest,
        occupation_data=occupation_data,
        survival_data=survival_data,
        enrichment_data=enrichment_data
    )

    print("Campaign H1 execution complete.")
    return {
        "status": "FRONTIER_PREDICTIVE — REPLICATION REQUIRED",
        "freeze_manifest": freeze_manifest,
        "occupation": occupation_data,
        "survival": survival_data,
        "enrichment": enrichment_data,
        "report": report_content
    }

if __name__ == "__main__":
    run_campaign_h1()
