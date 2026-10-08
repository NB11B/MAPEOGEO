# SPDX-License-Identifier: MIT
"""Generator for PDI-135M-v0.7A 128-Scenario Composite Goals Suite.

Distributes:
1. Family 1: (A ^ B) . C [CONTRACTION_WEDGE] (40 scenarios)
2. Family 2: [A, B] = AB - BA [COMMUTATOR_BRACKET] (40 scenarios)
3. Family 3: R * A * ~R [ROTOR_SANDWICH] (32 scenarios)
4. Family 4: UNSUPPORTED / MALFORMED (16 scenarios, testing 100% fail-closed gating)

Total: 128 scenarios.
Computes bit-exact Q16.16 expected postconditions for all valid scenarios.
"""

from __future__ import annotations

import json
from pathlib import Path
import random

import sys
PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from pdi.postcondition.fixed_point_oracle import Q16Multivector, RTLCliffordSimulator

OUT_PATH = PACKAGE_ROOT / "pdi" / "data" / "pdi_v07a_composite_goals.json"


def generate_composite_dataset():
    rng = random.Random(2026_07)
    records = []
    scen_id = 0

    def make_random_q16() -> Q16Multivector:
        # Keep values small enough to prevent intermediate overflow (e.g. [-2.0, +2.0] in Q16)
        def rand_coord():
            return int(rng.uniform(-1.5, 1.5) * 65536)
        return Q16Multivector(s=rand_coord(), e1=rand_coord(), e2=rand_coord(), e12=rand_coord())

    # -------------------------------------------------------------------------
    # Family 1: (A ^ B) . C (40 scenarios)
    # -------------------------------------------------------------------------
    for i in range(40):
        src_a = 10 + i * 3
        src_b = 11 + i * 3
        src_c = 12 + i * 3
        dest = 100 + i

        va = make_random_q16()
        vb = make_random_q16()
        vc = make_random_q16()

        # Reference calculation: T = A ^ B; Output = T . C
        t_wedge, _ = RTLCliffordSimulator.compute_op("OP_VECTOR_WEDGE", [va, vb])
        expected_output, _ = RTLCliffordSimulator.compute_op("OP_VECTOR_DOT", [t_wedge, vc])

        expr = f"(state {src_a} ^ state {src_b}) . state {src_c}"
        prompt = f"Goal {scen_id}: Compute contraction of exterior product: {expr} into destination {dest}."

        records.append({
            "scenario_id": f"PDI-V07A-COMP-s{scen_id:03d}",
            "family": "CONTRACTION_WEDGE",
            "expression": expr,
            "input_prompt": prompt,
            "dest_ref": dest,
            "src_refs": [src_a, src_b, src_c],
            "initial_state": {
                str(src_a): va.to_dict(),
                str(src_b): vb.to_dict(),
                str(src_c): vc.to_dict(),
            },
            "expected_q16": expected_output.to_dict(),
            "is_supported": True,
            "first_step_canonical": f"PROPOSE OP_VECTOR_WEDGE REF_{src_a} REF_{src_b} STAGE_0",
        })
        scen_id += 1

    # -------------------------------------------------------------------------
    # Family 2: [A, B] = AB - BA (40 scenarios)
    # -------------------------------------------------------------------------
    for i in range(40):
        src_a = 20 + i * 2
        src_b = 21 + i * 2
        dest = 140 + i

        va = make_random_q16()
        vb = make_random_q16()

        p1, _ = RTLCliffordSimulator.compute_op("OP_CL20_PRODUCT", [va, vb])
        p2, _ = RTLCliffordSimulator.compute_op("OP_CL20_PRODUCT", [vb, va])
        expected_output, _ = RTLCliffordSimulator.compute_op("OP_SUB", [p1, p2])

        expr = f"commutator bracket of state {src_a} and state {src_b}"
        prompt = f"Goal {scen_id}: Compute non-commutative commutator bracket: [state {src_a}, state {src_b}] into destination {dest}."

        records.append({
            "scenario_id": f"PDI-V07A-COMM-s{scen_id:03d}",
            "family": "COMMUTATOR_BRACKET",
            "expression": expr,
            "input_prompt": prompt,
            "dest_ref": dest,
            "src_refs": [src_a, src_b],
            "initial_state": {
                str(src_a): va.to_dict(),
                str(src_b): vb.to_dict(),
            },
            "expected_q16": expected_output.to_dict(),
            "is_supported": True,
            "first_step_canonical": f"PROPOSE OP_CL20_PRODUCT REF_{src_a} REF_{src_b} STAGE_0",
        })
        scen_id += 1

    # -------------------------------------------------------------------------
    # Family 3: R * A * ~R (32 scenarios)
    # -------------------------------------------------------------------------
    for i in range(32):
        src_r = 30 + i * 2
        src_a = 31 + i * 2
        dest = 180 + i

        # Rotor R: normalized rotor (cos theta/2 + sin theta/2 e12)
        theta = rng.uniform(0.1, 3.0)
        import math
        c = int(math.cos(theta / 2.0) * 65536)
        s = int(math.sin(theta / 2.0) * 65536)
        vr = Q16Multivector(s=c, e1=0, e2=0, e12=s)
        va = make_random_q16()

        # Step 0: ~R
        rev_r, _ = RTLCliffordSimulator.compute_op("OP_REVERSE", [vr])
        # Step 1: A * ~R
        t1, _ = RTLCliffordSimulator.compute_op("OP_CL20_PRODUCT", [va, rev_r])
        # Step 2: R * (A * ~R)
        expected_output, _ = RTLCliffordSimulator.compute_op("OP_CL20_PRODUCT", [vr, t1])

        expr = f"rotor sandwich of state {src_r} and state {src_a}"
        prompt = f"Goal {scen_id}: Apply sandwich rotor transformation of state {src_r} on state {src_a} into destination {dest}."

        records.append({
            "scenario_id": f"PDI-V07A-ROTOR-s{scen_id:03d}",
            "family": "ROTOR_SANDWICH",
            "expression": expr,
            "input_prompt": prompt,
            "dest_ref": dest,
            "src_refs": [src_r, src_a],
            "initial_state": {
                str(src_r): vr.to_dict(),
                str(src_a): va.to_dict(),
            },
            "expected_q16": expected_output.to_dict(),
            "is_supported": True,
            "first_step_canonical": f"PROPOSE OP_REVERSE REF_{src_r} STAGE_0",
        })
        scen_id += 1

    # -------------------------------------------------------------------------
    # Family 4: UNSUPPORTED / MALFORMED (16 scenarios, fail-closed)
    # -------------------------------------------------------------------------
    unsupported_templates = [
        "Compute division of state {a} / state {b} into destination {dest}.",
        "Calculate matrix_inverse of state {a} into destination {dest}.",
        "Evaluate transcendental sin(state {a}) into destination {dest}.",
        "Compute square root sqrt(state {a}) into destination {dest}.",
    ]

    for i in range(16):
        src_a = 50 + i
        src_b = 51 + i
        dest = 220 + i
        tmpl = unsupported_templates[i % len(unsupported_templates)]
        prompt = f"Goal {scen_id}: " + tmpl.format(a=src_a, b=src_b, dest=dest)

        records.append({
            "scenario_id": f"PDI-V07A-UNSUP-s{scen_id:03d}",
            "family": "UNSUPPORTED",
            "expression": prompt,
            "input_prompt": prompt,
            "dest_ref": dest,
            "src_refs": [src_a, src_b],
            "initial_state": {
                str(src_a): make_random_q16().to_dict(),
                str(src_b): make_random_q16().to_dict(),
            },
            "expected_q16": None,
            "is_supported": False,
            "first_step_canonical": "REFUSE",
        })
        scen_id += 1

    payload = {
        "metadata": {
            "suite_id": "PDI_V07A_COMPOSITE_GOALS_128",
            "total_scenarios": len(records),
            "distribution": {
                "CONTRACTION_WEDGE": 40,
                "COMMUTATOR_BRACKET": 40,
                "ROTOR_SANDWICH": 32,
                "UNSUPPORTED_FAIL_CLOSED": 16,
            },
        },
        "records": records,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"Generated {len(records)} composite goal scenarios at: {OUT_PATH}")


if __name__ == "__main__":
    generate_composite_dataset()
