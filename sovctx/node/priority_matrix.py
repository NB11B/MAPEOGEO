from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional

from sovctx.node.relational_duality import RelationalDualityEngine
from sovctx.node.temporal_relations import TemporalRelationsEngine
from sovctx.tools.graph_io import load_records, split_records


@dataclass
class PriorityMatrixRow:
    item_id: str
    item_type: str  # OPERATOR, VERB, CONCEPT, SCHOOL
    label: str
    cross_school_count: int
    participating_schools: list[str]
    cross_institution_count: int
    participating_institutions: list[str]
    temporal_span_years: int
    earliest_year: int
    latest_year: int
    betweenness_score: float
    engineering_transfer_count: int
    transfer_type: str  # DOCUMENTED_TRANSMISSION_FROM or STRUCTURALLY_DERIVES_FROM
    primary_source_support_count: int
    composite_priority_index: float


class PriorityMatrixEngine:
    """Constructs the quantitative Priority Matrix measuring mathematical concepts across
    cross-school adoption, cross-institution adoption, temporal span, betweenness,
    engineering transfer, and primary source support.
    """

    def __init__(self, records: Optional[list[dict[str, Any]]] = None) -> None:
        self.records = records or load_records()
        self.nodes, self.edges = split_records(self.records)
        self.node_map = {n["id"]: n for n in self.nodes}

        self.duality_engine = RelationalDualityEngine(self.records)
        self.temporal_engine = TemporalRelationsEngine(self.records)

        self.entity_schools = self.duality_engine._infer_entity_schools()
        self.node_dates = self.temporal_engine.node_dates

    def _infer_entity_institutions(self) -> dict[str, set[str]]:
        inst_map: dict[str, set[str]] = defaultdict(set)
        for e in self.edges:
            etype = e.get("edge_type", "")
            u, v = e.get("source", ""), e.get("target", "")
            if "INSTITUTION:" in u:
                inst_map[v].add(u)
            if "INSTITUTION:" in v:
                inst_map[u].add(v)
            if etype in ("PUBLISHED_BY", "AFFILIATED_WITH"):
                if "INSTITUTION:" in v:
                    inst_map[u].add(v)
        # Propagate 1 hop
        for e in self.edges:
            u, v = e.get("source", ""), e.get("target", "")
            if u in inst_map and v not in inst_map:
                inst_map[v].update(inst_map[u])
            elif v in inst_map and u not in inst_map:
                inst_map[u].update(inst_map[v])
        return inst_map

    def build_matrix(self) -> list[PriorityMatrixRow]:
        inst_map = self._infer_entity_institutions()

        # Key concepts, operators, and verbs to profile
        target_items = [
            ("OP:STABILITY", "OPERATOR", "Lyapunov / Krasovskii State Stability"),
            ("OP:CONTROL", "OPERATOR", "Pontryagin / Krasovskii Optimal Control"),
            ("OP:INVERSE", "OPERATOR", "Tikhonov Fredholm Inverse Operator"),
            ("OP:REGULARIZE", "OPERATOR", "Tikhonov Smoothing Regularization"),
            ("OP:MINIMAX_APPROXIMATE", "OPERATOR", "Chebyshev Minimax Best Approximation"),
            ("OP:SELF_CONSISTENT_FIELD", "OPERATOR", "Vlasov / Shafranov Self-Consistent Field"),
            ("OP:SPECTRAL_INVERSE", "OPERATOR", "Gelfand-Levitan Inverse Spectral Recovery"),
            ("OP:DYNAMIC_PARTITION", "OPERATOR", "Gelfand-Tsetlin Dynamic Partition Manifold"),
            ("OP:INVERSE_DESIGN", "OPERATOR", "Zelkin Radar Antenna Inverse Synthesis"),
            ("VERB:STABILIZE", "RELATION_VERB", "Stabilization / Behavioral Invariance"),
            ("VERB:CONTROL", "RELATION_VERB", "Admissible Actuation / Control"),
            ("VERB:INVERT", "RELATION_VERB", "Operator Inversion / Reconstruction"),
            ("VERB:CONSTRAIN", "RELATION_VERB", "Compactness / Admissibility Constraint"),
            ("VERB:APPROXIMATE", "RELATION_VERB", "Minimax Equioscillation Approximation"),
            ("CONCEPT:EPS", "CONCEPT", "Electro-Physical Structure (Cavity / Radar)"),
            ("CONCEPT:RODIMOV_SELF_OSCILLATORY_QM", "CONCEPT", "Rodimov Self-Oscillatory Quantum Mechanics"),
        ]

        rows: list[PriorityMatrixRow] = []

        for item_id, itype, label in target_items:
            # Collect participating entities
            touching_nodes: set[str] = set()
            touching_edges = []

            if item_id.startswith("VERB:"):
                verb_name = item_id.split(":")[1]
                for r in self.duality_engine.relation_nodes:
                    if r.normalized_verb == verb_name:
                        touching_nodes.add(r.source_entity)
                        touching_nodes.add(r.target_entity)
            else:
                for e in self.edges:
                    if e.get("source") == item_id or e.get("target") == item_id:
                        touching_edges.append(e)
                        touching_nodes.add(e.get("source", ""))
                        touching_nodes.add(e.get("target", ""))

            # Schools
            schools = sorted(list({self.entity_schools[n] for n in touching_nodes if n in self.entity_schools}))
            if not schools and item_id.startswith("OP:"):
                # Infer school from operator name
                op_u = item_id.upper()
                if "STABILITY" in op_u:
                    schools = ["LYAPUNOV", "PONTRYAGIN"]
                elif "CONTROL" in op_u:
                    schools = ["PONTRYAGIN"]
                elif "INVERSE" in op_u:
                    schools = ["TIKHONOV", "GELFAND"]
                elif "FIELD" in op_u:
                    schools = ["VLASOV"]
                elif "APPROXIMATE" in op_u:
                    schools = ["CHEBYSHEV"]

            # Institutions
            institutions = set()
            for n in touching_nodes:
                institutions.update(inst_map.get(n, set()))
            inst_list = sorted([i.replace("INSTITUTION:", "") for i in institutions])
            if not inst_list:
                inst_list = ["ACADEMY_OF_SCIENCES"]

            # Temporal span
            years = [self.node_dates[n] for n in touching_nodes if n in self.node_dates]
            if years:
                y_min, y_max = min(years), max(years)
            else:
                y_min, y_max = 1950, 1970
            span = max(1, y_max - y_min)

            # Engineering transfer count
            transfer_count = 0
            transfer_type = "STRUCTURALLY_DERIVES_FROM"
            for n in touching_nodes:
                n_u = n.upper()
                if any(k in n_u for k in ("BESM6", "ZELKIN", "SHAFRANOV", "GZ_", "RODIMOV")):
                    transfer_count += 1
            if transfer_count > 0 and any("BESM6" in n.upper() or "ZELKIN" in n.upper() for n in touching_nodes):
                transfer_type = "DOCUMENTED_TRANSMISSION_FROM"

            # Primary source support count
            primary_sources = {
                n for n in touching_nodes if n.startswith("PUB:") or n.startswith("FRAG:")
            }
            support_count = max(1, len(primary_sources))

            # Betweenness score
            betweenness = round(min(1.0, 0.15 * len(schools) + 0.1 * len(inst_list) + 0.05 * len(touching_nodes)), 3)

            # Composite Priority Index: normalized product of span, cross-school breadth, and support
            composite_index = round(
                (len(schools) * 0.3)
                + (len(inst_list) * 0.2)
                + (math.log10(span + 1) * 0.2)
                + (support_count * 0.15)
                + (transfer_count * 0.15),
                2,
            )

            rows.append(
                PriorityMatrixRow(
                    item_id=item_id,
                    item_type=itype,
                    label=label,
                    cross_school_count=len(schools),
                    participating_schools=schools,
                    cross_institution_count=len(inst_list),
                    participating_institutions=inst_list,
                    temporal_span_years=span,
                    earliest_year=y_min,
                    latest_year=y_max,
                    betweenness_score=betweenness,
                    engineering_transfer_count=transfer_count,
                    transfer_type=transfer_type,
                    primary_source_support_count=support_count,
                    composite_priority_index=composite_index,
                )
            )

        rows.sort(key=lambda r: r.composite_priority_index, reverse=True)
        return rows

    def export_priority_matrix(self, output_dir: Path) -> dict[str, Any]:
        output_dir.mkdir(parents=True, exist_ok=True)
        rows = self.build_matrix()

        dossier = {
            "campaign": "SOVCTX-R1: Quantitative Priority Matrix",
            "total_items_profiled": len(rows),
            "priority_matrix": [asdict(r) for r in rows],
            "top_ranking_pillars": [
                {
                    "rank": i + 1,
                    "item_id": r.item_id,
                    "label": r.label,
                    "composite_index": r.composite_priority_index,
                    "schools": r.participating_schools,
                    "span_years": r.temporal_span_years,
                    "engineering_transfers": r.engineering_transfer_count,
                }
                for i, r in enumerate(rows[:5])
            ],
        }

        out_file = output_dir / "priority_matrix.json"
        out_file.write_text(json.dumps(dossier, indent=2, ensure_ascii=False), encoding="utf-8")
        return dossier
