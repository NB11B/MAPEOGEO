"""SOVCTX Nano Research Work Plane Runner.

Executes the specialized Research Work Plane on the 2 GB Jetson Nano:
- Acquires sources, extracts evidence, queries open frontier questions
- Emits immutable CandidateBundles in PROPOSED status (PROPOSED != AUTHORIZED)
- Spools candidate bundles locally for control plane (UNO Q) pickup
- Continuously runs lightweight G1 Geometric Observer (Oja streaming update) in SHADOW_MODE
- Emits structured telemetry to evidence/n5/nano_workplane_telemetry.json
- Physical Separation: Contains ZERO admission authority or canonical write capabilities
"""

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sovctx.node.nano_research_worker import NanoResearchWorker
from sovctx.node.research_frontier import ResearchFrontierCoordinator


def main() -> int:
    parser = argparse.ArgumentParser(description="SOVCTX Nano Research Work Plane Runner")
    parser.add_argument("--worker-id", type=str, default="nano-jetson-01", help="Worker ID")
    parser.add_argument("--tracker-k", type=int, default=2, help="Subspace rank k (default: 2)")
    parser.add_argument("--tracker-alpha", type=float, default=0.5, help="Subspace memory alpha (default: 0.5)")
    parser.add_argument("--uow-id", type=str, default="UOW_BOUNDED_NANO_001", help="Unit of Work ID")
    parser.add_argument("--parent-uow-id", type=str, default=None, help="Parent Unit of Work ID")
    parser.add_argument("--telemetry-dir", type=Path, default=Path("evidence/n5"), help="Telemetry output directory")
    parser.add_argument("--spool-dir", type=Path, default=Path("evidence/n5/spool"), help="Candidate bundle spool directory")
    parser.add_argument("--single-uow", action="store_true", help="Execute single bounded UoW and exit")
    parser.add_argument(
        "--target-query",
        type=str,
        default=None,
        help="Primary research query to investigate in the local corpus cache",
    )
    args = parser.parse_args()

    print("=" * 80)
    print("SOVCTX NANO RESEARCH WORK PLANE (PHYSICAL RESEARCH WORKER NODE)")
    print(f"Worker ID: {args.worker_id} | Invariant: PROPOSED != AUTHORIZED")
    print(f"Self-Observation: G1 Geometric Observer (k={args.tracker_k}, alpha={args.tracker_alpha}) [SHADOW_MODE]")
    print(f"Admission Authority: NONE (Delegated strictly to UNO Q Control Node)")
    print("=" * 80)

    worker = NanoResearchWorker(
        worker_id=args.worker_id,
        tracker_k=args.tracker_k,
        tracker_alpha=args.tracker_alpha,
        shadow_mode=True,
        output_telemetry_dir=args.telemetry_dir,
        spool_dir=args.spool_dir,
    )

    if args.target_query:
        print(f"\n[WORK PLANE] Executing Primary Research UoW: '{args.target_query}'")
        packet = worker.execute_primary_research_uow(
            uow_id=args.uow_id,
            target_query=args.target_query,
            parent_uow_id=args.parent_uow_id,
        )
    else:
        coord = ResearchFrontierCoordinator()
        open_qs = coord.ledger.get_open_questions()
        selected_qs = open_qs[:5]

        packet = worker.process_work_unit(
            uow_id=args.uow_id,
            parent_uow_id=args.parent_uow_id,
            questions_to_probe=selected_qs,
        )

    geom = packet.geometric_observation
    bundle = packet.candidate_bundle

    print("\n--- Work Plane Execution Complete ---")
    print(f"UoW ID:                 {packet.uow_id}")
    print(f"Causal Sequence:        {packet.causal_sequence_id}")
    print(f"Candidate Status:       PROPOSED (Awaiting Control Plane Admission)")
    print(f"Evidence Hash (H_E):    {bundle.evidence_hash[:16]}...")
    print(f"Execution Hash (H_X):   {bundle.execution_hash[:16]}...")
    print(f"Software Commit:        {bundle.software_commit[:10]}")
    print(f"Source Manifest:        {bundle.source_manifest}")
    print(f"Extracted Fragments:    {len(bundle.source_fragments)}")
    print(f"Proposed Entities:      {len(bundle.candidate_entities)}")
    print(f"Proposed Relations:     {len(bundle.candidate_relations)}")
    print(f"Proposed Claims:        {len(bundle.candidate_claims)}")
    print(f"Proposed Questions:     {len(bundle.candidate_questions)}")
    if args.spool_dir:
        spool_path = args.spool_dir / f"candidate_bundle_{packet.uow_id}.json"
        print(f"Candidate Spooled At:   {spool_path}")

    if bundle.candidate_claims:
        print("\n--- Extracted Candidate Claims ---")
        for cl in bundle.candidate_claims:
            print(f"  [{cl.epistemic_status}] {cl.claim_id}: {cl.subject_id} --({cl.predicate})--> {cl.object_val}")

    if bundle.source_fragments:
        print("\n--- Ground-Truth Evidence Fragments ---")
        for fr in bundle.source_fragments:
            print(f"  [{fr.fragment_id}] ({fr.locator}): \"{fr.text}\"")

    print("\n--- G1 Geometric Self-Observation Telemetry ---")
    print(f"Reorientation Speed:    {geom.speed_max_angle:.4f} rad")
    print(f"Residual Novelty:       {geom.residual_norm:.4f}")
    print(f"Spectral Gap gamma_2:   {geom.spectral_gap:.4f}")
    print(f"Davis-Kahan Ratio D_k:  {geom.davis_kahan_ratio:.4f}")
    print(f"Identifiability:        {geom.identifiability}")
    print(f"Interpretation:         {geom.interpretation}")
    print(f"Recommended Action:     {geom.recommended_action}")
    print(f"Shadow Mode Active:     {geom.shadow_mode}")
    print("\n--- Resource Guard Telemetry ---")
    print(f"RAM Available:          {packet.ram_available_mb:.1f} MB")
    print(f"Worker RSS:             {packet.worker_rss_mb:.1f} MB")
    print(f"Thermal Max:            {packet.thermal_max_c:.1f} °C")
    print(f"Backpressure Flag:      {packet.backpressure_flag}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
