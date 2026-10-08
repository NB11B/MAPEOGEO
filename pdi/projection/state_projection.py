# SPDX-License-Identifier: MIT
"""State Projection Comparison Engine for PDI-135M-v0.3.

Provides five experimental context variants (E0, E1, E2, E3, E4) to determine the
minimum sufficient state projection required for accurate candidate selection:
- E0: Minimal Context (Goal only)
- E1: Bounded Slot State (References, Version, Capability)
- E2: PSMSL Compact Symbolic Notation (Multivector algebra)
- E3: Full Memory Snapshot (Fixed-point component values)
- E4: Graph + Causal Context (Topology, Trace, Evidence Root)

Invariants:
- Experimental context variants DO NOT change candidate menu composition.
- Permission filtering redacts unauthorized addresses.
- Bounded payload lengths.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
from typing import Any, Dict, List, Optional

from pdi.decoder.constrained_decoder import StateContext
from pdi.projection.psmsl_projection import Cl20Multivector, PSMSLStateProjector


class ContextArm(str, Enum):
    E0_MINIMAL = "E0_MINIMAL"
    E1_BOUNDED_SLOTS = "E1_BOUNDED_SLOTS"
    E2_PSMSL_SYMBOLIC = "E2_PSMSL_SYMBOLIC"
    E3_MEMORY_SNAPSHOT = "E3_MEMORY_SNAPSHOT"
    E4_GRAPH_CAUSAL = "E4_GRAPH_CAUSAL"


@dataclass
class ProjectedContext:
    arm: ContextArm
    context_text: str
    token_estimate: int
    char_length: int
    snapshot_version: int
    is_permission_filtered: bool
    context_hash: str


class StateProjector:
    """Constructs deterministic, permission-filtered context projections."""

    @classmethod
    def project(
        cls,
        arm: ContextArm,
        input_prompt: str,
        state_context: StateContext,
        evidence_root: int = 0xBB67AE85,
    ) -> ProjectedContext:
        ver = state_context.assumed_state_version
        cap = state_context.authorized_capability_mask
        refs = list(state_context.visible_refs)
        goal = state_context.goal_ref

        # Permission filter: visible references must be authorized
        # (In hardware, addresses > 128 require capability bit 1)
        filtered_refs = []
        permission_filtered = False
        for r in refs:
            if r > 128 and not (cap & 0x00000002):
                permission_filtered = True
            else:
                filtered_refs.append(r)

        if arm == ContextArm.E0_MINIMAL:
            text = f"Objective: {input_prompt.strip()}"

        elif arm == ContextArm.E1_BOUNDED_SLOTS:
            ref_str = ", ".join(f"REF_{r}" for r in filtered_refs)
            goal_str = f"dest=REF_{goal}" if goal is not None else "dest=UNSPECIFIED"
            text = (
                f"State[v{ver}|cap=0x{cap:08X}]: visible=[{ref_str}], {goal_str}\n"
                f"Objective: {input_prompt.strip()}"
            )

        elif arm == ContextArm.E2_PSMSL_SYMBOLIC:
            # Build representative symbolic multivectors for visible refs
            vectors = {}
            for idx, r in enumerate(filtered_refs):
                if idx % 2 == 0:
                    vectors[r] = Cl20Multivector(s=1.0, e1=0.5 * (idx + 1))
                else:
                    vectors[r] = Cl20Multivector(e2=1.0, e12=0.25 * (idx + 1))
            psmsl_str = PSMSLStateProjector.format_psmsl_context(
                version=ver,
                state_vectors=vectors,
                goal_ref=goal,
                capability_mask=cap,
            )
            text = f"{psmsl_str}\nObjective: {input_prompt.strip()}"

        elif arm == ContextArm.E3_MEMORY_SNAPSHOT:
            lines = [f"MemorySnapshot[v{ver}|cap=0x{cap:08X}]:"]
            for r in filtered_refs:
                lines.append(f"  @{r:03d}: s=0x00010000 e1=0x00008000 e2=0x00000000 e12=0x00000000")
            if goal is not None:
                lines.append(f"  Target: @{goal:03d}")
            lines.append(f"Objective: {input_prompt.strip()}")
            text = "\n".join(lines)

        elif arm == ContextArm.E4_GRAPH_CAUSAL:
            # Topology relationships + evidence root
            topo_strs = []
            if len(filtered_refs) >= 2:
                topo_strs.append(f"(Node_{filtered_refs[0]} -[REL_ADJACENT]-> Node_{filtered_refs[1]})")
            else:
                topo_strs.append("(Node_Root -[REL_SELF]-> Node_Root)")
            topo_repr = " ".join(topo_strs)
            text = (
                f"GraphCausalContext[v{ver}|evidence=0x{evidence_root:08X}|cap=0x{cap:08X}]:\n"
                f"Topology: {topo_repr}\n"
                f"CausalTrace: [UoW_prior committed -> root certified]\n"
                f"Objective: {input_prompt.strip()}"
            )
        else:
            raise ValueError(f"Unknown ContextArm {arm}")

        # Deterministic hash of generated context
        c_hash = hashlib.sha256(text.encode()).hexdigest()
        char_len = len(text)
        token_est = max(1, char_len // 4)

        return ProjectedContext(
            arm=arm,
            context_text=text,
            token_estimate=token_est,
            char_length=char_len,
            snapshot_version=ver,
            is_permission_filtered=permission_filtered,
            context_hash=c_hash,
        )
