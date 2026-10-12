#!/usr/bin/env python3
r"""
Developmental Extraction Schema.
Core Schema for Ingesting Elementary, Secondary, and Pedagogical Corpora.

Enforces the standardized 9-element developmental schema:
    grade/stage -> problem presented -> representation supplied -> representation student must invent ->
    allowed operations -> hint/scaffold -> key mathematical move -> what need not be computed -> expected new capability

Epistemic Isolation Principle:
    Raw episodes are extracted strictly according to their pedagogical and mathematical presentation.
    Mapping to the 16 methodological primitives is performed *post-hoc*, preserving independent historical fidelity.
"""

from __future__ import annotations

import enum
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple


class DevelopmentalStage(str, enum.Enum):
    GRADE_1_FIRST_DECADE = "GRADE_1_FIRST_DECADE"            # Numbers 1-10, concrete decomposition
    GRADE_1_SECOND_DECADE = "GRADE_1_SECOND_DECADE"          # Numbers 11-20, bridge across 10
    GRADE_2_HUNDRED = "GRADE_2_HUNDRED"                      # Addition/subtraction to 100, multiplication table
    GRADE_3_THOUSAND_FRACTIONS = "GRADE_3_THOUSAND_FRACTIONS"# Multidigit written algorithms, parts/fractions
    GRADE_4_MULTIDIGIT_PROPORTIONS = "GRADE_4_MULTIDIGIT_PROPORTIONS" # Multidigit numbers, proportional reasoning
    GRADE_6_7_PLANAR_GEOMETRY = "GRADE_6_7_PLANAR_GEOMETRY"  # Kiselev Planimetry: axioms, congruence, auxiliary lines
    GRADE_6_7_ELEMENTARY_ALGEBRA = "GRADE_6_7_ELEMENTARY_ALGEBRA" # Kiselev Algebra: signs, linear equations, factoring
    GRADE_8_9_QUADRATICS_SYSTEMS = "GRADE_8_9_QUADRATICS_SYSTEMS" # Quadratic equations, systems, equivalence
    GRADE_9_10_STEREOMETRY = "GRADE_9_10_STEREOMETRY"        # Spatial geometry, projections, polyhedra
    TEACHER_METHODOLOGY_DOCTRINE = "TEACHER_METHODOLOGY_DOCTRINE" # Pedagogical intent / teaching manuals (Pchelko/Lyapin)


class CorpusBatch(str, enum.Enum):
    BATCH_A_ORDINARY_PROGRESSION = "BATCH_A_ORDINARY_PROGRESSION"   # Ordinary school textbooks & teacher methodology
    BATCH_B_OLYMPIAD_ENRICHMENT = "BATCH_B_OLYMPIAD_ENRICHMENT"     # Circles, competitions, non-standard problem books
    BATCH_C_KOLMOGOROV_REFORM = "BATCH_C_KOLMOGOROV_REFORM"         # Post-1965 structural modernist reform


@dataclass
class DevelopmentalEpisode:
    """Standardized 9-element developmental extraction episode."""

    episode_id: str
    source_id: str
    source_citation: str
    corpus_batch: CorpusBatch
    grade_stage: DevelopmentalStage

    # 1. Problem presented
    problem_presented: str

    # 2. Representation supplied
    representation_supplied: str

    # 3. Representation student must invent
    representation_invented: str

    # 4. Allowed operations
    allowed_operations: List[str]

    # 5. Hint / scaffold supplied
    hint_scaffold: str

    # 6. Key mathematical move
    key_mathematical_move: str

    # 7. What need not be computed (Negative Information)
    what_need_not_be_computed: str

    # 8. Expected new capability
    expected_new_capability: str

    # 9. Pedagogical intent / teacher doctrine behind exercise
    pedagogical_intent: str

    # Optional metadata
    page_reference: Optional[str] = None
    original_russian_text: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["corpus_batch"] = self.corpus_batch.value
        d["grade_stage"] = self.grade_stage.value
        return d


@dataclass
class PrimitiveMappingRecord:
    """Post-extraction mapping of an episode onto the 16 methodological primitives."""

    episode_id: str
    primitive_symbols: List[str]  # e.g., ["Rs", "Ax", "N"]
    mapping_breakdown: Dict[str, str]  # Primitive -> specific instantiation in the episode
    structural_concordance: float  # 0.0 to 1.0 confidence/fit score
    epistemic_notes: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
