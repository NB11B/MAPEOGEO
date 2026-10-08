# SPDX-License-Identifier: MIT
"""Compact 4,225-Parameter PSMSL MLP Scorer for PDI-v0.7B.

Architecture:
    Input: 32 dense PSMSL work-relation features
    Layer 1: Linear(32, 64) + ReLU    [32*64 + 64 = 2,112 params]
    Layer 2: Linear(64, 32) + ReLU    [64*32 + 32 = 2,080 params]
    Layer 3: Linear(32, 1)            [32*1 + 1   =    33 params]
    Total Parameters: EXACTLY 4,225 parameters.

Features:
- Deterministic feature normalization derived strictly from training partitions.
- Permutation-equivariant candidate scoring (score(cand) is strictly independent of menu slot).
- Stable tie-breaking via candidate identity hash.
- Supports FP32, FP16, and simulated INT8 quantization.
- Pure PyTorch and standalone NumPy forward pass for microcontrollers / soft-core RTL.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn


class PSMSLCompactMLP(nn.Module):
    """Compact 4,225-parameter candidate work discriminator."""

    INPUT_DIM = 32
    HIDDEN_1 = 64
    HIDDEN_2 = 32
    OUTPUT_DIM = 1
    TOTAL_PARAMS = (32 * 64 + 64) + (64 * 32 + 32) + (32 * 1 + 1)  # 4,225

    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(self.INPUT_DIM, self.HIDDEN_1)
        self.relu1 = nn.ReLU()
        self.fc2 = nn.Linear(self.HIDDEN_1, self.HIDDEN_2)
        self.relu2 = nn.ReLU()
        self.fc3 = nn.Linear(self.HIDDEN_2, self.OUTPUT_DIM)

        # Registered buffers for deterministic normalization
        self.register_buffer("norm_mean", torch.zeros(self.INPUT_DIM))
        self.register_buffer("norm_std", torch.ones(self.INPUT_DIM))

        assert self.count_parameters() == 4225, f"Expected 4225 params, got {self.count_parameters()}"

    def count_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters())

    def set_normalization(self, mean: np.ndarray, std: np.ndarray):
        """Sets normalization parameters strictly derived from training split."""
        std_safe = np.where(std < 1e-6, 1.0, std)
        self.norm_mean.copy_(torch.from_numpy(mean.astype(np.float32)))
        self.norm_std.copy_(torch.from_numpy(std_safe.astype(np.float32)))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Normalize
        x_norm = (x - self.norm_mean) / self.norm_std
        h1 = self.relu1(self.fc1(x_norm))
        h2 = self.relu2(self.fc2(h1))
        out = self.fc3(h2)
        return out.squeeze(-1)

    def score_candidates_batch(
        self,
        features: List[List[float]],
        cand_ids: List[str],
    ) -> List[Tuple[float, str]]:
        """Scores candidate vectors with permutation equivariance and deterministic tiebreaking."""
        self.eval()
        with torch.no_grad():
            x = torch.tensor(features, dtype=torch.float32, device=self.fc1.weight.device)
            scores = self.forward(x).cpu().numpy().tolist()

        return list(zip(scores, cand_ids))

    def select_best_candidate(
        self,
        features: List[List[float]],
        cand_ids: List[str],
        actions: List[str],
    ) -> Tuple[int, str, str, float]:
        """Selects top candidate with deterministic identity tie-breaking.
        
        Returns: (index, cand_id, action_line, score)
        """
        scored = self.score_candidates_batch(features, cand_ids)
        # Sort by: (-score, cand_id) to ensure strict permutation equivariance and stable tiebreak
        ranked = sorted(
            [(s, cid, idx) for idx, (s, cid) in enumerate(scored)],
            key=lambda item: (-item[0], item[1])
        )
        best_score, best_cid, best_idx = ranked[0]
        return best_idx, best_cid, actions[best_idx], best_score

    # -------------------------------------------------------------------------
    # Standalone NumPy / INT8 Quantized Forward Execution (Embedded Simulation)
    # -------------------------------------------------------------------------
    def export_weights_dict(self) -> Dict[str, Any]:
        """Exports weights and normalization as serializable Python dictionary."""
        return {
            "metadata": {
                "architecture": "PSMSLCompactMLP",
                "total_parameters": self.count_parameters(),
                "layers": [
                    {"name": "fc1", "in": 32, "out": 64},
                    {"name": "fc2", "in": 64, "out": 32},
                    {"name": "fc3", "in": 32, "out": 1},
                ],
            },
            "norm_mean": self.norm_mean.cpu().numpy().tolist(),
            "norm_std": self.norm_std.cpu().numpy().tolist(),
            "weights": {
                "w1": self.fc1.weight.detach().cpu().numpy().tolist(),
                "b1": self.fc1.bias.detach().cpu().numpy().tolist(),
                "w2": self.fc2.weight.detach().cpu().numpy().tolist(),
                "b2": self.fc2.bias.detach().cpu().numpy().tolist(),
                "w3": self.fc3.weight.detach().cpu().numpy().tolist(),
                "b3": self.fc3.bias.detach().cpu().numpy().tolist(),
            },
        }

    def numpy_forward(self, x: np.ndarray, quantize_int8: bool = False) -> np.ndarray:
        """Standalone NumPy inference engine requiring ZERO PyTorch dependencies."""
        mean = self.norm_mean.cpu().numpy()
        std = self.norm_std.cpu().numpy()

        w1 = self.fc1.weight.detach().cpu().numpy()
        b1 = self.fc1.bias.detach().cpu().numpy()
        w2 = self.fc2.weight.detach().cpu().numpy()
        b2 = self.fc2.bias.detach().cpu().numpy()
        w3 = self.fc3.weight.detach().cpu().numpy()
        b3 = self.fc3.bias.detach().cpu().numpy()

        if quantize_int8:
            # Simulate INT8 symmetric quantization: Q(w) = round(w / scale)
            def quant_matrix(m: np.ndarray) -> np.ndarray:
                scale = np.max(np.abs(m)) / 127.0 if np.max(np.abs(m)) > 0 else 1.0
                q = np.clip(np.round(m / scale), -128, 127)
                return q * scale

            w1 = quant_matrix(w1)
            w2 = quant_matrix(w2)
            w3 = quant_matrix(w3)

        x_norm = (x - mean) / std
        h1 = np.maximum(0, np.dot(x_norm, w1.T) + b1)
        h2 = np.maximum(0, np.dot(h1, w2.T) + b2)
        out = np.dot(h2, w3.T) + b3
        return out.squeeze(-1)
