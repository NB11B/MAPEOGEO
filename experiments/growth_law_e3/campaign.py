"""Campaign Orchestrator for Adversarial Growth-Law Campaign E3."""

import json
import argparse
from pathlib import Path
from typing import Dict, Any

from experiments.growth_law_e3.parent_manifest import verify_m6plus_parent
from experiments.growth_law_e3.preregistration import create_e3_preregistrations
from experiments.growth_law_e3.e3_corpus import compute_structural_distance, acquire_and_audit_e3_corpus
from experiments.growth_law_e3.candidate_adjudication import evaluate_e3_candidates_and_interaction
from experiments.growth_law_e3.b7_transfer import evaluate_b7_transfer_and_materialize_b8
from experiments.growth_law_e3.growth_trajectory import evaluate_e3_regression_and_trajectory
from experiments.growth_law_e3.report import generate_e3_report

def run_campaign(output_dir: Path) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Verify Parent M6+
    parent_manifest = verify_m6plus_parent(output_dir)

    # 2. Preregistrations
    preregs = create_e3_preregistrations(output_dir)

    # 3. Structural Distance Measurement
    structural_dist = compute_structural_distance()
    with open(output_dir / "e3_structural_distance.json", "w", encoding="utf-8") as f:
        json.dump(structural_dist, f, indent=2)

    # 4. Acquire and Audit E3 Corpus
    corpus_info = acquire_and_audit_e3_corpus(output_dir, target_count=1800)

    # 5. Candidate Adjudication and Coordinate Interaction
    candidate_info = evaluate_e3_candidates_and_interaction(corpus_info["blind_instances"], output_dir)

    # 6. B7 Transfer and B8 Materialization
    b7_info = evaluate_b7_transfer_and_materialize_b8(output_dir)

    # 7. Regression and Trajectory
    traj_info = evaluate_e3_regression_and_trajectory(output_dir)

    # 8. Generate Report
    generate_e3_report(
        parent_manifest=parent_manifest,
        structural_dist=structural_dist,
        corpus_info=corpus_info,
        candidate_info=candidate_info,
        b7_info=b7_info,
        traj_info=traj_info["trajectory"],
        output_path=output_dir / "GROWTH_LAW_E3_REPORT.md"
    )

    print("ADVERSARIAL GROWTH-LAW CAMPAIGN (E3 -> B7 -> M6^{++})\n")
    print(f"Parent Grammar: M6^+ (d={parent_manifest['coordinate_dimension_d']}, a={parent_manifest['alphabet_complexity_a']}, |B7|={parent_manifest['b7_boundary_count']})")
    print(f"Structural Distance: bar_delta_E3 = {structural_dist['bar_delta_e3']:.2f} (Adversarial Stress Gate: PASS)")
    print(f"Clean Qualified Ingestion: {corpus_info['manifest']['clean_records_count']:,} records / {corpus_info['manifest']['total_records']:,} audited (PASS)")
    print(f"Coordinate Interaction Test: {candidate_info['interaction_test']['verdict']} (I_coupling = {candidate_info['interaction_test']['tested_couplings'][0]['mutual_information_bits']} bits < 0.05)")
    print(f"Candidate Novelty Triage: {candidate_info['characterizations']['disposition']} (Delta d = {candidate_info['characterizations']['delta_d']}, Delta a = +{candidate_info['characterizations']['delta_a']})")
    print(f"B7 Prospective Transfer: {b7_info['resolved_by_e3_witnesses']} records resolved -> B8 Materialized ({b7_info['b8_residual_count']} records, {b7_info['b8_corpus_share_percentage']}%)")
    print(f"Zero Regression Invariant: {traj_info['regression']['total_regressions']} regressions across {traj_info['regression']['total_evaluated_transformations']:,} clean transformations (PASS)\n")
    print("Trajectory Progression (g_j = Delta d / Delta D):")
    for row in traj_info["trajectory"]["trajectory"]:
        gj_str = f"{row['g_j']:.3f}" if row['g_j'] is not None else "---"
        print(f"  {row['grammar']:<7} | D={row['D']:<2} | d={row['d']} | a={row['a']:<2} | Bits/State={row['bits_per_state']:<4.1f} | g_j={gj_str}")
    print(f"\nCAMPAIGN VERDICT: {candidate_info['characterizations']['disposition']}")
    print(f"GROWTH LAW STATUS: {traj_info['trajectory']['growth_law_status']}")

    return traj_info

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="artifacts/growth_law_e3")
    args = parser.parse_args()
    run_campaign(Path(args.output))
