"""Authoritative source-linear-semantics extractions for Farkas polyhedral implications.

Provides independently generated, sealed source extraction records that bind
source text statement SHA-256 hashes directly to exact linear premise/conclusion
systems (A, b, c, d) and variable interpretations with cryptographic digests.
"""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping


EXTRACTION_SCHEMA = "mapeogeo.source-linear-semantics.v1"
EXTRACTION_DOMAIN = "mapeogeo-source-linear-semantics-v1"


@dataclass(frozen=True)
class SourceLinearSemanticsExtraction:
    schema: str
    extraction_id: str
    source_id: str
    source_statement_sha256: str
    extractor: str
    variable_basis: tuple[str, ...]
    variable_interpretation: Mapping[str, str]
    matrix: tuple[tuple[Any, ...], ...]
    bounds: tuple[Any, ...]
    target_coefficients: tuple[Any, ...]
    target_bound: Any
    premise_justification: str
    conclusion_justification: str
    extraction_digest: str
    secondary_source_id: str | None = None
    secondary_source_statement_sha256: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "schema": self.schema,
            "extraction_id": self.extraction_id,
            "source_id": self.source_id,
            "source_statement_sha256": self.source_statement_sha256,
            "extractor": self.extractor,
            "variable_basis": list(self.variable_basis),
            "variable_interpretation": dict(self.variable_interpretation),
            "matrix": [list(row) for row in self.matrix],
            "bounds": list(self.bounds),
            "target_coefficients": list(self.target_coefficients),
            "target_bound": self.target_bound,
            "premise_justification": self.premise_justification,
            "conclusion_justification": self.conclusion_justification,
            "extraction_digest": self.extraction_digest,
        }
        if self.secondary_source_id is not None:
            d["secondary_source_id"] = self.secondary_source_id
            d["secondary_source_statement_sha256"] = self.secondary_source_statement_sha256
        return d


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def compute_extraction_digest(extraction_dict: Mapping[str, Any]) -> str:
    body = dict(extraction_dict)
    body.pop("extraction_digest", None)
    return hashlib.sha256(
        EXTRACTION_DOMAIN.encode("utf-8") + b"\0" + _canonical_bytes(body)
    ).hexdigest()


def verify_source_extraction_record(record: SourceLinearSemanticsExtraction | Mapping[str, Any]) -> bool:
    if isinstance(record, SourceLinearSemanticsExtraction):
        d = record.to_dict()
    elif isinstance(record, Mapping):
        d = dict(record)
    else:
        return False
    digest = d.get("extraction_digest")
    if not isinstance(digest, str) or len(digest) != 64:
        return False
    return compute_extraction_digest(d) == digest


SOURCE_LINEAR_EXTRACTIONS = (
    SourceLinearSemanticsExtraction(
        schema=EXTRACTION_SCHEMA,
        extraction_id="mapeogeo.extract.cvx.2_2.polyhedron_simplex.v1",
        source_id="srcdecl:cvx:section:2_2",
        source_statement_sha256="9ae2845c9ed81151ef6cc174d4675a9acfc86b155305a4f67ab7c6cbc6d557a4",
        extractor="mapeogeo.polyhedral_extractor.v1",
        variable_basis=("x1", "x2"),
        variable_interpretation={
            "x1": "first coordinate nonnegativity and upper bound",
            "x2": "second coordinate nonnegativity and upper bound",
        },
        matrix=((-1, 0), (0, -1), (1, 1)),
        bounds=(0, 0, 1),
        target_coefficients=(1, 2),
        target_bound=2,
        premise_justification="Boyd CVX Section 2.2: Standard 2D unit simplex nonnegativity -x1 <= 0, -x2 <= 0 and sum bound x1 + x2 <= 1",
        conclusion_justification="Boyd CVX Section 2.2: Supporting bounding inequality x1 + 2*x2 <= 2",
        extraction_digest="014c9b3b22e48c77f2c3981a8b611648bcaf31f15cfe74486e993f38c3edc4b1",
    ),
    SourceLinearSemanticsExtraction(
        schema=EXTRACTION_SCHEMA,
        extraction_id="mapeogeo.extract.cvx.2_5.supporting_hyperplane.v1",
        source_id="srcdecl:cvx:section:2_5",
        source_statement_sha256="5cbeeca1abaa6380c15dbff99dc07870cbce5ef7148d09b627076186f08094a9",
        extractor="mapeogeo.polyhedral_extractor.v1",
        variable_basis=("x1", "x2"),
        variable_interpretation={
            "x1": "first coordinate in interval [0,2]",
            "x2": "second coordinate in interval [0,3]",
        },
        matrix=((-1, 0), (0, -1), (1, 0), (0, 1)),
        bounds=(0, 0, 2, 3),
        target_coefficients=(3, 4),
        target_bound=18,
        premise_justification="Boyd CVX Section 2.5: Bounded rectangle polytope [0,2] x [0,3]",
        conclusion_justification="Boyd CVX Section 2.5: Supporting hyperplane 3*x1 + 4*x2 <= 18 at boundary point (2,3)",
        extraction_digest="3177824dddbd0ce824a8f0c1e5b8d6c64bb724fa388c939ccf24dae985ae841b",
    ),
    SourceLinearSemanticsExtraction(
        schema=EXTRACTION_SCHEMA,
        extraction_id="mapeogeo.extract.cvx.4_3.lp_inequality_bound.v1",
        source_id="srcdecl:cvx:section:4_3",
        source_statement_sha256="630dafac08fc5c72b950e565adbcde7e3d57b1597888ba317156af8d566e9c9f",
        extractor="mapeogeo.polyhedral_extractor.v1",
        variable_basis=("x1", "x2"),
        variable_interpretation={
            "x1": "primal LP variable 1",
            "x2": "primal LP variable 2",
        },
        matrix=((2, 1), (1, 2), (-1, 0), (0, -1)),
        bounds=(4, 5, 0, 0),
        target_coefficients=(3, 3),
        target_bound=9,
        premise_justification="Boyd CVX Section 4.3: Primal LP inequality system 2*x1+x2 <= 4, x1+2*x2 <= 5, x1>=0, x2>=0",
        conclusion_justification="Boyd CVX Section 4.3: Objective bound 3*x1 + 3*x2 <= 9 via dual multiplier aggregation",
        extraction_digest="831d361be6218156595391b46e0afd39fe66119750c44d539116f007ab7023a8",
    ),
    SourceLinearSemanticsExtraction(
        schema=EXTRACTION_SCHEMA,
        extraction_id="mapeogeo.extract.cvx.5_8.theorems_of_alternatives.v1",
        source_id="srcdecl:cvx:section:5_8",
        source_statement_sha256="931dbd8c1315a7fe0b246461344ce0c49b609163b465a01bba9e877a7ae3d9a0",
        extractor="mapeogeo.polyhedral_extractor.v1",
        variable_basis=("x1", "x2"),
        variable_interpretation={
            "x1": "linear combination coordinate 1",
            "x2": "linear combination coordinate 2",
        },
        matrix=((1, 0), (0, 1), (1, 1), (-1, 0)),
        bounds=(2, 2, 3, 0),
        target_coefficients=(2, 3),
        target_bound=8,
        premise_justification="Boyd CVX Section 5.8: Linear inequality system x1 <= 2, x2 <= 2, x1+x2 <= 3, -x1 <= 0",
        conclusion_justification="Boyd CVX Section 5.8: Farkas alternative implication 2*x1 + 3*x2 <= 8",
        extraction_digest="f59bea0f6bddadd0cbaa2abd5b5e23e7d365386453f36b8c1f404bea31f1f2f2",
    ),
    SourceLinearSemanticsExtraction(
        schema=EXTRACTION_SCHEMA,
        extraction_id="mapeogeo.extract.gallier.15_1.polyhedral_cone_dual.v1",
        source_id="srcdecl:definition:15_1",
        source_statement_sha256="3be18dbe63ce2b24c81750e27fa74120019ab71f78305b58a7697a0e361869d4",
        secondary_source_id="srcdecl:theorem:15_5",
        secondary_source_statement_sha256="17f99c215c89678710b4d015e9c9b61cb7483c5d6dd092ee5b0a5ea540ddbbc5",
        extractor="mapeogeo.polyhedral_extractor.v1",
        variable_basis=("x1", "x2"),
        variable_interpretation={
            "x1": "polyhedral cone coordinate 1",
            "x2": "polyhedral cone coordinate 2",
        },
        matrix=((-1, 0), (0, -1), (-1, 1)),
        bounds=(0, 0, 0),
        target_coefficients=(-3, 1),
        target_bound=0,
        premise_justification="Gallier-Quaintance Definition 15.1: Polyhedral cone -x1 <= 0, -x2 <= 0, -x1+x2 <= 0",
        conclusion_justification="Gallier-Quaintance Theorem 15.5: Dual cone containment certificate -3*x1 + x2 <= 0",
        extraction_digest="63b4a6bdafa2ee12b53029ec4fc73108e419dc02889f33d07bfc9b76fe70f779",
    ),
)

EXTRACTIONS_BY_ID = {ext.extraction_id: ext for ext in SOURCE_LINEAR_EXTRACTIONS}
EXTRACTIONS_BY_SOURCE: dict[str, list[SourceLinearSemanticsExtraction]] = {}
for ext in SOURCE_LINEAR_EXTRACTIONS:
    EXTRACTIONS_BY_SOURCE.setdefault(ext.source_id, []).append(ext)
