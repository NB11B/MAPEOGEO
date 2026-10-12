#!/usr/bin/env python3
r"""
Developmental Corpus Registry.
Catalog of Primary, Secondary, Olympiad, and Reform Sources.

Enforces strict batch ordering:
    Batch A (Ordinary School & Teacher Intent: A1-A7) MUST be ingested and baseline-analyzed
    BEFORE Batch B (Olympiad Enrichment: B1-B4) and Batch C (Kolmogorov Reform: C1-C4).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from .developmental_schema import CorpusBatch


@dataclass
class CorpusSourceRecord:
    target_id: str
    short_title: str
    full_bibliographic_citation: str
    year: int
    corpus_batch: CorpusBatch
    priority_order: int
    educational_level: str  # e.g., "PRIMARY_GRADE_1_4", "SECONDARY_GRADE_6_10", "TEACHER_METHODOLOGY"
    epistemic_purpose: str
    access_uri: str
    access_status: str  # "OPEN_DIGITAL_RECORD", "DOWNLOADABLE_DJVU", "SCANNED_PDF", "VERIFIED_BIBLIOGRAPHY"
    is_ingested: bool = False

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["corpus_batch"] = self.corpus_batch.value
        return d


class DevelopmentalCorpusRegistry:
    """Manages the full acquisition registry for the Soviet mathematical developmental arc."""

    def __init__(self) -> None:
        self.sources: Dict[str, CorpusSourceRecord] = {}
        self._initialize_canonical_corpus()

    def _initialize_canonical_corpus(self) -> None:
        # =====================================================================
        # BATCH A: Ordinary School Progression & Teacher Intent (Baseline)
        # =====================================================================
        self.register_source(
            CorpusSourceRecord(
                target_id="A1_POPOVA_1933",
                short_title="Popova: Arithmetic Textbook for Primary School (Parts 1-3)",
                full_bibliographic_citation="Попова Н. С. Учебник арифметики для начальной школы. Части 1–3. — М.: Учпедгиз, 1933.",
                year=1933,
                corpus_batch=CorpusBatch.BATCH_A_ORDINARY_PROGRESSION,
                priority_order=1,
                educational_level="PRIMARY_GRADE_1_3",
                epistemic_purpose="Earliest clean Soviet primary-school baseline: introduces number, operations, word problems, decomposition, and representations before later postwar pedagogy.",
                access_uri="https://rusneb.ru/catalog/000199_000009_008988872/",
                access_status="OPEN_DIGITAL_RECORD",
            )
        )

        self.register_source(
            CorpusSourceRecord(
                target_id="A2_PCHELKO_POLYAK_GRADES_1_4",
                short_title="Pchelko & Polyak: Arithmetic Grades 1-4 (1954-56)",
                full_bibliographic_citation="Пчелко А. С., Поляк Г. Б. Арифметика: Учебник для 1–4 классов начальной школы. — М.: Учпедгиз, 1954–1956.",
                year=1954,
                corpus_batch=CorpusBatch.BATCH_A_ORDINARY_PROGRESSION,
                priority_order=2,
                educational_level="PRIMARY_GRADE_1_4",
                epistemic_purpose="Continuous postwar elementary progression: asks when representation shifts, negative information, invariance, decomposition, and inverse reasoning first appear.",
                access_uri="https://search.rsl.ru/ru/record/01009844216",
                access_status="OPEN_DIGITAL_RECORD",
            )
        )

        self.register_source(
            CorpusSourceRecord(
                target_id="A3_PCHELKO_TEACHER_METHODOLOGY_1949",
                short_title="Pchelko: Teaching Methodology of Arithmetic in Primary School (1949)",
                full_bibliographic_citation="Пчелко А. С. Методика преподавания арифметики в начальной школе: Пособие для учителей. — М.: Учпедгиз, 1949. — 367 с.",
                year=1949,
                corpus_batch=CorpusBatch.BATCH_A_ORDINARY_PROGRESSION,
                priority_order=3,
                educational_level="TEACHER_METHODOLOGY_PRIMARY",
                epistemic_purpose="Explicit teacher doctrine: exposes what teachers were supposed to cultivate (intent behind exercises, mental arithmetic rules, avoiding counting by ones).",
                access_uri="https://search.rsl.ru/ru/record/01006012208",
                access_status="OPEN_DIGITAL_RECORD",
            )
        )

        self.register_source(
            CorpusSourceRecord(
                target_id="A4_PCHELKO_PROBLEM_SOLVING_1949",
                short_title="Pchelko (ed.): Solving Arithmetic Problems in Primary School (1949)",
                full_bibliographic_citation="Решение арифметических задач в начальной школе / Под ред. А. С. Пчелко. — М.: Изд-во АПН РСФСР, 1949. — 224 с.",
                year=1949,
                corpus_batch=CorpusBatch.BATCH_A_ORDINARY_PROGRESSION,
                priority_order=4,
                educational_level="PRIMARY_PROBLEM_SOLVING",
                epistemic_purpose="Problem-solving methodology: maps problem -> representation -> auxiliary construction -> operation sequence (e.g. false assumption method, segment schemas).",
                access_uri="https://search.rsl.ru/ru/record/01006004789",
                access_status="OPEN_DIGITAL_RECORD",
            )
        )

        self.register_source(
            CorpusSourceRecord(
                target_id="A5_KISELEV_GEOMETRY_1938",
                short_title="Kiselev: Geometry (Planimetry & Stereometry) (1938)",
                full_bibliographic_citation="Киселев А. П. Геометрия: Ч. 1: Планиметрия для 6–9 классов; Ч. 2: Стереометрия для 9–10 классов. — М.: Учпедгиз, 1938.",
                year=1938,
                corpus_batch=CorpusBatch.BATCH_A_ORDINARY_PROGRESSION,
                priority_order=5,
                educational_level="SECONDARY_GRADE_6_10",
                epistemic_purpose="Critical pre-reform secondary baseline: tests whether auxiliary constructions, proof structure, invariants, and admissibility predate later Soviet reforms.",
                access_uri="https://search.rsl.ru/ru/record/01005124786",
                access_status="OPEN_DIGITAL_RECORD",
            )
        )

        self.register_source(
            CorpusSourceRecord(
                target_id="A6_KISELEV_ALGEBRA_1938",
                short_title="Kiselev: Algebra (Parts 1-2) (1938/1944)",
                full_bibliographic_citation="Киселев А. П. Алгебра: Учебник для 6–8 и 9–10 классов средней школы. — М.: Учпедгиз, 1938.",
                year=1938,
                corpus_batch=CorpusBatch.BATCH_A_ORDINARY_PROGRESSION,
                priority_order=6,
                educational_level="SECONDARY_GRADE_6_10",
                epistemic_purpose="Algebraic counterpart to Kiselev geometry: evaluates whether transformation/equivalence reasoning is taught procedurally or structurally.",
                access_uri="https://search.rsl.ru/ru/record/01005124777",
                access_status="OPEN_DIGITAL_RECORD",
            )
        )

        self.register_source(
            CorpusSourceRecord(
                target_id="A7_LYAPIN_SECONDARY_METHODOLOGY_1956",
                short_title="Lyapin et al.: Teaching Methodology of Mathematics, Part 2 (1956)",
                full_bibliographic_citation="Ляпин С. Е. и др. Методика преподавания математики. Ч. 2: Преподавание алгебры и геометрии в средней школе. — Л.: Учпедгиз, 1956. — 654 с.",
                year=1956,
                corpus_batch=CorpusBatch.BATCH_A_ORDINARY_PROGRESSION,
                priority_order=7,
                educational_level="TEACHER_METHODOLOGY_SECONDARY",
                epistemic_purpose="Secondary teacher doctrine before Kolmogorov reform: exposes explicit pedagogical doctrine behind algebra/geometry proofs.",
                access_uri="https://search.rsl.ru/ru/record/01005631210",
                access_status="OPEN_DIGITAL_RECORD",
            )
        )

        # =====================================================================
        # BATCH B: Olympiad & Circle Enrichment Track (Parallel Track)
        # =====================================================================
        self.register_source(
            CorpusSourceRecord(
                target_id="B1_BONCHKOVSKY_OLYMPIAD_1936",
                short_title="Bonchkovsky: Moscow Mathematical Olympiads 1935-1936",
                full_bibliographic_citation="Бончковский Р. Н. Московские математические олимпиады 1935 и 1936 годов. — М.–Л.: ОНТИ НКТП СССР, 1936. — 82 с.",
                year=1936,
                corpus_batch=CorpusBatch.BATCH_B_OLYMPIAD_ENRICHMENT,
                priority_order=8,
                educational_level="OLYMPIAD_SECONDARY",
                epistemic_purpose="Contemporaneous window into earliest Moscow Olympiad culture: problems, solutions, and mathematical framing.",
                access_uri="https://math.ru/lib/500",
                access_status="DOWNLOADABLE_DJVU",
            )
        )

        self.register_source(
            CorpusSourceRecord(
                target_id="B2_SHKLYARSKY_ARITH_ALG_1950",
                short_title="Shklyarsky/Chentsov/Yaglom: Selected Problems in Arithmetic & Algebra (1950)",
                full_bibliographic_citation="Шклярский Д. О., Ченцов Н. Н., Яглом И. М. Избранные задачи и теоремы элементарной математики: Арифметика и алгебра. — М.–Л.: ГИТТЛ, 1950.",
                year=1950,
                corpus_batch=CorpusBatch.BATCH_B_OLYMPIAD_ENRICHMENT,
                priority_order=9,
                educational_level="CIRCLE_ENRICHMENT",
                epistemic_purpose="Elementary methodological grammar: divisibility, transformations, integer equations, nonstandard solutions.",
                access_uri="https://math.ru/lib/bib-mat-kr/1",
                access_status="DOWNLOADABLE_DJVU",
            )
        )

        self.register_source(
            CorpusSourceRecord(
                target_id="B3_SHKLYARSKY_GEOM_1952_1954",
                short_title="Shklyarsky et al.: Selected Problems: Planimetry (1952) & Stereometry (1954)",
                full_bibliographic_citation="Шклярский Д. О., Ченцов Н. Н., Яглом И. М. Избранные задачи и теоремы элементарной математики: Планиметрия (1952); Стереометрия (1954). — М.: ГИТТЛ.",
                year=1952,
                corpus_batch=CorpusBatch.BATCH_B_OLYMPIAD_ENRICHMENT,
                priority_order=10,
                educational_level="CIRCLE_ENRICHMENT_GEOM",
                epistemic_purpose="Geometric grammar: auxiliary construction, geometric loci, extremum problems, cutting/reassembly, representation shifts.",
                access_uri="https://math.ru/lib/bib-mat-kr/2",
                access_status="DOWNLOADABLE_DJVU",
            )
        )

        self.register_source(
            CorpusSourceRecord(
                target_id="B4_MOSCOW_OLYMPIADS_1935_1957",
                short_title="Moscow Olympiad Corpus (1935-1957)",
                full_bibliographic_citation="Московские математические олимпиады 1935–1957 гг. Сборник задач / Сост. Р. М. Васильев и др. — М.: МЦНМО, 2006.",
                year=1957,
                corpus_batch=CorpusBatch.BATCH_B_OLYMPIAD_ENRICHMENT,
                priority_order=11,
                educational_level="OLYMPIAD_LONGITUDINAL",
                epistemic_purpose="Longitudinal problem set: tag problems/solutions by primitives to observe distribution shifts over 20+ years.",
                access_uri="https://math.ru/lib/549",
                access_status="DOWNLOADABLE_DJVU",
            )
        )

        # =====================================================================
        # BATCH C: Kolmogorov Structural Reform (Post-1965)
        # =====================================================================
        self.register_source(
            CorpusSourceRecord(
                target_id="C1_KOLMOGOROV_PROGRAM_DRAFT_1967",
                short_title="Kolmogorov/Markushevich/Yaglom: Secondary Math Curriculum Draft (1967)",
                full_bibliographic_citation="Колмогоров А. Н., Маркушевич А. И., Яглом И. М. Проект программы средней школы по математике // Математика в школе. — 1967. — № 1. — С. 5–24.",
                year=1967,
                corpus_batch=CorpusBatch.BATCH_C_KOLMOGOROV_REFORM,
                priority_order=12,
                educational_level="CURRICULUM_REFORM_INTENT",
                epistemic_purpose="Reform intent document: explicit mathematical habits reformers sought to introduce before comparing with actual textbooks.",
                access_uri="https://www.mathnet.ru/links/9f7f1136ca6e2425290a091898c4fa88/danma_381_refs_rus.htm",
                access_status="VERIFIED_BIBLIOGRAPHY",
            )
        )

        self.register_source(
            CorpusSourceRecord(
                target_id="C2_KOLMOGOROV_NEW_PROGRAMS_1967_1968",
                short_title="Kolmogorov: New Programs & 1968 National Curriculum",
                full_bibliographic_citation="Колмогоров А. Н. Новые программы по математике // Математика в школе. — 1967. — № 2. — С. 4–13; Программа по математике на 1968/69 уч. год.",
                year=1967,
                corpus_batch=CorpusBatch.BATCH_C_KOLMOGOROV_REFORM,
                priority_order=13,
                educational_level="NATIONAL_CURRICULUM_POLICY",
                epistemic_purpose="Distinguishes proposed reform philosophy from adopted curriculum policies.",
                access_uri="https://www.mathnet.ru/links/83527523bdc55fe4aaeb6b66c4f848e4/tvp1237.pdf",
                access_status="VERIFIED_BIBLIOGRAPHY",
            )
        )

        self.register_source(
            CorpusSourceRecord(
                target_id="C3_KOLMOGOROV_GEOMETRY_1979",
                short_title="Kolmogorov et al.: Geometry Grades 6-8 (1979/1982)",
                full_bibliographic_citation="Колмогоров А. Н., Семенович А. Ф., Черкасов Р. С. Геометрия: Учебное пособие для 6–8 классов средней школы. — М.: Просвещение, 1979.",
                year=1979,
                corpus_batch=CorpusBatch.BATCH_C_KOLMOGOROV_REFORM,
                priority_order=14,
                educational_level="REFORM_GEOMETRY",
                epistemic_purpose="Direct before/after comparison with Kiselev: tests whether transformations, vectors, coordinates alter taught grammar.",
                access_uri="https://search.rsl.ru/ru/record/01007642342",
                access_status="OPEN_DIGITAL_RECORD",
            )
        )

        self.register_source(
            CorpusSourceRecord(
                target_id="C4_KOLMOGOROV_ALGEBRA_ANALYSIS_1983",
                short_title="Kolmogorov et al.: Algebra & Elements of Analysis Grades 9-10 (1983)",
                full_bibliographic_citation="Колмогоров А. Н., Абрамов А. М., Вейц Б. Е. и др. Алгебра и начала анализа: Учебное пособие для 9–10 классов средней школы. — М.: Просвещение, 1983.",
                year=1983,
                corpus_batch=CorpusBatch.BATCH_C_KOLMOGOROV_REFORM,
                priority_order=15,
                educational_level="UPPER_SECONDARY_ANALYSIS",
                epistemic_purpose="Upper-secondary endpoint: tests whether elementary primitives persist into functions, limits, derivatives, and analysis.",
                access_uri="https://search.rsl.ru/ru/record/01001100671",
                access_status="OPEN_DIGITAL_RECORD",
            )
        )

    def register_source(self, record: CorpusSourceRecord) -> None:
        self.sources[record.target_id] = record

    def list_sources_by_batch(self, batch: CorpusBatch) -> List[CorpusSourceRecord]:
        return sorted(
            [s for s in self.sources.values() if s.corpus_batch == batch],
            key=lambda x: x.priority_order,
        )

    def get_source(self, target_id: str) -> Optional[CorpusSourceRecord]:
        return self.sources.get(target_id)
