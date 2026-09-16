#!/usr/bin/env python3
"""MAPEOGEO Foundation Backfill: Source Ingestion Module.

Extracts curated primitive and elementary mathematical declarations across 8 foundational layers:
  1. Logic & Proofs
  2. Set Theory
  3. Relations & Functions
  4. Number Systems
  5. Elementary Arithmetic & Algebra
  6. Order, Metrics & Sequences
  7. Euclidean Geometry & Trigonometry
  8. Elementary Calculus

Source attribution: Standard open foundational mathematical texts and definitions
  (Halmos 'Naive Set Theory', Enderton 'Elements of Set Theory', Birkhoff & MacLane
   'A Survey of Modern Algebra', Apostol 'Calculus Vol 1', Euclid/Hilbert 'Foundations of Geometry',
   Gallier 'Discrete Mathematics and Foundations').

Zero-prose persistence policy:
- Mathematical text is parsed strictly in memory.
- Output dictionaries store ONLY metadata: node_id, source_id, label, decl_type, chapter_section,
  statement_sha256, char_count, structural_refs, representation_profile.
- No copyrighted prose is persisted to disk in graph artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SOURCE_ID = "FOUNDATION_MATHEMATICS_BASE"
STAGE = "foundation"
FOUNDATION_AMENDMENTS_PATH = ROOT / "formal" / "foundation_mathematical_amendments_v0_20.json"
FOUNDATION_HISTORICAL_ROWS_SHA256 = "8d6a1c2fcedbadebd8d808dce67afdb45b931ea698288a4122a06ec194922a87"
FOUNDATION_HISTORICAL_SOURCE = {
    "file_sha256": "480f4c46f93d5fd03c2ee18e3ad8c95f8693b77b92f233b3add0739081d686d5",
    "git_commit": "c286184781359ee5c88e8de704b95e4738397fb9",
    "path": "scripts/import_foundation_backfill.py",
}

FORBIDDEN_PERSISTED_KEYS = {"statement_text", "proof_text", "source_prose", "page_image"}

# Detector Bank Keywords for Foundation candidates
FOUNDATION_EO_KEYWORDS = {
    "boolean_logic_evaluator": re.compile(r"\btruth table\b|\bboolean\b|\bmodus ponens\b|\bconjunction\b|\bdisjunction\b|\bnegation\b", re.IGNORECASE),
    "set_indicator_operator": re.compile(r"\bunion\b|\bintersection\b|\bcomplement\b|\bset difference\b|\bcartesian product\b|\bpower set\b", re.IGNORECASE),
    "relation_quotient_operator": re.compile(r"\bequivalence relation\b|\bequivalence class\b|\bquotient set\b|\bpartition\b|\bpartial order\b", re.IGNORECASE),
    "function_composition_operator": re.compile(r"\bfunction composition\b|\binjective\b|\bsurjective\b|\bbijective\b|\binverse function\b", re.IGNORECASE),
    "peano_arithmetic_operator": re.compile(r"\bpeano\b|\binduction\b|\bdivisibility\b|\beuclidean division\b|\bprime\b", re.IGNORECASE),
    "field_algebra_evaluator": re.compile(r"\bfield axioms\b|\bgroup axioms\b|\bring\b|\bdistributive\b|\bassociative\b|\bcommutative\b|\bpolynomial\b|\bbinomial\b", re.IGNORECASE),
    "sequence_convergence_bound": re.compile(r"\bsequence limit\b|\bepsilon-N\b|\bcauchy sequence\b|\bmonotone convergence\b|\bseries sum\b|\bgeometric series\b", re.IGNORECASE),
    "euclidean_metric_evaluator": re.compile(r"\bdot product\b|\bdistance formula\b|\binner product\b|\bpythagorean\b|\bcauchy-schwarz\b", re.IGNORECASE),
    "trigonometric_evaluator": re.compile(r"\bsine\b|\bcosine\b|\btangent\b|\btrigonometric identity\b|\bunit circle\b|\bangle sum\b", re.IGNORECASE),
    "differential_calculus_operator": re.compile(r"\bdifference quotient\b|\bderivative\b|\bpower rule\b|\bproduct rule\b|\bchain rule\b|\bintermediate value\b|\bmean value\b", re.IGNORECASE),
    "integral_calculus_operator": re.compile(r"\briemann sum\b|\bdefinite integral\b|\bfundamental theorem of calculus\b|\bintegration by parts\b", re.IGNORECASE),
}

FOUNDATION_GEO_KEYWORDS = {
    "logical_truth_geometry": re.compile(r"\bvenn diagram\b|\btruth value\b|\btruth table\b|\bvaluation\b|\bpropositional lattice\b|\bboolean algebra\b|\bboolean\b", re.IGNORECASE),
    "set_universe_topology": re.compile(r"\bopen set\b|\bneighborhood\b|\bsubset lattice\b|\bpower set\b|\bcoordinate plane\b|\buniversal set\b", re.IGNORECASE),
    "fiber_quotient_geometry": re.compile(r"\bfiber\b|\bpreimage\b|\bprojection\b|\bquotient space\b|\bquotient set\b|\bfoliation\b", re.IGNORECASE),
    "number_line_geometry": re.compile(r"\breal line\b|\bdedekind cut\b|\bcomplex plane\b|\bnumber axis\b|\binterval\b|\bpolar\b", re.IGNORECASE),
    "algebraic_variety_geometry": re.compile(r"\bpolynomial zero\b|\broot\b|\bparabola\b|\bcurve\b|\balgebraic set\b", re.IGNORECASE),
    "metric_ball_geometry": re.compile(r"\bopen ball\b|\bmetric neighborhood\b|\binterval \([a-z0-9, -]+\)\b|\bbounded set\b", re.IGNORECASE),
    "euclidean_space_geometry": re.compile(r"\beuclidean space\b|\br\^2\b|\br\^n\b|\bplane\b|\bvector\b|\bangle\b|\btriangle\b|\bcircle\b", re.IGNORECASE),
    "tangent_slope_area_geometry": re.compile(r"\btangent line\b|\bslope\b|\barea under curve\b|\bsecant line\b|\bextrema\b|\bconcavity\b", re.IGNORECASE),
}

REPRESENTATION_KINDS = {
    "abstract": re.compile(r"\baxiom\b|\bdefinition\b|\bproposition\b|\btheorem\b|\bset\b|\brelation\b|\bfield\b|\bgroup\b|\bspace\b", re.IGNORECASE),
    "algebraic": re.compile(r"\boperation\b|\bequation\b|\bassociative\b|\bdistributive\b|\bpolynomial\b|\bbinomial\b|\baddition\b|\bmultiplication\b|\bgroup\b", re.IGNORECASE),
    "geometric": re.compile(r"\bcircle\b|\bplane\b|\bline\b|\bangle\b|\btriangle\b|\barea\b|\bdistance\b|\bvector\b|\bslope\b|\binterval\b|\bball\b", re.IGNORECASE),
    "computational": re.compile(r"\balgorithm\b|\bcalculation\b|\bevaluation\b|\bformula\b|\bsum\b|\bquotient\b|\bapproximation\b|\bderivative\b|\bintegral\b", re.IGNORECASE),
    "applied": re.compile(r"\brate of change\b|\bmotion\b|\bphysics\b|\boptimization\b|\bcoordinates\b|\bmeasurement\b", re.IGNORECASE),
    "formal": re.compile(r"\bproof\b|\binduction\b|\bcontradiction\b|\bpeano\b|\bdedekind\b|\blean\b|\bformal\b", re.IGNORECASE),
}


@dataclass
class FoundationDeclaration:
    node_id: str
    source_id: str
    label: str
    decl_type: str
    chapter_section: str
    statement_sha256: str
    char_count: int
    layer: str
    structural_refs: list[str] = field(default_factory=list)
    representation_profile: dict[str, Any] = field(default_factory=dict)
    node_type: str = "SOURCE_DECLARATION"
    amendment_id: str | None = None
    amendment_status: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        for forbidden in FORBIDDEN_PERSISTED_KEYS:
            d.pop(forbidden, None)
        return d


def compute_sha256(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def detect_foundation_representation_profile(text: str, title: str) -> dict[str, Any]:
    full_text = f"{title}\n{text}"
    eo_tags = [tag for tag, pat in FOUNDATION_EO_KEYWORDS.items() if pat.search(full_text)]
    geo_tags = [tag for tag, pat in FOUNDATION_GEO_KEYWORDS.items() if pat.search(full_text)]

    if eo_tags and geo_tags:
        direct_status = "DUAL_DIRECT"
    elif eo_tags:
        direct_status = "EO_ONLY_DIRECT"
    elif geo_tags:
        direct_status = "GEO_ONLY_DIRECT"
    else:
        direct_status = "THEORETIC_DIRECT"

    rep_kinds = [k for k, pat in REPRESENTATION_KINDS.items() if pat.search(full_text)]
    if not rep_kinds:
        rep_kinds = ["abstract"]

    return {
        "direct_status": direct_status,
        "eo_tags": eo_tags,
        "geo_tags": geo_tags,
        "representation_kinds": rep_kinds,
        "diversity_count": len(rep_kinds),
    }


def _declaration_identity(declaration: FoundationDeclaration) -> dict[str, Any]:
    return {
        "label": declaration.label,
        "decl_type": declaration.decl_type,
        "statement_sha256": declaration.statement_sha256,
        "structural_refs": declaration.structural_refs,
    }


def apply_foundation_mathematical_amendments(
    declarations: list[FoundationDeclaration],
    amendments_path: Path = FOUNDATION_AMENDMENTS_PATH,
) -> None:
    """Validate and annotate the exact active correction projection.

    The registry records statement identity changes only.  It is not proof or
    kernel evidence, and an omitted or falsely listed changed row fails closed.
    """
    payload = json.loads(amendments_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "1.0.0":
        raise ValueError("unsupported foundation amendment schema")
    if payload.get("claim_boundary") != "STATEMENT_CORRECTION_ONLY_NOT_PROOF":
        raise ValueError("foundation amendment claim boundary is invalid")

    by_id = {item.node_id: item for item in declarations}
    if len(by_id) != len(declarations):
        raise ValueError("duplicate foundation declaration identity")
    historical = payload.get("historical_rows")
    if not isinstance(historical, dict) or set(historical) != set(by_id):
        raise ValueError("historical foundation registry is incomplete or overbroad")
    historical_digest = hashlib.sha256(
        json.dumps(
            historical,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    if historical_digest != FOUNDATION_HISTORICAL_ROWS_SHA256:
        raise ValueError("historical foundation baseline digest mismatch")
    if payload.get("historical_source") != FOUNDATION_HISTORICAL_SOURCE:
        raise ValueError("historical foundation source identity mismatch")

    changed_ids = {
        node_id
        for node_id, declaration in by_id.items()
        if historical[node_id] != _declaration_identity(declaration)
    }
    records = payload.get("amendments")
    if not isinstance(records, list):
        raise ValueError("foundation amendments must be a list")
    records_by_id: dict[str, dict[str, Any]] = {}
    for record in records:
        node_id = record.get("subject_id")
        if not isinstance(node_id, str) or node_id in records_by_id:
            raise ValueError("duplicate or invalid foundation amendment subject")
        records_by_id[node_id] = record
    if set(records_by_id) != changed_ids:
        raise ValueError("foundation amendment registry omits or falsely lists a changed row")

    for node_id, record in records_by_id.items():
        declaration = by_id[node_id]
        if record.get("status") != "ACTIVE_STATEMENT_AMENDMENT_UNVERIFIED":
            raise ValueError(f"invalid foundation amendment status: {node_id}")
        if record.get("historical_identity") != historical[node_id]:
            raise ValueError(f"historical foundation identity mismatch: {node_id}")
        if record.get("corrected_identity") != _declaration_identity(declaration):
            raise ValueError(f"corrected foundation identity mismatch: {node_id}")
        reason = record.get("reason")
        if not isinstance(reason, str) or len(reason) < 20:
            raise ValueError(f"foundation amendment reason is missing: {node_id}")
        core = {
            "subject_id": node_id,
            "historical_identity": record["historical_identity"],
            "corrected_identity": record["corrected_identity"],
            "reason": reason,
        }
        digest = hashlib.sha256(
            json.dumps(
                core,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            ).encode("utf-8")
        ).hexdigest()
        if record.get("amendment_sha256") != digest:
            raise ValueError(f"foundation amendment digest mismatch: {node_id}")
        amendment_id = record.get("amendment_id")
        expected_amendment_id = (
            "amendment:v0.20:foundation:"
            + node_id.removeprefix("srcdecl:foundation:").replace(":", "-")
        )
        if amendment_id != expected_amendment_id:
            raise ValueError(f"foundation amendment ID is invalid: {node_id}")
        declaration.amendment_id = amendment_id
        declaration.amendment_status = record["status"]


def generate_foundation_declarations() -> list[FoundationDeclaration]:
    """Generate curated, source-attributed foundational declarations across 8 layers.

    All mathematical statements are parsed strictly in memory and hashed with SHA-256.
    Zero prose text is persisted.
    """
    raw_declarations: list[dict[str, Any]] = [
        # =========================================================================
        # LAYER 1: LOGIC & PROOFS (20 Declarations)
        # =========================================================================
        {
            "node_id": "srcdecl:foundation:logic:proposition",
            "label": "Definition of Proposition / Statement",
            "decl_type": "DEFINITION",
            "layer": "logic",
            "chapter_section": "Logic §1.1",
            "structural_refs": [],
            "text": "In classical bivalent propositional semantics, a valuation assigns each atomic proposition exactly one truth value in {False, True}; compound propositions receive truth values from their truth-functional connectives.",
        },
        {
            "node_id": "srcdecl:foundation:logic:negation",
            "label": "Definition of Logical Negation (NOT)",
            "decl_type": "DEFINITION",
            "layer": "logic",
            "chapter_section": "Logic §1.2",
            "structural_refs": ["srcdecl:foundation:logic:proposition"],
            "text": "Given proposition P, its negation not-P (¬P) is true if and only if P is false.",
        },
        {
            "node_id": "srcdecl:foundation:logic:conjunction",
            "label": "Definition of Logical Conjunction (AND)",
            "decl_type": "DEFINITION",
            "layer": "logic",
            "chapter_section": "Logic §1.2",
            "structural_refs": ["srcdecl:foundation:logic:proposition"],
            "text": "Given propositions P and Q, the conjunction P and Q (P ∧ Q) is true if and only if both P and Q are true.",
        },
        {
            "node_id": "srcdecl:foundation:logic:disjunction",
            "label": "Definition of Logical Disjunction (OR)",
            "decl_type": "DEFINITION",
            "layer": "logic",
            "chapter_section": "Logic §1.2",
            "structural_refs": ["srcdecl:foundation:logic:proposition"],
            "text": "Given propositions P and Q, the disjunction P or Q (P ∨ Q) is true if at least one of P or Q is true, and false only when both are false.",
        },
        {
            "node_id": "srcdecl:foundation:logic:implication",
            "label": "Definition of Material Implication (Conditional)",
            "decl_type": "DEFINITION",
            "layer": "logic",
            "chapter_section": "Logic §1.3",
            "structural_refs": ["srcdecl:foundation:logic:proposition", "srcdecl:foundation:logic:negation", "srcdecl:foundation:logic:disjunction"],
            "text": "The conditional statement P implies Q (P => Q) is false if and only if P is true and Q is false. Logically equivalent to (¬P ∨ Q).",
        },
        {
            "node_id": "srcdecl:foundation:logic:biconditional",
            "label": "Definition of Logical Equivalence (Biconditional)",
            "decl_type": "DEFINITION",
            "layer": "logic",
            "chapter_section": "Logic §1.3",
            "structural_refs": ["srcdecl:foundation:logic:implication", "srcdecl:foundation:logic:conjunction"],
            "text": "The biconditional statement P if and only if Q (P <=> Q) is true when P and Q have identical truth values; equivalent to (P => Q) ∧ (Q => P).",
        },
        {
            "node_id": "srcdecl:foundation:logic:truth_table",
            "label": "Truth Table Functional Semantics",
            "decl_type": "DEFINITION",
            "layer": "logic",
            "chapter_section": "Logic §1.4",
            "structural_refs": ["srcdecl:foundation:logic:conjunction", "srcdecl:foundation:logic:disjunction", "srcdecl:foundation:logic:negation"],
            "text": "A truth table specifies the output truth value of a compound boolean proposition for all possible truth value assignments to its constituent atomic propositions.",
        },
        {
            "node_id": "srcdecl:foundation:logic:tautology",
            "label": "Definition of Tautology and Contradiction",
            "decl_type": "DEFINITION",
            "layer": "logic",
            "chapter_section": "Logic §1.4",
            "structural_refs": ["srcdecl:foundation:logic:truth_table"],
            "text": "A compound proposition is a tautology if it evaluates to true under all truth assignments, and a contradiction if it evaluates to false under all truth assignments.",
        },
        {
            "node_id": "srcdecl:foundation:logic:de_morgan_logic",
            "label": "De Morgan's Laws for Propositional Logic",
            "decl_type": "THEOREM",
            "layer": "logic",
            "chapter_section": "Logic §1.5",
            "structural_refs": ["srcdecl:foundation:logic:negation", "srcdecl:foundation:logic:conjunction", "srcdecl:foundation:logic:disjunction"],
            "text": "For propositions P and Q: ¬(P ∧ Q) <=> (¬P ∨ ¬Q), and ¬(P ∨ Q) <=> (¬P ∧ ¬Q).",
        },
        {
            "node_id": "srcdecl:foundation:logic:modus_ponens",
            "label": "Rule of Inference: Modus Ponens",
            "decl_type": "THEOREM",
            "layer": "logic",
            "chapter_section": "Logic §1.6",
            "structural_refs": ["srcdecl:foundation:logic:implication"],
            "text": "From premise P and conditional premise (P => Q), one validly infers conclusion Q. That is, (P ∧ (P => Q)) => Q is a tautology.",
        },
        {
            "node_id": "srcdecl:foundation:logic:modus_tollens",
            "label": "Rule of Inference: Modus Tollens",
            "decl_type": "THEOREM",
            "layer": "logic",
            "chapter_section": "Logic §1.6",
            "structural_refs": ["srcdecl:foundation:logic:implication", "srcdecl:foundation:logic:negation"],
            "text": "From premise ¬Q and conditional premise (P => Q), one validly infers conclusion ¬P. That is, (¬Q ∧ (P => Q)) => ¬P is a tautology.",
        },
        {
            "node_id": "srcdecl:foundation:logic:direct_proof",
            "label": "Direct Proof Method",
            "decl_type": "DEFINITION",
            "layer": "logic",
            "chapter_section": "Logic §1.7",
            "structural_refs": ["srcdecl:foundation:logic:implication", "srcdecl:foundation:logic:modus_ponens"],
            "text": "A direct proof of P => Q assumes premise P is true and constructs a sequence of deductive steps leading to conclusion Q.",
        },
        {
            "node_id": "srcdecl:foundation:logic:contrapositive_proof",
            "label": "Contrapositive Equivalence and Proof Method",
            "decl_type": "THEOREM",
            "layer": "logic",
            "chapter_section": "Logic §1.7",
            "structural_refs": ["srcdecl:foundation:logic:implication", "srcdecl:foundation:logic:negation"],
            "text": "Under classical bivalent semantics, the material conditional (P => Q) is logically equivalent to its contrapositive (¬Q => ¬P); a proof by contraposition establishes the latter. The reverse implication from a contrapositive proof is not asserted here for weaker non-classical logics.",
        },
        {
            "node_id": "srcdecl:foundation:logic:proof_by_contradiction",
            "label": "Proof by Contradiction (Reductio ad Absurdum)",
            "decl_type": "THEOREM",
            "layer": "logic",
            "chapter_section": "Logic §1.8",
            "structural_refs": ["srcdecl:foundation:logic:negation", "srcdecl:foundation:logic:tautology"],
            "text": "In classical logic, reductio ad absurdum proves P by deriving False from ¬P and then applying double-negation elimination ¬¬P => P. Intuitionistically, the derivation establishes only ¬¬P unless P is stable.",
        },
        {
            "node_id": "srcdecl:foundation:logic:universal_quantifier",
            "label": "Definition of Universal Quantifier (FOR ALL)",
            "decl_type": "DEFINITION",
            "layer": "logic",
            "chapter_section": "Logic §1.9",
            "structural_refs": ["srcdecl:foundation:logic:proposition"],
            "text": "The universal quantification ∀x P(x) asserts predicate P(x) is true for all elements x in universe of discourse U.",
        },
        {
            "node_id": "srcdecl:foundation:logic:existential_quantifier",
            "label": "Definition of Existential Quantifier (THERE EXISTS)",
            "decl_type": "DEFINITION",
            "layer": "logic",
            "chapter_section": "Logic §1.9",
            "structural_refs": ["srcdecl:foundation:logic:proposition"],
            "text": "The existential quantification ∃x P(x) asserts there exists at least one element x in universe U such that P(x) is true.",
        },
        {
            "node_id": "srcdecl:foundation:logic:quantifier_negation",
            "label": "Quantifier Negation Dualities",
            "decl_type": "THEOREM",
            "layer": "logic",
            "chapter_section": "Logic §1.9",
            "structural_refs": ["srcdecl:foundation:logic:universal_quantifier", "srcdecl:foundation:logic:existential_quantifier", "srcdecl:foundation:logic:negation"],
            "text": "For a predicate P over a fixed domain, classical logic validates ¬(∀x P(x)) <=> ∃x ¬P(x) and ¬(∃x P(x)) <=> ∀x ¬P(x); without classical principles the first left-to-right implication need not hold.",
        },
        {
            "node_id": "srcdecl:foundation:logic:distributive_logic",
            "label": "Distributive Laws of Propositional Logic",
            "decl_type": "THEOREM",
            "layer": "logic",
            "chapter_section": "Logic §1.5",
            "structural_refs": ["srcdecl:foundation:logic:conjunction", "srcdecl:foundation:logic:disjunction"],
            "text": "P ∧ (Q ∨ R) <=> (P ∧ Q) ∨ (P ∧ R), and P ∨ (Q ∧ R) <=> (P ∨ Q) ∧ (P ∨ R).",
        },
        {
            "node_id": "srcdecl:foundation:logic:law_of_excluded_middle",
            "label": "Classical Law of Excluded Middle",
            "decl_type": "AXIOM",
            "layer": "logic",
            "chapter_section": "Logic §1.1",
            "structural_refs": ["srcdecl:foundation:logic:negation", "srcdecl:foundation:logic:disjunction", "srcdecl:foundation:logic:conjunction"],
            "text": "The classical Law of Excluded Middle is the axiom schema P ∨ ¬P for every proposition P. The constructively valid theorem ¬(P ∧ ¬P) is not the same assertion and is not bundled into this classical axiom schema.",
        },
        {
            "node_id": "srcdecl:foundation:logic:hypothetical_syllogism",
            "label": "Rule of Hypothetical Syllogism (Transitivity of Implication)",
            "decl_type": "THEOREM",
            "layer": "logic",
            "chapter_section": "Logic §1.6",
            "structural_refs": ["srcdecl:foundation:logic:implication"],
            "text": "((P => Q) ∧ (Q => R)) => (P => R) is a valid deductive inference rule and tautology.",
        },

        # =========================================================================
        # LAYER 2: SET THEORY (22 Declarations)
        # =========================================================================
        {
            "node_id": "srcdecl:foundation:set:element_membership",
            "label": "Primitive Set Membership",
            "decl_type": "DEFINITION",
            "layer": "sets",
            "chapter_section": "Sets §2.1",
            "structural_refs": [],
            "text": "Membership x in A is the primitive non-logical relation of the set theory used here; it is not defined by calling a set a collection. Equality of sets is governed separately by the Extensionality axiom.",
        },
        {
            "node_id": "srcdecl:foundation:set:empty_set",
            "label": "Empty Set Axiom and Definition",
            "decl_type": "AXIOM",
            "layer": "sets",
            "chapter_section": "Sets §2.1",
            "structural_refs": ["srcdecl:foundation:set:element_membership"],
            "text": "The Empty Set axiom asserts that there exists a set E with no elements. Extensionality makes it unique; this set is denoted ∅, so for every x, x not-in ∅.",
        },
        {
            "node_id": "srcdecl:foundation:set:subset_definition",
            "label": "Definition of Subset and Superset",
            "decl_type": "DEFINITION",
            "layer": "sets",
            "chapter_section": "Sets §2.2",
            "structural_refs": ["srcdecl:foundation:set:element_membership"],
            "text": "A is a subset of B (A ⊆ B) iff every element of A belongs to B: ∀x (x in A => x in B).",
        },
        {
            "node_id": "srcdecl:foundation:set:proper_subset",
            "label": "Definition of Proper Subset",
            "decl_type": "DEFINITION",
            "layer": "sets",
            "chapter_section": "Sets §2.2",
            "structural_refs": ["srcdecl:foundation:set:subset_definition"],
            "text": "A is a proper subset of B (A ⊂ B) iff A ⊆ B and A ≠ B.",
        },
        {
            "node_id": "srcdecl:foundation:set:union",
            "label": "Pairing and Union Axioms; Binary Union",
            "decl_type": "AXIOM",
            "layer": "sets",
            "chapter_section": "Sets §2.3",
            "structural_refs": ["srcdecl:foundation:set:element_membership", "srcdecl:foundation:set:axiom_of_extensionality"],
            "text": "The Pairing axiom gives {A,B}, and the Union axiom gives a set containing exactly the members of members of {A,B}. Their binary union A ∪ B therefore exists and satisfies x in A ∪ B iff x in A or x in B.",
        },
        {
            "node_id": "srcdecl:foundation:set:intersection",
            "label": "Definition of Set Intersection",
            "decl_type": "DEFINITION",
            "layer": "sets",
            "chapter_section": "Sets §2.3",
            "structural_refs": ["srcdecl:foundation:set:element_membership", "srcdecl:foundation:set:axiom_of_specification"],
            "text": "For sets A and B, Separation applied to A gives the intersection A ∩ B = {x in A | x in B}; hence x in A ∩ B iff x in A and x in B.",
        },
        {
            "node_id": "srcdecl:foundation:set:set_difference",
            "label": "Definition of Set Difference (Relative Complement)",
            "decl_type": "DEFINITION",
            "layer": "sets",
            "chapter_section": "Sets §2.3",
            "structural_refs": ["srcdecl:foundation:set:element_membership", "srcdecl:foundation:set:axiom_of_specification"],
            "text": "For sets A and B, Separation applied to A gives the difference A \\ B = {x in A | x not-in B}; hence x in A \\ B iff x in A and x not-in B.",
        },
        {
            "node_id": "srcdecl:foundation:set:complement",
            "label": "Definition of Absolute Complement",
            "decl_type": "DEFINITION",
            "layer": "sets",
            "chapter_section": "Sets §2.3",
            "structural_refs": ["srcdecl:foundation:set:set_difference"],
            "text": "Relative to a fixed set U and a subset A of U, the complement A^c means U \\ A = {x in U | x not-in A}. No absolute universal set is assumed.",
        },
        {
            "node_id": "srcdecl:foundation:set:power_set",
            "label": "Power Set Axiom",
            "decl_type": "AXIOM",
            "layer": "sets",
            "chapter_section": "Sets §2.4",
            "structural_refs": ["srcdecl:foundation:set:subset_definition"],
            "text": "The Power Set axiom asserts that for every set X there exists a set P(X) whose elements are exactly the subsets of X.",
        },
        {
            "node_id": "srcdecl:foundation:set:ordered_pair",
            "label": "Definition of Kuratowski Ordered Pair",
            "decl_type": "DEFINITION",
            "layer": "sets",
            "chapter_section": "Sets §2.5",
            "structural_refs": ["srcdecl:foundation:set:element_membership", "srcdecl:foundation:set:union"],
            "text": "Using the Pairing axiom, the Kuratowski ordered pair is (a, b) = {{a}, {a, b}}; Extensionality proves (a, b) = (c, d) iff a = c and b = d.",
        },
        {
            "node_id": "srcdecl:foundation:set:cartesian_product",
            "label": "Definition of Cartesian Product",
            "decl_type": "DEFINITION",
            "layer": "sets",
            "chapter_section": "Sets §2.5",
            "structural_refs": ["srcdecl:foundation:set:ordered_pair", "srcdecl:foundation:set:power_set", "srcdecl:foundation:set:axiom_of_specification"],
            "text": "For sets A and B, Pairing, Union, Power Set, and Separation ensure that the Cartesian product A × B exists as {(a, b) | a in A and b in B}, a subset of P(P(A ∪ B)).",
        },
        {
            "node_id": "srcdecl:foundation:set:disjoint_sets",
            "label": "Definition of Disjoint Sets",
            "decl_type": "DEFINITION",
            "layer": "sets",
            "chapter_section": "Sets §2.3",
            "structural_refs": ["srcdecl:foundation:set:intersection", "srcdecl:foundation:set:empty_set"],
            "text": "Two sets A and B are disjoint iff their intersection is empty: A ∩ B = ∅. A family is pairwise disjoint if A_i ∩ A_j = ∅ for all i ≠ j.",
        },
        {
            "node_id": "srcdecl:foundation:set:set_partition",
            "label": "Definition of Set Partition",
            "decl_type": "DEFINITION",
            "layer": "sets",
            "chapter_section": "Sets §2.6",
            "structural_refs": ["srcdecl:foundation:set:disjoint_sets", "srcdecl:foundation:set:union"],
            "text": "A partition of a set X is a set P of nonempty subsets of X such that distinct members of P are disjoint and the union of the set P is X.",
        },
        {
            "node_id": "srcdecl:foundation:set:de_morgan_sets",
            "label": "De Morgan's Laws for Sets",
            "decl_type": "THEOREM",
            "layer": "sets",
            "chapter_section": "Sets §2.3",
            "structural_refs": ["srcdecl:foundation:set:complement", "srcdecl:foundation:set:union", "srcdecl:foundation:set:intersection"],
            "text": "For subsets A, B of U: (A ∪ B)^c = A^c ∩ B^c, and (A ∩ B)^c = A^c ∪ B^c.",
        },
        {
            "node_id": "srcdecl:foundation:set:distributive_laws_sets",
            "label": "Distributive Laws of Set Operations",
            "decl_type": "THEOREM",
            "layer": "sets",
            "chapter_section": "Sets §2.3",
            "structural_refs": ["srcdecl:foundation:set:union", "srcdecl:foundation:set:intersection"],
            "text": "A ∩ (B ∪ C) = (A ∩ B) ∪ (A ∩ C), and A ∪ (B ∩ C) = (A ∪ B) ∩ (A ∪ C).",
        },
        {
            "node_id": "srcdecl:foundation:set:inclusion_exclusion_finite",
            "label": "Principle of Inclusion-Exclusion (Finite Sets)",
            "decl_type": "THEOREM",
            "layer": "sets",
            "chapter_section": "Sets §2.7",
            "structural_refs": ["srcdecl:foundation:set:union", "srcdecl:foundation:set:intersection"],
            "text": "For finite sets A and B: |A ∪ B| = |A| + |B| - |A ∩ B|.",
        },
        {
            "node_id": "srcdecl:foundation:set:arbitrary_union_intersection",
            "label": "Arbitrary (Indexed) Union and Intersection",
            "decl_type": "DEFINITION",
            "layer": "sets",
            "chapter_section": "Sets §2.8",
            "structural_refs": ["srcdecl:foundation:set:union", "srcdecl:foundation:set:intersection"],
            "text": "For a set-sized indexed family {A_i}_{i in I}, the Union axiom gives union_{i in I} A_i = {x | exists i in I, x in A_i}. If I is nonempty, Separation from one A_i gives intersection_{i in I} A_i = {x | for every i in I, x in A_i}; an empty intersection requires a separately fixed universe.",
        },
        {
            "node_id": "srcdecl:foundation:set:axiom_of_specification",
            "label": "Axiom Schema of Specification (Separation)",
            "decl_type": "AXIOM",
            "layer": "sets",
            "chapter_section": "Sets §2.1",
            "structural_refs": ["srcdecl:foundation:set:element_membership"],
            "text": "Given a set X and predicate P(x), there exists a set Y = {x in X | P(x)} consisting of precisely those elements of X satisfying P.",
        },
        {
            "node_id": "srcdecl:foundation:set:indicator_function",
            "label": "Definition of Characteristic / Indicator Function",
            "decl_type": "DEFINITION",
            "layer": "sets",
            "chapter_section": "Sets §2.9",
            "structural_refs": ["srcdecl:foundation:set:subset_definition"],
            "text": "The indicator function 1_A: X -> {0, 1} of subset A ⊆ X is defined by 1_A(x) = 1 if x in A, and 0 if x not-in A.",
        },
        {
            "node_id": "srcdecl:foundation:set:indicator_algebra",
            "label": "Algebra of Indicator Functions",
            "decl_type": "THEOREM",
            "layer": "sets",
            "chapter_section": "Sets §2.9",
            "structural_refs": ["srcdecl:foundation:set:indicator_function", "srcdecl:foundation:set:intersection", "srcdecl:foundation:set:union", "srcdecl:foundation:set:complement"],
            "text": "For subsets A and B of one fixed universe X, indicator functions on X satisfy 1_{A ∩ B} = 1_A · 1_B, 1_{X \\ A} = 1 - 1_A, and 1_{A ∪ B} = 1_A + 1_B - 1_A · 1_B.",
        },
        {
            "node_id": "srcdecl:foundation:set:axiom_of_extensionality",
            "label": "Axiom of Extensionality",
            "decl_type": "AXIOM",
            "layer": "sets",
            "chapter_section": "Sets §2.1",
            "structural_refs": ["srcdecl:foundation:set:element_membership"],
            "text": "If two sets have exactly the same elements, then they are equal: (∀x (x in A <=> x in B)) => A = B.",
        },
        {
            "node_id": "srcdecl:foundation:set:axiom_of_choice_primitive",
            "label": "Axiom of Choice (Elementary Formulation)",
            "decl_type": "AXIOM",
            "layer": "sets",
            "chapter_section": "Sets §2.10",
            "structural_refs": ["srcdecl:foundation:set:cartesian_product", "srcdecl:foundation:set:empty_set"],
            "text": "For every set I and every set-indexed family (A_i)_{i in I} of nonempty sets, the Axiom of Choice asserts that there exists a function f with domain I such that f(i) in A_i for every i in I; pairwise disjointness is not required.",
        },

        # =========================================================================
        # LAYER 3: RELATIONS & FUNCTIONS (22 Declarations)
        # =========================================================================
        {
            "node_id": "srcdecl:foundation:rel:binary_relation",
            "label": "Definition of Binary Relation",
            "decl_type": "DEFINITION",
            "layer": "relations_functions",
            "chapter_section": "Relations §3.1",
            "structural_refs": ["srcdecl:foundation:set:cartesian_product"],
            "text": "A binary relation R from set X to set Y is a subset R ⊆ X × Y. We write x R y iff (x, y) in R.",
        },
        {
            "node_id": "srcdecl:foundation:rel:reflexive_relation",
            "label": "Definition of Reflexive Relation",
            "decl_type": "DEFINITION",
            "layer": "relations_functions",
            "chapter_section": "Relations §3.2",
            "structural_refs": ["srcdecl:foundation:rel:binary_relation"],
            "text": "A relation R on X is reflexive iff ∀x in X (x R x).",
        },
        {
            "node_id": "srcdecl:foundation:rel:symmetric_relation",
            "label": "Definition of Symmetric Relation",
            "decl_type": "DEFINITION",
            "layer": "relations_functions",
            "chapter_section": "Relations §3.2",
            "structural_refs": ["srcdecl:foundation:rel:binary_relation"],
            "text": "A relation R on X is symmetric iff ∀x, y in X (x R y => y R x).",
        },
        {
            "node_id": "srcdecl:foundation:rel:transitive_relation",
            "label": "Definition of Transitive Relation",
            "decl_type": "DEFINITION",
            "layer": "relations_functions",
            "chapter_section": "Relations §3.2",
            "structural_refs": ["srcdecl:foundation:rel:binary_relation"],
            "text": "A relation R on X is transitive iff ∀x, y, z in X ((x R y ∧ y R z) => x R z).",
        },
        {
            "node_id": "srcdecl:foundation:rel:antisymmetric_relation",
            "label": "Definition of Antisymmetric Relation",
            "decl_type": "DEFINITION",
            "layer": "relations_functions",
            "chapter_section": "Relations §3.2",
            "structural_refs": ["srcdecl:foundation:rel:binary_relation"],
            "text": "A relation R on X is antisymmetric iff ∀x, y in X ((x R y ∧ y R x) => x = y).",
        },
        {
            "node_id": "srcdecl:foundation:rel:equivalence_relation",
            "label": "Definition of Equivalence Relation",
            "decl_type": "DEFINITION",
            "layer": "relations_functions",
            "chapter_section": "Relations §3.3",
            "structural_refs": ["srcdecl:foundation:rel:reflexive_relation", "srcdecl:foundation:rel:symmetric_relation", "srcdecl:foundation:rel:transitive_relation"],
            "text": "A relation ~ on X is an equivalence relation iff it is reflexive, symmetric, and transitive.",
        },
        {
            "node_id": "srcdecl:foundation:rel:equivalence_class",
            "label": "Definition of Equivalence Class",
            "decl_type": "DEFINITION",
            "layer": "relations_functions",
            "chapter_section": "Relations §3.3",
            "structural_refs": ["srcdecl:foundation:rel:equivalence_relation"],
            "text": "Given equivalence relation ~ on X and x in X, the equivalence class of x is [x] = {y in X | y ~ x}.",
        },
        {
            "node_id": "srcdecl:foundation:rel:quotient_set",
            "label": "Definition of Quotient Set",
            "decl_type": "DEFINITION",
            "layer": "relations_functions",
            "chapter_section": "Relations §3.3",
            "structural_refs": ["srcdecl:foundation:rel:equivalence_class"],
            "text": "The quotient set X/~ is the set of all equivalence classes of elements of X: X/~ = {[x] | x in X}.",
        },
        {
            "node_id": "srcdecl:foundation:rel:fundamental_theorem_equivalence",
            "label": "Fundamental Theorem of Equivalence Relations",
            "decl_type": "THEOREM",
            "layer": "relations_functions",
            "chapter_section": "Relations §3.4",
            "structural_refs": ["srcdecl:foundation:rel:quotient_set", "srcdecl:foundation:set:set_partition"],
            "text": "Every equivalence relation ~ on X induces the partition X/~. Conversely, for a partition P of X define x ~_P y iff there exists A in P with x in A and y in A; this is an equivalence relation whose classes are exactly the members of P.",
        },
        {
            "node_id": "srcdecl:foundation:rel:partial_order",
            "label": "Definition of Partial Order (Poset)",
            "decl_type": "DEFINITION",
            "layer": "relations_functions",
            "chapter_section": "Relations §3.5",
            "structural_refs": ["srcdecl:foundation:rel:reflexive_relation", "srcdecl:foundation:rel:antisymmetric_relation", "srcdecl:foundation:rel:transitive_relation"],
            "text": "A relation <= on X is a partial order iff it is reflexive, antisymmetric, and transitive. A set equipped with a partial order is a poset.",
        },
        {
            "node_id": "srcdecl:foundation:rel:total_order",
            "label": "Definition of Total Order",
            "decl_type": "DEFINITION",
            "layer": "relations_functions",
            "chapter_section": "Relations §3.5",
            "structural_refs": ["srcdecl:foundation:rel:partial_order"],
            "text": "A partial order <= on X is a total (or linear) order iff for all x, y in X, either x <= y or y <= x (totality/comparability).",
        },
        {
            "node_id": "srcdecl:foundation:rel:function_definition",
            "label": "Definition of Function / Mapping",
            "decl_type": "DEFINITION",
            "layer": "relations_functions",
            "chapter_section": "Functions §3.6",
            "structural_refs": ["srcdecl:foundation:rel:binary_relation"],
            "text": "A function f: X -> Y is a relation f ⊆ X × Y such that for every x in X there exists a unique y in Y with (x, y) in f; we write f(x) = y.",
        },
        {
            "node_id": "srcdecl:foundation:rel:domain_codomain_image",
            "label": "Domain, Codomain, and Range / Image",
            "decl_type": "DEFINITION",
            "layer": "relations_functions",
            "chapter_section": "Functions §3.6",
            "structural_refs": ["srcdecl:foundation:rel:function_definition"],
            "text": "For f: X -> Y, X is domain, Y is codomain, and image im(f) = f(X) = {f(x) | x in X} ⊆ Y.",
        },
        {
            "node_id": "srcdecl:foundation:rel:preimage_fiber",
            "label": "Preimage (Inverse Image) and Fiber",
            "decl_type": "DEFINITION",
            "layer": "relations_functions",
            "chapter_section": "Functions §3.6",
            "structural_refs": ["srcdecl:foundation:rel:function_definition"],
            "text": "For f: X -> Y and B ⊆ Y, the preimage f^{-1}(B) is {x in X | f(x) in B}. For y in Y, fiber over y is f^{-1}({y}).",
        },
        {
            "node_id": "srcdecl:foundation:rel:injective_function",
            "label": "Definition of Injective (One-to-One) Function",
            "decl_type": "DEFINITION",
            "layer": "relations_functions",
            "chapter_section": "Functions §3.7",
            "structural_refs": ["srcdecl:foundation:rel:function_definition"],
            "text": "f: X -> Y is injective iff ∀x_1, x_2 in X (f(x_1) = f(x_2) => x_1 = x_2).",
        },
        {
            "node_id": "srcdecl:foundation:rel:surjective_function",
            "label": "Definition of Surjective (Onto) Function",
            "decl_type": "DEFINITION",
            "layer": "relations_functions",
            "chapter_section": "Functions §3.7",
            "structural_refs": ["srcdecl:foundation:rel:function_definition", "srcdecl:foundation:rel:domain_codomain_image"],
            "text": "f: X -> Y is surjective iff im(f) = Y, i.e., ∀y in Y ∃x in X (f(x) = y).",
        },
        {
            "node_id": "srcdecl:foundation:rel:bijective_function",
            "label": "Definition of Bijective (One-to-One and Onto) Function",
            "decl_type": "DEFINITION",
            "layer": "relations_functions",
            "chapter_section": "Functions §3.7",
            "structural_refs": ["srcdecl:foundation:rel:injective_function", "srcdecl:foundation:rel:surjective_function"],
            "text": "f: X -> Y is bijective iff f is both injective and surjective.",
        },
        {
            "node_id": "srcdecl:foundation:rel:function_composition",
            "label": "Definition of Function Composition",
            "decl_type": "DEFINITION",
            "layer": "relations_functions",
            "chapter_section": "Functions §3.8",
            "structural_refs": ["srcdecl:foundation:rel:function_definition"],
            "text": "For f: X -> Y and g: Y -> Z, composite function g ∘ f: X -> Z is defined by (g ∘ f)(x) = g(f(x)).",
        },
        {
            "node_id": "srcdecl:foundation:rel:associativity_composition",
            "label": "Associativity of Function Composition",
            "decl_type": "THEOREM",
            "layer": "relations_functions",
            "chapter_section": "Functions §3.8",
            "structural_refs": ["srcdecl:foundation:rel:function_composition"],
            "text": "For f: X -> Y, g: Y -> Z, h: Z -> W, h ∘ (g ∘ f) = (h ∘ g) ∘ f.",
        },
        {
            "node_id": "srcdecl:foundation:rel:identity_function",
            "label": "Definition of Identity Function",
            "decl_type": "DEFINITION",
            "layer": "relations_functions",
            "chapter_section": "Functions §3.8",
            "structural_refs": ["srcdecl:foundation:rel:function_definition"],
            "text": "The identity function on set X is id_X: X -> X defined by id_X(x) = x for all x in X.",
        },
        {
            "node_id": "srcdecl:foundation:rel:inverse_function",
            "label": "Definition of Inverse Function",
            "decl_type": "DEFINITION",
            "layer": "relations_functions",
            "chapter_section": "Functions §3.9",
            "structural_refs": ["srcdecl:foundation:rel:function_composition", "srcdecl:foundation:rel:identity_function"],
            "text": "f: X -> Y has inverse g: Y -> X iff g ∘ f = id_X and f ∘ g = id_Y. We write g = f^{-1}.",
        },
        {
            "node_id": "srcdecl:foundation:rel:invertibility_criterion",
            "label": "Bijectivity and Invertibility Equivalence",
            "decl_type": "THEOREM",
            "layer": "relations_functions",
            "chapter_section": "Functions §3.9",
            "structural_refs": ["srcdecl:foundation:rel:bijective_function", "srcdecl:foundation:rel:inverse_function"],
            "text": "A function f: X -> Y has a two-sided inverse f^{-1}: Y -> X if and only if f is bijective.",
        },

        # =========================================================================
        # LAYER 4: NUMBER SYSTEMS (20 Declarations)
        # =========================================================================
        {
            "node_id": "srcdecl:foundation:num:peano_axioms_naturals",
            "label": "Peano Axioms for Natural Numbers",
            "decl_type": "AXIOM",
            "layer": "number_systems",
            "chapter_section": "Numbers §4.1",
            "structural_refs": [],
            "text": "In the second-order Peano framework, 0 is in N, S: N -> N, S is injective, 0 is not a successor, and every subset containing 0 and closed under S equals N. Addition and multiplication are defined recursively, and m <= n iff there exists k in N with m + k = n.",
        },
        {
            "node_id": "srcdecl:foundation:num:principle_induction",
            "label": "Principle of Mathematical Induction",
            "decl_type": "THEOREM",
            "layer": "number_systems",
            "chapter_section": "Numbers §4.1",
            "structural_refs": ["srcdecl:foundation:num:peano_axioms_naturals"],
            "text": "If P(0) is true, and ∀k in N (P(k) => P(k+1)), then P(n) is true for all n in N.",
        },
        {
            "node_id": "srcdecl:foundation:num:well_ordering_principle",
            "label": "Well-Ordering Principle of Natural Numbers",
            "decl_type": "THEOREM",
            "layer": "number_systems",
            "chapter_section": "Numbers §4.1",
            "structural_refs": ["srcdecl:foundation:num:principle_induction"],
            "text": "Every non-empty subset S ⊆ N contains a least element: ∃m in S ∀x in S (m <= x). Equivalent to induction.",
        },
        {
            "node_id": "srcdecl:foundation:num:integers_construction",
            "label": "Construction of Integers as Quotient of N × N",
            "decl_type": "DEFINITION",
            "layer": "number_systems",
            "chapter_section": "Numbers §4.2",
            "structural_refs": ["srcdecl:foundation:rel:quotient_set", "srcdecl:foundation:num:peano_axioms_naturals", "srcdecl:foundation:rel:fundamental_theorem_equivalence"],
            "text": "The integers Z are equivalence classes [a,b] of N × N under (a,b) ~ (c,d) iff a + d = b + c. The well-defined operations are [a,b] + [c,d] = [a+c,b+d] and [a,b] * [c,d] = [ac+bd,ad+bc], with the induced total order.",
        },
        {
            "node_id": "srcdecl:foundation:num:integer_divisibility",
            "label": "Definition of Divisibility in Integers",
            "decl_type": "DEFINITION",
            "layer": "number_systems",
            "chapter_section": "Numbers §4.2",
            "structural_refs": ["srcdecl:foundation:num:integers_construction"],
            "text": "For all a, b in Z, including a = 0, a divides b (a | b) iff there exists k in Z such that b = a * k; consequently 0 divides only 0.",
        },
        {
            "node_id": "srcdecl:foundation:num:euclidean_division_algorithm",
            "label": "Euclidean Division Algorithm for Integers",
            "decl_type": "THEOREM",
            "layer": "number_systems",
            "chapter_section": "Numbers §4.2",
            "structural_refs": ["srcdecl:foundation:num:integers_construction", "srcdecl:foundation:num:well_ordering_principle"],
            "text": "For integers a and b > 0, there exist unique integers q (quotient) and r (remainder) such that a = b · q + r with 0 <= r < b.",
        },
        {
            "node_id": "srcdecl:foundation:num:rational_numbers_construction",
            "label": "Construction of Rational Numbers as Field of Fractions",
            "decl_type": "DEFINITION",
            "layer": "number_systems",
            "chapter_section": "Numbers §4.3",
            "structural_refs": ["srcdecl:foundation:rel:quotient_set", "srcdecl:foundation:num:integers_construction"],
            "text": "The rational numbers Q are equivalence classes [a,b] of Z × (Z \\ {0}) under (a,b) ~ (c,d) iff a*d = b*c. The well-defined field operations are [a,b] + [c,d] = [ad+bc,bd] and [a,b] * [c,d] = [ac,bd], with the induced order after choosing positive denominators.",
        },
        {
            "node_id": "srcdecl:foundation:num:rational_density",
            "label": "Density of Rational Numbers in Real Line",
            "decl_type": "THEOREM",
            "layer": "number_systems",
            "chapter_section": "Numbers §4.3",
            "structural_refs": ["srcdecl:foundation:num:rational_numbers_construction", "srcdecl:foundation:num:archimedean_property"],
            "text": "By the Archimedean property of the ordered field R containing Q, for real x < y there exists q in Q with x < q < y.",
        },
        {
            "node_id": "srcdecl:foundation:num:irrationality_sqrt_2",
            "label": "Existence of Irrationals: Irrationality of sqrt(2)",
            "decl_type": "THEOREM",
            "layer": "number_systems",
            "chapter_section": "Numbers §4.3",
            "structural_refs": ["srcdecl:foundation:num:rational_numbers_construction", "srcdecl:foundation:num:completeness_supremum", "srcdecl:foundation:logic:proof_by_contradiction"],
            "text": "Completeness gives a unique nonnegative real r with r^2 = 2. The parity argument proves that no rational q satisfies q^2 = 2; hence this real r, denoted sqrt(2), is irrational.",
        },
        {
            "node_id": "srcdecl:foundation:num:real_numbers_axioms",
            "label": "Axiomatic Definition of Real Numbers (Complete Ordered Field)",
            "decl_type": "AXIOM",
            "layer": "number_systems",
            "chapter_section": "Numbers §4.4",
            "structural_refs": ["srcdecl:foundation:num:rational_numbers_construction"],
            "text": "The real numbers R form a Dedekind-complete ordered field containing Q as an ordered subfield. Any two such complete ordered fields are uniquely order-field isomorphic by an isomorphism fixing Q, which is the intended categoricity statement.",
        },
        {
            "node_id": "srcdecl:foundation:num:completeness_supremum",
            "label": "Completeness Property: Least Upper Bound Axiom",
            "decl_type": "AXIOM",
            "layer": "number_systems",
            "chapter_section": "Numbers §4.4",
            "structural_refs": ["srcdecl:foundation:num:real_numbers_axioms"],
            "text": "Every non-empty subset S ⊆ R that is bounded above has a least upper bound (supremum) in R: sup(S) in R.",
        },
        {
            "node_id": "srcdecl:foundation:num:dedekind_cut_construction",
            "label": "Dedekind Cut Construction of Real Numbers",
            "decl_type": "DEFINITION",
            "layer": "number_systems",
            "chapter_section": "Numbers §4.4",
            "structural_refs": ["srcdecl:foundation:num:rational_numbers_construction"],
            "text": "A Dedekind cut is a proper nonempty lower subset A of Q with no greatest element. Ordered by inclusion and equipped with the standard cut addition, additive inverse, positive-cut multiplication, and sign extension, the set of cuts has well-defined field operations and is a Dedekind-complete ordered field.",
        },
        {
            "node_id": "srcdecl:foundation:num:cauchy_sequence_reals",
            "label": "Cauchy Sequence Metric Completion Construction of R",
            "decl_type": "DEFINITION",
            "layer": "number_systems",
            "chapter_section": "Numbers §4.4",
            "structural_refs": ["srcdecl:foundation:rel:quotient_set", "srcdecl:foundation:num:rational_numbers_construction"],
            "text": "Using the rational absolute-value metric, R is the quotient of the ring of rational Cauchy sequences by the null-sequence ideal: x ~ y iff x_n-y_n -> 0. Addition and multiplication are induced termwise, and the compatible order and completion embedding of Q are part of the construction.",
        },
        {
            "node_id": "srcdecl:foundation:num:archimedean_property",
            "label": "Archimedean Property of Real Numbers",
            "decl_type": "THEOREM",
            "layer": "number_systems",
            "chapter_section": "Numbers §4.4",
            "structural_refs": ["srcdecl:foundation:num:completeness_supremum"],
            "text": "For any positive real numbers x > 0 and y in R, there exists a natural number n in N such that n · x > y.",
        },
        {
            "node_id": "srcdecl:foundation:num:density_irrationals",
            "label": "Density of Irrational Numbers",
            "decl_type": "THEOREM",
            "layer": "number_systems",
            "chapter_section": "Numbers §4.4",
            "structural_refs": ["srcdecl:foundation:num:rational_density", "srcdecl:foundation:num:irrationality_sqrt_2"],
            "text": "Between any two distinct real numbers x < y, there exists an irrational number r in (R \\ Q) such that x < r < y.",
        },
        {
            "node_id": "srcdecl:foundation:num:complex_numbers_definition",
            "label": "Definition of Complex Numbers C",
            "decl_type": "DEFINITION",
            "layer": "number_systems",
            "chapter_section": "Numbers §4.5",
            "structural_refs": ["srcdecl:foundation:num:real_numbers_axioms", "srcdecl:foundation:set:cartesian_product"],
            "text": "The field of complex numbers C is R × R equipped with addition (a,b)+(c,d) = (a+c, b+d) and multiplication (a,b)·(c,d) = (ac-bd, ad+bc).",
        },
        {
            "node_id": "srcdecl:foundation:num:imaginary_unit",
            "label": "Definition of Imaginary Unit i",
            "decl_type": "DEFINITION",
            "layer": "number_systems",
            "chapter_section": "Numbers §4.5",
            "structural_refs": ["srcdecl:foundation:num:complex_numbers_definition"],
            "text": "The imaginary unit i = (0, 1) in C satisfies i^2 = -1. Every z in C is uniquely written z = a + bi with a, b in R.",
        },
        {
            "node_id": "srcdecl:foundation:num:complex_conjugate_modulus",
            "label": "Complex Conjugate and Absolute Value (Modulus)",
            "decl_type": "DEFINITION",
            "layer": "number_systems",
            "chapter_section": "Numbers §4.5",
            "structural_refs": ["srcdecl:foundation:num:imaginary_unit"],
            "text": "For z = a + bi in C, its conjugate is z_bar = a - bi. Its modulus |z| is the unique nonnegative real r satisfying r^2 = a^2 + b^2 = z*z_bar.",
        },
        {
            "node_id": "srcdecl:foundation:num:polar_form_complex",
            "label": "Polar Representation of Complex Numbers",
            "decl_type": "THEOREM",
            "layer": "number_systems",
            "chapter_section": "Numbers §4.5",
            "structural_refs": ["srcdecl:foundation:num:complex_conjugate_modulus", "srcdecl:foundation:geom:sine_cosine_unit_circle"],
            "text": "After the trigonometric functions are defined, every nonzero complex number z has a polar form z = r(cos theta + i sin theta), where r = |z| > 0 and theta is unique modulo 2*pi; choosing theta in [0,2*pi) gives one representative.",
        },
        {
            "node_id": "srcdecl:foundation:num:algebraic_closure_c_primitive",
            "label": "Algebraic Closure of Complex Numbers (Primitive Formulation)",
            "decl_type": "THEOREM",
            "layer": "number_systems",
            "chapter_section": "Numbers §4.5",
            "structural_refs": ["srcdecl:foundation:num:complex_numbers_definition", "srcdecl:foundation:alg:polynomial_definition"],
            "text": "The Fundamental Theorem of Algebra states that every nonconstant polynomial with complex coefficients has at least one complex root. The listed structural references identify its objects but do not constitute proof evidence.",
        },

        # =========================================================================
        # LAYER 5: ELEMENTARY ARITHMETIC & ALGEBRA (22 Declarations)
        # =========================================================================
        {
            "node_id": "srcdecl:foundation:alg:addition_operation",
            "label": "Binary Operation of Addition",
            "decl_type": "DEFINITION",
            "layer": "arithmetic_algebra",
            "chapter_section": "Algebra §5.1",
            "structural_refs": ["srcdecl:foundation:rel:function_definition"],
            "text": "Addition +: S × S -> S is a binary operation combining two elements a, b into a single sum a + b.",
        },
        {
            "node_id": "srcdecl:foundation:alg:multiplication_operation",
            "label": "Binary Operation of Multiplication",
            "decl_type": "DEFINITION",
            "layer": "arithmetic_algebra",
            "chapter_section": "Algebra §5.1",
            "structural_refs": ["srcdecl:foundation:rel:function_definition"],
            "text": "Multiplication ·: S × S -> S is a binary operation combining two elements a, b into product a · b.",
        },
        {
            "node_id": "srcdecl:foundation:alg:commutative_law",
            "label": "Commutative Property of Addition and Multiplication",
            "decl_type": "DEFINITION",
            "layer": "arithmetic_algebra",
            "chapter_section": "Algebra §5.1",
            "structural_refs": ["srcdecl:foundation:alg:addition_operation", "srcdecl:foundation:alg:multiplication_operation"],
            "text": "A binary operation circle on S is called commutative iff a circle b = b circle a for all a,b in S. Thus addition or multiplication is commutative only in a structure that imposes the corresponding law.",
        },
        {
            "node_id": "srcdecl:foundation:alg:associative_law",
            "label": "Associative Property of Addition and Multiplication",
            "decl_type": "DEFINITION",
            "layer": "arithmetic_algebra",
            "chapter_section": "Algebra §5.1",
            "structural_refs": ["srcdecl:foundation:alg:addition_operation", "srcdecl:foundation:alg:multiplication_operation"],
            "text": "A binary operation circle on S is called associative iff (a circle b) circle c = a circle (b circle c) for all a,b,c in S; arbitrary binary operations need not be associative.",
        },
        {
            "node_id": "srcdecl:foundation:alg:distributive_law",
            "label": "Distributive Property of Multiplication over Addition",
            "decl_type": "DEFINITION",
            "layer": "arithmetic_algebra",
            "chapter_section": "Algebra §5.1",
            "structural_refs": ["srcdecl:foundation:alg:addition_operation", "srcdecl:foundation:alg:multiplication_operation"],
            "text": "Two binary operations + and * on S are distributive iff a*(b+c)=a*b+a*c and (a+b)*c=a*c+b*c for all a,b,c in S; this is a property imposed on the pair of operations.",
        },
        {
            "node_id": "srcdecl:foundation:alg:identity_and_inverses",
            "label": "Additive and Multiplicative Identities and Inverses",
            "decl_type": "DEFINITION",
            "layer": "arithmetic_algebra",
            "chapter_section": "Algebra §5.1",
            "structural_refs": ["srcdecl:foundation:alg:addition_operation", "srcdecl:foundation:alg:multiplication_operation"],
            "text": "An additive identity 0, additive inverse -a, multiplicative identity 1, and multiplicative inverse a^{-1} are elements satisfying the usual equations when they exist; their existence is required separately by group, monoid, ring, or field axioms and is not automatic for arbitrary operations.",
        },
        {
            "node_id": "srcdecl:foundation:alg:group_axioms",
            "label": "Definition of Group Axioms",
            "decl_type": "DEFINITION",
            "layer": "arithmetic_algebra",
            "chapter_section": "Algebra §5.2",
            "structural_refs": ["srcdecl:foundation:alg:associative_law", "srcdecl:foundation:alg:identity_and_inverses"],
            "text": "A group (G, *) is a set with binary operation satisfying: closure, associativity, existence of identity element e, and existence of inverses for all elements.",
        },
        {
            "node_id": "srcdecl:foundation:alg:abelian_group",
            "label": "Definition of Abelian (Commutative) Group",
            "decl_type": "DEFINITION",
            "layer": "arithmetic_algebra",
            "chapter_section": "Algebra §5.2",
            "structural_refs": ["srcdecl:foundation:alg:group_axioms", "srcdecl:foundation:alg:commutative_law"],
            "text": "A group (G, *) is Abelian iff the operation is commutative: ∀a, b in G (a * b = b * a).",
        },
        {
            "node_id": "srcdecl:foundation:alg:ring_axioms",
            "label": "Definition of Ring Axioms",
            "decl_type": "DEFINITION",
            "layer": "arithmetic_algebra",
            "chapter_section": "Algebra §5.3",
            "structural_refs": ["srcdecl:foundation:alg:abelian_group", "srcdecl:foundation:alg:associative_law", "srcdecl:foundation:alg:identity_and_inverses", "srcdecl:foundation:alg:distributive_law"],
            "text": "Under the unital convention used here, a ring (R,+,*) is an Abelian group under +, multiplication is associative with identity 1, and multiplication distributes over addition; multiplication need not be commutative.",
        },
        {
            "node_id": "srcdecl:foundation:alg:field_axioms",
            "label": "Definition of Field Axioms",
            "decl_type": "DEFINITION",
            "layer": "arithmetic_algebra",
            "chapter_section": "Algebra §5.3",
            "structural_refs": ["srcdecl:foundation:alg:ring_axioms", "srcdecl:foundation:alg:commutative_law", "srcdecl:foundation:alg:identity_and_inverses"],
            "text": "A field (F, +, ·) is a commutative ring with 1 ≠ 0 where every non-zero element has a multiplicative inverse.",
        },
        {
            "node_id": "srcdecl:foundation:alg:subgroup_definition",
            "label": "Definition of Subgroup and Subgroup Criterion",
            "decl_type": "DEFINITION",
            "layer": "arithmetic_algebra",
            "chapter_section": "Algebra §5.2",
            "structural_refs": ["srcdecl:foundation:alg:group_axioms"],
            "text": "A non-empty subset H ⊆ G is a subgroup (H <= G) iff for all a, b in H, a * b^{-1} in H.",
        },
        {
            "node_id": "srcdecl:foundation:alg:group_homomorphism",
            "label": "Definition of Group Homomorphism and Kernel",
            "decl_type": "DEFINITION",
            "layer": "arithmetic_algebra",
            "chapter_section": "Algebra §5.2",
            "structural_refs": ["srcdecl:foundation:alg:group_axioms", "srcdecl:foundation:rel:function_definition"],
            "text": "For groups (G,*_G) and (H,*_H), a map phi:G->H is a homomorphism iff phi(a *_G b)=phi(a) *_H phi(b). Its kernel is {g in G | phi(g)=e_H}.",
        },
        {
            "node_id": "srcdecl:foundation:alg:polynomial_definition",
            "label": "Definition of Polynomial over a Field F",
            "decl_type": "DEFINITION",
            "layer": "arithmetic_algebra",
            "chapter_section": "Algebra §5.4",
            "structural_refs": ["srcdecl:foundation:alg:field_axioms"],
            "text": "A polynomial P in F[x] is a finite formal sum P(x) = sum_{i=0}^n a_i x^i for an integer n >= 0 and coefficients a_i in F; trailing zero coefficients do not change the polynomial.",
        },
        {
            "node_id": "srcdecl:foundation:alg:polynomial_degree",
            "label": "Degree and Leading Coefficient of Polynomial",
            "decl_type": "DEFINITION",
            "layer": "arithmetic_algebra",
            "chapter_section": "Algebra §5.4",
            "structural_refs": ["srcdecl:foundation:alg:polynomial_definition"],
            "text": "For non-zero P(x) = sum_{i=0}^n a_i x^i with a_n ≠ 0, deg(P) = n is the degree, and a_n is the leading coefficient.",
        },
        {
            "node_id": "srcdecl:foundation:alg:polynomial_division_algorithm",
            "label": "Division Algorithm for Polynomials",
            "decl_type": "THEOREM",
            "layer": "arithmetic_algebra",
            "chapter_section": "Algebra §5.4",
            "structural_refs": ["srcdecl:foundation:alg:polynomial_degree"],
            "text": "For P(x), D(x) in F[x] with D(x) != 0, there exist unique Q(x), R(x) in F[x] such that P(x) = D(x)*Q(x) + R(x) and either R(x) = 0 or deg(R) < deg(D).",
        },
        {
            "node_id": "srcdecl:foundation:alg:remainder_factor_theorem",
            "label": "Polynomial Remainder Theorem and Factor Theorem",
            "decl_type": "THEOREM",
            "layer": "arithmetic_algebra",
            "chapter_section": "Algebra §5.4",
            "structural_refs": ["srcdecl:foundation:alg:polynomial_division_algorithm"],
            "text": "For P(x) in F[x] and c in F, the remainder on division by x-c is P(c). Consequently, x-c divides P(x) iff P(c)=0.",
        },
        {
            "node_id": "srcdecl:foundation:alg:binomial_coefficients",
            "label": "Definition of Binomial Coefficient n choose k",
            "decl_type": "DEFINITION",
            "layer": "arithmetic_algebra",
            "chapter_section": "Algebra §5.5",
            "structural_refs": ["srcdecl:foundation:num:peano_axioms_naturals"],
            "text": "For integers n >= k >= 0, the binomial coefficient is C(n, k) = n! / (k! · (n-k)!).",
        },
        {
            "node_id": "srcdecl:foundation:alg:pascals_identity",
            "label": "Pascal's Recurrence Identity",
            "decl_type": "THEOREM",
            "layer": "arithmetic_algebra",
            "chapter_section": "Algebra §5.5",
            "structural_refs": ["srcdecl:foundation:alg:binomial_coefficients"],
            "text": "For integers n >= 2 and 1 <= k <= n-1, C(n,k) = C(n-1,k-1) + C(n-1,k); the boundary values are C(n,0)=C(n,n)=1.",
        },
        {
            "node_id": "srcdecl:foundation:alg:binomial_theorem",
            "label": "The Binomial Theorem",
            "decl_type": "THEOREM",
            "layer": "arithmetic_algebra",
            "chapter_section": "Algebra §5.5",
            "structural_refs": ["srcdecl:foundation:alg:binomial_coefficients", "srcdecl:foundation:alg:pascals_identity", "srcdecl:foundation:num:principle_induction", "srcdecl:foundation:alg:ring_axioms", "srcdecl:foundation:alg:commutative_law"],
            "text": "For a and b in a commutative unital ring and an integer n >= 0, (a+b)^n=sum_{k=0}^n C(n,k)*a^k*b^{n-k}.",
        },
        {
            "node_id": "srcdecl:foundation:alg:quadratic_formula",
            "label": "Quadratic Formula for Second-Degree Equations",
            "decl_type": "THEOREM",
            "layer": "arithmetic_algebra",
            "chapter_section": "Algebra §5.4",
            "structural_refs": ["srcdecl:foundation:alg:polynomial_definition", "srcdecl:foundation:num:complex_numbers_definition", "srcdecl:foundation:num:algebraic_closure_c_primitive"],
            "text": "For a, b, c in C with a != 0, choose s in C with s^2 = b^2 - 4*a*c. The roots of a*x^2+b*x+c are exactly x=(-b+s)/(2*a) and x=(-b-s)/(2*a), counted with multiplicity.",
        },
        {
            "node_id": "srcdecl:foundation:alg:vector_space_axioms_primitive",
            "label": "Vector Space Axioms over Field F (Primitive Formulation)",
            "decl_type": "DEFINITION",
            "layer": "arithmetic_algebra",
            "chapter_section": "Algebra §5.6",
            "structural_refs": ["srcdecl:foundation:alg:abelian_group", "srcdecl:foundation:alg:field_axioms", "srcdecl:foundation:rel:function_definition"],
            "text": "A vector space V over F is an Abelian group (V,+) with scalar multiplication satisfying alpha*(u+v)=alpha*u+alpha*v, (alpha+beta)*v=alpha*v+beta*v, (alpha*beta)*v=alpha*(beta*v), and 1_F v = v.",
        },
        {
            "node_id": "srcdecl:foundation:alg:linear_combination_span",
            "label": "Linear Combination and Span",
            "decl_type": "DEFINITION",
            "layer": "arithmetic_algebra",
            "chapter_section": "Algebra §5.6",
            "structural_refs": ["srcdecl:foundation:alg:vector_space_axioms_primitive"],
            "text": "A linear combination of vectors v_1, ..., v_k is sum_{i=1}^k c_i v_i with c_i in F. Span(S) is the set of all finite linear combinations of vectors in S.",
        },

        # =========================================================================
        # LAYER 6: ORDER, METRICS & SEQUENCES (22 Declarations)
        # =========================================================================
        {
            "node_id": "srcdecl:foundation:seq:bounded_set_reals",
            "label": "Definition of Bounded Set in Real Line",
            "decl_type": "DEFINITION",
            "layer": "order_sequences",
            "chapter_section": "Sequences §6.1",
            "structural_refs": ["srcdecl:foundation:num:real_numbers_axioms"],
            "text": "A subset S ⊆ R is bounded above if ∃M in R ∀x in S (x <= M); bounded below if ∃m in R ∀x in S (m <= x); bounded if both.",
        },
        {
            "node_id": "srcdecl:foundation:seq:supremum_infimum",
            "label": "Definition of Supremum and Infimum",
            "decl_type": "DEFINITION",
            "layer": "order_sequences",
            "chapter_section": "Sequences §6.1",
            "structural_refs": ["srcdecl:foundation:seq:bounded_set_reals", "srcdecl:foundation:num:completeness_supremum"],
            "text": "For a nonempty subset S of R bounded above, sup(S) is its least upper bound; for nonempty S bounded below, inf(S) is its greatest lower bound. Their existence in R follows from completeness.",
        },
        {
            "node_id": "srcdecl:foundation:seq:absolute_value",
            "label": "Definition of Absolute Value Function on R",
            "decl_type": "DEFINITION",
            "layer": "order_sequences",
            "chapter_section": "Sequences §6.2",
            "structural_refs": ["srcdecl:foundation:num:real_numbers_axioms"],
            "text": "For x in R, |x| = x if x >= 0, and |x| = -x if x < 0. Satisfies |x| >= 0 and |x| = 0 <=> x = 0.",
        },
        {
            "node_id": "srcdecl:foundation:seq:triangle_inequality_reals",
            "label": "Triangle Inequality for Real Numbers",
            "decl_type": "THEOREM",
            "layer": "order_sequences",
            "chapter_section": "Sequences §6.2",
            "structural_refs": ["srcdecl:foundation:seq:absolute_value"],
            "text": "For all real numbers a, b in R: |a + b| <= |a| + |b|.",
        },
        {
            "node_id": "srcdecl:foundation:seq:reverse_triangle_inequality",
            "label": "Reverse Triangle Inequality",
            "decl_type": "THEOREM",
            "layer": "order_sequences",
            "chapter_section": "Sequences §6.2",
            "structural_refs": ["srcdecl:foundation:seq:triangle_inequality_reals"],
            "text": "For all a, b in R: ||a| - |b|| <= |a - b|.",
        },
        {
            "node_id": "srcdecl:foundation:seq:real_sequence_definition",
            "label": "Definition of Real Sequence",
            "decl_type": "DEFINITION",
            "layer": "order_sequences",
            "chapter_section": "Sequences §6.3",
            "structural_refs": ["srcdecl:foundation:rel:function_definition", "srcdecl:foundation:num:peano_axioms_naturals"],
            "text": "A real sequence is a function a: N -> R, denoted (a_n)_{n=0}^\\infty or (a_n).",
        },
        {
            "node_id": "srcdecl:foundation:seq:sequence_limit_epsilon_N",
            "label": "Definition of Sequence Convergence (Epsilon-N Limit)",
            "decl_type": "DEFINITION",
            "layer": "order_sequences",
            "chapter_section": "Sequences §6.3",
            "structural_refs": ["srcdecl:foundation:seq:real_sequence_definition", "srcdecl:foundation:seq:absolute_value"],
            "text": "A sequence (a_n) converges to limit L (lim a_n = L) iff ∀ε > 0 ∃N in N ∀n >= N (|a_n - L| < ε).",
        },
        {
            "node_id": "srcdecl:foundation:seq:uniqueness_sequence_limit",
            "label": "Uniqueness of Limits of Sequences",
            "decl_type": "THEOREM",
            "layer": "order_sequences",
            "chapter_section": "Sequences §6.3",
            "structural_refs": ["srcdecl:foundation:seq:sequence_limit_epsilon_N", "srcdecl:foundation:seq:triangle_inequality_reals"],
            "text": "If a sequence (a_n) converges, its limit L is unique.",
        },
        {
            "node_id": "srcdecl:foundation:seq:convergent_implies_bounded",
            "label": "Boundedness of Convergent Sequences",
            "decl_type": "THEOREM",
            "layer": "order_sequences",
            "chapter_section": "Sequences §6.3",
            "structural_refs": ["srcdecl:foundation:seq:sequence_limit_epsilon_N", "srcdecl:foundation:seq:bounded_set_reals"],
            "text": "Every convergent sequence of real numbers is bounded.",
        },
        {
            "node_id": "srcdecl:foundation:seq:algebraic_limit_theorem",
            "label": "Algebraic Limit Theorem for Sequences",
            "decl_type": "THEOREM",
            "layer": "order_sequences",
            "chapter_section": "Sequences §6.4",
            "structural_refs": ["srcdecl:foundation:seq:sequence_limit_epsilon_N"],
            "text": "If lim a_n=A and lim b_n=B, then sums and products converge to A+B and A*B. If additionally B != 0 and b_n != 0 for every n, then lim(a_n/b_n)=A/B; an eventually defined quotient may equivalently be completed at finitely many earlier indices.",
        },
        {
            "node_id": "srcdecl:foundation:seq:squeeze_theorem",
            "label": "Squeeze (Sandwich) Theorem for Sequences",
            "decl_type": "THEOREM",
            "layer": "order_sequences",
            "chapter_section": "Sequences §6.4",
            "structural_refs": ["srcdecl:foundation:seq:sequence_limit_epsilon_N"],
            "text": "If a_n <= b_n <= c_n for all n >= N_0, and lim a_n = lim c_n = L, then lim b_n = L.",
        },
        {
            "node_id": "srcdecl:foundation:seq:monotone_convergence_theorem",
            "label": "Monotone Convergence Theorem for Sequences",
            "decl_type": "THEOREM",
            "layer": "order_sequences",
            "chapter_section": "Sequences §6.5",
            "structural_refs": ["srcdecl:foundation:seq:sequence_limit_epsilon_N", "srcdecl:foundation:num:completeness_supremum"],
            "text": "Every bounded monotone (non-decreasing or non-increasing) sequence of real numbers converges in R.",
        },
        {
            "node_id": "srcdecl:foundation:seq:subsequence_definition",
            "label": "Definition of Subsequence",
            "decl_type": "DEFINITION",
            "layer": "order_sequences",
            "chapter_section": "Sequences §6.5",
            "structural_refs": ["srcdecl:foundation:seq:real_sequence_definition"],
            "text": "Given (a_n) and strictly increasing index sequence n_1 < n_2 < n_3 < ..., the sequence (a_{n_k})_{k=1}^\\infty is a subsequence.",
        },
        {
            "node_id": "srcdecl:foundation:seq:bolzano_weierstrass_primitive",
            "label": "Bolzano-Weierstrass Theorem (Elementary)",
            "decl_type": "THEOREM",
            "layer": "order_sequences",
            "chapter_section": "Sequences §6.5",
            "structural_refs": ["srcdecl:foundation:seq:subsequence_definition", "srcdecl:foundation:seq:monotone_convergence_theorem", "srcdecl:foundation:seq:bounded_set_reals"],
            "text": "Every real sequence has a monotone subsequence; consequently every bounded sequence of real numbers has a convergent subsequence by monotone convergence.",
        },
        {
            "node_id": "srcdecl:foundation:seq:cauchy_sequence_definition",
            "label": "Definition of Cauchy Sequence",
            "decl_type": "DEFINITION",
            "layer": "order_sequences",
            "chapter_section": "Sequences §6.6",
            "structural_refs": ["srcdecl:foundation:seq:real_sequence_definition", "srcdecl:foundation:seq:absolute_value"],
            "text": "A sequence (a_n) is a Cauchy sequence iff ∀ε > 0 ∃N in N ∀m, n >= N (|a_n - a_m| < ε).",
        },
        {
            "node_id": "srcdecl:foundation:seq:cauchy_criterion_convergence",
            "label": "Cauchy Convergence Criterion in R",
            "decl_type": "THEOREM",
            "layer": "order_sequences",
            "chapter_section": "Sequences §6.6",
            "structural_refs": ["srcdecl:foundation:seq:cauchy_sequence_definition", "srcdecl:foundation:num:completeness_supremum"],
            "text": "A sequence of real numbers converges in R if and only if it is a Cauchy sequence (Completeness of R).",
        },
        {
            "node_id": "srcdecl:foundation:seq:infinite_series_definition",
            "label": "Definition of Infinite Series and Partial Sums",
            "decl_type": "DEFINITION",
            "layer": "order_sequences",
            "chapter_section": "Sequences §6.7",
            "structural_refs": ["srcdecl:foundation:seq:real_sequence_definition"],
            "text": "For sequence (a_n), infinite series sum_{n=0}^\\infty a_n is the sequence of partial sums s_k = sum_{n=0}^k a_n. The series converges to S iff lim s_k = S.",
        },
        {
            "node_id": "srcdecl:foundation:seq:geometric_series_sum",
            "label": "Sum Formula for Geometric Series",
            "decl_type": "THEOREM",
            "layer": "order_sequences",
            "chapter_section": "Sequences §6.7",
            "structural_refs": ["srcdecl:foundation:seq:infinite_series_definition"],
            "text": "For real |r| < 1: sum_{n=0}^\\infty a r^n = a / (1 - r). If |r| >= 1 and a ≠ 0, the series diverges.",
        },
        {
            "node_id": "srcdecl:foundation:seq:divergence_test",
            "label": "Divergence Test (n-th Term Test) for Series",
            "decl_type": "THEOREM",
            "layer": "order_sequences",
            "chapter_section": "Sequences §6.7",
            "structural_refs": ["srcdecl:foundation:seq:infinite_series_definition"],
            "text": "If sum a_n converges, then a_n converges to 0. Equivalently by contraposition, if a_n does not converge to 0, including when it has no limit, then sum a_n diverges.",
        },
        {
            "node_id": "srcdecl:foundation:seq:comparison_test_series",
            "label": "Direct Comparison Test for Non-Negative Series",
            "decl_type": "THEOREM",
            "layer": "order_sequences",
            "chapter_section": "Sequences §6.7",
            "structural_refs": ["srcdecl:foundation:seq:infinite_series_definition", "srcdecl:foundation:seq:monotone_convergence_theorem"],
            "text": "If 0 <= a_n <= b_n for all n, then convergence of sum b_n implies convergence of sum a_n, and divergence of sum a_n implies divergence of sum b_n.",
        },
        {
            "node_id": "srcdecl:foundation:seq:metric_space_axioms_primitive",
            "label": "Definition of Metric Space (Primitive Formulation)",
            "decl_type": "DEFINITION",
            "layer": "order_sequences",
            "chapter_section": "Sequences §6.8",
            "structural_refs": ["srcdecl:foundation:rel:function_definition", "srcdecl:foundation:num:real_numbers_axioms"],
            "text": "A metric space (M,d) is a set M with d: M x M -> R satisfying d(x,y)>=0, d(x,y)=0 iff x=y, d(x,y)=d(y,x), and d(x, z) <= d(x, y) + d(y, z) for all x,y,z in M.",
        },
        {
            "node_id": "srcdecl:foundation:seq:open_ball_metric",
            "label": "Definition of Open Ball and Neighborhood in Metric Space",
            "decl_type": "DEFINITION",
            "layer": "order_sequences",
            "chapter_section": "Sequences §6.8",
            "structural_refs": ["srcdecl:foundation:seq:metric_space_axioms_primitive"],
            "text": "The open ball of radius r > 0 centered at x_0 in metric space (M, d) is B(x_0, r) = {x in M | d(x, x_0) < r}.",
        },

        # =========================================================================
        # LAYER 7: EUCLIDEAN GEOMETRY & TRIGONOMETRY (22 Declarations)
        # =========================================================================
        {
            "node_id": "srcdecl:foundation:geom:euclidean_plane_R2",
            "label": "Definition of Euclidean Plane R^2",
            "decl_type": "DEFINITION",
            "layer": "geometry_trig",
            "chapter_section": "Geometry §7.1",
            "structural_refs": ["srcdecl:foundation:set:cartesian_product", "srcdecl:foundation:num:real_numbers_axioms"],
            "text": "The Euclidean plane is R^2 = R x R equipped with the standard inner product <(x,y),(u,v)>=x*u+y*v and its induced distance; points are represented by Cartesian coordinates.",
        },
        {
            "node_id": "srcdecl:foundation:geom:euclidean_space_Rn",
            "label": "Definition of Euclidean Space R^n",
            "decl_type": "DEFINITION",
            "layer": "geometry_trig",
            "chapter_section": "Geometry §7.1",
            "structural_refs": ["srcdecl:foundation:set:cartesian_product", "srcdecl:foundation:num:real_numbers_axioms", "srcdecl:foundation:alg:vector_space_axioms_primitive"],
            "text": "For an integer n >= 1, Euclidean space R^n is the real vector space of ordered n-tuples equipped with the standard inner product <x,y>=sum_{i=1}^n x_i*y_i and its induced norm and distance.",
        },
        {
            "node_id": "srcdecl:foundation:geom:distance_formula_R2",
            "label": "Euclidean Distance Formula in R^2",
            "decl_type": "DEFINITION",
            "layer": "geometry_trig",
            "chapter_section": "Geometry §7.2",
            "structural_refs": ["srcdecl:foundation:geom:euclidean_plane_R2"],
            "text": "The distance between points P=(x_1, y_1) and Q=(x_2, y_2) in R^2 is d(P, Q) = sqrt((x_2 - x_1)^2 + (y_2 - y_1)^2).",
        },
        {
            "node_id": "srcdecl:foundation:geom:distance_formula_Rn",
            "label": "Euclidean Distance Formula in R^n",
            "decl_type": "DEFINITION",
            "layer": "geometry_trig",
            "chapter_section": "Geometry §7.2",
            "structural_refs": ["srcdecl:foundation:geom:euclidean_space_Rn"],
            "text": "The distance between vectors x, y in R^n is d(x, y) = sqrt(sum_{i=1}^n (x_i - y_i)^2).",
        },
        {
            "node_id": "srcdecl:foundation:geom:dot_product_Rn",
            "label": "Definition of Standard Dot Product (Inner Product) on R^n",
            "decl_type": "DEFINITION",
            "layer": "geometry_trig",
            "chapter_section": "Geometry §7.3",
            "structural_refs": ["srcdecl:foundation:geom:euclidean_space_Rn"],
            "text": "The dot product of vectors u, v in R^n is u · v = sum_{i=1}^n u_i v_i.",
        },
        {
            "node_id": "srcdecl:foundation:geom:euclidean_norm_length",
            "label": "Euclidean Norm (Length) of a Vector",
            "decl_type": "DEFINITION",
            "layer": "geometry_trig",
            "chapter_section": "Geometry §7.3",
            "structural_refs": ["srcdecl:foundation:geom:dot_product_Rn"],
            "text": "The Euclidean norm of v in R^n is ||v|| = sqrt(v · v) = sqrt(sum_{i=1}^n v_i^2).",
        },
        {
            "node_id": "srcdecl:foundation:geom:cauchy_schwarz_elementary",
            "label": "Cauchy-Schwarz Inequality in Euclidean Space",
            "decl_type": "THEOREM",
            "layer": "geometry_trig",
            "chapter_section": "Geometry §7.3",
            "structural_refs": ["srcdecl:foundation:geom:dot_product_Rn", "srcdecl:foundation:geom:euclidean_norm_length"],
            "text": "For all vectors u, v in R^n: |u · v| <= ||u|| · ||v||, with equality iff u and v are linearly dependent.",
        },
        {
            "node_id": "srcdecl:foundation:geom:triangle_inequality_Rn",
            "label": "Triangle Inequality in Euclidean Space R^n",
            "decl_type": "THEOREM",
            "layer": "geometry_trig",
            "chapter_section": "Geometry §7.3",
            "structural_refs": ["srcdecl:foundation:geom:cauchy_schwarz_elementary"],
            "text": "For all vectors u, v in R^n: ||u + v|| <= ||u|| + ||v||.",
        },
        {
            "node_id": "srcdecl:foundation:geom:orthogonality_vectors",
            "label": "Definition of Orthogonality (Perpendicularity)",
            "decl_type": "DEFINITION",
            "layer": "geometry_trig",
            "chapter_section": "Geometry §7.4",
            "structural_refs": ["srcdecl:foundation:geom:dot_product_Rn"],
            "text": "Two vectors u, v in R^n are orthogonal (u ⊥ v) iff u · v = 0.",
        },
        {
            "node_id": "srcdecl:foundation:geom:pythagorean_theorem",
            "label": "The Pythagorean Theorem in R^n",
            "decl_type": "THEOREM",
            "layer": "geometry_trig",
            "chapter_section": "Geometry §7.4",
            "structural_refs": ["srcdecl:foundation:geom:orthogonality_vectors", "srcdecl:foundation:geom:euclidean_norm_length"],
            "text": "Vectors u, v in R^n are orthogonal iff ||u + v||^2 = ||u||^2 + ||v||^2.",
        },
        {
            "node_id": "srcdecl:foundation:geom:unit_circle_equation",
            "label": "Equation of the Unit Circle in R^2",
            "decl_type": "DEFINITION",
            "layer": "geometry_trig",
            "chapter_section": "Geometry §7.5",
            "structural_refs": ["srcdecl:foundation:geom:euclidean_plane_R2", "srcdecl:foundation:geom:distance_formula_R2"],
            "text": "The unit circle S^1 in R^2 is the set of all points at distance 1 from origin: S^1 = {(x, y) in R^2 | x^2 + y^2 = 1}.",
        },
        {
            "node_id": "srcdecl:foundation:geom:sine_cosine_unit_circle",
            "label": "Geometric Definition of Sine and Cosine via Unit Circle",
            "decl_type": "DEFINITION",
            "layer": "geometry_trig",
            "chapter_section": "Trigonometry §7.6",
            "structural_refs": ["srcdecl:foundation:geom:unit_circle_equation"],
            "text": "For a directed angle theta in standard position measured in radians, the oriented unit-circle parametrization assigns the point (cos theta, sin theta); hence cos^2 theta + sin^2 theta = 1.",
        },
        {
            "node_id": "srcdecl:foundation:geom:tangent_trig_definition",
            "label": "Definition of Tangent and Reciprocal Trigonometric Functions",
            "decl_type": "DEFINITION",
            "layer": "geometry_trig",
            "chapter_section": "Trigonometry §7.6",
            "structural_refs": ["srcdecl:foundation:geom:sine_cosine_unit_circle", "srcdecl:foundation:geom:unit_circle_equation", "srcdecl:foundation:geom:law_of_cosines"],
            "text": "When cos theta != 0, tan theta = sin theta / cos theta and sec theta = 1/cos theta. When sin theta != 0, csc theta = 1/sin theta and cot theta = cos theta/sin theta.",
        },
        {
            "node_id": "srcdecl:foundation:geom:pythagorean_trig_identities",
            "label": "Fundamental Pythagorean Trigonometric Identities",
            "decl_type": "THEOREM",
            "layer": "geometry_trig",
            "chapter_section": "Trigonometry §7.6",
            "structural_refs": ["srcdecl:foundation:geom:sine_cosine_unit_circle", "srcdecl:foundation:geom:tangent_trig_definition"],
            "text": "For every real theta, sin^2 theta + cos^2 theta = 1. Also 1+tan^2 theta=sec^2 theta and 1+cot^2 theta=csc^2 theta where both sides are defined.",
        },
        {
            "node_id": "srcdecl:foundation:geom:angle_sum_formulas",
            "label": "Angle Sum and Difference Formulas for Sine and Cosine",
            "decl_type": "THEOREM",
            "layer": "geometry_trig",
            "chapter_section": "Trigonometry §7.7",
            "structural_refs": ["srcdecl:foundation:geom:sine_cosine_unit_circle", "srcdecl:foundation:geom:distance_formula_R2"],
            "text": "sin(α ± β) = sin α cos β ± cos α sin β, and cos(α ± β) = cos α cos β ∓ sin α sin β.",
        },
        {
            "node_id": "srcdecl:foundation:geom:double_angle_formulas",
            "label": "Double-Angle and Half-Angle Formulas",
            "decl_type": "THEOREM",
            "layer": "geometry_trig",
            "chapter_section": "Trigonometry §7.7",
            "structural_refs": ["srcdecl:foundation:geom:angle_sum_formulas"],
            "text": "sin(2θ) = 2 sin θ cos θ, and cos(2θ) = cos^2 θ - sin^2 θ = 2 cos^2 θ - 1 = 1 - 2 sin^2 θ.",
        },
        {
            "node_id": "srcdecl:foundation:geom:law_of_cosines",
            "label": "The Law of Cosines for Triangles",
            "decl_type": "THEOREM",
            "layer": "geometry_trig",
            "chapter_section": "Geometry §7.8",
            "structural_refs": ["srcdecl:foundation:geom:dot_product_Rn", "srcdecl:foundation:geom:pythagorean_theorem"],
            "text": "In any nondegenerate Euclidean triangle with positive side lengths a, b, c and angle γ opposite c: c^2 = a^2 + b^2 - 2ab cos γ.",
        },
        {
            "node_id": "srcdecl:foundation:geom:law_of_sines",
            "label": "The Law of Sines for Triangles",
            "decl_type": "THEOREM",
            "layer": "geometry_trig",
            "chapter_section": "Geometry §7.8",
            "structural_refs": ["srcdecl:foundation:geom:sine_cosine_unit_circle"],
            "text": "In a nondegenerate Euclidean triangle with positive side lengths a,b,c, opposite angles alpha,beta,gamma, and circumradius R, a/sin alpha = b/sin beta = c/sin gamma = 2R.",
        },
        {
            "node_id": "srcdecl:foundation:geom:polar_coordinates_R2",
            "label": "Polar Coordinates in R^2",
            "decl_type": "DEFINITION",
            "layer": "geometry_trig",
            "chapter_section": "Geometry §7.9",
            "structural_refs": ["srcdecl:foundation:geom:sine_cosine_unit_circle"],
            "text": "For a nonzero point (x,y), polar coordinates satisfy r=sqrt(x^2+y^2)>0, theta=atan2(y,x) in a declared branch interval, x=r*cos theta, and y=r*sin theta. At the origin r=0 and the angle is not uniquely defined.",
        },
        {
            "node_id": "srcdecl:foundation:geom:rotation_matrix_2d",
            "label": "2D Planar Rotation Transformation Matrix",
            "decl_type": "DEFINITION",
            "layer": "geometry_trig",
            "chapter_section": "Geometry §7.9",
            "structural_refs": ["srcdecl:foundation:geom:euclidean_plane_R2", "srcdecl:foundation:geom:sine_cosine_unit_circle", "srcdecl:foundation:alg:vector_space_axioms_primitive"],
            "text": "Counterclockwise rotation by angle θ in R^2 is linear map given by matrix R_θ = [[cos θ, -sin θ], [sin θ, cos θ]].",
        },
        {
            "node_id": "srcdecl:foundation:geom:angle_between_vectors",
            "label": "Angle Between Vectors in Euclidean Space",
            "decl_type": "DEFINITION",
            "layer": "geometry_trig",
            "chapter_section": "Geometry §7.3",
            "structural_refs": ["srcdecl:foundation:geom:dot_product_Rn", "srcdecl:foundation:geom:cauchy_schwarz_elementary"],
            "text": "For non-zero u, v in R^n, angle θ in [0, π] satisfies cos θ = (u · v) / (||u|| · ||v||).",
        },
        {
            "node_id": "srcdecl:foundation:geom:cross_product_R3",
            "label": "Definition of Vector Cross Product in R^3",
            "decl_type": "DEFINITION",
            "layer": "geometry_trig",
            "chapter_section": "Geometry §7.10",
            "structural_refs": ["srcdecl:foundation:geom:euclidean_space_Rn", "srcdecl:foundation:geom:orthogonality_vectors"],
            "text": "For u, v in R^3, cross product u × v = (u_2 v_3 - u_3 v_2, u_3 v_1 - u_1 v_3, u_1 v_2 - u_2 v_1). Satisfies (u × v) ⊥ u and (u × v) ⊥ v.",
        },

        # =========================================================================
        # LAYER 8: ELEMENTARY CALCULUS (26 Declarations)
        # =========================================================================
        {
            "node_id": "srcdecl:foundation:calc:function_limit_epsilon_delta",
            "label": "Epsilon-Delta Definition of Limit of a Function",
            "decl_type": "DEFINITION",
            "layer": "elementary_calculus",
            "chapter_section": "Calculus §8.1",
            "structural_refs": ["srcdecl:foundation:rel:function_definition", "srcdecl:foundation:seq:absolute_value"],
            "text": "Let f:D subset R -> R and let c be an accumulation point of D. Then lim_{x->c} f(x)=L iff for every epsilon>0 there exists delta>0 such that x in D and 0<|x-c|<delta imply |f(x)-L|<epsilon.",
        },
        {
            "node_id": "srcdecl:foundation:calc:one_sided_limits",
            "label": "Definition of Left-Hand and Right-Hand Limits",
            "decl_type": "DEFINITION",
            "layer": "elementary_calculus",
            "chapter_section": "Calculus §8.1",
            "structural_refs": ["srcdecl:foundation:calc:function_limit_epsilon_delta"],
            "text": "At a right or left one-sided accumulation point of the domain, the corresponding epsilon-delta limit restricts x to c<x<c+delta or c-delta<x<c. When c is an accumulation point from both sides, the two-sided limit exists iff both one-sided limits exist and are equal.",
        },
        {
            "node_id": "srcdecl:foundation:calc:continuity_at_point",
            "label": "Definition of Continuity of a Function at a Point",
            "decl_type": "DEFINITION",
            "layer": "elementary_calculus",
            "chapter_section": "Calculus §8.2",
            "structural_refs": ["srcdecl:foundation:calc:function_limit_epsilon_delta"],
            "text": "For f:D subset R -> R and c in D, f is continuous at c iff for every epsilon>0 there exists delta>0 such that x in D and |x-c|<delta imply |f(x)-f(c)|<epsilon. This includes isolated domain points.",
        },
        {
            "node_id": "srcdecl:foundation:calc:continuity_on_interval",
            "label": "Definition of Continuity on an Interval",
            "decl_type": "DEFINITION",
            "layer": "elementary_calculus",
            "chapter_section": "Calculus §8.2",
            "structural_refs": ["srcdecl:foundation:calc:continuity_at_point"],
            "text": "A function is continuous on (a,b) iff it is continuous at every point there. For a<b, it is continuous on [a,b] iff it is continuous on (a,b), right-continuous at a, and left-continuous at b.",
        },
        {
            "node_id": "srcdecl:foundation:calc:intermediate_value_theorem",
            "label": "The Intermediate Value Theorem (IVT)",
            "decl_type": "THEOREM",
            "layer": "elementary_calculus",
            "chapter_section": "Calculus §8.2",
            "structural_refs": ["srcdecl:foundation:calc:continuity_on_interval", "srcdecl:foundation:num:completeness_supremum"],
            "text": "If a < b, f:[a,b]->R is continuous, and u is strictly between f(a) and f(b), then there exists c in (a,b) such that f(c)=u.",
        },
        {
            "node_id": "srcdecl:foundation:calc:extreme_value_theorem",
            "label": "The Extreme Value Theorem (EVT)",
            "decl_type": "THEOREM",
            "layer": "elementary_calculus",
            "chapter_section": "Calculus §8.2",
            "structural_refs": ["srcdecl:foundation:calc:continuity_on_interval", "srcdecl:foundation:seq:bolzano_weierstrass_primitive"],
            "text": "If a <= b and f:[a,b]->R is continuous, then f attains an absolute maximum and an absolute minimum on [a,b].",
        },
        {
            "node_id": "srcdecl:foundation:calc:derivative_difference_quotient",
            "label": "Definition of Derivative via Difference Quotient Limit",
            "decl_type": "DEFINITION",
            "layer": "elementary_calculus",
            "chapter_section": "Calculus §8.3",
            "structural_refs": ["srcdecl:foundation:calc:function_limit_epsilon_delta"],
            "text": "For f:D subset R -> R and an interior point x of D, f'(x)=lim_{h->0, h!=0, x + h in D} (f(x+h)-f(x))/h when this finite two-sided limit exists.",
        },
        {
            "node_id": "srcdecl:foundation:calc:differentiability_implies_continuity",
            "label": "Differentiability Implies Continuity",
            "decl_type": "THEOREM",
            "layer": "elementary_calculus",
            "chapter_section": "Calculus §8.3",
            "structural_refs": ["srcdecl:foundation:calc:derivative_difference_quotient", "srcdecl:foundation:calc:continuity_at_point"],
            "text": "If f is differentiable at c, then f is continuous at c.",
        },
        {
            "node_id": "srcdecl:foundation:calc:derivative_power_rule",
            "label": "Power Rule for Derivatives",
            "decl_type": "THEOREM",
            "layer": "elementary_calculus",
            "chapter_section": "Calculus §8.4",
            "structural_refs": ["srcdecl:foundation:calc:derivative_difference_quotient", "srcdecl:foundation:alg:binomial_theorem"],
            "text": "For every integer n >= 1 and real x, d/dx(x^n)=n*x^{n-1}. For n=0 the constant function x^0=1 has derivative 0, stated separately to avoid the undefined expression 0*x^{-1} at x=0.",
        },
        {
            "node_id": "srcdecl:foundation:calc:derivative_linearity",
            "label": "Linearity (Sum and Constant Multiple Rule) of Differentiation",
            "decl_type": "THEOREM",
            "layer": "elementary_calculus",
            "chapter_section": "Calculus §8.4",
            "structural_refs": ["srcdecl:foundation:calc:derivative_difference_quotient"],
            "text": "If f and g are differentiable at x and c is real, then (c*f+g)'(x)=c*f'(x)+g'(x).",
        },
        {
            "node_id": "srcdecl:foundation:calc:derivative_product_rule",
            "label": "Product Rule (Leibniz Rule) for Derivatives",
            "decl_type": "THEOREM",
            "layer": "elementary_calculus",
            "chapter_section": "Calculus §8.4",
            "structural_refs": ["srcdecl:foundation:calc:derivative_difference_quotient", "srcdecl:foundation:calc:differentiability_implies_continuity"],
            "text": "If f and g are differentiable at x, then (f*g)'(x)=f'(x)*g(x)+f(x)*g'(x).",
        },
        {
            "node_id": "srcdecl:foundation:calc:derivative_quotient_rule",
            "label": "Quotient Rule for Derivatives",
            "decl_type": "THEOREM",
            "layer": "elementary_calculus",
            "chapter_section": "Calculus §8.4",
            "structural_refs": ["srcdecl:foundation:calc:derivative_product_rule", "srcdecl:foundation:calc:derivative_chain_rule", "srcdecl:foundation:calc:derivative_power_rule"],
            "text": "If f and g are differentiable at x and g(x) != 0, then (f/g)'(x)=(f'(x)*g(x)-f(x)*g'(x))/(g(x))^2.",
        },
        {
            "node_id": "srcdecl:foundation:calc:derivative_chain_rule",
            "label": "Chain Rule for Composite Functions",
            "decl_type": "THEOREM",
            "layer": "elementary_calculus",
            "chapter_section": "Calculus §8.4",
            "structural_refs": ["srcdecl:foundation:calc:derivative_difference_quotient", "srcdecl:foundation:rel:function_composition"],
            "text": "If g is differentiable at x and f is differentiable at g(x), then (f ∘ g)'(x) = f'(g(x)) · g'(x).",
        },
        {
            "node_id": "srcdecl:foundation:calc:derivative_trig_functions",
            "label": "Derivatives of Elementary Trigonometric Functions",
            "decl_type": "THEOREM",
            "layer": "elementary_calculus",
            "chapter_section": "Calculus §8.4",
            "structural_refs": ["srcdecl:foundation:calc:derivative_difference_quotient", "srcdecl:foundation:geom:sine_cosine_unit_circle", "srcdecl:foundation:geom:angle_sum_formulas"],
            "text": "With angles measured in radians, (sin x)'=cos x and (cos x)'=-sin x for all real x; where cos x != 0, (tan x)'=sec^2 x.",
        },
        {
            "node_id": "srcdecl:foundation:calc:derivative_exponential_log",
            "label": "Derivatives of Natural Exponential and Logarithm",
            "decl_type": "THEOREM",
            "layer": "elementary_calculus",
            "chapter_section": "Calculus §8.4",
            "structural_refs": ["srcdecl:foundation:calc:ftc_part1", "srcdecl:foundation:rel:inverse_function", "srcdecl:foundation:calc:derivative_chain_rule"],
            "text": "Define ln x = int_1^x (1/t) dt for x > 0 and let exp be its inverse from R to (0,infinity). Then ln'(x)=1/x for x>0 and exp'(x)=exp(x) for every real x.",
        },
        {
            "node_id": "srcdecl:foundation:calc:rolles_theorem",
            "label": "Rolle's Theorem",
            "decl_type": "THEOREM",
            "layer": "elementary_calculus",
            "chapter_section": "Calculus §8.5",
            "structural_refs": ["srcdecl:foundation:calc:extreme_value_theorem", "srcdecl:foundation:calc:derivative_difference_quotient", "srcdecl:foundation:calc:continuity_on_interval"],
            "text": "If a < b, f:[a,b]->R is continuous on [a,b], differentiable on (a,b), and f(a)=f(b), then there exists c in (a,b) such that f'(c)=0.",
        },
        {
            "node_id": "srcdecl:foundation:calc:mean_value_theorem",
            "label": "The Mean Value Theorem (MVT)",
            "decl_type": "THEOREM",
            "layer": "elementary_calculus",
            "chapter_section": "Calculus §8.5",
            "structural_refs": ["srcdecl:foundation:calc:rolles_theorem"],
            "text": "If a < b, f:[a,b]->R is continuous on [a,b] and differentiable on (a,b), then there exists c in (a,b) such that f'(c)=(f(b)-f(a))/(b-a).",
        },
        {
            "node_id": "srcdecl:foundation:calc:first_derivative_test",
            "label": "First Derivative Test for Local Extrema",
            "decl_type": "THEOREM",
            "layer": "elementary_calculus",
            "chapter_section": "Calculus §8.5",
            "structural_refs": ["srcdecl:foundation:calc:mean_value_theorem", "srcdecl:foundation:calc:continuity_at_point"],
            "text": "Suppose f is continuous at c and differentiable on a punctured neighborhood of c. If there exists delta > 0 such that f'(x)>0 for c-delta<x<c and f'(x)<0 for c<x<c+delta, then f has a strict local maximum at c; the reversed inequalities give a strict local minimum.",
        },
        {
            "node_id": "srcdecl:foundation:calc:second_derivative_test",
            "label": "Second Derivative Test for Concavity and Extrema",
            "decl_type": "THEOREM",
            "layer": "elementary_calculus",
            "chapter_section": "Calculus §8.5",
            "structural_refs": ["srcdecl:foundation:calc:first_derivative_test"],
            "text": "If f'(c) = 0 and f''(c) exists: if f''(c) > 0 then f has local min at c; if f''(c) < 0 then f has local max at c.",
        },
        {
            "node_id": "srcdecl:foundation:calc:riemann_partition_sum",
            "label": "Definition of Riemann Partition and Riemann Sum",
            "decl_type": "DEFINITION",
            "layer": "elementary_calculus",
            "chapter_section": "Calculus §8.6",
            "structural_refs": ["srcdecl:foundation:num:real_numbers_axioms"],
            "text": "For a < b and an integer n >= 1, a partition P of [a,b] is a=x_0<x_1<...<x_n=b. A tagged Riemann sum is sum_{i=1}^n f(t_i)*(x_i-x_{i-1}) with t_i in [x_{i-1},x_i].",
        },
        {
            "node_id": "srcdecl:foundation:calc:riemann_definite_integral",
            "label": "Definition of Definite Riemann Integral",
            "decl_type": "DEFINITION",
            "layer": "elementary_calculus",
            "chapter_section": "Calculus §8.6",
            "structural_refs": ["srcdecl:foundation:calc:riemann_partition_sum"],
            "text": "For a < b, a bounded f:[a,b]->R is Riemann integrable with integral I iff every sequence of tagged partitions whose mesh tends to 0 has Riemann sums tending to the same I, independently of tags and partitions; then I=int_a^b f(x) dx. Oriented integrals use int_b^a f=-int_a^b f and int_a^a f=0.",
        },
        {
            "node_id": "srcdecl:foundation:calc:ftc_part1",
            "label": "Fundamental Theorem of Calculus (Part 1: Accumulation Derivative)",
            "decl_type": "THEOREM",
            "layer": "elementary_calculus",
            "chapter_section": "Calculus §8.7",
            "structural_refs": ["srcdecl:foundation:calc:riemann_definite_integral", "srcdecl:foundation:calc:derivative_difference_quotient", "srcdecl:foundation:calc:continuity_on_interval"],
            "text": "If a < b, f is continuous on [a,b], and F(x)=int_a^x f(t)dt, then F is continuous on [a,b], differentiable on (a,b), and F'(x)=f(x).",
        },
        {
            "node_id": "srcdecl:foundation:calc:ftc_part2",
            "label": "Fundamental Theorem of Calculus (Part 2: Evaluation)",
            "decl_type": "THEOREM",
            "layer": "elementary_calculus",
            "chapter_section": "Calculus §8.7",
            "structural_refs": ["srcdecl:foundation:calc:ftc_part1", "srcdecl:foundation:calc:mean_value_theorem"],
            "text": "If a < b, f is continuous on [a,b], and F is continuous on [a,b] with F'=f on (a,b), then int_a^b f(x)dx=F(b)-F(a).",
        },
        {
            "node_id": "srcdecl:foundation:calc:integration_by_parts",
            "label": "Integration by Parts Formula",
            "decl_type": "THEOREM",
            "layer": "elementary_calculus",
            "chapter_section": "Calculus §8.8",
            "structural_refs": ["srcdecl:foundation:calc:ftc_part2", "srcdecl:foundation:calc:derivative_product_rule"],
            "text": "If u and v are continuously differentiable on [a,b], then int_a^b u(x)*v'(x) dx = u(b)v(b)-u(a)v(a)-int_a^b v(x)*u'(x) dx.",
        },
        {
            "node_id": "srcdecl:foundation:calc:integration_by_substitution",
            "label": "Integration by Substitution (u-Substitution)",
            "decl_type": "THEOREM",
            "layer": "elementary_calculus",
            "chapter_section": "Calculus §8.8",
            "structural_refs": ["srcdecl:foundation:calc:ftc_part2", "srcdecl:foundation:calc:derivative_chain_rule"],
            "text": "If g is continuously differentiable on [a,b] and f is continuous on an interval containing g([a,b]), then int_a^b f(g(x))*g'(x) dx = int_{g(a)}^{g(b)} f(u) du.",
        },
        {
            "node_id": "srcdecl:foundation:calc:taylors_theorem_primitive",
            "label": "Taylor's Theorem with Lagrange Remainder (Primitive Formulation)",
            "decl_type": "THEOREM",
            "layer": "elementary_calculus",
            "chapter_section": "Calculus §8.9",
            "structural_refs": ["srcdecl:foundation:calc:mean_value_theorem", "srcdecl:foundation:calc:derivative_power_rule"],
            "text": "Let n be an integer n >= 0. Suppose f has continuous derivatives through order n on the closed interval joining a and x and has an (n+1)-st derivative on its interior. If x != a, then f(x)=sum_{k=0}^n f^{(k)}(a)(x-a)^k/k! + f^{(n+1)}(c)(x-a)^{n+1}/(n+1)! for some c strictly between a and x; x=a is immediate.",
        },
    ]

    declarations: list[FoundationDeclaration] = []
    for item in raw_declarations:
        text = item["text"]
        title = item["label"]
        sha = compute_sha256(text)
        char_count = len(text)
        profile = detect_foundation_representation_profile(text, title)

        decl = FoundationDeclaration(
            node_id=item["node_id"],
            source_id=SOURCE_ID,
            label=title,
            decl_type=item["decl_type"],
            chapter_section=item["chapter_section"],
            statement_sha256=sha,
            char_count=char_count,
            layer=item["layer"],
            structural_refs=item.get("structural_refs", []),
            representation_profile=profile,
        )
        declarations.append(decl)

    apply_foundation_mathematical_amendments(declarations)
    return declarations


def main() -> int:
    parser = argparse.ArgumentParser(description="MAPEOGEO Foundation Backfill Ingestion Generator")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "artifacts" / "foundation_backfill" / "foundation_declarations.json",
        help="Path to output declarations JSON",
    )
    args = parser.parse_args()

    decls = generate_foundation_declarations()
    args.out.parent.mkdir(parents=True, exist_ok=True)

    out_data = {
        "source_id": SOURCE_ID,
        "stage": STAGE,
        "count": len(decls),
        "declarations": [d.to_dict() for d in decls],
    }
    args.out.write_text(json.dumps(out_data, indent=2), encoding="utf-8")
    print(f"Generated {len(decls)} foundation declarations to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
