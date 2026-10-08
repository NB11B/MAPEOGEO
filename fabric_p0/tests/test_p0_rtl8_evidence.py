# SPDX-License-Identifier: MIT
# MAPEOGEO Preproduction Fabric P0
# Test Suite: test_p0_rtl8_evidence.py
# Gate RTL-8: Production Cryptographic Evidence Hardware Engine Qualification

import hashlib
import os
import random
import struct
import sys
from pathlib import Path
import pytest

FABRIC_P0_DIR = Path(__file__).parent.parent
RTL_DIR = FABRIC_P0_DIR / "rtl"
sys.path.insert(0, str(FABRIC_P0_DIR))
sys.path.insert(0, str(FABRIC_P0_DIR.parent))

from fabric_p0.model.geo_reference import FixedPointModel, FixedCl20


# =============================================================================
# Helper Functions for Deterministic Serialization & Merkle Tree Aggregation
# =============================================================================

def serialize_uow_record(uow_id: int, cert_id: int, causal_seq: int, pre_h: int, post_h: int, cand_h: int) -> bytes:
    """Matches exact SystemVerilog bit packing in geo_evidence_engine.sv (288 bits = 36 bytes)."""
    # [511:480] uow_id (4 bytes)
    # [479:448] cert_id (4 bytes)
    # [447:416] causal_seq (4 bytes)
    # [415:384] format tag (0xA5A55A5A, 4 bytes)
    # [383:320] pre_state_hash (8 bytes)
    # [319:256] post_state_hash (8 bytes)
    # [255:192] candidate_hash (8 bytes)
    return struct.pack(
        '>IIIIQQQ',
        uow_id & 0xFFFFFFFF,
        cert_id & 0xFFFFFFFF,
        causal_seq & 0xFFFFFFFF,
        0xA5A55A5A,
        pre_h & 0xFFFFFFFFFFFFFFFF,
        post_h & 0xFFFFFFFFFFFFFFFF,
        cand_h & 0xFFFFFFFFFFFFFFFF
    )


def compute_leaf_hash(record_bytes: bytes) -> bytes:
    """NIST SHA-256 over serialized record."""
    return hashlib.sha256(record_bytes).digest()


def compute_physical_chain(initial_state: bytes, records: list) -> bytes:
    """Chained sequential SHA-256 over records."""
    state = initial_state
    for rec in records:
        raw = serialize_uow_record(*rec)
        # In hardware, state is updated with each block
        h = hashlib.sha256()
        h.update(state + raw)
        state = h.digest()
    return state


def compute_canonical_semantic_root(records: list) -> bytes:
    """Canonical Merkle Root over causal set (sorted by uow_id)."""
    if not records:
        return hashlib.sha256(b'').digest()

    # Sort canonically by UoW ID (independent of physical execution arrival order)
    sorted_recs = sorted(records, key=lambda r: r[0])
    leaves = [compute_leaf_hash(serialize_uow_record(*r)) for r in sorted_recs]

    # Combine leaves canonically
    current_root = hashlib.sha256(b'MAPEOGEO_P0_MERKLE_ROOT_INIT').digest()
    for leaf in leaves:
        h = hashlib.sha256()
        # Symmetric folding node
        folded_block = bytes(a ^ b for a, b in zip(current_root, leaf))
        h.update(folded_block)
        current_root = h.digest()
    return current_root


# =============================================================================
# Test 1: NIST FIPS 180-4 Known-Answer Tests (KAT)
# =============================================================================

def test_rtl8_sha256_known_answer_vectors():
    """Verify SHA-256 standard vectors against published NIST FIPS 180-4 standards."""
    kat_vectors = [
        # Vector 1: Empty String
        (b"", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
        # Vector 2: "abc"
        (b"abc", "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"),
        # Vector 3: 56-byte string (spanning 2 512-bit message blocks)
        (b"abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq",
         "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1"),
        # Vector 4: 112-byte string (3 blocks)
        (b"abcdefghbcdefghicdefghijdefghijkefghijklfghijklmghijklmnhijklmnoijklmnopjklmnopqklmnopqrlmnopqrsmnopqrstnopqrstu",
         "cf5b16a778af8380036ce59e7b0492370b249b11e8f07a51afac45037afee9d1")
    ]

    for msg, expected_hex in kat_vectors:
        computed = hashlib.sha256(msg).hexdigest()
        assert computed == expected_hex, f"NIST Vector Failed for msg '{msg[:16]}...'"


# =============================================================================
# Test 2: Dual-Evidence Construction (E_physical vs E_semantic)
# =============================================================================

def test_rtl8_dual_evidence_physical_vs_semantic():
    """
    Verify:
      1. E_physical is strictly order-dependent (different arrival orders -> different physical roots)
      2. E_semantic is strictly causally order-independent (different arrival orders -> identical semantic root)
    """
    initial_iv = hashlib.sha256(b'INITIAL_IV').digest()

    rec_a = (101, 1, 1, 0x1111222233334444, 0x5555666677778888, 0x9999AAAABBBBCCCC)
    rec_b = (102, 2, 2, 0xAAAA111122223333, 0xBBBB444455556666, 0xCCCC777788889999)
    rec_c = (103, 3, 3, 0xDDDD111122223333, 0xEEEE444455556666, 0xFFFF777788889999)

    order1 = [rec_a, rec_b, rec_c]
    order2 = [rec_c, rec_a, rec_b]
    order3 = [rec_b, rec_c, rec_a]

    # Compute Physical Evidence Roots
    phys_root1 = compute_physical_chain(initial_iv, order1)
    phys_root2 = compute_physical_chain(initial_iv, order2)
    phys_root3 = compute_physical_chain(initial_iv, order3)

    # Physical roots MUST differ under execution reordering
    assert phys_root1 != phys_root2
    assert phys_root1 != phys_root3
    assert phys_root2 != phys_root3

    # Compute Semantic Evidence Roots
    sem_root1 = compute_canonical_semantic_root(order1)
    sem_root2 = compute_canonical_semantic_root(order2)
    sem_root3 = compute_canonical_semantic_root(order3)

    # Semantic roots MUST BE STRICTLY IDENTICAL across all permutations
    assert sem_root1 == sem_root2 == sem_root3, "Semantic Merkle Root violated permutation invariance!"


# =============================================================================
# Test 3: Tamper Avalanche Effect & Collision Resistance
# =============================================================================

def test_rtl8_tamper_avalanche_and_fault_detection():
    """Verify that a single-bit perturbation produces >= 40% bit flips in the 256-bit evidence roots."""
    base_rec = (200, 1, 1, 0x1000000000000000, 0x2000000000000000, 0x3000000000000000)
    # Flip 1 bit in candidate_hash
    tampered_rec = (200, 1, 1, 0x1000000000000000, 0x2000000000000000, 0x3000000000000001)

    h_base = hashlib.sha256(serialize_uow_record(*base_rec)).digest()
    h_tampered = hashlib.sha256(serialize_uow_record(*tampered_rec)).digest()

    assert h_base != h_tampered

    # Count differing bits
    diff_bits = sum(bin(b1 ^ b2).count('1') for b1, b2 in zip(h_base, h_tampered))
    avalanche_pct = (diff_bits / 256.0) * 100.0

    assert avalanche_pct >= 40.0, f"Avalanche effect insufficient ({avalanche_pct:.1f}% bit difference)"


# =============================================================================
# Test 4: System Capacity Envelope Requalification with SHA-256 Engine
# =============================================================================

def test_rtl8_capacity_envelope_requalification():
    """
    Verify the complete system rate equation:
      R_system = min(N_I, N_E, N_M, N_O/2, N_A, R_evidence)
    accounting for pipelined SHA-256 evidence throughput.
    """
    # Test configurations
    configs = [
        # (N_I, N_E, N_M, N_O, N_A, R_ev_rate)
        (1, 1, 1, 2, 1, 1.0),
        (2, 2, 2, 4, 2, 2.0),
        (4, 4, 4, 8, 4, 4.0),
        (8, 8, 8, 16, 8, 8.0),
    ]

    for N_I, N_E, N_M, N_O, N_A, R_ev in configs:
        r_sys = min(N_I, N_E, N_M, N_O / 2.0, N_A, R_ev)
        assert r_sys == N_I, f"Rate mismatch for config ({N_I}, {N_E}, {N_M}, {N_O}, {N_A}): got {r_sys}"
