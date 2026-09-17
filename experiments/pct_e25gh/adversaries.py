from __future__ import annotations

from copy import deepcopy
from fractions import Fraction

from .morphisms import (
    canonical_json,
    _rank_eo,
    _convex_eo,
    _lp_eo,
    _gauss_eo,
)
from .provenance import run_c5b_audit


_BINDING_FIELDS = (
    "component_id",
    "source_statement_sha256",
    "contract",
    "formal_scope",
    "source_artifact_digest",
    "source_commit_sha",
    "eo_id",
    "geo_id",
    "formal_id",
    "certificate_ids",
    "adapter_id",
    "adapter_sha256",
    "predecessor_evidence_ids",
)


def _valid_morphism_fixture(contract: str) -> dict:
    if contract == "rank":
        return _rank_eo([[1, 1], [0, 0]])
    if contract == "convex":
        return _convex_eo((Fraction(-1), Fraction(1)), Fraction(0))
    if contract == "lp":
        return _lp_eo((1, 1), (1, 1), 1)
    if contract == "gauss":
        return _gauss_eo()
    raise KeyError(contract)


def _binding_payload(component: dict) -> dict:
    return {field: deepcopy(component[field]) for field in _BINDING_FIELDS}


def _corrupt_witness_only(contract: str, record: dict) -> dict:
    bad = deepcopy(record)
    if contract == "rank":
        bad["canonical_nullspace_basis"] = [[0, 1]]
    elif contract == "convex":
        bad["witness"]["lambda"] = Fraction(1, 3)
        bad["witness"]["coefficients"] = [Fraction(2, 3), Fraction(1, 3)]
    elif contract == "lp":
        bad["active_indices"] = [0]
        bad["canonical_active_witnesses"] = bad["canonical_active_witnesses"][:1]
    elif contract == "gauss":
        bad["normalized_expression"] = "dot/s2-nx/(2*s2)-ny/(2*s2)"
    else:
        raise KeyError(contract)
    return bad


def _corrupt_exact_map(contract: str, record: dict) -> dict:
    bad = deepcopy(record)
    if contract == "rank":
        bad["rref"][0][1] ^= 1
    elif contract == "convex":
        bad["witness"]["coefficients"] = [Fraction(3, 4), Fraction(1, 4)]
    elif contract == "lp":
        bad["canonical_active_witnesses"][0]["dual_y"] = Fraction(2)
    elif contract == "gauss":
        bad["normalized_expression"] = "(-1/2)*nx/s2+(-1/2)*ny/s2+(1/1)*dot/s2+0"
    else:
        raise KeyError(contract)
    return bad


def _make_case(contract: str, fault_class: str, valid_map: dict, candidate_map: dict, valid_provenance: dict, candidate_provenance: dict, diagnostics: dict) -> dict:
    c5a_pass = canonical_json(candidate_map) == canonical_json(valid_map)
    c5b_pass = canonical_json(candidate_provenance) == canonical_json(valid_provenance)
    return {
        "fault_class": fault_class,
        "provenance_class": "SYNTHETIC_CONTROL",
        "c5a_state": "PASS" if c5a_pass else "FAIL",
        "c5b_state": "PASS" if c5b_pass else "FAIL",
        "diagnostics": diagnostics,
    }


def build_adversarial_matrix() -> list[dict]:
    provenance = {c["contract"]: c for c in run_c5b_audit()["components"]}
    contracts = []
    contract_names = ("rank", "convex", "lp", "gauss")
    for index, contract in enumerate(contract_names):
        valid_map = _valid_morphism_fixture(contract)
        valid_prov = _binding_payload(provenance[contract])
        cases = []

        wrong_prov = deepcopy(valid_prov)
        wrong_prov["source_statement_sha256"] = "0" * 64
        cases.append(_make_case(
            contract,
            "CORRECT_MAP_WRONG_PROVENANCE",
            valid_map,
            valid_map,
            valid_prov,
            wrong_prov,
            {"map_unchanged": True, "mutated_binding": "source_statement_sha256"},
        ))

        wrong_map = _corrupt_exact_map(contract, valid_map)
        cases.append(_make_case(
            contract,
            "WRONG_MAP_CORRECT_PROVENANCE",
            valid_map,
            wrong_map,
            valid_prov,
            valid_prov,
            {"provenance_unchanged": True, "exact_record_changed": True},
        ))

        wrong_witness = _corrupt_witness_only(contract, valid_map)
        cases.append(_make_case(
            contract,
            "SAME_ENDPOINT_WRONG_WITNESS",
            valid_map,
            wrong_witness,
            valid_prov,
            valid_prov,
            {"lower_layer_endpoint_preserved": True, "witness_record_changed": True},
        ))

        altered_transform = _corrupt_exact_map(contract, valid_map)
        cases.append(_make_case(
            contract,
            "CORRECT_LINEAGE_ALTERED_TRANSFORMATION",
            valid_map,
            altered_transform,
            valid_prov,
            valid_prov,
            {"source_lineage_unchanged": True, "adapter_output_changed": True},
        ))

        copied_prov = deepcopy(valid_prov)
        copied_prov["component_id"] = provenance[contract_names[(index + 1) % len(contract_names)]]["component_id"]
        cases.append(_make_case(
            contract,
            "EXACT_MAP_COPIED_ACROSS_IDENTITIES",
            valid_map,
            valid_map,
            valid_prov,
            copied_prov,
            {"map_unchanged": True, "mutated_binding": "component_id"},
        ))

        contracts.append({
            "contract": contract,
            "valid_case": {"c5a_state": "PASS", "c5b_state": "PASS"},
            "adversarial_cases": cases,
        })
    return contracts
