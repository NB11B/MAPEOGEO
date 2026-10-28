"""MAPEOGEO-LLM milestone 2: compositional generalization of a learned controller
that plans over frozen, compiled operators.

Task
----
A natural-language-like instruction describes a chain of 1-4 operations over
named 8-bit operands, e.g.

    "add c and a , then subtract f from it , then xor it with b"
    "xor it with b , after subtract f from it , after add c and a"   (reverse)

The controller (a small Transformer encoder-decoder) must emit an explicit
dataflow program in execution order:

    ADD c a   SUB RES f   XOR RES b   <eos>

which is executed by the zero-parameter CompiledALU. Answers are scored against
an independent plain-Python reference evaluated on the *true* program.

Splits (all with fresh operand values and freshly sampled names/templates)
----------------------------------------------------------------------------
iid                  : operator combinations seen in training
L2_heldout_pair      : length-2 chains whose (op1, op2) pair never appears in training
L3_heldout_pair      : length-3 chains containing a held-out adjacent pair
L3_unseen_triple     : length-3 chains, unseen as triples but every adjacent pair seen
L4_length            : length-4 chains (training max length is 3)

Baselines
---------
majority             : always output the most common training answer
end_to_end_neural    : Transformer that reads prompt + operand bits and predicts the
                       8-bit answer directly, with no operators (same training set)
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import random
import time
from collections import Counter
from pathlib import Path

import torch
from torch import nn
from torch.nn import functional as F

try:  # package import (python -m experiments.mapeogeo_llm.compositional)
    from .operators import OPS, CompiledALU, from_bits, reference, to_bits, verify_exhaustive
except ImportError:  # script import (python compositional.py)
    from operators import OPS, CompiledALU, from_bits, reference, to_bits, verify_exhaustive

NAMES = ("a", "b", "c", "d", "e", "f")
RES = "RES"

# {p},{q} are filled so that the template denotes op(p, q).
TEMPLATES = {
    "ADD": ["add {p} and {q}", "{p} plus {q}", "sum {p} with {q}"],
    "SUB": ["subtract {q} from {p}", "{p} minus {q}", "take {q} away from {p}"],
    "XOR": ["xor {p} with {q}", "{p} exclusive or {q}", "parity of {p} and {q}"],
    "AND": ["mask {p} with {q}", "bitwise and of {p} and {q}", "{p} intersect {q}"],
    "OR": ["merge {p} with {q}", "bitwise or of {p} and {q}", "{p} union {q}"],
    "EQ": ["compare {p} with {q}", "is {p} equal to {q}", "check {p} equals {q}"],
}
MODES = ("forward", "reverse")

PAD, BOS, EOS, UNK = "<pad>", "<bos>", "<eos>", "<unk>"
SRC_VOCAB = [PAD, UNK, ",", "then", "after", "it"] + list(NAMES)
for _ts in TEMPLATES.values():
    for _t in _ts:
        for _w in _t.split():
            if not _w.startswith("{") and _w not in SRC_VOCAB:
                SRC_VOCAB.append(_w)
TGT_VOCAB = [PAD, BOS, EOS] + list(OPS) + list(NAMES) + [RES]
SRC_IX = {w: i for i, w in enumerate(SRC_VOCAB)}
TGT_IX = {w: i for i, w in enumerate(TGT_VOCAB)}
MAX_LEN = 4


# --------------------------------------------------------------------------- data
def make_split(seed: int, n_heldout_pairs: int = 8, triple_holdout_frac: float = 0.15) -> dict:
    """Choose held-out operator combinations. Every operator still appears in
    every position of some training combination."""
    rng = random.Random(seed)
    pairs = list(itertools.product(OPS, repeat=2))
    while True:
        held = set(rng.sample(pairs, n_heldout_pairs))
        train_pairs = [p for p in pairs if p not in held]
        if all(any(p[0] == o for p in train_pairs) and any(p[1] == o for p in train_pairs) for o in OPS):
            break
    triples = list(itertools.product(OPS, repeat=3))
    novel = [t for t in triples if (t[0], t[1]) in held or (t[1], t[2]) in held]
    clean = [t for t in triples if t not in set(novel)]
    rng.shuffle(clean)
    k = int(len(clean) * triple_holdout_frac)
    return {
        "heldout_pairs": sorted(held),
        "train_combos": [(o,) for o in OPS] + train_pairs + sorted(clean[k:]),
        "L2_heldout_pair": sorted(held),
        "L3_heldout_pair": sorted(novel),
        "L3_unseen_triple": sorted(clean[:k]),
    }


def make_example(combo: tuple, rng: random.Random, mode: str | None = None) -> dict:
    L = len(combo)
    names = rng.sample(NAMES, L + 1)
    env = {n: rng.randrange(256) for n in names}
    mode = mode or rng.choice(MODES)
    program, phrases = [], []
    for k, op in enumerate(combo):
        if k == 0:
            p, q = names[0], names[1]
            prog_args = (p, q)
        else:
            x = names[k + 1]
            if rng.random() < 0.5:
                p, q, prog_args = "it", x, (RES, x)
            else:
                p, q, prog_args = x, "it", (x, RES)
        program.append((op,) + prog_args)
        phrases.append(rng.choice(TEMPLATES[op]).format(p=p, q=q))
    if mode == "forward":
        text = " , then ".join(phrases)
    else:
        text = " , after ".join(reversed(phrases))
    target = [t for step in program for t in step] + [EOS]
    return {"prompt": text.split(), "target": target, "program": program, "env": env,
            "combo": combo, "mode": mode, "answer": run_reference(program, env)}


def run_reference(program, env) -> int:
    r = None
    for op, x, y in program:
        a = r if x == RES else env[x]
        b = r if y == RES else env[y]
        r = reference(op, a, b)
    return r


def build_dataset(split: dict, seed: int, n_train: int, n_test: int) -> dict:
    rng = random.Random(seed + 1)
    by_len = {L: [c for c in split["train_combos"] if len(c) == L] for L in (1, 2, 3)}
    len_p = [0.15, 0.35, 0.50]
    train = [make_example(rng.choice(by_len[rng.choices((1, 2, 3), len_p)[0]]), rng) for _ in range(n_train)]
    test = {
        "iid": [make_example(rng.choice(by_len[rng.choices((1, 2, 3), len_p)[0]]), rng) for _ in range(n_test)],
        "L2_heldout_pair": [make_example(rng.choice(split["L2_heldout_pair"]), rng) for _ in range(n_test)],
        "L3_heldout_pair": [make_example(rng.choice(split["L3_heldout_pair"]), rng) for _ in range(n_test)],
        "L3_unseen_triple": [make_example(rng.choice(split["L3_unseen_triple"]), rng) for _ in range(n_test)],
        "L4_length": [make_example(tuple(rng.choice(OPS) for _ in range(4)), rng) for _ in range(n_test)],
    }
    train_combos = set(split["train_combos"])
    for name in ("L2_heldout_pair", "L3_heldout_pair", "L3_unseen_triple", "L4_length"):
        assert not any(ex["combo"] in train_combos for ex in test[name]), name
    return {"train": train, "test": test}


def encode_src(batch, device):
    n = max(len(ex["prompt"]) for ex in batch)
    t = torch.full((len(batch), n), SRC_IX[PAD], dtype=torch.long)
    for i, ex in enumerate(batch):
        t[i, : len(ex["prompt"])] = torch.tensor([SRC_IX.get(w, SRC_IX[UNK]) for w in ex["prompt"]])
    return t.to(device)


def encode_tgt(batch, device):
    n = max(len(ex["target"]) for ex in batch) + 1
    t = torch.full((len(batch), n), TGT_IX[PAD], dtype=torch.long)
    for i, ex in enumerate(batch):
        seq = [BOS] + ex["target"]
        t[i, : len(seq)] = torch.tensor([TGT_IX[w] for w in seq])
    return t.to(device)


# ------------------------------------------------------------------------ models
def sinusoid(n, d, device):
    pos = torch.arange(n, device=device, dtype=torch.float32)[:, None]
    div = torch.exp(torch.arange(0, d, 2, device=device, dtype=torch.float32) * (-math.log(10000.0) / d))
    pe = torch.zeros(n, d, device=device)
    pe[:, 0::2] = torch.sin(pos * div)
    pe[:, 1::2] = torch.cos(pos * div)
    return pe


class Controller(nn.Module):
    """Learned planner. Emits a dataflow program; it never computes answers."""

    def __init__(self, d=64, heads=4, layers=2, ff=128, dropout=0.1):
        super().__init__()
        self.d = d
        self.src_emb = nn.Embedding(len(SRC_VOCAB), d, padding_idx=SRC_IX[PAD])
        self.tgt_emb = nn.Embedding(len(TGT_VOCAB), d, padding_idx=TGT_IX[PAD])
        self.tf = nn.Transformer(d, heads, layers, layers, ff, dropout, batch_first=True)
        self.out = nn.Linear(d, len(TGT_VOCAB))

    def forward(self, src, tgt_in):
        dev = src.device
        s = self.src_emb(src) * math.sqrt(self.d) + sinusoid(src.size(1), self.d, dev)
        t = self.tgt_emb(tgt_in) * math.sqrt(self.d) + sinusoid(tgt_in.size(1), self.d, dev)
        mask = nn.Transformer.generate_square_subsequent_mask(tgt_in.size(1), device=dev)
        h = self.tf(s, t, tgt_mask=mask, src_key_padding_mask=src == SRC_IX[PAD],
                    tgt_key_padding_mask=tgt_in == TGT_IX[PAD], memory_key_padding_mask=src == SRC_IX[PAD])
        return self.out(h)

    @torch.no_grad()
    def decode(self, src, max_steps=3 * (MAX_LEN + 1) + 1):
        ys = torch.full((src.size(0), 1), TGT_IX[BOS], dtype=torch.long, device=src.device)
        for _ in range(max_steps):
            nxt = self.forward(src, ys)[:, -1].argmax(-1, keepdim=True)
            ys = torch.cat([ys, nxt], 1)
            if bool((ys == TGT_IX[EOS]).any(1).all()):
                break
        out = []
        for row in ys[:, 1:].tolist():
            toks = []
            for i in row:
                if TGT_VOCAB[i] == EOS:
                    break
                toks.append(TGT_VOCAB[i])
            out.append(toks)
        return out


class EndToEndBaseline(nn.Module):
    """No operators: reads prompt tokens + named operand bits, predicts the answer."""

    def __init__(self, d=96, heads=4, layers=3, ff=256, dropout=0.1):
        super().__init__()
        self.d = d
        self.src_emb = nn.Embedding(len(SRC_VOCAB), d, padding_idx=SRC_IX[PAD])
        self.name_emb = nn.Embedding(len(NAMES), d)
        self.bits = nn.Linear(8, d)
        self.cls = nn.Parameter(torch.zeros(1, 1, d))
        layer = nn.TransformerEncoderLayer(d, heads, ff, dropout, batch_first=True)
        self.enc = nn.TransformerEncoder(layer, layers)
        self.out = nn.Linear(d, 256)

    def forward(self, src, env_bits):
        # env_bits: (B, len(NAMES), 8); value 0 bits for absent names is still
        # informative-free because absent names never appear in the prompt.
        s = self.src_emb(src) * math.sqrt(self.d) + sinusoid(src.size(1), self.d, src.device)
        names = torch.arange(len(NAMES), device=src.device)
        v = self.bits(env_bits) + self.name_emb(names)[None]
        x = torch.cat([self.cls.expand(src.size(0), -1, -1), v, s], 1)
        pad = torch.cat([torch.zeros(src.size(0), 1 + len(NAMES), dtype=torch.bool, device=src.device),
                         src == SRC_IX[PAD]], 1)
        return self.out(self.enc(x, src_key_padding_mask=pad)[:, 0])


def env_tensor(batch, device):
    t = torch.zeros(len(batch), len(NAMES), 8)
    for i, ex in enumerate(batch):
        for j, n in enumerate(NAMES):
            if n in ex["env"]:
                t[i, j] = to_bits(torch.tensor([ex["env"][n]]))[:, 0].float()
    return t.to(device)


# --------------------------------------------------------------------- execution
def parse_program(tokens):
    """Fail-closed parse of decoder output into [(op, arg, arg), ...]."""
    if len(tokens) == 0 or len(tokens) % 3:
        return None
    prog = []
    for k in range(0, len(tokens), 3):
        op, x, y = tokens[k: k + 3]
        if op not in OPS or x not in NAMES + (RES,) or y not in NAMES + (RES,):
            return None
        if k == 0 and RES in (x, y):
            return None
        prog.append((op, x, y))
    return prog


def execute(alu: CompiledALU, program, env):
    """Run a program on the compiled ALU. Returns None if it references
    operands that were not supplied (fail closed)."""
    r = None
    for op, x, y in program:
        if (x != RES and x not in env) or (y != RES and y not in env):
            return None
        a = r if x == RES else to_bits(torch.tensor([env[x]]))
        b = r if y == RES else to_bits(torch.tensor([env[y]]))
        r = alu(op, a, b)
    return int(from_bits(r)[0])


# ---------------------------------------------------------------------- training
def batches(data, bs, rng):
    idx = list(range(len(data)))
    rng.shuffle(idx)
    for i in range(0, len(idx), bs):
        yield [data[j] for j in idx[i: i + bs]]


def train_controller(train, epochs, seed, device, bs=128, lr=1e-3, log=print):
    torch.manual_seed(seed)
    model = Controller().to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    total = epochs * math.ceil(len(train) / bs)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, lr, total_steps=total, pct_start=0.1)
    rng = random.Random(seed)
    for ep in range(epochs):
        model.train()
        tot, n = 0.0, 0
        for b in batches(train, bs, rng):
            src, tgt = encode_src(b, device), encode_tgt(b, device)
            logits = model(src, tgt[:, :-1])
            loss = F.cross_entropy(logits.reshape(-1, logits.size(-1)), tgt[:, 1:].reshape(-1),
                                   ignore_index=TGT_IX[PAD])
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            tot += loss.item() * len(b)
            n += len(b)
        if ep == epochs - 1 or ep % 5 == 0:
            log(f"  controller epoch {ep + 1}/{epochs} loss {tot / n:.4f}")
    return model


def train_end_to_end(train, epochs, seed, device, bs=128, lr=5e-4, log=print):
    torch.manual_seed(seed)
    model = EndToEndBaseline().to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    total = epochs * math.ceil(len(train) / bs)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, lr, total_steps=total, pct_start=0.1)
    rng = random.Random(seed)
    for ep in range(epochs):
        model.train()
        tot, n = 0.0, 0
        for b in batches(train, bs, rng):
            y = torch.tensor([ex["answer"] for ex in b], device=device)
            loss = F.cross_entropy(model(encode_src(b, device), env_tensor(b, device)), y)
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            tot += loss.item() * len(b)
            n += len(b)
        if ep == epochs - 1 or ep % 5 == 0:
            log(f"  end-to-end epoch {ep + 1}/{epochs} loss {tot / n:.4f}")
    return model


# -------------------------------------------------------------------- evaluation
def evaluate_controller(model, data, device, alu, bs=256):
    model.eval()
    stats = Counter()
    per_mode = {m: Counter() for m in MODES}
    for i in range(0, len(data), bs):
        b = data[i: i + bs]
        for ex, toks in zip(b, model.decode(encode_src(b, device))):
            prog = parse_program(toks)
            ans = execute(alu, prog, ex["env"]) if prog is not None else None
            ok = {"program_exact": prog == ex["program"],
                  "ops_exact": prog is not None and [s[0] for s in prog] == list(ex["combo"]),
                  "answer": ans is not None and ans == ex["answer"],
                  "invalid": prog is None or ans is None}
            for k, v in ok.items():
                stats[k] += int(v)
                per_mode[ex["mode"]][k] += int(v)
            per_mode[ex["mode"]]["n"] += 1
    n = len(data)
    out = {k: stats[k] / n for k in ("program_exact", "ops_exact", "answer", "invalid")}
    out["answer_by_mode"] = {m: per_mode[m]["answer"] / max(1, per_mode[m]["n"]) for m in MODES}
    return out


@torch.no_grad()
def evaluate_end_to_end(model, data, device, bs=512):
    model.eval()
    good = 0
    for i in range(0, len(data), bs):
        b = data[i: i + bs]
        pred = model(encode_src(b, device), env_tensor(b, device)).argmax(-1).tolist()
        good += sum(int(p == ex["answer"]) for p, ex in zip(pred, b))
    return {"answer": good / len(data)}


# -------------------------------------------------------------------------- main
def run_seed(seed, args, device, alu, log=print):
    split = make_split(seed)
    data = build_dataset(split, seed, args.n_train, args.n_test)
    log(f"seed {seed}: heldout pairs {split['heldout_pairs']}")
    t0 = time.time()
    ctrl = train_controller(data["train"], args.epochs, seed, device, log=log)
    res = {"heldout_pairs": [list(p) for p in split["heldout_pairs"]],
           "n_train_combos": len(split["train_combos"]),
           "controller": {k: evaluate_controller(ctrl, v, device, alu) for k, v in data["test"].items()},
           "controller_train_seconds": round(time.time() - t0, 1)}
    majority = Counter(ex["answer"] for ex in data["train"]).most_common(1)[0][0]
    res["majority"] = {k: sum(ex["answer"] == majority for ex in v) / len(v) for k, v in data["test"].items()}
    if not args.skip_baseline:
        e2e = train_end_to_end(data["train"], args.baseline_epochs, seed, device, log=log)
        res["end_to_end_neural"] = {k: evaluate_end_to_end(e2e, v, device)["answer"] for k, v in data["test"].items()}
    return res, ctrl


def summarize(per_seed):
    splits = list(per_seed[0]["controller"].keys())
    summary = {}
    for s in splits:
        row = {}
        for metric in ("program_exact", "answer", "invalid"):
            vals = [r["controller"][s][metric] for r in per_seed]
            row[f"controller_{metric}"] = {"mean": sum(vals) / len(vals), "min": min(vals), "max": max(vals)}
        vals = [r["majority"][s] for r in per_seed]
        row["majority_answer"] = sum(vals) / len(vals)
        if "end_to_end_neural" in per_seed[0]:
            vals = [r["end_to_end_neural"][s] for r in per_seed]
            row["end_to_end_neural_answer"] = {"mean": sum(vals) / len(vals), "min": min(vals), "max": max(vals)}
        summary[s] = row
    return summary


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    p.add_argument("--epochs", type=int, default=30)
    p.add_argument("--baseline-epochs", type=int, default=40)
    p.add_argument("--n-train", type=int, default=24000)
    p.add_argument("--n-test", type=int, default=1000)
    p.add_argument("--skip-baseline", action="store_true")
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    p.add_argument("--out", default=str(Path(__file__).parent / "results" / "compositional.json"))
    args = p.parse_args(argv)

    alu = CompiledALU()
    print("verifying compiled operators exhaustively ...")
    op_counts = verify_exhaustive(alu)
    print(f"  {sum(op_counts.values())} input pairs, all exact")
    assert sum(q.numel() for q in alu.parameters()) == 0

    per_seed = []
    for seed in args.seeds:
        r, ctrl = run_seed(seed, args, args.device, alu)
        per_seed.append(r)
        print(json.dumps(r["controller"], indent=1))
    results = {"config": vars(args), "operator_verification": op_counts,
               "summary": summarize(per_seed), "per_seed": per_seed}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2))
    torch.save({"state_dict": ctrl.state_dict(), "src_vocab": SRC_VOCAB, "tgt_vocab": TGT_VOCAB},
               out.with_suffix(".pt"))
    print(json.dumps(results["summary"], indent=2))
    return results


if __name__ == "__main__":
    main()
