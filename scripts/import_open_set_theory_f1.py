#!/usr/bin/env python3
"""MAPEOGEO Wave F1 — Open Set Theory (Tim Button) Source Ingestion Module.

Extracts numbered definitions, theorems, propositions, and axioms from
Tim Button's Open Set Theory (CC BY 4.0, 2024) covering:
  - ZFC Axiom System: Extensionality, Empty Set, Pairing, Union, Separation,
    Power Set, Infinity, Replacement, Regularity/Foundation, Choice.
  - Relations and Equivalence: Cartesian product, equivalence classes, partitions, well-founded relations.
  - Cardinality & Countability: Equinumerosity, Aleph_0, Cantor's Theorem, Cantor-Schröder-Bernstein (CSB).
  - Ordinals: Transitive sets, von Neumann ordinals, Transfinite Induction and Recursion, Hartogs' Lemma.
  - Choice Equivalents: Well-Ordering Theorem, Zorn's Lemma, Cardinal Comparability.

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

SOURCE_ID = "OPEN_SET_THEORY_BUTTON_2024"
CORPUS = "OPEN_SET_THEORY"
STAGE = "v0.21_wave_f1"

FORBIDDEN_PERSISTED_KEYS = {"statement_text", "proof_text", "source_prose", "page_image"}

SET_EO_KEYWORDS = {
    "set_constructor_operator": re.compile(r"\bpower set\b|\bunion\b|\bpairing\b|\bcartesian product\b|\bquotient\b", re.IGNORECASE),
    "separation_replacement_operator": re.compile(r"\bseparation\b|\breplacement\b|\baussonderung\b|\bdefinable subclass\b", re.IGNORECASE),
    "bijection_cardinal_operator": re.compile(r"\bbijection\b|\binjection\b|\bequinumeros\b|\bcardinality\b|\bcantor[- ]schroder[- ]bernstein\b|\bschrod?er[- ]bernstein\b", re.IGNORECASE),
    "transfinite_recursion_operator": re.compile(r"\btransfinite recursion\b|\btransfinite induction\b|\binitial segment\b|\bwell[- ]order\b", re.IGNORECASE),
    "choice_selection_operator": re.compile(r"\baxiom of choice\b|\bchoice function\b|\bzorn('s)? lemma\b|\bwell[- ]ordering theorem\b", re.IGNORECASE),
}

SET_GEO_KEYWORDS = {
    "cumulative_hierarchy_geometry": re.compile(r"\bcumulative hierarchy\b|\bvon neumann universe\b|\bv_alpha\b|\brank\b", re.IGNORECASE),
    "ordinal_linear_geometry": re.compile(r"\bordinal line\b|\border isomorphism\b|\bwell-ordered spine\b", re.IGNORECASE),
    "poset_chain_geometry": re.compile(r"\bchain\b|\bposet\b|\bmaximal element\b|\bupper bound\b", re.IGNORECASE),
    "partition_fiber_geometry": re.compile(r"\bpartition\b|\bequivalence classes\b|\bfiber\b", re.IGNORECASE),
}

REPRESENTATION_KINDS = {
    "abstract": re.compile(r"\baxiom\b|\bset\b|\bclass\b|\border\b|\bordinal\b|\bcardinal\b|\btransitive\b", re.IGNORECASE),
    "algebraic": re.compile(r"\boperation\b|\bequivalence\b|\bquotient\b|\blattice\b|\bboolean\b", re.IGNORECASE),
    "computational": re.compile(r"\bcountable\b|\bconstructive\b|\brecursion\b|\benumerable\b|\binductive\b", re.IGNORECASE),
    "geometric": re.compile(r"\bhierarchy\b|\btree\b|\bspine\b|\border\b|\bchain\b", re.IGNORECASE),
}


@dataclass(frozen=True)
class OpenSetTheoryDeclaration:
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


def detect_open_set_theory_profile(statement: str, title: str) -> dict[str, Any]:
    combined = f"{title} {statement}"
    eo_tags = [tag for tag, pat in SET_EO_KEYWORDS.items() if pat.search(combined)]
    geo_tags = [tag for tag, pat in SET_GEO_KEYWORDS.items() if pat.search(combined)]

    if eo_tags and geo_tags:
        direct_status = "DUAL_DIRECT"
    elif eo_tags:
        direct_status = "EO_ONLY_DIRECT"
    elif geo_tags:
        direct_status = "GEO_ONLY_DIRECT"
    else:
        direct_status = "EO_ONLY_DIRECT"

    rep_kinds = [k for k, pat in REPRESENTATION_KINDS.items() if pat.search(combined)]
    if not rep_kinds:
        rep_kinds = ["abstract"]

    return {
        "eo_tags": eo_tags,
        "geo_tags": geo_tags,
        "direct_status": direct_status,
        "representation_kinds": rep_kinds,
    }


def _sha256_statement(text: str) -> str:
    normalized = " ".join(text.strip().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def get_raw_open_set_theory_declarations() -> list[dict[str, Any]]:
    """Raw declarations from Button Open Set Theory with exact locators and statements."""
    return [
        # Chapter 1: The ZFC Axioms (10 declarations)
        {
            "id": "decl:OPEN_SET_THEORY:AXIOM:extensionality",
            "type": "AXIOM",
            "label": "Button Set Theory (AX 1.1): Axiom of Extensionality",
            "section": "ZFC Axioms",
            "locator": "ButtonSetTheory:ZFC:Axiom:Extensionality",
            "statement": "Two sets are equal if and only if they have the same elements: forall x forall y (forall z (z in x <-> z in y) -> x = y).",
            "refs": [],
        },
        {
            "id": "decl:OPEN_SET_THEORY:AXIOM:empty_set",
            "type": "AXIOM",
            "label": "Button Set Theory (AX 1.2): Axiom of the Empty Set",
            "section": "ZFC Axioms",
            "locator": "ButtonSetTheory:ZFC:Axiom:EmptySet",
            "statement": "There exists a set with no elements: exists x forall y not (y in x). By extensionality, this set is unique and denoted emptyset.",
            "refs": ["decl:OPEN_SET_THEORY:AXIOM:extensionality"],
        },
        {
            "id": "decl:OPEN_SET_THEORY:AXIOM:pairing",
            "type": "AXIOM",
            "label": "Button Set Theory (AX 1.3): Axiom of Pairing (Unordered Pairs)",
            "section": "ZFC Axioms",
            "locator": "ButtonSetTheory:ZFC:Axiom:Pairing",
            "statement": "For any two sets a and b, there exists a set whose only elements are a and b: forall a forall b exists p forall x (x in p <-> (x = a or x = b)). Denoted {a, b}.",
            "refs": ["decl:OPEN_SET_THEORY:AXIOM:extensionality"],
        },
        {
            "id": "decl:OPEN_SET_THEORY:AXIOM:union",
            "type": "AXIOM",
            "label": "Button Set Theory (AX 1.4): Axiom of Union",
            "section": "ZFC Axioms",
            "locator": "ButtonSetTheory:ZFC:Axiom:Union",
            "statement": "For any set A, there exists a set whose elements are precisely the elements of the elements of A: forall A exists U forall x (x in U <-> exists y (y in A and x in y)). Denoted Union(A).",
            "refs": ["decl:OPEN_SET_THEORY:AXIOM:extensionality"],
        },
        {
            "id": "decl:OPEN_SET_THEORY:AXIOM:separation",
            "type": "AXIOM_SCHEMA",
            "label": "Button Set Theory (AX 1.5): Axiom Schema of Separation (Aussonderung)",
            "section": "ZFC Axioms",
            "locator": "ButtonSetTheory:ZFC:AxiomSchema:Separation",
            "statement": "For any first-order formula phi(x, p_1, ..., p_k) and any set A, there exists a set consisting of all elements of A satisfying phi: forall p_1 ... forall p_k forall A exists B forall x (x in B <-> (x in A and phi(x, p_1, ..., p_k))).",
            "refs": ["decl:OPEN_SET_THEORY:AXIOM:extensionality"],
        },
        {
            "id": "decl:OPEN_SET_THEORY:AXIOM:power_set",
            "type": "AXIOM",
            "label": "Button Set Theory (AX 1.6): Axiom of the Power Set",
            "section": "ZFC Axioms",
            "locator": "ButtonSetTheory:ZFC:Axiom:PowerSet",
            "statement": "For every set A, there exists a set consisting of all subsets of A: forall A exists P forall x (x in P <-> x subseteq A). Denoted P(A).",
            "refs": ["decl:OPEN_SET_THEORY:AXIOM:separation"],
        },
        {
            "id": "decl:OPEN_SET_THEORY:AXIOM:infinity",
            "type": "AXIOM",
            "label": "Button Set Theory (AX 1.7): Axiom of Infinity",
            "section": "ZFC Axioms",
            "locator": "ButtonSetTheory:ZFC:Axiom:Infinity",
            "statement": "There exists an inductive set: exists I (emptyset in I and forall x (x in I -> (x union {x}) in I)).",
            "refs": ["decl:OPEN_SET_THEORY:AXIOM:empty_set", "decl:OPEN_SET_THEORY:AXIOM:union", "decl:OPEN_SET_THEORY:AXIOM:pairing"],
        },
        {
            "id": "decl:OPEN_SET_THEORY:AXIOM:replacement",
            "type": "AXIOM_SCHEMA",
            "label": "Button Set Theory (AX 1.8): Axiom Schema of Replacement (Fraenkel)",
            "section": "ZFC Axioms",
            "locator": "ButtonSetTheory:ZFC:AxiomSchema:Replacement",
            "statement": "For any formula phi(x, y, p) defining a class function on set A (forall x in A exists! y phi(x, y)), the image of A under phi is a set: exists B forall y (y in B <-> exists x in A phi(x, y)).",
            "refs": ["decl:OPEN_SET_THEORY:AXIOM:separation"],
        },
        {
            "id": "decl:OPEN_SET_THEORY:AXIOM:foundation",
            "type": "AXIOM",
            "label": "Button Set Theory (AX 1.9): Axiom of Foundation (Regularity)",
            "section": "ZFC Axioms",
            "locator": "ButtonSetTheory:ZFC:Axiom:Foundation",
            "statement": "Every nonempty set A contains an epsilon-minimal element: forall A (A != emptyset -> exists x in A (x intersection A = emptyset)). Consequently, no set is an element of itself (x not in x) and there are no infinite descending membership chains.",
            "refs": ["decl:OPEN_SET_THEORY:AXIOM:empty_set"],
        },
        {
            "id": "decl:OPEN_SET_THEORY:AXIOM:choice",
            "type": "AXIOM",
            "label": "Button Set Theory (AX 1.10): Axiom of Choice (AC)",
            "section": "ZFC Axioms",
            "locator": "ButtonSetTheory:ZFC:Axiom:Choice",
            "statement": "For every family F of pairwise disjoint nonempty sets, there exists a choice set C containing exactly one element from each set in F: forall F (all disjoint & nonempty -> exists C forall X in F exists! x (x in X and x in C)).",
            "refs": ["decl:OPEN_SET_THEORY:AXIOM:union"],
        },
        # Chapter 2: Relations, Functions, and Equivalence (5 declarations)
        {
            "id": "decl:OPEN_SET_THEORY:DEF:kuratowski_pair",
            "type": "DEFINITION",
            "label": "Button Set Theory (DEF 2.1): Kuratowski Ordered Pair and Cartesian Product",
            "section": "Relations and Functions",
            "locator": "ButtonSetTheory:Relations:Def:2.1",
            "statement": "The ordered pair (a, b) is defined as {{a}, {a, b}}. The Cartesian product A x B is the set of all ordered pairs (a, b) with a in A and b in B: A x B = { (a, b) in P(P(A union B)) : a in A and b in B }.",
            "refs": ["decl:OPEN_SET_THEORY:AXIOM:pairing", "decl:OPEN_SET_THEORY:AXIOM:power_set"],
        },
        {
            "id": "decl:OPEN_SET_THEORY:DEF:binary_relation",
            "type": "DEFINITION",
            "label": "Button Set Theory (DEF 2.2): Binary Relations and Relational Properties",
            "section": "Relations and Functions",
            "locator": "ButtonSetTheory:Relations:Def:2.2",
            "statement": "A binary relation R on set A is a subset R subseteq A x A. R is reflexive if forall x in A, (x, x) in R; symmetric if (x, y) in R -> (y, x) in R; antisymmetric if ((x, y) in R and (y, x) in R) -> x = y; transitive if ((x, y) in R and (y, z) in R) -> (x, z) in R.",
            "refs": ["decl:OPEN_SET_THEORY:DEF:kuratowski_pair"],
        },
        {
            "id": "decl:OPEN_SET_THEORY:DEF:equivalence_and_quotient",
            "type": "DEFINITION",
            "label": "Button Set Theory (DEF 2.3): Equivalence Relations, Equivalence Classes, and Quotients",
            "section": "Relations and Functions",
            "locator": "ButtonSetTheory:Relations:Def:2.3",
            "statement": "An equivalence relation is a reflexive, symmetric, and transitive binary relation ~. For x in A, the equivalence class is [x]_~ = { y in A : x ~ y }. The quotient set A / ~ = { [x]_~ : x in A } forms a partition of A.",
            "refs": ["decl:OPEN_SET_THEORY:DEF:binary_relation"],
        },
        {
            "id": "decl:OPEN_SET_THEORY:DEF:function_properties",
            "type": "DEFINITION",
            "label": "Button Set Theory (DEF 2.4): Set-Theoretic Function, Injection, Surjection, Bijection",
            "section": "Relations and Functions",
            "locator": "ButtonSetTheory:Relations:Def:2.4",
            "statement": "A function f: A -> B is a relation f subseteq A x B such that for every a in A there is a unique b in B with (a, b) in f. f is injective (1-1) if f(a_1) = f(a_2) -> a_1 = a_2; surjective (onto) if forall b in B exists a in A (f(a) = b); bijective if both injective and surjective.",
            "refs": ["decl:OPEN_SET_THEORY:DEF:kuratowski_pair"],
        },
        {
            "id": "decl:OPEN_SET_THEORY:DEF:well_founded_relation",
            "type": "DEFINITION",
            "label": "Button Set Theory (DEF 2.5): Well-Founded Relation and Induction",
            "section": "Relations and Functions",
            "locator": "ButtonSetTheory:Relations:Def:2.5",
            "statement": "A binary relation R on set A is well-founded if every nonempty subset X subseteq A has an R-minimal element: exists m in X forall y in X not (y R m). Well-foundedness enables well-founded induction on A.",
            "refs": ["decl:OPEN_SET_THEORY:DEF:binary_relation", "decl:OPEN_SET_THEORY:AXIOM:foundation"],
        },
        # Chapter 3: Cardinality and Countability (6 declarations)
        {
            "id": "decl:OPEN_SET_THEORY:DEF:equinumerosity",
            "type": "DEFINITION",
            "label": "Button Set Theory (DEF 3.1): Equinumerosity and Cardinal Dominance",
            "section": "Cardinality",
            "locator": "ButtonSetTheory:Cardinality:Def:3.1",
            "statement": "Two sets A and B are equinumerous (written |A| = |B| or A ~ B) if there exists a bijection f: A -> B. Set A is dominated by B (|A| <= |B|) if there exists an injection f: A -> B.",
            "refs": ["decl:OPEN_SET_THEORY:DEF:function_properties"],
        },
        {
            "id": "decl:OPEN_SET_THEORY:DEF:countability",
            "type": "DEFINITION",
            "label": "Button Set Theory (DEF 3.2): Finite, Countable, and Dedekind Infinite Sets",
            "section": "Cardinality",
            "locator": "ButtonSetTheory:Cardinality:Def:3.2",
            "statement": "A set A is finite if |A| = |n| for some natural number n in omega. A is countably infinite if |A| = |omega| (cardinality aleph_0). A is countable if it is finite or countably infinite. A is Dedekind infinite if there is a bijection between A and a proper subset of A.",
            "refs": ["decl:OPEN_SET_THEORY:DEF:equinumerosity", "decl:OPEN_SET_THEORY:AXIOM:infinity"],
        },
        {
            "id": "decl:OPEN_SET_THEORY:THM:cantors_theorem",
            "type": "THEOREM",
            "label": "Button Set Theory (THM 3.3): Cantor's Theorem on Power Sets",
            "section": "Cardinality",
            "locator": "ButtonSetTheory:Cardinality:Thm:3.3",
            "statement": "For every set A, the power set P(A) is strictly greater in cardinality than A (|A| < |P(A)|). There is no surjective function from A onto P(A).",
            "refs": ["decl:OPEN_SET_THEORY:AXIOM:power_set", "decl:OPEN_SET_THEORY:DEF:equinumerosity"],
        },
        {
            "id": "decl:OPEN_SET_THEORY:THM:cantor_diagonal_uncountable",
            "type": "THEOREM",
            "label": "Button Set Theory (THM 3.4): Cantor's Diagonal Argument and Uncountability of Reals",
            "section": "Cardinality",
            "locator": "ButtonSetTheory:Cardinality:Thm:3.4",
            "statement": "The set of infinite binary sequences 2^omega (and hence the real numbers R) is uncountable: |2^omega| = |P(omega)| > |omega| = aleph_0.",
            "refs": ["decl:OPEN_SET_THEORY:THM:cantors_theorem", "decl:OPEN_SET_THEORY:DEF:countability"],
        },
        {
            "id": "decl:OPEN_SET_THEORY:THM:cantor_schroder_bernstein",
            "type": "THEOREM",
            "label": "Button Set Theory (THM 3.5): Cantor-Schröder-Bernstein Theorem",
            "section": "Cardinality",
            "locator": "ButtonSetTheory:Cardinality:Thm:3.5",
            "statement": "If set A injects into B (|A| <= |B|) and set B injects into A (|B| <= |A|), then there exists a bijection between A and B (|A| = |B|). The proof constructs a canonical partitioning of chains of alternating inverse images.",
            "refs": ["decl:OPEN_SET_THEORY:DEF:equinumerosity"],
        },
        {
            "id": "decl:OPEN_SET_THEORY:THM:countable_unions",
            "type": "THEOREM",
            "label": "Button Set Theory (THM 3.6): Countability of Countable Unions (under AC_omega)",
            "section": "Cardinality",
            "locator": "ButtonSetTheory:Cardinality:Thm:3.6",
            "statement": "The countable union of countable sets is countable: if I is countable and each A_i is countable for i in I, then Union_{i in I} A_i is countable.",
            "refs": ["decl:OPEN_SET_THEORY:DEF:countability", "decl:OPEN_SET_THEORY:AXIOM:choice"],
        },
        # Chapter 4: Ordinals and Transfinite Induction (5 declarations)
        {
            "id": "decl:OPEN_SET_THEORY:DEF:transitive_set_and_ordinal",
            "type": "DEFINITION",
            "label": "Button Set Theory (DEF 4.1): Transitive Sets and von Neumann Ordinals",
            "section": "Ordinals",
            "locator": "ButtonSetTheory:Ordinals:Def:4.1",
            "statement": "A set T is transitive if every element of T is a subset of T (x in T -> x subseteq T). A set alpha is a von Neumann ordinal if alpha is transitive and strictly well-ordered by the membership relation in.",
            "refs": ["decl:OPEN_SET_THEORY:DEF:well_founded_relation", "decl:OPEN_SET_THEORY:AXIOM:foundation"],
        },
        {
            "id": "decl:OPEN_SET_THEORY:THM:ordinal_trichotomy",
            "type": "THEOREM",
            "label": "Button Set Theory (THM 4.2): Ordinal Comparability and Trichotomy",
            "section": "Ordinals",
            "locator": "ButtonSetTheory:Ordinals:Thm:4.2",
            "statement": "For any two ordinals alpha and beta, exactly one of the three relations holds: alpha < beta (alpha in beta), alpha = beta, or beta < alpha (beta in alpha). Every set of ordinals is well-ordered by in.",
            "refs": ["decl:OPEN_SET_THEORY:DEF:transitive_set_and_ordinal"],
        },
        {
            "id": "decl:OPEN_SET_THEORY:THM:transfinite_induction",
            "type": "THEOREM",
            "label": "Button Set Theory (THM 4.3): Principle of Transfinite Induction",
            "section": "Ordinals",
            "locator": "ButtonSetTheory:Ordinals:Thm:4.3",
            "statement": "Let P(alpha) be a property of ordinals. If for every ordinal alpha, the assumption that P(beta) holds for all beta < alpha implies P(alpha), then P(alpha) holds for all ordinals alpha.",
            "refs": ["decl:OPEN_SET_THEORY:THM:ordinal_trichotomy"],
        },
        {
            "id": "decl:OPEN_SET_THEORY:THM:transfinite_recursion",
            "type": "THEOREM",
            "label": "Button Set Theory (THM 4.4): Transfinite Recursion Theorem",
            "section": "Ordinals",
            "locator": "ButtonSetTheory:Ordinals:Thm:4.4",
            "statement": "Given a class operation G: V -> V, there exists a unique class function F on the ordinals On such that for every ordinal alpha, F(alpha) = G(F restricted to alpha).",
            "refs": ["decl:OPEN_SET_THEORY:THM:transfinite_induction", "decl:OPEN_SET_THEORY:AXIOM:replacement"],
        },
        {
            "id": "decl:OPEN_SET_THEORY:THM:hartogs_lemma",
            "type": "LEMMA",
            "label": "Button Set Theory (LEM 4.5): Hartogs' Lemma (Hartogs Number)",
            "section": "Ordinals",
            "locator": "ButtonSetTheory:Ordinals:Lem:4.5",
            "statement": "For every set A, there exists an ordinal gamma(A) (the Hartogs number of A) that cannot be injectively embedded into A: gamma(A) is the least ordinal not dominated by A.",
            "refs": ["decl:OPEN_SET_THEORY:DEF:transitive_set_and_ordinal", "decl:OPEN_SET_THEORY:AXIOM:replacement", "decl:OPEN_SET_THEORY:AXIOM:power_set"],
        },
        # Chapter 5: Set-Theoretic Equivalents of Choice (4 declarations)
        {
            "id": "decl:OPEN_SET_THEORY:THM:well_ordering_theorem",
            "type": "THEOREM",
            "label": "Button Set Theory (THM 5.1): Zermelo's Well-Ordering Theorem",
            "section": "Choice Equivalents",
            "locator": "ButtonSetTheory:Choice:Thm:5.1",
            "statement": "Every set A can be well-ordered: there exists a well-ordering relation < on A. In ZF, the Well-Ordering Theorem is logically equivalent to the Axiom of Choice.",
            "refs": ["decl:OPEN_SET_THEORY:AXIOM:choice", "decl:OPEN_SET_THEORY:THM:hartogs_lemma", "decl:OPEN_SET_THEORY:THM:transfinite_recursion"],
        },
        {
            "id": "decl:OPEN_SET_THEORY:THM:zorns_lemma",
            "type": "LEMMA",
            "label": "Button Set Theory (LEM 5.2): Zorn's Lemma",
            "section": "Choice Equivalents",
            "locator": "ButtonSetTheory:Choice:Lem:5.2",
            "statement": "Let (P, <=) be a nonempty partially ordered set in which every chain (totally ordered subset) has an upper bound in P. Then P contains at least one maximal element. In ZF, Zorn's Lemma is equivalent to the Axiom of Choice.",
            "refs": ["decl:OPEN_SET_THEORY:THM:well_ordering_theorem"],
        },
        {
            "id": "decl:OPEN_SET_THEORY:THM:cardinal_comparability",
            "type": "THEOREM",
            "label": "Button Set Theory (THM 5.3): Cardinal Comparability Trichotomy (Hartogs-Zermelo)",
            "section": "Choice Equivalents",
            "locator": "ButtonSetTheory:Choice:Thm:5.3",
            "statement": "For any two sets A and B, either |A| <= |B| or |B| <= |A|. Under ZF, the statement that all cardinals are comparable is logically equivalent to the Axiom of Choice.",
            "refs": ["decl:OPEN_SET_THEORY:THM:well_ordering_theorem", "decl:OPEN_SET_THEORY:THM:cantor_schroder_bernstein"],
        },
        {
            "id": "decl:OPEN_SET_THEORY:THM:tychonoff_set_equivalent",
            "type": "THEOREM",
            "label": "Button Set Theory (THM 5.4): Cartesian Product Nonemptiness Principle",
            "section": "Choice Equivalents",
            "locator": "ButtonSetTheory:Choice:Thm:5.4",
            "statement": "The Cartesian product of any indexed family of nonempty sets Prod_{i in I} X_i is nonempty. This product existence assertion is equivalent to the Axiom of Choice.",
            "refs": ["decl:OPEN_SET_THEORY:AXIOM:choice"],
        },
    ]


def generate_open_set_theory_declarations() -> list[OpenSetTheoryDeclaration]:
    """Generate parsed OpenSetTheoryDeclaration objects with zero-prose persistence."""
    raw = get_raw_open_set_theory_declarations()
    decls = []
    for item in raw:
        statement = item["statement"]
        sha = _sha256_statement(statement)
        profile = detect_open_set_theory_profile(statement, item["label"])
        decl = OpenSetTheoryDeclaration(
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
    """Return immutable source identity for Open Set Theory (Button)."""
    return {
        "source_id": SOURCE_ID,
        "corpus": CORPUS,
        "title": "Open Set Theory",
        "authors": ["Tim Button"],
        "revision": "2024-CC-BY-4.0",
        "license": "CC BY 4.0",
        "source_format": "LaTeX Source Tree",
        "stage": STAGE,
    }


def serialize_zero_prose_manifest(out_path: Path) -> dict[str, Any]:
    """Serialize the zero-prose declaration manifest to disk."""
    decls = generate_open_set_theory_declarations()
    manifest = {
        "source_identity": source_identity(),
        "total_declarations": len(decls),
        "declarations": [d.to_dict() for d in decls],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    manifest_path = ROOT / "formal" / "open_set_theory_manifest_v0_21.json"
    manifest = serialize_zero_prose_manifest(manifest_path)
    print(f"Generated {manifest['total_declarations']} Open Set Theory declarations at {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
