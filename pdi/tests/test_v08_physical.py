# SPDX-License-Identifier: MIT
"""Unit and Integration Tests for Track PDI-v0.8 Physical PSMSL Scorer."""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import pytest
import torch

from pdi.candidates.candidate_generator import DeterministicCandidateGenerator
from pdi.candidates.observable_state import ObservableStateExtractor
from pdi.models.bit_exact_scorer import BitExactPSMSLScorer
from pdi.models.observable_guard import ObservableStateGuard
from pdi.models.psmsl_mlp import PSMSLCompactMLP
from pdi.projection.dense_psmsl_encoder import DensePSMSLEncoder

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent


def test_observable_guard_isolation():
    """Verify ObservableStateGuard correctly identifies refusal and clarification without oracle regime."""
    # Test refusal (out-of-bounds destination address)
    prompt_refuse = "Context: Dest address 300, version 1000. Security constraint: out of bounds. Request: PROPOSE OP_ADD REF_10 REF_11 GOAL_300."
    ctx_refuse = ObservableStateExtractor.extract_from_prompt(prompt_refuse)
    viol, clarify = ObservableStateGuard.evaluate(prompt_refuse, ctx_refuse)
    assert viol is True, "Expected constraint violation on dest address 300 >= 256"
    assert clarify is False

    # Test clarification (missing primary source operands)
    prompt_clarify = "Context: Pre-state version 1000. Notice: Missing primary operand source address. Work request requires resolution."
    ctx_clarify = ObservableStateExtractor.extract_from_prompt(prompt_clarify)
    viol2, clarify2 = ObservableStateGuard.evaluate(prompt_clarify, ctx_clarify)
    assert viol2 is False
    assert clarify2 is True, "Expected clarification required when operands missing"


def test_bit_exact_scorer_top1_agreement():
    """Verify bit-exact integer scorer matches FP32 top-1 selection on transfer challenge suite."""
    scorer_int = BitExactPSMSLScorer()
    mlp_fp32 = PSMSLCompactMLP()
    ckpt = PACKAGE_ROOT / "pdi" / "checkpoints" / "psmsl_mlp_v07b" / "psmsl_mlp_best.pt"
    mlp_fp32.load_state_dict(torch.load(ckpt, map_location="cpu", weights_only=True))
    mlp_fp32.eval()

    gen = DeterministicCandidateGenerator()
    enc_dense = DensePSMSLEncoder()
    transfer_path = PACKAGE_ROOT / "pdi" / "data" / "pdi_v06_independent_transfer.json"
    with open(transfer_path, "r", encoding="utf-8") as f:
        records = json.load(f)["records"]

    agreements = 0
    for r in records:
        prompt = r["input_prompt"]
        ctx = ObservableStateExtractor.extract_from_prompt(prompt, default_version=r["assumed_state_version"])
        menu = gen.generate_menu(r["scenario_id"], ctx, prompt)

        cand_scores_int = []
        for slot in menu.slots:
            feats = enc_dense.encode_dense_vector(slot.cand_id, slot.action_line, ctx, prompt)
            score_i = scorer_int.score_vector(feats)
            cand_scores_int.append((score_i, slot.cand_id))
        cand_scores_int.sort(key=lambda item: (-item[0], item[1]))
        best_int_cid = cand_scores_int[0][1]

        cand_feats = [
            enc_dense.encode_dense_vector(s.cand_id, s.action_line, ctx, prompt) for s in menu.slots
        ]
        _, best_fp32_cid, _, _ = mlp_fp32.select_best_candidate(
            cand_feats,
            [s.cand_id for s in menu.slots],
            [s.action_line for s in menu.slots],
        )

        if best_int_cid == best_fp32_cid:
            agreements += 1

    assert agreements == len(records), f"Expected 100% agreement, got {agreements}/{len(records)}"


def test_rtl_simulation_differential_matches():
    """Verify Icarus Verilog simulation passes with 0 mismatches against Python integer reference."""
    res = subprocess.run(
        [
            "wsl",
            "bash",
            "-c",
            "cd /mnt/c/Users/nateb/OneDrive/Documents/MAPEOGEO && "
            "iverilog -g2012 -o /tmp/tb_geo_psmsl_scorer fabric_p0/rtl/scorer/geo_psmsl_scorer.sv fabric_p0/sim/tb_geo_psmsl_scorer.sv && "
            "vvp /tmp/tb_geo_psmsl_scorer",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert res.returncode == 0, f"RTL simulation failed: {res.stderr}"
    assert "Mismatches:          0" in res.stdout, f"RTL simulation found mismatches: {res.stdout}"
    assert "All 80 vectors matched bit-exact down to LSB!" in res.stdout


def test_scorer_authority_isolation():
    """Verify geo_psmsl_scorer.sv has zero write ports or mutation interfaces to state memory."""
    rtl_path = PACKAGE_ROOT / "fabric_p0" / "rtl" / "scorer" / "geo_psmsl_scorer.sv"
    assert rtl_path.exists(), f"RTL file not found: {rtl_path}"
    content = rtl_path.read_text(encoding="utf-8")

    # Check port declarations
    forbidden_terms = ["wr_en", "we", "write_data", "din", "bus_master", "mem_wr", "state_wr"]
    port_match = re.search(r"module\s+geo_psmsl_scorer\s*#?\(.*?\)\s*\((.*?)\);", content, re.DOTALL)
    assert port_match is not None, "Could not extract port list from geo_psmsl_scorer.sv"
    ports_text = port_match.group(1).lower()

    for term in forbidden_terms:
        assert term not in ports_text, f"Authority boundary violation: found '{term}' in scorer port list"

    # Confirm only read-only outputs exist
    assert "busy" in ports_text
    assert "done" in ports_text
    assert "score_out" in ports_text
