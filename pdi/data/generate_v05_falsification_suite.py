# SPDX-License-Identifier: MIT
"""Independent Prospective Falsification Suite Generator for PDI-135M-v0.5.

Constructs 128 completely unseen scenarios across 4 independent test regimes:
1. HELD_OUT_OPERATORS (32 scenarios):
   - OP_REVERSE (6), OP_INVOLUTION (7), OP_CONJUGATE (8), OP_ANTICOMMUTATOR (12)
2. INADMISSIBLE_REFUSAL (24 scenarios):
   - Out-of-bounds addresses, uncertified capabilities, stale versions
3. INSUFFICIENT_CLARIFICATION (24 scenarios):
   - Omitted operands, missing destinations, ambiguous projections
4. UNSEEN_AMBIGUITY_CHALLENGE (48 scenarios):
   - Fresh non-commutative products, commutators, and geometric contractions

All expected multivector values computed via bit-exact RTL Q16.16 simulation.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Dict, List

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from pdi.postcondition.fixed_point_oracle import Q16Multivector, RTLCliffordSimulator


def generate_v05_suite(output_path: Path) -> Dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    records: List[Dict[str, Any]] = []

    # -------------------------------------------------------------------------
    # 1. HELD_OUT_OPERATORS (32 scenarios)
    # -------------------------------------------------------------------------
    held_out_ops = [
        (6, "OP_REVERSE", "Clifford reversion", 1),
        (7, "OP_GRADE_INVOLUTION", "grade involution", 1),
        (8, "OP_CLIFFORD_CONJUGATE", "Clifford conjugation", 1),
        (12, "OP_ANTICOMMUTATOR", "anticommutator product {A, B}", 2),
    ]

    for i in range(32):
        op_info = held_out_ops[i % len(held_out_ops)]
        op_id, mne, op_desc, arity = op_info
        src_a = 40 + (i * 2) % 60
        src_b = 41 + (i * 2) % 60
        dest = 140 + i
        ver = 3000 + i * 4

        val_a = Q16Multivector.from_floats(1.0 + 0.05 * i, 1.5, -0.5, 0.75)
        val_b = Q16Multivector.from_floats(-0.5, 0.8, 1.2, -0.25)

        if op_id == 6:  # Reversion: s -> s, e1 -> e1, e2 -> e2, e12 -> -e12
            exp_q = Q16Multivector(val_a.s, val_a.e1, val_a.e2, -val_a.e12)
            prompt = f"Context: Dest address {dest}, version {ver}. Pre-state: @{src_a} = {val_a.to_floats()}. Goal: Apply {op_desc} to state {src_a} into destination {dest}."
            canonical = f"PROPOSE {mne} REF_{src_a} GOAL_{dest}"
            srcs = [src_a]
        elif op_id == 7:  # Involution: s -> s, e1 -> -e1, e2 -> -e2, e12 -> e12
            exp_q = Q16Multivector(val_a.s, -val_a.e1, -val_a.e2, val_a.e12)
            prompt = f"Context: Dest address {dest}, version {ver}. Pre-state: @{src_a} = {val_a.to_floats()}. Goal: Apply {op_desc} to state {src_a} into destination {dest}."
            canonical = f"PROPOSE {mne} REF_{src_a} GOAL_{dest}"
            srcs = [src_a]
        elif op_id == 8:  # Conjugation: s -> s, e1 -> -e1, e2 -> -e2, e12 -> -e12
            exp_q = Q16Multivector(val_a.s, -val_a.e1, -val_a.e2, -val_a.e12)
            prompt = f"Context: Dest address {dest}, version {ver}. Pre-state: @{src_a} = {val_a.to_floats()}. Goal: Apply {op_desc} to state {src_a} into destination {dest}."
            canonical = f"PROPOSE {mne} REF_{src_a} GOAL_{dest}"
            srcs = [src_a]
        else:  # Anticommutator: 1/2 (AB + BA)
            ab, _ = RTLCliffordSimulator.cl20_product(val_a, val_b)
            ba, _ = RTLCliffordSimulator.cl20_product(val_b, val_a)
            exp_q = Q16Multivector(
                (ab.s + ba.s) // 2,
                (ab.e1 + ba.e1) // 2,
                (ab.e2 + ba.e2) // 2,
                (ab.e12 + ba.e12) // 2,
            )
            prompt = f"Context: Dest address {dest}, version {ver}. Pre-state: @{src_a} = {val_a.to_floats()}, @{src_b} = {val_b.to_floats()}. Goal: Compute {op_desc} of state {src_a} and state {src_b} into destination {dest}."
            canonical = f"PROPOSE {mne} REF_{src_a} REF_{src_b} GOAL_{dest}"
            srcs = [src_a, src_b]

        records.append({
            "scenario_id": f"PDI-V05-HELDOUT-s{i:03d}",
            "regime": "HELD_OUT_OPERATORS",
            "input_prompt": prompt,
            "assumed_state_version": ver,
            "authorized_capability_mask": 0x00000001,
            "dest_ref": dest,
            "src_refs": srcs,
            "pre_state": {
                str(src_a): {"s": val_a.to_floats()[0], "e1": val_a.to_floats()[1], "e2": val_a.to_floats()[2], "e12": val_a.to_floats()[3]},
                str(src_b): {"s": val_b.to_floats()[0], "e1": val_b.to_floats()[1], "e2": val_b.to_floats()[2], "e12": val_b.to_floats()[3]},
            },
            "expected_q16": {"s": exp_q.s, "e1": exp_q.e1, "e2": exp_q.e2, "e12": exp_q.e12},
            "canonical_action": canonical,
            "expected_route": "RULE",
            "is_abstention": False,
        })

    # -------------------------------------------------------------------------
    # 2. INADMISSIBLE_REFUSAL (24 scenarios)
    # -------------------------------------------------------------------------
    refuse_reasons = [
        ("Destination memory address out of bounds (dest=300 >= 256)", 300, 10, 11, 0x00000001),
        ("Source operand address out of bounds (src=280 >= 256)", 50, 280, 11, 0x00000001),
        ("Uncertified capability mask requirement (cap=0x80000000)", 60, 10, 11, 0x80000000),
        ("Stale state temporal sequence violation (requested v900 < current v1500)", 70, 10, 11, 0x00000001),
    ]

    for i in range(24):
        reason, dest, s0, s1, cap = refuse_reasons[i % len(refuse_reasons)]
        ver = 3500 + i * 3
        prompt = f"Context: Dest address {dest}, version {ver}. Pre-state: @{s0} = 1s, @{s1} = 2s. Security constraint: {reason}. Request: PROPOSE OP_ADD REF_{s0} REF_{s1} GOAL_{dest}."

        records.append({
            "scenario_id": f"PDI-V05-REFUSE-s{i:03d}",
            "regime": "INADMISSIBLE_REFUSAL",
            "input_prompt": prompt,
            "assumed_state_version": ver,
            "authorized_capability_mask": cap,
            "dest_ref": dest if dest < 256 else None,
            "src_refs": [s0, s1],
            "pre_state": {},
            "expected_q16": None,
            "canonical_action": "ABSTAIN / NONE_OF_THE_ABOVE",
            "expected_route": "REFUSE",
            "is_abstention": True,
        })

    # -------------------------------------------------------------------------
    # 3. INSUFFICIENT_CLARIFICATION (24 scenarios)
    # -------------------------------------------------------------------------
    clarify_reasons = [
        "Missing primary operand source address",
        "Unspecified destination memory address",
        "Ambiguous multivector projection grade requested",
        "Conflicting pre-state temporal version tags (v1010 vs v1080)",
    ]

    for i in range(24):
        reason = clarify_reasons[i % len(clarify_reasons)]
        ver = 4000 + i * 5
        prompt = f"Context: Pre-state version {ver}. State memory observation. Notice: {reason}. Work request requires resolution before dispatch."

        records.append({
            "scenario_id": f"PDI-V05-CLARIFY-s{i:03d}",
            "regime": "INSUFFICIENT_CLARIFICATION",
            "input_prompt": prompt,
            "assumed_state_version": ver,
            "authorized_capability_mask": 0x00000001,
            "dest_ref": None,
            "src_refs": [],
            "pre_state": {},
            "expected_q16": None,
            "canonical_action": "CLARIFY SLOT_operator_id REASON_unspecified_ambiguity",
            "expected_route": "CLARIFY",
            "is_abstention": True,
        })

    # -------------------------------------------------------------------------
    # 4. UNSEEN_AMBIGUITY_CHALLENGE (48 scenarios)
    # -------------------------------------------------------------------------
    for i in range(48):
        src_a = 70 + (i * 2) % 40
        src_b = 71 + (i * 2) % 40
        dest = 180 + i
        ver = 4500 + i * 7

        val_a = Q16Multivector.from_floats(1.5, 0.5 * (i % 3), -1.0, 0.5)
        val_b = Q16Multivector.from_floats(-0.5, 1.0, 1.5, -0.5 * (i % 2))

        if i % 3 == 0:  # Non-commutative Clifford product
            exp_q, _ = RTLCliffordSimulator.cl20_product(val_a, val_b)
            prompt = f"Context: Dest address {dest}, version {ver}. Pre-state: @{src_a} = {val_a.to_floats()}, @{src_b} = {val_b.to_floats()}. Goal: Compute oriented geometric Clifford product of state {src_a} by state {src_b} into destination state {dest}."
            canonical = f"PROPOSE OP_CL20_PRODUCT REF_{src_a} REF_{src_b} GOAL_{dest}"
        elif i % 3 == 1:  # Non-commutative Commutator
            exp_q, _ = RTLCliffordSimulator.commutator(val_a, val_b)
            prompt = f"Context: Dest address {dest}, version {ver}. Pre-state: @{src_a} = {val_a.to_floats()}, @{src_b} = {val_b.to_floats()}. Goal: Compute oriented commutator product [A, B] of state {src_a} by state {src_b} into destination state {dest}."
            canonical = f"PROPOSE OP_COMMUTATOR REF_{src_a} REF_{src_b} GOAL_{dest}"
        else:  # Contextual ambiguity between dot and wedge
            if i % 2 == 0:
                exp_q, _ = RTLCliffordSimulator.vector_dot(val_a, val_b)
                prompt = f"Context: Dest address {dest}, version {ver}. Pre-state: @{src_a} = {val_a.to_floats()}, @{src_b} = {val_b.to_floats()}. Task intent: Extract symmetric scalar projection metric between state {src_a} and state {src_b} into destination state {dest}."
                canonical = f"PROPOSE OP_VECTOR_DOT REF_{src_a} REF_{src_b} GOAL_{dest}"
            else:
                exp_q, _ = RTLCliffordSimulator.vector_wedge(val_a, val_b)
                prompt = f"Context: Dest address {dest}, version {ver}. Pre-state: @{src_a} = {val_a.to_floats()}, @{src_b} = {val_b.to_floats()}. Task intent: Construct oriented planar bivector span spanned by state {src_a} and state {src_b} into destination state {dest}."
                canonical = f"PROPOSE OP_VECTOR_WEDGE REF_{src_a} REF_{src_b} GOAL_{dest}"

        records.append({
            "scenario_id": f"PDI-V05-AMBIG-s{i:03d}",
            "regime": "UNSEEN_AMBIGUITY_CHALLENGE",
            "input_prompt": prompt,
            "assumed_state_version": ver,
            "authorized_capability_mask": 0x00000001,
            "dest_ref": dest,
            "src_refs": [src_a, src_b],
            "pre_state": {
                str(src_a): {"s": val_a.to_floats()[0], "e1": val_a.to_floats()[1], "e2": val_a.to_floats()[2], "e12": val_a.to_floats()[3]},
                str(src_b): {"s": val_b.to_floats()[0], "e1": val_b.to_floats()[1], "e2": val_b.to_floats()[2], "e12": val_b.to_floats()[3]},
            },
            "expected_q16": {"s": exp_q.s, "e1": exp_q.e1, "e2": exp_q.e2, "e12": exp_q.e12},
            "canonical_action": canonical,
            "expected_route": "NEURAL",
            "is_abstention": False,
        })

    assert len(records) == 128, f"Expected 128 records, got {len(records)}"

    manifest = {
        "schema_version": "1.0.0",
        "corpus_id": "pdi-v05-prospective-falsification-128",
        "total_records": 128,
        "distribution": {
            "held_out_operators": 32,
            "inadmissible_refusal": 24,
            "insufficient_clarification": 24,
            "unseen_ambiguity_challenge": 48,
        },
        "records": records,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Generated {len(records)} prospective falsification scenarios to: {output_path}")
    return manifest


if __name__ == "__main__":
    out_file = PACKAGE_ROOT / "pdi" / "data" / "pdi_v05_prospective_falsification.json"
    generate_v05_suite(out_file)
