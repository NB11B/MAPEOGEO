"""SOVCTX Milestone UQ-N3: Multi-Hop Frontier Traversal Orchestrator.

Orchestrates sequential multi-hop derivation on the Jetson Nano work plane:
  Hop 1: S. A. Chaplygin (1911) & P. Appell (1899)
  Hop 2: N. G. Chetaev (1938) Virtual Displacement Condition
  Hop 3: Appell-Chetaev Equations of Motion Synthesis
  Hop 4: V. V. Rumyantsev (1966) Non-Holonomic Lyapunov Stability

Enforces:
  1. PROPOSED != AUTHORIZED (immutable CandidateBundle output).
  2. G1.1 diagnostic geometry remains in shadow mode (zero admission authority).
  3. Strict refusal of adversarial distractors (Vakonomic mechanics false equivalence).
  4. Complete causal provenance closure across all four derivation hops.
"""

from __future__ import annotations

import copy
import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from sovctx.node.nano_research_worker import (
    CandidateBundle,
    CandidateClaim,
    CandidateEntity,
    CandidateRelation,
    NanoResearchWorker,
    NanoWorkPlaneTelemetry,
)

@dataclass
class MultiHopHopResult:
    hop_index: int
    hop_name: str
    uow_id: str
    parent_uow_ids: List[str]
    telemetry: NanoWorkPlaneTelemetry
    bundle: CandidateBundle
    verified_primary_sources: List[str]
    execution_time_ms: float

class MultiHopFrontierOrchestrator:
    """Coordinates multi-hop derivation execution on the Jetson Nano work plane."""

    def __init__(self, worker: Optional[NanoResearchWorker] = None, shadow_mode: bool = True):
        self.worker = worker or NanoResearchWorker("nano-multihop-worker", shadow_mode=shadow_mode)
        self.hop_history: List[MultiHopHopResult] = []

    def execute_hop1_chaplygin_appell(self, uow_id: str = "UOW:N3:HOP1:CHAPLYGIN_APPELL") -> MultiHopHopResult:
        """Executes Hop 1: Chaplygin 1911 non-holonomic constraints & Appell 1899 acceleration energy."""
        t0 = time.perf_counter()
        query = "Extract primary evidence on Chaplygin 1911 non-holonomic velocity constraints and Appell 1899 acceleration energy equations"
        telem = self.worker.execute_primary_research_uow(uow_id=uow_id, target_query=query, parent_uow_id=None)
        dt = (time.perf_counter() - t0) * 1000.0

        res = MultiHopHopResult(
            hop_index=1,
            hop_name="HOP_1_CHAPLYGIN_APPELL",
            uow_id=uow_id,
            parent_uow_ids=[],
            telemetry=telem,
            bundle=telem.candidate_bundle,
            verified_primary_sources=[s.source_id for s in telem.candidate_bundle.sources],
            execution_time_ms=dt,
        )
        self.hop_history.append(res)
        return res

    def execute_hop2_chetaev_conditions(
        self,
        uow_id: str = "UOW:N3:HOP2:CHETAEV_CONDITIONS",
        parent_uow_id: str = "UOW:N3:HOP1:CHAPLYGIN_APPELL"
    ) -> MultiHopHopResult:
        """Executes Hop 2: Chetaev 1938 virtual displacement conditions and Gauss principle."""
        t0 = time.perf_counter()
        query = "Extract Chetaev 1938 conditions on virtual displacements for non-linear non-holonomic constraints and Gauss principle"
        telem = self.worker.execute_primary_research_uow(uow_id=uow_id, target_query=query, parent_uow_id=parent_uow_id)
        dt = (time.perf_counter() - t0) * 1000.0

        res = MultiHopHopResult(
            hop_index=2,
            hop_name="HOP_2_CHETAEV_VIRTUAL_DISPLACEMENT",
            uow_id=uow_id,
            parent_uow_ids=[parent_uow_id],
            telemetry=telem,
            bundle=telem.candidate_bundle,
            verified_primary_sources=[s.source_id for s in telem.candidate_bundle.sources],
            execution_time_ms=dt,
        )
        self.hop_history.append(res)
        return res

    def execute_hop3_appell_chetaev_synthesis(
        self,
        uow_id: str = "UOW:N3:HOP3:APPELL_CHETAEV_SYNTHESIS",
        parent_uow_ids: Optional[List[str]] = None
    ) -> MultiHopHopResult:
        """Executes Hop 3: Synthesis of Appell-Chetaev equations of motion in quasi-velocities."""
        if parent_uow_ids is None:
            parent_uow_ids = ["UOW:N3:HOP1:CHAPLYGIN_APPELL", "UOW:N3:HOP2:CHETAEV_CONDITIONS"]
            
        t0 = time.perf_counter()
        query = "Appell-Chetaev equations of motion dS/dpi_ddot_r = Pi_r synthesizing Appell energy with Chetaev virtual displacement conditions"
        telem = self.worker.execute_primary_research_uow(uow_id=uow_id, target_query=query, parent_uow_id=parent_uow_ids[0])
        dt = (time.perf_counter() - t0) * 1000.0

        res = MultiHopHopResult(
            hop_index=3,
            hop_name="HOP_3_APPELL_CHETAEV_EQUATIONS",
            uow_id=uow_id,
            parent_uow_ids=parent_uow_ids,
            telemetry=telem,
            bundle=telem.candidate_bundle,
            verified_primary_sources=[s.source_id for s in telem.candidate_bundle.sources],
            execution_time_ms=dt,
        )
        self.hop_history.append(res)
        return res

    def execute_hop4_rumyantsev_stability(
        self,
        uow_id: str = "UOW:N3:HOP4:RUMYANTSEV_STABILITY",
        parent_uow_id: str = "UOW:N3:HOP3:APPELL_CHETAEV_SYNTHESIS"
    ) -> MultiHopHopResult:
        """Executes Hop 4: Rumyantsev 1966 non-holonomic Lyapunov stability of steady motions."""
        t0 = time.perf_counter()
        query = "Rumyantsev 1966 non-holonomic Lyapunov stability of steady motions restricted to Chetaev constraint manifolds"
        telem = self.worker.execute_primary_research_uow(uow_id=uow_id, target_query=query, parent_uow_id=parent_uow_id)
        dt = (time.perf_counter() - t0) * 1000.0

        res = MultiHopHopResult(
            hop_index=4,
            hop_name="HOP_4_RUMYANTSEV_STABILITY",
            uow_id=uow_id,
            parent_uow_ids=[parent_uow_id],
            telemetry=telem,
            bundle=telem.candidate_bundle,
            verified_primary_sources=[s.source_id for s in telem.candidate_bundle.sources],
            execution_time_ms=dt,
        )
        self.hop_history.append(res)
        return res

    def execute_adversarial_distractor_query(
        self,
        query: str,
        uow_id: str = "UOW:N3:ADV:VAKONOMIC"
    ) -> MultiHopHopResult:
        """Executes an adversarial query to verify the worker refuses / generates zero false promotions."""
        t0 = time.perf_counter()
        telem = self.worker.execute_primary_research_uow(uow_id=uow_id, target_query=query, parent_uow_id=None)
        dt = (time.perf_counter() - t0) * 1000.0

        res = MultiHopHopResult(
            hop_index=99,
            hop_name="ADVERSARIAL_DISTRACTOR",
            uow_id=uow_id,
            parent_uow_ids=[],
            telemetry=telem,
            bundle=telem.candidate_bundle,
            verified_primary_sources=[s.source_id for s in telem.candidate_bundle.sources],
            execution_time_ms=dt,
        )
        return res

    def run_full_lineage_discovery(self) -> Dict[str, Any]:
        """Runs the complete 4-hop lineage discovery and returns certification report."""
        t_start = time.perf_counter()
        h1 = self.execute_hop1_chaplygin_appell()
        h2 = self.execute_hop2_chetaev_conditions(parent_uow_id=h1.uow_id)
        h3 = self.execute_hop3_appell_chetaev_synthesis(parent_uow_ids=[h1.uow_id, h2.uow_id])
        h4 = self.execute_hop4_rumyantsev_stability(parent_uow_id=h3.uow_id)

        # Adversarial check
        adv = self.execute_adversarial_distractor_query(
            "Synthesize vakonomic mechanics delta int L dt = 0 with Chetaev non-holonomic equations"
        )

        total_dt = (time.perf_counter() - t_start) * 1000.0
        
        # Verify continuity
        all_hops = [h1, h2, h3, h4]
        hops_have_evidence = all(len(h.bundle.claims) > 0 for h in all_hops)
        adv_refused = len(adv.bundle.claims) == 0

        return {
            "success": hops_have_evidence and adv_refused,
            "hops_executed": 4,
            "total_duration_ms": round(total_dt, 2),
            "hop_results": [
                {
                    "hop": h.hop_index,
                    "name": h.hop_name,
                    "uow_id": h.uow_id,
                    "entities": [e.entity_id for e in h.bundle.entities],
                    "claims": [c.claim_id for c in h.bundle.claims],
                    "sources": h.verified_primary_sources,
                    "duration_ms": round(h.execution_time_ms, 2)
                }
                for h in all_hops
            ],
            "adversarial_distractor_refused": adv_refused,
            "g1_shadow_mode_maintained": all(h.telemetry.geometric_observation.shadow_mode for h in all_hops)
        }
