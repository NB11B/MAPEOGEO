#!/usr/bin/env python3
"""MAPEOGEO Wave F2 / F2.1 — Commutation Manifest Generator.

Pre-registers all 32 Canonical Concepts, their Equivalence Contracts,
aligned Wave F1 Source Declarations, statement SHA-256 hashes, and
expected Commutation Verdicts.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUTPUT_PATH = ROOT / "formal" / "wave_f2_commutation_manifest.json"
ALIGNMENTS_PATH = ROOT / "formal" / "cross_source_alignments_v0_21_f1.json"
OPEN_LOGIC_PATH = ROOT / "formal" / "open_logic_manifest_v0_21.json"
OPEN_SET_PATH = ROOT / "formal" / "open_set_theory_manifest_v0_21.json"
LEVIN_PATH = ROOT / "formal" / "levin_discrete_manifest_v0_21.json"


def load_source_declarations_map() -> dict[str, dict[str, Any]]:
    decl_map: dict[str, dict[str, Any]] = {}
    for p in [OPEN_LOGIC_PATH, OPEN_SET_PATH, LEVIN_PATH]:
        if p.is_file():
            data = json.loads(p.read_text(encoding="utf-8"))
            for d in data.get("declarations", []):
                decl_map[d["node_id"]] = {
                    "statement_sha256": d.get("statement_sha256", ""),
                    "structural_refs": d.get("structural_refs", []),
                    "locator": d.get("locator", ""),
                    "label": d.get("label", ""),
                }
    return decl_map


def load_alignments_map() -> dict[str, list[str]]:
    align_map: dict[str, list[str]] = {}
    if ALIGNMENTS_PATH.is_file():
        data = json.loads(ALIGNMENTS_PATH.read_text(encoding="utf-8"))
        for a in data.get("alignments", []):
            cid = a["target_canonical_id"]
            sid = a["source_node_id"]
            if cid not in align_map:
                align_map[cid] = []
            if sid not in align_map[cid]:
                align_map[cid].append(sid)
    return align_map


def get_canonical_concepts_base() -> list[dict[str, Any]]:
    return [
        # --- Logic & Proof Theory (14) ---
        {
            "canonical_id": "canonical:logic:propositional_syntax_and_semantics",
            "name": "Propositional Logic Syntax and Valuation Semantics",
            "domain": "Logic & Proof Theory",
            "layer": "Logic & Proofs",
            "contract": "EXACT_MATCH",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "description": "Truth polynomial ring in F2[p,q] commutes with 2D hypercube cell partitioning.",
        },
        {
            "canonical_id": "canonical:logic:propositional_compactness_theorem",
            "name": "Propositional Compactness Theorem",
            "domain": "Logic & Proof Theory",
            "layer": "Logic & Proofs",
            "contract": "BOUNDED_MODEL_EQUIVALENCE",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "description": "Finite ideal intersection variety matches closed hypercube cell intersection.",
        },
        {
            "canonical_id": "canonical:logic:first_order_syntax_and_terms",
            "name": "First-Order Language, Terms, and Formulas",
            "domain": "Logic & Proof Theory",
            "layer": "Logic & Proofs",
            "contract": "ISOMORPHIC_WITNESS",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "description": "Free term algebraic substitution matches planar syntax tree substitution DAG.",
        },
        {
            "canonical_id": "canonical:logic:first_order_structures_and_satisfaction",
            "name": "First-Order Structures and Tarskian Satisfaction",
            "domain": "Logic & Proof Theory",
            "layer": "Logic & Proofs",
            "contract": "BOUNDED_MODEL_EQUIVALENCE",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "description": "Relational algebra evaluation matches relational directed graph model satisfaction.",
        },
        {
            "canonical_id": "canonical:logic:elementary_equivalence_substructures",
            "name": "Elementary Equivalence and Tarski-Vaught Criterion",
            "domain": "Logic & Proof Theory",
            "layer": "Logic & Proofs",
            "contract": "ISOMORPHIC_WITNESS",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "description": "Algebraic theory invariant agreement matches Ehrenfeucht-Fraïssé pebble game strategy.",
        },
        {
            "canonical_id": "canonical:logic:natural_deduction_and_sequent_calculus",
            "name": "Classical Proof Systems (Natural Deduction and Sequent Calculus LK)",
            "domain": "Logic & Proof Theory",
            "layer": "Logic & Proofs",
            "contract": "ISOMORPHIC_WITNESS",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "description": "LK sequent inference tensor matches planar proof tree acyclic DAG.",
        },
        {
            "canonical_id": "canonical:logic:gentzen_cut_elimination",
            "name": "Gentzen's Cut-Elimination Hauptsatz and Subformula Property",
            "domain": "Logic & Proof Theory",
            "layer": "Logic & Proofs",
            "contract": "ISOMORPHIC_WITNESS",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "description": "Term rewriting cut rank reduction matches proof tree homotopy contraction.",
        },
        {
            "canonical_id": "canonical:logic:first_order_soundness_theorem",
            "name": "Soundness Theorem for First-Order Logic",
            "domain": "Logic & Proof Theory",
            "layer": "Logic & Proofs",
            "contract": "EXACT_MATCH",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "description": "Syntactic derivability preservation matches topological model validity embedding.",
        },
        {
            "canonical_id": "canonical:logic:first_order_completeness_theorem",
            "name": "Gödel's First-Order Completeness Theorem",
            "domain": "Logic & Proof Theory",
            "layer": "Logic & Proofs",
            "contract": "PARTIAL_ONE_SIDED",
            "expected_verdict": "PARTIAL_ONE_SIDED_REALIZATION",
            "description": "Algebraic sequent calculus is constructive, but full infinite Henkin term model requires transfinite witness.",
        },
        {
            "canonical_id": "canonical:logic:first_order_compactness_theorem",
            "name": "First-Order Compactness Theorem",
            "domain": "Logic & Proof Theory",
            "layer": "Logic & Proofs",
            "contract": "UNSUPPORTED_INFINITE",
            "expected_verdict": "OUTSIDE_CURRENT_EXECUTABLE_SCOPE",
            "description": "Unbounded infinite compactness requires non-constructive ultrafilters outside finite executable scope.",
        },
        {
            "canonical_id": "canonical:logic:lowenheim_skolem_theorems",
            "name": "Downward and Upward Löwenheim-Skolem Theorems",
            "domain": "Logic & Proof Theory",
            "layer": "Logic & Proofs",
            "contract": "BOUNDED_MODEL_EQUIVALENCE",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "description": "Skolem hull algebraic closure matches induced sub-hypergraph elementary embedding.",
        },
        {
            "canonical_id": "canonical:computability:turing_machines_and_computability",
            "name": "Turing Machines and Computable Functions",
            "domain": "Logic & Proof Theory",
            "layer": "Logic & Proofs",
            "contract": "EXACT_MATCH",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "description": "Transition monoid trace matches 2D spacetime grid computation lattice.",
        },
        {
            "canonical_id": "canonical:computability:halting_problem_undecidability",
            "name": "Undecidability of the Halting Problem and Church-Turing Thesis",
            "domain": "Logic & Proof Theory",
            "layer": "Logic & Proofs",
            "contract": "UNSUPPORTED_INFINITE",
            "expected_verdict": "OUTSIDE_CURRENT_EXECUTABLE_SCOPE",
            "description": "Halting problem undecidability is an inherently non-computable infinite decision barrier.",
        },
        {
            "canonical_id": "canonical:logic:first_order_undecidability_and_incompleteness",
            "name": "Church-Turing FOL Undecidability and Gödel's Incompleteness Theorems",
            "domain": "Logic & Proof Theory",
            "layer": "Logic & Proofs",
            "contract": "UNSUPPORTED_INFINITE",
            "expected_verdict": "OUTSIDE_CURRENT_EXECUTABLE_SCOPE",
            "description": "Gödel incompleteness is a metamathematical limit on formal proof systems outside finite dual execution.",
        },

        # --- Set Theory (7) ---
        {
            "canonical_id": "canonical:sets:zfc_axioms_core",
            "name": "Zermelo-Fraenkel Set Theory Axiom System (ZF/ZFC)",
            "domain": "Set Theory",
            "layer": "Set Theory",
            "contract": "HOMOLOGY_EQUIVALENCE",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "description": "Hereditary epsilon membership matrix matches cumulative hierarchy V_3 tree.",
        },
        {
            "canonical_id": "canonical:sets:relations_and_quotients",
            "name": "Binary Relations, Equivalence Classes, and Quotient Sets",
            "domain": "Set Theory",
            "layer": "Set Theory",
            "contract": "EXACT_MATCH",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "description": "Equivalence relation matrix rank matches geometric disjoint cluster partition.",
        },
        {
            "canonical_id": "canonical:sets:functions_and_well_foundedness",
            "name": "Functions and Well-Founded Relations",
            "domain": "Set Theory",
            "layer": "Set Theory",
            "contract": "HOMOLOGY_EQUIVALENCE",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "description": "Strictly upper-triangular nilpotent matrix matches topological sort DAG.",
        },
        {
            "canonical_id": "canonical:sets:cardinality_and_cantor_theorem",
            "name": "Cardinality, Countability, and Cantor's Theorem",
            "domain": "Set Theory",
            "layer": "Set Theory",
            "contract": "ISOMORPHIC_WITNESS",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "description": "Cantor diagonal polynomial exclusion matches bipartite grid diagonal separation.",
        },
        {
            "canonical_id": "canonical:sets:cantor_schroder_bernstein_theorem",
            "name": "Cantor-Schröder-Bernstein (CSB) Theorem",
            "domain": "Set Theory",
            "layer": "Set Theory",
            "contract": "ISOMORPHIC_WITNESS",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "description": "CSB orbit functional iteration matches bipartite alternating reachability graph.",
        },
        {
            "canonical_id": "canonical:sets:von_neumann_ordinals_and_transfinite_induction",
            "name": "Von Neumann Ordinals, Transfinite Induction and Recursion",
            "domain": "Set Theory",
            "layer": "Set Theory",
            "contract": "HOMOLOGY_EQUIVALENCE",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "description": "Transitive ordinal successor algebra matches linear tournament simplicial chain.",
        },
        {
            "canonical_id": "canonical:sets:axiom_of_choice_equivalents",
            "name": "Axiom of Choice and Equivalent Principles",
            "domain": "Set Theory",
            "layer": "Set Theory",
            "contract": "UNSUPPORTED_INFINITE",
            "expected_verdict": "OUTSIDE_CURRENT_EXECUTABLE_SCOPE",
            "description": "Arbitrary infinite family choice function lacks constructive finite witness and is independent of ZF.",
        },

        # --- Discrete Mathematics & Combinatorics (11) ---
        {
            "canonical_id": "canonical:discrete:mathematical_induction_principles",
            "name": "Mathematical Induction Principles and Well-Ordering",
            "domain": "Discrete Mathematics & Combinatorics",
            "layer": "Elementary Arithmetic & Algebra",
            "contract": "HOMOLOGY_EQUIVALENCE",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "description": "Algebraic inductive polynomial identity matches linear chain poset connectivity.",
        },
        {
            "canonical_id": "canonical:discrete:recurrence_relations",
            "name": "Linear Recurrence Relations and Divide-and-Conquer Recurrences",
            "domain": "Discrete Mathematics & Combinatorics",
            "layer": "Elementary Arithmetic & Algebra",
            "contract": "EXACT_MATCH",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "description": "Companion matrix recurrence powers match 2D phase-space trajectory vertices.",
        },
        {
            "canonical_id": "canonical:discrete:combinatorial_counting_principles",
            "name": "Combinatorial Enumeration Principles",
            "domain": "Discrete Mathematics & Combinatorics",
            "layer": "Elementary Arithmetic & Algebra",
            "contract": "EXACT_MATCH",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "description": "Binomial polynomial expansion matches Pascal simplicial grid lattice paths.",
        },
        {
            "canonical_id": "canonical:discrete:pigeonhole_and_inclusion_exclusion",
            "name": "Pigeonhole Principle and Principle of Inclusion-Exclusion (PIE)",
            "domain": "Discrete Mathematics & Combinatorics",
            "layer": "Elementary Arithmetic & Algebra",
            "contract": "EXACT_MATCH",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "description": "PIE alternating sum formula matches geometric Venn spatial volume partition.",
        },
        {
            "canonical_id": "canonical:discrete:generating_functions_and_catalan",
            "name": "Generating Functions and Catalan Numbers",
            "domain": "Discrete Mathematics & Combinatorics",
            "layer": "Elementary Arithmetic & Algebra",
            "contract": "EXACT_MATCH",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "description": "Catalan formal power series convolution matches monotonic Dyck grid paths in Z^2.",
        },
        {
            "canonical_id": "canonical:discrete:graph_fundamentals_and_handshaking",
            "name": "Graph Fundamentals and Euler's Handshaking Lemma",
            "domain": "Discrete Mathematics & Combinatorics",
            "layer": "Euclidean Geometry & Trigonometry",
            "contract": "HOMOLOGY_EQUIVALENCE",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "description": "Algebraic degree sum 1^T A 1 matches simplicial 1-complex boundary incidence d_1.",
        },
        {
            "canonical_id": "canonical:discrete:trees_and_spanning_trees",
            "name": "Trees, Characterizations, and Spanning Trees",
            "domain": "Discrete Mathematics & Combinatorics",
            "layer": "Euclidean Geometry & Trigonometry",
            "contract": "EXACT_MATCH",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "description": "Matrix-Tree theorem Laplacian determinant matches simplicial spanning tree count.",
        },
        {
            "canonical_id": "canonical:discrete:bipartite_graphs_and_matching",
            "name": "Bipartite Graphs, 2-Colorability, and Hall's Marriage Theorem",
            "domain": "Discrete Mathematics & Combinatorics",
            "layer": "Euclidean Geometry & Trigonometry",
            "contract": "ISOMORPHIC_WITNESS",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "description": "Symmetric adjacency spectrum matches bipartite 2-coloring partition and matching.",
        },
        {
            "canonical_id": "canonical:discrete:planarity_and_eulers_formula",
            "name": "Planar Graphs, Plane Embeddings, and Euler's Planar Formula",
            "domain": "Discrete Mathematics & Combinatorics",
            "layer": "Euclidean Geometry & Trigonometry",
            "contract": "HOMOLOGY_EQUIVALENCE",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "description": "Cycle space rank dim(C) = E - V + 1 matches planar cell complex Euler formula V - E + F = 2.",
        },
        {
            "canonical_id": "canonical:discrete:graph_coloring_theorems",
            "name": "Graph Vertex Coloring, Four Color and Five Color Theorems",
            "domain": "Discrete Mathematics & Combinatorics",
            "layer": "Euclidean Geometry & Trigonometry",
            "contract": "EXACT_MATCH",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "description": "Chromatic polynomial evaluation matches proper vertex coloring partition.",
        },
        {
            "canonical_id": "canonical:discrete:traversal_euler_and_hamilton",
            "name": "Euler Paths/Circuits and Dirac's Hamiltonian Theorem",
            "domain": "Discrete Mathematics & Combinatorics",
            "layer": "Euclidean Geometry & Trigonometry",
            "contract": "EXACT_MATCH",
            "expected_verdict": "VERIFIED_BOUNDED_CONTRACT_COMMUTATION",
            "description": "Eulerian degree parity algebraic condition matches closed 1-cycle edge traversal.",
        },
    ]


def generate_manifest() -> dict[str, Any]:
    concepts = get_canonical_concepts_base()
    decl_map = load_source_declarations_map()
    align_map = load_alignments_map()

    contracts_count: dict[str, int] = {}
    verdicts_count: dict[str, int] = {}

    enriched_concepts: list[dict[str, Any]] = []

    for c in concepts:
        cid = c["canonical_id"]
        ctr = c["contract"]
        v = c["expected_verdict"]
        contracts_count[ctr] = contracts_count.get(ctr, 0) + 1
        verdicts_count[v] = verdicts_count.get(v, 0) + 1

        aligned_sids = sorted(align_map.get(cid, []))
        aligned_hashes: list[str] = []
        bound_deps: list[str] = []

        for sid in aligned_sids:
            d_info = decl_map.get(sid, {})
            h = d_info.get("statement_sha256")
            if h:
                aligned_hashes.append(h)
            for ref in d_info.get("structural_refs", []):
                if ref not in bound_deps:
                    bound_deps.append(ref)

        entry = dict(c)
        entry["aligned_source_node_ids"] = aligned_sids
        entry["aligned_statement_sha256s"] = aligned_hashes
        entry["bound_dependencies"] = sorted(bound_deps)
        enriched_concepts.append(entry)

    return {
        "schema_version": "0.21",
        "stage": "v0.21_wave_f2",
        "campaign_name": "EO_GEO_DUAL_VIEW_COMMUTATION_AUDIT",
        "total_canonical_concepts": len(enriched_concepts),
        "contracts_breakdown": contracts_count,
        "expected_verdicts_breakdown": verdicts_count,
        "target_concepts": enriched_concepts,
    }


def main() -> int:
    manifest = generate_manifest()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Successfully generated Wave F2.1 manifest: {OUTPUT_PATH}")
    print(f"Total concepts: {manifest['total_canonical_concepts']}")
    print(f"Expected verdicts: {manifest['expected_verdicts_breakdown']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
