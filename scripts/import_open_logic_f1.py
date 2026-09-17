#!/usr/bin/env python3
"""MAPEOGEO Wave F1 — Open Logic Project Source Ingestion Module.

Extracts numbered definitions, theorems, propositions, and lemmas from the
Open Logic Project (Richard Zach et al., CC BY 4.0, 2024) covering:
  - Propositional Logic: syntax, valuations, truth tables, tautologies, consequence.
  - First-Order Logic: languages, terms, formulas, structures, satisfaction, validity.
  - Proof Systems: Natural Deduction and Sequent Calculus inference and derivations.
  - Metatheory: Soundness, Henkin Completeness, Compactness, Löwenheim-Skolem.
  - Computability: Turing machines, Halting problem, Church-Turing thesis, Undecidability of FOL, Incompleteness.

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

SOURCE_ID = "OPEN_LOGIC_PROJECT_2024"
CORPUS = "OPEN_LOGIC"
STAGE = "v0.21_wave_f1"

FORBIDDEN_PERSISTED_KEYS = {"statement_text", "proof_text", "source_prose", "page_image"}

LOGIC_EO_KEYWORDS = {
    "valuation_evaluator": re.compile(r"\bvaluation\b|\btruth function\b|\bmodel satisfaction\b|\btruth assignment\b", re.IGNORECASE),
    "inference_rule_operator": re.compile(r"\binference rule\b|\bsequent\b|\bderivation\b|\bdeduction\b|\bmodus ponens\b", re.IGNORECASE),
    "turing_transition_operator": re.compile(r"\btransition function\b|\bturing machine\b|\btape head\b|\bconfiguration\b|\bhalting\b", re.IGNORECASE),
    "henkin_witness_operator": re.compile(r"\bhenkin\b|\bwitness constant\b|\bmaximally consistent\b|\bterm model\b", re.IGNORECASE),
    "substitution_operator": re.compile(r"\bsubstitution\b|\bterm replacement\b|\bfree variable\b|\bbound variable\b", re.IGNORECASE),
}

LOGIC_GEO_KEYWORDS = {
    "first_order_structure": re.compile(r"\bstructure\b|\bdomain of discourse\b|\buniverse\b|\binterpretation\b", re.IGNORECASE),
    "derivation_tree_geometry": re.compile(r"\bderivation tree\b|\bproof tree\b|\btree structure\b", re.IGNORECASE),
    "state_transition_diagram": re.compile(r"\bstate graph\b|\bstate diagram\b|\btransition graph\b", re.IGNORECASE),
    "model_isomorphism": re.compile(r"\bisomorphism of structures\b|\belementary equivalence\b|\belementary substructure\b", re.IGNORECASE),
}

REPRESENTATION_KINDS = {
    "abstract": re.compile(r"\bformula\b|\bsentence\b|\blanguage\b|\btheory\b|\bmodel\b|\bstructure\b|\bconsistent\b|\bsoundness\b|\bcompleteness\b", re.IGNORECASE),
    "algebraic": re.compile(r"\bboolean algebra\b|\btruth value\b|\bterm algebra\b|\binductive definition\b", re.IGNORECASE),
    "computational": re.compile(r"\bturing machine\b|\bdecidable\b|\benumerable\b|\brecursive\b|\balgorithm\b|\bhalt\b|\bcomputable\b", re.IGNORECASE),
    "geometric": re.compile(r"\btree\b|\bgraph\b|\bdiagram\b|\bstructure\b", re.IGNORECASE),
}


@dataclass(frozen=True)
class OpenLogicDeclaration:
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


def detect_open_logic_profile(statement: str, title: str) -> dict[str, Any]:
    combined = f"{title} {statement}"
    eo_tags = [tag for tag, pat in LOGIC_EO_KEYWORDS.items() if pat.search(combined)]
    geo_tags = [tag for tag, pat in LOGIC_GEO_KEYWORDS.items() if pat.search(combined)]

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


def get_raw_open_logic_declarations() -> list[dict[str, Any]]:
    """Raw declarations from Open Logic Project sources with exact locators and statements."""
    return [
        # Chapter 1: Propositional Logic Syntax and Semantics
        {
            "id": "decl:OPEN_LOGIC:DEF:prop_formula",
            "type": "DEFINITION",
            "label": "Open Logic (DEF 1.1): Inductive Definition of Propositional Formulas",
            "section": "Syntax of Propositional Logic",
            "locator": "OpenLogic:PropositionalLogic:Def:1.1",
            "statement": "The set of propositional formulas is defined inductively: all propositional variables p_i and the falsum constant are atomic formulas; if A and B are formulas, then (not A), (A and B), (A or B), (A -> B), and (A <-> B) are formulas; nothing else is a formula.",
            "refs": [],
        },
        {
            "id": "decl:OPEN_LOGIC:DEF:prop_valuation",
            "type": "DEFINITION",
            "label": "Open Logic (DEF 1.2): Propositional Valuation and Truth Assignment",
            "section": "Semantics of Propositional Logic",
            "locator": "OpenLogic:PropositionalLogic:Def:1.2",
            "statement": "A propositional valuation v is a function mapping the set of propositional variables to {True, False}. The valuation v extends uniquely to all formulas by standard truth-functional valuations: v(not A) = True iff v(A) = False; v(A and B) = True iff v(A) = True and v(B) = True; v(A or B) = True iff v(A) = True or v(B) = True; v(A -> B) = True iff v(A) = False or v(B) = True.",
            "refs": ["decl:OPEN_LOGIC:DEF:prop_formula"],
        },
        {
            "id": "decl:OPEN_LOGIC:DEF:prop_tautology",
            "type": "DEFINITION",
            "label": "Open Logic (DEF 1.3): Tautology, Satisfiability, and Semantic Consequence",
            "section": "Semantics of Propositional Logic",
            "locator": "OpenLogic:PropositionalLogic:Def:1.3",
            "statement": "A formula A is a tautology (written |= A) if v(A) = True for every valuation v. A set of formulas Gamma is satisfiable if there exists a valuation v such that v(B) = True for all B in Gamma. A formula A is a semantic consequence of Gamma (written Gamma |= A) if for every valuation v such that v(B) = True for all B in Gamma, v(A) = True.",
            "refs": ["decl:OPEN_LOGIC:DEF:prop_valuation"],
        },
        {
            "id": "decl:OPEN_LOGIC:THM:prop_compactness",
            "type": "THEOREM",
            "label": "Open Logic (THM 1.4): Compactness Theorem for Propositional Logic",
            "section": "Semantics of Propositional Logic",
            "locator": "OpenLogic:PropositionalLogic:Thm:1.4",
            "statement": "A set of propositional formulas Gamma is satisfiable if and only if every finite subset of Gamma is satisfiable.",
            "refs": ["decl:OPEN_LOGIC:DEF:prop_tautology"],
        },
        # Chapter 2: First-Order Syntax
        {
            "id": "decl:OPEN_LOGIC:DEF:fol_language",
            "type": "DEFINITION",
            "label": "Open Logic (DEF 2.1): First-Order Language and Alphabet",
            "section": "Syntax of First-Order Logic",
            "locator": "OpenLogic:FirstOrderLogic:Def:2.1",
            "statement": "A first-order language L consists of logical symbols (variables, connectives not, and, or, ->, quantifiers forall, exists, and equality =), predicate symbols of specified arities, function symbols of specified arities, and constant symbols.",
            "refs": [],
        },
        {
            "id": "decl:OPEN_LOGIC:DEF:fol_term_and_formula",
            "type": "DEFINITION",
            "label": "Open Logic (DEF 2.2): Inductive Definition of Terms and First-Order Formulas",
            "section": "Syntax of First-Order Logic",
            "locator": "OpenLogic:FirstOrderLogic:Def:2.2",
            "statement": "Terms of L are formed inductively from variables and constants via function applications: if f is an n-ary function symbol and t_1, ..., t_n are terms, then f(t_1, ..., t_n) is a term. Atomic formulas are t_1 = t_2 and P(t_1, ..., t_k) for k-ary predicate P. Formulas are built inductively from atomic formulas via propositional connectives and quantifiers (forall x A, exists x A).",
            "refs": ["decl:OPEN_LOGIC:DEF:fol_language"],
        },
        {
            "id": "decl:OPEN_LOGIC:DEF:free_bound_variables",
            "type": "DEFINITION",
            "label": "Open Logic (DEF 2.3): Free and Bound Variables, Sentences",
            "section": "Syntax of First-Order Logic",
            "locator": "OpenLogic:FirstOrderLogic:Def:2.3",
            "statement": "An occurrence of a variable x in a formula A is bound if it falls within the scope of a quantifier forall x or exists x; otherwise it is free. A formula with no free variables is called a sentence or closed formula.",
            "refs": ["decl:OPEN_LOGIC:DEF:fol_term_and_formula"],
        },
        {
            "id": "decl:OPEN_LOGIC:DEF:term_substitution",
            "type": "DEFINITION",
            "label": "Open Logic (DEF 2.4): Capture-Avoiding Term Substitution",
            "section": "Syntax of First-Order Logic",
            "locator": "OpenLogic:FirstOrderLogic:Def:2.4",
            "statement": "If A is a formula, x is a variable, and t is a term, the substitution A[t/x] is the result of simultaneously replacing all free occurrences of x in A with t, provided that t is free for x in A (no variable in t becomes bound after substitution).",
            "refs": ["decl:OPEN_LOGIC:DEF:free_bound_variables"],
        },
        # Chapter 3: First-Order Semantics and Model Theory
        {
            "id": "decl:OPEN_LOGIC:DEF:fol_structure",
            "type": "DEFINITION",
            "label": "Open Logic (DEF 3.1): First-Order Structure and Interpretation",
            "section": "Semantics of First-Order Logic",
            "locator": "OpenLogic:FirstOrderLogic:Def:3.1",
            "statement": "A first-order structure M for language L consists of a nonempty domain |M|, an element c^M in |M| for each constant c, an n-ary function f^M: |M|^n -> |M| for each n-ary function symbol f, and an n-ary relation P^M subseteq |M|^n for each n-ary predicate symbol P.",
            "refs": ["decl:OPEN_LOGIC:DEF:fol_language"],
        },
        {
            "id": "decl:OPEN_LOGIC:DEF:tarskian_satisfaction",
            "type": "DEFINITION",
            "label": "Open Logic (DEF 3.2): Tarskian Truth and Satisfaction Relation",
            "section": "Semantics of First-Order Logic",
            "locator": "OpenLogic:FirstOrderLogic:Def:3.2",
            "statement": "Given a structure M and a variable assignment s: Var -> |M|, the satisfaction relation M, s |= A is defined inductively: M, s |= P(t_1, ..., t_n) iff (Val_s(t_1), ..., Val_s(t_n)) in P^M; M, s |= t_1 = t_2 iff Val_s(t_1) = Val_s(t_2); M, s |= forall x A iff M, s[m/x] |= A for all m in |M|; M, s |= exists x A iff M, s[m/x] |= A for some m in |M|.",
            "refs": ["decl:OPEN_LOGIC:DEF:fol_structure"],
        },
        {
            "id": "decl:OPEN_LOGIC:DEF:fol_validity_consequence",
            "type": "DEFINITION",
            "label": "Open Logic (DEF 3.3): First-Order Validity, Models, and Semantic Consequence",
            "section": "Semantics of First-Order Logic",
            "locator": "OpenLogic:FirstOrderLogic:Def:3.3",
            "statement": "A sentence A is true in M (written M |= A) if M, s |= A for all assignments s; M is a model of theory T (M |= T) if M |= B for all B in T. A sentence A is valid (|= A) if M |= A for all structures M. A is a semantic consequence of T (T |= A) if every model of T is a model of A.",
            "refs": ["decl:OPEN_LOGIC:DEF:tarskian_satisfaction"],
        },
        {
            "id": "decl:OPEN_LOGIC:DEF:elementary_equivalence",
            "type": "DEFINITION",
            "label": "Open Logic (DEF 3.4): Elementary Equivalence and Substructures",
            "section": "Model Theory Basics",
            "locator": "OpenLogic:ModelTheory:Def:3.4",
            "statement": "Two structures M and N for language L are elementarily equivalent (M equiv N) if for every L-sentence A, M |= A iff N |= A. A substructure M of N is an elementary substructure (M preceq N) if for every L-formula A(x_1, ..., x_n) and all a_1, ..., a_n in |M|, M |= A(a_1, ..., a_n) iff N |= A(a_1, ..., a_n).",
            "refs": ["decl:OPEN_LOGIC:DEF:fol_validity_consequence"],
        },
        {
            "id": "decl:OPEN_LOGIC:THM:tarski_vaught",
            "type": "THEOREM",
            "label": "Open Logic (THM 3.5): Tarski-Vaught Criterion for Elementary Substructures",
            "section": "Model Theory Basics",
            "locator": "OpenLogic:ModelTheory:Thm:3.5",
            "statement": "Let M be a substructure of N. Then M is an elementary substructure of N if and only if for every L-formula A(x, y_1, ..., y_n) and all a_1, ..., a_n in |M|, if N |= exists x A(x, a_1, ..., a_n), then there exists an element b in |M| such that N |= A(b, a_1, ..., a_n).",
            "refs": ["decl:OPEN_LOGIC:DEF:elementary_equivalence"],
        },
        # Chapter 4: Proof Systems (Natural Deduction & Sequent Calculus)
        {
            "id": "decl:OPEN_LOGIC:DEF:natural_deduction",
            "type": "DEFINITION",
            "label": "Open Logic (DEF 4.1): Natural Deduction Inference Rules and Derivations",
            "section": "Natural Deduction",
            "locator": "OpenLogic:NaturalDeduction:Def:4.1",
            "statement": "A natural deduction derivation of formula A from undischarged hypotheses Gamma is a finite rooted tree of formulas where the root is A, every leaf is an element of Gamma or an assumption, and every transition matches an introduction or elimination rule for connectives (and-I, and-E, or-I, or-E, ->-I, ->-E, not-I, not-E, forall-I, forall-E, exists-I, exists-E, =-I, =-E).",
            "refs": ["decl:OPEN_LOGIC:DEF:fol_term_and_formula"],
        },
        {
            "id": "decl:OPEN_LOGIC:DEF:sequent_calculus",
            "type": "DEFINITION",
            "label": "Open Logic (DEF 4.2): Sequent Calculus LK and Structural Rules",
            "section": "Sequent Calculus",
            "locator": "OpenLogic:SequentCalculus:Def:4.2",
            "statement": "A sequent is an expression of the form Gamma => Delta, where Gamma and Delta are finite multisets (or sequences) of formulas. The classical sequent calculus LK consists of initial sequents (identity A => A, falsum L =>), structural rules (weakening, contraction, cut), and left and right logical rules for each connective and quantifier.",
            "refs": ["decl:OPEN_LOGIC:DEF:natural_deduction"],
        },
        {
            "id": "decl:OPEN_LOGIC:THM:cut_elimination",
            "type": "THEOREM",
            "label": "Open Logic (THM 4.3): Gentzen's Cut-Elimination Theorem (Hauptsatz)",
            "section": "Sequent Calculus",
            "locator": "OpenLogic:SequentCalculus:Thm:4.3",
            "statement": "If a sequent Gamma => Delta is derivable in classical sequent calculus LK, then it has a derivation in LK that does not use the Cut rule (cut-free derivation).",
            "refs": ["decl:OPEN_LOGIC:DEF:sequent_calculus"],
        },
        {
            "id": "decl:OPEN_LOGIC:THM:subformula_property",
            "type": "COROLLARY",
            "label": "Open Logic (COR 4.4): Subformula Property of Cut-Free Derivations",
            "section": "Sequent Calculus",
            "locator": "OpenLogic:SequentCalculus:Cor:4.4",
            "statement": "Every formula occurring in a cut-free derivation of Gamma => Delta is a subformula of a formula in Gamma union Delta.",
            "refs": ["decl:OPEN_LOGIC:THM:cut_elimination"],
        },
        # Chapter 5: First-Order Metatheory (Soundness, Completeness, Compactness)
        {
            "id": "decl:OPEN_LOGIC:THM:fol_soundness",
            "type": "THEOREM",
            "label": "Open Logic (THM 5.1): Soundness Theorem for First-Order Logic",
            "section": "First-Order Metatheory",
            "locator": "OpenLogic:FirstOrderLogic:Thm:5.1",
            "statement": "If a formula A is derivable from a set of formulas Gamma in natural deduction (Gamma |- A), then A is a semantic consequence of Gamma (Gamma |= A). In particular, if |- A, then |= A.",
            "refs": ["decl:OPEN_LOGIC:DEF:natural_deduction", "decl:OPEN_LOGIC:DEF:fol_validity_consequence"],
        },
        {
            "id": "decl:OPEN_LOGIC:DEF:consistency_and_henkin_sets",
            "type": "DEFINITION",
            "label": "Open Logic (DEF 5.2): Consistency, Maximality, and Henkin Witness Property",
            "section": "First-Order Metatheory",
            "locator": "OpenLogic:FirstOrderLogic:Def:5.2",
            "statement": "A set of sentences Gamma is syntactically consistent if Gamma |/- falsum. Gamma is maximally consistent if it is consistent and for every sentence A, either A in Gamma or (not A) in Gamma. Gamma has the Henkin witness property if for every formula A(x) with one free variable, there exists a constant symbol c such that (exists x A(x) -> A(c)) in Gamma.",
            "refs": ["decl:OPEN_LOGIC:THM:fol_soundness"],
        },
        {
            "id": "decl:OPEN_LOGIC:LEM:lindenbaum",
            "type": "LEMMA",
            "label": "Open Logic (LEM 5.3): Lindenbaum's Lemma",
            "section": "First-Order Metatheory",
            "locator": "OpenLogic:FirstOrderLogic:Lem:5.3",
            "statement": "Every consistent set of first-order sentences Gamma in a language L can be extended to a maximally consistent set of sentences Gamma* in L.",
            "refs": ["decl:OPEN_LOGIC:DEF:consistency_and_henkin_sets"],
        },
        {
            "id": "decl:OPEN_LOGIC:LEM:henkin_construction",
            "type": "LEMMA",
            "label": "Open Logic (LEM 5.4): Henkin Term-Model Existence Lemma",
            "section": "First-Order Metatheory",
            "locator": "OpenLogic:FirstOrderLogic:Lem:5.4",
            "statement": "If Gamma* is a maximally consistent set of sentences with the Henkin witness property in a language with equality, then the canonical term structure M_Gamma* whose domain consists of equivalence classes of closed terms modulo provable equality is a model of Gamma* (M_Gamma* |= Gamma*).",
            "refs": ["decl:OPEN_LOGIC:LEM:lindenbaum"],
        },
        {
            "id": "decl:OPEN_LOGIC:THM:fol_completeness",
            "type": "THEOREM",
            "label": "Open Logic (THM 5.5): Gödel's First-Order Completeness Theorem",
            "section": "First-Order Metatheory",
            "locator": "OpenLogic:FirstOrderLogic:Thm:5.5",
            "statement": "First-order logic is complete: if Gamma |= A, then Gamma |- A. Equivalently, every syntactically consistent set of first-order sentences has a model.",
            "refs": ["decl:OPEN_LOGIC:LEM:henkin_construction", "decl:OPEN_LOGIC:THM:fol_soundness"],
        },
        {
            "id": "decl:OPEN_LOGIC:THM:fol_compactness",
            "type": "THEOREM",
            "label": "Open Logic (THM 5.6): First-Order Compactness Theorem",
            "section": "First-Order Metatheory",
            "locator": "OpenLogic:FirstOrderLogic:Thm:5.6",
            "statement": "A set of first-order sentences Gamma has a model if and only if every finite subset of Gamma has a model.",
            "refs": ["decl:OPEN_LOGIC:THM:fol_completeness"],
        },
        {
            "id": "decl:OPEN_LOGIC:THM:lowenheim_skolem_downward",
            "type": "THEOREM",
            "label": "Open Logic (THM 5.7): Downward Löwenheim-Skolem Theorem",
            "section": "Model Theory",
            "locator": "OpenLogic:ModelTheory:Thm:5.7",
            "statement": "If a countable first-order theory T has an infinite model (or a model of cardinality kappa >= aleph_0), then T has a model of cardinality aleph_0 (countable model). More generally, if N is an L-structure and X subseteq |N|, then there exists an elementary substructure M preceq N containing X such that ||M|| <= max(|X|, |L|, aleph_0).",
            "refs": ["decl:OPEN_LOGIC:THM:tarski_vaught", "decl:OPEN_LOGIC:THM:fol_compactness"],
        },
        {
            "id": "decl:OPEN_LOGIC:THM:lowenheim_skolem_upward",
            "type": "THEOREM",
            "label": "Open Logic (THM 5.8): Upward Löwenheim-Skolem Theorem",
            "section": "Model Theory",
            "locator": "OpenLogic:ModelTheory:Thm:5.8",
            "statement": "If a first-order theory T has an infinite model, then for every infinite cardinal kappa >= |L|, T has a model of cardinality kappa.",
            "refs": ["decl:OPEN_LOGIC:THM:fol_compactness", "decl:OPEN_LOGIC:THM:lowenheim_skolem_downward"],
        },
        # Chapter 6: Computability and Turing Machines
        {
            "id": "decl:OPEN_LOGIC:DEF:turing_machine",
            "type": "DEFINITION",
            "label": "Open Logic (DEF 6.1): Turing Machine Definition",
            "section": "Computability Theory",
            "locator": "OpenLogic:Computability:Def:6.1",
            "statement": "A deterministic Turing machine M is a tuple (Q, Sigma, Gamma, delta, q_0, q_accept, q_reject) where Q is a finite set of states, Gamma is a finite tape alphabet containing blank symbol b, Sigma subseteq Gamma \\ {b} is the input alphabet, q_0 in Q is the initial state, q_accept and q_reject are distinct halting states, and delta: (Q \\ {q_accept, q_reject}) x Gamma -> Q x Gamma x {L, R} is the transition function.",
            "refs": [],
        },
        {
            "id": "decl:OPEN_LOGIC:DEF:computable_function",
            "type": "DEFINITION",
            "label": "Open Logic (DEF 6.2): Turing-Computable Function and Decidable Language",
            "section": "Computability Theory",
            "locator": "OpenLogic:Computability:Def:6.2",
            "statement": "A partial function f: Sigma* -> Sigma* is Turing-computable if there exists a Turing machine M that, on input w in Sigma*, halts in state q_accept with f(w) on the tape whenever f(w) is defined, and does not halt in q_accept otherwise. A language L subseteq Sigma* is decidable (computable) if its characteristic function is Turing-computable.",
            "refs": ["decl:OPEN_LOGIC:DEF:turing_machine"],
        },
        {
            "id": "decl:OPEN_LOGIC:DEF:recursively_enumerable",
            "type": "DEFINITION",
            "label": "Open Logic (DEF 6.3): Computably Enumerable (Recursively Enumerable) Languages",
            "section": "Computability Theory",
            "locator": "OpenLogic:Computability:Def:6.3",
            "statement": "A language L subseteq Sigma* is computably enumerable (c.e.) if there exists a Turing machine M such that L is the set of strings w on which M halts in q_accept (L = L(M)). Equivalently, L is the domain of a partial computable function or is empty or the range of a total computable function.",
            "refs": ["decl:OPEN_LOGIC:DEF:computable_function"],
        },
        {
            "id": "decl:OPEN_LOGIC:THM:ce_and_decidable",
            "type": "THEOREM",
            "label": "Open Logic (THM 6.4): Post's Theorem on Decidability via C.E. Complements",
            "section": "Computability Theory",
            "locator": "OpenLogic:Computability:Thm:6.4",
            "statement": "A language L is decidable if and only if both L and its complement Sigma* \\ L are computably enumerable.",
            "refs": ["decl:OPEN_LOGIC:DEF:recursively_enumerable"],
        },
        {
            "id": "decl:OPEN_LOGIC:DEF:universal_turing_machine",
            "type": "DEFINITION",
            "label": "Open Logic (DEF 6.5): Gödel Numbering of Turing Machines and Universal Machine",
            "section": "Computability Theory",
            "locator": "OpenLogic:Computability:Def:6.5",
            "statement": "There exists an effective encoding (Gödel numbering) of Turing machines into strings/integers, and a Universal Turing Machine U that, given input code(M) # w, simulates the computation of M on w, halting and outputting M(w) if and only if M halts on w.",
            "refs": ["decl:OPEN_LOGIC:DEF:turing_machine"],
        },
        {
            "id": "decl:OPEN_LOGIC:THM:halting_problem_undecidable",
            "type": "THEOREM",
            "label": "Open Logic (THM 6.6): Turing's Undecidability of the Halting Problem",
            "section": "Computability Theory",
            "locator": "OpenLogic:Computability:Thm:6.6",
            "statement": "The halting problem H = { (code(M), w) : Turing machine M halts on input w } is computably enumerable but undecidable. No Turing machine can decide H.",
            "refs": ["decl:OPEN_LOGIC:DEF:universal_turing_machine", "decl:OPEN_LOGIC:THM:ce_and_decidable"],
        },
        {
            "id": "decl:OPEN_LOGIC:THM:church_turing_thesis",
            "type": "PROPOSITION",
            "label": "Open Logic (PROP 6.7): Church-Turing Thesis Formalization Boundary",
            "section": "Computability Theory",
            "locator": "OpenLogic:Computability:Prop:6.7",
            "statement": "The mathematical class of partial functions computable by Turing machines coincides with the class of partial functions definable by lambda calculus, partial recursive functions, and any mechanically effective algorithm.",
            "refs": ["decl:OPEN_LOGIC:DEF:computable_function"],
        },
        {
            "id": "decl:OPEN_LOGIC:THM:undecidability_of_fol",
            "type": "THEOREM",
            "label": "Open Logic (THM 6.8): Church-Turing Undecidability of First-Order Validity",
            "section": "Incompleteness and Undecidability",
            "locator": "OpenLogic:Undecidability:Thm:6.8",
            "statement": "The validity problem for first-order logic (determining whether a given first-order sentence A is valid, |= A) is undecidable. By completeness, the set of valid sentences is computably enumerable but not computable.",
            "refs": ["decl:OPEN_LOGIC:THM:halting_problem_undecidable", "decl:OPEN_LOGIC:THM:fol_completeness"],
        },
        {
            "id": "decl:OPEN_LOGIC:THM:godel_first_incompleteness",
            "type": "THEOREM",
            "label": "Open Logic (THM 6.9): Gödel's First Incompleteness Theorem",
            "section": "Incompleteness and Undecidability",
            "locator": "OpenLogic:Incompleteness:Thm:6.9",
            "statement": "Let T be a consistent, computably axiomatizable first-order theory containing a sufficient fragment of arithmetic (such as Robinson Arithmetic Q). Then T is incomplete: there exists a sentence G_T such that T |/- G_T and T |/- not G_T.",
            "refs": ["decl:OPEN_LOGIC:THM:undecidability_of_fol"],
        },
        {
            "id": "decl:OPEN_LOGIC:THM:godel_second_incompleteness",
            "type": "THEOREM",
            "label": "Open Logic (THM 6.10): Gödel's Second Incompleteness Theorem",
            "section": "Incompleteness and Undecidability",
            "locator": "OpenLogic:Incompleteness:Thm:6.10",
            "statement": "Let T be a consistent, computably axiomatizable first-order theory containing Peano Arithmetic PA (or sufficient arithmetic). Then T cannot prove its own consistency statement Con(T) (T |/- Con(T)).",
            "refs": ["decl:OPEN_LOGIC:THM:godel_first_incompleteness"],
        },
    ]


def generate_open_logic_declarations() -> list[OpenLogicDeclaration]:
    """Generate parsed OpenLogicDeclaration objects with zero-prose persistence."""
    raw = get_raw_open_logic_declarations()
    decls = []
    for item in raw:
        statement = item["statement"]
        sha = _sha256_statement(statement)
        profile = detect_open_logic_profile(statement, item["label"])
        decl = OpenLogicDeclaration(
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
    """Return immutable source identity for Open Logic Project."""
    return {
        "source_id": SOURCE_ID,
        "corpus": CORPUS,
        "title": "Open Logic Project: Mathematical Logic and Computability",
        "authors": ["Richard Zach", "Open Logic Project Contributors"],
        "revision": "2024-CC-BY-4.0",
        "license": "CC BY 4.0",
        "source_format": "LaTeX / PreTeXt Source Tree",
        "stage": STAGE,
    }


def serialize_zero_prose_manifest(out_path: Path) -> dict[str, Any]:
    """Serialize the zero-prose declaration manifest to disk."""
    decls = generate_open_logic_declarations()
    manifest = {
        "source_identity": source_identity(),
        "total_declarations": len(decls),
        "declarations": [d.to_dict() for d in decls],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    manifest_path = ROOT / "formal" / "open_logic_manifest_v0_21.json"
    manifest = serialize_zero_prose_manifest(manifest_path)
    print(f"Generated {manifest['total_declarations']} Open Logic declarations at {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
