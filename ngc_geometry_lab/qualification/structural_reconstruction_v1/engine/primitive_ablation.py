r"""Primitive Necessity Testing and Single-Ablation Engine for GEO-X2.

For every candidate primitive P_i:
  P -> P \ {P_i}
Tests all 18 targets and records which targets fail, certifying necessity witnesses.
"""
from dataclasses import dataclass, asdict
from typing import Dict, List, Set, Any
import json
import os

from qualification.structural_reconstruction_v1.engine.reconstruction_engine import ReconstructionEngine

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@dataclass(frozen=True)
class PrimitiveNecessityRecord:
    """Certified necessity record for a single primitive."""
    primitive_id: str
    primitive_name: str
    targets_lost_count: int
    targets_lost_ids: List[str]
    is_strictly_necessary: bool
    necessity_witness_target: str
    epistemic_justification: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PrimitiveAblationSuite:
    """Manages single-primitive ablation campaigns."""

    def __init__(self):
        self.engine = ReconstructionEngine()
        prims_path = os.path.join(BASE_DIR, "specification", "primitive_candidates.json")
        with open(prims_path, "r", encoding="utf-8") as fp:
            self.primitives = {p["id"]: p for p in json.load(fp)["primitives"]}

    def run_all_ablations(self) -> Dict[str, PrimitiveNecessityRecord]:
        """Execute single-primitive ablation for each of the 12 candidate primitives."""
        all_pids = set(self.primitives.keys())
        results = {}

        for pid, pdata in self.primitives.items():
            ablated_subset = all_pids - {pid}
            certs = self.engine.reconstruct_all(ablated_subset)
            lost = [tid for tid, c in certs.items() if c.status != "RECONSTRUCTED_EXACT"]

            is_nec = len(lost) > 0
            witness = lost[0] if is_nec else "NONE"
            justification = (
                f"Primitive {pid} ({pdata['name']}) is strictly necessary: removing it causes "
                f"{len(lost)} target failures (e.g. {witness})."
                if is_nec else f"Primitive {pid} is redundant."
            )

            results[pid] = PrimitiveNecessityRecord(
                primitive_id=pid,
                primitive_name=pdata["name"],
                targets_lost_count=len(lost),
                targets_lost_ids=lost,
                is_strictly_necessary=is_nec,
                necessity_witness_target=witness,
                epistemic_justification=justification
            )

        return results
