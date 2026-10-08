# SPDX-License-Identifier: MIT
"""Unit Tests for TwoStageHybridSelector in PDI-135M-v0.4.

Verifies:
1. Fast-path deterministic routing for unambiguous work.
2. Fast-path abstention routing for underspecified / uncertified work.
3. Neural tiebreaking invocation for ambiguous / tied candidates.
4. Strict permutation-equivariance of selected candidate under arbitrary menu permutation.
"""

from __future__ import annotations

import json
from pathlib import Path
import random
import sys

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from pdi.candidates.candidate_generator import DeterministicCandidateGenerator
from pdi.candidates.observable_state import ObservableStateExtractor
from pdi.models.candidate_scorer import TwoStageHybridSelector
from pdi.projection.work_relation_encoder import PSMSLWorkRelationEncoder


@pytest.fixture(scope="module")
def selector():
    return TwoStageHybridSelector()


def test_fast_path_routing_unambiguous(selector):
    """Unambiguous operations with high score margin must route via FAST_PATH."""
    prompt = "Context: State memory initialized. Version: 1042. Apply standard vector addition between state 10 and state 11 into destination 20."
    ctx = ObservableStateExtractor.extract_from_prompt(prompt, default_version=1042)
    gen = DeterministicCandidateGenerator()
    enc = PSMSLWorkRelationEncoder()

    menu = gen.generate_menu("test-unambig", ctx, prompt)
    sigs = [enc.encode(s.cand_id, s.action_line, ctx, prompt) for s in menu.slots]

    selected_sig, route = selector.select(sigs, prompt)
    assert route == "FAST_PATH"
    assert "OP_ADD" in selected_sig.action_line or "OP_ALU_ADD" in selected_sig.action_line


def test_fast_path_routing_abstention(selector):
    """Partially observable work requiring abstention must route via FAST_PATH without neural inference."""
    prompt = "Context: Missing primary operand source address. Cannot proceed."
    ctx = ObservableStateExtractor.extract_from_prompt(prompt, default_version=1000)
    gen = DeterministicCandidateGenerator()
    enc = PSMSLWorkRelationEncoder()

    menu = gen.generate_menu("test-abstain", ctx, prompt)
    sigs = [enc.encode(s.cand_id, s.action_line, ctx, prompt) for s in menu.slots]

    selected_sig, route = selector.select(sigs, prompt)
    assert route == "FAST_PATH"
    assert selected_sig.constraints.is_abstention is True


def test_neural_tiebreaker_contextual_ambiguity(selector):
    """Contextually ambiguous work with tied rule scores routes to NEURAL_PATH and resolves correctly."""
    prompt = "Context: Dest address 90, version 1700. Pre-state: @30 = 2s + 1e1, @31 = 1s + 2e2. Task intent: Extract symmetric scalar projection metric between state 30 and state 31 into destination state 90."
    ctx = ObservableStateExtractor.extract_from_prompt(prompt, default_version=1700)
    gen = DeterministicCandidateGenerator()
    enc = PSMSLWorkRelationEncoder()

    menu = gen.generate_menu("test-context", ctx, prompt)
    sigs = [enc.encode(s.cand_id, s.action_line, ctx, prompt) for s in menu.slots]

    selected_sig, route = selector.select(sigs, prompt)
    assert route == "NEURAL_PATH"
    assert "OP_VECTOR_DOT" in selected_sig.action_line


def test_hybrid_selector_permutation_equivariance(selector):
    """Selected candidate identity must be invariant under arbitrary permutation of menu candidates."""
    prompt = "Context: Dest address 90, version 1700. Pre-state: @30 = 2s + 1e1, @31 = 1s + 2e2. Task intent: Extract symmetric scalar projection metric between state 30 and state 31 into destination state 90."
    ctx = ObservableStateExtractor.extract_from_prompt(prompt, default_version=1700)
    gen = DeterministicCandidateGenerator()
    enc = PSMSLWorkRelationEncoder()

    menu = gen.generate_menu("test-perm", ctx, prompt)
    sigs = [enc.encode(s.cand_id, s.action_line, ctx, prompt) for s in menu.slots]

    baseline_sig, _ = selector.select(sigs, prompt)

    for seed in [42, 101, 777]:
        permuted_sigs = list(sigs)
        rng = random.Random(seed)
        rng.shuffle(permuted_sigs)

        perm_sig, _ = selector.select(permuted_sigs, prompt)
        assert perm_sig.cand_id == baseline_sig.cand_id
        assert perm_sig.action_line == baseline_sig.action_line
