"""Campaign Execution Runner for Growth-Law Campaign E4."""

import json
from pathlib import Path
from typing import Dict, Any

from .parent_manifest import verify_m6plusplus_parent
from .preregistration import create_e4_preregistrations
from .e4_corpus import acquire_and_audit_e4_corpus
from .interaction_audit import audit_coordinate_interaction_and_composition
from .candidate_adjudication import adjudicate_e4_candidates
from .b8_transfer import evaluate_b8_transfer_and_materialize_b9
from .growth_trajectory import evaluate_e4_regression_and_trajectory
from .report import generate_e4_report

def run_campaign_e4(output_dir: Path = None) -> Dict[str, Any]:
    if output_dir is None:
        output_dir = Path("artifacts/growth_law_e4")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Step 1: Verifying M6^{++} parent architecture and B8 boundary...")
    parent_data = verify_m6plusplus_parent(output_dir)

    print("Step 2: Recording E4 preregistration and failure modes...")
    prereg_data = create_e4_preregistrations(output_dir)

    print("Step 3: Acquiring E4 dense interaction corpus and auditing contamination...")
    corpus_data = acquire_and_audit_e4_corpus(output_dir, target_count=3000)

    print("Step 4: Executing information-theoretic interaction audit and composition complexity audit...")
    interaction_data = audit_coordinate_interaction_and_composition(output_dir)

    print("Step 5: Adjudicating candidate novelty via hierarchical reduction...")
    adjudication_data = adjudicate_e4_candidates(output_dir)

    print("Step 6: Executing B8 boundary transfer and materializing B9...")
    b8_data = evaluate_b8_transfer_and_materialize_b9(output_dir)

    print("Step 7: Evaluating zero regressions and updating trajectory...")
    trajectory_data = evaluate_e4_regression_and_trajectory(output_dir)

    print("Step 8: Generating Campaign E4 Closure Report...")
    report_content = generate_e4_report(
        output_dir=output_dir,
        parent_data=parent_data,
        prereg_data=prereg_data,
        corpus_data=corpus_data,
        interaction_data=interaction_data,
        adjudication_data=adjudication_data,
        b8_data=b8_data,
        trajectory_data=trajectory_data
    )

    print("Campaign E4 execution complete.")
    return {
        "status": "E4_PASS_FACTORIZATION_AND_COMPACTNESS_MAINTAINED",
        "parent": parent_data,
        "corpus": corpus_data,
        "interaction": interaction_data,
        "adjudication": adjudication_data,
        "b8_transfer": b8_data,
        "trajectory": trajectory_data,
        "report": report_content
    }

if __name__ == "__main__":
    run_campaign_e4()
