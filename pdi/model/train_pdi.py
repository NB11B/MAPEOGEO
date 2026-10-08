# SPDX-License-Identifier: MIT
"""PDI-135M Supervised LoRA Fine-Tuning Script.

Trains two active experimental arms and evaluates against the frozen H3 baseline:
- Arm A: Frozen H3 Baseline (unmodified)
- Arm B: H3 + PDI Adaptation (initialized from H3 adapter)
- Arm C: SmolLM2 Base + PDI Adaptation (initialized from scratch LoRA)
"""

from __future__ import annotations

import gc
import json
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import torch
from peft import LoraConfig, PeftModel, get_peft_model
from torch.optim import AdamW
from transformers import AutoModelForCausalLM, AutoTokenizer
import yaml

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from pdi.model.prepare_corpus import PDICorpusGenerator, build_and_save_pdi_manifest
from pdi.model.evaluate_pdi import evaluate_arm


CONFIG_PATH = PACKAGE_ROOT / "pdi" / "model" / "training_config.yaml"
MANIFEST_PATH = PACKAGE_ROOT / "pdi" / "data" / "pdi_corpus_manifest.json"
CHECKPOINTS_DIR = PACKAGE_ROOT / "pdi" / "checkpoints"


def prepare_training_tensors(
    train_records: list[dict[str, Any]],
    tokenizer: Any,
) -> Tuple[list[torch.Tensor], list[torch.Tensor]]:
    input_ids_list: list[torch.Tensor] = []
    labels_list: list[torch.Tensor] = []

    system_msg = (
        "You are the SmolLM2-135M deterministic work proposal interface for MAPEOGEO FPGA P0.\n"
        "Output exclusively valid JSON matching the PDI-v0 schema.\n"
        "Operations: PROPOSE, OBSERVE, COMPARE, CLARIFY, ESCALATE.\n"
        "Never fabricate state versions or unauthorized capabilities."
    )

    for rec in train_records:
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": rec["input_prompt"]},
        ]
        prompt_text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        target_json = json.dumps(rec["target_output"], indent=2)
        full_text = prompt_text + target_json + tokenizer.eos_token

        enc_prompt = tokenizer(prompt_text, add_special_tokens=False)["input_ids"]
        enc_full = tokenizer(full_text, add_special_tokens=False)["input_ids"]

        # Completion-only loss masking: prompt tokens set to -100
        labels = [-100] * len(enc_prompt) + enc_full[len(enc_prompt) :]

        input_ids_list.append(torch.tensor(enc_full, dtype=torch.long))
        labels_list.append(torch.tensor(labels, dtype=torch.long))

    return input_ids_list, labels_list


def train_single_arm(
    arm_id: str,
    arm_name: str,
    base_model_id: str,
    base_revision: str,
    cfg: dict[str, Any],
    train_inputs: list[torch.Tensor],
    train_labels: list[torch.Tensor],
    output_dir: Path,
    device: str,
    starting_weights: str,
    init_adapter_path: Optional[str] = None,
) -> dict[str, Any]:
    print(f"\n{'='*70}")
    print(f"  TRAINING PDI ARM {arm_id}: {arm_name}")
    print(f"  Starting Weights: {starting_weights}")
    print(f"  Output Directory: {output_dir}")
    print(f"{'='*70}")

    output_dir.mkdir(parents=True, exist_ok=True)
    dtype = torch.float16 if device == "cuda" else torch.float32

    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_id,
        revision=base_revision,
        dtype=dtype,
        device_map=device,
    )

    lora_cfg = cfg["lora"]
    if starting_weights == "base_smollm2":
        peft_config = LoraConfig(
            r=lora_cfg["r"],
            lora_alpha=lora_cfg["lora_alpha"],
            target_modules=lora_cfg["target_modules"],
            lora_dropout=lora_cfg["lora_dropout"],
            bias=lora_cfg["bias"],
            task_type=lora_cfg["task_type"],
        )
        model = get_peft_model(base_model, peft_config)
    else:
        assert init_adapter_path is not None, "init_adapter_path required for transfer arm"
        print(f"Loading initial weights from prior adapter: {init_adapter_path}")
        model = PeftModel.from_pretrained(
            base_model,
            str(init_adapter_path),
            is_trainable=True,
        )

    trainable_params, all_params = model.get_nb_trainable_parameters()
    print(f"Trainable parameters: {trainable_params:,d} / {all_params:,d} ({100.0 * trainable_params / all_params:.4f}%)")

    train_cfg = cfg["training"]
    optimizer = AdamW(model.parameters(), lr=train_cfg["learning_rate"])
    model.train()

    epochs = train_cfg["epochs"]
    t0 = time.perf_counter()
    initial_loss = 0.0
    final_loss = 0.0
    epoch_losses = []

    for epoch in range(1, epochs + 1):
        running_loss = 0.0
        for step, (input_ids, labels) in enumerate(zip(train_inputs, train_labels)):
            optimizer.zero_grad()
            inp = input_ids.unsqueeze(0).to(device)
            lbl = labels.unsqueeze(0).to(device)

            outputs = model(input_ids=inp, labels=lbl)
            loss = outputs.loss
            loss.backward()
            optimizer.step()

            loss_val = loss.item()
            running_loss += loss_val
            if epoch == 1 and step == 0:
                initial_loss = loss_val

        avg_loss = running_loss / len(train_inputs)
        epoch_losses.append(round(avg_loss, 4))
        final_loss = avg_loss
        print(f"  Epoch {epoch}/{epochs} - Average Loss: {avg_loss:.4f}")

    wall_time = time.perf_counter() - t0
    reduction_pct = 100.0 * (1.0 - (final_loss / initial_loss)) if initial_loss > 0 else 0.0
    print(f"Training complete in {wall_time:.2f}s! Initial: {initial_loss:.4f} -> Final: {final_loss:.4f} ({reduction_pct:.2f}% reduction)")

    model.save_pretrained(str(output_dir))
    print(f"Saved adapted model weights to {output_dir}")

    arm_summary = {
        "arm_id": arm_id,
        "arm_name": arm_name,
        "starting_weights": starting_weights,
        "output_dir": str(output_dir),
        "trainable_parameters": trainable_params,
        "total_parameters": all_params,
        "initial_loss": round(initial_loss, 4),
        "final_loss": round(final_loss, 4),
        "loss_reduction_pct": round(reduction_pct, 2),
        "epoch_losses": epoch_losses,
        "wall_time_seconds": round(wall_time, 2),
    }

    del model
    del base_model
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return arm_summary


def run_training_campaign(device: Optional[str] = None) -> dict[str, Any]:
    dev = device or ("cuda" if torch.cuda.is_available() else "cpu")
    print(f"=== PDI-135M Training Campaign on {dev} ===")

    cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    train_recs = [r for r in manifest["records"] if r["partition"] == "train"]

    base_model_id = cfg["base_model"]
    base_revision = cfg["base_revision"]

    print(f"Loading tokenizer {base_model_id}...")
    tokenizer = AutoTokenizer.from_pretrained(base_model_id, revision=base_revision)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id

    print(f"Preparing {len(train_recs)} training sequences...")
    train_inputs, train_labels = prepare_training_tensors(train_recs, tokenizer)

    # 1. Arm A: Frozen H3 Baseline Evaluation
    h3_path = cfg["arms"]["A"]["checkpoint_path"]
    eval_a = evaluate_arm("Arm A: Frozen H3 Baseline", h3_path, MANIFEST_PATH, device=dev)

    # 2. Arm B: H3 + PDI LoRA Training & Evaluation
    arm_b_cfg = cfg["arms"]["B"]
    arm_b_dir = PACKAGE_ROOT / arm_b_cfg["output_dir"]
    train_b = train_single_arm(
        arm_id="B",
        arm_name=arm_b_cfg["name"],
        base_model_id=base_model_id,
        base_revision=base_revision,
        cfg=cfg,
        train_inputs=train_inputs,
        train_labels=train_labels,
        output_dir=arm_b_dir,
        device=dev,
        starting_weights=arm_b_cfg["starting_weights"],
        init_adapter_path=arm_b_cfg["checkpoint_path"],
    )
    eval_b = evaluate_arm("Arm B: H3 + PDI LoRA", arm_b_dir, MANIFEST_PATH, device=dev)

    # 3. Arm C: Original SmolLM2 + PDI LoRA Training & Evaluation
    arm_c_cfg = cfg["arms"]["C"]
    arm_c_dir = PACKAGE_ROOT / arm_c_cfg["output_dir"]
    train_c = train_single_arm(
        arm_id="C",
        arm_name=arm_c_cfg["name"],
        base_model_id=base_model_id,
        base_revision=base_revision,
        cfg=cfg,
        train_inputs=train_inputs,
        train_labels=train_labels,
        output_dir=arm_c_dir,
        device=dev,
        starting_weights=arm_c_cfg["starting_weights"],
    )
    eval_c = evaluate_arm("Arm C: Original SmolLM2 + PDI LoRA", arm_c_dir, MANIFEST_PATH, device=dev)

    comparison_results = {
        "program": "PDI-135M-v0.1",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "base_model": base_model_id,
        "base_revision": base_revision,
        "device": dev,
        "total_training_examples": len(train_recs),
        "total_holdout_examples": len(manifest["records"]) - len(train_recs),
        "arms": {
            "A_frozen_h3": {
                "train_summary": None,
                "evaluation": eval_a,
            },
            "B_h3_pdi_transfer": {
                "train_summary": train_b,
                "evaluation": eval_b,
            },
            "C_smollm2_fresh_pdi": {
                "train_summary": train_c,
                "evaluation": eval_c,
            },
        },
        "summary_table": {
            "arm_a_syntax_pct": eval_a["syntax_rate_pct"],
            "arm_a_semantic_pct": eval_a["semantic_rate_pct"],
            "arm_a_unsafe_pct": eval_a["unsafe_rate_pct"],
            "arm_b_syntax_pct": eval_b["syntax_rate_pct"],
            "arm_b_semantic_pct": eval_b["semantic_rate_pct"],
            "arm_b_unsafe_pct": eval_b["unsafe_rate_pct"],
            "arm_c_syntax_pct": eval_c["syntax_rate_pct"],
            "arm_c_semantic_pct": eval_c["semantic_rate_pct"],
            "arm_c_unsafe_pct": eval_c["unsafe_rate_pct"],
        },
    }

    out_json = PACKAGE_ROOT / "pdi" / "qualification" / "pdi_model_comparison.json"
    out_json.write_text(json.dumps(comparison_results, indent=2), encoding="utf-8")
    print(f"\nSaved PDI Model Comparison Results to: {out_json}")
    return comparison_results


if __name__ == "__main__":
    run_training_campaign()
