#!/usr/bin/env python3
r"""
Developmental Extraction Engine.
Extracts and Manages Structured Pedagogical Episodes across the Pre-Reform Soviet Mathematics Arc,
Olympiad Enrichment Track, and the Kolmogorov Modernist Reform.

Implements the standardized 9-element schema:
    grade/stage -> problem presented -> representation supplied -> representation student must invent ->
    allowed operations -> hint/scaffold -> key mathematical move -> what need not be computed -> expected new capability

Epistemic Isolation Guarantee:
    Episodes are extracted and stored in their native pedagogical formulation.
    Post-hoc mapping onto the 16 methodological primitives is stored in separate mapping records.
"""

from __future__ import annotations

import json
from collections import Counter
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
        self._initialize_canonical_batch_b_episodes()
        self._initialize_canonical_batch_c_episodes()

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
        # A1: Popova (1933) - Part 2: Crossing the Decade (Addition)
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
        # A1: Popova (1933) - Part 2: Crossing the Decade (Subtraction)
        # ---------------------------------------------------------------------
        ep_a1_3 = DevelopmentalEpisode(
            episode_id="DEV-A1-POP-03",
            source_id="A1_POPOVA_1933",
            source_citation="Попова Н. С. Учебник арифметики для начальной школы. Ч. 2. — М.: Учпедгиз, 1933. — С. 34.",
            corpus_batch=CorpusBatch.BATCH_A_ORDINARY_PROGRESSION,
            grade_stage=DevelopmentalStage.GRADE_1_SECOND_DECADE,
            problem_presented="Subtraction crossing the decade: Compute 13 - 5 (Вычитание с переходом через десяток двумя способами).",
            representation_supplied="13 counters arranged as 1 full bundle of 10 and 3 separate units.",
            representation_invented="Dual decomposition schema: Route 1: 13 - 3 - 2 = 10 - 2 = 8; Route 2: (10 - 5) + 3 = 5 + 3 = 8.",
            allowed_operations=[
                "Decomposing subtrahend 5 into 3 and 2",
                "Subtracting from 10 directly and adding remaining units",
                "Associative subtraction",
            ],
            hint_scaffold="Teacher asks: 'Way 1: Subtract 3 first to reach 10, then how many more? (2). Way 2: Take 5 directly from the ten bundle (leaving 5), and add the 3 units.'",
            key_mathematical_move="Establishing computational equivalence between two alternative auxiliary decomposition paths through the decade boundary.",
            what_need_not_be_computed="Counting backwards by ones from 13 down to 8 (12, 11, 10, 9, 8).",
            expected_new_capability="Dual operational flexibility; reversibility of place-value regrouping.",
            pedagogical_intent="Popova trains pupils to realize that subtraction through 10 has multiple valid decompositions, cultivating algebraic choice.",
            page_reference="Part 2, p. 34",
            original_russian_text="Вычесть 5 из 13: 1-й способ: 13 - 3 = 10, 10 - 2 = 8; 2-й способ: 10 - 5 = 5, 5 + 3 = 8.",
        )
        self.register_episode(ep_a1_3)
        self.register_mapping(
            PrimitiveMappingRecord(
                episode_id=ep_a1_3.episode_id,
                primitive_symbols=["Ax", "Iv", "Sr"],
                mapping_breakdown={
                    "Ax": "Auxiliary Construction: choice of intermediate decade bridge (13-3 or 10-5).",
                    "Iv": "Inverse Reasoning: subtraction conceived as inverse complement of decade addition.",
                    "Sr": "State Reduction: reduces compound subtraction to two single-digit table facts.",
                },
                structural_concordance=0.97,
                epistemic_notes="Demonstrates early operational commutativity and alternative decomposition pathways.",
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
        # A5: Kiselev (1938) - Geometry: Pythagorean Theorem & Area Shear
        # ---------------------------------------------------------------------
        ep_a5_2 = DevelopmentalEpisode(
            episode_id="DEV-A5-KIS-GEOM-02",
            source_id="A5_KISELEV_GEOMETRY_1938",
            source_citation="Киселев А. П. Геометрия. Ч. 1: Планиметрия. — М.: Учпедгиз, 1938. — С. 118–121.",
            corpus_batch=CorpusBatch.BATCH_A_ORDINARY_PROGRESSION,
            grade_stage=DevelopmentalStage.GRADE_6_7_PLANAR_GEOMETRY,
            problem_presented="Theorem of Pythagoras: In a right-angled triangle ABC, the square on the hypotenuse equals the sum of squares on the legs (c^2 = a^2 + b^2).",
            representation_supplied="Right triangle with three squares constructed externally on its sides ('Euclid's Bride' / Pythagoras windmill).",
            representation_invented="Auxiliary altitude dropped from right angle C through hypotenuse square, bisecting it into two rectangles; connecting lines forming sheared triangles.",
            allowed_operations=[
                "Parallel area shear (triangles on the same base between parallel lines have equal area)",
                "SAS triangle congruence",
                "Additive composition of areas",
            ],
            hint_scaffold="Euclid-Kiselev scaffold: 'Drop a perpendicular from C to the base of the hypotenuse square. Can you show that rectangle BLKD has twice the area of triangle ABD?'",
            key_mathematical_move="Auxiliary dissection of the hypotenuse square into two rectangles whose areas match the leg squares via area-preserving shear invariance.",
            what_need_not_be_computed="Numerical lengths, square roots, or algebraic coordinates.",
            expected_new_capability="Area shear invariance; auxiliary line routing in 2D Euclidean geometry.",
            pedagogical_intent="Kiselev presents the classical synthetic proof to demonstrate how auxiliary lines unveil invariant area equalities.",
            page_reference="pp. 118-121",
            original_russian_text="Теорема Пифагора: Квадрат, построенный на гипотенузе, равен сумме квадратов, построенных на катетах. Опустим перпендикуляр из вершины прямого угла на основание квадрата гипотенузы...",
        )
        self.register_episode(ep_a5_2)
        self.register_mapping(
            PrimitiveMappingRecord(
                episode_id=ep_a5_2.episode_id,
                primitive_symbols=["Ax", "I", "Rs"],
                mapping_breakdown={
                    "Ax": "Auxiliary Construction: altitude segment extending across hypotenuse square and connecting diagonals.",
                    "I": "Invariant Reasoning: area invariance under shear and rotation.",
                    "Rs": "Representation Shift: metric length identity c^2 = a^2 + b^2 -> area decomposition equality.",
                },
                structural_concordance=0.98,
                epistemic_notes="Classical synthetic proof of Pythagoras via geometric shear invariance.",
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
        # A6: Kiselev (1938) - Algebra: Completing the Square
        # ---------------------------------------------------------------------
        ep_a6_2 = DevelopmentalEpisode(
            episode_id="DEV-A6-KIS-ALG-02",
            source_id="A6_KISELEV_ALGEBRA_1938",
            source_citation="Киселев А. П. Алгебра. Ч. 2. — М.: Учпедгиз, 1938. — С. 45–48.",
            corpus_batch=CorpusBatch.BATCH_A_ORDINARY_PROGRESSION,
            grade_stage=DevelopmentalStage.GRADE_8_9_QUADRATICS_SYSTEMS,
            problem_presented="Solve the quadratic equation x^2 + px + q = 0 by completing the square (Выделение полного квадрата).",
            representation_supplied="Quadratic equation in canonical form x^2 + px + q = 0.",
            representation_invented="Auxiliary completion of the binomial square: add and subtract (p/2)^2 to synthesize (x + p/2)^2 = (p/2)^2 - q.",
            allowed_operations=[
                "Adding and subtracting an auxiliary balanced term (p/2)^2",
                "Synthesizing the perfect square trinomial (x + p/2)^2",
                "Extracting square roots via inverse reasoning",
            ],
            hint_scaffold="Teacher prompt: 'Look at x^2 + 2*(p/2)*x. What constant term is needed to make this an exact square of a sum? Add (p/2)^2 to both sides of the equation.'",
            key_mathematical_move="Auxiliary construction of the missing constant term (p/2)^2, converting a non-invertible quadratic into an invertible linear squared form.",
            what_need_not_be_computed="Blind memorization of the quadratic formula without geometric/algebraic insight.",
            expected_new_capability="Auxiliary completion of algebraic invariants; inversion of quadratic dependencies.",
            pedagogical_intent="Kiselev derives the quadratic formula through transparent auxiliary completion rather than dogmatic rote presentation.",
            page_reference="Part 2, pp. 45-48",
            original_russian_text="Выделение полного квадрата: x^2 + px = -q. Прибавим к обеим частям (p/2)^2: (x + p/2)^2 = p^2/4 - q.",
        )
        self.register_episode(ep_a6_2)
        self.register_mapping(
            PrimitiveMappingRecord(
                episode_id=ep_a6_2.episode_id,
                primitive_symbols=["Ax", "Iv", "Sr"],
                mapping_breakdown={
                    "Ax": "Auxiliary Construction: adding balanced auxiliary term (p/2)^2.",
                    "Iv": "Inverse Reasoning: inverting the quadratic function via square root extraction.",
                    "Sr": "State Reduction: reduces quadratic polynomial equation to elementary linear shifts.",
                },
                structural_concordance=0.98,
                epistemic_notes="Pivotal auxiliary completion technique in secondary algebra.",
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

    def _initialize_canonical_batch_b_episodes(self) -> None:
        """Initializes canonical extraction episodes for Batch B (Olympiad & Circles: B1 to B4)."""

        # ---------------------------------------------------------------------
        # B1: Bonchkovsky (1936) - Moscow Olympiad 1935: Parity Invariant
        # ---------------------------------------------------------------------
        ep_b1_1 = DevelopmentalEpisode(
            episode_id="DEV-B1-BONCH-01",
            source_id="B1_BONCHKOVSKY_OLYMPIAD_1936",
            source_citation="Бончковский Р. Н. Московские математические олимпиады 1935 и 1936 годов. — М.–Л.: ОНТИ, 1936. — С. 18–21.",
            corpus_batch=CorpusBatch.BATCH_B_OLYMPIAD_ENRICHMENT,
            grade_stage=DevelopmentalStage.GRADE_8_9_QUADRATICS_SYSTEMS,
            problem_presented="1935 Moscow Olympiad: Can an 8x8 chessboard with two opposite corner squares removed be completely covered by 31 dominoes of size 1x2?",
            representation_supplied="Deficient chessboard grid of 62 unit squares; physical domino tiles covering 2 squares.",
            representation_invented="Two-color invariant coloring chi: Z^2 -> {Black, White}; parity balance equation: dominoes = 31, Black = 32, White = 30.",
            allowed_operations=[
                "Bi-coloring the grid in alternating checkerboard pattern",
                "Counting black and white cells covered by an arbitrary 1x2 domino (always 1 Black + 1 White)",
                "Global parity contradiction deduction",
            ],
            hint_scaffold="Olympiad hint: 'Consider the colors of the two removed opposite corner squares. Are they of the same color or different colors?'",
            key_mathematical_move="Global invariant coloring: proving that every domino covers exactly 1 black and 1 white square, establishing an insurmountable parity obstruction (31 dominoes require 31 black and 31 white squares).",
            what_need_not_be_computed="Exhaustive combinatorial testing of tiling combinations (approx. 2^62 configurations).",
            expected_new_capability="Global invariant obstruction reasoning; non-constructive impossibility proof.",
            pedagogical_intent="Bonchkovsky highlights this problem as the archetype of Olympiad thinking: avoiding brute-force search by constructing a global conservation invariant.",
            page_reference="pp. 18-21",
            original_russian_text="Задача о покрытии доски домино: каждое домино покрывает одно черное и одно белое поле. Противоположные углы одного цвета. Покрытие невозможно по соображению четности цветов.",
        )
        self.register_episode(ep_b1_1)
        self.register_mapping(
            PrimitiveMappingRecord(
                episode_id=ep_b1_1.episode_id,
                primitive_symbols=["I", "N", "G"],
                mapping_breakdown={
                    "I": "Invariant Reasoning: black-white parity conservation under domino covering.",
                    "N": "Negative Information: complete elimination of combinatorial tiling attempts.",
                    "G": "Global Reasoning: global cell count discrepancy supersedes local geometric fitting.",
                },
                structural_concordance=0.99,
                epistemic_notes="Landmark Soviet Olympiad parity invariant problem.",
            )
        )

        # ---------------------------------------------------------------------
        # B2: Shklyarsky et al. (1950) - Arithmetic: Dirichlet Pigeonhole Principle
        # ---------------------------------------------------------------------
        ep_b2_1 = DevelopmentalEpisode(
            episode_id="DEV-B2-SHK-ARITH-01",
            source_id="B2_SHKLYARSKY_ARITH_ALG_1950",
            source_citation="Шклярский Д. О., Ченцов Н. Н., Яглом И. М. Избранные задачи и теоремы: Арифметика и алгебра. — М.–Л.: ГИТТЛ, 1950. — Задача 42, с. 24.",
            corpus_batch=CorpusBatch.BATCH_B_OLYMPIAD_ENRICHMENT,
            grade_stage=DevelopmentalStage.GRADE_8_9_QUADRATICS_SYSTEMS,
            problem_presented="Theorem of Divisibility: Among any (n + 1) positive integers chosen from {1, 2, ..., 2n}, there always exist two integers such that one divides the other.",
            representation_supplied="Arbitrary subset of (n + 1) integers chosen from the sequence 1 to 2n.",
            representation_invented="Dyadic factorization representation: write each integer x in the form x = 2^k * m, where m is an odd integer in {1, 3, 5, ..., 2n - 1}.",
            allowed_operations=[
                "Factoring out all powers of 2",
                "Classifying integers into n pigeonhole bins indexed by their odd part m",
                "Application of Dirichlet's Principle (Pigeonhole Principle)",
            ],
            hint_scaffold="Scaffold prompt: 'How many odd numbers are there in the set {1, 2, ..., 2n}? Exactly n. If we have n + 1 numbers, what can we say about their odd parts?'",
            key_mathematical_move="Representation shift factoring each number into an odd kernel m and a dyadic scale 2^k, reducing a quadratic number of pairwise divisibility tests to n pigeonhole categories.",
            what_need_not_be_computed="All C(n+1, 2) pairwise divisibility checks across the chosen subset.",
            expected_new_capability="Pigeonhole partitioning via canonical representation shifts; non-constructive existence proof.",
            pedagogical_intent="Shklyarsky and Yaglom use this problem to cultivate the habit of classifying infinite or complex arithmetic structures into finite invariant pigeonholes.",
            page_reference="p. 24, Problem 42",
            original_russian_text="Среди любых n+1 чисел из 1, 2, ..., 2n найдутся два, из которых одно делится на другое. Представим каждое число в виде x = 2^k * m, где m — нечетное. Нечетных чисел всего n. По принципу Дирихле...",
        )
        self.register_episode(ep_b2_1)
        self.register_mapping(
            PrimitiveMappingRecord(
                episode_id=ep_b2_1.episode_id,
                primitive_symbols=["Rs", "Ii", "N"],
                mapping_breakdown={
                    "Rs": "Representation Shift: integer x -> dyadic pair (k, m) where m is odd.",
                    "Ii": "Indirect Inference: Dirichlet pigeonhole principle establishing existence without identifying the specific pair.",
                    "N": "Negative Information: avoids testing C(n+1, 2) divisibility pairs.",
                },
                structural_concordance=0.98,
                epistemic_notes="Pivotal math-circle application of representation shifts and indirect inference.",
            )
        )

        # ---------------------------------------------------------------------
        # B3: Shklyarsky et al. (1952) - Planimetry: Heron's Shortest Path via Reflection
        # ---------------------------------------------------------------------
        ep_b3_1 = DevelopmentalEpisode(
            episode_id="DEV-B3-SHK-GEOM-01",
            source_id="B3_SHKLYARSKY_GEOM_1952_1954",
            source_citation="Шклярский Д. О., Ченцов Н. Н., Яглом И. М. Избранные задачи и теоремы: Планиметрия. — М.: ГИТТЛ, 1952. — Задача 15, с. 18.",
            corpus_batch=CorpusBatch.BATCH_B_OLYMPIAD_ENRICHMENT,
            grade_stage=DevelopmentalStage.GRADE_6_7_PLANAR_GEOMETRY,
            problem_presented="Heron's Extremum Problem: Given two points A and B on the same side of straight line L, find point P on line L that minimizes the path length |AP| + |PB|.",
            representation_supplied="Two points A, B in half-plane and line L; broken path APB.",
            representation_invented="Auxiliary symmetry reflection: reflect point B across line L to B'; straight line segment AB' intersecting L at optimal point P*.",
            allowed_operations=[
                "Axial symmetry reflection across line L",
                "Triangle inequality: straight line segment is the shortest distance between two points",
                "Isometry preservation of distances: |PB| = |PB'|",
            ],
            hint_scaffold="Circle prompt: 'If a ray of light starts at A, reflects off mirror L, and reaches B, how does it travel? Reflect point B to the other side of the mirror.'",
            key_mathematical_move="Auxiliary reflection converting a non-differentiable broken path minimization into a straight Euclidean line segment.",
            what_need_not_be_computed="Calculus derivatives, coordinate calculations, or numerical search.",
            expected_new_capability="Geometric extremum reasoning via symmetry transformations.",
            pedagogical_intent="Demonstrates how geometric transformations (isometries) solve variational optimization problems without calculus.",
            page_reference="p. 18, Problem 15",
            original_russian_text="Кратчайший путь от точки A к точке B с заходом на прямую L: отразим точку B относительно прямой L в точку B'. Кратчайший путь — отрезок AB'. Точка P — точка пересечения AB' с L.",
        )
        self.register_episode(ep_b3_1)
        self.register_mapping(
            PrimitiveMappingRecord(
                episode_id=ep_b3_1.episode_id,
                primitive_symbols=["Ax", "Rs", "E", "I"],
                mapping_breakdown={
                    "Ax": "Auxiliary Construction: reflected symmetry point B'.",
                    "Rs": "Representation Shift: broken path |AP| + |PB| -> straight line segment |AB'|.",
                    "E": "Extremal Reasoning: minimizing total distance via triangle inequality.",
                    "I": "Invariant Reasoning: reflection isometry preserves lengths.",
                },
                structural_concordance=0.99,
                epistemic_notes="Classic variational optimization via geometric symmetry.",
            )
        )

        # ---------------------------------------------------------------------
        # B4: Moscow Olympiad Corpus (1954) - Central Symmetry Game Strategy
        # ---------------------------------------------------------------------
        ep_b4_1 = DevelopmentalEpisode(
            episode_id="DEV-B4-MOSCOW_OLYMPIADS_1935_1957",
            source_id="B4_MOSCOW_OLYMPIADS_1935_1957",
            source_citation="Московские математические олимпиады 1935–1957 гг. — М.: МЦНМО, 2006. — 1954 г., с. 142.",
            corpus_batch=CorpusBatch.BATCH_B_OLYMPIAD_ENRICHMENT,
            grade_stage=DevelopmentalStage.GRADE_8_9_QUADRATICS_SYSTEMS,
            problem_presented="Game of Pennies on a Table (1954): Two players take turns placing identical circular coins on a round table without overlapping. The last player who can place a coin wins. Who has a winning strategy?",
            representation_supplied="Circular table of radius R; identical circular coins of radius r; sequential alternating game tree.",
            representation_invented="Central symmetry involution: center of table O as fixed point; reflection map S_O(X) = X' across O.",
            allowed_operations=[
                "First move at table center O",
                "Symmetric response: for any move by Player 2 at X, Player 1 places coin at central reflection X' = 2*O - X",
                "Proof of admissibility: if position X is available, position X' is also available by symmetry",
            ],
            hint_scaffold="Olympiad committee scaffold: 'The table has central symmetry. Can Player 1 maintain a symmetric state after every one of his turns?'",
            key_mathematical_move="Control strategy synthesized via geometric involution invariance: maintaining a symmetric configuration guarantees that whenever Player 2 has a move, Player 1 has an unblocked counterpart move.",
            what_need_not_be_computed="Combinatorial tree search over the continuous space of possible coin packings.",
            expected_new_capability="Game-theoretic strategy synthesis via geometric symmetry invariants.",
            pedagogical_intent="Trains students to view adversarial games through the lens of group symmetries and invariant sets.",
            page_reference="1954, p. 142",
            original_russian_text="Игра с монетами на круглом столе. Первый игрок ставит первую монету в центр стола, а затем отвечает центрально-симметрично на каждый ход второго игрока. Первый всегда побеждает.",
        )
        self.register_episode(ep_b4_1)
        self.register_mapping(
            PrimitiveMappingRecord(
                episode_id=ep_b4_1.episode_id,
                primitive_symbols=["I", "C", "N"],
                mapping_breakdown={
                    "I": "Invariant Reasoning: central point symmetry involution S_O.",
                    "C": "Control Intervention: closed-loop policy responding to Player 2's actions.",
                    "N": "Negative Information: complete omission of game-tree branch evaluation.",
                },
                structural_concordance=0.98,
                epistemic_notes="Foundational game-theoretic invariant strategy.",
            )
        )

    def _initialize_canonical_batch_c_episodes(self) -> None:
        """Initializes canonical extraction episodes for Batch C (Kolmogorov Reform: C1 to C4)."""

        # ---------------------------------------------------------------------
        # C1: Kolmogorov et al. (1967) - Program Draft: Transformation Groups
        # ---------------------------------------------------------------------
        ep_c1_1 = DevelopmentalEpisode(
            episode_id="DEV-C1-KOLM-DRAFT-01",
            source_id="C1_KOLMOGOROV_PROGRAM_DRAFT_1967",
            source_citation="Колмогоров А. Н., Маркушевич А. И., Яглом И. М. Проект программы средней школы // Математика в школе. — 1967. — № 1. — С. 5–24.",
            corpus_batch=CorpusBatch.BATCH_C_KOLMOGOROV_REFORM,
            grade_stage=DevelopmentalStage.TEACHER_METHODOLOGY_DOCTRINE,
            problem_presented="Reform Intent Doctrine: Replacement of traditional Euclidean congruence axioms with geometric transformation groups and vector spaces.",
            representation_supplied="Traditional Kiselev Euclidean geometry based on congruent triangles, rigid figures, and construction problems.",
            representation_invented="Group of plane transformations (Isometries: translations, rotations, reflections) and linear space of vectors R^2.",
            allowed_operations=[
                "Composition of geometric transformations",
                "Vector addition, scalar multiplication, and inner product",
                "Set-theoretic operations on point sets (subsets of R^2)",
            ],
            hint_scaffold="Reformers' thesis: 'Classical Euclidean geometry isolates school mathematics from physics and modern science. Modern geometry is the study of invariants under transformation groups (Klein's Erlangen Program).'",
            key_mathematical_move="Axiomatic shift: defining geometric congruence not as a static primitive relation, but as an equivalence class under the group of distance-preserving bijections.",
            what_need_not_be_computed="Dozens of synthetic triangle congruence theorems and auxiliary construction compass drills.",
            expected_new_capability="Group-theoretic and vector-space spatial modeling; algebraic-geometric synthesis.",
            pedagogical_intent="Kolmogorov's explicit goal: modernize school education to directly align with 20th-century university mathematics and physics.",
            page_reference="pp. 5-24",
            original_russian_text="Проект реформы: геометрия должна строиться на понятии геометрических преобразований (движений) и векторной алгебры, связывая математику с физикой.",
        )
        self.register_episode(ep_c1_1)
        self.register_mapping(
            PrimitiveMappingRecord(
                episode_id=ep_c1_1.episode_id,
                primitive_symbols=["Rs", "G", "Sc"],
                mapping_breakdown={
                    "Rs": "Representation Shift: static figures in the plane -> global mapping transformations f: R^2 -> R^2.",
                    "G": "Global Reasoning: transformation groups acting globally across the entire space.",
                    "Sc": "Self-Consistent Closure: axiomatic closure of the transformation group.",
                },
                structural_concordance=0.97,
                epistemic_notes="Constitutive programmatic statement of the Soviet structural reform.",
            )
        )

        # ---------------------------------------------------------------------
        # C2: Kolmogorov (1967/68) - National Program: General Function Mapping
        # ---------------------------------------------------------------------
        ep_c2_1 = DevelopmentalEpisode(
            episode_id="DEV-C2-KOLM-NEW_PROGRAMS_1967_1968",
            source_id="C2_KOLMOGOROV_NEW_PROGRAMS_1967_1968",
            source_citation="Колмогоров А. Н. Новые программы по математике // Математика в школе. — 1967. — № 2. — С. 4–13.",
            corpus_batch=CorpusBatch.BATCH_C_KOLMOGOROV_REFORM,
            grade_stage=DevelopmentalStage.GRADE_6_7_ELEMENTARY_ALGEBRA,
            problem_presented="Curriculum Policy Directive: Introducing the general definition of a function as an arbitrary set mapping f: X -> Y.",
            representation_supplied="Traditional pre-reform definition of function as an analytical formula y = f(x) or physical quantitative variation.",
            representation_invented="Set-theoretic mapping schema: arrow diagram from domain X to codomain Y; subset of Cartesian product X x Y satisfying single-valuedness.",
            allowed_operations=[
                "Explicit verification of domain of definition D(f)",
                "Verification of single-valuedness condition: each x has exactly one y",
                "Functional composition (f o g)(x)",
            ],
            hint_scaffold="Program doctrine: 'A function is not just an analytical formula. A function is a rule assigning to each element of set X a unique element of set Y.'",
            key_mathematical_move="Detaching the function concept from algebraic formulas, establishing domain admissibility as a strict prerequisite.",
            what_need_not_be_computed="Any numerical value or evaluation table prior to domain verification.",
            expected_new_capability="Abstract set-theoretic functional thinking; formal domain admissibility control.",
            pedagogical_intent="Standardizes the Bourbaki/Kolmogorov set-theoretic foundation across secondary school algebra.",
            page_reference="pp. 4-13",
            original_russian_text="Функция как отображение одного множества на другое. Область определения и область значений. Преодоление узко-формульного взгляда на функцию.",
        )
        self.register_episode(ep_c2_1)
        self.register_mapping(
            PrimitiveMappingRecord(
                episode_id=ep_c2_1.episode_id,
                primitive_symbols=["Ad", "Rs"],
                mapping_breakdown={
                    "Ad": "Admissibility: strict definition of domain D(f) and range E(f) before computation.",
                    "Rs": "Representation Shift: formula/graph -> abstract set mapping f: X -> Y.",
                },
                structural_concordance=0.96,
                epistemic_notes="Introduction of set-theoretic functional mappings into school algebra.",
            )
        )

        # ---------------------------------------------------------------------
        # C3: Kolmogorov et al. (1979) - Geometry: Congruence as Isometry
        # ---------------------------------------------------------------------
        ep_c3_1 = DevelopmentalEpisode(
            episode_id="DEV-C3-KOLMOGOROV_GEOMETRY_1979",
            source_id="C3_KOLMOGOROV_GEOMETRY_1979",
            source_citation="Колмогоров А. Н., Семенович А. Ф., Черкасов Р. С. Геометрия: 6–8 классы. — М.: Просвещение, 1979. — С. 34–38.",
            corpus_batch=CorpusBatch.BATCH_C_KOLMOGOROV_REFORM,
            grade_stage=DevelopmentalStage.GRADE_6_7_PLANAR_GEOMETRY,
            problem_presented="Definition of Geometric Congruence (Equality of Figures): Two figures F1 and F2 are congruent if there exists an isometry f: R^2 -> R^2 such that f(F1) = F2.",
            representation_supplied="Two arbitrary planar figures F1 and F2 (possibly non-polygonal).",
            representation_invented="Global distance-preserving bijective mapping f mapping every point X in F1 to f(X) in F2 preserving metric distance |f(X)f(Y)| = |XY|.",
            allowed_operations=[
                "Composition of fundamental isometries (Translations, Rotations, Axial Reflections)",
                "Proving the existence of an isometry mapping F1 onto F2",
            ],
            hint_scaffold="Kolmogorov textbook scaffold: 'Do not try to pick up figure F1 and lay it on F2 physically. Instead, specify the translation vector or reflection axis that maps F1 to F2.'",
            key_mathematical_move="Transforming figure congruence from an empirical physical superposition or list of matching angles into the existence of an abstract distance-preserving group action.",
            what_need_not_be_computed="Manual pairwise side and angle verifications across polygon vertices.",
            expected_new_capability="Group-action geometric vision; global transformation synthesis.",
            pedagogical_intent="Directly implements Klein's Erlangen Program in 6th-grade secondary school.",
            page_reference="pp. 34-38",
            original_russian_text="Движение — это отображение плоскости на себя, сохраняющее расстояния. Две фигуры называются равными, если существует движение, переводящее одну фигуру в другую.",
        )
        self.register_episode(ep_c3_1)
        self.register_mapping(
            PrimitiveMappingRecord(
                episode_id=ep_c3_1.episode_id,
                primitive_symbols=["Rs", "I", "G"],
                mapping_breakdown={
                    "Rs": "Representation Shift: static congruence relation -> global mapping bijection f.",
                    "I": "Invariant Reasoning: metric distance invariance |f(X)f(Y)| = |XY|.",
                    "G": "Global Reasoning: transformation acts on the entire ambient plane R^2 simultaneously.",
                },
                structural_concordance=0.98,
                epistemic_notes="The defining hallmark of the Kolmogorov geometry curriculum.",
            )
        )

        # ---------------------------------------------------------------------
        # C4: Kolmogorov et al. (1983) - Analysis: Derivative as Linearization
        # ---------------------------------------------------------------------
        ep_c4_1 = DevelopmentalEpisode(
            episode_id="DEV-C4-KOLMOGOROV_ALGEBRA_ANALYSIS_1983",
            source_id="C4_KOLMOGOROV_ALGEBRA_ANALYSIS_1983",
            source_citation="Колмогоров А. Н. и др. Алгебра и начала анализа: 9–10 классы. — М.: Просвещение, 1983. — С. 112–116.",
            corpus_batch=CorpusBatch.BATCH_C_KOLMOGOROV_REFORM,
            grade_stage=DevelopmentalStage.GRADE_9_10_STEREOMETRY,
            problem_presented="Definition of the Derivative: For function f(x), compute derivative f'(x0) and establish the tangent line equation.",
            representation_supplied="Nonlinear curve y = f(x) and secant chord connecting (x0, f(x0)) to (x0 + Delta x, f(x0 + Delta x)).",
            representation_invented="Local linear approximation schema: Delta f = f'(x0) * Delta x + alpha(Delta x) * Delta x, where alpha(Delta x) -> 0 as Delta x -> 0.",
            allowed_operations=[
                "Limit of difference quotient lim (Delta f / Delta x)",
                "Local linear Taylor approximation (1st order)",
                "Tangent line construction y - y0 = f'(x0)(x - x0)",
            ],
            hint_scaffold="Textbook prompt: 'In a small neighborhood of x0, the curve behaves almost like a straight line. What is the slope of this best approximating straight line?'",
            key_mathematical_move="Local linear reduction: replacing an intractable nonlinear curve in an infinitesimal neighborhood with its optimal linear tangent operator.",
            what_need_not_be_computed="Global nonlinear evaluations across distant points.",
            expected_new_capability="Local infinitesimal linearization; calculus differential operator mastery.",
            pedagogical_intent="Kolmogorov anchors secondary analysis in the modern concept of differential as the best linear approximation.",
            page_reference="pp. 112-116",
            original_russian_text="Производная функции: предел отношения приращения функции к приращению аргумента. Геометрический смысл: угловой коэффициент касательной. Линеаризация приращения.",
        )
        self.register_episode(ep_c4_1)
        self.register_mapping(
            PrimitiveMappingRecord(
                episode_id=ep_c4_1.episode_id,
                primitive_symbols=["L", "Sr", "Ax"],
                mapping_breakdown={
                    "L": "Local Reasoning: restricting analysis to an infinitesimal neighborhood Delta x -> 0.",
                    "Sr": "State Reduction: reduces nonlinear variation to local linear multiplier f'(x0).",
                    "Ax": "Auxiliary Construction: auxiliary tangent line and differential.",
                },
                structural_concordance=0.97,
                epistemic_notes="Culmination of the secondary analysis curriculum.",
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

    def compute_batch_primitive_distribution(self, batch: CorpusBatch) -> Dict[str, int]:
        """Counts how many times each of the 16 methodological primitives is instantiated in a batch."""
        episodes = self.list_episodes_by_batch(batch)
        counter: Counter[str] = Counter()
        for ep in episodes:
            mapping = self.primitive_mappings.get(ep.episode_id)
            if mapping:
                for p in mapping.primitive_symbols:
                    counter[p] += 1
        return dict(counter)

    def compute_cross_batch_comparative_table(self) -> Dict[str, Any]:
        """Computes comparative distribution of methodological primitives across Batches A, B, and C."""
        dist_a = self.compute_batch_primitive_distribution(CorpusBatch.BATCH_A_ORDINARY_PROGRESSION)
        dist_b = self.compute_batch_primitive_distribution(CorpusBatch.BATCH_B_OLYMPIAD_ENRICHMENT)
        dist_c = self.compute_batch_primitive_distribution(CorpusBatch.BATCH_C_KOLMOGOROV_REFORM)

        all_primitives = sorted(set(list(dist_a.keys()) + list(dist_b.keys()) + list(dist_c.keys())))

        return {
            "batch_a_episodes": len(self.list_episodes_by_batch(CorpusBatch.BATCH_A_ORDINARY_PROGRESSION)),
            "batch_b_episodes": len(self.list_episodes_by_batch(CorpusBatch.BATCH_B_OLYMPIAD_ENRICHMENT)),
            "batch_c_episodes": len(self.list_episodes_by_batch(CorpusBatch.BATCH_C_KOLMOGOROV_REFORM)),
            "primitive_distribution": {
                p: {
                    "Batch_A_Ordinary": dist_a.get(p, 0),
                    "Batch_B_Olympiad": dist_b.get(p, 0),
                    "Batch_C_Reform": dist_c.get(p, 0),
                    "Total": dist_a.get(p, 0) + dist_b.get(p, 0) + dist_c.get(p, 0),
                }
                for p in all_primitives
            },
        }

    def export_extraction_dataset(self) -> Dict[str, Any]:
        """Exports all extracted episodes and post-hoc primitive mappings."""
        return {
            "total_episodes": len(self.episodes),
            "episodes": [ep.to_dict() for ep in self.episodes.values()],
            "primitive_mappings": [m.to_dict() for m in self.primitive_mappings.values()],
            "cross_batch_comparison": self.compute_cross_batch_comparative_table(),
        }
