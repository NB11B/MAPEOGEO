"""Mathematical Domain Ontology and Semantic Objects.

Captures domain-specific mathematical concepts:
- Theorems, Lemmas, Corollaries, Propositions, Conjectures, Counterexamples.
- Mathematical Objects, Structures, Invariants, Equivalence Classes.
- Mathematical Constructions and Problems.

The generic kernel and proof engine remain unaware of theorem semantics;
they interact solely through domain-neutral contracts, obligations, and claims.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class TheoremKind(StrEnum):
    """Categorical kind of mathematical statement."""

    THEOREM = "THEOREM"
    LEMMA = "LEMMA"
    COROLLARY = "COROLLARY"
    PROPOSITION = "PROPOSITION"
    CONJECTURE = "CONJECTURE"
    COUNTEREXAMPLE = "COUNTEREXAMPLE"


class MathematicalObjectType(StrEnum):
    """Types of foundational mathematical objects."""

    OBJECT = "OBJECT"
    STRUCTURE = "STRUCTURE"
    SPACE = "SPACE"
    MAP = "MAP"
    ALGEBRA = "ALGEBRA"
    SYSTEM = "SYSTEM"


@dataclass(frozen=True)
class MathematicalObject:
    """Domain model of a mathematical object or space."""

    object_id: str
    name: str
    object_type: MathematicalObjectType
    domain: str
    properties: tuple[str, ...] = ()
    invariants: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Theorem:
    """Domain model of a mathematical theorem or conjecture."""

    theorem_id: str
    name: str
    statement: str
    kind: TheoremKind
    domain: str
    premises: tuple[str, ...] = ()
    conclusion: str = ""
    invariants: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def is_conjecture(self) -> bool:
        return self.kind == TheoremKind.CONJECTURE

    @property
    def is_counterexample(self) -> bool:
        return self.kind == TheoremKind.COUNTEREXAMPLE


@dataclass(frozen=True)
class Construction:
    """Formal mathematical construction step."""

    construction_id: str
    name: str
    target_object_id: str
    inputs: tuple[str, ...] = ()
    steps: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EquivalenceClass:
    """Equivalence class of isomorphic or semantically identical structures."""

    class_id: str
    domain: str
    canonical_representative_id: str
    members: tuple[str, ...] = ()
    relation_name: str = "isomorphic"
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MathematicalProblem:
    """Benchmarking mathematical problem with severity weighting."""

    problem_id: str
    title: str
    domain: str
    difficulty: float
    structural_distance: float
    novelty: float
    depth: float
    weight: float
    required_signatures: tuple[str, ...]
    base_ability_pct: float = 0.0
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        problem_id: str,
        title: str,
        domain: str,
        difficulty: float,
        structural_distance: float,
        novelty: float,
        depth: float,
        required_signatures: tuple[str, ...],
        base_ability_pct: float = 0.0,
        metadata: Mapping[str, Any] | None = None,
    ) -> MathematicalProblem:
        weight = round(difficulty * structural_distance * novelty * depth, 3)
        return cls(
            problem_id=problem_id,
            title=title,
            domain=domain,
            difficulty=difficulty,
            structural_distance=structural_distance,
            novelty=novelty,
            depth=depth,
            weight=weight,
            required_signatures=required_signatures,
            base_ability_pct=base_ability_pct,
            metadata=dict(metadata or {}),
        )
