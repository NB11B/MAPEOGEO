# SPDX-License-Identifier: MIT
"""Generator for PDI-135M-v0.6 Independent Transfer & Generalization Challenge Suite (64 scenarios).

Constructs three distinct challenge regimes adhering to the formal PDI schema:
1. MULTI_STEP_COMPOSITION (20 scenarios): Sequential operator chains (e.g. wedge then dot, multivector reflections).
2. PARAPHRASED_NATURAL_GOALS (24 scenarios): Fresh paraphrased prompt structures authored with diverse terminology.
3. REPRESENTATIONAL_TRANSFER (20 scenarios): Cl(3,0) 3D rotors and Cl(1,3) spacetime boosts (explicitly scored as
   representational transfer, distinct from Cl(2,0) hardware execution).
"""

from __future__ import annotations

import json
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
OUT_PATH = PACKAGE_ROOT / "pdi" / "data" / "pdi_v06_independent_transfer.json"


def generate_transfer_suite():
    records = []
    scen_id = 0

    # -------------------------------------------------------------------------
    # Regime 1: MULTI_STEP_COMPOSITION (20 scenarios)
    # -------------------------------------------------------------------------
    comp_templates = [
        (
            "Execute composite geometric pipeline: first compute wedge product of state {src0} and state {src1} into destination {dest}, followed by contraction with state {src2}.",
            "OP_VECTOR_WEDGE",
        ),
        (
            "Two-stage multivector rotor application: first form geometric product of state {src0} and state {src1} into destination {dest}.",
            "OP_CL20_PRODUCT",
        ),
        (
            "Cascade vector addition then geometric product: add state {src0} and state {src1} into destination {dest} prior to multiplication with state {src2}.",
            "OP_ADD",
        ),
        (
            "Form geometric commutator bracket: evaluate commutator product of state {src0} and state {src1} targeting destination {dest}.",
            "OP_COMMUTATOR",
        ),
    ]

    for i in range(20):
        src0 = 10 + (i * 2)
        src1 = 11 + (i * 2)
        src2 = 12 + (i * 2)
        dest = 100 + i
        ver = 4000 + i * 4

        tmpl_text, op_mne = comp_templates[i % len(comp_templates)]
        prompt_goal = tmpl_text.format(src0=src0, src1=src1, src2=src2, dest=dest)
        prompt = f"Context: Dest address {dest}, version {ver}. Pre-state: state {src0}, state {src1}, state {src2}. Goal: {prompt_goal}"

        records.append({
            "scenario_id": f"PDI-V06-COMP-{scen_id:03d}",
            "regime": "MULTI_STEP_COMPOSITION",
            "input_prompt": prompt,
            "assumed_state_version": ver,
            "authorized_capability_mask": 1,
            "dest_ref": dest,
            "src_refs": [src0, src1],
            "canonical_action": f"PROPOSE {op_mne} REF_{src0} REF_{src1} GOAL_{dest}",
            "is_abstention": False,
            "is_representational_only": False,
        })
        scen_id += 1

    # -------------------------------------------------------------------------
    # Regime 2: PARAPHRASED_NATURAL_GOALS (24 scenarios)
    # -------------------------------------------------------------------------
    paraphrase_templates = [
        (
            "Compute the directed bivector area planar bivector span of state {src0} and state {src1} into destination {dest}.",
            "OP_VECTOR_WEDGE",
            2,
        ),
        (
            "Contract state {src0} with state {src1} via vector dot product into destination {dest}.",
            "OP_VECTOR_DOT",
            2,
        ),
        (
            "Calculate the Clifford geometric product of state {src0} and state {src1} into destination {dest}.",
            "OP_CL20_PRODUCT",
            2,
        ),
        (
            "Find the metric dot product between state {src0} and state {src1} into destination {dest}.",
            "OP_VECTOR_DOT",
            2,
        ),
        (
            "Synthesize the oriented wedge product of state {src0} and state {src1} into destination {dest}.",
            "OP_VECTOR_WEDGE",
            2,
        ),
        (
            "Apply grade involution to state {src0} into destination {dest}.",
            "OP_GRADE_INVOLUTION",
            1,
        ),
    ]

    for i in range(24):
        src0 = 20 + (i * 2)
        src1 = 21 + (i * 2)
        dest = 120 + i
        ver = 4100 + i * 4

        tmpl_text, op_mne, arity = paraphrase_templates[i % len(paraphrase_templates)]
        prompt_goal = tmpl_text.format(src0=src0, src1=src1, dest=dest)
        prompt = f"Context: Dest address {dest}, version {ver}. Pre-state: state {src0}, state {src1}. Goal: {prompt_goal}"

        if arity == 1:
            canonical = f"PROPOSE {op_mne} REF_{src0} GOAL_{dest}"
            src_refs = [src0]
        else:
            canonical = f"PROPOSE {op_mne} REF_{src0} REF_{src1} GOAL_{dest}"
            src_refs = [src0, src1]

        records.append({
            "scenario_id": f"PDI-V06-PARA-{scen_id:03d}",
            "regime": "PARAPHRASED_NATURAL_GOALS",
            "input_prompt": prompt,
            "assumed_state_version": ver,
            "authorized_capability_mask": 1,
            "dest_ref": dest,
            "src_refs": src_refs,
            "canonical_action": canonical,
            "is_abstention": False,
            "is_representational_only": False,
        })
        scen_id += 1

    # -------------------------------------------------------------------------
    # Regime 3: REPRESENTATIONAL_TRANSFER (20 scenarios)
    # -------------------------------------------------------------------------
    rep_templates = [
        (
            "[REPRESENTATIONAL TRANSFER Cl(3,0)] Evaluate 3D spatial rotor: geometric product of state {src0} and state {src1} into destination {dest}.",
            "OP_CL20_PRODUCT",
        ),
        (
            "[REPRESENTATIONAL TRANSFER Cl(1,3)] Minkowski spacetime boost generator: wedge product of state {src0} and state {src1} into destination {dest}.",
            "OP_VECTOR_WEDGE",
        ),
        (
            "[REPRESENTATIONAL TRANSFER Cl(3,0)] 3D spatial duality contraction: vector dot of state {src0} and state {src1} into destination {dest}.",
            "OP_VECTOR_DOT",
        ),
        (
            "[REPRESENTATIONAL TRANSFER Cl(1,3)] Spacetime invariant: vector dot contraction of state {src0} and state {src1} into destination {dest}.",
            "OP_VECTOR_DOT",
        ),
    ]

    for i in range(20):
        src0 = 40 + (i * 2)
        src1 = 41 + (i * 2)
        dest = 150 + i
        ver = 4200 + i * 4

        tmpl_text, op_mne = rep_templates[i % len(rep_templates)]
        prompt_goal = tmpl_text.format(src0=src0, src1=src1, dest=dest)
        prompt = f"Context: Dest address {dest}, version {ver}. Pre-state: state {src0}, state {src1}. Goal: {prompt_goal}"

        records.append({
            "scenario_id": f"PDI-V06-REP-{scen_id:03d}",
            "regime": "REPRESENTATIONAL_TRANSFER",
            "input_prompt": prompt,
            "assumed_state_version": ver,
            "authorized_capability_mask": 1,
            "dest_ref": dest,
            "src_refs": [src0, src1],
            "canonical_action": f"PROPOSE {op_mne} REF_{src0} REF_{src1} GOAL_{dest}",
            "is_abstention": False,
            "is_representational_only": True,
        })
        scen_id += 1

    payload = {
        "metadata": {
            "suite_id": "PDI_V06_INDEPENDENT_TRANSFER_SUITE",
            "total_scenarios": len(records),
            "regimes": {
                "MULTI_STEP_COMPOSITION": 20,
                "PARAPHRASED_NATURAL_GOALS": 24,
                "REPRESENTATIONAL_TRANSFER": 20,
            },
            "note": "REPRESENTATIONAL_TRANSFER is evaluated strictly for semantic scoring transfer; native P0 execution is Cl(2,0).",
        },
        "records": records,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"Generated {len(records)} independent transfer scenarios at: {OUT_PATH}")


if __name__ == "__main__":
    generate_transfer_suite()
