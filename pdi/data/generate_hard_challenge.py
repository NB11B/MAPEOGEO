# SPDX-License-Identifier: MIT
"""Hard Ambiguity and Independence Challenge Corpus Generator for PDI-135M-v0.4.

Constructs 64 rigorous test scenarios across three critical challenge categories:
1. Category A (24 scenarios): Non-Commutative & Subtle Operand Discriminators
   - Menus contain competing candidates with identical opcodes and destinations,
     differing ONLY in operand ordering (e.g. A*B vs B*A, A^B vs B^A, [A,B] vs [B,A]).
   - Fully numerical evaluation verifies that only the correct ordering satisfies P_G.
2. Category B (20 scenarios): Partially Observable / Underspecified Work
   - Crucial state information or operands are omitted from the visible prompt.
   - Any execution proposal is unsafe guessing (label = -1).
   - ONLY explicit abstention or clarification is verified useful (label = +1).
3. Category C (20 scenarios): Genuinely Ambiguous Contextual Work
   - Multiple legal candidate actions are admissible; subtle contextual cues
     in the task description distinguish the optimal transformation.
   - Tests whether learned representations add value over simple rule heuristics.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Dict, List

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from pdi.postcondition.goal_postcondition_engine import CliffordSimulator
from pdi.postcondition.state_transition_oracle import NumericalGoalProperty, StateTransitionOracle
from pdi.projection.psmsl_projection import Cl20Multivector


def generate_hard_challenge_corpus(output_path: Path) -> Dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    records: List[Dict[str, Any]] = []

    # -----------------------------------------------------------------------
    # Category A: 24 Non-Commutative Operand Discriminators
    # -----------------------------------------------------------------------
    for i in range(24):
        src_a = 10 + i * 2
        src_b = 11 + i * 2
        dest = 70 + i
        ver = 1500 + i * 3

        # Asymmetric pre-state multivectors
        val_a = Cl20Multivector(s=1.0 + 0.1 * i, e1=2.0, e2=-0.5, e12=0.5)
        val_b = Cl20Multivector(s=-0.5, e1=1.0, e2=1.5, e12=-1.0 + 0.1 * i)

        # Alternating non-commutative operators: CL20_PRODUCT (5), WEDGE (10), COMMUTATOR (11)
        op_types = [(5, "OP_CL20_PRODUCT", "geometric Clifford product"),
                    (10, "OP_VECTOR_WEDGE", "exterior wedge product"),
                    (11, "OP_COMMUTATOR", "commutator product [A, B]")]
        op_id, mne, op_name = op_types[i % len(op_types)]

        if op_id == 5:
            expected_mv = CliffordSimulator.cl20_product(val_a, val_b)
        elif op_id == 10:
            expected_mv = CliffordSimulator.vector_wedge(val_a, val_b)
        else:
            ab = CliffordSimulator.cl20_product(val_a, val_b)
            ba = CliffordSimulator.cl20_product(val_b, val_a)
            diff = CliffordSimulator.sub(ab, ba)
            expected_mv = Cl20Multivector(s=0.5*diff.s, e1=0.5*diff.e1, e2=0.5*diff.e2, e12=0.5*diff.e12)

        prompt = (
            f"Context: Dest address {dest}, pre-state version {ver}. "
            f"Pre-state: @{src_a} = {val_a.to_psmsl()}, @{src_b} = {val_b.to_psmsl()}. "
            f"Goal: Compute oriented {op_name} of state {src_a} by state {src_b} into destination state {dest}."
        )

        records.append({
            "scenario_id": f"PDI-HARD-NONCOMM-s{i:03d}",
            "challenge_category": "NON_COMMUTATIVE_DISCRIMINATOR",
            "input_prompt": prompt,
            "assumed_state_version": ver,
            "authorized_capability_mask": 0x00000001,
            "dest_ref": dest,
            "src_refs": [src_a, src_b],
            "pre_state": {
                str(src_a): {"s": val_a.s, "e1": val_a.e1, "e2": val_a.e2, "e12": val_a.e12},
                str(src_b): {"s": val_b.s, "e1": val_b.e1, "e2": val_b.e2, "e12": val_b.e12},
            },
            "expected_multivector": {"s": expected_mv.s, "e1": expected_mv.e1, "e2": expected_mv.e2, "e12": expected_mv.e12},
            "canonical_action": f"PROPOSE {mne} REF_{src_a} REF_{src_b} GOAL_{dest}",
            "reversed_action": f"PROPOSE {mne} REF_{src_b} REF_{src_a} GOAL_{dest}",
            "requires_abstention": False,
        })

    # -----------------------------------------------------------------------
    # Category B: 20 Partially Observable / Underspecified Scenarios
    # -----------------------------------------------------------------------
    underspec_reasons = [
        "Missing primary operand source address",
        "Conflicting pre-state temporal version tags (v1010 vs v1080)",
        "Destination memory address unspecified",
        "Ambiguous multivector projection grade requested",
        "Uncertified capability requirement 0x80000000",
    ]
    for i in range(20):
        reason = underspec_reasons[i % len(underspec_reasons)]
        ver = 1600 + i * 4
        prompt = (
            f"Context: Execution request under incomplete state observation, version {ver}. "
            f"Issue: {reason}. "
            f"Directive: Unsafe execution prohibited. Must clarify ambiguity or abstain from state mutation."
        )
        records.append({
            "scenario_id": f"PDI-HARD-UNDERSPEC-s{i:03d}",
            "challenge_category": "PARTIALLY_OBSERVABLE_UNDERSPECIFIED",
            "input_prompt": prompt,
            "assumed_state_version": ver,
            "authorized_capability_mask": 0x00000001,
            "dest_ref": None,
            "src_refs": [],
            "pre_state": {},
            "expected_multivector": None,
            "canonical_action": "ABSTAIN / NONE_OF_THE_ABOVE",
            "requires_abstention": True,
            "abstention_reason": reason,
        })

    # -----------------------------------------------------------------------
    # Category C: 20 Genuinely Ambiguous Contextual Scenarios
    # -----------------------------------------------------------------------
    for i in range(20):
        src_a = 30 + i * 2
        src_b = 31 + i * 2
        dest = 90 + i
        ver = 1700 + i * 7

        val_a = Cl20Multivector(s=2.0, e1=1.0, e2=0.0, e12=0.0)
        val_b = Cl20Multivector(s=1.0, e1=0.0, e2=2.0, e12=0.0)

        # Contextual prompt choosing between symmetric dot vs oriented wedge
        if i % 2 == 0:
            prompt = (
                f"Context: Dest address {dest}, version {ver}. "
                f"Pre-state: @{src_a} = {val_a.to_psmsl()}, @{src_b} = {val_b.to_psmsl()}. "
                f"Task intent: Extract symmetric scalar projection metric between state {src_a} and state {src_b} into destination state {dest}."
            )
            canonical = f"PROPOSE OP_VECTOR_DOT REF_{src_a} REF_{src_b} GOAL_{dest}"
            exp_mv = CliffordSimulator.vector_dot(val_a, val_b)
        else:
            prompt = (
                f"Context: Dest address {dest}, version {ver}. "
                f"Pre-state: @{src_a} = {val_a.to_psmsl()}, @{src_b} = {val_b.to_psmsl()}. "
                f"Task intent: Construct oriented planar bivector span spanned by state {src_a} and state {src_b} into destination state {dest}."
            )
            canonical = f"PROPOSE OP_VECTOR_WEDGE REF_{src_a} REF_{src_b} GOAL_{dest}"
            exp_mv = CliffordSimulator.vector_wedge(val_a, val_b)

        records.append({
            "scenario_id": f"PDI-HARD-CONTEXT-s{i:03d}",
            "challenge_category": "CONTEXTUAL_AMBIGUITY",
            "input_prompt": prompt,
            "assumed_state_version": ver,
            "authorized_capability_mask": 0x00000001,
            "dest_ref": dest,
            "src_refs": [src_a, src_b],
            "pre_state": {
                str(src_a): {"s": val_a.s, "e1": val_a.e1, "e2": val_a.e2, "e12": val_a.e12},
                str(src_b): {"s": val_b.s, "e1": val_b.e1, "e2": val_b.e2, "e12": val_b.e12},
            },
            "expected_multivector": {"s": exp_mv.s, "e1": exp_mv.e1, "e2": exp_mv.e2, "e12": exp_mv.e12},
            "canonical_action": canonical,
            "requires_abstention": False,
        })

    assert len(records) == 64, f"Expected 64 records, got {len(records)}"

    manifest = {
        "schema_version": "1.0.0",
        "corpus_id": "pdi-hard-ambiguity-challenge-64",
        "total_records": 64,
        "distribution": {
            "non_commutative_discriminators": 24,
            "partially_observable_underspecified": 20,
            "contextual_ambiguity": 20,
        },
        "records": records,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Generated 64-scenario Hard Ambiguity Challenge at: {output_path}")
    return manifest


if __name__ == "__main__":
    out_file = PACKAGE_ROOT / "pdi" / "data" / "pdi_v04_hard_ambiguity_challenge.json"
    generate_hard_challenge_corpus(out_file)
