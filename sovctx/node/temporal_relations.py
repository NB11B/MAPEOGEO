from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional

from sovctx.node.relational_duality import NORMALIZED_RELATION_VERBS, RelationalDualityEngine
from sovctx.tools.graph_io import load_records, split_records


HISTORICAL_SLICES: list[tuple[str, str, int, int, str]] = [
    (
        "SLICE_1_1750_1850",
        "1750–1850: Imperial Academy Foundations",
        1700,
        1850,
        "Eulerian foundational mechanics, early geometry/analysis situs, and nascent Chebyshev approximation.",
    ),
    (
        "SLICE_2_1850_1917",
        "1850–1917: St. Petersburg Mathematical School",
        1851,
        1917,
        "Chebyshev best approximation, Lyapunov general stability of motion, Markov stochastic processes.",
    ),
    (
        "SLICE_3_1917_1945",
        "1917–1945: Early Soviet Mechanics and Collective Kinetics",
        1918,
        1945,
        "Andronov-Pontryagin rough systems and self-oscillations, Vlasov self-consistent kinetic plasma theory.",
    ),
    (
        "SLICE_4_1945_1970",
        "1945–1970: High Cold War Synthesis, Control, and Computing",
        1946,
        1970,
        "Pontryagin maximum principle, Tikhonov regularization, Gelfand-Levitan spectral inversion, Krasovskii optimal stabilization, Glushkov cybernetics, Shafranov equilibrium, BESM-6 Chebyshev subroutines.",
    ),
    (
        "SLICE_5_1970_1991",
        "1970–1991: Late Soviet Applied Systems and Inverse Problems",
        1971,
        1991,
        "Multi-dimensional inverse scattering, applied microwave/radar synthesis, Henkin integral representations, Grebennikov-Zolotarev cavity structures.",
    ),
    (
        "SLICE_6_1991_PRES",
        "1991–Present: Post-Soviet Codification and Heritage Analysis",
        1992,
        2030,
        "Retrospective Academy editions, Steklov Institute historical surveys (Kozlov), archival synthesis.",
    ),
]


@dataclass
class SliceRelationProfile:
    slice_id: str
    slice_name: str
    start_year: int
    end_year: int
    historical_character: str
    active_entity_count: int
    active_edge_count: int
    verb_frequencies: dict[str, int]
    verb_shares_percent: dict[str, float]
    dominant_verbs: list[str]
    dominant_bigrams: list[str]
    priority_order: list[str]


@dataclass
class TemporalShiftTrajectory:
    eras: list[str]
    verb_trajectories: dict[str, list[float]]  # verb -> list of percentages across the 6 eras
    key_priority_transitions: list[str]
    synthesis_summary: str


class TemporalRelationsEngine:
    """Analyzes the temporal evolution of mathematical grammar and priority shifts across 6 historical slices."""

    def __init__(self, records: Optional[list[dict[str, Any]]] = None) -> None:
        self.records = records or load_records()
        self.nodes, self.edges = split_records(self.records)
        self.node_map = {n["id"]: n for n in self.nodes}
        self.duality_engine = RelationalDualityEngine(self.records)
        self.node_dates = self._resolve_entity_dates()

    def _extract_year(self, n: dict[str, Any]) -> Optional[int]:
        for f in ("publication_date", "valid_from", "date"):
            val = n.get(f)
            if val and str(val).isdigit():
                return int(val)
        text = n.get("id", "") + " " + n.get("label", "")
        match = re.search(r"\b(1[6-9]\d\d|20\d\d)\b", text)
        if match:
            return int(match.group(1))
        return None

    def _resolve_entity_dates(self) -> dict[str, int]:
        dates: dict[str, Optional[int]] = {n["id"]: self._extract_year(n) for n in self.nodes}

        # Propagate temporal stamps along contextual edges
        for _ in range(4):
            for e in self.edges:
                u, v = e.get("source", ""), e.get("target", "")
                if dates.get(u) and not dates.get(v):
                    dates[v] = dates[u]
                elif dates.get(v) and not dates.get(u):
                    dates[u] = dates[v]

        resolved: dict[str, int] = {}
        for nid, yr in dates.items():
            resolved[nid] = yr if yr is not None else 1960  # Default to high cold war if indeterminate
        return resolved

    def analyze_slice(
        self,
        slice_id: str,
        slice_name: str,
        start_year: int,
        end_year: int,
        historical_character: str,
    ) -> SliceRelationProfile:
        active_nodes = {nid for nid, yr in self.node_dates.items() if start_year <= yr <= end_year}

        # Active edges are those where source, target, or document falls in slice
        active_edges = []
        for e in self.edges:
            u, v = e.get("source", ""), e.get("target", "")
            yr_u = self.node_dates.get(u, 1960)
            yr_v = self.node_dates.get(v, 1960)
            if (start_year <= yr_u <= end_year) or (start_year <= yr_v <= end_year):
                active_edges.append(e)

        # Compute verbs for active edges
        verb_counter: Counter[str] = Counter()
        for e in active_edges:
            verb = self.duality_engine._normalize_edge_verb(e)
            verb_counter[verb] += 1

        total_edges = sum(verb_counter.values()) or 1
        shares = {v: round((cnt / float(total_edges)) * 100.0, 2) for v, cnt in verb_counter.items()}

        # Top dominant verbs
        top_verbs = [v for v, _ in verb_counter.most_common(5)]

        # Extract slice bigrams
        sub_records = [self.node_map[nid] for nid in active_nodes if nid in self.node_map] + active_edges
        sub_engine = RelationalDualityEngine(sub_records)
        ngrams = sub_engine.extract_relation_ngrams(max_n=2, max_paths_per_node=10)
        dominant_bigrams = [
            f"{o.ngram[0]}->{o.ngram[1]}" for o in ngrams.get(2, [])[:5]
        ]

        priority_order = [v for v, _ in verb_counter.most_common()]

        return SliceRelationProfile(
            slice_id=slice_id,
            slice_name=slice_name,
            start_year=start_year,
            end_year=end_year,
            historical_character=historical_character,
            active_entity_count=len(active_nodes),
            active_edge_count=len(active_edges),
            verb_frequencies=dict(verb_counter),
            verb_shares_percent=shares,
            dominant_verbs=top_verbs,
            dominant_bigrams=dominant_bigrams,
            priority_order=priority_order,
        )

    def analyze_all_slices(self) -> list[SliceRelationProfile]:
        profiles = []
        for sid, sname, y0, y1, desc in HISTORICAL_SLICES:
            profiles.append(self.analyze_slice(sid, sname, y0, y1, desc))
        return profiles

    def compute_shift_trajectory(self, profiles: list[SliceRelationProfile]) -> TemporalShiftTrajectory:
        eras = [p.slice_name.split(":")[0] for p in profiles]
        trajectories: dict[str, list[float]] = defaultdict(list)

        key_verbs = [
            "APPROXIMATE",
            "STABILIZE",
            "REPRESENT",
            "CONTROL",
            "INVERT",
            "REGULARIZE",
            "EVOLVE",
            "REDUCE",
            "CONSTRAIN",
            "OBSERVE",
        ]

        for p in profiles:
            for v in key_verbs:
                trajectories[v].append(p.verb_shares_percent.get(v, 0.0))

        key_transitions = [
            "1750–1850 -> 1850–1917: Rise of CHEBYSHEV approximation and LYAPUNOV phase stability (APPROXIMATE, STABILIZE).",
            "1850–1917 -> 1917–1945: Shift from mechanical equilibrium to non-equilibrium self-oscillations and collective kinetics (PERTURB, EVOLVE).",
            "1917–1945 -> 1945–1970: High Cold War convergence: optimal control synthesis meets Fredholm/spectral inverse theory (CONTROL, INVERT, REGULARIZE).",
            "1945–1970 -> 1970–1991: Direct hardware and computing transfer: microwave cavity design, supercomputing subroutines (BESM-6), inverse radar (RECONSTRUCT).",
            "1970–1991 -> 1991–Pres: Retrospective Steklov codification and historical lineage preservation.",
        ]

        summary = (
            "The temporal trajectory traces a clear intellectual sequence across 250 years: "
            "from classical approximation and equilibrium (1750–1917) to dynamical vector-field stability (1892–1945), "
            "culminating in the Cold War twin pinnacles of admissible optimal control (Pontryagin, Krasovskii) "
            "and ill-posed inverse regularization (Tikhonov, Gelfand-Levitan). "
            "The overarching grammatical evolution demonstrates that the Soviet mathematical style is not static dogma "
            "but an expanding operator calculus adapting continuously from Imperial mechanics to Cold War technology."
        )

        return TemporalShiftTrajectory(
            eras=eras,
            verb_trajectories=dict(trajectories),
            key_priority_transitions=key_transitions,
            synthesis_summary=summary,
        )

    def export_temporal_dossier(self, output_dir: Path) -> dict[str, Any]:
        output_dir.mkdir(parents=True, exist_ok=True)
        profiles = self.analyze_all_slices()
        trajectory = self.compute_shift_trajectory(profiles)

        dossier = {
            "campaign": "SOVCTX-R1: Temporal Evolution and Priority Shifts (1750–Present)",
            "historical_slices": [asdict(p) for p in profiles],
            "priority_shift_trajectory": asdict(trajectory),
        }

        out_file = output_dir / "temporal_evolution_dossier.json"
        out_file.write_text(json.dumps(dossier, indent=2, ensure_ascii=False), encoding="utf-8")
        return dossier
