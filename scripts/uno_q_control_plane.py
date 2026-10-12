"""SOVCTX UNO Q Regulatory Control Plane Runner.

Acts as the authoritative control node governing the Jetson Nano work plane:
- Issues signed/bounded UoWs into the Issuance Ledger
- Retrieves and verifies CandidateBundles from worker spool
- Enforces the hard law: PROPOSED != AUTHORIZED (Nano proposes, UNO Q admits)
- Validates dual-tier hashes: H_E (evidence payload) and H_X (execution envelope)
- Handles concurrent out-of-order completions via issuance tracking (no high-water lockout)
- Detects independent replication (same H_E, different H_X) and duplicate candidates (DEDUP)
- Evaluates epistemic grounding (DOWNGRADE ungrounded strong claims to HYPOTHETICAL)
- Quarantines dangling canonical references
- Refuses unauthorized canonical mutations and scheduler overrides
- Respects worker backpressure signaling
"""

import argparse
import json
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sovctx.node.control_plane import (
    AdmissionDecision,
    AdmissionVerdict,
    UnoQControlPlaneGateway,
    UoWIssuanceLedger,
)
from sovctx.node.nano_research_worker import CandidateBundle, NanoResearchWorker


def run_feldbaum_sized_battery(
    gateway: UnoQControlPlaneGateway,
    worker: NanoResearchWorker,
    output_dir: Path,
) -> List[AdmissionDecision]:
    """Runs a 12-question experimental battery spanning Feldbaum, Tsetlin, Krasovskii, Stratonovich, Pontryagin.

    Demonstrates the full spectrum of regulatory dispositions:
    - ADMIT
    - QUARANTINE
    - DOWNGRADE
    - REJECT
    - REJECT_IDEMPOTENT
    - DEDUP (Replication)
    - UNRESOLVED
    """
    print("\n" + "=" * 80)
    print("EXECUTING FELDBAUM-SIZED EXPERIMENTAL RESEARCH BATTERY (12 UoWs)")
    print("Corpus: Feldbaum, Tsetlin, Krasovskii, Stratonovich, Pontryagin")
    print("=" * 80)

    decisions: List[AdmissionDecision] = []

    # Battery Question 1: Feldbaum dual control primary evidence -> Expected: ADMIT
    uow1 = "UOW_BATTERY_001_FELDBAUM_DIRECT"
    gateway.ledger.issue_uow(
        uow_id=uow1,
        worker_id=worker.worker_id,
        target_query="Find primary-source evidence bearing on whether Feldbaum's dual-control formulation explicitly distinguishes information-gathering action from directing action.",
    )
    pkt1 = worker.execute_primary_research_uow(
        uow_id=uow1,
        target_query="Find primary-source evidence bearing on whether Feldbaum's dual-control formulation explicitly distinguishes information-gathering action from directing action.",
    )
    dec1 = gateway.verify_bundle(pkt1.candidate_bundle)
    decisions.append(dec1)
    print(f"[{dec1.verdict.value:17s}] {uow1}: {dec1.reason[:75]}...")

    # Battery Question 2: Tsetlin finite automata learning in unknown media -> Expected: ADMIT
    uow2 = "UOW_BATTERY_002_TSETLIN_AUTOMATA"
    gateway.ledger.issue_uow(
        uow_id=uow2,
        worker_id=worker.worker_id,
        target_query="How do Tsetlin's finite automata learn in random unknown media through trial and error state transitions?",
    )
    pkt2 = worker.execute_primary_research_uow(
        uow_id=uow2,
        target_query="How do Tsetlin's finite automata learn in random unknown media through trial and error state transitions?",
    )
    dec2 = gateway.verify_bundle(pkt2.candidate_bundle)
    decisions.append(dec2)
    print(f"[{dec2.verdict.value:17s}] {uow2}: {dec2.reason[:75]}...")

    # Battery Question 3: Krasovskii optimal regulation & Lyapunov derivative -> Expected: ADMIT
    uow3 = "UOW_BATTERY_003_KRASOVSKII_LYAPUNOV"
    gateway.ledger.issue_uow(
        uow_id=uow3,
        worker_id=worker.worker_id,
        target_query="How does Krasovskii's 1959 optimal regulation minimize the total derivative of the Lyapunov function?",
    )
    pkt3 = worker.execute_primary_research_uow(
        uow_id=uow3,
        target_query="How does Krasovskii's 1959 optimal regulation minimize the total derivative of the Lyapunov function?",
    )
    dec3 = gateway.verify_bundle(pkt3.candidate_bundle)
    decisions.append(dec3)
    print(f"[{dec3.verdict.value:17s}] {uow3}: {dec3.reason[:75]}...")

    # Battery Question 4: Independent replication of Feldbaum evidence under new execution envelope -> Expected: DEDUP (Replication)
    uow4 = "UOW_BATTERY_004_FELDBAUM_REPLICATION"
    gateway.ledger.issue_uow(
        uow_id=uow4,
        worker_id=worker.worker_id,
        target_query="Replicate Feldbaum dual-control investigative vs directing action distinction.",
    )
    pkt4 = worker.execute_primary_research_uow(
        uow_id=uow4,
        target_query="Find primary-source evidence bearing on whether Feldbaum's dual-control formulation explicitly distinguishes information-gathering action from directing action.",
    )
    dec4 = gateway.verify_bundle(pkt4.candidate_bundle)
    decisions.append(dec4)
    print(f"[{dec4.verdict.value:17s}] {uow4}: {dec4.reason[:75]}...")

    # Battery Question 5: Replay of UoW 1 -> Expected: REJECT_IDEMPOTENT
    dec5 = gateway.verify_bundle(pkt1.candidate_bundle)
    decisions.append(dec5)
    print(f"[{dec5.verdict.value:17s}] {uow1} [REPLAY]: {dec5.reason[:75]}...")

    # Battery Question 6: Unissued UoW arrival -> Expected: REJECT
    uow6 = "UOW_BATTERY_006_UNISSUED_ARRIVAL"
    pkt6 = worker.execute_primary_research_uow(
        uow_id=uow6,
        target_query="Find Feldbaum dual control evidence without control plane issuance.",
    )
    dec6 = gateway.verify_bundle(pkt6.candidate_bundle)
    decisions.append(dec6)
    print(f"[{dec6.verdict.value:17s}] {uow6}: {dec6.reason[:75]}...")

    # Battery Question 7: Ungrounded claim (Epistemic overpromotion) -> Expected: DOWNGRADE
    uow7 = "UOW_BATTERY_007_EPISTEMIC_OVERPROMOTION"
    gateway.ledger.issue_uow(uow_id=uow7, worker_id=worker.worker_id, target_query="Ungrounded claim test")
    pkt7 = worker.execute_primary_research_uow(
        uow_id=uow7,
        target_query="Find primary-source evidence bearing on whether Feldbaum's dual-control formulation explicitly distinguishes information-gathering action from directing action.",
    )
    # Remove fragments to force overpromotion
    pkt7.candidate_bundle.source_fragments = []
    pkt7.candidate_bundle.compute_hash()
    dec7 = gateway.verify_bundle(pkt7.candidate_bundle)
    decisions.append(dec7)
    print(f"[{dec7.verdict.value:17s}] {uow7}: {dec7.reason[:75]}...")

    # Battery Question 8: Dangling reference to nonexistent node -> Expected: QUARANTINE
    uow8 = "UOW_BATTERY_008_DANGLING_NODE"
    gateway.ledger.issue_uow(uow_id=uow8, worker_id=worker.worker_id, target_query="Dangling reference test")
    pkt8 = worker.execute_primary_research_uow(
        uow_id=uow8,
        target_query="Find primary-source evidence bearing on whether Feldbaum's dual-control formulation explicitly distinguishes information-gathering action from directing action.",
    )
    from sovctx.node.nano_research_worker import CandidateRelation

    pkt8.candidate_bundle.candidate_relations.append(
        CandidateRelation(
            source_id="CONCEPT:NONEXISTENT_GHOST_ENTITY_999",
            target_id="CONCEPT:DUAL_CONTROL",
            verb="PROBES",
            rationale="Dangling link",
            evidence_fragment_ids=[],
        )
    )
    pkt8.candidate_bundle.compute_hash()
    dec8 = gateway.verify_bundle(pkt8.candidate_bundle)
    decisions.append(dec8)
    print(f"[{dec8.verdict.value:17s}] {uow8}: {dec8.reason[:75]}...")

    # Battery Question 9: Tampered evidence payload (H_E mismatch) -> Expected: REJECT
    uow9 = "UOW_BATTERY_009_PAYLOAD_TAMPER"
    gateway.ledger.issue_uow(uow_id=uow9, worker_id=worker.worker_id, target_query="Payload tamper test")
    pkt9 = worker.execute_primary_research_uow(
        uow_id=uow9,
        target_query="Find primary-source evidence bearing on whether Feldbaum's dual-control formulation explicitly distinguishes information-gathering action from directing action.",
    )
    pkt9.candidate_bundle.candidate_claims[0].object_val = "ALTERED_WITHOUT_HASH_UPDATE"
    dec9 = gateway.verify_bundle(pkt9.candidate_bundle)
    decisions.append(dec9)
    print(f"[{dec9.verdict.value:17s}] {uow9}: {dec9.reason[:75]}...")

    # Battery Question 10: Open Stratonovich inquiry without primary fragments -> Expected: UNRESOLVED
    uow10 = "UOW_BATTERY_010_STRATONOVICH_OPEN"
    gateway.ledger.issue_uow(
        uow_id=uow10,
        worker_id=worker.worker_id,
        target_query="How did Stratonovich's 1960 conditional Markov processes relate to Kalman-Bucy filtering?",
    )
    pkt10 = worker.execute_primary_research_uow(
        uow_id=uow10,
        target_query="How did Stratonovich's 1960 conditional Markov processes relate to Kalman-Bucy filtering?",
    )
    dec10 = gateway.verify_bundle(pkt10.candidate_bundle)
    decisions.append(dec10)
    print(f"[{dec10.verdict.value:17s}] {uow10}: {dec10.reason[:75]}...")

    # Battery Question 11: Superseded parent state -> Expected: REJECT
    uow11_parent = "UOW_BATTERY_011_PARENT_STATE"
    uow11_child = "UOW_BATTERY_011_CHILD_RESULT"
    gateway.ledger.issue_uow(uow_id=uow11_parent, worker_id=worker.worker_id, target_query="Parent question")
    gateway.ledger.issue_uow(
        uow_id=uow11_child,
        worker_id=worker.worker_id,
        parent_uow_id=uow11_parent,
        target_query="Child question",
    )
    # Supersede parent before child arrives
    gateway.ledger.supersede_uow(uow11_parent, reason="Evidence updated in canonical store")
    pkt11 = worker.execute_primary_research_uow(
        uow_id=uow11_child,
        parent_uow_id=uow11_parent,
        target_query="Find primary-source evidence bearing on whether Feldbaum's dual-control formulation explicitly distinguishes information-gathering action from directing action.",
    )
    dec11 = gateway.verify_bundle(pkt11.candidate_bundle)
    decisions.append(dec11)
    print(f"[{dec11.verdict.value:17s}] {uow11_child}: {dec11.reason[:75]}...")

    # Battery Question 12: Unauthorized schedule override attempt -> Expected: REFUSE
    uow12 = "UOW_BATTERY_012_SCHEDULE_OVERRIDE"
    gateway.ledger.issue_uow(uow_id=uow12, worker_id=worker.worker_id, target_query="Authority attack")
    pkt12 = worker.execute_primary_research_uow(
        uow_id=uow12,
        target_query="Find primary-source evidence bearing on whether Feldbaum's dual-control formulation explicitly distinguishes information-gathering action from directing action.",
    )
    pkt12.candidate_bundle.observer_state["mutate_schedule_direct"] = True
    pkt12.candidate_bundle.compute_hash()
    dec12 = gateway.verify_bundle(pkt12.candidate_bundle)
    decisions.append(dec12)
    print(f"[{dec12.verdict.value:17s}] {uow12}: {dec12.reason[:75]}...")

    return decisions


def main() -> int:
    parser = argparse.ArgumentParser(description="SOVCTX UNO Q Regulatory Control Plane Runner")
    parser.add_argument("--spool-dir", type=Path, default=Path("evidence/n5/spool"), help="Worker spool directory")
    parser.add_argument("--output-dir", type=Path, default=Path("evidence/n5"), help="Output directory")
    parser.add_argument("--run-battery", action="store_true", help="Run 12-question research battery")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    log_file = args.output_dir / "control_plane_admission_log.jsonl"
    ledger_file = args.output_dir / "uno_q_issuance_ledger.json"

    ledger = UoWIssuanceLedger(ledger_file=ledger_file)
    gateway = UnoQControlPlaneGateway(
        ledger=ledger,
        log_file=log_file,
    )

    print("=" * 80)
    print("SOVCTX UNO Q REGULATORY CONTROL PLANE GATEWAY")
    print("Role: Authoritative Control Node | Invariant: PROPOSED != AUTHORIZED")
    print(f"Issuance Ledger: {ledger_file}")
    print(f"Admission Log:   {log_file}")
    print("=" * 80)

    if args.run_battery:
        worker = NanoResearchWorker(
            worker_id="nano-jetson-01",
            shadow_mode=True,
            output_telemetry_dir=args.output_dir,
            spool_dir=args.spool_dir,
        )
        decisions = run_feldbaum_sized_battery(gateway, worker, args.output_dir)
        verdict_counts = {}
        for d in decisions:
            v = d.verdict.value
            verdict_counts[v] = verdict_counts.get(v, 0) + 1

        print("\n" + "=" * 80)
        print("RESEARCH BATTERY ADMISSION SUMMARY")
        print("=" * 80)
        for v, cnt in sorted(verdict_counts.items()):
            print(f"  {v:20s}: {cnt}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
