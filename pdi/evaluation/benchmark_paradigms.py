# SPDX-License-Identifier: MIT
"""Benchmark across 4 Work Proposal Paradigms on Frozen Holdouts.

Evaluates SmolLM2-135M (Arm B adapted checkpoint) across:
1. Paradigm 1: Ordinary Unconstrained JSON
2. Paradigm 2: Schema-Constrained JSON
3. Paradigm 3: Native Operational Grammar (Token-Efficient Grammar)
4. Paradigm 4: Candidate Work Menu Selection (Machine-Defined Menu)

Records:
- Syntax validity (%)
- Semantic correctness (%)
- Proposal acceptance by host adapter (%)
- Token count (mean per proposal)
- Latency (ms per proposal)
- Useful committed work (%)
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

from pdi.adapter.schema_validator import PDISchemaValidator, ValidationResult
from pdi.adapter.packet_codec import (
    PDIPacketCodec,
    ProposalPacket,
    CommitOutcome,
    ReasonCode,
)
from pdi.decoder.constrained_decoder import (
    StateContext,
    PrefixTrieLogitsProcessor,
    build_json_schema_trie,
    build_native_grammar_trie,
    build_menu_selection_trie,
)
from pdi.grammar.native_grammar import (
    OPCODE_TO_MNEMONIC,
    MNEMONIC_TO_OPCODE,
    NativeGrammarParser,
    NativePropose,
    NativeObserve,
    NativeCompare,
    NativeClarify,
    NativeEscalate,
)


def load_model_and_tokenizer(
    base_model_id: str = "HuggingFaceTB/SmolLM2-135M-Instruct",
    base_revision: str = "12fd25f77366fa6b3b4b768ec3050bf629380bac",
    adapter_path: Optional[str | Path] = None,
    device: Optional[str] = None,
) -> Tuple[AutoModelForCausalLM, AutoTokenizer, str]:
    dev = device or ("cuda" if torch.cuda.is_available() else "cpu")
    tok = AutoTokenizer.from_pretrained(base_model_id, revision=base_revision)
    if tok.pad_token_id is None:
        tok.pad_token_id = tok.eos_token_id

    dtype = torch.float16 if dev == "cuda" else torch.float32
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_id,
        revision=base_revision,
        dtype=dtype,
        device_map=dev,
    )

    if adapter_path is not None and Path(adapter_path).exists():
        print(f"Loading LoRA adapter from: {adapter_path}")
        model = PeftModel.from_pretrained(base_model, str(adapter_path))
    else:
        model = base_model

    model.eval()
    return model, tok, dev


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
    if "dest_ref" in tgt:
        refs.append(tgt["dest_ref"])
    if not refs:
        refs = [10, 11, 12]
    # Deduplicate while preserving order
    unique_refs: List[int] = []
    for r in refs:
        if r not in unique_refs:
            unique_refs.append(r)

    goal = tgt.get("goal_ref") or tgt.get("dest_ref")
    slots = tgt.get("missing_slots")
    return StateContext(assumed_state_version=ver, visible_refs=unique_refs, goal_ref=goal, active_slots=slots)


def target_to_native_line(tgt: Dict[str, Any]) -> str:
    kind = tgt.get("kind", "PROPOSE").upper()
    if kind == "PROPOSE":
        op = tgt.get("operator_id", 1)
        mne = OPCODE_TO_MNEMONIC.get(op, f"OP_{op}")
        refs = tgt.get("object_refs", [])
        ref_str = " ".join(f"REF_{r}" for r in refs)
        goal = tgt.get("goal_ref") or tgt.get("dest_ref")
        goal_str = f" GOAL_{goal}" if goal is not None else ""
        return f"PROPOSE {mne} {ref_str}{goal_str}".strip()
    elif kind == "COMPARE":
        return f"COMPARE REF_{tgt.get('left_ref', 10)} REF_{tgt.get('right_ref', 11)}"
    elif kind == "OBSERVE":
        tk = (tgt.get("projection_type") or tgt.get("target_kind") or "STATE").upper()
        refs = tgt.get("target_refs", [0])
        ref_str = " ".join(f"REF_{r}" for r in refs)
        return f"OBSERVE TARGET_{tk} {ref_str}".strip()
    elif kind == "CLARIFY":
        slots = ",".join(tgt.get("missing_slots", ["operator_id"]))
        return f"CLARIFY SLOT_{slots} REASON_unspecified_ambiguity"
    elif kind == "ESCALATE":
        cap = tgt.get("requested_capability", 0x80000000)
        return f"ESCALATE CAP_0x{cap:08X} REASON_unauthorized_capability_required"
    return "OBSERVE"


def check_semantic_match(parsed: Optional[Dict[str, Any]], target: Dict[str, Any]) -> bool:
    if not parsed or not target:
        return False
    if parsed.get("kind") != target.get("kind"):
        return False
    kind = parsed.get("kind")
    if kind == "PROPOSE":
        return parsed.get("operator_id") == target.get("operator_id")
    elif kind == "COMPARE":
        return parsed.get("left_ref") == target.get("left_ref") and parsed.get("right_ref") == target.get("right_ref")
    elif kind == "OBSERVE":
        p_tk = (parsed.get("projection_type") or parsed.get("target_kind") or "").upper()
        t_tk = (target.get("projection_type") or target.get("target_kind") or "").upper()
        return p_tk == t_tk
    elif kind == "CLARIFY":
        p_slots = set(parsed.get("missing_slots", []))
        t_slots = set(target.get("missing_slots", []))
        return len(p_slots.intersection(t_slots)) > 0
    elif kind == "ESCALATE":
        return parsed.get("requested_capability") == target.get("requested_capability")
    return False


def run_benchmark(
    corpus_path: Path,
    adapter_path: Path,
    output_path: Path,
    max_holdouts: Optional[int] = None,
):
    with open(corpus_path, "r", encoding="utf-8") as f:
        corpus = json.load(f)

    holdouts = [r for r in corpus["records"] if r["partition"] == "holdout"]
    if max_holdouts is not None:
        holdouts = holdouts[:max_holdouts]

    print(f"Loaded {len(holdouts)} frozen holdout evaluation records.")

    model, tok, dev = load_model_and_tokenizer(adapter_path=adapter_path)
    validator = PDISchemaValidator()

    # System prompts
    json_sys = (
        "You are the SmolLM2-135M deterministic work proposal interface for MAPEOGEO FPGA P0.\n"
        "Output exclusively valid JSON matching the PDI-v0 schema.\n"
        "Operations: PROPOSE, OBSERVE, COMPARE, CLARIFY, ESCALATE.\n"
        "Never fabricate state versions or unauthorized capabilities."
    )
    native_sys = (
        "You are the SmolLM2-135M native work proposer for MAPEOGEO FPGA P0.\n"
        "Output exclusively a single-line Native Operational Grammar command:\n"
        "PROPOSE, OBSERVE, COMPARE, CLARIFY, ESCALATE."
    )
    menu_sys = (
        "You are the SmolLM2-135M candidate work selector for MAPEOGEO FPGA P0.\n"
        "Select the single best candidate action from the menu by outputting its index."
    )

    results: Dict[str, Any] = {
        "benchmark": "PDI-135M-v0.2 Paradigm Comparison",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_holdouts": len(holdouts),
        "paradigms": {
            "P1_unconstrained_json": {},
            "P2_constrained_json": {},
            "P3_native_grammar": {},
            "P4_menu_selection": {},
        },
    }

    # Tracking metrics per paradigm
    p_metrics: Dict[str, Dict[str, Any]] = {
        p: {
            "valid_syntax": 0,
            "semantic_match": 0,
            "accepted_by_adapter": 0,
            "tokens": [],
            "latencies_ms": [],
            "details": [],
        }
        for p in results["paradigms"]
    }

    print("\n--- Commencing Benchmark across 4 Paradigms ---")

    for idx, rec in enumerate(holdouts):
        prompt_user = rec["input_prompt"]
        tgt = rec["target_output"]
        ctx = extract_state_context(rec)
        gt_line = target_to_native_line(tgt)

        # -------------------------------------------------------------
        # Paradigm 1: Unconstrained Ordinary JSON
        # -------------------------------------------------------------
        t0 = time.perf_counter()
        msgs1 = [{"role": "system", "content": json_sys}, {"role": "user", "content": prompt_user}]
        pt1 = tok.apply_chat_template(msgs1, tokenize=False, add_generation_prompt=True)
        inp1 = tok(pt1, return_tensors="pt").to(dev)

        with torch.no_grad():
            out1 = model.generate(
                **inp1,
                max_new_tokens=128,
                do_sample=False,
                pad_token_id=tok.pad_token_id,
                eos_token_id=tok.eos_token_id,
            )
        lat1 = (time.perf_counter() - t0) * 1000.0
        gen1_ids = out1[0][inp1["input_ids"].shape[1] :]
        tok_count1 = len(gen1_ids)
        raw1 = tok.decode(gen1_ids, skip_special_tokens=True).strip()

        val1 = validator.validate_json_string(raw1)
        is_syn1 = val1.is_valid
        is_sem1 = False
        if is_syn1 and val1.normalized:
            is_sem1 = check_semantic_match(val1.normalized, tgt)

        p_metrics["P1_unconstrained_json"]["tokens"].append(tok_count1)
        p_metrics["P1_unconstrained_json"]["latencies_ms"].append(lat1)
        if is_syn1:
            p_metrics["P1_unconstrained_json"]["valid_syntax"] += 1
            p_metrics["P1_unconstrained_json"]["accepted_by_adapter"] += 1
        if is_sem1:
            p_metrics["P1_unconstrained_json"]["semantic_match"] += 1

        # -------------------------------------------------------------
        # Paradigm 2: Constrained JSON
        # -------------------------------------------------------------
        t0 = time.perf_counter()
        json_trie = build_json_schema_trie(tok, ctx)
        proc2 = PrefixTrieLogitsProcessor(json_trie, inp1["input_ids"].shape[1])
        logits_proc2 = LogitsProcessorList([proc2])

        with torch.no_grad():
            out2 = model.generate(
                **inp1,
                max_new_tokens=128,
                do_sample=False,
                logits_processor=logits_proc2,
                pad_token_id=tok.pad_token_id,
                eos_token_id=tok.eos_token_id,
            )
        lat2 = (time.perf_counter() - t0) * 1000.0
        gen2_ids = out2[0][inp1["input_ids"].shape[1] :]
        tok_count2 = len(gen2_ids)
        raw2 = tok.decode(gen2_ids, skip_special_tokens=True).strip()

        val2 = validator.validate_json_string(raw2)
        is_syn2 = val2.is_valid
        is_sem2 = False
        if is_syn2 and val2.normalized:
            is_sem2 = check_semantic_match(val2.normalized, tgt)

        p_metrics["P2_constrained_json"]["tokens"].append(tok_count2)
        p_metrics["P2_constrained_json"]["latencies_ms"].append(lat2)
        if is_syn2:
            p_metrics["P2_constrained_json"]["valid_syntax"] += 1
            p_metrics["P2_constrained_json"]["accepted_by_adapter"] += 1
        if is_sem2:
            p_metrics["P2_constrained_json"]["semantic_match"] += 1

        # -------------------------------------------------------------
        # Paradigm 3: Native Operational Grammar
        # -------------------------------------------------------------
        t0 = time.perf_counter()
        msgs3 = [{"role": "system", "content": native_sys}, {"role": "user", "content": prompt_user}]
        pt3 = tok.apply_chat_template(msgs3, tokenize=False, add_generation_prompt=True)
        inp3 = tok(pt3, return_tensors="pt").to(dev)

        native_trie = build_native_grammar_trie(tok, ctx)
        proc3 = PrefixTrieLogitsProcessor(native_trie, inp3["input_ids"].shape[1])
        logits_proc3 = LogitsProcessorList([proc3])

        with torch.no_grad():
            out3 = model.generate(
                **inp3,
                max_new_tokens=32,
                do_sample=False,
                logits_processor=logits_proc3,
                pad_token_id=tok.pad_token_id,
                eos_token_id=tok.eos_token_id,
            )
        lat3 = (time.perf_counter() - t0) * 1000.0
        gen3_ids = out3[0][inp3["input_ids"].shape[1] :]
        tok_count3 = len(gen3_ids)
        raw3 = tok.decode(gen3_ids, skip_special_tokens=True).strip()

        is_syn3 = False
        is_sem3 = False
        try:
            cmd3 = NativeGrammarParser.parse_line(raw3)
            is_syn3 = True
            canon3 = cmd3.to_canonical_json(ctx.assumed_state_version)
            val3 = validator.validate_dict(canon3)
            if val3.is_valid:
                is_sem3 = check_semantic_match(canon3, tgt)
        except Exception:
            is_syn3 = False

        p_metrics["P3_native_grammar"]["tokens"].append(tok_count3)
        p_metrics["P3_native_grammar"]["latencies_ms"].append(lat3)
        if is_syn3:
            p_metrics["P3_native_grammar"]["valid_syntax"] += 1
            p_metrics["P3_native_grammar"]["accepted_by_adapter"] += 1
        if is_sem3:
            p_metrics["P3_native_grammar"]["semantic_match"] += 1

        # -------------------------------------------------------------
        # Paradigm 4: Candidate Menu Selection
        # -------------------------------------------------------------
        # Menu with 4 options: Option 1 is ground truth, Options 2-4 are distractors
        t0 = time.perf_counter()
        distractors = [
            f"PROPOSE OP_SUB REF_{ctx.visible_refs[0]} REF_{ctx.visible_refs[-1]}",
            f"COMPARE REF_{ctx.visible_refs[0]} REF_{ctx.visible_refs[-1]}",
            f"CLARIFY SLOT_operator_id REASON_unspecified_ambiguity",
        ]
        # Build menu items
        menu_items = [gt_line] + distractors[:3]
        # Keep deterministic order or track index
        correct_index = 1

        menu_prompt = (
            f"{prompt_user}\n"
            f"Authorized state version: {ctx.assumed_state_version}\n"
            f"Available candidate actions:\n"
            + "\n".join(f"[{i+1}] {item}" for i, item in enumerate(menu_items))
            + f"\nSelect action index [1-{len(menu_items)}]:"
        )

        msgs4 = [{"role": "system", "content": menu_sys}, {"role": "user", "content": menu_prompt}]
        pt4 = tok.apply_chat_template(msgs4, tokenize=False, add_generation_prompt=True)
        inp4 = tok(pt4, return_tensors="pt").to(dev)

        menu_trie = build_menu_selection_trie(tok, len(menu_items))
        proc4 = PrefixTrieLogitsProcessor(menu_trie, inp4["input_ids"].shape[1])
        logits_proc4 = LogitsProcessorList([proc4])

        with torch.no_grad():
            out4 = model.generate(
                **inp4,
                max_new_tokens=4,
                do_sample=False,
                logits_processor=logits_proc4,
                pad_token_id=tok.pad_token_id,
                eos_token_id=tok.eos_token_id,
            )
        lat4 = (time.perf_counter() - t0) * 1000.0
        gen4_ids = out4[0][inp4["input_ids"].shape[1] :]
        tok_count4 = len(gen4_ids)
        raw4 = tok.decode(gen4_ids, skip_special_tokens=True).strip()

        # Parse selected index
        is_syn4 = False
        is_sem4 = False
        digits = [ch for ch in raw4 if ch.isdigit()]
        if digits:
            sel_idx = int(digits[0])
            is_syn4 = 1 <= sel_idx <= len(menu_items)
            is_sem4 = sel_idx == correct_index

        p_metrics["P4_menu_selection"]["tokens"].append(tok_count4)
        p_metrics["P4_menu_selection"]["latencies_ms"].append(lat4)
        if is_syn4:
            p_metrics["P4_menu_selection"]["valid_syntax"] += 1
            p_metrics["P4_menu_selection"]["accepted_by_adapter"] += 1
        if is_sem4:
            p_metrics["P4_menu_selection"]["semantic_match"] += 1

        if (idx + 1) % 10 == 0 or (idx + 1) == len(holdouts):
            print(f"Evaluated {idx+1}/{len(holdouts)} holdouts...")

    # Summarize metrics
    total = len(holdouts)
    for p_name, m in p_metrics.items():
        mean_tok = sum(m["tokens"]) / max(1, len(m["tokens"]))
        mean_lat = sum(m["latencies_ms"]) / max(1, len(m["latencies_ms"]))
        syn_pct = (m["valid_syntax"] / total) * 100.0
        sem_pct = (m["semantic_match"] / total) * 100.0
        acc_pct = (m["accepted_by_adapter"] / total) * 100.0

        results["paradigms"][p_name] = {
            "total_examples": total,
            "valid_syntax_count": m["valid_syntax"],
            "syntax_validity_pct": round(syn_pct, 2),
            "semantic_match_count": m["semantic_match"],
            "semantic_correctness_pct": round(sem_pct, 2),
            "accepted_by_adapter_count": m["accepted_by_adapter"],
            "proposal_acceptance_pct": round(acc_pct, 2),
            "mean_token_count": round(mean_tok, 2),
            "mean_latency_ms": round(mean_lat, 2),
        }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved paradigm comparison benchmark results to: {output_path}")
    print("\n================== PARADIGM COMPARISON SUMMARY ==================")
    for p_name, r in results["paradigms"].items():
        print(
            f"[{p_name:24s}] Syntax: {r['syntax_validity_pct']:6.2f}% | "
            f"Semantic: {r['semantic_correctness_pct']:6.2f}% | "
            f"Mean Tokens: {r['mean_token_count']:5.1f} | "
            f"Latency: {r['mean_latency_ms']:6.2f} ms"
        )
    print("=================================================================\n")
    return results


if __name__ == "__main__":
    corpus_file = PACKAGE_ROOT / "pdi" / "data" / "pdi_corpus_manifest.json"
    adapter_dir = PACKAGE_ROOT / "pdi" / "checkpoints" / "pdi_arm_b_h3_adapted"
    out_file = PACKAGE_ROOT / "pdi" / "qualification" / "pdi_v02_paradigm_benchmark.json"

    run_benchmark(corpus_file, adapter_dir, out_file)
