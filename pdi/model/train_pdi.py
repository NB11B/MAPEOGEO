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
