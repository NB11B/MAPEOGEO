"""Unit Tests for Mathematics Domain Adapter Subsystem.

Tests:
1. Mathematical domain ontology (Theorem, MathematicalObject, Problem).
2. Translation of mathematical problems into domain-neutral WorkContracts.
3. Literal 6D grammar factoring (EXACT_FACTOR, WITNESS_EXTENSION, COMPOSITION).
4. Semantic drift detection and rejection of illegal coordinate expansion.
5. MathematicalProofObligation translation to generic ProofEngine claims/obligations.
6. Certification of mathematical theorems via independent proof replay.
7. Ability measurement and candidate machinery proposal.
"""

from __future__ import annotations

from mapeogeo.domains.mathematics import (
    FactoringClassification,
    MathematicalObject,
    MathematicalObjectType,
    MathematicalProblem,
    MathematicalProofObligation,
    MathematicsAdapter,
    Theorem,
    TheoremKind,
)
from mapeogeo.kernel.deficiency import DeficiencyRecord
from mapeogeo.kernel.state import KnowledgeState


def test_mathematics_ontology() -> None:
    obj = MathematicalObject(
        object_id="obj:so3",
        name="SO(3) Lie Group",
        object_type=MathematicalObjectType.STRUCTURE,
        domain="Differential Geometry",
        properties=("compact", "connected", "dimension_3"),
        invariants=("det_plus_one", "orthogonality"),
    )
    assert obj.object_type == MathematicalObjectType.STRUCTURE
    assert "compact" in obj.properties

    thm = Theorem(
        theorem_id="thm:artin",
        name="Artin Reciprocity",
        statement="Isomorphism of idele class groups and abelian Galois group",
        kind=TheoremKind.THEOREM,
        domain="Class Field Theory",
        premises=("global_field_K", "abelian_extension_L"),
        conclusion="C_K / N(C_L) =~ Gal(L/K)",
    )
    assert not thm.is_conjecture
    assert not thm.is_counterexample

    prob = MathematicalProblem.create(
        problem_id="Q-TEST-01",
        title="Test Problem",
        domain="Algebra",
        difficulty=1.5,
        structural_distance=2.0,
        novelty=1.2,
        depth=1.4,
        required_signatures=("SIG_A", "SIG_B"),
    )
    assert prob.weight == round(1.5 * 2.0 * 1.2 * 1.4, 3)
    assert len(prob.required_signatures) == 2


def test_required_work_contract_translation() -> None:
    adapter = MathematicsAdapter()
    prob = MathematicalProblem.create(
        problem_id="Q-CFT-001",
        title="Artin Reciprocity Problem",
        domain="Class Field Theory",
        difficulty=1.7,
        structural_distance=6.0,
        novelty=1.5,
        depth=1.5,
        required_signatures=("ARTIN_RECIPROCITY_ISOMORPHISM", "IDELE_CLASS_GROUP_CHARACTERS"),
    )

    contract = adapter.required_work(prob)
    assert contract.contract_id == "work:math:Q-CFT-001"
    assert contract.error_tolerance == 0.0  # Exact mathematical rigor
    assert "has_signature(ARTIN_RECIPROCITY_ISOMORPHISM)" in contract.preconditions
    assert "has_signature(IDELE_CLASS_GROUP_CHARACTERS)" in contract.preconditions
    assert "solved(Q-CFT-001)" in contract.postconditions


def test_grammar_factoring_literal_coordinates() -> None:
    adapter = MathematicsAdapter()

    # 1. Exact factor using registered witness
    res_exact = adapter.factor_grammar(
        work="w_expr_1",
        witness_id="w_cft_1",
        witness_symbol="WITNESS_ARTIN_RECIPROCITY",
        witness_role="Artin reciprocity",
    )
    assert res_exact.classification == FactoringClassification.WITNESS_EXTENSION
    assert res_exact.is_compliant
    assert not res_exact.drift_detected

    # 2. Composition over coordinates
    res_comp = adapter.factor_grammar(
        work=r"\Pi \circ \Gamma \circ w_{cft_1}",
        witness_id="w_cft_1",
    )
    assert res_comp.classification in {
        FactoringClassification.EXACT_FACTOR,
        FactoringClassification.COMPOSITION,
    }
    assert res_comp.is_compliant


def test_grammar_factoring_drift_detection_and_illegal_dimensions() -> None:
    adapter = MathematicsAdapter()

    # Semantic drift via ungrounded heuristic tokens
    res_drift = adapter.factor_grammar(
        work=r"\Delta \circ HEURISTIC_HANDWAVE \circ w_1",
        witness_id="w_1",
    )
    assert res_drift.classification == FactoringClassification.SEMANTIC_DRIFT
    assert res_drift.drift_detected
    assert not res_drift.is_compliant

    # Illegal attempt to expand coordinates beyond d=6
    res_dim = adapter.factor_grammar(
        work=r"\Delta \circ EXTENDED_DIMENSION \circ w_1",
        witness_id="w_1",
    )
    assert res_dim.classification == FactoringClassification.NEW_COORDINATE_REQUIRED
    assert res_dim.drift_detected
    assert not res_dim.is_compliant


def test_mathematical_proof_obligations_translation() -> None:
    thm = Theorem(
        theorem_id="thm:bool_equiv",
        name="De Morgan Equivalence",
        statement="not (A and B) iff (not A) or (not B)",
        kind=TheoremKind.THEOREM,
        domain="Mathematical Logic",
    )

    ob = MathematicalProofObligation(
        obligation_id="ob:math:demorgan",
        theorem=thm,
        verifier_semantic_id="GFY.ROBDD_EQUIVALENCE.v1",
        proof_payload={
            "left": ["not", ["and", "A", "B"]],
            "right": ["or", ["not", "A"], ["not", "B"]],
            "variable_order": ["A", "B"],
        },
    )

    generic_claim = ob.to_generic_claim()
    assert generic_claim.claim_id == "claim:ob:math:demorgan"
    assert generic_claim.subject == "Mathematical Logic"
    assert generic_claim.predicate == "SAME_SEMANTICS"
    assert len(generic_claim.source_identity_sha256) == 64

    generic_ob = ob.to_generic_obligation()
    assert generic_ob.obligation_id == "ob:math:demorgan"
    assert generic_ob.claim == generic_claim

    generic_ev = ob.to_generic_evidence()
    assert generic_ev.evidence_id == "ev:ob:math:demorgan"
    assert len(generic_ev.digest) == 64


def test_mathematics_adapter_certify_via_proof_engine() -> None:
    adapter = MathematicsAdapter()
    thm = Theorem(
        theorem_id="thm:demorgan_sound",
        name="De Morgan Sound Theorem",
        statement="not (A and B) iff (not A) or (not B)",
        kind=TheoremKind.THEOREM,
        domain="Logic",
    )
    ob = MathematicalProofObligation(
        obligation_id="ob:math:demorgan_sound",
        theorem=thm,
        verifier_semantic_id="GFY.ROBDD_EQUIVALENCE.v1",
        proof_payload={
            "left": ["not", ["and", "A", "B"]],
            "right": ["or", ["not", "A"], ["not", "B"]],
            "variable_order": ["A", "B"],
        },
    )

    cert_res = adapter.certify(ob)
    assert cert_res.is_certified
    assert "proof_replay" in cert_res.gates_passed
    assert cert_res.certificate_id is not None


def test_candidate_machinery_and_measure_ability() -> None:
    adapter = MathematicsAdapter()
    prob = MathematicalProblem.create(
        problem_id="Q-TEST-02",
        title="Ability Test Problem",
        domain="Topology",
        difficulty=1.0,
        structural_distance=1.0,
        novelty=1.0,
        depth=1.0,
        required_signatures=("SIG_X", "SIG_Y"),
    )

    state = KnowledgeState.initial()
    assert adapter.measure_ability(prob, state) == 0.0

    deficiency = DeficiencyRecord(
        req_id="d:01",
        weight=2.0,
        required=("SIG_X", "SIG_Y"),
        missing=("SIG_X", "SIG_Y"),
        covered=(),
        is_covered=False,
        coverage_ratio=0.0,
    )
    candidates = adapter.candidate_machinery(deficiency, state)
    assert len(candidates) == 2
    assert {c.provided_signatures[0] for c in candidates} == {"SIG_X", "SIG_Y"}

    # Acquire SIG_X
    node_x = candidates[0] if candidates[0].provided_signatures[0] == "SIG_X" else candidates[1]
    state_step1 = state.transition(
        new_signatures=("SIG_X",),
        new_nodes=[node_x],
    )
    assert 0.0 < adapter.measure_ability(prob, state_step1) < 1.0

    # Acquire SIG_Y
    node_y = candidates[1] if candidates[0].provided_signatures[0] == "SIG_X" else candidates[0]
    state_step2 = state_step1.transition(
        new_signatures=("SIG_Y",),
        new_nodes=[node_y],
    )
    assert adapter.measure_ability(prob, state_step2) == 1.0
