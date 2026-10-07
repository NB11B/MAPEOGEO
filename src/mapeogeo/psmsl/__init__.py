"""PSMSL Operator Algebra and Representation Substrate.

Provides domain-neutral linear transformation operators, operator word composition,
state projection, inverse reconstruction, and trajectory observability.
"""

from __future__ import annotations

from mapeogeo.psmsl.algebra import (
    InformationSemantics,
    OrderingSemantics,
    analyze_information,
    analyze_ordering,
    commutator,
    discover_linear_operator_basis,
    eye,
    frobenius_norm,
    matmul,
    matsub,
    rank,
    rref_solve,
)
from mapeogeo.psmsl.latent import LatentGenerator, ObservableSignature, Observation
from mapeogeo.psmsl.operator import (
    OperatorWord,
    RepresentationTransform,
    TransformationOperator,
)
from mapeogeo.psmsl.projection import (
    InverseProjection,
    InverseResult,
    StateProjection,
)
from mapeogeo.psmsl.serialization import (
    deserialize_latent_generator,
    deserialize_observable_signature,
    deserialize_observation,
    deserialize_operator,
    deserialize_operator_word,
    serialize_latent_generator,
    serialize_observable_signature,
    serialize_observation,
    serialize_operator,
    serialize_operator_word,
)

__all__ = [
    "InformationSemantics",
    "InverseProjection",
    "InverseResult",
    "LatentGenerator",
    "ObservableSignature",
    "Observation",
    "OperatorWord",
    "OrderingSemantics",
    "RepresentationTransform",
    "StateProjection",
    "TransformationOperator",
    "analyze_information",
    "analyze_ordering",
    "commutator",
    "deserialize_latent_generator",
    "deserialize_observable_signature",
    "deserialize_observation",
    "deserialize_operator",
    "deserialize_operator_word",
    "discover_linear_operator_basis",
    "eye",
    "frobenius_norm",
    "matmul",
    "matsub",
    "rank",
    "rref_solve",
    "serialize_latent_generator",
    "serialize_observable_signature",
    "serialize_observation",
    "serialize_operator",
    "serialize_operator_word",
]
