"""Mathematics Domain Adapter Subsystem.

Adapts formal mathematical problems, theorems, and proof obligations to the
canonical UoW architecture and generic ProofEngine.
"""

from __future__ import annotations

from mapeogeo.domains.mathematics.adapter import MathematicsAdapter
from mapeogeo.domains.mathematics.clean_room import (
    BlindCurriculumGenerator,
    get_fresh_problem_corpus,
)
from mapeogeo.domains.mathematics.grammar_mapping import (
    FactoringAuditRecord,
    FactoringClassification,
    MathematicalGrammarFactorer,
)
from mapeogeo.domains.mathematics.obligations import MathematicalProofObligation
from mapeogeo.domains.mathematics.ontology import (
    Construction,
    EquivalenceClass,
    MathematicalObject,
    MathematicalObjectType,
    MathematicalProblem,
    Theorem,
    TheoremKind,
)

__all__ = [
    "BlindCurriculumGenerator",
    "Construction",
    "EquivalenceClass",
    "FactoringAuditRecord",
    "FactoringClassification",
    "MathematicalGrammarFactorer",
    "MathematicalObject",
    "MathematicalObjectType",
    "MathematicalProblem",
    "MathematicalProofObligation",
    "MathematicsAdapter",
    "Theorem",
    "TheoremKind",
    "get_fresh_problem_corpus",
]
