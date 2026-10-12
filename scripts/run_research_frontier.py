"""SOVCTX Autonomous Research Frontier Driver.

Executes an autonomous cycle of the redesigned research frontier:
1. Loads the 9 Thread Families (T1 through T9).
2. Budgets attention according to 50% Spines / 30% Bridges / 20% Anomalies.
3. Scores frontier questions with P = N + B + E + I + G - D.
4. Evaluates evidence-driven branching (T10+).
5. Monitors saturation Delta new relations -> 0.
6. Outputs discovery-oriented autonomous report to evidence/.
"""

import json
from pathlib import Path
from sovctx.node.research_question import (
    AutonomousBranchingEngine,
    BranchingTrigger,
    InstitutionalChannelType,
    PriorityComponents,
    ResearchQuestion,
    ThreadSaturationDetector,
)
from sovctx.node.research_frontier import (
    ResearchFrontierCoordinator,
)


def run_cycle() -> None:
    print("=" * 78)
    print("SOVCTX AUTONOMOUS RESEARCH FRONTIER: CYCLE EXECUTION")
    print("=" * 78)

    coord = ResearchFrontierCoordinator()
    print(f"[+] Loaded {len(coord.ledger.threads)} Thread Families (T1 through T9)")
    for tid, tf in coord.ledger.threads.items():
        print(f"    - [{tid}] {tf.name}")
        print(f"      Starting region: {tf.starting_region}")
        print(f"      Negative bound:  {tf.negative_presumptions[0]}")

    print("\n[+] Allocating Cycle Budget (50% Spines / 30% Bridges / 20% Anomalies)...")
    alloc = coord.allocate_cycle(total_slots=10)
    print(f"    - Spines quota (50%):    {alloc.spines_quota} slots -> {len(alloc.selected_spines)} assigned")
    print(f"    - Bridges quota (30%):   {alloc.bridges_quota} slots -> {len(alloc.selected_bridges)} assigned")
    print(f"    - Anomalies quota (20%): {alloc.anomalies_quota} slots -> {len(alloc.selected_anomalies)} assigned")

    print("\n[+] Priority-Ranked Frontier Questions for this Cycle:")
    for idx, q in enumerate(alloc.all_selected(), 1):
        print(f"    {idx}. [{q.question_id}] ({q.thread_id}) Priority P={q.priority:.4f}")
        print(f"       Relation under test: {q.relation_under_test}")
        print(f"       Question: {q.question_text}")
        print(f"       Target Channel: {q.target_channel.value}")
        print(f"       Endpoints: Known={q.known_endpoints} | Unknown={q.unknown_endpoint}")

    print("\n[+] Testing Autonomous Branching Engine...")
    spawned = coord.branching_engine.evaluate_branching(
        trigger=BranchingTrigger.NEW_RECURRING_RELATION,
        label="State Estimation",
        starting_region="Radar -> Navigation -> Meteorology",
        follow_targets=["OBSERVE", "FILTER", "ESTIMATE_STATE", "CORRECT"],
        rationale="Encountered OBSERVE -> FILTER -> ESTIMATE_STATE -> CORRECT recurring across radar, navigation, and meteorology.",
    )
    print(f"    [SPAWN] Successfully spawned new thread: {spawned.thread_id}")
    print(f"            Name: {spawned.name}")
    print(f"            Rationale: {spawned.spawn_rationale}")

    print("\n[+] Testing Saturation Detector on T3...")
    sat_state = ThreadSaturationDetector.evaluate_thread_saturation(
        thread_id="T3",
        recent_acquisitions=50,
        duplicate_relations=49,
        new_relations=1,
    )
    print(f"    - T3 Saturation status: {sat_state.is_saturated}")
    print(f"    - New relation ratio:  {sat_state.new_relation_ratio*100:.2f}%")
    print(f"    - Policy recommendation: {sat_state.recommendation}")

    print("\n[+] Generating Discovery-Oriented Autonomous Report...")
    report = coord.generate_discovery_report(
        new_relations=[
            {
                "relation": "STABILIZE -> CONTROL",
                "endpoints": "Lyapunov -> Krasovskii",
                "source": "Krasovskii (1959) 'Stability of Motion'",
            }
        ],
        new_threads=[spawned.to_dict()],
        saturated_threads=[sat_state.to_dict()],
    )

    out_dir = Path("/home/uow/sovctx-kg/evidence")
    out_dir.mkdir(parents=True, exist_ok=True)
    report_json_path = out_dir / "sovctx_research_frontier_report.json"
    report_md_path = out_dir / "sovctx_research_frontier_report.md"

    report_json_path.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    report_md_path.write_text(report.to_markdown(), encoding="utf-8")

    print(f"    [+] Saved report to {report_json_path}")
    print(f"    [+] Saved markdown to {report_md_path}")
    print("\n" + report.to_markdown())


if __name__ == "__main__":
    run_cycle()
