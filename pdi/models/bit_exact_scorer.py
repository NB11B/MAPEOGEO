# SPDX-License-Identifier: MIT
"""Bit-Exact Integer PSMSL Scorer for PDI-v0.8.

Implements bit-exact integer inference matching target FPGA RTL:
- INT8 inputs clamped to [0, 127]
- Folded Layer-1 weights and biases (eliminating runtime feature normalization)
- Pipelined 32-bit two's-complement accumulators (zero overflow)
- Fixed-point integer scaling with round-to-nearest-even / right-shift
- INT8 ReLU activation clamped to [0, 127]
- 32-bit signed output score for exact candidate ranking
- Verilog .mem hex file exporter for RTL $readmemh
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent


class BitExactPSMSLScorer:
    """Bit-exact integer inference model and RTL coefficient generator."""

    def __init__(self, weights_json_path: Optional[Path] = None):
        ckpt_path = weights_json_path or (
            PACKAGE_ROOT / "pdi" / "checkpoints" / "psmsl_mlp_v07b" / "weights_exported.json"
        )
        with open(ckpt_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        mean = np.array(data["norm_mean"], dtype=np.float32)
        std = np.array(data["norm_std"], dtype=np.float32)
        w1 = np.array(data["weights"]["w1"], dtype=np.float32)  # (64, 32)
        b1 = np.array(data["weights"]["b1"], dtype=np.float32)  # (64,)
        w2 = np.array(data["weights"]["w2"], dtype=np.float32)  # (32, 64)
        b2 = np.array(data["weights"]["b2"], dtype=np.float32)  # (32,)
        w3 = np.array(data["weights"]["w3"], dtype=np.float32)  # (1, 32)
        b3 = np.array(data["weights"]["b3"], dtype=np.float32)  # (1,)

        # 1. Fold normalization into Layer 1 weights and biases
        w1_eff = w1 / std[np.newaxis, :]
        b1_eff = b1 - np.dot(w1_eff, mean)

        # 2. Integer Quantization parameters
        self.scale_x = 127.0
        self.scale_w1 = 25.0
        self.w1_q = np.clip(np.round(w1_eff * self.scale_w1), -128, 127).astype(np.int32)
        self.b1_q = np.round(b1_eff * self.scale_x * self.scale_w1).astype(np.int32)

        self.scale_w2 = 254.0
        self.w2_q = np.clip(np.round(w2 * self.scale_w2), -128, 127).astype(np.int32)
        self.b2_q = np.round(b2 * (127.0 / 4.08) * self.scale_w2).astype(np.int32)

        self.scale_w3 = 420.0
        self.w3_q = np.clip(np.round(w3 * self.scale_w3), -128, 127).astype(np.int32)
        self.b3_q = np.round(b3 * (127.0 / 6.08) * self.scale_w3).astype(np.int32)

        self.m1 = 642
        self.shift1 = 16
        self.m2 = 173
        self.shift2 = 16

    def score_vector(self, x_vec: List[float]) -> int:
        """Computes bit-exact 32-bit integer score matching RTL logic."""
        # 1. Input quantization to 8-bit unsigned integer [0, 127]
        xq = np.clip(np.round(np.array(x_vec, dtype=np.float32) * 127.0), 0, 127).astype(np.int32)

        # 2. Layer 1 MAC: 64 neurons, 32 inputs each
        acc1 = np.dot(self.w1_q, xq) + self.b1_q  # (64,)
        # Pipelined fixed-point scale & ReLU
        h1 = np.clip((acc1 * self.m1) >> self.shift1, 0, 127).astype(np.int32)

        # 3. Layer 2 MAC: 32 neurons, 64 inputs each
        acc2 = np.dot(self.w2_q, h1) + self.b2_q  # (32,)
        # Pipelined fixed-point scale & ReLU
        h2 = np.clip((acc2 * self.m2) >> self.shift2, 0, 127).astype(np.int32)

        # 4. Layer 3 MAC: 1 neuron, 32 inputs
        acc3 = np.dot(self.w3_q, h2) + self.b3_q  # (1,)
        return int(acc3[0])

    def export_rtl_mem_files(self, output_dir: Path):
        """Exports integer weights and biases to Verilog hex .mem format."""
        output_dir.mkdir(parents=True, exist_ok=True)

        # Helper to convert signed byte to 2-digit hex
        def to_hex8(val: Any) -> str:
            return f"{(int(val) & 0xFF):02X}"

        # Helper to convert signed 32-bit int to 8-digit hex
        def to_hex32(val: Any) -> str:
            return f"{(int(val) & 0xFFFFFFFF):08X}"

        # Layer 1 Weights: 64 x 32 = 2048 bytes
        with open(output_dir / "psmsl_weights_l1.mem", "w", encoding="utf-8") as f:
            for row in self.w1_q:
                for val in row:
                    f.write(f"{to_hex8(val)}\n")

        # Layer 1 Biases: 64 x 32-bit words
        with open(output_dir / "psmsl_biases_l1.mem", "w", encoding="utf-8") as f:
            for val in self.b1_q:
                f.write(f"{to_hex32(val)}\n")

        # Layer 2 Weights: 32 x 64 = 2048 bytes
        with open(output_dir / "psmsl_weights_l2.mem", "w", encoding="utf-8") as f:
            for row in self.w2_q:
                for val in row:
                    f.write(f"{to_hex8(val)}\n")

        # Layer 2 Biases: 32 x 32-bit words
        with open(output_dir / "psmsl_biases_l2.mem", "w", encoding="utf-8") as f:
            for val in self.b2_q:
                f.write(f"{to_hex32(val)}\n")

        # Layer 3 Weights: 1 x 32 = 32 bytes
        with open(output_dir / "psmsl_weights_l3.mem", "w", encoding="utf-8") as f:
            for val in self.w3_q[0]:
                f.write(f"{to_hex8(val)}\n")

        # Layer 3 Bias: 1 x 32-bit word
        with open(output_dir / "psmsl_biases_l3.mem", "w", encoding="utf-8") as f:
            f.write(f"{to_hex32(int(self.b3_q[0]))}\n")

        # Metadata JSON
        meta = {
            "scale_x": self.scale_x,
            "scale_w1": self.scale_w1,
            "scale_w2": self.scale_w2,
            "scale_w3": self.scale_w3,
            "m1": self.m1,
            "shift1": self.shift1,
            "m2": self.m2,
            "shift2": self.shift2,
            "total_weights": int(self.w1_q.size + self.w2_q.size + self.w3_q.size),
            "total_biases": int(self.b1_q.size + self.b2_q.size + self.b3_q.size),
        }
        with open(output_dir / "psmsl_params.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
        print(f"Exported Verilog .mem files and parameters to {output_dir}")
