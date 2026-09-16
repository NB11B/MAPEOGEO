"""Adversarial requirements for the v0.20 foundation mathematics amendment."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import pytest

from scripts.compute_foundation_depth import (
    RAW_DIRECTIONAL_TYPES,
    build_registered_edge_evidence,
    compute_foundation_metrics,
)
from scripts.foundation_contracts import (
    binomial_coefficient,
    cauchy_sequence_leibniz_pi,
    compute_equivalence_classes,
    geometric_series_sum,
    numerical_difference_quotient,
    numerical_riemann_sum,
    polynomial_eval,
    polynomial_multiply,
    verify_chain_rule_derivative,
    verify_fundamental_theorem_of_calculus,
    verify_product_rule_derivative,
    verify_pythagorean_theorem,
    verify_sequence_convergence_bound,
)
from scripts.foundation_intake import ingest_foundation_declarations
from scripts.import_foundation_backfill import (
    apply_foundation_mathematical_amendments,
    generate_foundation_declarations,
)


ROOT = Path(__file__).resolve().parents[1]
AMENDMENTS = ROOT / "formal" / "foundation_mathematical_amendments_v0_20.json"
REPORT = ROOT / "docs" / "FOUNDATION_MATHEMATICAL_AMENDMENT_V0_20.md"


def _raw_declarations() -> dict[str, dict]:
    source = ROOT / "scripts" / "import_foundation_backfill.py"
    module = ast.parse(source.read_text(encoding="utf-8"))
    function = next(
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "generate_foundation_declarations"
    )
    assignment = next(
        node
        for node in function.body
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id == "raw_declarations"
    )
    rows = ast.literal_eval(assignment.value)
    return {row["node_id"]: row for row in rows}


def test_corrected_statements_expose_required_domains_and_axioms() -> None:
    rows = _raw_declarations()
    required_fragments = {
        "srcdecl:foundation:logic:proposition": ("classical", "bivalent", "valuation"),
        "srcdecl:foundation:logic:contrapositive_proof": ("classical",),
        "srcdecl:foundation:logic:proof_by_contradiction": ("classical", "double-negation"),
        "srcdecl:foundation:logic:quantifier_negation": ("classical", "fixed domain"),
        "srcdecl:foundation:logic:law_of_excluded_middle": ("axiom schema", "not the same assertion"),
        "srcdecl:foundation:set:element_membership": ("primitive", "Extensionality"),
        "srcdecl:foundation:set:empty_set": ("Empty Set axiom", "exists"),
        "srcdecl:foundation:set:union": ("Pairing", "Union axiom"),
        "srcdecl:foundation:set:intersection": ("Separation",),
        "srcdecl:foundation:set:set_difference": ("Separation",),
        "srcdecl:foundation:set:complement": ("fixed set U",),
        "srcdecl:foundation:set:power_set": ("Power Set axiom",),
        "srcdecl:foundation:set:ordered_pair": ("Pairing axiom",),
        "srcdecl:foundation:set:cartesian_product": ("Power Set", "Separation"),
        "srcdecl:foundation:set:set_partition": ("set P",),
        "srcdecl:foundation:set:arbitrary_union_intersection": ("set-sized", "nonempty"),
        "srcdecl:foundation:set:indicator_algebra": ("fixed universe X",),
        "srcdecl:foundation:set:axiom_of_choice_primitive": ("set I", "nonempty set"),
        "srcdecl:foundation:rel:fundamental_theorem_equivalence": ("x ~_P y",),
        "srcdecl:foundation:num:peano_axioms_naturals": ("second-order", "m <= n",),
        "srcdecl:foundation:num:integers_construction": ("well-defined", "[a,b] + [c,d]"),
        "srcdecl:foundation:num:integer_divisibility": ("including a = 0",),
        "srcdecl:foundation:num:rational_numbers_construction": ("[a,b] + [c,d]", "[a,b] * [c,d]"),
        "srcdecl:foundation:num:rational_density": ("Archimedean",),
        "srcdecl:foundation:num:irrationality_sqrt_2": ("unique nonnegative real", "no rational"),
        "srcdecl:foundation:num:real_numbers_axioms": ("Dedekind-complete ordered field", "fixing Q"),
        "srcdecl:foundation:num:dedekind_cut_construction": ("proper nonempty lower", "field operations"),
        "srcdecl:foundation:num:cauchy_sequence_reals": ("null-sequence ideal", "termwise"),
        "srcdecl:foundation:num:complex_conjugate_modulus": ("unique nonnegative real",),
        "srcdecl:foundation:num:polar_form_complex": ("nonzero", "trigonometric"),
        "srcdecl:foundation:num:algebraic_closure_c_primitive": ("nonconstant", "complex coefficients"),
        "srcdecl:foundation:alg:commutative_law": ("is called commutative iff",),
        "srcdecl:foundation:alg:associative_law": ("is called associative iff",),
        "srcdecl:foundation:alg:distributive_law": ("are distributive iff",),
        "srcdecl:foundation:alg:identity_and_inverses": ("when they exist",),
        "srcdecl:foundation:alg:polynomial_division_algorithm": ("R(x) = 0 or",),
        "srcdecl:foundation:alg:pascals_identity": ("1 <= k <= n-1",),
        "srcdecl:foundation:alg:quadratic_formula": ("a, b, c in C", "s^2"),
        "srcdecl:foundation:alg:vector_space_axioms_primitive": ("1_F v = v",),
        "srcdecl:foundation:seq:supremum_infimum": ("nonempty", "bounded above"),
        "srcdecl:foundation:seq:algebraic_limit_theorem": ("b_n != 0",),
        "srcdecl:foundation:seq:divergence_test": ("does not converge to 0",),
        "srcdecl:foundation:seq:metric_space_axioms_primitive": ("d(x, z) <= d(x, y) + d(y, z)",),
        "srcdecl:foundation:geom:euclidean_plane_R2": ("standard inner product",),
        "srcdecl:foundation:geom:euclidean_space_Rn": ("integer n >= 1", "standard inner product"),
        "srcdecl:foundation:geom:sine_cosine_unit_circle": ("radians",),
        "srcdecl:foundation:geom:tangent_trig_definition": ("sin theta != 0",),
        "srcdecl:foundation:geom:pythagorean_trig_identities": ("where both sides are defined",),
        "srcdecl:foundation:geom:law_of_sines": ("nondegenerate", "circumradius"),
        "srcdecl:foundation:geom:polar_coordinates_R2": ("nonzero", "origin"),
        "srcdecl:foundation:calc:function_limit_epsilon_delta": ("accumulation point",),
        "srcdecl:foundation:calc:one_sided_limits": ("one-sided accumulation",),
        "srcdecl:foundation:calc:continuity_at_point": ("for every epsilon",),
        "srcdecl:foundation:calc:continuity_on_interval": ("right-continuous", "left-continuous"),
        "srcdecl:foundation:calc:intermediate_value_theorem": ("a < b",),
        "srcdecl:foundation:calc:derivative_difference_quotient": ("x + h in D",),
        "srcdecl:foundation:calc:derivative_power_rule": ("integer n >= 1",),
        "srcdecl:foundation:calc:derivative_linearity": ("differentiable at x",),
        "srcdecl:foundation:calc:derivative_product_rule": ("differentiable at x",),
        "srcdecl:foundation:calc:derivative_quotient_rule": ("differentiable at x",),
        "srcdecl:foundation:calc:derivative_trig_functions": ("radians", "cos x != 0"),
        "srcdecl:foundation:calc:derivative_exponential_log": ("Define ln x = int_1^x", "let exp be its inverse"),
        "srcdecl:foundation:calc:rolles_theorem": ("a < b",),
        "srcdecl:foundation:calc:mean_value_theorem": ("a < b",),
        "srcdecl:foundation:calc:first_derivative_test": ("continuous at c", "there exists delta > 0"),
        "srcdecl:foundation:calc:riemann_partition_sum": ("a < b", "n >= 1"),
        "srcdecl:foundation:calc:riemann_definite_integral": ("every sequence of tagged partitions", "int_b^a"),
        "srcdecl:foundation:calc:integration_by_parts": ("continuously differentiable",),
        "srcdecl:foundation:calc:integration_by_substitution": ("continuously differentiable",),
        "srcdecl:foundation:calc:taylors_theorem_primitive": ("integer n >= 0", "x != a"),
    }
    for node_id, fragments in required_fragments.items():
        text = rows[node_id]["text"]
        for fragment in fragments:
            assert fragment in text, f"{node_id} lacks {fragment!r}"


def test_structural_references_are_candidates_not_automatic_proofs() -> None:
    assert "STRUCTURAL_REFERENCE" in RAW_DIRECTIONAL_TYPES
    declarations = generate_foundation_declarations()
    graph = ingest_foundation_declarations({"nodes": [], "edges": []}, declarations)
    reference_edges = [edge for edge in graph["edges"] if edge["id"].startswith("e:ref:")]
    assert reference_edges
    assert {edge["type"] for edge in reference_edges} == {"STRUCTURAL_REFERENCE"}
    assert all(edge["attributes"]["relation_status"] == "UNVERIFIED_CANDIDATE" for edge in reference_edges)
    assert not any(edge["type"] == "PROOF_DEPENDENCY" for edge in graph["edges"])


def test_proof_dependency_requires_closed_endpoint_bound_evidence() -> None:
    source = "srcdecl:foundation:test:source"
    target = "canonical:advanced:test"
    graph = {
        "nodes": [
            {
                "id": source,
                "type": "SOURCE_DECLARATION",
                "attributes": {
                    "source_id": "FOUNDATION_MATHEMATICS_BASE",
                    "statement_sha256": "1" * 64,
                },
            },
            {"id": target, "type": "CANONICAL_OBJECT", "attributes": {"domain": "Test"}},
        ],
        "edges": [],
    }
    nodes = {node["id"]: node for node in graph["nodes"]}
    edge, record = build_registered_edge_evidence(
        edge_id="proof",
        edge_type="PROOF_DEPENDENCY",
        source=source,
        target=target,
        nodes=nodes,
    )
    graph["edges"] = [edge]
    without_registry = compute_foundation_metrics(graph, validated_root_ids={source})
    with_registry = compute_foundation_metrics(
        graph,
        edge_evidence_registry={record.evidence_digest: record},
        validated_root_ids={source},
    )
    assert without_registry["proof_eligible_grounding"]["advanced_canonical_objects_reachable"] == 0
    assert with_registry["proof_eligible_grounding"]["advanced_canonical_objects_reachable"] == 1


def test_amendment_registry_binds_every_changed_statement_hash() -> None:
    payload = json.loads(AMENDMENTS.read_text(encoding="utf-8"))
    records = payload["amendments"]
    assert payload["schema_version"] == "1.0.0"
    assert payload["claim_boundary"] == "STATEMENT_CORRECTION_ONLY_NOT_PROOF"
    historical = payload["historical_rows"]
    current_rows = _raw_declarations()
    assert len(historical) == len(current_rows) == 176
    assert len(records) == len({item["subject_id"] for item in records})
    generated = {item.node_id: item for item in generate_foundation_declarations()}
    changed_ids = {
        node_id
        for node_id, row in current_rows.items()
        if historical[node_id]
        != {
            "label": row["label"],
            "decl_type": row["decl_type"],
            "statement_sha256": generated[node_id].statement_sha256,
            "structural_refs": row["structural_refs"],
        }
    }
    assert changed_ids == {item["subject_id"] for item in records}
    for item in records:
        assert item["status"] == "ACTIVE_STATEMENT_AMENDMENT_UNVERIFIED"
        assert len(item["reason"]) >= 20
        assert item["historical_identity"] == historical[item["subject_id"]]
        row = current_rows[item["subject_id"]]
        assert item["corrected_identity"] == {
            "label": row["label"],
            "decl_type": row["decl_type"],
            "statement_sha256": generated[item["subject_id"]].statement_sha256,
            "structural_refs": row["structural_refs"],
        }
        assert item["historical_identity"] != item["corrected_identity"]
        canonical = json.dumps(
            {
                "subject_id": item["subject_id"],
                "historical_identity": item["historical_identity"],
                "corrected_identity": item["corrected_identity"],
                "reason": item["reason"],
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        assert item["amendment_sha256"] == hashlib.sha256(canonical.encode()).hexdigest()


def test_amendment_registry_cannot_rewrite_history_or_forge_ids(tmp_path: Path) -> None:
    payload = json.loads(AMENDMENTS.read_text(encoding="utf-8"))
    first = payload["amendments"][0]
    subject_id = first["subject_id"]
    payload["historical_rows"][subject_id] = first["corrected_identity"]
    payload["amendments"] = [
        item for item in payload["amendments"] if item["subject_id"] != subject_id
    ]
    forged_history = tmp_path / "forged-history.json"
    forged_history.write_text(json.dumps(payload), encoding="utf-8")
    declarations = generate_foundation_declarations()
    for declaration in declarations:
        declaration.amendment_id = None
        declaration.amendment_status = None
    with pytest.raises(ValueError, match="historical foundation baseline digest"):
        apply_foundation_mathematical_amendments(declarations, forged_history)

    payload = json.loads(AMENDMENTS.read_text(encoding="utf-8"))
    payload["amendments"][0]["amendment_id"] = "amendment:v0.20:foundation:forged"
    forged_id = tmp_path / "forged-id.json"
    forged_id.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="amendment ID is invalid"):
        apply_foundation_mathematical_amendments(declarations, forged_id)


def test_active_declaration_projection_exposes_only_exact_amendments() -> None:
    declarations = generate_foundation_declarations()
    amended = [item for item in declarations if item.amendment_id is not None]
    untouched = [item for item in declarations if item.amendment_id is None]
    assert len(amended) == 84
    assert len(untouched) == 92
    assert all(item.amendment_status == "ACTIVE_STATEMENT_AMENDMENT_UNVERIFIED" for item in amended)
    assert all(item.amendment_status is None for item in untouched)
    graph = ingest_foundation_declarations({"nodes": [], "edges": []}, declarations)
    nodes = {node["id"]: node for node in graph["nodes"]}
    amended_node = nodes[amended[0].node_id]["attributes"]
    untouched_node = nodes[untouched[0].node_id]["attributes"]
    assert amended_node["statement_amendment_id"] == amended[0].amendment_id
    assert amended_node["statement_amendment_status"] == "ACTIVE_STATEMENT_AMENDMENT_UNVERIFIED"
    assert "statement_amendment_id" not in untouched_node


def test_misleading_public_helpers_fail_closed() -> None:
    with pytest.raises(ValueError, match="equivalence relation"):
        compute_equivalence_classes(set(), {1})
    with pytest.raises(ValueError, match="nonnegative"):
        binomial_coefficient(-1, 0)
    with pytest.raises(ValueError, match="nonnegative"):
        geometric_series_sum(1.0, 0.5, -1)
    with pytest.raises(ValueError, match="nonnegative"):
        cauchy_sequence_leibniz_pi(-1)
    with pytest.raises(ValueError, match="nonempty"):
        polynomial_eval([], 1.0)
    with pytest.raises(ValueError, match="nonempty"):
        polynomial_multiply([], [1.0])
    with pytest.raises(ValueError, match="finite window"):
        verify_sequence_convergence_bound(lambda _n: 0.0, 0.0, 0.1, 0, 100)
    assert not verify_pythagorean_theorem([1.0, 0.0], [1e-8, 1.0])
    assert not verify_product_rule_derivative(
        lambda _x: 1.0,
        lambda _x: 1.0,
        lambda _x: 1.0,
        lambda _x: -1.0,
        0.0,
    )
    assert not verify_chain_rule_derivative(
        lambda y: y * y,
        lambda _y: 999.0,
        lambda _x: 0.0,
        lambda _x: 0.0,
        2.0,
    )
    assert not verify_fundamental_theorem_of_calculus(
        lambda _x: 0.0,
        lambda x: x * (x - 1.0),
        0.0,
        1.0,
    )
    with pytest.raises(ValueError, match="nonzero"):
        numerical_difference_quotient(lambda x: x, 0.0, 0.0)
    with pytest.raises(ValueError, match="positive integer"):
        numerical_riemann_sum(lambda x: x, 0.0, 1.0, -1)


def test_foundation_amendment_report_keeps_the_claim_boundary_truthful() -> None:
    text = REPORT.read_text(encoding="utf-8")
    assert "84 exact declaration identity amendments" in text
    assert "not proof" in text.lower()
    assert "1 / 176" in text
    assert "0 / 176" in text
    assert "STRUCTURAL_REFERENCE" in text
    assert "PROOF_DEPENDENCY" in text
