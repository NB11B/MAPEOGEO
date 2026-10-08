# SPDX-License-Identifier: MIT
"""Unit tests for PDI-135M-v0.3 State Projection Isolation.

Verifies:
1. Predefined context variants E0, E1, E2, E3, and E4.
2. Permission filtering redacting unauthorized addresses.
3. State versioning and deterministic serialization hashing.
4. Bounded payload lengths.
5. Invariance: Context variants DO NOT change candidate menu composition or candidate hashes.
"""

import pytest
from pdi.candidates.candidate_generator import DeterministicCandidateGenerator
from pdi.decoder.constrained_decoder import StateContext
from pdi.projection.state_projection import ContextArm, StateProjector


@pytest.fixture
def base_context() -> StateContext:
    return StateContext(
        assumed_state_version=1042,
        authorized_capability_mask=0x00000001,  # bit 0 set, bit 1 clear
        visible_refs=(10, 20, 150),             # 150 is > 128 (unauthorized without bit 1)
        goal_ref=20,
    )


def test_context_variants_generation(base_context: StateContext):
    """Ensure all five variants generate valid text with deterministic hashes."""
    prompt = "Compute relative offset of ref 10 into 20"
    for arm in ContextArm:
        proj = StateProjector.project(arm, prompt, base_context)
        assert proj.arm == arm
        assert proj.snapshot_version == 1042
        assert len(proj.context_text) > 0
        assert proj.context_hash is not None
        assert len(proj.context_hash) == 64
        assert proj.token_estimate > 0


def test_permission_filtering():
    """Verify addresses > 128 are redacted when cap bit 1 is missing."""
    prompt = "Test capability check"
    # Unauthorized context:
    unauth_ctx = StateContext(
        assumed_state_version=100,
        authorized_capability_mask=0x00000001,
        visible_refs=(12, 140),
        goal_ref=12,
    )
    proj_unauth = StateProjector.project(ContextArm.E1_BOUNDED_SLOTS, prompt, unauth_ctx)
    assert proj_unauth.is_permission_filtered is True
    assert "REF_140" not in proj_unauth.context_text
    assert "REF_12" in proj_unauth.context_text

    # Authorized context (cap bit 1 set: 0x2):
    auth_ctx = StateContext(
        assumed_state_version=100,
        authorized_capability_mask=0x00000003,
        visible_refs=(12, 140),
        goal_ref=12,
    )
    proj_auth = StateProjector.project(ContextArm.E1_BOUNDED_SLOTS, prompt, auth_ctx)
    assert proj_auth.is_permission_filtered is False
    assert "REF_140" in proj_auth.context_text
    assert "REF_12" in proj_auth.context_text


def test_deterministic_serialization(base_context: StateContext):
    """Identical inputs must produce identical context strings and hashes."""
    prompt = "Rotate reference 10"
    proj1 = StateProjector.project(ContextArm.E2_PSMSL_SYMBOLIC, prompt, base_context)
    proj2 = StateProjector.project(ContextArm.E2_PSMSL_SYMBOLIC, prompt, base_context)
    assert proj1.context_text == proj2.context_text
    assert proj1.context_hash == proj2.context_hash
    assert proj1.token_estimate == proj2.token_estimate


def test_bounded_payload_lengths(base_context: StateContext):
    """Context lengths must be bounded and follow expected relative complexity."""
    prompt = "Transform vector"
    e0 = StateProjector.project(ContextArm.E0_MINIMAL, prompt, base_context)
    e1 = StateProjector.project(ContextArm.E1_BOUNDED_SLOTS, prompt, base_context)
    e2 = StateProjector.project(ContextArm.E2_PSMSL_SYMBOLIC, prompt, base_context)
    e3 = StateProjector.project(ContextArm.E3_MEMORY_SNAPSHOT, prompt, base_context)
    e4 = StateProjector.project(ContextArm.E4_GRAPH_CAUSAL, prompt, base_context)

    # E0 should be minimal (goal only)
    assert e0.char_length < e1.char_length
    # None of the contexts should exceed 2048 chars for bounded operations
    for proj in (e0, e1, e2, e3, e4):
        assert proj.char_length < 2048
        assert proj.token_estimate < 512


def test_menu_invariance_across_context_arms(base_context: StateContext):
    """Crucial requirement: Context arms must not alter candidate menu generation.

    The menu is generated solely from the StateContext and operator registry,
    completely decoupled from the textual context arm projection.
    """
    generator = DeterministicCandidateGenerator()
    prompt = "Test task for menu invariance"
    menu1 = generator.generate_menu("test_scen_1", base_context, prompt)

    # Generate menus under various simulated context arms
    for arm in ContextArm:
        _ = StateProjector.project(arm, prompt, base_context)
        menu_test = generator.generate_menu("test_scen_1", base_context, prompt)
        assert menu_test.menu_hash == menu1.menu_hash
        assert len(menu_test.slots) == len(menu1.slots) == 8
        for s1, s2 in zip(menu1.slots, menu_test.slots):
            assert s1.cand_id == s2.cand_id
            assert s1.action_line == s2.action_line
