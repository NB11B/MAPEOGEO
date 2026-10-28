"""Recurrent step-wise policy module with Transformer clause encoder and state feedback."""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple
import torch
from torch import nn
from torch.nn import functional as F

from .machine import ALL_OPS, ALU_OPS, GEO_OPS, RecurrentMachineState, Value

INPUT_NAMES = ("a", "b", "c", "d", "e", "f", "g", "h")
SCRATCH_NAMES = ("R0", "R1", "R2", "R3")
ALL_REGS = INPUT_NAMES + SCRATCH_NAMES

PAD, BOS, EOS = "<pad>", "<bos>", "<eos>"
VOCAB_SPECIAL = [PAD, BOS, EOS, ",", "then", "after", "it", "with", "from", "and", "to", "combine", "eq", "sub", "add", "xor", "or"]
TEMPLATES = {
    "ADD": ["add {p} and {q}", "{p} plus {q}"],
    "SUB": ["subtract {q} from {p}", "{p} minus {q}"],
    "XOR": ["xor {p} with {q}", "parity of {p} and {q}"],
    "AND": ["mask {p} with {q}", "bitwise and of {p} and {q}"],
    "OR": ["merge {p} with {q}", "bitwise or of {p} and {q}"],
    "EQ": ["compare {p} with {q}", "check {p} equals {q}"],
    "GEO_GP3": ["clifford product of {p} and {q}", "geometric multiply {p} by {q}"]
}

WORDS = set(VOCAB_SPECIAL + list(INPUT_NAMES) + list(SCRATCH_NAMES))
for ts in TEMPLATES.values():
    for t in ts:
        for w in t.split():
            if not w.startswith("{"):
                WORDS.add(w)
WORD_LIST = sorted(list(WORDS))
WORD_IX = {w: i for i, w in enumerate(WORD_LIST)}

OP_IX = {op: i for i, op in enumerate(ALL_OPS)}
REG_IX = {r: i for i, r in enumerate(ALL_REGS)}
SCRATCH_IX = {r: i for i, r in enumerate(SCRATCH_NAMES)}

class TransformerClausePolicy(nn.Module):
    """Closed-loop recurrent policy with Transformer clause encoding and GRU state core."""
    def __init__(self, d=64):
        super().__init__()
        self.d = d
        self.num_regs = len(ALL_REGS)
        self.num_scratch = len(SCRATCH_NAMES)

        self.word_emb = nn.Embedding(len(WORD_LIST), d, padding_idx=WORD_IX[PAD])
        self.pos_emb = nn.Embedding(16, d)
        enc_layer = nn.TransformerEncoderLayer(d_model=d, nhead=4, dim_feedforward=128, batch_first=True, dropout=0.0)
        self.enc = nn.TransformerEncoder(enc_layer, num_layers=2)

        self.core = nn.GRUCell(d + 1, d)

        self.head_op = nn.Linear(d, len(ALL_OPS))
        self.head_src1 = nn.Linear(d, len(ALL_REGS))
        self.head_src2 = nn.Linear(d, len(ALL_REGS))
        self.head_dst = nn.Linear(d, len(SCRATCH_NAMES))
        self.head_halt = nn.Linear(d, 2)

    def forward(self, clause_tokens, is_last, h_prev):
        B, seq_len = clause_tokens.shape
        pos = torch.arange(seq_len, device=clause_tokens.device).unsqueeze(0)
        emb = self.word_emb(clause_tokens) + self.pos_emb(pos)
        pad_mask = (clause_tokens == WORD_IX[PAD])
        h_enc = self.enc(emb, src_key_padding_mask=pad_mask)
        c_ctx = h_enc[:, 0]

        in_feat = torch.cat([c_ctx, is_last.unsqueeze(-1).float()], dim=-1)
        h_t = self.core(in_feat, h_prev)

        return h_t, (self.head_op(h_t), self.head_src1(h_t), self.head_src2(h_t), self.head_dst(h_t), self.head_halt(h_t))
