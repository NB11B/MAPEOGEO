# SPDX-License-Identifier: MIT
"""Dense 32-Dimensional PSMSL Work-Relation Feature Encoder for PDI-v0.7B.

Encodes (Goal, StateContext, CandidateAction) into a fixed 32-dimensional numeric vector
strictly prior to execution, with zero oracle knowledge and zero position features.

Feature Layout (32 dims):
- [0..7]   Structural (opcode, arity, dest match, commutativity, category flags)
- [8..11]  Causal & Versions (version current, causal dependency, read count, shadow scratch dest)
- [12..19] Geometric Algebra (grade compatibility, scalar/vector/bivector/mv expected, norm preservation)
- [20..25] Prompt Semantic Alignment (keyword detection for wedge, dot, commutator, rotor, operand order)
- [26..31] Hardware Authority & Constraints (in-bounds, capability authorized, abstention, safety violation)
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from pdi.decoder.constrained_decoder import StateContext
from pdi.grammar.native_grammar import NativeCommand, NativeGrammarParser, OPCODE_TO_MNEMONIC
from pdi.projection.work_relation_encoder import (
    PSMSLWorkRelationEncoder,
    WorkRelationSignature,
)

COMMUTATIVE_OPCODES = {1, 3, 9, 31, 33}


class DensePSMSLEncoder:
    """Encodes pre-execution work relations into a fixed 32-dimensional dense float vector."""

    FEATURE_DIM = 32

    def __init__(self):
        self.base_encoder = PSMSLWorkRelationEncoder()

    def encode_dense_vector(
        self,
        cand_id: str,
        action_line: str,
        context: StateContext,
        input_prompt: str,
    ) -> List[float]:
        sig: WorkRelationSignature = self.base_encoder.encode(cand_id, action_line, context, input_prompt)
        prompt_lower = input_prompt.lower()
        act_lower = action_line.lower()

        vec = [0.0] * self.FEATURE_DIM

        # ---------------------------------------------------------------------
        # 1. Structural Features [0..7]
        # ---------------------------------------------------------------------
        op = sig.structural.opcode or 0
        vec[0] = float(op) / 34.0
        vec[1] = float(sig.structural.arity) / 2.0
        vec[2] = 1.0 if sig.structural.has_destination else 0.0
        vec[3] = 1.0 if sig.structural.dest_matches_goal else 0.0
        vec[4] = 1.0 if op in COMMUTATIVE_OPCODES else 0.0
        vec[5] = 1.0 if op in (6, 7, 8) else 0.0  # Unary geometric: reverse, grade involution, conjugate
        vec[6] = 1.0 if op in (5, 9, 10, 11, 12) else 0.0  # Bilinear geometric
        vec[7] = 1.0 if op in (1, 2, 3, 31, 32, 33) else 0.0  # ALU arithmetic

        # ---------------------------------------------------------------------
        # 2. Causal & Version Features [8..11]
        # ---------------------------------------------------------------------
        vec[8] = 1.0 if sig.causal.is_version_current else 0.0
        vec[9] = 1.0 if sig.causal.has_causal_dependency else 0.0
        vec[10] = float(min(sig.structural.operand_count, 3)) / 3.0
        dest_val = 0
        dest_m = re.search(r"GOAL_(\d+)|STAGE_(\d+)", action_line)
        if dest_m:
            dest_val = int(dest_m.group(1) or dest_m.group(2) or 0)
        vec[11] = 1.0 if dest_val >= 224 or "stage_" in act_lower else 0.0  # Shadow scratch range

        # ---------------------------------------------------------------------
        # 3. Geometric Algebra Features [12..19]
        # ---------------------------------------------------------------------
        vec[12] = 1.0 if sig.geometric.grade_compatible else 0.0
        out_grade = sig.geometric.expected_output_grade.lower()
        vec[13] = 1.0 if "scalar" in out_grade else 0.0
        vec[14] = 1.0 if "vector" in out_grade else 0.0
        vec[15] = 1.0 if "bivector" in out_grade else 0.0
        vec[16] = 1.0 if "multivector" in out_grade or "cl20" in out_grade else 0.0
        # Check source operand compatibility
        vec[17] = 1.0 if len(sig.geometric.operand_grades) >= 2 and sig.geometric.operand_grades[0] == sig.geometric.operand_grades[1] else 0.0
        vec[18] = 1.0 if op == 6 else 0.0  # Reversion operator
        vec[19] = 1.0 if op in (6, 7, 8, 4) else 0.0  # Norm preservation

        # ---------------------------------------------------------------------
        # 4. Prompt Semantic Alignment Features [20..25]
        # ---------------------------------------------------------------------
        mne = OPCODE_TO_MNEMONIC.get(op, "").lower().replace("op_", "")
        vec[20] = 1.0 if mne and mne in prompt_lower else 0.0
        vec[21] = 1.0 if any(w in prompt_lower for w in ["wedge", "exterior", "^", "bivector span"]) and op == 10 else 0.0
        vec[22] = 1.0 if any(w in prompt_lower for w in ["dot", "inner", "contraction", "metric"]) and op == 9 else 0.0
        vec[23] = 1.0 if any(w in prompt_lower for w in ["commutator", "bracket", "["]) and op in (5, 11) else 0.0
        vec[24] = 1.0 if any(w in prompt_lower for w in ["rotor", "sandwich", "rotation", "reflection"]) and op in (5, 6) else 0.0
        
        # Operand order match (non-commutative alignment)
        refs_in_act = [int(x) for x in re.findall(r"REF_(\d+)", action_line)]
        refs_in_prompt = [int(x) for x in re.findall(r"(?:state|ref)\s*[_:]?\s*(\d+)", prompt_lower)]
        vec[25] = 1.0 if len(refs_in_act) >= 2 and len(refs_in_prompt) >= 2 and refs_in_act[:2] == refs_in_prompt[:2] else 0.0

        # ---------------------------------------------------------------------
        # 5. Hardware Authority & Constraints [26..31]
        # ---------------------------------------------------------------------
        vec[26] = 1.0 if sig.constraints.addresses_in_bounds else 0.0
        vec[27] = 1.0 if sig.constraints.capability_authorized else 0.0
        vec[28] = 1.0 if sig.constraints.is_abstention else 0.0
        vec[29] = 1.0 if sig.constraints.has_safety_violation else 0.0
        vec[30] = 1.0 if not sig.constraints.has_safety_violation and sig.structural.dest_matches_goal else 0.0
        vec[31] = 1.0 if not sig.constraints.capability_authorized else 0.0

        return vec
