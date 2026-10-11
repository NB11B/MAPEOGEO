from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def main():
    graph_dir = REPO_ROOT / "sovctx" / "graph"
    atlas_dir = REPO_ROOT / "sovctx" / "operator_atlas"

    equations = load_jsonl(graph_dir / "equations.jsonl")
    eq_families = load_jsonl(graph_dir / "equation_families.jsonl")
    claims = load_jsonl(graph_dir / "claims.jsonl")
    edges = load_jsonl(graph_dir / "edges.jsonl")
    operators = load_jsonl(atlas_dir / "operators.jsonl")
    invariants = load_jsonl(graph_dir / "invariants.jsonl")
    assumptions = load_jsonl(graph_dir / "assumptions.jsonl")

    print(f"Loaded: {len(equations)} equations, {len(eq_families)} equation families, {len(claims)} claims, {len(edges)} edges, {len(operators)} operators")

    # 1. School to Operators mapping
    # An equation belongs to a family, and implements an operator
    eq_to_family = {}
    eq_to_operators = defaultdict(list)
    eq_to_invariants = defaultdict(list)
    eq_to_assumptions = defaultdict(list)

    for e in edges:
        etype = e.get("edge_type")
        src = e.get("source")
        tgt = e.get("target")
        if etype == "MEMBER_OF_EQUATION_FAMILY":
            eq_to_family[src] = tgt
        elif etype in ("IMPLEMENTS_OPERATOR", "USES_OPERATOR"):
            eq_to_operators[src].append((etype, tgt))
        elif etype == "PRESERVES_INVARIANT":
            eq_to_invariants[src].append(tgt)
        elif etype == "HAS_ASSUMPTION":
            eq_to_assumptions[src].append(tgt)

    # Group by family
    family_to_equations = defaultdict(list)
    for eq_id, fam_id in eq_to_family.items():
        family_to_equations[fam_id].append(eq_id)

    print("\n=== AXIS B: CROSS-SCHOOL MATHEMATICAL MOTIFS & OPERATORS ===")
    family_operators = defaultdict(set)
    for fam in eq_families:
        fam_id = fam["id"]
        label = fam.get("label", "")
        focus = fam.get("behavior_focus", [])
        eqs = family_to_equations.get(fam_id, [])
        ops = set()
        for eq in eqs:
            for et, op in eq_to_operators.get(eq, []):
                ops.add(op)
        # also check edges directly from family or source
        for e in edges:
            if e.get("source") == fam_id and e.get("edge_type") in ("IMPLEMENTS_OPERATOR", "USES_OPERATOR"):
                ops.add(e.get("target"))

        family_operators[fam_id] = ops
        print(f"\n[{fam_id}] {label}")
        print(f"  Focus Behaviors : {', '.join(focus)}")
        print(f"  Equations ({len(eqs)})  : {', '.join(eqs)}")
        print(f"  Linked Operators: {', '.join(sorted(ops)) if ops else 'Pending extraction'}")

    # Find shared operators across schools
    op_to_families = defaultdict(set)
    for fam_id, ops in family_operators.items():
        for op in ops:
            op_to_families[op].add(fam_id)

    print("\n--- OPERATORS SHARED ACROSS MULTIPLE SCHOOLS ---")
    for op, fams in sorted(op_to_families.items(), key=lambda x: len(x[1]), reverse=True):
        if len(fams) > 1:
            print(f"  {op:<25} shared by ({len(fams)} schools): {', '.join(sorted(fams))}")

    print("\n=== AXIS C: SCIENCE-TO-ENGINEERING TRANSFER CHAINS IN GRAPH ===")
    app_claims = []
    for c in claims:
        lbl = c.get("label", "")
        cid = c.get("id", "")
        # look for engineering terms
        app_keywords = [
            "radiating", "antenna", "control", "stability", "mechanism", "radar", 
            "physiological", "self-organizing", "search", "spectral", "scatter",
            "oscillator", "plasma", "ill-posed", "regulariz"
        ]
        if any(kw in lbl.lower() for kw in app_keywords):
            app_claims.append((cid, lbl, c.get("source_ids", [])))

    for cid, lbl, srcs in app_claims:
        print(f"  [{cid}]")
        print(f"    Claim  : {lbl}")
        print(f"    Sources: {', '.join(srcs)}")

if __name__ == "__main__":
    main()
