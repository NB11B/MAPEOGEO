# SPDX-License-Identifier: MIT
"""Trainer for Compact 4,225-Parameter PSMSL MLP Scorer in Track PDI-v0.7B.

Uses Pairwise Margin Ranking Loss:
    L = log(1 + exp(-(s(a+) - s(a-))))
trained strictly on training partitions with deterministic normalization.

Guarantees:
- Zero test holdout leakage: Holdouts (64 transfer scenarios and 15% v0.7A holdout) are strictly excluded.
- Feature normalization mean/std derived exclusively from training records.
"""

from __future__ import annotations

import json
from pathlib import Path
import random
import sys
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from pdi.candidates.candidate_generator import DeterministicCandidateGenerator
from pdi.candidates.observable_state import ObservableStateExtractor
from pdi.models.psmsl_mlp import PSMSLCompactMLP
from pdi.projection.dense_psmsl_encoder import DensePSMSLEncoder


def build_training_dataset():
    """Compiles candidate-level training pairs (pos_feature, neg_feature) from training partitions."""
    encoder = DensePSMSLEncoder()
    gen = DeterministicCandidateGenerator()

    # 1. Load v0.7A Composite Goals
    v07a_path = PACKAGE_ROOT / "pdi" / "data" / "pdi_v07a_composite_goals.json"
    with open(v07a_path, "r", encoding="utf-8") as f:
        v07a_recs = json.load(f)["records"]

    # 2. Load v0.5 Falsification Suite
    v05_path = PACKAGE_ROOT / "pdi" / "data" / "pdi_v05_prospective_falsification.json"
    with open(v05_path, "r", encoding="utf-8") as f:
        v05_recs = json.load(f)["records"]

    rng = random.Random(2026_07)
    # 70% train split for v07a, 15% val, 15% test
    shuffled_v07a = list(v07a_recs)
    rng.shuffle(shuffled_v07a)
    n_v07a_train = int(len(shuffled_v07a) * 0.70)
    v07a_train = shuffled_v07a[:n_v07a_train]
    v07a_val = shuffled_v07a[n_v07a_train:n_v07a_train + 19]
    v07a_test = shuffled_v07a[n_v07a_train + 19:]

    # 70% train split for v05
    shuffled_v05 = list(v05_recs)
    rng.shuffle(shuffled_v05)
    n_v05_train = int(len(shuffled_v05) * 0.70)
    v05_train = shuffled_v05[:n_v05_train]
    v05_val = shuffled_v05[n_v05_train:n_v05_train + 19]
    v05_test = shuffled_v05[n_v05_train + 19:]

    def extract_pairs(records_list, is_v07a: bool = False):
        pairs = []
        all_features = []
        for r in records_list:
            prompt = r["input_prompt"]
            ver = r.get("assumed_state_version", 1)
            ctx = ObservableStateExtractor.extract_from_prompt(prompt, default_version=ver)
            menu = gen.generate_menu(r["scenario_id"], ctx, prompt)

            can = r.get("first_step_canonical") if is_v07a else r.get("canonical_action")
            if not can or "REFUSE" in can:
                can = "ABSTAIN"

            pos_feat = None
            neg_feats = []

            for s in menu.slots:
                feat = encoder.encode_dense_vector(s.cand_id, s.action_line, ctx, prompt)
                all_features.append(feat)

                is_pos = (can.strip() in s.action_line.strip()) or (can == "ABSTAIN" and s.is_abstain)
                if is_pos and pos_feat is None:
                    pos_feat = feat
                else:
                    neg_feats.append(feat)

            if pos_feat is not None and neg_feats:
                for neg in neg_feats:
                    pairs.append((pos_feat, neg))

        return pairs, all_features

    train_pairs_v07a, feats_v07a = extract_pairs(v07a_train, is_v07a=True)
    train_pairs_v05, feats_v05 = extract_pairs(v05_train, is_v07a=False)
    train_pairs = train_pairs_v07a + train_pairs_v05
    train_feats = np.array(feats_v07a + feats_v05, dtype=np.float32)

    val_pairs_v07a, _ = extract_pairs(v07a_val, is_v07a=True)
    val_pairs_v05, _ = extract_pairs(v05_val, is_v07a=False)
    val_pairs = val_pairs_v07a + val_pairs_v05

    # Compute deterministic normalization mean and std EXCLUSIVELY on training features
    mean = np.mean(train_feats, axis=0)
    std = np.std(train_feats, axis=0)

    print(f"Compiled {len(train_pairs)} training pairs and {len(val_pairs)} validation pairs.")
    print(f"Feature normalization derived from {len(train_feats)} training vectors.")

    return train_pairs, val_pairs, mean, std, {
        "v07a_test_ids": [r["scenario_id"] for r in v07a_test],
        "v05_test_ids": [r["scenario_id"] for r in v05_test],
    }


def train_psmsl_mlp(epochs: int = 50, batch_size: int = 64, lr: float = 0.003):
    print("=== Training Compact 4,225-Parameter PSMSL MLP ===")
    train_pairs, val_pairs, mean, std, split_info = build_training_dataset()

    model = PSMSLCompactMLP()
    model.set_normalization(mean, std)

    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)

    # Softplus ranking loss: log(1 + exp(-(s+ - s-)))
    loss_fn = nn.Softplus()

    pos_train = torch.tensor([p[0] for p in train_pairs], dtype=torch.float32)
    neg_train = torch.tensor([p[1] for p in train_pairs], dtype=torch.float32)

    pos_val = torch.tensor([p[0] for p in val_pairs], dtype=torch.float32)
    neg_val = torch.tensor([p[1] for p in val_pairs], dtype=torch.float32)

    n_samples = len(pos_train)
    best_val_loss = float("inf")
    ckpt_dir = PACKAGE_ROOT / "pdi" / "checkpoints" / "psmsl_mlp_v07b"
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    for epoch in range(1, epochs + 1):
        model.train()
        indices = torch.randperm(n_samples)
        total_loss = 0.0

        for start_idx in range(0, n_samples, batch_size):
            batch_idx = indices[start_idx : start_idx + batch_size]
            b_pos = pos_train[batch_idx]
            b_neg = neg_train[batch_idx]

            optimizer.zero_grad()
            s_pos = model(b_pos)
            s_neg = model(b_neg)

            loss = loss_fn(s_neg - s_pos).mean()
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * len(batch_idx)

        train_loss = total_loss / n_samples

        # Validation
        model.eval()
        with torch.no_grad():
            s_pos_val = model(pos_val)
            s_neg_val = model(neg_val)
            val_loss = loss_fn(s_neg_val - s_pos_val).mean().item()
            val_acc = (s_pos_val > s_neg_val).float().mean().item()

        if epoch % 10 == 0 or epoch == epochs:
            print(f"Epoch {epoch:2d}/{epochs} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | Val Ranking Acc: {val_acc*100:.2f}%")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            # Save checkpoint
            torch.save(model.state_dict(), ckpt_dir / "psmsl_mlp_best.pt")
            with open(ckpt_dir / "weights_exported.json", "w", encoding="utf-8") as f:
                json.dump(model.export_weights_dict(), f, indent=2)

    with open(ckpt_dir / "split_info.json", "w", encoding="utf-8") as f:
        json.dump(split_info, f, indent=2)

    print(f"\nModel training complete. Best checkpoint saved to: {ckpt_dir / 'psmsl_mlp_best.pt'}")
    return model


if __name__ == "__main__":
    train_psmsl_mlp()
