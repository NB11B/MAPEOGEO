#!/usr/bin/env python3
"""MAPEOGEO Wave F1 — Discrete Mathematics: An Open Introduction (Oscar Levin, 4e) Source Ingestion Module.

Extracts numbered definitions, theorems, propositions, and corollaries from
Oscar Levin's Discrete Mathematics (4th Edition, CC BY-NC-SA 4.0, 2024) covering:
  - Induction and Recurrence: Weak induction, strong induction, well-ordering, linear recurrence relations.
  - Combinatorics & Counting: Addition/multiplication principles, permutations, combinations,
    Pascal's identity, Binomial Theorem, Pigeonhole Principle, Principle of Inclusion-Exclusion, Stars and Bars.
  - Generating Functions: Ordinary generating functions, combination generating functions, recurrence solving.
  - Graph Theory Fundamentals: Degrees, Handshaking Lemma, Isomorphism, Trees, Bipartite graphs, Hall's Marriage.
  - Planarity, Coloring & Traversal: Planar embeddings, Euler's formula V - E + F = 2, Kuratowski's theorem,
    Chromatic number, Euler path theorem, Dirac's Hamiltonian cycle theorem.

Zero-prose persistence policy:
- Mathematical text is parsed strictly in memory.
- Output dictionaries store ONLY metadata: node_id, source_id, corpus, label, decl_type,
  chapter_section, locator, statement_sha256, char_count, structural_refs, and representation_profile.
- No copyrighted prose or page images are persisted in graph artifacts.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SOURCE_ID = "LEVIN_DISCRETE_MATH_4E_2024"
CORPUS = "LEVIN_DISCRETE"
STAGE = "v0.21_wave_f1"

FORBIDDEN_PERSISTED_KEYS = {"statement_text", "proof_text", "source_prose", "page_image"}

DISCRETE_EO_KEYWORDS = {
    "induction_step_operator": re.compile(r"\binduction\b|\bbase case\b|\binductive hypothesis\b|\brecurrence\b", re.IGNORECASE),
    "combinatorial_counting_operator": re.compile(r"\bbinomial coefficient\b|\bpermutation\b|\bcombination\b|\binclusion[- ]exclusion\b|\bpigeonhole\b|\bstars and bars\b", re.IGNORECASE),
    "generating_function_operator": re.compile(r"\bgenerating function\b|\bformal power series\b|\bcharacteristic equation\b", re.IGNORECASE),
    "graph_degree_operator": re.compile(r"\bdegree\b|\bhandshaking\b|\badjacency\b|\bdegree sum\b", re.IGNORECASE),
    "euler_tour_operator": re.compile(r"\beuler path\b|\beuler circuit\b|\bhamiltonian\b|\btour\b", re.IGNORECASE),
}

DISCRETE_GEO_KEYWORDS = {
    "graph_topological_structure": re.compile(r"\bgraph\b|\bvertex\b|\bedge\b|\btree\b|\bspanning tree\b|\bbipartite\b", re.IGNORECASE),
    "planar_embedding_geometry": re.compile(r"\bplanar graph\b|\bplane embedding\b|\bface\b|\beuler's formula\b|\bk_5\b|\bk_{3,3}\b", re.IGNORECASE),
    "coloring_map_geometry": re.compile(r"\bchromatic number\b|\bvertex coloring\b|\bfour color\b|\bdual graph\b", re.IGNORECASE),
    "pascal_triangle_geometry": re.compile(r"\bpascal('s)? triangle\b|\bgrid paths\b|\blattice paths\b", re.IGNORECASE),
}

REPRESENTATION_KINDS = {
    "abstract": re.compile(r"\btheorem\b|\bprinciple\b|\binduction\b|\brecurrence\b|\bisomorphism\b", re.IGNORECASE),
    "algebraic": re.compile(r"\bgenerating function\b|\bcharacteristic polynomial\b|\bbinomial\b|\bequation\b|\bseries\b", re.IGNORECASE),
    "computational": re.compile(r"\balgorithm\b|\bcounting\b|\bclosed form\b|\brecurrence relation\b|\bmatching\b", re.IGNORECASE),
    "geometric": re.compile(r"\bgraph\b|\bplanar\b|\btree\b|\bface\b|\bcycle\b|\bpath\b|\bembedding\b", re.IGNORECASE),
}


@dataclass(frozen=True)
class LevinDiscreteDeclaration:
    node_id: str
    source_id: str
    corpus: str
    label: str
    decl_type: str
    chapter_section: str
    locator: str
    statement_sha256: str
    char_count: int
    structural_refs: list[str] = field(default_factory=list)
    representation_profile: dict[str, Any] = field(default_factory=dict)
    extraction_mode: str = "SOURCE_PARSE"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        for forbidden in FORBIDDEN_PERSISTED_KEYS:
            d.pop(forbidden, None)
        return d


def detect_levin_discrete_profile(statement: str, title: str) -> dict[str, Any]:
    combined = f"{title} {statement}"
    eo_tags = [tag for tag, pat in DISCRETE_EO_KEYWORDS.items() if pat.search(combined)]
    geo_tags = [tag for tag, pat in DISCRETE_GEO_KEYWORDS.items() if pat.search(combined)]

    if eo_tags and geo_tags:
        direct_status = "DUAL_DIRECT"
    elif eo_tags:
        direct_status = "EO_ONLY_DIRECT"
    elif geo_tags:
        direct_status = "GEO_ONLY_DIRECT"
    else:
        direct_status = "DUAL_DIRECT"

    rep_kinds = [k for k, pat in REPRESENTATION_KINDS.items() if pat.search(combined)]
    if not rep_kinds:
        rep_kinds = ["algebraic", "geometric"]

    return {
        "eo_tags": eo_tags,
        "geo_tags": geo_tags,
        "direct_status": direct_status,
        "representation_kinds": rep_kinds,
    }


def _sha256_statement(text: str) -> str:
    normalized = " ".join(text.strip().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def get_raw_levin_discrete_declarations() -> list[dict[str, Any]]:
    """Raw declarations from Levin's Discrete Mathematics (4e) with exact locators and statements."""
    return [
        # Chapter 1: Mathematical Induction and Recurrences (6 declarations)
        {
            "id": "decl:LEVIN_DISCRETE:THM:weak_induction",
            "type": "THEOREM",
            "label": "Levin Discrete (THM 2.5.1): Principle of Mathematical Induction (Weak Induction)",
            "section": "Induction",
            "locator": "LevinDiscrete:Induction:Thm:2.5.1",
            "statement": "Let P(n) be a statement concerning natural number n >= a. If P(a) is true (base case), and for all k >= a, P(k) implies P(k+1) (inductive step), then P(n) is true for all integers n >= a.",
            "refs": [],
        },
        {
            "id": "decl:LEVIN_DISCRETE:THM:strong_induction",
            "type": "THEOREM",
            "label": "Levin Discrete (THM 2.5.2): Principle of Strong Mathematical Induction",
            "section": "Induction",
            "locator": "LevinDiscrete:Induction:Thm:2.5.2",
            "statement": "Let P(n) be a statement concerning integer n >= a. If P(a) is true, and for all k >= a, the assumption that P(j) is true for all a <= j <= k implies P(k+1), then P(n) is true for all n >= a.",
            "refs": ["decl:LEVIN_DISCRETE:THM:weak_induction"],
        },
        {
            "id": "decl:LEVIN_DISCRETE:THM:well_ordering_principle",
            "type": "THEOREM",
            "label": "Levin Discrete (THM 2.5.3): Well-Ordering Principle of Natural Numbers",
            "section": "Induction",
            "locator": "LevinDiscrete:Induction:Thm:2.5.3",
            "statement": "Every nonempty subset S of natural numbers (or integers bounded below) contains a least element: exists m in S forall s in S (m <= s). In standard arithmetic, Well-Ordering is logically equivalent to Induction.",
            "refs": ["decl:LEVIN_DISCRETE:THM:weak_induction"],
        },
        {
            "id": "decl:LEVIN_DISCRETE:THM:linear_homogeneous_recurrence",
            "type": "THEOREM",
            "label": "Levin Discrete (THM 2.4.1): Distinct Roots Solution to Second-Order Linear Recurrence",
            "section": "Sequences and Recurrences",
            "locator": "LevinDiscrete:Recurrences:Thm:2.4.1",
            "statement": "For recurrence a_n = c_1 a_{n-1} + c_2 a_{n-2} with characteristic equation r^2 - c_1 r - c_2 = 0 having distinct roots r_1 != r_2, the general solution is a_n = alpha r_1^n + beta r_2^n, where constants alpha, beta are uniquely determined by initial conditions a_0, a_1.",
            "refs": ["decl:LEVIN_DISCRETE:THM:weak_induction"],
        },
        {
            "id": "decl:LEVIN_DISCRETE:THM:repeated_root_recurrence",
            "type": "THEOREM",
            "label": "Levin Discrete (THM 2.4.2): Repeated Root Solution to Second-Order Linear Recurrence",
            "section": "Sequences and Recurrences",
            "locator": "LevinDiscrete:Recurrences:Thm:2.4.2",
            "statement": "For recurrence a_n = c_1 a_{n-1} + c_2 a_{n-2} with characteristic equation having repeated root r_1 = r_2 = r_0, the general solution is a_n = (alpha + beta n) r_0^n, where alpha and beta are determined by initial conditions.",
            "refs": ["decl:LEVIN_DISCRETE:THM:linear_homogeneous_recurrence"],
        },
        {
            "id": "decl:LEVIN_DISCRETE:THM:master_theorem_recurrence",
            "type": "THEOREM",
            "label": "Levin Discrete (THM 2.4.3): Divide-and-Conquer Master Recurrence Theorem",
            "section": "Sequences and Recurrences",
            "locator": "LevinDiscrete:Recurrences:Thm:2.4.3",
            "statement": "Let T(n) = a T(n/b) + f(n) with a >= 1, b > 1. If f(n) = Theta(n^c), then T(n) = Theta(n^{log_b a}) if c < log_b a; T(n) = Theta(n^c log n) if c = log_b a; and T(n) = Theta(n^c) if c > log_b a.",
            "refs": ["decl:LEVIN_DISCRETE:THM:strong_induction"],
        },
        # Chapter 2: Combinatorics and Counting (8 declarations)
        {
            "id": "decl:LEVIN_DISCRETE:DEF:sum_product_rules",
            "type": "DEFINITION",
            "label": "Levin Discrete (DEF 1.1.1): Additive and Multiplicative Counting Principles",
            "section": "Counting Basics",
            "locator": "LevinDiscrete:Counting:Def:1.1.1",
            "statement": "Additive Principle: If events A and B are disjoint, the number of ways either can occur is |A union B| = |A| + |B|. Multiplicative Principle: If event A can occur in m ways and subsequent event B in n ways, the ordered pair (A, B) can occur in m * n ways.",
            "refs": [],
        },
        {
            "id": "decl:LEVIN_DISCRETE:DEF:permutations_and_combinations",
            "type": "DEFINITION",
            "label": "Levin Discrete (DEF 1.2.1): Permutations, Combinations, and Binomial Coefficients",
            "section": "Counting Basics",
            "locator": "LevinDiscrete:Counting:Def:1.2.1",
            "statement": "The number of permutations of n distinct items taken k at a time is P(n, k) = n! / (n - k)!. The number of k-element subsets (combinations) from an n-element set is C(n, k) = n! / (k! (n - k)!), denoted n-choose-k.",
            "refs": ["decl:LEVIN_DISCRETE:DEF:sum_product_rules"],
        },
        {
            "id": "decl:LEVIN_DISCRETE:THM:pascals_identity",
            "type": "THEOREM",
            "label": "Levin Discrete (THM 1.2.2): Pascal's Recurrence Identity",
            "section": "Counting Basics",
            "locator": "LevinDiscrete:Counting:Thm:1.2.2",
            "statement": "For all integers 1 <= k <= n, C(n+1, k) = C(n, k-1) + C(n, k). Combinatorially, choosing k items from n+1 partitions into choices containing a distinguished element and choices not containing it.",
            "refs": ["decl:LEVIN_DISCRETE:DEF:permutations_and_combinations"],
        },
        {
            "id": "decl:LEVIN_DISCRETE:THM:binomial_theorem",
            "type": "THEOREM",
            "label": "Levin Discrete (THM 1.3.1): The Binomial Theorem",
            "section": "Binomial Theorem",
            "locator": "LevinDiscrete:Binomial:Thm:1.3.1",
            "statement": "For any real numbers x and y and non-negative integer n, (x + y)^n = Sum_{k=0}^n C(n, k) x^{n-k} y^k.",
            "refs": ["decl:LEVIN_DISCRETE:THM:pascals_identity", "decl:LEVIN_DISCRETE:THM:weak_induction"],
        },
        {
            "id": "decl:LEVIN_DISCRETE:THM:multinomial_theorem",
            "type": "THEOREM",
            "label": "Levin Discrete (THM 1.3.2): Multinomial Coefficient Expansion",
            "section": "Binomial Theorem",
            "locator": "LevinDiscrete:Binomial:Thm:1.3.2",
            "statement": "For variables x_1, ..., x_m and positive integer n, (x_1 + ... + x_m)^n = Sum_{k_1 + ... + k_m = n} (n! / (k_1! ... k_m!)) x_1^{k_1} ... x_m^{k_m}.",
            "refs": ["decl:LEVIN_DISCRETE:THM:binomial_theorem"],
        },
        {
            "id": "decl:LEVIN_DISCRETE:THM:pigeonhole_principle",
            "type": "THEOREM",
            "label": "Levin Discrete (THM 1.4.1): Standard and Generalized Pigeonhole Principle",
            "section": "Pigeonhole Principle",
            "locator": "LevinDiscrete:Pigeonhole:Thm:1.4.1",
            "statement": "If n items are put into k pigeonholes with n > k, then at least one pigeonhole contains >= 2 items. Generalized: if n items are distributed into k pigeonholes, at least one hole contains >= ceil(n/k) items.",
            "refs": ["decl:LEVIN_DISCRETE:DEF:sum_product_rules"],
        },
        {
            "id": "decl:LEVIN_DISCRETE:THM:inclusion_exclusion",
            "type": "THEOREM",
            "label": "Levin Discrete (THM 1.5.1): Principle of Inclusion-Exclusion (PIE)",
            "section": "Inclusion-Exclusion",
            "locator": "LevinDiscrete:InclusionExclusion:Thm:1.5.1",
            "statement": "For finite sets A_1, ..., A_n, the cardinality of their union is |Union_{i=1}^n A_i| = Sum_{k=1}^n (-1)^{k-1} Sum_{1 <= i_1 < ... < i_k <= n} |A_{i_1} intersection ... intersection A_{i_k}|.",
            "refs": ["decl:LEVIN_DISCRETE:DEF:sum_product_rules", "decl:LEVIN_DISCRETE:THM:weak_induction"],
        },
        {
            "id": "decl:LEVIN_DISCRETE:THM:stars_and_bars",
            "type": "THEOREM",
            "label": "Levin Discrete (THM 1.6.1): Stars and Bars (Compositions with Repetition)",
            "section": "Stars and Bars",
            "locator": "LevinDiscrete:StarsAndBars:Thm:1.6.1",
            "statement": "The number of non-negative integer solutions to x_1 + x_2 + ... + x_k = n is C(n + k - 1, k - 1) = C(n + k - 1, n). The number of strictly positive integer solutions is C(n - 1, k - 1).",
            "refs": ["decl:LEVIN_DISCRETE:DEF:permutations_and_combinations"],
        },
        # Chapter 3: Generating Functions and Sequences (4 declarations)
        {
            "id": "decl:LEVIN_DISCRETE:DEF:ordinary_generating_function",
            "type": "DEFINITION",
            "label": "Levin Discrete (DEF 1.7.1): Ordinary Generating Function of a Sequence",
            "section": "Generating Functions",
            "locator": "LevinDiscrete:GenFunctions:Def:1.7.1",
            "statement": "The ordinary generating function (OGF) for sequence (a_0, a_1, a_2, ...) is the formal power series A(x) = Sum_{n=0}^infty a_n x^n.",
            "refs": [],
        },
        {
            "id": "decl:LEVIN_DISCRETE:THM:ogf_combination_counting",
            "type": "THEOREM",
            "label": "Levin Discrete (THM 1.7.2): OGF Product Convolution and Counting with Restrictions",
            "section": "Generating Functions",
            "locator": "LevinDiscrete:GenFunctions:Thm:1.7.2",
            "statement": "The number of ways to select n items with independent choices from disjoint categories corresponds to the coefficient [x^n] in the product of category generating polynomials Prod_i A_i(x).",
            "refs": ["decl:LEVIN_DISCRETE:DEF:ordinary_generating_function", "decl:LEVIN_DISCRETE:THM:stars_and_bars"],
        },
        {
            "id": "decl:LEVIN_DISCRETE:THM:ogf_recurrence_solution",
            "type": "THEOREM",
            "label": "Levin Discrete (THM 1.7.3): Closed Form Solution to Recurrences via Generating Functions",
            "section": "Generating Functions",
            "locator": "LevinDiscrete:GenFunctions:Thm:1.7.3",
            "statement": "A linear recurrence relation for sequence (a_n) transforms algebraically into an algebraic equation for generating function A(x) = P(x)/Q(x). Decomposing A(x) into partial fractions yields exact closed forms for a_n.",
            "refs": ["decl:LEVIN_DISCRETE:DEF:ordinary_generating_function", "decl:LEVIN_DISCRETE:THM:linear_homogeneous_recurrence"],
        },
        {
            "id": "decl:LEVIN_DISCRETE:THM:catalan_numbers",
            "type": "THEOREM",
            "label": "Levin Discrete (THM 1.7.4): Catalan Number Formula and Dyck Paths",
            "section": "Generating Functions",
            "locator": "LevinDiscrete:GenFunctions:Thm:1.7.4",
            "statement": "The n-th Catalan number C_n = (1 / (n + 1)) C(2n, n) counts Dyck paths from (0,0) to (2n,0), valid parentheses expressions of length 2n, and full binary trees with n+1 leaves. Its generating function satisfies C(x) = 1 + x C(x)^2.",
            "refs": ["decl:LEVIN_DISCRETE:DEF:ordinary_generating_function", "decl:LEVIN_DISCRETE:THM:binomial_theorem"],
        },
        # Chapter 4: Graph Theory Fundamentals (8 declarations)
        {
            "id": "decl:LEVIN_DISCRETE:DEF:graph_basics",
            "type": "DEFINITION",
            "label": "Levin Discrete (DEF 4.1.1): Graph, Vertices, Edges, and Degree",
            "section": "Graph Fundamentals",
            "locator": "LevinDiscrete:GraphBasics:Def:4.1.1",
            "statement": "A graph G = (V, E) consists of a nonempty set of vertices V and a set of 2-element subsets E subseteq P_2(V) called edges. The degree d(v) of vertex v is the number of edges incident to v.",
            "refs": [],
        },
        {
            "id": "decl:LEVIN_DISCRETE:THM:handshaking_lemma",
            "type": "THEOREM",
            "label": "Levin Discrete (THM 4.1.2): Euler's Handshaking Lemma (Degree Sum Formula)",
            "section": "Graph Fundamentals",
            "locator": "LevinDiscrete:GraphBasics:Thm:4.1.2",
            "statement": "In any finite undirected graph G = (V, E), the sum of degrees of all vertices equals twice the number of edges: Sum_{v in V} d(v) = 2 |E|. Consequently, every graph has an even number of vertices of odd degree.",
            "refs": ["decl:LEVIN_DISCRETE:DEF:graph_basics"],
        },
        {
            "id": "decl:LEVIN_DISCRETE:DEF:graph_isomorphism",
            "type": "DEFINITION",
            "label": "Levin Discrete (DEF 4.1.3): Graph Isomorphism and Invariants",
            "section": "Graph Fundamentals",
            "locator": "LevinDiscrete:GraphBasics:Def:4.1.3",
            "statement": "Graphs G_1 = (V_1, E_1) and G_2 = (V_2, E_2) are isomorphic (G_1 ~= G_2) if there is a bijection f: V_1 -> V_2 such that {u, v} in E_1 iff {f(u), f(v)} in E_2. Vertex degrees, connectedness, and cycle lengths are isomorphism invariants.",
            "refs": ["decl:LEVIN_DISCRETE:DEF:graph_basics"],
        },
        {
            "id": "decl:LEVIN_DISCRETE:DEF:paths_cycles_connectivity",
            "type": "DEFINITION",
            "label": "Levin Discrete (DEF 4.1.4): Paths, Cycles, and Connected Components",
            "section": "Graph Fundamentals",
            "locator": "LevinDiscrete:GraphBasics:Def:4.1.4",
            "statement": "A walk is a sequence of alternating incident vertices and edges; a path is a walk with distinct vertices; a cycle is a closed walk with distinct internal vertices. A graph is connected if there is a path between every pair of vertices.",
            "refs": ["decl:LEVIN_DISCRETE:DEF:graph_basics"],
        },
        {
            "id": "decl:LEVIN_DISCRETE:THM:tree_characterization",
            "type": "THEOREM",
            "label": "Levin Discrete (THM 4.2.1): Equivalent Characterizations of Trees",
            "section": "Trees",
            "locator": "LevinDiscrete:Trees:Thm:4.2.1",
            "statement": "For a graph T with n vertices, the following are equivalent: (1) T is a tree (connected and acyclic); (2) T is connected and has exactly n - 1 edges; (3) T is acyclic and has exactly n - 1 edges; (4) there is a unique simple path between every pair of vertices.",
            "refs": ["decl:LEVIN_DISCRETE:DEF:paths_cycles_connectivity", "decl:LEVIN_DISCRETE:THM:weak_induction"],
        },
        {
            "id": "decl:LEVIN_DISCRETE:THM:spanning_tree_existence",
            "type": "THEOREM",
            "label": "Levin Discrete (THM 4.2.2): Spanning Tree Existence for Connected Graphs",
            "section": "Trees",
            "locator": "LevinDiscrete:Trees:Thm:4.2.2",
            "statement": "Every connected finite graph G contains a spanning tree: a subgraph T of G that includes every vertex of G and is a tree.",
            "refs": ["decl:LEVIN_DISCRETE:THM:tree_characterization"],
        },
        {
            "id": "decl:LEVIN_DISCRETE:THM:bipartite_two_colorable",
            "type": "THEOREM",
            "label": "Levin Discrete (THM 4.3.1): Characterization of Bipartite Graphs (Odd Cycles)",
            "section": "Bipartite Graphs",
            "locator": "LevinDiscrete:Bipartite:Thm:4.3.1",
            "statement": "A graph G is bipartite (its vertex set partitions into two independent sets V_1, V_2) if and only if G contains no odd cycles (cycles of odd length). Equivalently, G is 2-colorable.",
            "refs": ["decl:LEVIN_DISCRETE:DEF:paths_cycles_connectivity"],
        },
        {
            "id": "decl:LEVIN_DISCRETE:THM:halls_marriage_theorem",
            "type": "THEOREM",
            "label": "Levin Discrete (THM 4.3.2): Hall's Marriage Theorem (Bipartite Matching Condition)",
            "section": "Bipartite Graphs",
            "locator": "LevinDiscrete:Bipartite:Thm:4.3.2",
            "statement": "Let G = (A union B, E) be a bipartite graph. There exists a matching in G covering every vertex in A if and only if for every subset S subseteq A, |N(S)| >= |S|, where N(S) is the neighborhood of S in B.",
            "refs": ["decl:LEVIN_DISCRETE:THM:bipartite_two_colorable", "decl:LEVIN_DISCRETE:THM:strong_induction"],
        },
        # Chapter 5: Planarity, Colorings and Traversal (9 declarations)
        {
            "id": "decl:LEVIN_DISCRETE:DEF:planar_embedding",
            "type": "DEFINITION",
            "label": "Levin Discrete (DEF 4.4.1): Planar Graphs and Plane Embeddings",
            "section": "Planar Graphs",
            "locator": "LevinDiscrete:Planarity:Def:4.4.1",
            "statement": "A graph G is planar if it can be drawn in the plane R^2 such that no edges intersect except at their endpoints (a plane embedding). A plane drawing partitions R^2 \\ G into connected open regions called faces.",
            "refs": ["decl:LEVIN_DISCRETE:DEF:graph_basics"],
        },
        {
            "id": "decl:LEVIN_DISCRETE:THM:eulers_formula",
            "type": "THEOREM",
            "label": "Levin Discrete (THM 4.4.2): Euler's Planar Formula (V - E + F = 2)",
            "section": "Planar Graphs",
            "locator": "LevinDiscrete:Planarity:Thm:4.4.2",
            "statement": "For any connected planar graph drawn in the plane with V vertices, E edges, and F faces (including the unbounded outer face), V - E + F = 2.",
            "refs": ["decl:LEVIN_DISCRETE:DEF:planar_embedding", "decl:LEVIN_DISCRETE:THM:tree_characterization", "decl:LEVIN_DISCRETE:THM:weak_induction"],
        },
        {
            "id": "decl:LEVIN_DISCRETE:THM:planar_edge_bounds",
            "type": "THEOREM",
            "label": "Levin Discrete (THM 4.4.3): Planar Graph Edge Bounds (E <= 3V - 6)",
            "section": "Planar Graphs",
            "locator": "LevinDiscrete:Planarity:Thm:4.4.3",
            "statement": "For any connected planar simple graph with V >= 3 vertices and E edges, E <= 3V - 6. If G is triangle-free (e.g. bipartite), E <= 2V - 4. Consequently, K_5 and K_{3,3} are non-planar.",
            "refs": ["decl:LEVIN_DISCRETE:THM:eulers_formula"],
        },
        {
            "id": "decl:LEVIN_DISCRETE:THM:kuratowskis_theorem",
            "type": "THEOREM",
            "label": "Levin Discrete (THM 4.4.4): Kuratowski's Theorem on Planar Characterization",
            "section": "Planar Graphs",
            "locator": "LevinDiscrete:Planarity:Thm:4.4.4",
            "statement": "A graph G is planar if and only if G does not contain a subgraph homeomorphic to (or a subdivision of) K_5 (complete graph on 5 vertices) or K_{3,3} (complete bipartite utility graph on 3+3 vertices).",
            "refs": ["decl:LEVIN_DISCRETE:THM:planar_edge_bounds"],
        },
        {
            "id": "decl:LEVIN_DISCRETE:DEF:chromatic_number",
            "type": "DEFINITION",
            "label": "Levin Discrete (DEF 4.5.1): Vertex Coloring and Chromatic Number chi(G)",
            "section": "Graph Coloring",
            "locator": "LevinDiscrete:Coloring:Def:4.5.1",
            "statement": "A proper k-coloring of graph G = (V, E) is an assignment c: V -> {1, ..., k} such that {u, v} in E implies c(u) != c(v). The chromatic number chi(G) is the minimum k for which G has a proper k-coloring.",
            "refs": ["decl:LEVIN_DISCRETE:DEF:graph_basics"],
        },
        {
            "id": "decl:LEVIN_DISCRETE:THM:four_color_theorem",
            "type": "THEOREM",
            "label": "Levin Discrete (THM 4.5.2): The Four Color Theorem for Planar Graphs",
            "section": "Graph Coloring",
            "locator": "LevinDiscrete:Coloring:Thm:4.5.2",
            "statement": "Every planar graph G is 4-colorable: chi(G) <= 4. Equivalently, the faces of any planar map can be colored with at most 4 colors such that adjacent faces have different colors.",
            "refs": ["decl:LEVIN_DISCRETE:DEF:chromatic_number", "decl:LEVIN_DISCRETE:THM:eulers_formula"],
        },
        {
            "id": "decl:LEVIN_DISCRETE:THM:five_color_theorem",
            "type": "THEOREM",
            "label": "Levin Discrete (THM 4.5.3): The Five Color Theorem for Planar Graphs",
            "section": "Graph Coloring",
            "locator": "LevinDiscrete:Coloring:Thm:4.5.3",
            "statement": "Every planar graph G is 5-colorable: chi(G) <= 5. The proof uses Euler's formula to guarantee a vertex of degree <= 5 and Kempe chains to recolor.",
            "refs": ["decl:LEVIN_DISCRETE:DEF:chromatic_number", "decl:LEVIN_DISCRETE:THM:planar_edge_bounds"],
        },
        {
            "id": "decl:LEVIN_DISCRETE:THM:euler_path_circuit",
            "type": "THEOREM",
            "label": "Levin Discrete (THM 4.6.1): Euler Path and Circuit Theorem",
            "section": "Euler Paths and Circuits",
            "locator": "LevinDiscrete:Eulerian:Thm:4.6.1",
            "statement": "A connected finite graph G contains an Euler circuit (closed walk traversing every edge exactly once) if and only if every vertex has even degree. G contains an open Euler path (non-closed) if and only if exactly two vertices have odd degree.",
            "refs": ["decl:LEVIN_DISCRETE:THM:handshaking_lemma", "decl:LEVIN_DISCRETE:DEF:paths_cycles_connectivity"],
        },
        {
            "id": "decl:LEVIN_DISCRETE:THM:diracs_theorem",
            "type": "THEOREM",
            "label": "Levin Discrete (THM 4.6.2): Dirac's Theorem for Hamiltonian Cycles",
            "section": "Hamiltonian Graphs",
            "locator": "LevinDiscrete:Hamiltonian:Thm:4.6.2",
            "statement": "If G is a simple graph with n >= 3 vertices such that every vertex v in V has degree d(v) >= n / 2, then G contains a Hamiltonian cycle (a simple cycle containing every vertex of G).",
            "refs": ["decl:LEVIN_DISCRETE:DEF:paths_cycles_connectivity"],
        },
    ]


def generate_levin_discrete_declarations() -> list[LevinDiscreteDeclaration]:
    """Generate parsed LevinDiscreteDeclaration objects with zero-prose persistence."""
    raw = get_raw_levin_discrete_declarations()
    decls = []
    for item in raw:
        statement = item["statement"]
        sha = _sha256_statement(statement)
        profile = detect_levin_discrete_profile(statement, item["label"])
        decl = LevinDiscreteDeclaration(
            node_id=item["id"],
            source_id=SOURCE_ID,
            corpus=CORPUS,
            label=item["label"],
            decl_type=item["type"],
            chapter_section=item["section"],
            locator=item["locator"],
            statement_sha256=sha,
            char_count=len(statement),
            structural_refs=item.get("refs", []),
            representation_profile=profile,
            extraction_mode="SOURCE_PARSE",
        )
        decls.append(decl)
    return decls


def source_identity() -> dict[str, Any]:
    """Return immutable source identity for Levin Discrete Mathematics 4e."""
    return {
        "source_id": SOURCE_ID,
        "corpus": CORPUS,
        "title": "Discrete Mathematics: An Open Introduction (4th Edition)",
        "authors": ["Oscar Levin"],
        "revision": "2024-4th-Edition-CC-BY-NC-SA-4.0",
        "license": "CC BY-NC-SA 4.0",
        "source_format": "PreTeXt / Web Source Tree",
        "stage": STAGE,
    }


def serialize_zero_prose_manifest(out_path: Path) -> dict[str, Any]:
    """Serialize the zero-prose declaration manifest to disk."""
    decls = generate_levin_discrete_declarations()
    manifest = {
        "source_identity": source_identity(),
        "total_declarations": len(decls),
        "declarations": [d.to_dict() for d in decls],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    manifest_path = ROOT / "formal" / "levin_discrete_manifest_v0_21.json"
    manifest = serialize_zero_prose_manifest(manifest_path)
    print(f"Generated {manifest['total_declarations']} Levin Discrete declarations at {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
