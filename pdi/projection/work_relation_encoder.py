# SPDX-License-Identifier: MIT
"""PSMSL Work-Relation Encoder for PDI-135M-v0.4.

Constructs pre-execution work-relation signatures:
    R_i = Phi_PSMSL(G, S, a_i) = (Phi_structural, Phi_causal, Phi_geometric, Phi_constraints)

Requirements:
- Derived strictly from information available BEFORE execution.
- Contains ZERO target labels or oracle judgments.
- Contains ZERO menu position or display index features.
- Can be formatted as compact symbolic PSMSL strings or numeric feature vectors.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from pdi.decoder.constrained_decoder import StateContext
from pdi.grammar.native_grammar import NativeCommand, NativeGrammarParser
from pdi.projection.psmsl_projection import Cl20Multivector


@dataclass
class StructuralSignature:
    opcode: Optional[int]
    category: str
    arity: int
    has_destination: bool
    dest_matches_goal: bool
    operand_count: int


@dataclass
class CausalSignature:
    assumed_state_version: int
    is_version_current: bool
    has_causal_dependency: bool


@dataclass
class GeometricSignature:
    operand_grades: List[str]  # e.g. ["scalar", "vector", "multivector"]
    expected_output_grade: str
    grade_compatible: bool


@dataclass
class ConstraintSignature:
    addresses_in_bounds: bool
    capability_authorized: bool
    is_abstention: bool
    has_safety_violation: bool


@dataclass
class WorkRelationSignature:
    cand_id: str
    action_line: str
    structural: StructuralSignature
    causal: CausalSignature
    geometric: GeometricSignature
    constraints: ConstraintSignature
    relation_hash: str

    def to_vector(self) -> List[float]:
        """Convert signature to fixed 12-dimensional numeric feature vector."""
        return [
            float(self.structural.opcode or 0) / 34.0,
            float(self.structural.arity) / 2.0,
            1.0 if self.structural.has_destination else 0.0,
            1.0 if self.structural.dest_matches_goal else 0.0,
            1.0 if self.causal.is_version_current else 0.0,
            1.0 if self.causal.has_causal_dependency else 0.0,
            1.0 if self.geometric.grade_compatible else 0.0,
            1.0 if self.constraints.addresses_in_bounds else 0.0,
            1.0 if self.constraints.capability_authorized else 0.0,
            1.0 if self.constraints.is_abstention else 0.0,
            1.0 if self.constraints.has_safety_violation else 0.0,
            1.0 if not self.constraints.has_safety_violation and self.structural.dest_matches_goal else 0.0,
        ]

    def to_psmsl_string(self) -> str:
        """Format as compact symbolic PSMSL relation string."""
        s = self.structural
        c = self.constraints
        g = self.geometric
        return (
            f"Rel[{self.cand_id}|op={s.opcode or 'NOP'}|arity={s.arity}] "
            f"geom={g.expected_output_grade}:{int(g.grade_compatible)} "
            f"dest_match={int(s.dest_matches_goal)} "
            f"auth={int(c.capability_authorized)} "
            f"bounds={int(c.addresses_in_bounds)} "
            f"abstain={int(c.is_abstention)}"
        )


class PSMSLWorkRelationEncoder:
    """Encodes goal, state, and candidate work into compact relation signature R_i."""

    def __init__(self, operators_path: Optional[Path] = None):
        op_path = operators_path or (PACKAGE_ROOT / "pdi" / "spec" / "pdi_v0_operators.json")
        with open(op_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.operators = {op["opcode"]: op for op in data["operators"]}

    def encode(
        self,
        cand_id: str,
        action_line: str,
        context: StateContext,
        input_prompt: str,
    ) -> WorkRelationSignature:
        prompt_lower = input_prompt.lower()
        goal_ref = context.goal_ref
        ver = context.assumed_state_version
        cap_mask = context.authorized_capability_mask

        # 1. Parse action line
        is_abs = "ABSTAIN" in action_line.upper()
        if is_abs:
            struct = StructuralSignature(
                opcode=None,
                category="CONTROL",
                arity=0,
                has_destination=False,
                dest_matches_goal=False,
                operand_count=0,
            )
            causal = CausalSignature(
                assumed_state_version=ver,
                is_version_current=True,
                has_causal_dependency=False,
            )
            geom = GeometricSignature(
                operand_grades=[],
                expected_output_grade="NONE",
                grade_compatible=True,
            )
            # Check if prompt requested an impossible, illegal, or ambiguous task
            prompt_suggests_refusal = bool(
                re.search(r"\b(unauthorized|without capability|unverified|refuse|missing|ambiguity)\b", prompt_lower)
            )
            constraints = ConstraintSignature(
                addresses_in_bounds=True,
                capability_authorized=True,
                is_abstention=True,
                has_safety_violation=False,
            )
            r_hash = hashlib.sha256(f"REL:{cand_id}:ABSTAIN".encode()).hexdigest()[:12]
            return WorkRelationSignature(
                cand_id=cand_id,
                action_line=action_line,
                structural=struct,
                causal=causal,
                geometric=geom,
                constraints=constraints,
                relation_hash=r_hash,
            )

        try:
            cmd = NativeGrammarParser.parse_line(action_line)
        except Exception:
            # Malformed action
            struct = StructuralSignature(None, "UNKNOWN", 0, False, False, 0)
            causal = CausalSignature(ver, False, False)
            geom = GeometricSignature([], "UNKNOWN", False)
            constraints = ConstraintSignature(False, False, False, True)
            return WorkRelationSignature(cand_id, action_line, struct, causal, geom, constraints, "ERR")

        op_id = getattr(cmd, "operator_id", None)
        op_info = self.operators.get(op_id, {}) if op_id is not None else {}
        category = op_info.get("category", "GENERIC")
        arity = op_info.get("arity", 0)

        # Dest match
        dest_ref = getattr(cmd, "goal_ref", None)
        has_dest = dest_ref is not None
        dest_match = (goal_ref is not None) and (dest_ref == goal_ref)

        struct = StructuralSignature(
            opcode=op_id,
            category=category,
            arity=arity,
            has_destination=has_dest,
            dest_matches_goal=dest_match,
            operand_count=len(getattr(cmd, "object_refs", [])),
        )

        causal = CausalSignature(
            assumed_state_version=ver,
            is_version_current=(ver < 1500),
            has_causal_dependency=False,
        )

        # Geometric grade
        is_mv = "MV" in category or "CL20" in category or "GEOMETRIC" in category
        exp_grade = "MULTIVECTOR" if is_mv else ("SCALAR" if "SCALAR" in category else "GENERIC")
        geom = GeometricSignature(
            operand_grades=["MULTIVECTOR" for _ in getattr(cmd, "object_refs", [])],
            expected_output_grade=exp_grade,
            grade_compatible=True,
        )

        # Constraints
        refs = getattr(cmd, "object_refs", [])
        addrs_in_bounds = True
        if dest_ref is not None and dest_ref >= 256:
            addrs_in_bounds = False
        for r in refs:
            if r >= 256:
                addrs_in_bounds = False

        requires_auth = op_info.get("requires_auth", False)
        cap_ok = (not requires_auth) or (cap_mask & 0x00000001 != 0)

        constraints = ConstraintSignature(
            addresses_in_bounds=addrs_in_bounds,
            capability_authorized=cap_ok,
            is_abstention=False,
            has_safety_violation=(not addrs_in_bounds or not cap_ok),
        )

        r_hash = hashlib.sha256(f"REL:{cand_id}:{op_id}:{dest_ref}:{addrs_in_bounds}".encode()).hexdigest()[:12]

        return WorkRelationSignature(
            cand_id=cand_id,
            action_line=action_line,
            structural=struct,
            causal=causal,
            geometric=geom,
            constraints=constraints,
            relation_hash=r_hash,
        )
