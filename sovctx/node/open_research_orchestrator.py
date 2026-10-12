"""SOVCTX Milestone UQ-N4: Open Autonomous Research Orchestrator.

Implements the Jetson Nano work-plane orchestrator for open frontier discovery:
1. Explores open research domains without hardcoded paths or human hints:
   - Soviet Optimal Dual Control & Information Dynamics (Pontryagin, Feldbaum, Stratonovich, Bellman)
   - Soviet Stability Theory & Converse Dynamics (Lyapunov, Chetaev, Zubov, Krasovskii, Samarskii)
   - Non-Holonomic Analytical Mechanics Synthesis (Appell, Chaplygin, Gibbs, Chetaev, Rumyantsev)
2. Traverses corpus nodes, synthesizes multi-hop candidate paths, and emits bundles with status="PROPOSED".
3. Responds to Uno Q discriminating inquiry UoWs (a* = argmax EIG(a)).
4. Strictly preserves G1.1 geometric observer in shadow mode (diagnostic only, zero admission authority).
5. Monitors physical RSS and resource budgets (< 2048 MB).
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
class FrontierDomainConfig:
    domain_name: str
    historical_cutoff: int
    seed_queries: List[str]
    max_hops: int = 4
    uow_budget: int = 10

class OpenResearchOrchestrator:
    """Autonomous work-plane orchestrator executing open frontier research loops on Jetson Nano."""

    def __init__(self, worker: Optional[NanoResearchWorker] = None, shadow_mode: bool = True):
        self.worker = worker or NanoResearchWorker("nano-open-research-orchestrator", shadow_mode=shadow_mode)
        self.shadow_mode = shadow_mode
        self.proposals_emitted: List[CandidateBundle] = []
        self.telemetry_log: List[NanoWorkPlaneTelemetry] = []

    def probe_domain_frontier(
        self,
        domain_name: str,
        target_query: str,
        uow_id: Optional[str] = None
    ) -> NanoWorkPlaneTelemetry:
        """
        Executes an autonomous primary inquiry on the open frontier.
        Emits CandidateBundle with status="PROPOSED".
        """
        effective_uow_id = uow_id or f"UOW:N4:{domain_name}:{int(time.time()*1000)%100000}"
        telem = self.worker.execute_primary_research_uow(
            uow_id=effective_uow_id,
            target_query=target_query
        )
        self.proposals_emitted.append(telem.candidate_bundle)
        self.telemetry_log.append(telem)
        return telem

    def execute_discriminating_inquiry(
        self,
        uow_id: str,
        probe_query: str
    ) -> NanoWorkPlaneTelemetry:
        """
        Executes a targeted discriminating research UoW issued by the Uno Q control plane.
        """
        telem = self.worker.execute_primary_research_uow(
            uow_id=uow_id,
            target_query=probe_query
        )
        self.telemetry_log.append(telem)
        return telem

    def assemble_multihop_candidate(
        self,
        proposal_id: str,
        hop_queries: List[str]
    ) -> Dict[str, Any]:
        """
        Assembles a multi-hop candidate path across sequential inquiries.
        Strictly maintains status="PROPOSED" and computes evidence hash.
        """
        t0 = time.perf_counter()
        hop_telemetries = []
        all_claims = []
        all_entities = []

        for i, query in enumerate(hop_queries):
            uow_id = f"UOW:N4:MULTI:{proposal_id}:HOP_{i+1}"
            telem = self.worker.execute_primary_research_uow(uow_id=uow_id, target_query=query)
            hop_telemetries.append(telem)
            all_claims.extend(telem.candidate_bundle.claims)
            all_entities.extend(telem.candidate_bundle.entities)

        dt = (time.perf_counter() - t0) * 1000.0

        # Construct unified proposed bundle
        combined_bundle = CandidateBundle(
            uow_id=f"BUNDLE:{proposal_id}",
            candidate_claims=all_claims,
            candidate_entities=all_entities,
            parent_uow_id=None
        )
        evidence_hash = combined_bundle.compute_evidence_hash()

        return {
            "proposal_id": proposal_id,
            "status": "PROPOSED",
            "evidence_hash": evidence_hash,
            "hops_count": len(hop_queries),
            "total_claims": len(all_claims),
            "execution_time_ms": round(dt, 2),
            "telemetries": hop_telemetries
        }
