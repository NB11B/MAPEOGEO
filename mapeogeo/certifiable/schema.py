"""MAPEOGEO Certifiable Mathematical Representation Schema & Models (v1).

Defines the formal data contracts, payload modes, and provenance chains for
machine-readable certifiable mathematical representations in MAPEOGEO.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Mapping


SCHEMA_REPRESENTATION_ID = "mapeogeo.certifiable-representation.v1"
SCHEMA_PROVENANCE_ID = "mapeogeo.certifiable-provenance.v1"


def sha256_text(text: str) -> str:
    """Compute standard SHA-256 hex digest of a UTF-8 string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_json(data: Any) -> str:
    """Serialize data structure to canonical deterministically sorted JSON."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


class PayloadMode(str, Enum):
    CONCRETE = "concrete"
    SYMBOLIC = "symbolic"
    CONTRACT_REFERENCE = "contract_reference"


class OriginKind(str, Enum):
    SOURCE_LITERAL = "SOURCE_LITERAL"
    FORMAL_DECLARATION = "FORMAL_DECLARATION"
    EXECUTABLE_CONTRACT = "EXECUTABLE_CONTRACT"
    VERIFIED_CERTIFICATE = "VERIFIED_CERTIFICATE"
    CANONICAL_DERIVATION = "CANONICAL_DERIVATION"


# Explicitly forbidden origins (must never appear in certifiable provenance)
FORBIDDEN_ORIGINS = {
    "HEURISTIC_INFERENCE",
    "LIKELY_EXAMPLE",
    "DOMAIN_DEFAULT",
    "CANONICAL_EXAMPLE",
    "SYNTHETIC_FALLBACK",
}


@dataclass(frozen=True)
class ProvenanceOrigin:
    kind: OriginKind
    source_node: str
    statement_sha256: str
    formal_decl: str | None = None
    contract_id: str | None = None

    def __post_init__(self) -> None:
        if isinstance(self.kind, str) and self.kind in FORBIDDEN_ORIGINS:
            raise ValueError(f"Origin kind {self.kind} is explicitly forbidden under zero-fabrication rules")
        if not re_is_sha256(self.statement_sha256):
            raise ValueError(f"Invalid statement_sha256: {self.statement_sha256}")


@dataclass(frozen=True)
class ProvenanceDerivation:
    adapter: str
    adapter_version: str
    inputs_sha256: str
    output_sha256: str

    def __post_init__(self) -> None:
        if not re_is_sha256(self.inputs_sha256):
            raise ValueError(f"Invalid inputs_sha256: {self.inputs_sha256}")
        if not re_is_sha256(self.output_sha256):
            raise ValueError(f"Invalid output_sha256: {self.output_sha256}")


@dataclass(frozen=True)
class CertifiableProvenance:
    origin: ProvenanceOrigin
    derivation: ProvenanceDerivation
    schema: str = SCHEMA_PROVENANCE_ID

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "origin": asdict(self.origin),
            "derivation": asdict(self.derivation),
        }


@dataclass(frozen=True)
class CertifiableRepresentation:
    id: str
    semantic_family: str
    payload_mode: PayloadMode
    payload: dict[str, Any]
    provenance: CertifiableProvenance
    assumptions: list[str] = field(default_factory=list)
    formal_decl: str | None = None
    executable_contract: str | None = None
    scope: str | None = None
    type: str = "REPRESENTATION"
    view: str = "EXECUTABLE"
    schema: str = SCHEMA_REPRESENTATION_ID

    def __post_init__(self) -> None:
        if not self.id.startswith("repr:exec:"):
            raise ValueError(f"Representation node ID must start with 'repr:exec:', got: {self.id}")
        if self.type != "REPRESENTATION" or self.view != "EXECUTABLE":
            raise ValueError(f"Invalid type/view: type={self.type}, view={self.view}")

        # Validate payload mode integrity
        if self.payload_mode == PayloadMode.CONTRACT_REFERENCE:
            if not self.executable_contract and not self.payload.get("contract_id"):
                raise ValueError("Contract reference payload requires executable_contract identifier")
        elif self.payload_mode == PayloadMode.CONCRETE:
            if not self.payload:
                raise ValueError("Concrete payload mode requires non-empty explicit mathematical payload")
        elif self.payload_mode == PayloadMode.SYMBOLIC:
            if not self.payload.get("variables") and not self.payload.get("claim"):
                raise ValueError("Symbolic payload mode requires variables or claim specification")

    def to_node_dict(self) -> dict[str, Any]:
        """Convert to canonical MAPEOGEO graph node format."""
        attrs = {
            "schema": self.schema,
            "semantic_family": self.semantic_family,
            "payload_mode": self.payload_mode.value if isinstance(self.payload_mode, PayloadMode) else str(self.payload_mode),
            "payload": self.payload,
            "assumptions": self.assumptions,
            "formal_decl": self.formal_decl,
            "executable_contract": self.executable_contract,
            "scope": self.scope,
            "provenance": self.provenance.to_dict(),
        }
        return {
            "id": self.id,
            "type": self.type,
            "view": self.view,
            "attributes": attrs,
        }

    @classmethod
    def from_node_dict(cls, data: Mapping[str, Any]) -> CertifiableRepresentation:
        """Parse from MAPEOGEO graph node format."""
        nid = str(data["id"])
        ntype = str(data.get("type", "REPRESENTATION"))
        nview = str(data.get("view", "EXECUTABLE"))
        attrs = data.get("attributes", {})

        prov_dict = attrs.get("provenance", {})
        origin_dict = prov_dict.get("origin", {})
        deriv_dict = prov_dict.get("derivation", {})

        origin = ProvenanceOrigin(
            kind=OriginKind(origin_dict["kind"]),
            source_node=origin_dict["source_node"],
            statement_sha256=origin_dict["statement_sha256"],
            formal_decl=origin_dict.get("formal_decl"),
            contract_id=origin_dict.get("contract_id"),
        )
        derivation = ProvenanceDerivation(
            adapter=deriv_dict["adapter"],
            adapter_version=deriv_dict["adapter_version"],
            inputs_sha256=deriv_dict["inputs_sha256"],
            output_sha256=deriv_dict["output_sha256"],
        )
        provenance = CertifiableProvenance(
            schema=prov_dict.get("schema", SCHEMA_PROVENANCE_ID),
            origin=origin,
            derivation=derivation,
        )

        return cls(
            id=nid,
            semantic_family=attrs["semantic_family"],
            payload_mode=PayloadMode(attrs["payload_mode"]),
            payload=dict(attrs["payload"]),
            provenance=provenance,
            assumptions=list(attrs.get("assumptions", [])),
            formal_decl=attrs.get("formal_decl"),
            executable_contract=attrs.get("executable_contract"),
            scope=attrs.get("scope"),
            type=ntype,
            view=nview,
            schema=attrs.get("schema", SCHEMA_REPRESENTATION_ID),
        )


def re_is_sha256(val: str) -> bool:
    """Validate 64-char lowercase hex SHA-256 string."""
    return bool(len(val) == 64 and all(c in "0123456789abcdef" for c in val.lower()))
