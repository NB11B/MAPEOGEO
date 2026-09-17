from __future__ import annotations

from .atlas import run_e25d
from .planner import run_e25e
from .fault_matrix import run_e25f


def build_report() -> str:
    d = run_e25d()
    e = run_e25e()
    f = run_e25f()

    lines = [
        "# MAPEOGEO E25D–E25F Closure Verification Program",
        "",
        f"**Stage status:** {'PASS' if d['status'] == e['status'] == f['status'] == 'PASS' else 'FAIL'}",
        "",
        f"E25D evaluates **{d['real_components']} real source-bound components** from the frozen v0.9 artifact.",
        "Synthetic controls do not count as repository closure.",
        "",
        "## Closure model",
        "",
        "`C0 identity → C1 certificate → C2 executable contract → C3 chain map → C4 induced homology → C5 exact morphism/provenance`",
        "",
        "## E25D — Closure Depth Atlas",
        "",
        "| Component | Contract | C0 | C1 | C2 | C3 | C4 | C5 | Frontier |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for c in d["components"]:
        s = c["closure"]
        lines.append(
            f"| `{c['component_id']}` | {c['contract']} | {s['C0']['state']} | {s['C1']['state']} | "
            f"{s['C2']['state']} | {s['C3']['state']} | {s['C4']['state']} | {s['C5']['state']} | {c['closure_frontier']} |"
        )

    lines += [
        "",
        f"Frontier histogram: `{d['frontier_histogram']}`.",
        "",
        "## E25E — Verification Upgrade Planner",
        "",
        "| Priority | Component | Next level | Blocking gap |",
        "|---|---|---|---|",
    ]
    for item in e["queue"]:
        lines.append(
            f"| `{item['priority_class']}` | `{item['component_id']}` | {item['expected_next_level']} | {item['blocking_gap']} |"
        )

    lines += [
        "",
        "The current queue is evidence work only. `P4_EXACT_MORPHISM_PROVENANCE_REQUIRED` does not authorize semantic promotion.",
        "",
        "## E25F — First-Capable-Layer Fault Coverage",
        "",
        "| Fault | Expected detector | Observed detector | Early false positive | Missed expected layer |",
        "|---|---|---|---|---|",
    ]
    for fault in f["faults"]:
        lines.append(
            f"| `{fault['fault_id']}` | {fault['expected_first_detector']} | {fault['observed_first_detector']} | "
            f"{fault['false_positive_before_expected']} | {fault['missed_at_expected']} |"
        )

    lines += [
        "",
        "## Provenance boundary",
        "",
        "The four closure-atlas entries are bound to the audited source artifact. The twenty reconstructed E25B equivalence triangles are calibration fixtures only and are excluded from real closure coverage. E25F uses synthetic faults only to validate detector separation.",
        "",
        "## Claim boundary",
        "",
        "A passing stage establishes deterministic closure accounting, evidence-prioritization, and layer-specific fault detection on the frozen component set. It does not establish whole-repository executable commutativity, automatic proof, or permission to promote graph semantics.",
    ]
    return "\n".join(lines) + "\n"
