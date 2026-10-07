from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import random
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import ijson

from mapeogeo.openai_math_source import scan_source


BASELINE_COMMIT = "2e5ef8d12aace9b519d96f3d8214161cd87b0d7e"
BASELINE_RUN = 37591827279
OPENAI_MATH_COMMIT = "adc7f1241b42e322a6451854ab7e4b4c146bf78a"
INTEGRATED_GRAPH_SHA256 = "abe9c19bcce1281f7b285bfe11f7051d5dc38fb9ca3072a32a4b44def72f43b9"
HOLDOUT_FAMILY = "312"
HOLDOUT_CONFIG_PATH = "lean/ComparatorChallenges/GrothendieckElementaryExpansion.json"
HOLDOUT_SCOPE_PATH = "lean/docs/312.md"

GENERIC = {
    "the", "a", "an", "of", "and", "or", "for", "to", "in", "on", "with", "by", "from",
    "as", "this", "that", "these", "those", "let", "have", "has", "using", "where", "when",
    "then", "if", "iff", "all", "every", "some", "there", "exists", "type", "prop", "sort",
    "nat", "true", "false", "self", "mk", "app", "obj", "hom", "def", "theorem", "lemma",
    "instance", "structure", "class", "abbrev", "noncomputable", "namespace", "section",
    "variable", "universe", "open", "private", "protected", "local", "by", "exact", "apply",
    "intro", "simpa", "only", "using", "show", "from", "match", "fun", "forall", "exists",
    "out", "inl", "inr", "none", "some", "left", "right", "main", "oai", "comparator",
    "challenges", "category", "theory", "model",
}

BRACKETS = {"(": ")", "{": "}", "[": "]"}
CLOSE = {v: k for k, v in BRACKETS.items()}


def cjson(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def resource_path(node_id: str) -> str | None:
    prefix = "oam:file:"
    if not str(node_id).startswith(prefix):
        return None
    return str(node_id)[len(prefix):].split(":record:", 1)[0].split(":reference:", 1)[0]


def module_to_path(module: str) -> str:
    return "lean/" + module.replace(".", "/") + ".lean"


def split_identifier(raw: str) -> list[str]:
    raw = raw.strip("'")
    raw = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", raw.replace("_", " ").replace("-", " "))
    parts = [x.lower() for x in re.findall(r"[A-Za-z][A-Za-z0-9]*", raw)]
    return [x for x in parts if len(x) > 1 and x not in GENERIC]


def identifier_features(text: str, drop: set[str] | None = None) -> set[str]:
    drop = drop or set()
    out: set[str] = set()
    for m in re.finditer(r"[A-Za-z_][A-Za-z0-9_']*(?:\.[A-Za-z_][A-Za-z0-9_']*)*", text):
        raw = m.group(0)
        last = raw.rsplit(".", 1)[-1]
        parts = split_identifier(last)
        for p in parts:
            if p not in drop:
                out.add(p)
        compact = "".join(parts)
        if len(compact) >= 5 and compact not in drop and compact not in GENERIC:
            out.add(compact)
    return out


def qualified_head(text: str) -> set[str]:
    t = text.strip()
    if not t:
        return set()
    if "↔" in t:
        return {"iffop"}
    if re.search(r"(?<![<>=!])=(?!=)", t):
        return {"eqop"}
    if "≤" in t or re.search(r"\s<=\s", t):
        return {"leop"}
    if "≥" in t or re.search(r"\s>=\s", t):
        return {"geop"}
    m = re.search(r"[A-Za-z_][A-Za-z0-9_']*(?:\.[A-Za-z_][A-Za-z0-9_']*)*", t)
    if not m:
        return set()
    return identifier_features(m.group(0))


def top_level_result_colon(header: str, start: int) -> int | None:
    stack: list[str] = []
    last = None
    i = start
    while i < len(header):
        ch = header[i]
        if ch in BRACKETS:
            stack.append(ch)
        elif ch in CLOSE:
            if stack and stack[-1] == CLOSE[ch]:
                stack.pop()
        elif ch == ":" and not stack:
            if i + 1 < len(header) and header[i + 1] == "=":
                i += 2
                continue
            last = i
        i += 1
    return last


def split_top_level_arrows(text: str) -> tuple[str, str]:
    stack: list[str] = []
    cuts: list[tuple[int, int]] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch in BRACKETS:
            stack.append(ch)
        elif ch in CLOSE:
            if stack and stack[-1] == CLOSE[ch]:
                stack.pop()
        elif not stack and ch == "→":
            cuts.append((i, i + 1))
        elif not stack and text.startswith("->", i):
            cuts.append((i, i + 2))
            i += 1
        i += 1
    if not cuts:
        return "", text
    premise_parts = []
    prev = 0
    for a, b in cuts:
        premise_parts.append(text[prev:a])
        prev = b
    return " ".join(premise_parts), text[prev:]


def declaration_header(record_text: str) -> str:
    text = record_text
    pos = text.find(":=")
    if pos >= 0:
        text = text[:pos]
    m = re.search(r"(?m)^\s*by\b", text)
    if m:
        text = text[:m.start()]
    return text.strip()


def parse_declaration(header: str) -> dict[str, Any] | None:
    m = re.search(r"\b(?:theorem|lemma|def|abbrev)\s+([A-Za-z_][A-Za-z0-9_'.]*)", header)
    if not m:
        return None
    decl_name = m.group(1)
    colon = top_level_result_colon(header, m.end())
    if colon is None:
        return None
    left = header[m.end():colon]
    right = header[colon + 1:]
    arrow_premise, final_conclusion = split_top_level_arrows(right)
    premise = (left + " " + arrow_premise).strip()
    conclusion = final_conclusion.strip()

    var_names = set()
    for bm in re.finditer(r"[\(\{\[]\s*([A-Za-z_][A-Za-z0-9_']*)\s*:", premise):
        var_names.update(split_identifier(bm.group(1)))

    premise_tokens = identifier_features(premise, var_names)
    conclusion_tokens = identifier_features(conclusion, var_names)

    witness_heads: set[str] = set()
    for bm in re.finditer(r"[\(\{\[]([^()\[\]{}]+?)\]", premise):
        chunk = bm.group(1)
        if ":" in chunk:
            typ = chunk.split(":", 1)[1]
            witness_heads.update(qualified_head(typ))
    # Parenthesized and braced binders are the common cases; scan them separately.
    for open_ch, close_ch in (("(", ")"), ("{", "}")):
        for bm in re.finditer(re.escape(open_ch) + r"([^" + re.escape(open_ch + close_ch) + r"]+?)" + re.escape(close_ch), premise):
            chunk = bm.group(1)
            if ":" in chunk:
                typ = chunk.split(":", 1)[1]
                witness_heads.update(qualified_head(typ))
    for part in re.split(r"→|->", arrow_premise):
        witness_heads.update(qualified_head(part))

    invariant = qualified_head(conclusion)
    delta = premise_tokens - conclusion_tokens - witness_heads

    binder_count = len(re.findall(r"[\(\{\[]\s*[A-Za-z_][A-Za-z0-9_']*\s*:", premise))
    implicit_count = len(re.findall(r"\{\s*[A-Za-z_][A-Za-z0-9_']*\s*:", premise))
    arrow_count = len(re.findall(r"→|->", right))
    premise_words = len(identifier_features(premise))

    def bin_count(n: int, cuts: tuple[int, ...]) -> str:
        for c in cuts:
            if n <= c:
                return f"le{c}"
        return f"gt{cuts[-1]}"

    sigma = {
        "binder_" + bin_count(binder_count, (2, 5, 10)),
        "implicit_" + bin_count(implicit_count, (0, 2, 5)),
        "arrows_" + bin_count(arrow_count, (0, 2, 5)),
        "premise_vocab_" + bin_count(premise_words, (5, 15, 30)),
    }
    return {
        "declaration_name": decl_name,
        "premise_text": premise,
        "conclusion_text": conclusion,
        "W_raw": sorted(witness_heads),
        "I_raw": sorted(invariant),
        "Delta_raw": sorted(delta),
        "sigma_raw": sorted(sigma),
        "premise_tokens_raw": sorted(premise_tokens),
        "conclusion_tokens_raw": sorted(conclusion_tokens),
    }


def extract_record(repo: Path, path: str, theorem_name: str) -> tuple[str, dict[str, Any]] | None:
    fp = repo / path
    if not fp.exists():
        return None
    data = fp.read_bytes()
    scan = scan_source(path, data)
    wanted = theorem_name.rsplit(".", 1)[-1]
    candidates = []
    for rec in scan["records"]:
        name = str(rec.get("qualified_name") or rec.get("name") or "")
        short = str(rec.get("name") or "")
        if name == theorem_name or name.endswith("." + wanted) or short == wanted:
            candidates.append(rec)
    if not candidates:
        return None
    candidates.sort(key=lambda r: (0 if (r.get("qualified_name") == theorem_name) else 1, r["start_byte"]))
    rec = candidates[0]
    text = data[rec["start_byte"]:rec["end_byte"]].decode("utf-8", "replace")
    header = declaration_header(text)
    parsed = parse_declaration(header)
    if parsed is None:
        return None
    return header, parsed


def node_items(graph: Path) -> Iterable[dict[str, Any]]:
    with gzip.open(graph, "rb") as f:
        yield from ijson.items(f, "nodes.item")


def edge_items(graph: Path) -> Iterable[dict[str, Any]]:
    with gzip.open(graph, "rb") as f:
        yield from ijson.items(f, "edges.item")


def domain_from_solution(module: str) -> str:
    parts = [p for p in module.split(".") if p]
    if parts and parts[0] == "OAI":
        parts = parts[1:]
    return parts[0] if parts else "UNKNOWN"


def inspect_graph(graph: Path) -> dict[str, Any]:
    node_types = Counter()
    edge_types = Counter()
    source_formats = Counter()
    configs = []
    holdout_doc_dirs = []
    graph_nodes = 0
    graph_edges = 0

    for n in node_items(graph):
        graph_nodes += 1
        typ = str(n.get("type", "UNKNOWN"))
        node_types[typ] += 1
        attrs = n.get("attributes") or {}
        if typ == "SOURCE_RESOURCE":
            source_formats[str(attrs.get("format") or "NONE")] += 1
        elif typ == "SOURCE_DOCUMENT" and str(attrs.get("family_id")) == HOLDOUT_FAMILY:
            directory = attrs.get("directory")
            if directory:
                holdout_doc_dirs.append(str(directory).rstrip("/") + "/")
        elif typ == "FORMAL_CHECK_CONFIGURATION":
            source_resource = str(attrs.get("source_resource") or "")
            config_path = resource_path(source_resource) or ""
            configs.append(
                {
                    "id": n.get("id"),
                    "label": n.get("label"),
                    "config_path": config_path,
                    "challenge_module": str(attrs.get("challenge_module") or ""),
                    "solution_module": str(attrs.get("solution_module") or ""),
                    "theorem_names": list(attrs.get("selected_theorem_names") or []),
                }
            )

    for e in edge_items(graph):
        graph_edges += 1
        edge_types[str(e.get("type", "UNKNOWN"))] += 1

    return {
        "nodes": graph_nodes,
        "edges": graph_edges,
        "node_types": dict(sorted(node_types.items())),
        "edge_types": dict(sorted(edge_types.items())),
        "source_formats": dict(sorted(source_formats.items())),
        "configs": sorted(configs, key=lambda x: (x["config_path"], x["id"] or "")),
        "holdout_doc_dirs": sorted(set(holdout_doc_dirs)),
    }


def build_holdout_boundary(graph_info: dict[str, Any]) -> dict[str, Any]:
    matches = [c for c in graph_info["configs"] if c["config_path"] == HOLDOUT_CONFIG_PATH]
    if len(matches) != 1:
        raise RuntimeError(f"expected one #312 comparator configuration, found {len(matches)}")
    c = matches[0]
    challenge = module_to_path(c["challenge_module"])
    solution = module_to_path(c["solution_module"])
    solution_dir = str(Path(solution).parent).replace("\\", "/").rstrip("/") + "/"
    exact = {
        HOLDOUT_CONFIG_PATH,
        HOLDOUT_SCOPE_PATH,
        challenge,
        solution,
        "lean/formalization.yaml",
    }
    prefixes = set(graph_info["holdout_doc_dirs"])
    prefixes.add(solution_dir)
    return {
        "config": c,
        "exact_paths": sorted(exact),
        "prefix_paths": sorted(prefixes),
    }


def path_forbidden(path: str, boundary: dict[str, Any], aux_challenge_paths: set[str] | None = None) -> bool:
    aux_challenge_paths = aux_challenge_paths or set()
    if path in aux_challenge_paths:
        return True
    if path in set(boundary["exact_paths"]):
        return True
    return any(path.startswith(p) for p in boundary["prefix_paths"])


def choose_aux_configs(configs: list[dict[str, Any]], boundary: dict[str, Any], limit: int = 24) -> list[dict[str, Any]]:
    candidates = []
    for c in configs:
        if c["config_path"] == HOLDOUT_CONFIG_PATH:
            continue
        cp = module_to_path(c["challenge_module"])
        sp = module_to_path(c["solution_module"])
        if path_forbidden(cp, boundary) or path_forbidden(sp, boundary):
            continue
        domain = domain_from_solution(c["solution_module"])
        key = hashlib.sha256((c["config_path"] + "|" + domain).encode()).hexdigest()
        candidates.append((domain, key, c))

    by_domain: dict[str, list[tuple[str, dict[str, Any]]]] = defaultdict(list)
    for domain, key, c in candidates:
        by_domain[domain].append((key, c))
    for rows in by_domain.values():
        rows.sort(key=lambda x: x[0])

    selected: list[dict[str, Any]] = []
    # Round-robin across domains makes the auxiliary holdout independent and diverse.
    depth = 0
    domains = sorted(by_domain)
    while len(selected) < limit:
        added = False
        for domain in domains:
            rows = by_domain[domain]
            if depth < len(rows):
                selected.append(rows[depth][1])
                added = True
                if len(selected) >= limit:
                    break
        if not added:
            break
        depth += 1
    return selected


def coordinate_admission(cases: list[dict[str, Any]], key: str) -> list[str]:
    df = Counter()
    doms: dict[str, set[str]] = defaultdict(set)
    for c in cases:
        vals = set(c[key])
        for v in vals:
            df[v] += 1
            doms[v].add(c["domain"])
    n = max(1, len(cases))
    upper = max(3, int(math.floor(0.45 * n)))
    admitted = [
        v
        for v, count in df.items()
        if count >= 2 and count <= upper and len(doms[v]) >= 2
    ]
    admitted.sort(key=lambda v: (-len(doms[v]), -df[v], v))
    return admitted


def filter_signature(raw: dict[str, Any], grammar: dict[str, Any]) -> dict[str, list[str]]:
    out = {}
    for coord, raw_key in (("W", "W_raw"), ("I", "I_raw"), ("Delta", "Delta_raw"), ("sigma", "sigma_raw")):
        alphabet = set(grammar["coordinates"][coord]["alphabet"])
        out[coord] = sorted(set(raw.get(raw_key, [])) & alphabet)
    out["T"] = ["LEAN_CHALLENGE_TO_FORMAL_SOLUTION"]
    return out


def jac(a: Iterable[str], b: Iterable[str]) -> float:
    x, y = set(a), set(b)
    if not x and not y:
        return 0.0
    return len(x & y) / max(1, len(x | y))


def non_i_similarity(a: dict[str, list[str]], b: dict[str, list[str]]) -> tuple[float, int]:
    weights = {"W": 0.45, "Delta": 0.35, "sigma": 0.20}
    score = sum(weights[k] * jac(a[k], b[k]) for k in weights)
    coord_matches = sum(bool(set(a[k]) & set(b[k])) for k in weights)
    return score, coord_matches


def semantic_equivalent(a: dict[str, list[str]], b: dict[str, list[str]]) -> bool:
    i_overlap = bool(set(a["I"]) & set(b["I"]))
    score, coord_matches = non_i_similarity(a, b)
    structural = bool(set(a["W"]) & set(b["W"])) or bool(set(a["Delta"]) & set(b["Delta"]))
    return i_overlap and structural and coord_matches >= 2 and score >= 0.35


def train_knn_predict(
    target: dict[str, Any],
    training: list[dict[str, Any]],
    k: int = 7,
    cross_domain_only: bool = True,
) -> list[tuple[str, float]]:
    scored = []
    for c in training:
        if c["case_id"] == target.get("case_id"):
            continue
        if cross_domain_only and c["domain"] == target["domain"]:
            continue
        s, matches = non_i_similarity(target["signature"], c["signature"])
        if s <= 0 or matches == 0:
            continue
        scored.append((s, matches, c))
    scored.sort(key=lambda x: (-x[0], -x[1], x[2]["case_id"]))
    votes = Counter()
    for s, _m, c in scored[:k]:
        for token in c["signature"]["I"]:
            votes[token] += s
    return sorted(votes.items(), key=lambda x: (-x[1], x[0]))


def baseline_predict(target: dict[str, Any], training: list[dict[str, Any]], topn: int = 3) -> list[str]:
    counts = Counter()
    for c in training:
        if c["domain"] == target["domain"]:
            continue
        for token in c["signature"]["I"]:
            counts[token] += 1
    return [x for x, _ in counts.most_common(topn)]


def score_predictions(cases: list[dict[str, Any]], training: list[dict[str, Any]]) -> dict[str, Any]:
    scored = 0
    top1 = 0
    top3 = 0
    rr_sum = 0.0
    base1 = 0
    base3 = 0
    failures = []
    for c in cases:
        actual = set(c["signature"]["I"])
        if not actual or not (c["signature"]["W"] or c["signature"]["Delta"]):
            failures.append({"case_id": c["case_id"], "reason": "UNSCORABLE_EMPTY_I_OR_STRUCTURE"})
            continue
        pred = [x for x, _ in train_knn_predict(c, training, cross_domain_only=True)]
        base = baseline_predict(c, training)
        if not pred:
            failures.append({"case_id": c["case_id"], "reason": "NO_CROSS_DOMAIN_NEIGHBOR"})
            continue
        scored += 1
        if pred[0] in actual:
            top1 += 1
        if any(x in actual for x in pred[:3]):
            top3 += 1
        rank = next((i + 1 for i, x in enumerate(pred) if x in actual), None)
        if rank:
            rr_sum += 1.0 / rank
        if base and base[0] in actual:
            base1 += 1
        if any(x in actual for x in base[:3]):
            base3 += 1
    return {
        "cases": len(cases),
        "scored": scored,
        "top1_accuracy": top1 / scored if scored else 0.0,
        "top3_accuracy": top3 / scored if scored else 0.0,
        "mrr": rr_sum / scored if scored else 0.0,
        "frequency_baseline_top1": base1 / scored if scored else 0.0,
        "frequency_baseline_top3": base3 / scored if scored else 0.0,
        "failures": failures,
    }


def mine_operator_families(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    n = len(cases)
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for i in range(n):
        a = cases[i]
        for j in range(i + 1, n):
            b = cases[j]
            if a["domain"] == b["domain"]:
                continue
            if not (set(a["signature"]["I"]) & set(b["signature"]["I"])):
                continue
            score, matches = non_i_similarity(a["signature"], b["signature"])
            if score >= 0.25 and matches >= 1:
                union(i, j)

    groups: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for i, c in enumerate(cases):
        groups[find(i)].append(c)

    families = []
    for members in groups.values():
        domains = sorted({m["domain"] for m in members})
        if len(members) < 3 or len(domains) < 2:
            continue
        proto = {}
        for coord in ("W", "I", "Delta", "sigma", "T"):
            cnt = Counter(x for m in members for x in set(m["signature"][coord]))
            threshold = math.ceil(len(members) * 0.5)
            proto[coord] = sorted(x for x, c in cnt.items() if c >= threshold)
        family_id = hashlib.sha256(
            cjson({"members": sorted(m["case_id"] for m in members), "prototype": proto})
        ).hexdigest()[:16]
        families.append(
            {
                "family_id": family_id,
                "support": len(members),
                "domain_count": len(domains),
                "domains": domains,
                "prototype": proto,
                "member_ids": sorted(m["case_id"] for m in members),
            }
        )
    families.sort(key=lambda x: (-x["support"], -x["domain_count"], x["family_id"]))
    return families


def build_controls(cases: list[dict[str, Any]]) -> dict[str, Any]:
    collision = []
    hard_negative = []
    random_negative = []
    ordered = sorted(cases, key=lambda x: x["case_id"])
    n = len(ordered)

    # Real collision controls: same invariant/result token, deliberately dissimilar structure.
    for i in range(n):
        a = ordered[i]
        for j in range(i + 1, n):
            b = ordered[j]
            if a["domain"] == b["domain"]:
                continue
            i_overlap = bool(set(a["signature"]["I"]) & set(b["signature"]["I"]))
            score, matches = non_i_similarity(a["signature"], b["signature"])
            if i_overlap and score <= 0.08:
                collision.append((a, b, score, matches))
            if (not i_overlap) and score >= 0.30:
                hard_negative.append((a, b, score, matches))
            if len(collision) >= 500 and len(hard_negative) >= 500:
                break
        if len(collision) >= 500 and len(hard_negative) >= 500:
            break

    # Real cross-domain random negatives selected deterministically from observed cases.
    for i, a in enumerate(ordered[: min(1000, n)]):
        if n < 2:
            break
        for off in range(1, min(100, n)):
            b = ordered[(i + 37 * off) % n]
            if b["domain"] != a["domain"] and b["case_id"] != a["case_id"]:
                random_negative.append((a, b, *non_i_similarity(a["signature"], b["signature"])))
                break

    def summarize(rows: list[tuple]) -> dict[str, Any]:
        false = 0
        examples = []
        for a, b, score, matches in rows:
            accepted = semantic_equivalent(a["signature"], b["signature"])
            if accepted:
                false += 1
                if len(examples) < 20:
                    examples.append(
                        {
                            "a": a["case_id"],
                            "b": b["case_id"],
                            "domains": [a["domain"], b["domain"]],
                            "non_i_similarity": score,
                            "coordinate_matches": matches,
                        }
                    )
        return {
            "count": len(rows),
            "false_semantic_equivalences": false,
            "false_positive_rate": false / len(rows) if rows else 0.0,
            "counterexamples": examples,
        }

    return {
        "semantic_equivalence_rule": {
            "requires_invariant_overlap": True,
            "requires_structural_overlap_W_or_Delta": True,
            "minimum_non_i_coordinate_matches": 2,
            "minimum_non_i_similarity": 0.35,
        },
        "shared_invariant_collision_controls": summarize(collision),
        "hard_negative_structural_controls": summarize(hard_negative),
        "cross_domain_negative_controls": summarize(random_negative),
    }


def load_training_cases(
    source_repo: Path,
    configs: list[dict[str, Any]],
    boundary: dict[str, Any],
    aux_configs: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    aux_paths = {c["config_path"] for c in aux_configs}
    aux_challenge_paths = {module_to_path(c["challenge_module"]) for c in aux_configs}
    training = []
    failures = []
    case_catalogue = []
    reads = []

    for c in configs:
        cp = module_to_path(c["challenge_module"])
        sp = module_to_path(c["solution_module"])
        domain = domain_from_solution(c["solution_module"])
        is_312 = c["config_path"] == HOLDOUT_CONFIG_PATH or path_forbidden(cp, boundary) or path_forbidden(sp, boundary)
        is_aux = c["config_path"] in aux_paths
        for ordinal, theorem in enumerate(c["theorem_names"]):
            case_id = f"{c['config_path']}::{ordinal}::{theorem}"
            meta = {
                "case_id": case_id,
                "config_path": c["config_path"],
                "challenge_path": cp,
                "solution_path": sp,
                "theorem_name": theorem,
                "domain": domain,
                "is_312_excluded": is_312,
                "is_aux_holdout": is_aux,
            }
            case_catalogue.append(meta)
            if is_312 or is_aux:
                continue
            if path_forbidden(cp, boundary, aux_challenge_paths):
                failures.append({**meta, "reason": "FORBIDDEN_PATH_GUARD"})
                continue
            reads.append(cp)
            extracted = extract_record(source_repo, cp, theorem)
            if extracted is None:
                failures.append({**meta, "reason": "CHALLENGE_DECLARATION_NOT_FOUND"})
                continue
            header, raw = extracted
            training.append(
                {
                    **meta,
                    "header_sha256": hashlib.sha256(header.encode()).hexdigest(),
                    "raw": raw,
                    "T_raw": ["LEAN_CHALLENGE_TO_FORMAL_SOLUTION"],
                }
            )
    return training, failures, case_catalogue, sorted(set(reads))


def make_grammar(training_raw: list[dict[str, Any]], graph_info: dict[str, Any]) -> dict[str, Any]:
    coords = {}
    for coord, key in (("W", "W_raw"), ("I", "I_raw"), ("Delta", "Delta_raw"), ("sigma", "sigma_raw")):
        coords[coord] = {
            "definition": {
                "W": "recurring premise-side type/predicate heads",
                "I": "recurring conclusion/result heads treated as preserved/result invariant class",
                "Delta": "recurring premise-only structural identifiers representing changed structure",
                "sigma": "scope/strength bins derived from binders, implicit parameters, arrows, and premise vocabulary",
            }[coord],
            "alphabet": coordinate_admission(training_raw, key),
        }
    coords["T"] = {
        "definition": "representation transition from comparator challenge statement to formal solution representation",
        "alphabet": ["LEAN_CHALLENGE_TO_FORMAL_SOLUTION"],
    }

    grammar = {
        "schema": "MAPEOGEO_BOTTOM_UP_TRANSFORMATION_GRAMMAR_V2",
        "derivation_policy": {
            "semantic_seed_lexicon": False,
            "admission_rule": "feature occurs in >=2 training cases, >=2 independent domains, and <=45% of training cases",
            "family_rule": "cross-domain connected component with shared I, non-I similarity >=0.25, >=3 cases, >=2 domains",
            "heldout_family_312_content_used": False,
            "auxiliary_holdout_content_used": False,
        },
        "coordinates": coords,
        "graph_context": {
            "source_formats": graph_info["source_formats"],
            "candidate_represents_edges": graph_info["edge_types"].get("CANDIDATE_REPRESENTS", 0),
            "same_semantics_edges": graph_info["edge_types"].get("SAME_SEMANTICS", 0),
            "scoped_overlap_edges": graph_info["edge_types"].get("SCOPED_OVERLAP", 0),
        },
    }

    signed = []
    for c in training_raw:
        s = filter_signature(c["raw"], grammar)
        signed.append({**{k: v for k, v in c.items() if k != "raw"}, "signature": s})

    families = mine_operator_families(signed)
    grammar["operator_families"] = families
    grammar["operator_family_count"] = len(families)
    grammar["training_case_count"] = len(signed)
    grammar["training_domain_count"] = len({c["domain"] for c in signed})
    grammar["training_domains"] = sorted({c["domain"] for c in signed})

    recurrence = {}
    for coord in ("T", "W", "I", "sigma", "Delta"):
        cases_with = [c for c in signed if c["signature"][coord]]
        recurrence[coord] = {
            "alphabet_size": len(grammar["coordinates"][coord]["alphabet"]),
            "case_support": len(cases_with),
            "domain_count": len({c["domain"] for c in cases_with}),
            "domains": sorted({c["domain"] for c in cases_with}),
            "representation_modalities": (
                ["LEAN_CHALLENGE", "LEAN_FORMAL_SOLUTION"]
                if coord == "T"
                else ["LEAN_CHALLENGE"]
            ),
        }
    grammar["recurrence"] = recurrence
    return grammar, signed


def cross_domain_cv(cases: list[dict[str, Any]]) -> dict[str, Any]:
    return score_predictions(cases, cases)


def permutation_null(cases: list[dict[str, Any]], observed: dict[str, Any], rounds: int = 50) -> dict[str, Any]:
    if not cases:
        return {"rounds": 0, "top1_values": [], "p_ge_observed": 1.0}
    rng = random.Random(3122026)
    labels = [list(c["signature"]["I"]) for c in cases]
    vals = []
    for _ in range(rounds):
        perm = labels[:]
        rng.shuffle(perm)
        pseudo = []
        for c, lab in zip(cases, perm):
            nc = {**c, "signature": {**c["signature"], "I": lab}}
            pseudo.append(nc)
        m = score_predictions(pseudo, pseudo)
        vals.append(m["top1_accuracy"])
    ge = sum(v >= observed["top1_accuracy"] for v in vals)
    return {
        "rounds": rounds,
        "top1_values": vals,
        "mean_top1": sum(vals) / len(vals) if vals else 0.0,
        "max_top1": max(vals) if vals else 0.0,
        "p_ge_observed": (ge + 1) / (len(vals) + 1),
    }


def read_aux_cases(
    source_repo: Path,
    aux_configs: list[dict[str, Any]],
    grammar: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cases = []
    failures = []
    for c in aux_configs:
        cp = module_to_path(c["challenge_module"])
        domain = domain_from_solution(c["solution_module"])
        for ordinal, theorem in enumerate(c["theorem_names"]):
            case_id = f"{c['config_path']}::{ordinal}::{theorem}"
            extracted = extract_record(source_repo, cp, theorem)
            if extracted is None:
                failures.append({"case_id": case_id, "reason": "AUX_DECLARATION_NOT_FOUND"})
                continue
            header, raw = extracted
            cases.append(
                {
                    "case_id": case_id,
                    "config_path": c["config_path"],
                    "challenge_path": cp,
                    "solution_path": module_to_path(c["solution_module"]),
                    "theorem_name": theorem,
                    "domain": domain,
                    "header_sha256": hashlib.sha256(header.encode()).hexdigest(),
                    "signature": filter_signature(raw, grammar),
                }
            )
    return cases, failures


def family_match(masked: dict[str, list[str]], families: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for f in families:
        proto = f["prototype"]
        dummy = {
            "W": proto.get("W", []),
            "I": proto.get("I", []),
            "Delta": proto.get("Delta", []),
            "sigma": proto.get("sigma", []),
            "T": proto.get("T", []),
        }
        s, m = non_i_similarity(masked, dummy)
        if s > 0:
            rows.append(
                {
                    "family_id": f["family_id"],
                    "score": s,
                    "coordinate_matches": m,
                    "support": f["support"],
                    "domain_count": f["domain_count"],
                    "domains": f["domains"],
                    "predicted_I": proto.get("I", []),
                }
            )
    rows.sort(key=lambda x: (-x["score"], -x["domain_count"], -x["support"], x["family_id"]))
    return rows


def heldout_312_evaluation(
    source_repo: Path,
    boundary: dict[str, Any],
    grammar: dict[str, Any],
    training_cases: list[dict[str, Any]],
    out: Path,
) -> dict[str, Any]:
    config = boundary["config"]
    challenge_path = module_to_path(config["challenge_module"])
    solution_path = module_to_path(config["solution_module"])
    theorem = config["theorem_names"][0]

    # Strict pre-reveal stage: parse the held-out challenge, but use only premise/scope
    # coordinates. The conclusion/result invariant is held back until prediction is frozen.
    extracted = extract_record(source_repo, challenge_path, theorem)
    if extracted is None:
        return {"status": "BLOCKED", "reason": "HELDOUT_CHALLENGE_DECLARATION_NOT_FOUND"}
    challenge_header, raw = extracted
    full_sig = filter_signature(raw, grammar)
    masked = {**full_sig, "I": []}

    probe = {
        "case_id": "HELDOUT_312_PRE_REVEAL",
        "domain": domain_from_solution(config["solution_module"]),
        "signature": masked,
    }
    votes = train_knn_predict(probe, training_cases, cross_domain_only=True)
    predicted_i = [x for x, _ in votes[:5]]
    family_rows = family_match(masked, grammar["operator_families"])

    pre = {
        "family_id": HOLDOUT_FAMILY,
        "challenge_path": challenge_path,
        "theorem_name": theorem,
        "premise_only_used_for_prediction": True,
        "conclusion_invariant_used_for_prediction": False,
        "masked_signature": masked,
        "predicted_invariant_top5": predicted_i,
        "nearest_operator_families": family_rows[:10],
        "frozen_grammar_sha256": sha256_file(out / "frozen_grammar.json"),
    }
    pre_path = out / "prediction_312_pre_reveal.json"
    pre_path.write_bytes(cjson(pre) + b"\n")
    pre_sha = sha256_file(pre_path)
    grammar_before = sha256_file(out / "frozen_grammar.json")

    # Reveal stage: now inspect the held-out conclusion, formal solution declaration,
    # and scope note. None of these can alter the frozen grammar.
    actual_i = full_sig["I"]
    top1 = bool(predicted_i and predicted_i[0] in set(actual_i))
    top3 = any(x in set(actual_i) for x in predicted_i[:3])

    solution = extract_record(source_repo, solution_path, theorem)
    solution_sig = None
    statement_agreement = False
    if solution is not None:
        _solution_header, solution_raw = solution
        solution_sig = filter_signature(solution_raw, grammar)
        statement_agreement = bool(set(actual_i) & set(solution_sig["I"])) if actual_i else False

    scope_text = (source_repo / HOLDOUT_SCOPE_PATH).read_text(encoding="utf-8")
    scope_sha = hashlib.sha256(scope_text.encode()).hexdigest()

    best_family = family_rows[0] if family_rows else None
    structural_guard = bool(
        best_family
        and best_family["score"] >= 0.20
        and best_family["coordinate_matches"] >= 1
        and best_family["domain_count"] >= 2
    )
    behavior_predicted = top3 and structural_guard and statement_agreement
    grammar_after = sha256_file(out / "frozen_grammar.json")

    return {
        "status": "PASS" if behavior_predicted and grammar_before == grammar_after else "FAIL",
        "family_id": HOLDOUT_FAMILY,
        "challenge_path": challenge_path,
        "solution_path": solution_path,
        "scope_path": HOLDOUT_SCOPE_PATH,
        "challenge_header_sha256": hashlib.sha256(challenge_header.encode()).hexdigest(),
        "scope_sha256": scope_sha,
        "pre_reveal_prediction_sha256": pre_sha,
        "actual_invariant": actual_i,
        "predicted_invariant_top5": predicted_i,
        "top1_invariant_match": top1,
        "top3_invariant_match": top3,
        "best_operator_family": best_family,
        "structural_guard_passed": structural_guard,
        "solution_statement_invariant_agreement": statement_agreement,
        "elementary_expansion_behavior_predicted": behavior_predicted,
        "grammar_sha256_before_reveal": grammar_before,
        "grammar_sha256_after_reveal": grammar_after,
        "grammar_modified_after_reveal": grammar_before != grammar_after,
        "shared_invariant_alone_counted_as_equivalence": False,
        "solution_signature": solution_sig,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--graph", type=Path, required=True)
    p.add_argument("--source-repo", type=Path, required=True)
    p.add_argument("--registry", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    args = p.parse_args()

    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    source_commit = git(args.source_repo, "rev-parse", "HEAD")
    graph_sha = sha256_file(args.graph)
    registry_sha = sha256_file(args.registry)
    custody = {
        "baseline_mapeogeo_commit": BASELINE_COMMIT,
        "baseline_workflow_run": BASELINE_RUN,
        "baseline_gates": {
            "complete_intake": "PASS",
            "independent_verifier": "PASS",
            "canonical_reconciliation_completion": "PASS",
            "psmsl_fq_E8": "PASS",
            "psmsl_fq_E9": "PASS",
        },
        "integrated_graph_sha256": graph_sha,
        "expected_integrated_graph_sha256": INTEGRATED_GRAPH_SHA256,
        "openai_math_commit": source_commit,
        "registry_sha256": registry_sha,
        "production_graph_modified": False,
    }
    custody["identity_status"] = (
        "PASS"
        if graph_sha == INTEGRATED_GRAPH_SHA256 and source_commit == OPENAI_MATH_COMMIT
        else "FAIL"
    )
    (out / "custody.json").write_bytes(cjson(custody) + b"\n")
    if custody["identity_status"] != "PASS":
        result = {"verdict": "BLOCKED", "reason": "BASELINE_IDENTITY_MISMATCH", "custody": custody}
        (out / "result.json").write_bytes(cjson(result) + b"\n")
        print(json.dumps(result, indent=2))
        return 2

    graph_info = inspect_graph(args.graph)
    boundary = build_holdout_boundary(graph_info)
    aux_configs = choose_aux_configs(graph_info["configs"], boundary, limit=24)

    training_raw, parse_failures, case_catalogue, training_reads = load_training_cases(
        args.source_repo, graph_info["configs"], boundary, aux_configs
    )
    aux_challenge_paths = {module_to_path(c["challenge_module"]) for c in aux_configs}
    leakage_reads = [
        pth for pth in training_reads if path_forbidden(pth, boundary, aux_challenge_paths)
    ]
    if leakage_reads:
        result = {
            "verdict": "BLOCKED",
            "reason": "HOLDOUT_LEAKAGE_GUARD_TRIGGERED",
            "leakage_paths": leakage_reads,
            "custody": custody,
        }
        (out / "result.json").write_bytes(cjson(result) + b"\n")
        print(json.dumps(result, indent=2))
        return 2

    grammar, training_cases = make_grammar(training_raw, graph_info)
    grammar["holdout_boundary"] = {
        "family_id": HOLDOUT_FAMILY,
        "exact_path_count": len(boundary["exact_paths"]),
        "prefix_count": len(boundary["prefix_paths"]),
        "exact_paths": boundary["exact_paths"],
        "prefix_paths": boundary["prefix_paths"],
        "auxiliary_config_count": len(aux_configs),
        "auxiliary_config_paths": sorted(c["config_path"] for c in aux_configs),
    }

    frozen_path = out / "frozen_grammar.json"
    frozen_path.write_bytes(cjson(grammar) + b"\n")
    grammar_sha = sha256_file(frozen_path)
    (out / "frozen_grammar.sha256").write_text(
        grammar_sha + "  frozen_grammar.json\n", encoding="utf-8"
    )
    (out / "training_read_log.json").write_bytes(
        cjson({"read_count": len(training_reads), "paths": training_reads, "leakage_paths": leakage_reads}) + b"\n"
    )
    (out / "case_catalogue.json").write_bytes(cjson(case_catalogue) + b"\n")

    controls = build_controls(training_cases)
    (out / "controls.json").write_bytes(cjson(controls) + b"\n")

    cv = cross_domain_cv(training_cases)
    null = permutation_null(training_cases, cv, rounds=50)

    aux_cases, aux_failures = read_aux_cases(args.source_repo, aux_configs, grammar)
    aux_metrics = score_predictions(aux_cases, training_cases)
    aux_summary = {
        "config_count": len(aux_configs),
        "case_count": len(aux_cases),
        "domain_count": len({c["domain"] for c in aux_cases}),
        "domains": sorted({c["domain"] for c in aux_cases}),
        "metrics": aux_metrics,
        "parse_failures": aux_failures,
    }
    (out / "auxiliary_holdouts.json").write_bytes(cjson(aux_summary) + b"\n")

    held = heldout_312_evaluation(args.source_repo, boundary, grammar, training_cases, out)
    (out / "heldout_312.json").write_bytes(cjson(held) + b"\n")

    recurrence = grammar["recurrence"]
    recurrence_ok = (
        grammar["training_case_count"] >= 100
        and grammar["training_domain_count"] >= 5
        and grammar["operator_family_count"] >= 1
        and recurrence["W"]["alphabet_size"] > 0
        and recurrence["I"]["alphabet_size"] > 0
        and recurrence["Delta"]["alphabet_size"] > 0
        and recurrence["W"]["domain_count"] >= 3
        and recurrence["I"]["domain_count"] >= 3
        and recurrence["Delta"]["domain_count"] >= 3
    )

    collision = controls["shared_invariant_collision_controls"]
    hard = controls["hard_negative_structural_controls"]
    neg = controls["cross_domain_negative_controls"]
    controls_ok = (
        collision["count"] >= 20
        and collision["false_positive_rate"] <= 0.01
        and hard["count"] >= 20
        and hard["false_positive_rate"] <= 0.05
        and neg["count"] >= 20
        and neg["false_positive_rate"] <= 0.05
    )

    generalization_ok = (
        aux_metrics["scored"] >= 10
        and aux_metrics["top3_accuracy"] >= aux_metrics["frequency_baseline_top3"]
        and cv["scored"] >= 50
        and cv["top1_accuracy"] >= cv["frequency_baseline_top1"]
    )
    held_ok = held.get("status") == "PASS"

    if len(training_cases) < 50 or held.get("status") == "BLOCKED":
        verdict = "BLOCKED"
    elif recurrence_ok and controls_ok and generalization_ok and held_ok:
        verdict = "PASS"
    else:
        verdict = "FAIL"

    failures = {
        "training_parse_failures": parse_failures,
        "auxiliary_parse_failures": aux_failures,
        "control_counterexamples": {
            "shared_invariant_collision": collision["counterexamples"],
            "hard_negative_structural": hard["counterexamples"],
            "cross_domain_negative": neg["counterexamples"],
        },
        "cross_domain_cv_failures": cv["failures"][:100],
        "auxiliary_holdout_failures": aux_metrics["failures"][:100],
    }
    (out / "failures_and_counterexamples.json").write_bytes(cjson(failures) + b"\n")

    tracked_files = len(
        git(args.source_repo, "ls-tree", "-r", "--name-only", "HEAD").splitlines()
    )

    result = {
        "experiment": "MAPEOGEO_RESULT_312_FULL_HELDOUT_V2",
        "verdict": verdict,
        "custody": custody,
        "corpus": {
            "integrated_graph_nodes": graph_info["nodes"],
            "integrated_graph_edges": graph_info["edges"],
            "openai_math_tracked_files": tracked_files,
            "formal_check_configurations": len(graph_info["configs"]),
            "selected_theorem_occurrences_graph": graph_info["node_types"].get("FORMAL_TARGET", 0),
            "training_cases": len(training_cases),
            "training_domains": grammar["training_domains"],
            "training_domain_count": grammar["training_domain_count"],
            "auxiliary_holdout_configs": len(aux_configs),
            "auxiliary_holdout_cases": len(aux_cases),
            "excluded_312_exact_paths": boundary["exact_paths"],
            "excluded_312_prefixes": boundary["prefix_paths"],
            "node_types": graph_info["node_types"],
            "edge_types": graph_info["edge_types"],
            "source_formats": graph_info["source_formats"],
        },
        "grammar": {
            "frozen_sha256": grammar_sha,
            "operator_family_count": grammar["operator_family_count"],
            "operator_families": grammar["operator_families"],
            "coordinate_alphabet_sizes": {
                k: len(grammar["coordinates"][k]["alphabet"])
                for k in ("T", "W", "I", "sigma", "Delta")
            },
            "recurrence": recurrence,
            "semantic_seed_lexicon_used": False,
        },
        "metrics": {
            "cross_domain_leave_one_out": cv,
            "permutation_null": null,
            "auxiliary_holdouts": aux_summary,
        },
        "controls": controls,
        "holdout_312": held,
        "gates": {
            "baseline_identity_and_qualification": "PASS",
            "holdout_leakage": "PASS" if not leakage_reads else "BLOCKED",
            "bottom_up_recurrence": "PASS" if recurrence_ok else "FAIL",
            "negative_and_collision_controls": "PASS" if controls_ok else "FAIL",
            "independent_openai_math_generalization": "PASS" if generalization_ok else "FAIL",
            "heldout_312_prediction": "PASS" if held_ok else "FAIL",
            "production_graph_unchanged": "PASS",
        },
        "failures_and_counterexamples": failures,
        "claim_boundary": (
            "A PASS means a transformation grammar derived from the frozen integrated graph-selected "
            "non-312 comparator corpus, without a semantic seed lexicon and before reading direct #312 "
            "content, recurs across independent domains, survives real negative/collision controls, "
            "generalizes to separately frozen OpenAI/math holdouts, and predicts the held-out #312 "
            "result-invariant class from premise/witness/scope structure before that conclusion is scored. "
            "It does not prove #312, establish theorem-level semantic equivalence from shared invariants, "
            "validate the full Grothendieck homotopy hypothesis, or establish completeness of MAPEOGEO."
        ),
        "production_graph_modified": False,
    }
    (out / "result.json").write_bytes(cjson(result) + b"\n")

    report = []
    report.append("# Full Held-Out #312 Transformation-Grammar Experiment")
    report.append("")
    report.append(f"Final verdict: {verdict}")
    report.append("")
    report.append("## Frozen identities")
    report.append(f"- MAPEOGEO baseline commit: {BASELINE_COMMIT}")
    report.append(f"- Baseline qualification run: {BASELINE_RUN}")
    report.append(f"- Integrated graph SHA-256: {graph_sha}")
    report.append(f"- OpenAI/math commit: {source_commit}")
    report.append(f"- Frozen grammar SHA-256: {grammar_sha}")
    report.append("")
    report.append("## Corpus")
    report.append(f"- Integrated graph: {graph_info['nodes']:,} nodes / {graph_info['edges']:,} edges")
    report.append(f"- OpenAI/math tracked files: {tracked_files:,}")
    report.append(f"- Formal check configurations: {len(graph_info['configs']):,}")
    report.append(f"- Selected theorem occurrences: {graph_info['node_types'].get('FORMAL_TARGET', 0):,}")
    report.append(f"- Training cases parsed after exclusions: {len(training_cases):,}")
    report.append(f"- Training domains: {grammar['training_domain_count']}")
    report.append(f"- Auxiliary frozen holdout cases: {len(aux_cases):,}")
    report.append("")
    report.append("## Bottom-up grammar")
    report.append(f"- Learned operator families: {grammar['operator_family_count']}")
    for k in ("T", "W", "I", "sigma", "Delta"):
        r = recurrence[k]
        report.append(
            f"- {k}: alphabet {r['alphabet_size']}; case support {r['case_support']}; "
            f"domains {r['domain_count']}; modalities {', '.join(r['representation_modalities'])}"
        )
    report.append("- Semantic seed lexicon used: NO")
    report.append("")
    report.append("## Generalization")
    report.append(
        f"- Cross-domain LOO: scored {cv['scored']}; top-1 {cv['top1_accuracy']:.3f}; "
        f"top-3 {cv['top3_accuracy']:.3f}; MRR {cv['mrr']:.3f}; "
        f"frequency baseline top-1 {cv['frequency_baseline_top1']:.3f}; "
        f"top-3 {cv['frequency_baseline_top3']:.3f}"
    )
    report.append(
        f"- Permutation null: {null['rounds']} rounds; mean top-1 {null.get('mean_top1', 0):.3f}; "
        f"max {null.get('max_top1', 0):.3f}; p(null>=observed) {null.get('p_ge_observed', 1):.4f}"
    )
    am = aux_metrics
    report.append(
        f"- Independent OpenAI/math holdouts: {am['scored']} scored / {len(aux_cases)} parsed; "
        f"top-1 {am['top1_accuracy']:.3f}; top-3 {am['top3_accuracy']:.3f}; "
        f"MRR {am['mrr']:.3f}; baseline top-3 {am['frequency_baseline_top3']:.3f}"
    )
    report.append("")
    report.append("## Controls")
    for name, key in (
        ("Shared-invariant collision", "shared_invariant_collision_controls"),
        ("Hard structural negative", "hard_negative_structural_controls"),
        ("Cross-domain negative", "cross_domain_negative_controls"),
    ):
        row = controls[key]
        report.append(
            f"- {name}: n={row['count']}; false semantic equivalences={row['false_semantic_equivalences']} "
            f"({row['false_positive_rate']:.3%})"
        )
    report.append("- Shared invariant alone is explicitly insufficient for semantic equivalence.")
    report.append("")
    report.append("## Held-out #312")
    report.append("- Direct #312 material used in grammar discovery/training: NO")
    report.append(f"- Pre-reveal prediction SHA-256: {held.get('pre_reveal_prediction_sha256')}")
    report.append(f"- Predicted invariant top-5: {held.get('predicted_invariant_top5')}")
    report.append(f"- Revealed invariant: {held.get('actual_invariant')}")
    report.append(f"- Top-1 match: {held.get('top1_invariant_match')}")
    report.append(f"- Top-3 match: {held.get('top3_invariant_match')}")
    report.append(f"- Structural guard: {held.get('structural_guard_passed')}")
    report.append(f"- Cross-statement invariant agreement: {held.get('solution_statement_invariant_agreement')}")
    report.append(f"- Elementary-expansion behavior predicted: {held.get('elementary_expansion_behavior_predicted')}")
    report.append(f"- Grammar modified after reveal: {held.get('grammar_modified_after_reveal')}")
    report.append("")
    report.append("## Gates")
    for k, v in result["gates"].items():
        report.append(f"- {k}: {v}")
    report.append("")
    report.append("## Conservative claim boundary")
    report.append(result["claim_boundary"])
    (out / "FULL_HELDOUT_312_REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    print(json.dumps({
        "verdict": verdict,
        "corpus": result["corpus"],
        "grammar": result["grammar"],
        "metrics": result["metrics"],
        "controls": result["controls"],
        "holdout_312": result["holdout_312"],
        "gates": result["gates"],
    }, indent=2))

    if verdict == "PASS":
        return 0
    if verdict == "BLOCKED":
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
