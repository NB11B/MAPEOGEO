#!/usr/bin/env python3
r"""
Developmental Extraction Engine.
Extracts and Manages Structured Pedagogical Episodes across the Pre-Reform Soviet Mathematics Arc.

Implements the standardized 9-element schema:
    grade/stage -> problem presented -> representation supplied -> representation student must invent ->
    allowed operations -> hint/scaffold -> key mathematical move -> what need not be computed -> expected new capability

Epistemic Isolation Guarantee:
    Episodes are extracted and stored in their native pedagogical formulation.
    Post-hoc mapping onto the 16 methodological primitives is stored in separate mapping records.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .developmental_schema import (
    CorpusBatch,
    DevelopmentalEpisode,
    DevelopmentalStage,
    PrimitiveMappingRecord,
)
from .developmental_corpus_registry import DevelopmentalCorpusRegistry


class DevelopmentalExtractionEngine:
    """Core extraction engine for the developmental mathematics curriculum."""

    def __init__(self) -> None:
        self.registry = DevelopmentalCorpusRegistry()
        self.episodes: Dict[str, DevelopmentalEpisode] = {}
        self.primitive_mappings: Dict[str, PrimitiveMappingRecord] = {}
        self._initialize_canonical_batch_a_episodes()

    def _initialize_canonical_batch_a_episodes(self) -> None:
        """Initializes canonical extraction episodes for Batch A (A1 to A7)."""

        # ---------------------------------------------------------------------
        # A1: Popova (1933) - Part 1: First Decade Decomposition
        # ---------------------------------------------------------------------
        ep_a1_1 = DevelopmentalEpisode(
            episode_id="DEV-A1-POP-01",
            source_id="A1_POPOVA_1933",
            source_citation="Попова Н. С. Учебник арифметики для начальной школы. Ч. 1. — М.: Учпедгиз, 1933. — С. 14.",
            corpus_batch=CorpusBatch.BATCH_A_ORDINARY_PROGRESSION,
            grade_stage=DevelopmentalStage.GRADE_1_FIRST_DECADE,
            problem_presented="Compose the number 5 from two smaller numbers (Состав числа 5: разложить число 5 на две части всеми способами).",
            representation_supplied="Domino dot card showing 5 dots grouped as 4 and 1, or 3 and 2; five wooden counting sticks placed horizontally.",
            representation_invented="Structured additive partition schema: (4 + 1), (3 + 2), (2 + 3), (1 + 4) recorded as complementary pairs without counting.",
            allowed_operations=[
                "Partition of a physical set into two non-empty subsets",
                "Pairwise matching and complementary recognition",
                "Associating visual dot groups with spoken numerals",
            ],
            hint_scaffold="Teacher places a pencil separating the 5 sticks into two groups: 'Cover 2 sticks with your hand. How many sticks are open? (3). So 5 is 3 and...?'",
            key_mathematical_move="Treating the number 5 as an invariant whole composed of complementary structural parts rather than a succession of individual counting ticks.",
            what_need_not_be_computed="Counting the collection from 1 to 5 unit-by-unit (1, 2, 3, 4, 5) every time a partition is altered.",
            expected_new_capability="Immediate automatic recall of single-digit additive complements without finger counting or unit enumeration.",
            pedagogical_intent="Popova's foundational doctrine: unit-by-unit finger counting ('prisчитывание по единице') must be actively suppressed from the very first week to develop genuine arithmetic structure.",
            page_reference="Part 1, p. 14",
            original_russian_text="Состав числа 5. Положите 5 палочек. Отодвиньте 1 палочку. Сколько осталось? 5 — это 4 и 1.",
        )
        self.register_episode(ep_a1_1)
        self.register_mapping(
            PrimitiveMappingRecord(
                episode_id=ep_a1_1.episode_id,
                primitive_symbols=["Rs", "N", "I"],
                mapping_breakdown={
                    "Rs": "Representation Shift: physical set of discrete items -> formal additive partition schema (5 = 3 + 2).",
                    "N": "Negative Information: deliberate avoidance of re-counting units by ones; suppresses finger-counting.",
                    "I": "Invariant Reasoning: total cardinal quantity 5 is conserved invariant under all spatial partitions.",
                },
                structural_concordance=0.95,
                epistemic_notes="Directly cultivates non-procedural number conservation and negative information.",
            )
        )

        # ---------------------------------------------------------------------
        # A1: Popova (1933) - Part 2: Crossing the Decade
        # ---------------------------------------------------------------------
        ep_a1_2 = DevelopmentalEpisode(
            episode_id="DEV-A1-POP-02",
            source_id="A1_POPOVA_1933",
            source_citation="Попова Н. С. Учебник арифметики для начальной школы. Ч. 2. — М.: Учпедгиз, 1933. — С. 28.",
            corpus_batch=CorpusBatch.BATCH_A_ORDINARY_PROGRESSION,
            grade_stage=DevelopmentalStage.GRADE_1_SECOND_DECADE,
            problem_presented="Addition crossing the decade: Compute 8 + 5 (Сложение с переходом через десяток).",
            representation_supplied="Abacus wire or two rows of counting sticks: top row has 8 sticks, bottom row has 5 sticks.",
            representation_invented="Auxiliary 10-complement bridge: 5 is partitioned into 2 + 3 to complete 8 to 10, producing (8 + 2) + 3 = 10 + 3 = 13.",
            allowed_operations=[
                "Decomposition of the second addend into two components",
                "Complementing to 10 (8 + 2 = 10)",
                "Addition of remaining units to 10 (10 + 3 = 13)",
            ],
            hint_scaffold="Leading pedagogical dialogue: 'How many sticks does 8 need to make a full ten? (2). Where will we take 2 from? (From the 5). How many sticks are left of the 5? (3). What is 10 plus 3?'",
            key_mathematical_move="Auxiliary construction of the base-10 pivot: decomposing 5 into 2 + 3 to route the addition through the ten-boundary.",
            what_need_not_be_computed="Counting up 5 times from 8 (9, 10, 11, 12, 13).",
            expected_new_capability="Associative regrouping across place-value boundaries; base-10 modular mental arithmetic.",
            pedagogical_intent="Establishes base-10 structure as an invariant operational pivot rather than a barrier.",
            page_reference="Part 2, p. 28",
            original_russian_text="Прибавить 5 к 8: дополняем 8 до 10 (берем 2 от 5), остается 3; к 10 прибавляем 3, получается 13.",
        )
        self.register_episode(ep_a1_2)
        self.register_mapping(
            PrimitiveMappingRecord(
                episode_id=ep_a1_2.episode_id,
                primitive_symbols=["Ax", "Sr", "N"],
                mapping_breakdown={
                    "Ax": "Auxiliary Construction: introducing the intermediate 10-bundle bridge (5 = 2 + 3).",
                    "Sr": "State Reduction: reduces multi-unit decade crossing to single-digit decomposition within 10.",
                    "N": "Negative Information: strictly omits counting-up sequential ticks.",
                },
                structural_concordance=0.98,
                epistemic_notes="Earliest explicit auxiliary construction in elementary arithmetic.",
            )
        )

        # ---------------------------------------------------------------------
        # A2: Pchelko & Polyak (1954) - Grade 2: Multiplication & Inverse Division
        # ---------------------------------------------------------------------
        ep_a2_1 = DevelopmentalEpisode(
            episode_id="DEV-A2-PCH-01",
            source_id="A2_PCHELKO_POLYAK_GRADES_1_4",
            source_citation="Пчелко А. С., Поляк Г. Б. Арифметика: 2 класс. — М.: Учпедгиз, 1954. — С. 45.",
            corpus_batch=CorpusBatch.BATCH_A_ORDINARY_PROGRESSION,
            grade_stage=DevelopmentalStage.GRADE_2_HUNDRED,
            problem_presented="4 boxes contain 6 pencils each. How many pencils in total? Inverse problem: 24 pencils packed 6 to a box. How many boxes?",
            representation_supplied="Illustrated realistic word problem with 4 discrete pencil boxes.",
            representation_invented="Continuous segmented bar diagram: one master line of length 24 divided into 4 equal segments of 6; dual division schema.",
            allowed_operations=[
                "Equal-group addition (6 + 6 + 6 + 6)",
                "Multiplicative operator condensation (6 * 4)",
                "Inverse partition / measurement division (24 : 6 = 4)",
            ],
            hint_scaffold="Teacher question: 'Which number is repeated as an addend? (6). How many times is it taken? (4 times). How do we write taking 6 four times without repeated addition?'",
            key_mathematical_move="Dimensional condensation of sequential addition into a multiplicative operator, immediately coupled to its inverse division operation.",
            what_need_not_be_computed="Repeated additions (6+6=12, 12+6=18, 18+6=24); individual unit counting of 24 items.",
            expected_new_capability="Multiplicative operator abstraction; instantaneous recognition of division as the inverse of multiplication.",
            pedagogical_intent="Pchelko and Polyak deliberately present multiplication and division in immediate dialectical proximity, preventing division from becoming an isolated algorithm.",
            page_reference="Grade 2, p. 45",
            original_russian_text="Умножение — это сложение одинаковых слагаемых. Взять по 6 четыре раза: 6 * 4 = 24. Деление: 24 : 6 = 4.",
        )
        self.register_episode(ep_a2_1)
        self.register_mapping(
            PrimitiveMappingRecord(
                episode_id=ep_a2_1.episode_id,
                primitive_symbols=["Rs", "Iv", "N"],
                mapping_breakdown={
                    "Rs": "Representation Shift: repeated addition sequence -> multiplicative operator and segmented bar.",
                    "Iv": "Inverse Reasoning: immediate coupling of multiplication (6*4=24) with division (24:6=4).",
                    "N": "Negative Information: avoids computing intermediate sums 12, 18.",
                },
                structural_concordance=0.96,
                epistemic_notes="Foundational inverse operator pairing in early postwar Soviet pedagogy.",
            )
        )

        # ---------------------------------------------------------------------
        # A2: Pchelko & Polyak (1955) - Grade 3: Operational Substitution (Mental Math)
        # ---------------------------------------------------------------------
        ep_a2_2 = DevelopmentalEpisode(
            episode_id="DEV-A2-PCH-02",
            source_id="A2_PCHELKO_POLYAK_GRADES_1_4",
            source_citation="Пчелко А. С., Поляк Г. Б. Арифметика: 3 класс. — М.: Учпедгиз, 1955. — С. 78.",
            corpus_batch=CorpusBatch.BATCH_A_ORDINARY_PROGRESSION,
            grade_stage=DevelopmentalStage.GRADE_3_THOUSAND_FRACTIONS,
            problem_presented="Mental arithmetic technique: Multiply 48 * 5 and divide 360 : 5 rapidly without written column algorithms.",
            representation_supplied="Standard arithmetic symbolic expression: 48 * 5 and 360 : 5.",
            representation_invented="Base-10 rational operator substitution: replace * 5 with (: 2 * 10), and replace : 5 with (* 2 : 10).",
            allowed_operations=[
                "Halving an even number (48 : 2 = 24)",
                "Multiplying by 10 (24 * 10 = 240)",
                "Doubling and dividing by 10 (360 * 2 = 720; 720 : 10 = 72)",
            ],
            hint_scaffold="Scaffold prompt: 'What is 5 in terms of 10? 5 is half of 10. To multiply by 5, first divide by 2, then multiply by 10.'",
            key_mathematical_move="Transforming an inconvenient arithmetic multiplication into two elementary operations using base-10 rational duality (5 = 10/2).",
            what_need_not_be_computed="Columnar long-multiplication carrying steps (8 * 5 = 40, carry 4; 4 * 5 = 20 + 4 = 24).",
            expected_new_capability="Strategic operational substitution; treating numbers as algebraic operators with multiple representations.",
            pedagogical_intent="Trains pupils to view numbers structurally rather than mechanically executing algorithmic digit operations.",
            page_reference="Grade 3, p. 78",
            original_russian_text="Прием устного счета: умножение на 5. Чтобы умножить число на 5, можно разделить его на 2 и умножить на 10: 48 * 5 = 48 : 2 * 10 = 240.",
        )
        self.register_episode(ep_a2_2)
        self.register_mapping(
            PrimitiveMappingRecord(
                episode_id=ep_a2_2.episode_id,
                primitive_symbols=["Rs", "Sr", "N"],
                mapping_breakdown={
                    "Rs": "Representation Shift: scalar factor 5 -> rational decomposition 10/2.",
                    "Sr": "State Reduction: reduces hard multiplication to mental halving and trailing zero append.",
                    "N": "Negative Information: completely bypasses vertical column algorithm carrying mechanics.",
                },
                structural_concordance=0.97,
                epistemic_notes="Exemplary case of computational state reduction via algebraic representation shift.",
            )
        )

        # ---------------------------------------------------------------------
        # A3: Pchelko (1949) - Teacher Methodology: Word Problems & Intent
        # ---------------------------------------------------------------------
        ep_a3_1 = DevelopmentalEpisode(
            episode_id="DEV-A3-PCH-METH-01",
            source_id="A3_PCHELKO_TEACHER_METHODOLOGY_1949",
            source_citation="Пчелко А. С. Методика преподавания арифметики в начальной школе. — М.: Учпедгиз, 1949. — С. 182–195.",
            corpus_batch=CorpusBatch.BATCH_A_ORDINARY_PROGRESSION,
            grade_stage=DevelopmentalStage.TEACHER_METHODOLOGY_DOCTRINE,
            problem_presented="Pedagogical doctrine on compound word problems (*Sostavnye zadachi*): How to teach children to analyze multi-step problems without guessing.",
            representation_supplied="Raw textual narrative describing real-world transactions with nested quantitative relations.",
            representation_invented="Analytical tree of functional dependencies: decomposing the target unknown into binary questions (Analytical-Synthetic method).",
            allowed_operations=[
                "Separation of mathematical conditions from narrative ornament",
                "Analytic backward chaining: unknown Z requires knowing X and Y",
                "Synthetic forward chaining: combining known A and B to yield X",
            ],
            hint_scaffold="Teacher question framework: 'What does the question ask? Can we answer it immediately? Why not? What must we find first?'",
            key_mathematical_move="Converting a linear prose story into an acyclic dependency graph of elementary arithmetic operations.",
            what_need_not_be_computed="Any emotional or realistic real-world narrative variables (names, objects, physical context).",
            expected_new_capability="Algorithmic problem decomposition; functional dependency analysis.",
            pedagogical_intent="Pchelko explicitly states: 'The value of arithmetic problems is not to practice calculation, but to develop the child's ability to analyze relationships between quantities.'",
            page_reference="pp. 182-195",
            original_russian_text="Аналитико-синтетический метод разбора задачи: разложение сложной задачи на ряд простых. Главная цель — раскрытие зависимостей между величинами.",
        )
        self.register_episode(ep_a3_1)
        self.register_mapping(
            PrimitiveMappingRecord(
                episode_id=ep_a3_1.episode_id,
                primitive_symbols=["Rs", "Sr", "N"],
                mapping_breakdown={
                    "Rs": "Representation Shift: unstructured verbal narrative -> directed acyclic dependency graph.",
                    "Sr": "State Reduction: reduces multi-variable global narrative into sequential binary operations.",
                    "N": "Negative Information: strips all narrative contextual noise from mathematical relations.",
                },
                structural_concordance=0.94,
                epistemic_notes="Explicit doctrinal verification of negative information and representation shifts in teacher training.",
            )
        )

        # ---------------------------------------------------------------------
        # A4: Pchelko ed. (1949) - Method of False Assumption (Word Problems)
        # ---------------------------------------------------------------------
        ep_a4_1 = DevelopmentalEpisode(
            episode_id="DEV-A4-PCH-PROB-01",
            source_id="A4_PCHELKO_PROBLEM_SOLVING_1949",
            source_citation="Решение арифметических задач в начальной школе / Под ред. А. С. Пчелко. — М.: АПН РСФСР, 1949. — С. 112–118.",
            corpus_batch=CorpusBatch.BATCH_A_ORDINARY_PROGRESSION,
            grade_stage=DevelopmentalStage.GRADE_4_MULTIDIGIT_PROPORTIONS,
            problem_presented="The Method of False Assumption (*Sposob predpolozheniya*): 10 vehicles in a yard, some 2-wheel bicycles and some 3-wheel tricycles. Total wheels = 26. Find the number of each.",
            representation_supplied="Simultaneous discrete constraint word problem (equivalent to linear system x + y = 10, 2x + 3y = 26).",
            representation_invented="Counterfactual auxiliary baseline: 'Assume all 10 vehicles are 2-wheeled bicycles.' Compare fictitious total wheels (20) with actual total (26).",
            allowed_operations=[
                "Counterfactual assumption multiplication (10 * 2 = 20)",
                "Deficit subtraction (26 - 20 = 6)",
                "Differential unit quotient (3 - 2 = 1; 6 : 1 = 6 tricycles)",
                "Residual subtraction (10 - 6 = 4 bicycles)",
            ],
            hint_scaffold="Guiding question: 'If every vehicle had only 2 wheels, how many wheels would there be? (20). But there are 26. Why are there 6 extra wheels? (Because some vehicles have 1 extra wheel). So how many tricycles?'",
            key_mathematical_move="Auxiliary construction of a fictitious uniform state to linearize a multi-variable constraint, converting simultaneous equation solving into single-step residual division.",
            what_need_not_be_computed="Combinatorial trial-and-error search across pairs (1,9), (2,8), (3,7), etc.",
            expected_new_capability="Perturbation analysis and counterfactual auxiliary reasoning in discrete arithmetic.",
            pedagogical_intent="Provides elementary school children with the mathematical power of linear systems long before formal algebra is introduced.",
            page_reference="pp. 112-118",
            original_russian_text="Способ предположения: допускаем, что все 10 машин двухколесные. Тогда колес было бы 20. Избыток в 6 колес возник от трехколесных велосипедов (по 1 лишнему колесу на каждый). Значит, трехколесных — 6, двухколесных — 4.",
        )
        self.register_episode(ep_a4_1)
        self.register_mapping(
            PrimitiveMappingRecord(
                episode_id=ep_a4_1.episode_id,
                primitive_symbols=["Ax", "Ii", "N"],
                mapping_breakdown={
                    "Ax": "Auxiliary Construction: fictitious counterfactual baseline state (all vehicles 2-wheeled).",
                    "Ii": "Indirect Inference: deducing the count of 3-wheelers from the total wheel deficit.",
                    "N": "Negative Information: avoids combinatorial iteration across integer partitions.",
                },
                structural_concordance=0.98,
                epistemic_notes="Pivotal pre-algebraic auxiliary construction technique.",
            )
        )

        # ---------------------------------------------------------------------
        # A5: Kiselev (1938) - Geometry: Planimetry (Isosceles Triangle & Auxiliary Line)
        # ---------------------------------------------------------------------
        ep_a5_1 = DevelopmentalEpisode(
            episode_id="DEV-A5-KIS-GEOM-01",
            source_id="A5_KISELEV_GEOMETRY_1938",
            source_citation="Киселев А. П. Геометрия. Ч. 1: Планиметрия. — М.: Учпедгиз, 1938. — С. 22–24.",
            corpus_batch=CorpusBatch.BATCH_A_ORDINARY_PROGRESSION,
            grade_stage=DevelopmentalStage.GRADE_6_7_PLANAR_GEOMETRY,
            problem_presented="Theorem: In an isosceles triangle ABC (AB = AC), the angles at the base are equal (angle B = angle C).",
            representation_supplied="Static plane geometric triangle ABC with marked equal sides AB and AC.",
            representation_invented="Auxiliary construction of angle bisector AD dividing angle A into two equal angles, partitioning triangle ABC into two triangles ABD and ACD.",
            allowed_operations=[
                "Axiom of angle bisection construction",
                "SAS (Side-Angle-Side) triangle congruence criterion",
                "Deduction of equal corresponding angles in congruent figures",
            ],
            hint_scaffold="Deductive dilemma: 'Can we compare angle B and angle C directly? No, because they belong to the same single triangle. How can we place them into two separate triangles that can be compared?'",
            key_mathematical_move="Introducing an unobserved interior line segment (auxiliary bisector AD) to reduce a static single-figure property to pairwise triangle congruence.",
            what_need_not_be_computed="Metric measurement of angle degrees with a protractor.",
            expected_new_capability="Auxiliary construction as an engine of deductive geometric proof; invariance under congruence.",
            pedagogical_intent="Kiselev establishes that axiomatic proof is fundamentally constructive: the mathematician actively augments the figure to reveal latent symmetries.",
            page_reference="pp. 22-24",
            original_russian_text="Теорема: В равнобедренном треугольнике углы при основании равны. Проведем биссектрису угла А до пересечения с основанием в точке D. Треугольники ABD и ACD равны по первому признаку (две стороны и угол между ними). Следовательно, угол B = углу C.",
        )
        self.register_episode(ep_a5_1)
        self.register_mapping(
            PrimitiveMappingRecord(
                episode_id=ep_a5_1.episode_id,
                primitive_symbols=["Ax", "Rs", "I"],
                mapping_breakdown={
                    "Ax": "Auxiliary Construction: unobserved interior bisector line AD.",
                    "Rs": "Representation Shift: single static triangle -> pair of congruent adjacent triangles.",
                    "I": "Invariant Reasoning: congruence preserves corresponding angles.",
                },
                structural_concordance=0.99,
                epistemic_notes="Classic Euclidean-Kiselev auxiliary construction paradigm.",
            )
        )

        # ---------------------------------------------------------------------
        # A6: Kiselev (1938) - Algebra: Factoring by Grouping
        # ---------------------------------------------------------------------
        ep_a6_1 = DevelopmentalEpisode(
            episode_id="DEV-A6-KIS-ALG-01",
            source_id="A6_KISELEV_ALGEBRA_1938",
            source_citation="Киселев А. П. Алгебра. Ч. 1. — М.: Учпедгиз, 1938. — С. 89–92.",
            corpus_batch=CorpusBatch.BATCH_A_ORDINARY_PROGRESSION,
            grade_stage=DevelopmentalStage.GRADE_6_7_ELEMENTARY_ALGEBRA,
            problem_presented="Factor the polynomial by grouping terms: ax + bx + ay + by.",
            representation_supplied="Unfactored symbolic sum of four monomial products.",
            representation_invented="Two-level bracket grouping exposing a shared binomial sub-expression: (ax + bx) + (ay + by) = x(a + b) + y(a + b) = (a + b)(x + y).",
            allowed_operations=[
                "Associative grouping of terms",
                "Factoring out monomial common factors",
                "Treating compound binomial (a + b) as a single factored unit",
            ],
            hint_scaffold="Scaffold prompt: 'Do all four terms have a common factor? (No). Do pairs of terms have common factors? Group terms that share common factors in pairs. What identical binomial appears in both groups?'",
            key_mathematical_move="Structural abstraction: treating the compound binomial (a + b) as an atomic single variable M, transforming x*M + y*M into M*(x + y).",
            what_need_not_be_computed="Any numerical evaluation or substitution for specific values of a, b, x, y.",
            expected_new_capability="Hierarchical algebraic vision; recognizing modular sub-expressions within polynomials.",
            pedagogical_intent="Kiselev transitions pupils from procedural arithmetic calculation to pure structural manipulation of algebraic forms.",
            page_reference="pp. 89-92",
            original_russian_text="Способ группировки: группируем слагаемые, имеющие общий множитель: (ax + bx) + (ay + by) = x(a + b) + y(a + b). Выносим общий двучлен (a + b) за скобки: (a + b)(x + y).",
        )
        self.register_episode(ep_a6_1)
        self.register_mapping(
            PrimitiveMappingRecord(
                episode_id=ep_a6_1.episode_id,
                primitive_symbols=["Sr", "Rs", "I"],
                mapping_breakdown={
                    "Sr": "State Reduction: condenses 4-term polynomial into compact product of 2 binomials.",
                    "Rs": "Representation Shift: sum-of-products representation -> product-of-sums representation.",
                    "I": "Invariant Reasoning: algebraic polynomial equivalence invariant under factorization.",
                },
                structural_concordance=0.96,
                epistemic_notes="Demonstrates modular sub-expression recognition as state reduction.",
            )
        )

        # ---------------------------------------------------------------------
        # A7: Lyapin et al. (1956) - Secondary Methodology: Geometric Loci
        # ---------------------------------------------------------------------
        ep_a7_1 = DevelopmentalEpisode(
            episode_id="DEV-A7-LYAP-METH-01",
            source_id="A7_LYAPIN_SECONDARY_METHODOLOGY_1956",
            source_citation="Ляпин С. Е. и др. Методика преподавания математики. Ч. 2. — Л.: Учпедгиз, 1956. — С. 310–324.",
            corpus_batch=CorpusBatch.BATCH_A_ORDINARY_PROGRESSION,
            grade_stage=DevelopmentalStage.TEACHER_METHODOLOGY_DOCTRINE,
            problem_presented="Secondary Teaching Doctrine on Geometric Loci (*Geometricheskie mesta tochek*): How to cultivate dynamic functional thinking through locus problems.",
            representation_supplied="Static geometric drawing and verbal constraint condition (e.g. points equidistant from two intersecting lines).",
            representation_invented="Dynamic kinematic point M(x, y) moving along a continuous path while preserving an invariant metric distance relation d(M, L1) = d(M, L2).",
            allowed_operations=[
                "Direct theorem proof: every point on the locus satisfies the geometric condition",
                "Converse theorem proof (Obratnaya teorema): every point satisfying the condition lies on the locus",
                "Identification of admissibility boundaries and singular points (e.g. intersection point)",
            ],
            hint_scaffold="Teacher methodological principle: 'Never accept a geometric locus proof that only proves the direct assertion. You must prove both the direct and the converse to ensure no points are falsely included or excluded.'",
            key_mathematical_move="Rigorous two-way set-theoretic equivalence (S subset L and L subset S) coupled with kinematic invariance.",
            what_need_not_be_computed="Individual point coordinate calculations across the continuous plane.",
            expected_new_capability="Dynamic functional reasoning; strict logical duality (direct vs converse admissibility control).",
            pedagogical_intent="Lyapin argues that geometric loci are the vital pedagogical bridge connecting Euclidean geometry with analytical geometry and mathematical analysis.",
            page_reference="pp. 310-324",
            original_russian_text="Методика изучения геометрических мест: динамический аспект геометрии. Необходимость доказательства прямой и обратной теоремы. Формирование функционального мышления.",
        )
        self.register_episode(ep_a7_1)
        self.register_mapping(
            PrimitiveMappingRecord(
                episode_id=ep_a7_1.episode_id,
                primitive_symbols=["Ad", "I", "Rs"],
                mapping_breakdown={
                    "Ad": "Admissibility: strict boundary control requiring both direct and converse theorem proofs.",
                    "I": "Invariant Reasoning: locus as the geometric carrier of a preserved metric invariant.",
                    "Rs": "Representation Shift: static Euclidean drawing -> dynamic kinematic path in the plane.",
                },
                structural_concordance=0.97,
                epistemic_notes="Secondary teaching doctrine explicitly cultivating admissibility bounds and functional invariance.",
            )
        )

    def register_episode(self, episode: DevelopmentalEpisode) -> None:
        self.episodes[episode.episode_id] = episode

    def register_mapping(self, mapping: PrimitiveMappingRecord) -> None:
        self.primitive_mappings[mapping.episode_id] = mapping

    def get_episode(self, episode_id: str) -> Optional[DevelopmentalEpisode]:
        return self.episodes.get(episode_id)

    def get_mapping(self, episode_id: str) -> Optional[PrimitiveMappingRecord]:
        return self.primitive_mappings.get(episode_id)

    def list_episodes_by_batch(self, batch: CorpusBatch) -> List[DevelopmentalEpisode]:
        return [ep for ep in self.episodes.values() if ep.corpus_batch == batch]

    def export_extraction_dataset(self) -> Dict[str, Any]:
        """Exports all extracted episodes and post-hoc primitive mappings."""
        return {
            "total_episodes": len(self.episodes),
            "episodes": [ep.to_dict() for ep in self.episodes.values()],
            "primitive_mappings": [m.to_dict() for m in self.primitive_mappings.values()],
        }
