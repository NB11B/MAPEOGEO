"""Grammar and Coordinate Algebra Layer.

Provides the literal 6-coordinate work grammar M_6 = (Delta, I, W, sigma, Pi, Gamma),
witness extensions Delta a_W, and semantic drift auditing.
"""

from __future__ import annotations

from mapeogeo.grammar.coordinates import (
    CANONICAL_COORDINATES,
    COMPOSE_OPERATOR,
    COORDINATE_DEFINITIONS,
    KERNEL_GRAMMAR_DIMENSION,
    CanonicalCoordinate,
    WitnessCertificate,
)
from mapeogeo.grammar.work_grammar import (
    SemanticDriftError,
    WorkGrammar,
)

__all__ = [
    "CANONICAL_COORDINATES",
    "COMPOSE_OPERATOR",
    "COORDINATE_DEFINITIONS",
    "KERNEL_GRAMMAR_DIMENSION",
    "CanonicalCoordinate",
    "SemanticDriftError",
    "WitnessCertificate",
    "WorkGrammar",
]
