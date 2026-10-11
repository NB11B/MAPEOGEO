from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ResearchSchoolCandidate:
    id: str
    school_label: str
    lead_person: str
    institution: str
    methods: list[str]
    terms: list[str]
    supporting_sources: list[str]
    subgraph: dict[str, Any]
    confidence: float
    discovered_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ResearchSchoolDetector:
    """Discovers emerging higher-order research school clusters across acquired sources.

    Emits RESEARCH_SCHOOL_CANDIDATE with supporting subgraph.
    Strictly withholds canonical RESEARCH_SCHOOL promotion (reserved for Gate N4.5).
    """

    def __init__(self, db: Any) -> None:
        self.db = db

    def detect_candidates(self, cohort_sources: list[dict[str, Any]]) -> list[ResearchSchoolCandidate]:
        candidates: list[ResearchSchoolCandidate] = []

        # Known historical research school anchors in Soviet mathematical science
        anchor_patterns = [
            {
                "lead_person": "Тихонов А. Н.",
                "institution": "ИПМ им. Келдыша",
                "methods": ["Метод регуляризации Тихонова", "Обратные задачи математической физики"],
                "terms": ["некорректно поставленные задачи", "регуляризирующий алгоритм"],
                "label": "Научная школа А. Н. Тихонова по некорректным и обратным задачам",
            },
            {
                "lead_person": "Понтрягин Л. С.",
                "institution": "МИАН",
                "methods": ["Принцип максимума Понтрягина", "Теория структурной устойчивости"],
                "terms": ["оптимальные процессы", "быстродействие", "грубые системы"],
                "label": "Математическая школа Л. С. Понтрягина по теории управления и дифференциальным уравнениям",
            },
            {
                "lead_person": "Власов А. А.",
                "institution": "МГУ",
                "methods": ["Уравнение Власова", "Метод самосогласованного поля"],
                "terms": ["самосогласованное поле", "коллективные взаимодействия", "электронная плазма"],
                "label": "Школа А. А. Власова по кинетической теории плазмы и коллективным полям",
            },
            {
                "lead_person": "Гельфанд И. М.",
                "institution": "МИАН",
                "methods": ["Уравнение Гельфанда-Левитана", "Оператор Штурма-Лиувилля"],
                "terms": ["обратная спектральная задача", "спектральная функция"],
                "label": "Школа И. М. Гельфанда по спектральной теории операторов и обратным задачам",
            },
            {
                "lead_person": "Чебышев П. Л.",
                "institution": "СПбГУ",
                "methods": ["Метод наилучшего приближения Чебышева", "Метод моментов Чебышева-Маркова"],
                "terms": ["наилучшее приближение", "ортогональные многочлены", "шарнирные механизмы"],
                "label": "Петербургская математическая школа П. Л. Чебышева",
            },
            {
                "lead_person": "Боголюбов Н. Н.",
                "institution": "АН УССР",
                "methods": ["Цепочка уравнений ББГКИ", "Введение в нелинейную механику"],
                "terms": ["цепочка ббгки", "асимптотические методы", "статистическая механика"],
                "label": "Школа Н. Н. Боголюбова по нелинейной механике и статистической физике",
            },
            {
                "lead_person": "Ляпунов А. М.",
                "institution": "Харьковское математическое общество",
                "methods": ["Функция Ляпунова", "Метод функций Ляпунова"],
                "terms": ["устойчивость движения", "характеристические числа"],
                "label": "Школа А. М. Ляпунова по теории устойчивости движения",
            },
            {
                "lead_person": "Фаддеев Л. Д.",
                "institution": "ЛОМИ",
                "methods": ["Уравнения Фаддеева"],
                "terms": ["квантовая задача трех тел", "теория рассеяния"],
                "label": "Ленинградская школа математической физики Л. Д. Фаддеева",
            },
        ]

        for anc in anchor_patterns:
            lead = anc["lead_person"]
            inst = anc["institution"]
            matching_sources: list[str] = []

            for s in cohort_sources:
                text = (s.get("title", "") + " " + s.get("sample_text", "") + " " + " ".join(s.get("authors", []))).lower()
                has_person = lead.split()[0].lower() in text
                has_method = any(m.split()[0].lower() in text for m in anc["methods"])
                if has_person or has_method:
                    matching_sources.append(s.get("id") or s.get("source_id", ""))

            if matching_sources:
                cid_digest = hashlib.sha256(f"{lead}:{inst}:{anc['label']}".encode("utf-8")).hexdigest()[:16]
                cand = ResearchSchoolCandidate(
                    id=f"SOVSCH:{cid_digest}",
                    school_label=anc["label"],
                    lead_person=lead,
                    institution=inst,
                    methods=anc["methods"],
                    terms=anc["terms"],
                    supporting_sources=matching_sources,
                    subgraph={
                        "nodes": [
                            {"type": "PERSON", "label": lead},
                            {"type": "INSTITUTION", "label": inst},
                            {"type": "METHOD", "labels": anc["methods"]},
                            {"type": "TERMS", "labels": anc["terms"]},
                        ],
                        "edges": [
                            {"from": lead, "to": inst, "relation": "AFFILIATED_WITH"},
                            {"from": inst, "to": anc["label"], "relation": "PRODUCES"},
                            {"from": anc["label"], "to": anc["methods"][0], "relation": "DEVELOPS_METHOD"},
                        ],
                    },
                    confidence=0.88,
                )
                candidates.append(cand)

                # Persist to DB
                with self.db.get_connection() as con:
                    con.execute(
                        """
                        INSERT OR REPLACE INTO research_school_candidates (
                            id, school_label, lead_person, institution,
                            methods_json, terms_json, supporting_sources_json,
                            subgraph_json, confidence, discovered_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            cand.id,
                            cand.school_label,
                            cand.lead_person,
                            cand.institution,
                            json.dumps(cand.methods, ensure_ascii=False),
                            json.dumps(cand.terms, ensure_ascii=False),
                            json.dumps(cand.supporting_sources, ensure_ascii=False),
                            json.dumps(cand.subgraph, ensure_ascii=False),
                            cand.confidence,
                            cand.discovered_at,
                        ),
                    )
                    con.commit()

        return candidates
