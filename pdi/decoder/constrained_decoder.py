# SPDX-License-Identifier: MIT
"""Grammar-Constrained and Menu-Selection Decoders for PDI-135M.

Provides:
1. Trie-based prefix-constrained logits processors for Transformers.
2. PDINativeGrammarDecoder: Constrains output to valid Native Operational Grammar.
3. PDIJsonConstrainedDecoder: Constrains output to valid PDI-v0 canonical JSON.
4. PDIMenuSelectionDecoder: Machine-defined candidate work selection f_theta(O, G, A) -> a_i.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

import torch
from transformers import AutoTokenizer, LogitsProcessor, LogitsProcessorList

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from pdi.grammar.native_grammar import (
    MNEMONIC_TO_OPCODE,
    OPCODE_TO_MNEMONIC,
    NativeCommand,
    NativeGrammarParser,
    NativePropose,
    NativeObserve,
    NativeCompare,
    NativeClarify,
    NativeEscalate,
)


class TrieNode:
    __slots__ = ("children", "is_end")

    def __init__(self):
        self.children: Dict[int, TrieNode] = {}
        self.is_end: bool = False


class TokenTrie:
    """Prefix trie over token ID sequences."""

    def __init__(self, eos_token_id: int):
        self.root = TrieNode()
        self.eos_token_id = eos_token_id

    def insert(self, token_ids: Sequence[int]) -> None:
        curr = self.root
        for tid in token_ids:
            if tid not in curr.children:
                curr.children[tid] = TrieNode()
            curr = curr.children[tid]
        curr.is_end = True

    def get_allowed_tokens(self, prefix: Sequence[int]) -> Set[int]:
        """Return the set of valid next token IDs given prefix."""
        curr = self.root
        for tid in prefix:
            if tid not in curr.children:
                # Prefix departed from trie: allow EOS or nothing
                return {self.eos_token_id}
            curr = curr.children[tid]

        allowed = set(curr.children.keys())
        if curr.is_end:
            allowed.add(self.eos_token_id)
        if not allowed:
            allowed.add(self.eos_token_id)
        return allowed


class PrefixTrieLogitsProcessor(LogitsProcessor):
    """Masks logits so only tokens permissible according to TokenTrie can be sampled."""

    def __init__(self, trie: TokenTrie, prompt_len: int):
        self.trie = trie
        self.prompt_len = prompt_len

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor) -> torch.FloatTensor:
        batch_size = input_ids.shape[0]
        for b in range(batch_size):
            gen_tokens = input_ids[b, self.prompt_len :].tolist()
            allowed = self.trie.get_allowed_tokens(gen_tokens)
            mask = torch.full((scores.shape[-1],), -float("inf"), device=scores.device)
            mask[list(allowed)] = 0.0
            scores[b] = scores[b] + mask
        return scores


class StateContext:
    """Authoritative state context supplied by FPGA / host for work proposal."""

    def __init__(
        self,
        assumed_state_version: int,
        visible_refs: List[int],
        goal_ref: Optional[int] = None,
        authorized_capability_mask: int = 0x00000001,
        active_slots: Optional[List[str]] = None,
    ):
        self.assumed_state_version = assumed_state_version
        self.visible_refs = visible_refs
        self.goal_ref = goal_ref
        self.authorized_capability_mask = authorized_capability_mask
        self.active_slots = active_slots or [
            "operator_id",
            "object_refs",
            "dest_ref",
            "assumed_state_version",
            "goal_ref",
        ]


def build_native_grammar_trie(
    tokenizer: AutoTokenizer,
    context: StateContext,
    candidate_opcodes: Optional[List[int]] = None,
) -> TokenTrie:
    """Build a TokenTrie containing valid native grammar sentences for the current context."""
    eos_id = tokenizer.eos_token_id or tokenizer.pad_token_id
    trie = TokenTrie(eos_token_id=eos_id)

    opcodes = candidate_opcodes if candidate_opcodes is not None else list(OPCODE_TO_MNEMONIC.keys())
    refs = context.visible_refs
    goal = context.goal_ref

    sentences: List[str] = []

    # 1. PROPOSE commands
    for op in opcodes:
        mne = OPCODE_TO_MNEMONIC.get(op, f"OP_{op}")
        if len(refs) >= 2:
            for r0 in refs:
                for r1 in refs:
                    line = f"PROPOSE {mne} REF_{r0} REF_{r1}"
                    if goal is not None:
                        line += f" GOAL_{goal}"
                    sentences.append(line)
        elif len(refs) == 1:
            line = f"PROPOSE {mne} REF_{refs[0]}"
            if goal is not None:
                line += f" GOAL_{goal}"
            sentences.append(line)
        else:
            sentences.append(f"PROPOSE {mne}")

    # 2. COMPARE commands
    if len(refs) >= 2:
        for r0 in refs:
            for r1 in refs:
                sentences.append(f"COMPARE REF_{r0} REF_{r1}")

    # 3. OBSERVE commands
    sentences.append("OBSERVE")
    for target in ["STATE", "GRAPH", "EVIDENCE", "TELEMETRY"]:
        sentences.append(f"OBSERVE TARGET_{target}")
        for r in refs:
            sentences.append(f"OBSERVE TARGET_{target} REF_{r}")

    # 4. CLARIFY commands
    for slot in context.active_slots:
        sentences.append(f"CLARIFY SLOT_{slot} REASON_unspecified_ambiguity")
        sentences.append(f"CLARIFY SLOT_{slot} REASON_missing_required_reference")

    # 5. ESCALATE commands
    for cap in [0x00000020, 0x00000040, 0x80000000]:
        sentences.append(f"ESCALATE CAP_0x{cap:08X} REASON_unauthorized_capability_required")

    for s in sentences:
        # Tokenize with and without leading space to be robust
        for prefix in ["", " "]:
            tids = tokenizer.encode(prefix + s, add_special_tokens=False)
            trie.insert(tids)

    return trie


def build_json_schema_trie(
    tokenizer: AutoTokenizer,
    context: StateContext,
    candidate_opcodes: Optional[List[int]] = None,
) -> TokenTrie:
    """Build a TokenTrie containing valid PDI-v0 JSON proposals for the current context."""
    eos_id = tokenizer.eos_token_id or tokenizer.pad_token_id
    trie = TokenTrie(eos_token_id=eos_id)

    opcodes = candidate_opcodes if candidate_opcodes is not None else list(OPCODE_TO_MNEMONIC.keys())
    refs = context.visible_refs
    goal = context.goal_ref
    ver = context.assumed_state_version

    json_strings: List[str] = []

    # PROPOSE JSONs
    for op in opcodes:
        if len(refs) >= 2:
            for r0 in refs:
                for r1 in refs:
                    d: Dict[str, Any] = {
                        "schema_version": 1,
                        "kind": "PROPOSE",
                        "operator_id": op,
                        "object_refs": [r0, r1],
                        "parameters": [],
                        "assumed_state_version": ver,
                    }
                    if goal is not None:
                        d["goal_ref"] = goal
                    json_strings.append(json.dumps(d, indent=2))
                    json_strings.append(json.dumps(d))
        elif len(refs) == 1:
            d = {
                "schema_version": 1,
                "kind": "PROPOSE",
                "operator_id": op,
                "object_refs": [refs[0]],
                "parameters": [],
                "assumed_state_version": ver,
            }
            if goal is not None:
                d["goal_ref"] = goal
            json_strings.append(json.dumps(d, indent=2))
            json_strings.append(json.dumps(d))

    # COMPARE JSONs
    if len(refs) >= 2:
        for r0 in refs:
            for r1 in refs:
                d = {
                    "schema_version": 1,
                    "kind": "COMPARE",
                    "left_ref": r0,
                    "right_ref": r1,
                    "assumed_state_version": ver,
                }
                json_strings.append(json.dumps(d, indent=2))
                json_strings.append(json.dumps(d))

    # OBSERVE JSONs
    for target in ["STATE", "GRAPH", "EVIDENCE", "TELEMETRY"]:
        d = {
            "schema_version": 1,
            "kind": "OBSERVE",
            "projection_type": target,
            "target_refs": refs if refs else [0],
        }
        json_strings.append(json.dumps(d, indent=2))
        json_strings.append(json.dumps(d))

    # CLARIFY JSONs
    for slot in context.active_slots:
        d = {
            "schema_version": 1,
            "kind": "CLARIFY",
            "missing_slots": [slot],
            "ambiguity_reason": f"Missing reference for {slot}",
        }
        json_strings.append(json.dumps(d, indent=2))
        json_strings.append(json.dumps(d))

    # ESCALATE JSONs
    for cap in [0x00000020, 0x00000040, 0x80000000]:
        d = {
            "schema_version": 1,
            "kind": "ESCALATE",
            "requested_capability": cap,
            "reason": "Privileged operation requires capability grant",
        }
        json_strings.append(json.dumps(d, indent=2))
        json_strings.append(json.dumps(d))

    for s in json_strings:
        for prefix in ["", " "]:
            tids = tokenizer.encode(prefix + s, add_special_tokens=False)
            trie.insert(tids)

    return trie


def build_menu_selection_trie(
    tokenizer: AutoTokenizer,
    menu_size: int,
) -> TokenTrie:
    """Build a TokenTrie allowing only option indices 1 .. menu_size."""
    eos_id = tokenizer.eos_token_id or tokenizer.pad_token_id
    trie = TokenTrie(eos_token_id=eos_id)

    for i in range(1, menu_size + 1):
        for form in [str(i), f" {i}", f"[{i}]", f" [{i}]"]:
            tids = tokenizer.encode(form, add_special_tokens=False)
            trie.insert(tids)

    return trie
