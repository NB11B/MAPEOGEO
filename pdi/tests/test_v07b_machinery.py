# SPDX-License-Identifier: MIT
"""Unit and Integration Tests for Track PDI-v0.7B Minimum Learned Machinery."""

import json
from pathlib import Path
import numpy as np
import pytest
import torch

from pdi.models.psmsl_mlp import PSMSLCompactMLP
from pdi.projection.dense_psmsl_encoder import DensePSMSLEncoder
from pdi.decoder.constrained_decoder import StateContext


def test_psmsl_mlp_parameter_count():
    model = PSMSLCompactMLP()
    # Must be exactly 4,225 parameters
    assert model.count_parameters() == 4225
    expected = (32 * 64 + 64) + (64 * 32 + 32) + (32 * 1 + 1)
    assert model.count_parameters() == expected


def test_dense_psmsl_encoder_dimensions():
    encoder = DensePSMSLEncoder()
    ctx = StateContext(assumed_state_version=1000, authorized_capability_mask=1, visible_refs=(10, 11), goal_ref=100)
    vec = encoder.encode_dense_vector("cand_0", "PROPOSE OP_VECTOR_WEDGE REF_10 REF_11 GOAL_100", ctx, "Compute wedge product")
    assert len(vec) == 32
    for val in vec:
        assert isinstance(val, (int, float))
        assert not np.isnan(val)


def test_psmsl_mlp_permutation_equivariance():
    model = PSMSLCompactMLP()
    encoder = DensePSMSLEncoder()
    ctx = StateContext(assumed_state_version=1000, authorized_capability_mask=1, visible_refs=(10, 11), goal_ref=100)
    
    actions = [
        "PROPOSE OP_ADD REF_10 REF_11 GOAL_100",
        "PROPOSE OP_VECTOR_WEDGE REF_10 REF_11 GOAL_100",
        "PROPOSE OP_SUB REF_10 REF_11 GOAL_100",
        "ABSTAIN / NONE_OF_THE_ABOVE",
    ]
    cands = [f"c_{i}" for i in range(len(actions))]
    feats = [encoder.encode_dense_vector(c, a, ctx, "Compute wedge product") for c, a in zip(cands, actions)]
    
    # Forward original
    idx1, cid1, act1, _ = model.select_best_candidate(feats, cands, actions)
    
    # Forward permuted (reverse order)
    rev_feats = list(reversed(feats))
    rev_cands = list(reversed(cands))
    rev_actions = list(reversed(actions))
    idx2, cid2, act2, _ = model.select_best_candidate(rev_feats, rev_cands, rev_actions)
    
    assert cid1 == cid2
    assert act1 == act2


def test_psmsl_mlp_quantization_stability():
    model = PSMSLCompactMLP()
    x = np.random.randn(8, 32).astype(np.float32)
    out_fp32 = model.numpy_forward(x, quantize_int8=False)
    out_int8 = model.numpy_forward(x, quantize_int8=True)
    
    assert len(out_fp32) == 8
    assert len(out_int8) == 8
    # High correlation between FP32 and simulated INT8
    corr = np.corrcoef(out_fp32, out_int8)[0, 1]
    assert corr > 0.90
