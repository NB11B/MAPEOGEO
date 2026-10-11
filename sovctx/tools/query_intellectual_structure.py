from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sovctx.node.intellectual_audit import IntellectualStructureAuditor


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Query SOVCTX Intellectual Structure & Motif Matrix")
    parser.add_argument("--matrix", action="store_true", help="Display the Core Mathematical Motif Matrix")
    parser.add_argument("--audit", action="store_true", help="Display quantitative audit metrics (centrality, bridges)")
    parser.add_argument("--summary", action="store_true", help="Display cross-school operator connections and transfer claims")
    args = parser.parse_args()

    # Default to matrix if no specific action provided
    show_matrix = args.matrix or (not args.audit and not args.summary)
    show_audit = args.audit
    show_summary = args.summary

    auditor = IntellectualStructureAuditor()

    if show_matrix:
        matrix = auditor.build_core_motif_matrix()
        print("=========================================================================================")
        print("                        CORE MATHEMATICAL MOTIF MATRIX")
        print("=========================================================================================")
        for m in matrix:
            print(f"\n[MOTIF] {m.motif}")
            print(f"  Schools     : {', '.join(m.schools)}")
            print(f"  Earliest Yr : {m.earliest_evidence_year} | Recurrence: {m.cross_school_recurrence} | Confidence: {m.evidentiary_confidence}")
            print(f"  Essence     : {m.epistemic_essence}")
            print(f"  Documented  : {'; '.join(m.engineering_descendants_documented)}")
            if m.engineering_descendants_candidate:
                print(f"  Candidates  : {'; '.join(m.engineering_descendants_candidate)}")

    if show_audit:
        centrality = auditor.compute_term_centrality()
        bridges = auditor.compute_institutional_bridges()
        print("\n=========================================================================================")
        print("                  QUANTITATIVE TERM CENTRALITY & INSTITUTIONAL BRIDGES")
        print("=========================================================================================")
        print("\n--- Top Cross-School Native Terms ---")
        for t in centrality[:8]:
            print(f"  Rank {t.centrality_rank}: `{t.native_term}` ({t.english_concept}) - {t.school_count} schools, {t.equation_count} eq connections")
        print("\n--- Key Institutional Bridges (Theory <-> Engineering) ---")
        for b in bridges:
            print(f"  [{b.bridge_score}/10] {b.institution_name} ({b.city})")
            print(f"         Pure: {'; '.join(b.pure_math_connections[:2])}")
            print(f"         Eng : {'; '.join(b.engineering_domain_connections[:2])}")

    if show_summary:
        graph_dir = REPO_ROOT / "sovctx" / "graph"
        atlas_dir = REPO_ROOT / "sovctx" / "operator_atlas"

        equations = load_jsonl(graph_dir / "equations.jsonl")
        eq_families = load_jsonl(graph_dir / "equation_families.jsonl")
        claims = load_jsonl(graph_dir / "claims.jsonl")
        edges = load_jsonl(graph_dir / "edges.jsonl")
        operators = load_jsonl(atlas_dir / "operators.jsonl")

        print(f"\nLoaded: {len(equations)} equations, {len(eq_families)} equation families, {len(claims)} claims, {len(edges)} edges, {len(operators)} operators")

        eq_to_family = {}
        eq_to_operators = defaultdict(list)
        for e in edges:
            etype = e.get("edge_type")
            src = e.get("source")
            tgt = e.get("target")
            if etype == "MEMBER_OF_EQUATION_FAMILY":
                eq_to_family[src] = tgt
            elif etype in ("IMPLEMENTS_OPERATOR", "USES_OPERATOR"):
                eq_to_operators[src].append(tgt)

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
                for op in eq_to_operators.get(eq, []):
                    ops.add(op)
            for e in edges:
                if e.get("source") == fam_id and e.get("edge_type") in ("IMPLEMENTS_OPERATOR", "USES_OPERATOR"):
                    ops.add(e.get("target"))

            family_operators[fam_id] = ops
            print(f"\n[{fam_id}] {label}")
            print(f"  Focus Behaviors : {', '.join(focus)}")
            print(f"  Equations ({len(eqs)})  : {', '.join(eqs)}")
            print(f"  Linked Operators: {', '.join(sorted(ops)) if ops else 'Pending extraction'}")

        op_to_families = defaultdict(set)
        for fam_id, ops in family_operators.items():
            for op in ops:
                op_to_families[op].add(fam_id)

        print("\n--- OPERATORS SHARED ACROSS MULTIPLE SCHOOLS ---")
        for op, fams in sorted(op_to_families.items(), key=lambda x: len(x[1]), reverse=True):
            if len(fams) > 1:
                print(f"  {op:<25} shared by ({len(fams)} schools): {', '.join(sorted(fams))}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
