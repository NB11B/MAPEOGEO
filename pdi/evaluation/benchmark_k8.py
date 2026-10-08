# SPDX-License-Identifier: MIT
"""Comprehensive K=8 Menu Selector Benchmark for PDI-135M-v0.3.

Evaluates five selector strategies:
1. Uniform Random Selector
2. First-Eligible Selector
3. Deterministic Heuristic Selector
4. Frozen SmolLM2-135M Selector (with Arm B adapter)
5. Oracle Selector (Upper bound)

Across:
- 49 frozen holdout scenarios
- 3 fixed permutation seeds: [42, 137, 2026]
- 5 context arms: [E0, E1, E2, E3, E4]

Outputs:
- pdi/qualification/pdi_v03_k8_benchmark.json
- pdi/qualification/pdi_v03_coverage_analysis.json
- pdi/qualification/pdi_v03_projection_ablation.json
- pdi/qualification/pdi_v03_latency_report.json
"""

from __future__ import annotations

import json
from pathlib import Path
import random
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, LogitsProcessorList

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from pdi.candidates.candidate_generator import (
    CandidateMenu,
    CandidateSlot,
    DeterministicCandidateGenerator,
    PermutedMenu,
)
from pdi.candidates.candidate_oracle import (
    CandidateJudgement,
    CandidateOracle,
    OracleMenuEvaluation,
)
from pdi.decoder.constrained_decoder import (
    PrefixTrieLogitsProcessor,
    StateContext,
    build_menu_selection_trie,
)
from pdi.evaluation.latency_profiler import LatencyProfiler
from pdi.evaluation.selection_metrics import (
    SelectionMetricsAggregator,
    TrialResult,
)
from pdi.projection.state_projection import ContextArm, StateProjector


SEEDS = [42, 137, 2026]
CONTEXT_ARMS = [
    ContextArm.E0_MINIMAL,
    ContextArm.E1_BOUNDED_SLOTS,
    ContextArm.E2_PSMSL_SYMBOLIC,
    ContextArm.E3_MEMORY_SNAPSHOT,
    ContextArm.E4_GRAPH_CAUSAL,
]


def extract_state_context(rec: Dict[str, Any]) -> StateContext:
    tgt = rec["target_output"]
    ver = int(tgt.get("assumed_state_version", 1000))
    refs: List[int] = []
    if "object_refs" in tgt:
        refs.extend(tgt["object_refs"])
    if "target_refs" in tgt:
        refs.extend(tgt["target_refs"])
    if "left_ref" in tgt:
        refs.append(tgt["left_ref"])
    if "right_ref" in tgt:
        refs.append(tgt["right_ref"])
    goal = tgt.get("dest_ref") or tgt.get("goal_ref")
    cap = 0x00000001
    return StateContext(
        assumed_state_version=ver,
        authorized_capability_mask=cap,
        visible_refs=tuple(refs),
        goal_ref=goal,
    )


# ---------------------------------------------------------------------------
# Selectors
# ---------------------------------------------------------------------------

class UniformRandomSelector:
    @staticmethod
    def select(menu: PermutedMenu, seed: int) -> int:
        rng = random.Random(seed + 999)
        return rng.randint(1, len(menu.display_slots))


class FirstEligibleSelector:
    @staticmethod
    def select(menu: PermutedMenu) -> int:
        for idx, slot in enumerate(menu.display_slots, start=1):
            if slot.is_admissible and not slot.is_abstain:
                return idx
        return len(menu.display_slots)


class DeterministicHeuristicSelector:
    @staticmethod
    def select(menu: PermutedMenu, input_prompt: str) -> int:
        prompt_lower = input_prompt.lower()
        best_idx = 8
        best_score = -1.0

        for idx, slot in enumerate(menu.display_slots, start=1):
            if not slot.is_admissible:
                continue
            if slot.is_abstain:
                if 0.5 > best_score:
                    best_score = 0.5
                    best_idx = idx
                continue

            score = 0.0
            act = slot.action_line.lower()

            # Operator matching
            keywords = [
                ("add", "op_add"), ("sub", "op_sub"), ("mul", "op_mul"),
                ("product", "op_cl20_product"), ("reverse", "op_reverse"),
                ("involution", "op_grade_involution"), ("conjugate", "op_clifford_conjugate"),
                ("dot", "op_vector_dot"), ("wedge", "op_vector_wedge"),
                ("commutator", "op_commutator"), ("projection", "projection"),
                ("norm", "op_norm"), ("matrix", "matrix"),
                ("compare", "compare"), ("observe", "observe"),
                ("clarify", "clarify"), ("escalate", "escalate"),
            ]
            for kw, mne_substr in keywords:
                if kw in prompt_lower and mne_substr in act:
                    score += 5.0

            # Operand matching
            for r in slot.object_refs:
                if str(r) in input_prompt:
                    score += 2.0
            if slot.goal_ref is not None and str(slot.goal_ref) in input_prompt:
                score += 2.0

            if score > best_score:
                best_score = score
                best_idx = idx

        return best_idx


class OracleSelector:
    @staticmethod
    def select(oracle_eval: OracleMenuEvaluation) -> int:
        if oracle_eval.optimal_display_index is not None:
            return oracle_eval.optimal_display_index
        # Return display index of abstention slot
        for s in oracle_eval.slot_judgements:
            if "ABSTAIN" in s.action_line and s.display_index is not None:
                return s.display_index
        return 8


class FrozenSmolLM2Selector:
    def __init__(
        self,
        base_model_id: str = "HuggingFaceTB/SmolLM2-135M-Instruct",
        base_revision: str = "12fd25f77366fa6b3b4b768ec3050bf629380bac",
        adapter_path: Optional[Path] = None,
        device: Optional[str] = None,
    ) -> None:
        self.dev = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.tok = AutoTokenizer.from_pretrained(base_model_id, revision=base_revision)
        if self.tok.pad_token_id is None:
            self.tok.pad_token_id = self.tok.eos_token_id

        dtype = torch.float16 if self.dev == "cuda" else torch.float32
        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_id,
            revision=base_revision,
            dtype=dtype,
            device_map=self.dev,
        )
        if adapter_path is not None and adapter_path.exists():
            print(f"Loading frozen SmolLM2 adapter from {adapter_path}")
            self.model = PeftModel.from_pretrained(base_model, str(adapter_path))
        else:
            self.model = base_model

        self.model.eval()

    def select(
        self,
        context_text: str,
        menu: PermutedMenu,
    ) -> Tuple[int, int, int]:
        """Greedy-selection of candidate index [1-8].

        Returns (selected_index, prompt_tokens, generated_tokens).
        """
        system_prompt = (
            "You are an assistant selecting the optimal work proposal for an FPGA execution pipeline. "
            "Given the current state and task objective, select the single best candidate action index from the menu below (1 to 8). "
            "Output ONLY the single digit of your choice."
        )
        user_prompt = (
            f"{context_text}\n\n"
            f"Candidate actions:\n"
            f"{menu.format_prompt_menu()}\n\n"
            f"Select action index [1-8]:"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        prompt_str = self.tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tok(prompt_str, return_tensors="pt").to(self.dev)
        prompt_tokens = inputs["input_ids"].shape[1]

        # Use constrained trie logits processor to enforce single digit 1..8
        menu_trie = build_menu_selection_trie(self.tok, len(menu.display_slots))
        proc = PrefixTrieLogitsProcessor(menu_trie, prompt_tokens)
        logits_proc = LogitsProcessorList([proc])

        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=4,
                do_sample=False,
                logits_processor=logits_proc,
                pad_token_id=self.tok.pad_token_id,
                eos_token_id=self.tok.eos_token_id,
            )

        gen_ids = output_ids[0][prompt_tokens:]
        gen_tokens = len(gen_ids)
        raw_text = self.tok.decode(gen_ids, skip_special_tokens=True).strip()

        # Parse first digit
        digits = [ch for ch in raw_text if ch.isdigit()]
        if digits:
            idx = int(digits[0])
            if 1 <= idx <= len(menu.display_slots):
                return idx, prompt_tokens, gen_tokens

        return -1, prompt_tokens, gen_tokens


# ---------------------------------------------------------------------------
# Benchmark Runner
# ---------------------------------------------------------------------------

def run_k8_benchmark(
    corpus_manifest_path: Path,
    adapter_path: Path,
    output_dir: Path,
) -> Dict[str, Any]:
    print("=" * 70)
    print("PDI-135M-v0.3: Starting K=8 Candidate Work Menu Selector Benchmark")
    print("=" * 70)

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(corpus_manifest_path, "r", encoding="utf-8") as f:
        corpus = json.load(f)

    holdouts = [r for r in corpus["records"] if r.get("partition") == "holdout"]
    print(f"Loaded {len(holdouts)} frozen holdout scenarios.")

    generator = DeterministicCandidateGenerator()
    profiler = LatencyProfiler()
    aggregator = SelectionMetricsAggregator()

    # Load frozen SmolLM2-135M selector
    print("Initializing Frozen SmolLM2-135M Selector on GPU/CPU...")
    model_selector = FrozenSmolLM2Selector(adapter_path=adapter_path)

    # Pre-generate candidate menus (isolated from oracle labels)
    # Menu is constructed only once per scenario; permuted per seed
    scenarios_data = []
    coverage_records = []

    print("\n[Phase 1] Generating deterministic 8-slot candidate menus...")
    for rec in holdouts:
        scen_id = rec["example_id"]
        prompt = rec["input_prompt"]
        tgt = rec["target_output"]
        ctx = extract_state_context(rec)

        profiler.start("candidate_gen")
        menu = generator.generate_menu(scen_id, ctx, prompt)
        gen_lat = profiler.stop("candidate_gen")

        # Evaluate Oracle Coverage@8 on frozen menu
        oracle_eval = CandidateOracle.evaluate_menu(menu, tgt)
        coverage_records.append({
            "scenario_id": scen_id,
            "family": rec.get("family", "unknown"),
            "menu_hash": menu.menu_hash,
            "coverage_at_8": oracle_eval.coverage_at_8,
            "optimal_cand_id": oracle_eval.optimal_cand_id,
            "slots": [
                {
                    "cand_id": s.cand_id,
                    "action": s.action_line,
                    "is_abstain": s.is_abstain,
                }
                for s in menu.slots
            ],
        })

        scenarios_data.append({
            "rec": rec,
            "ctx": ctx,
            "menu": menu,
            "gen_latency": gen_lat,
        })

    # Coverage summary
    cov_count = sum(1 for c in coverage_records if c["coverage_at_8"])
    cov_pct = (cov_count / len(coverage_records)) * 100.0
    print(f"Oracle Coverage@8: {cov_count}/{len(coverage_records)} ({cov_pct:.2f}%)")

    # Benchmark across Seeds x Arms x Selectors
    print("\n[Phase 2 & 3] Benchmarking Selectors across Seeds and Context Arms...")
    total_evals = len(scenarios_data) * len(SEEDS) * len(CONTEXT_ARMS)
    print(f"Total scenario permutations per selector: {len(scenarios_data) * len(SEEDS)}")
    print(f"Total model evaluations (SmolLM2): {total_evals}")

    eval_count = 0
    t_start = time.perf_counter()

    for arm in CONTEXT_ARMS:
        print(f"\n--- Context Arm: {arm.value} ---")
        for s_data in scenarios_data:
            rec = s_data["rec"]
            ctx = s_data["ctx"]
            menu: CandidateMenu = s_data["menu"]
            gen_lat = s_data["gen_latency"]
            scen_id = rec["example_id"]
            family = rec.get("family", "unknown")
            tgt = rec["target_output"]

            # Project state under current arm
            profiler.start("projection")
            proj = StateProjector.project(arm, rec["input_prompt"], ctx)
            proj_lat = profiler.stop("projection")

            for seed in SEEDS:
                # Permute menu under fixed seed
                permuted = menu.permute(seed)
                # Oracle evaluation of permuted view
                oracle_eval = CandidateOracle.evaluate_menu(permuted, tgt)

                # 1. Oracle Selector
                t0 = time.perf_counter()
                oracle_idx = OracleSelector.select(oracle_eval)
                oracle_sel_lat = (time.perf_counter() - t0) * 1000.0
                _record_trial(
                    aggregator=aggregator,
                    scen_id=scen_id,
                    seed=seed,
                    arm=arm.value,
                    selector_name="oracle",
                    family=family,
                    sel_idx=oracle_idx,
                    permuted=permuted,
                    oracle_eval=oracle_eval,
                    gen_lat=gen_lat,
                    proj_lat=proj_lat,
                    sel_lat=oracle_sel_lat,
                    prompt_toks=proj.token_estimate,
                    gen_toks=1,
                )

                # 2. Uniform Random Selector
                t0 = time.perf_counter()
                rand_idx = UniformRandomSelector.select(permuted, seed)
                rand_sel_lat = (time.perf_counter() - t0) * 1000.0
                _record_trial(
                    aggregator=aggregator,
                    scen_id=scen_id,
                    seed=seed,
                    arm=arm.value,
                    selector_name="uniform_random",
                    family=family,
                    sel_idx=rand_idx,
                    permuted=permuted,
                    oracle_eval=oracle_eval,
                    gen_lat=gen_lat,
                    proj_lat=proj_lat,
                    sel_lat=rand_sel_lat,
                    prompt_toks=proj.token_estimate,
                    gen_toks=1,
                )

                # 3. First-Eligible Selector
                t0 = time.perf_counter()
                first_idx = FirstEligibleSelector.select(permuted)
                first_sel_lat = (time.perf_counter() - t0) * 1000.0
                _record_trial(
                    aggregator=aggregator,
                    scen_id=scen_id,
                    seed=seed,
                    arm=arm.value,
                    selector_name="first_eligible",
                    family=family,
                    sel_idx=first_idx,
                    permuted=permuted,
                    oracle_eval=oracle_eval,
                    gen_lat=gen_lat,
                    proj_lat=proj_lat,
                    sel_lat=first_sel_lat,
                    prompt_toks=proj.token_estimate,
                    gen_toks=1,
                )

                # 4. Deterministic Heuristic Selector
                t0 = time.perf_counter()
                heur_idx = DeterministicHeuristicSelector.select(permuted, rec["input_prompt"])
                heur_sel_lat = (time.perf_counter() - t0) * 1000.0
                _record_trial(
                    aggregator=aggregator,
                    scen_id=scen_id,
                    seed=seed,
                    arm=arm.value,
                    selector_name="deterministic_heuristic",
                    family=family,
                    sel_idx=heur_idx,
                    permuted=permuted,
                    oracle_eval=oracle_eval,
                    gen_lat=gen_lat,
                    proj_lat=proj_lat,
                    sel_lat=heur_sel_lat,
                    prompt_toks=proj.token_estimate,
                    gen_toks=1,
                )

                # 5. Frozen SmolLM2-135M Selector
                t0 = time.perf_counter()
                m_idx, p_toks, g_toks = model_selector.select(proj.context_text, permuted)
                model_sel_lat = (time.perf_counter() - t0) * 1000.0
                _record_trial(
                    aggregator=aggregator,
                    scen_id=scen_id,
                    seed=seed,
                    arm=arm.value,
                    selector_name="frozen_smollm2",
                    family=family,
                    sel_idx=m_idx,
                    permuted=permuted,
                    oracle_eval=oracle_eval,
                    gen_lat=gen_lat,
                    proj_lat=proj_lat,
                    sel_lat=model_sel_lat,
                    prompt_toks=p_toks,
                    gen_toks=g_toks,
                )

                eval_count += 1
                if eval_count % 50 == 0 or eval_count == total_evals:
                    elapsed = time.perf_counter() - t_start
                    print(f"Evaluated {eval_count}/{total_evals} permutations (Elapsed: {elapsed:.1f}s)...")

    # -----------------------------------------------------------------------
    # Generate Output Reports
    # -----------------------------------------------------------------------
    selectors = [
        "oracle",
        "uniform_random",
        "first_eligible",
        "deterministic_heuristic",
        "frozen_smollm2",
    ]

    benchmark_summary: Dict[str, Any] = {
        "metadata": {
            "experiment": "PDI-135M-v0.3",
            "date": "2026-10-08",
            "holdout_count": len(holdouts),
            "seeds": SEEDS,
            "context_arms": [a.value for a in CONTEXT_ARMS],
            "selectors": selectors,
        },
        "coverage_at_8_pct": round(cov_pct, 2),
        "overall_by_selector": {},
    }

    for sel in selectors:
        benchmark_summary["overall_by_selector"][sel] = aggregator.summarize(filter_selector=sel)

    # 1. Main Benchmark Report
    bench_file = output_dir / "pdi_v03_k8_benchmark.json"
    with open(bench_file, "w", encoding="utf-8") as f:
        json.dump(benchmark_summary, f, indent=2)

    # 2. Coverage Analysis Report
    cov_file = output_dir / "pdi_v03_coverage_analysis.json"
    cov_by_fam: Dict[str, Dict[str, Any]] = {}
    for cr in coverage_records:
        fam = cr["family"]
        if fam not in cov_by_fam:
            cov_by_fam[fam] = {"total": 0, "covered": 0}
        cov_by_fam[fam]["total"] += 1
        if cr["coverage_at_8"]:
            cov_by_fam[fam]["covered"] += 1

    cov_summary = {
        "overall_coverage_pct": round(cov_pct, 2),
        "total_scenarios": len(holdouts),
        "covered_scenarios": cov_count,
        "by_family": {
            k: {
                "total": v["total"],
                "covered": v["covered"],
                "coverage_pct": round((v["covered"] / v["total"]) * 100.0, 2),
            }
            for k, v in cov_by_fam.items()
        },
        "scenarios": coverage_records,
    }
    with open(cov_file, "w", encoding="utf-8") as f:
        json.dump(cov_summary, f, indent=2)

    # 3. Projection Arm Ablation Report (focus on SmolLM2 performance across E0-E4)
    ablation_summary: Dict[str, Any] = {
        "model_selector": "frozen_smollm2_135m",
        "arms": {},
    }
    for arm in CONTEXT_ARMS:
        arm_val = arm.value
        arm_stats = aggregator.summarize(filter_selector="frozen_smollm2", filter_arm=arm_val)
        ablation_summary["arms"][arm_val] = {
            "coverage_at_8_pct": arm_stats["coverage_at_8_pct"],
            "conditional_top1_pct": arm_stats["conditional_top1_pct"],
            "end_to_end_useful_pct": arm_stats["end_to_end_useful_pct"],
            "order_sensitivity_pct": arm_stats["order_sensitivity_pct"],
            "order_consistency_pct": arm_stats["order_consistency_pct"],
            "mean_prompt_tokens": arm_stats["tokens"]["mean_prompt"],
            "latency_p50_ms": arm_stats["latencies_ms"]["selection"]["p50"],
            "latency_p95_ms": arm_stats["latencies_ms"]["selection"]["p95"],
            "end_to_end_p50_ms": arm_stats["latencies_ms"]["end_to_end"]["p50"],
        }
    ablation_file = output_dir / "pdi_v03_projection_ablation.json"
    with open(ablation_file, "w", encoding="utf-8") as f:
        json.dump(ablation_summary, f, indent=2)

    # 4. Latency Profiling Report
    latency_summary: Dict[str, Any] = {
        "candidate_generation": aggregator.summarize(filter_selector="frozen_smollm2")["latencies_ms"]["candidate_gen"],
        "projection": aggregator.summarize(filter_selector="frozen_smollm2")["latencies_ms"]["projection"],
        "inference_by_arm": {
            arm.value: aggregator.summarize(filter_selector="frozen_smollm2", filter_arm=arm.value)["latencies_ms"]["selection"]
            for arm in CONTEXT_ARMS
        },
        "end_to_end_by_arm": {
            arm.value: aggregator.summarize(filter_selector="frozen_smollm2", filter_arm=arm.value)["latencies_ms"]["end_to_end"]
            for arm in CONTEXT_ARMS
        },
    }
    lat_file = output_dir / "pdi_v03_latency_report.json"
    with open(lat_file, "w", encoding="utf-8") as f:
        json.dump(latency_summary, f, indent=2)

    print("\n" + "=" * 70)
    print("K=8 MENU SELECTOR BENCHMARK COMPLETED")
    print("=" * 70)
    for sel, stats in benchmark_summary["overall_by_selector"].items():
        print(
            f"[{sel:24s}] Top-1: {stats['conditional_top1_pct']:6.2f}% | "
            f"Useful: {stats['end_to_end_useful_pct']:6.2f}% | "
            f"Consistency: {stats['order_consistency_pct']:6.2f}% | "
            f"Sel Lat p50: {stats['latencies_ms']['selection']['p50']:6.2f}ms"
        )
    print("=" * 70)
    print(f"Generated artifacts in {output_dir}:")
    print(f"  - {bench_file.name}")
    print(f"  - {cov_file.name}")
    print(f"  - {ablation_file.name}")
    print(f"  - {lat_file.name}\n")

    return benchmark_summary


def _record_trial(
    aggregator: SelectionMetricsAggregator,
    scen_id: str,
    seed: int,
    arm: str,
    selector_name: str,
    family: str,
    sel_idx: int,
    permuted: PermutedMenu,
    oracle_eval: OracleMenuEvaluation,
    gen_lat: float,
    proj_lat: float,
    sel_lat: float,
    prompt_toks: int,
    gen_toks: int,
) -> None:
    is_valid_idx = (1 <= sel_idx <= len(permuted.display_slots))
    selected_cand_id: Optional[str] = None
    is_eligible = False
    is_abstain = False
    is_cond_top1 = False
    is_acceptable = False
    is_correct_abs = False
    is_useful = False

    if is_valid_idx:
        slot = permuted.display_slots[sel_idx - 1]
        selected_cand_id = slot.cand_id
        is_eligible = slot.is_admissible
        is_abstain = slot.is_abstain

        # Find judgement for this slot in oracle_eval
        for sj in oracle_eval.slot_judgements:
            if sj.display_index == sel_idx:
                if sj.judgement == CandidateJudgement.OPTIMAL_MATCH:
                    is_cond_top1 = True
                    is_useful = True
                elif sj.judgement == CandidateJudgement.ACCEPTABLE_ALTERNATIVE:
                    is_acceptable = True
                elif sj.judgement == CandidateJudgement.CORRECT_ABSTENTION:
                    is_correct_abs = True
                    is_useful = True
                break

    e2e_lat = gen_lat + proj_lat + sel_lat

    trial = TrialResult(
        scenario_id=scen_id,
        seed=seed,
        context_arm=arm,
        selector_name=selector_name,
        op_family=family,
        selected_index=sel_idx,
        selected_cand_id=selected_cand_id,
        is_valid_index=is_valid_idx,
        is_eligible=is_eligible,
        coverage_at_8=oracle_eval.coverage_at_8,
        is_conditional_top1=is_cond_top1,
        is_acceptable_alternative=is_acceptable,
        is_abstain=is_abstain,
        is_correct_abstention=is_correct_abs,
        is_useful_selection=is_useful,
        candidate_gen_latency_ms=gen_lat,
        projection_latency_ms=proj_lat,
        selection_latency_ms=sel_lat,
        end_to_end_latency_ms=e2e_lat,
        prompt_tokens=prompt_toks,
        generated_tokens=gen_toks,
    )
    aggregator.record(trial)


if __name__ == "__main__":
    c_path = PACKAGE_ROOT / "pdi" / "data" / "pdi_corpus_manifest.json"
    a_path = PACKAGE_ROOT / "pdi" / "checkpoints" / "pdi_arm_b_h3_adapted"
    out_dir = PACKAGE_ROOT / "pdi" / "qualification"
    run_k8_benchmark(c_path, a_path, out_dir)
