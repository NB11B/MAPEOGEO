"""Campaign Execution Runner for Growth-Law Campaign E5."""

import json
from pathlib import Path
from typing import Dict, Any

from .parent_manifest import verify_m6plusplusplus_parent
from .model_selection_freeze import freeze_model_selection_protocol
from .preregistration import create_e5_preregistrations
from .e5_corpus import acquire_and_audit_e5_corpus
from .representation_audit import audit_representation_invariance
from .interaction_and_composition_audit import audit_e5_interaction_and_composition
from .candidate_adjudication import adjudicate_e5_candidates
from .b9_transfer import evaluate_b9_transfer_and_materialize_b10
from .regression_audit import audit_e5_regression
from .model_selection_runner import execute_model_selection
from .growth_trajectory import evaluate_e5_trajectory
from .report import generate_e5_report

def run_campaign_e5(output_dir: Path = None) -> Dict[str, Any]:
    if output_dir is None:
        output_dir = Path("artifacts/growth_law_e5")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Step 1: Verifying M6^{+++} parent architecture and B9 boundary...")
    parent_data = verify_m6plusplusplus_parent(output_dir)

    print("Step 2: Freezing asymptotic model-selection protocol BEFORE data evaluation...")
    frozen_spec = freeze_model_selection_protocol(output_dir)

    print("Step 3: Recording E5 preregistrations and failure modes...")
    prereg_data = create_e5_preregistrations(output_dir)

    print("Step 4: Acquiring multi-formalism corpus across 9 formalisms and auditing contamination...")
    corpus_data = acquire_and_audit_e5_corpus(output_dir, target_count=3600)

    print("Step 5: Executing representation-invariance audit across 4 semantic tiers and adversarial controls...")
    representation_data = audit_representation_invariance(output_dir)

    print("Step 6: Auditing coordinate interaction and composition complexity...")
    interaction_data = audit_e5_interaction_and_composition(output_dir)

    print("Step 7: Adjudicating candidate novelty via hierarchical reduction...")
    adjudication_data = adjudicate_e5_candidates(output_dir)

    print("Step 8: Executing B9 boundary transfer and materializing B10...")
    b9_data = evaluate_b9_transfer_and_materialize_b10(output_dir)

    print("Step 9: Auditing zero regression invariant across 55,800 clean transformations...")
    regression_data = audit_e5_regression(output_dir)

    print("Step 10: Unlocking and executing pre-frozen model selection across 5 prospective cycles...")
    model_data = execute_model_selection(output_dir)

    print("Step 11: Recording full empirical trajectory through Milestone 6 / Cycle E5...")
    trajectory_data = evaluate_e5_trajectory(output_dir)

    print("Step 12: Generating Campaign E5 Closure Report...")
    report_content = generate_e5_report(
        output_dir=output_dir,
        parent_data=parent_data,
        prereg_data=prereg_data,
        corpus_data=corpus_data,
        representation_data=representation_data,
        interaction_data=interaction_data,
        adjudication_data=adjudication_data,
        b9_data=b9_data,
        regression_data=regression_data,
        model_data=model_data,
        trajectory_data=trajectory_data
    )

    print("Campaign E5 execution complete.")
    return {
        "status": "E5_PASS_REPRESENTATION_INVARIANCE_CONFIRMED",
        "parent": parent_data,
        "frozen_spec": frozen_spec,
        "corpus": corpus_data,
        "representation": representation_data,
        "interaction": interaction_data,
        "adjudication": adjudication_data,
        "b9_transfer": b9_data,
        "regression": regression_data,
        "model_selection": model_data,
        "trajectory": trajectory_data,
        "report": report_content
    }

if __name__ == "__main__":
    run_campaign_e5()
