# SPDX-License-Identifier: MIT
"""PSMSL (Probabilistic-to-Symbolic Multivector State Language) Compact Projection.

Provides dense, token-efficient Cl(2,0) multivector symbolic state notation for LLM context:
Representing scalar, vector, and bivector grades concisely without JSON or raw binary overhead.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Cl20Multivector:
    s: float = 0.0
    e1: float = 0.0
    e2: float = 0.0
    e12: float = 0.0

    def to_psmsl(self) -> str:
        """Format as compact PSMSL string: e.g. '1.5s + 2e1 - 0.5e12'."""
        terms = []
        if self.s != 0.0 or (self.e1 == 0.0 and self.e2 == 0.0 and self.e12 == 0.0):
            terms.append(f"{self.s:g}s")
        if self.e1 != 0.0:
            sign = "+ " if self.e1 > 0 and terms else ("- " if self.e1 < 0 and terms else "")
            val = abs(self.e1)
            terms.append(f"{sign}{val:g}e1")
        if self.e2 != 0.0:
            sign = "+ " if self.e2 > 0 and terms else ("- " if self.e2 < 0 and terms else "")
            val = abs(self.e2)
            terms.append(f"{sign}{val:g}e2")
        if self.e12 != 0.0:
            sign = "+ " if self.e12 > 0 and terms else ("- " if self.e12 < 0 and terms else "")
            val = abs(self.e12)
            terms.append(f"{sign}{val:g}e12")
        return " ".join(terms)


class PSMSLStateProjector:
    """Serializes authorized FPGA multivector memory states into symbolic PSMSL context."""

    @staticmethod
    def format_psmsl_context(
        version: int,
        state_vectors: Dict[int, Cl20Multivector],
        goal_ref: Optional[int] = None,
        capability_mask: int = 0x00000001,
    ) -> str:
        parts = [f"PSMSL[v{version}|cap=0x{capability_mask:X}]"]
        slot_strs = []
        for addr in sorted(state_vectors.keys()):
            mv = state_vectors[addr]
            slot_strs.append(f"@{addr}={mv.to_psmsl()}")
        parts.append("{" + ", ".join(slot_strs) + "}")
        if goal_ref is not None:
            parts.append(f"-> @{goal_ref}")
        return " ".join(parts)
