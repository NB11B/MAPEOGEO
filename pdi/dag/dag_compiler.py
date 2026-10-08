# SPDX-License-Identifier: MIT
"""PDI-135M-v0.7A Phase A1: Composite-Goal DAG Compiler.

Parses high-level geometric expressions into deterministic, topologically ordered
Directed Acyclic Graphs (DAGs) of Unit-of-Work (UoW) operations.

Supported Expression Families:
1. CONTRACTION_WEDGE: (A ^ B) . C
2. COMMUTATOR_BRACKET: [A, B] = A*B - B*A
3. ROTOR_SANDWICH: R * A * ~R
4. SINGLE_STEP: Standard registered unary and binary operators.

Fail-Closed Requirement:
Unsupported expressions (e.g. division, arbitrary polynomials, unresolvable dependencies)
fail-closed immediately with a structured rejection code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import re
from typing import Any, Dict, List, Optional, Set, Tuple

OPCODE_REGISTRY = {
    "OP_NOP": 0,
    "OP_ADD": 1,
    "OP_SUB": 2,
    "OP_MUL": 3,
    "OP_COMPARE": 4,
    "OP_CL20_PRODUCT": 5,
    "OP_REVERSE": 6,
    "OP_GRADE_INVOLUTION": 7,
    "OP_CLIFFORD_CONJUGATE": 8,
    "OP_VECTOR_DOT": 9,
    "OP_VECTOR_WEDGE": 10,
    "OP_COMMUTATOR": 11,
    "OP_ANTICOMMUTATOR": 12,
}


class ExpressionFamily(str, Enum):
    CONTRACTION_WEDGE = "CONTRACTION_WEDGE"      # (A ^ B) . C
    COMMUTATOR_BRACKET = "COMMUTATOR_BRACKET"    # [A, B] = A*B - B*A
    ROTOR_SANDWICH = "ROTOR_SANDWICH"            # R * A * ~R
    SINGLE_STEP = "SINGLE_STEP"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass
class UoWNode:
    """A discrete node in the multi-step execution DAG."""
    node_id: str
    step_index: int
    operator_mnemonic: str
    operator_opcode: int
    source_operands: List[str]  # e.g. ["REF_10", "REF_11"] or ["STAGE_0", "REF_12"]
    destination_target: str     # e.g. "STAGE_0" (scratch) or "GOAL_100" (final)
    dependencies: List[str] = field(default_factory=list)  # node_ids that must complete first
    is_terminal: bool = False   # True if this node produces the final goal state


@dataclass
class CompositeDAG:
    """Compiled execution graph with metadata and topological order."""
    goal_id: str
    family: ExpressionFamily
    nodes: List[UoWNode]
    is_valid: bool
    error_message: Optional[str] = None
    input_refs: Set[int] = field(default_factory=set)
    dest_ref: Optional[int] = None
    scratch_registers_required: int = 0

    def get_topological_order(self) -> List[UoWNode]:
        """Returns nodes in valid execution order respecting dependencies."""
        return sorted(self.nodes, key=lambda n: n.step_index)


class DAGCompiler:
    """Compiles geometric goal specifications into validated multi-step UoW DAGs."""

    @classmethod
    def compile_expression(
        cls,
        goal_id: str,
        expression_text: str,
        dest_ref: int,
    ) -> CompositeDAG:
        text = expression_text.strip()
        lower = text.lower()

        # Check for explicitly unsupported operations first (fail-closed)
        if any(unsupported in lower for unsupported in ["div", "/", "inv", "sqrt", "sin", "cos", "matrix_inverse"]):
            return CompositeDAG(
                goal_id=goal_id,
                family=ExpressionFamily.UNSUPPORTED,
                nodes=[],
                is_valid=False,
                error_message="Unsupported operator in geometric expression: fail-closed",
            )

        # ---------------------------------------------------------------------
        # Family 1: (A ^ B) . C  [Contraction on exterior product]
        # Regex matches e.g. "(REF_10 ^ REF_11) . REF_12", "wedge state 10 and 11, then dot with 12"
        # ---------------------------------------------------------------------
        wedge_dot_match = re.search(
            r"(?:\(?\s*(?:ref_|state\s*)?(\d+)\s*\^\s*(?:ref_|state\s*)?(\d+)\s*\)?\s*\.\s*(?:ref_|state\s*)?(\d+))|"
            r"(?:wedge\s+(?:state\s*)?(\d+)\s+(?:and\s+)?(?:state\s*)?(\d+).*?dot\s+(?:with\s+)?(?:state\s*)?(\d+))",
            lower
        )
        if wedge_dot_match:
            g = [x for x in wedge_dot_match.groups() if x is not None]
            if len(g) == 3:
                a, b, c = int(g[0]), int(g[1]), int(g[2])
                n0 = UoWNode(
                    node_id=f"{goal_id}_s0",
                    step_index=0,
                    operator_mnemonic="OP_VECTOR_WEDGE",
                    operator_opcode=OPCODE_REGISTRY["OP_VECTOR_WEDGE"],
                    source_operands=[f"REF_{a}", f"REF_{b}"],
                    destination_target="STAGE_0",
                    dependencies=[],
                    is_terminal=False,
                )
                n1 = UoWNode(
                    node_id=f"{goal_id}_s1",
                    step_index=1,
                    operator_mnemonic="OP_VECTOR_DOT",
                    operator_opcode=OPCODE_REGISTRY["OP_VECTOR_DOT"],
                    source_operands=["STAGE_0", f"REF_{c}"],
                    destination_target=f"GOAL_{dest_ref}",
                    dependencies=[n0.node_id],
                    is_terminal=True,
                )
                return CompositeDAG(
                    goal_id=goal_id,
                    family=ExpressionFamily.CONTRACTION_WEDGE,
                    nodes=[n0, n1],
                    is_valid=True,
                    input_refs={a, b, c},
                    dest_ref=dest_ref,
                    scratch_registers_required=1,
                )

        # ---------------------------------------------------------------------
        # Family 2: [A, B] = A*B - B*A  [Commutator Bracket Expansion]
        # ---------------------------------------------------------------------
        comm_match = re.search(
            r"(?:\[\s*(?:ref_|state\s*)?(\d+)\s*,\s*(?:ref_|state\s*)?(\d+)\s*\])|"
            r"(?:commutator\s+(?:bracket\s+)?(?:of\s+)?(?:state\s*)?(\d+)\s+(?:and\s+)?(?:state\s*)?(\d+))",
            lower
        )
        if comm_match:
            g = [x for x in comm_match.groups() if x is not None]
            if len(g) == 2:
                a, b = int(g[0]), int(g[1])
                # Step 0: T0 = A * B
                n0 = UoWNode(
                    node_id=f"{goal_id}_s0",
                    step_index=0,
                    operator_mnemonic="OP_CL20_PRODUCT",
                    operator_opcode=OPCODE_REGISTRY["OP_CL20_PRODUCT"],
                    source_operands=[f"REF_{a}", f"REF_{b}"],
                    destination_target="STAGE_0",
                    dependencies=[],
                    is_terminal=False,
                )
                # Step 1: T1 = B * A
                n1 = UoWNode(
                    node_id=f"{goal_id}_s1",
                    step_index=1,
                    operator_mnemonic="OP_CL20_PRODUCT",
                    operator_opcode=OPCODE_REGISTRY["OP_CL20_PRODUCT"],
                    source_operands=[f"REF_{b}", f"REF_{a}"],
                    destination_target="STAGE_1",
                    dependencies=[],
                    is_terminal=False,
                )
                # Step 2: Goal = T0 - T1
                n2 = UoWNode(
                    node_id=f"{goal_id}_s2",
                    step_index=2,
                    operator_mnemonic="OP_SUB",
                    operator_opcode=OPCODE_REGISTRY["OP_SUB"],
                    source_operands=["STAGE_0", "STAGE_1"],
                    destination_target=f"GOAL_{dest_ref}",
                    dependencies=[n0.node_id, n1.node_id],
                    is_terminal=True,
                )
                return CompositeDAG(
                    goal_id=goal_id,
                    family=ExpressionFamily.COMMUTATOR_BRACKET,
                    nodes=[n0, n1, n2],
                    is_valid=True,
                    input_refs={a, b},
                    dest_ref=dest_ref,
                    scratch_registers_required=2,
                )

        # ---------------------------------------------------------------------
        # Family 3: R * A * ~R  [Rotor Sandwich Reflection/Rotation]
        # ---------------------------------------------------------------------
        sandwich_match = re.search(
            r"(?:(?:ref_|state\s*)?(\d+)\s*\*\s*(?:ref_|state\s*)?(\d+)\s*\*\s*~\s*(?:ref_|state\s*)?(\d+))|"
            r"(?:rotor\s+sandwich\s+(?:of\s+)?(?:state\s*)?(\d+)\s+(?:and\s+)?(?:state\s*)?(\d+))|"
            r"(?:sandwich\s+rotor\s+product\s+between\s+(?:state\s*)?(\d+)\s+(?:and\s+)?(?:state\s*)?(\d+))",
            lower
        )
        if sandwich_match:
            g = [x for x in sandwich_match.groups() if x is not None]
            if len(g) >= 2:
                r_ref = int(g[0])
                a_ref = int(g[1])
                # Step 0: T0 = ~R (Reversion of rotor)
                n0 = UoWNode(
                    node_id=f"{goal_id}_s0",
                    step_index=0,
                    operator_mnemonic="OP_REVERSE",
                    operator_opcode=OPCODE_REGISTRY["OP_REVERSE"],
                    source_operands=[f"REF_{r_ref}"],
                    destination_target="STAGE_0",
                    dependencies=[],
                    is_terminal=False,
                )
                # Step 1: T1 = A * T0
                n1 = UoWNode(
                    node_id=f"{goal_id}_s1",
                    step_index=1,
                    operator_mnemonic="OP_CL20_PRODUCT",
                    operator_opcode=OPCODE_REGISTRY["OP_CL20_PRODUCT"],
                    source_operands=[f"REF_{a_ref}", "STAGE_0"],
                    destination_target="STAGE_1",
                    dependencies=[n0.node_id],
                    is_terminal=False,
                )
                # Step 2: Goal = R * T1
                n2 = UoWNode(
                    node_id=f"{goal_id}_s2",
                    step_index=2,
                    operator_mnemonic="OP_CL20_PRODUCT",
                    operator_opcode=OPCODE_REGISTRY["OP_CL20_PRODUCT"],
                    source_operands=[f"REF_{r_ref}", "STAGE_1"],
                    destination_target=f"GOAL_{dest_ref}",
                    dependencies=[n1.node_id],
                    is_terminal=True,
                )
                return CompositeDAG(
                    goal_id=goal_id,
                    family=ExpressionFamily.ROTOR_SANDWICH,
                    nodes=[n0, n1, n2],
                    is_valid=True,
                    input_refs={r_ref, a_ref},
                    dest_ref=dest_ref,
                    scratch_registers_required=2,
                )

        # ---------------------------------------------------------------------
        # Fallback: Single-Step Operator
        # ---------------------------------------------------------------------
        for mne, opcode in OPCODE_REGISTRY.items():
            if mne.lower() in lower or mne.replace("op_", "").lower() in lower:
                refs = [int(x) for x in re.findall(r"(?:ref_|state\s*)(\d+)", lower)]
                if refs:
                    srcs = [f"REF_{r}" for r in refs if r != dest_ref][:2]
                    n0 = UoWNode(
                        node_id=f"{goal_id}_s0",
                        step_index=0,
                        operator_mnemonic=mne,
                        operator_opcode=opcode,
                        source_operands=srcs,
                        destination_target=f"GOAL_{dest_ref}",
                        dependencies=[],
                        is_terminal=True,
                    )
                    return CompositeDAG(
                        goal_id=goal_id,
                        family=ExpressionFamily.SINGLE_STEP,
                        nodes=[n0],
                        is_valid=True,
                        input_refs=set(refs),
                        dest_ref=dest_ref,
                        scratch_registers_required=0,
                    )

        # Unrecognized grammar -> Fail-closed
        return CompositeDAG(
            goal_id=goal_id,
            family=ExpressionFamily.UNSUPPORTED,
            nodes=[],
            is_valid=False,
            error_message=f"Unrecognized or unsupported expression grammar: '{expression_text}'",
        )
