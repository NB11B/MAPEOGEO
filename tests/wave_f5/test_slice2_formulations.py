from __future__ import annotations

import json
from pathlib import Path
import jsonschema

from mapeogeo.wave_f5.scopes import (
    ScopeComparisonOutcome,
    StructuredScopeRecord,
    compare_structured_scopes,
)

ROOT = Path(__file__).resolve().parents[2]


def test_structured_scope_comparison_and_distinctions():
    # 1. Exact match -> EQUAL
    s1 = StructuredScopeRecord(
        space_type="BANACH_SPACE",
        scalar_field="REAL",
        topology_or_norm="NORM_TOPOLOGY",
        dimension_bound="INFINITE_OR_FINITE",
        operator_domain="ENTIRE_SPACE",
        regularity="BOUNDED_LINEAR",
        quantifier_structure="FORALL_X_EXISTS_UNIQUE_Y",
        parameter_box="NONE",
        exceptions="NONE",
    )
    s2 = StructuredScopeRecord(
        space_type="BANACH_SPACE",
        scalar_field="REAL",
        topology_or_norm="NORM_TOPOLOGY",
        dimension_bound="INFINITE_OR_FINITE",
        operator_domain="ENTIRE_SPACE",
        regularity="BOUNDED_LINEAR",
        quantifier_structure="FORALL_X_EXISTS_UNIQUE_Y",
        parameter_box="NONE",
        exceptions="NONE",
    )
    res_eq = compare_structured_scopes(s1, s2)
    assert res_eq.outcome == ScopeComparisonOutcome.EQUAL

    # 2. Weak topology vs Norm topology -> INCOMPATIBLE
    s_weak = StructuredScopeRecord(
        space_type="BANACH_SPACE",
        scalar_field="REAL",
        topology_or_norm="WEAK_TOPOLOGY",
        dimension_bound="INFINITE_OR_FINITE",
        operator_domain="ENTIRE_SPACE",
        regularity="BOUNDED_LINEAR",
        quantifier_structure="FORALL_X_EXISTS_UNIQUE_Y",
        parameter_box="NONE",
        exceptions="NONE",
    )
    res_weak = compare_structured_scopes(s1, s_weak)
    assert res_weak.outcome == ScopeComparisonOutcome.INCOMPATIBLE
    assert "topology_or_norm" in res_weak.mismatches

    # 3. Finite dimension vs Infinite dimension -> CHECKED_RESTRICTION or INCOMPATIBLE
    s_fin = StructuredScopeRecord(
        space_type="BANACH_SPACE",
        scalar_field="REAL",
        topology_or_norm="NORM_TOPOLOGY",
        dimension_bound="FINITE_DIMENSIONAL",
        operator_domain="ENTIRE_SPACE",
        regularity="BOUNDED_LINEAR",
        quantifier_structure="FORALL_X_EXISTS_UNIQUE_Y",
        parameter_box="NONE",
        exceptions="NONE",
    )
    res_fin = compare_structured_scopes(s1, s_fin)
    assert res_fin.outcome == ScopeComparisonOutcome.CHECKED_RESTRICTION


def test_formulations_file_and_schema():
    schema_file = ROOT / "schema" / "wave-f5-formulation.schema.json"
    assert schema_file.is_file(), "schema/wave-f5-formulation.schema.json missing"
    schema = json.loads(schema_file.read_text(encoding="utf-8"))

    form_file = ROOT / "formal" / "wave_f5" / "formulations.json"
    assert form_file.is_file(), "formal/wave_f5/formulations.json missing"
    data = json.loads(form_file.read_text(encoding="utf-8"))

    jsonschema.validate(instance=data, schema=schema)
    assert len(data["formulations"]) >= 10
