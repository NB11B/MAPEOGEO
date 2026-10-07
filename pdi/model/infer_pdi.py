# SPDX-License-Identifier: MIT
"""Inference script for SmolLM2-135M under PDI grammar."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Dict, Optional, Tuple

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from pdi.adapter.schema_validator import PDISchemaValidator, ValidationResult


class PDIInferenceEngine:
    def __init__(
        self,
        base_model_id: str = "HuggingFaceTB/SmolLM2-135M-Instruct",
        base_revision: str = "12fd25f77366fa6b3b4b768ec3050bf629380bac",
        adapter_path: Optional[str | Path] = None,
        device: Optional[str] = None,
    ):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(base_model_id, revision=base_revision)
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

        dtype = torch.float16 if self.device == "cuda" else torch.float32
        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_id,
            revision=base_revision,
            dtype=dtype,
            device_map=self.device,
        )

        if adapter_path is not None:
            print(f"Loading adapter weights from: {adapter_path}")
            self.model = PeftModel.from_pretrained(base_model, str(adapter_path))
        else:
            self.model = base_model

        self.model.eval()
        self.validator = PDISchemaValidator()

    def generate_proposal(self, prompt: str, max_new_tokens: int = 128) -> Tuple[str, ValidationResult]:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are the SmolLM2-135M deterministic work proposal interface for MAPEOGEO FPGA P0.\n"
                    "Output exclusively valid JSON matching the PDI-v0 schema.\n"
                    "Operations: PROPOSE, OBSERVE, COMPARE, CLARIFY, ESCALATE.\n"
                    "Never fabricate state versions or unauthorized capabilities."
                ),
            },
            {"role": "user", "content": prompt},
        ]
        prompt_text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        inputs = self.tokenizer(prompt_text, return_tensors="pt").to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                temperature=0.0,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )

        gen_tokens = outputs[0][inputs["input_ids"].shape[1] :]
        raw_output = self.tokenizer.decode(gen_tokens, skip_special_tokens=True).strip()
        val_res = self.validator.validate_json_string(raw_output)
        return raw_output, val_res
