"""Tests for MAPEOGEO certifiable endpoint semantics schema, models, and census audit."""

from __future__ import annotations

import json
import os
from pathlib import Path
import jsonschema
import pytest

from mapeogeo.certifiable.schema import (
    FORBIDDEN_ORIGINS,
    OriginKind,
    PayloadMode,
    ProvenanceDerivation,
    ProvenanceOrigin,
    CertifiableProvenance,
    CertifiableRepresentation,
)
from scripts.audit_certifiable_semantics import run_certifiable_semantics_census

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "schema" / "certifiable-representation.schema.json"
ARTIFACTS_DIR = REPO_ROOT / "artifacts" / "certifiable_semantics"


def _load_schema() -> dict:
    with open(SCHEMA_PATH, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def _valid_provenance() -> CertifiableProvenance:
    origin = ProvenanceOrigin(
        kind=OriginKind.EXECUTABLE_CONTRACT,
        source_node="srcdecl:proposition:3_13",
        statement_sha256="a" * 64,
        contract_id="linear_independence_not_in_span_q",
        formal_decl="linear_independence_not_in_span_q",
    )
    derivation = ProvenanceDerivation(
        adapter="mapeogeo.adapters.executable_contract",
        adapter_version="1.0.0",
        inputs_sha256="b" * 64,
        output_sha256="c" * 64,
    )
    return CertifiableProvenance(origin=origin, derivation=derivation)


class TestCertifiableSchemaAndValidation:
    """Test JSON Schema and Python model validation."""

    def test_schema_loads_and_is_valid(self):
        schema = _load_schema()
        assert schema["$id"] == "mapeogeo.certifiable-representation.v1"
        assert schema["type"] == "object"
        # Validate schema against Meta-schema
        validator_cls = jsonschema.validators.validator_for(schema)
        validator_cls.check_schema(schema)

    def test_schema_validates_contract_reference_mode(self):
        schema = _load_schema()
        repr_obj = CertifiableRepresentation(
            id="repr:exec:linear_independence_not_in_span_q",
            semantic_family="GFY.ORTHOGONAL_PROJECTION_EQUIVALENCE.v1",
            payload_mode=PayloadMode.CONTRACT_REFERENCE,
            payload={"contract_id": "linear_independence_not_in_span_q"},
            executable_contract="linear_independence_not_in_span_q",
            scope="EXACT_RATIONAL_VECTORS",
            formal_decl="linear_independence_not_in_span_q",
            provenance=_valid_provenance(),
        )
        node_dict = repr_obj.to_node_dict()
        jsonschema.validate(instance=node_dict, schema=schema)

    def test_schema_validates_concrete_mode(self):
        schema = _load_schema()
        origin = ProvenanceOrigin(
            kind=OriginKind.SOURCE_LITERAL,
            source_node="srcdecl:theorem:farkas_concrete",
            statement_sha256="1" * 64,
        )
        derivation = ProvenanceDerivation(
            adapter="mapeogeo.adapters.literal_parser",
            adapter_version="1.0.0",
            inputs_sha256="2" * 64,
            output_sha256="3" * 64,
        )
        prov = CertifiableProvenance(origin=origin, derivation=derivation)
        repr_obj = CertifiableRepresentation(
            id="repr:exec:farkas_cone_01",
            semantic_family="GFY.FARKAS_IMPLICATION.v1",
            payload_mode=PayloadMode.CONCRETE,
            payload={"matrix": [[1.0, 2.0], [3.0, 4.0]], "rhs": [1.0, 1.0]},
            provenance=prov,
        )
        node_dict = repr_obj.to_node_dict()
        jsonschema.validate(instance=node_dict, schema=schema)

    def test_schema_validates_symbolic_mode(self):
        schema = _load_schema()
        origin = ProvenanceOrigin(
            kind=OriginKind.FORMAL_DECLARATION,
            source_node="canonical:spectral_decomposition",
            statement_sha256="4" * 64,
            formal_decl="spectral_decomposition_symmetric_matrix",
        )
        derivation = ProvenanceDerivation(
            adapter="mapeogeo.adapters.formal_ast",
            adapter_version="1.0.0",
            inputs_sha256="5" * 64,
            output_sha256="6" * 64,
        )
        prov = CertifiableProvenance(origin=origin, derivation=derivation)
        repr_obj = CertifiableRepresentation(
            id="repr:exec:spectral_decomp_symbolic",
            semantic_family="GFY.SPECTRAL_DECOMPOSITION.v1",
            payload_mode=PayloadMode.SYMBOLIC,
            payload={"variables": ["A", "Q", "Lambda"], "claim": "A == Q @ Lambda @ Q.T"},
            formal_decl="spectral_decomposition_symmetric_matrix",
            provenance=prov,
        )
        node_dict = repr_obj.to_node_dict()
        jsonschema.validate(instance=node_dict, schema=schema)

    def test_schema_rejects_invalid_id_prefix(self):
        schema = _load_schema()
        node_dict = {
            "id": "srcdecl:invalid_prefix",
            "type": "REPRESENTATION",
            "view": "EXECUTABLE",
            "attributes": {
                "schema": "mapeogeo.certifiable-representation.v1",
                "semantic_family": "GFY.ORTHOGONAL_PROJECTION_EQUIVALENCE.v1",
                "payload_mode": "concrete",
                "payload": {"matrix": [[1, 0], [0, 1]]},
                "provenance": _valid_provenance().to_dict(),
            },
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=node_dict, schema=schema)

    def test_schema_rejects_invalid_type_view(self):
        schema = _load_schema()
        node_dict = {
            "id": "repr:exec:valid_id",
            "type": "SOURCE_DECLARATION",
            "view": "EXECUTABLE",
            "attributes": {
                "schema": "mapeogeo.certifiable-representation.v1",
                "semantic_family": "GFY.ORTHOGONAL_PROJECTION_EQUIVALENCE.v1",
                "payload_mode": "concrete",
                "payload": {"matrix": [[1, 0], [0, 1]]},
                "provenance": _valid_provenance().to_dict(),
            },
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=node_dict, schema=schema)


class TestForbiddenOriginsRejection:
    """Test zero-fabrication origin enforcement."""

    @pytest.mark.parametrize("forbidden_kind", list(FORBIDDEN_ORIGINS))
    def test_forbidden_origin_in_provenance_rejected(self, forbidden_kind: str):
        with pytest.raises(ValueError, match="explicitly forbidden under zero-fabrication rules"):
            ProvenanceOrigin(
                kind=forbidden_kind,  # type: ignore[arg-type]
                source_node="srcdecl:test",
                statement_sha256="a" * 64,
            )

    @pytest.mark.parametrize("forbidden_kind", list(FORBIDDEN_ORIGINS))
    def test_forbidden_origin_in_schema_rejected(self, forbidden_kind: str):
        schema = _load_schema()
        prov_dict = _valid_provenance().to_dict()
        prov_dict["origin"]["kind"] = forbidden_kind
        node_dict = {
            "id": "repr:exec:test_node",
            "type": "REPRESENTATION",
            "view": "EXECUTABLE",
            "attributes": {
                "schema": "mapeogeo.certifiable-representation.v1",
                "semantic_family": "GFY.ORTHOGONAL_PROJECTION_EQUIVALENCE.v1",
                "payload_mode": "concrete",
                "payload": {"data": 123},
                "provenance": prov_dict,
            },
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=node_dict, schema=schema)


class TestDataclassModelInvariants:
    """Test dataclass behavior, invariants, and round-trips."""

    def test_representation_roundtrip(self):
        repr_obj = CertifiableRepresentation(
            id="repr:exec:linear_independence_not_in_span_q",
            semantic_family="GFY.ORTHOGONAL_PROJECTION_EQUIVALENCE.v1",
            payload_mode=PayloadMode.CONTRACT_REFERENCE,
            payload={"contract_id": "linear_independence_not_in_span_q"},
            executable_contract="linear_independence_not_in_span_q",
            scope="EXACT_RATIONAL_VECTORS",
            formal_decl="linear_independence_not_in_span_q",
            provenance=_valid_provenance(),
        )
        node_dict = repr_obj.to_node_dict()
        restored = CertifiableRepresentation.from_node_dict(node_dict)
        assert restored == repr_obj
        assert restored.id == repr_obj.id
        assert restored.provenance.origin.statement_sha256 == "a" * 64

    def test_concrete_payload_cannot_be_empty(self):
        with pytest.raises(ValueError, match="Concrete payload mode requires non-empty"):
            CertifiableRepresentation(
                id="repr:exec:empty_concrete",
                semantic_family="GFY.ORTHOGONAL_PROJECTION_EQUIVALENCE.v1",
                payload_mode=PayloadMode.CONCRETE,
                payload={},
                provenance=_valid_provenance(),
            )

    def test_contract_reference_requires_contract(self):
        with pytest.raises(ValueError, match="Contract reference payload requires executable_contract"):
            CertifiableRepresentation(
                id="repr:exec:missing_contract",
                semantic_family="GFY.ORTHOGONAL_PROJECTION_EQUIVALENCE.v1",
                payload_mode=PayloadMode.CONTRACT_REFERENCE,
                payload={},
                executable_contract=None,
                provenance=_valid_provenance(),
            )

    def test_symbolic_requires_variables_or_claim(self):
        with pytest.raises(ValueError, match="Symbolic payload mode requires variables or claim"):
            CertifiableRepresentation(
                id="repr:exec:empty_symbolic",
                semantic_family="GFY.ORTHOGONAL_PROJECTION_EQUIVALENCE.v1",
                payload_mode=PayloadMode.SYMBOLIC,
                payload={"description": "empty"},
                provenance=_valid_provenance(),
            )

    def test_invalid_sha256_raises_value_error(self):
        with pytest.raises(ValueError, match="Invalid statement_sha256"):
            ProvenanceOrigin(
                kind=OriginKind.SOURCE_LITERAL,
                source_node="srcdecl:test",
                statement_sha256="not_a_sha256",
            )


class TestCensusReproducibilityAndConservation:
    """Test Workstream 1 Census reproducibility, conservation arithmetic, and artifact generation."""

    def test_census_execution_and_conservation(self):
        coverage = run_certifiable_semantics_census()

        # Audit exact totals
        assert coverage["total_nodes_audited"] == 670
        assert coverage["total_edges_in_snapshot"] == 1608

        # Audit tier breakdown
        summary = coverage["classification_summary"]
        assert summary["DIRECT_PAYLOAD"] == 0
        assert summary["EXECUTABLE_CONTRACT"] == 3
        assert summary["FORMAL_DERIVABLE"] == 29
        assert summary["CERTIFICATE_DERIVABLE"] == 20
        assert summary["STRUCTURAL_ONLY"] == 443
        assert summary["NARRATIVE_ONLY"] == 175

        # Conservation arithmetic
        assert coverage["conservation_check"]["total_matches_sum"] is True
        assert coverage["certifiable_pool_total"] == 52
        assert coverage["unresolved_pool_total"] == 618
        assert coverage["certifiable_pool_total"] + coverage["unresolved_pool_total"] == 670
        assert coverage["certifiable_coverage_pct"] == 7.76

        # Check artifact persistence on disk
        assert (ARTIFACTS_DIR / "coverage.json").exists()
        assert (ARTIFACTS_DIR / "candidates.json").exists()
        assert (ARTIFACTS_DIR / "unresolved.json").exists()
        assert (ARTIFACTS_DIR / "verifier_coverage.json").exists()

        with open(ARTIFACTS_DIR / "candidates.json", "r", encoding="utf-8") as f:
            cand_data = json.load(f)
            assert cand_data["total_candidates"] == 52
            assert len(cand_data["candidates"]) == 52

        with open(ARTIFACTS_DIR / "unresolved.json", "r", encoding="utf-8") as f:
            unres_data = json.load(f)
            assert unres_data["total_unresolved"] == 618
            assert len(unres_data["unresolved"]) == 618
