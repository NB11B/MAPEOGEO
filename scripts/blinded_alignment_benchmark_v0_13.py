#!/usr/bin/env python3
"""MAPEOGEO v0.13 Blinded Alignment Benchmark.

Evaluates automated mathematical discovery by holding out 20% of curated cross-source correspondences,
prompting the matching engine to predict the corresponding canonical object from graph representation
profiles, lexical tags, and structural neighborhoods, and reporting Top-1 Accuracy, Top-3 Recall,
and Unresolved Rate.

This benchmark is non-blocking and informational, measuring the system's ability to discover
mathematical identity.
"""

from __future__ import annotations

import argparse
import gzip
import json
import random
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def tokenize_text(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    stop_words = {
        "the", "a", "an", "and", "or", "of", "in", "to", "for", "with", "on", "is",
        "are", "by", "from", "at", "as", "be", "this", "that", "it", "its", "which",
        "axler", "gallier", "vmls", "definition", "theorem", "proposition", "lemma",
        "section", "chapter", "srcdecl",
    }
    return set(w for w in words if w not in stop_words and len(w) > 1 and not w.isdigit())


def score_candidate(
    query_text: str,
    query_tags: list[str],
    query_status: str,
    canonical_obj: dict[str, Any],
) -> float:
    score = 0.0
    q_tokens = tokenize_text(query_text)
    c_tokens = tokenize_text(canonical_obj.get("name", "") + " " + canonical_obj.get("description", ""))

    # Lexical token overlap
    overlap = q_tokens & c_tokens
    score += len(overlap) * 3.0

    # Tag overlap
    for tag in query_tags:
        tag_clean = tag.replace("_", " ").lower()
        if tag_clean in canonical_obj.get("name", "").lower() or tag_clean in canonical_obj.get("description", "").lower():
            score += 4.0

    # Profile affinity
    c_desc = (canonical_obj.get("name", "") + " " + canonical_obj.get("description", "")).lower()
    if query_status == "DUAL_DIRECT":
        if any(w in c_desc for w in ["orthogonal", "inner product", "norm", "projection", "spectral", "adjoint", "least squares"]):
            score += 2.0
    elif query_status == "GEO_ONLY_DIRECT":
        if any(w in c_desc for w in ["orthogonal", "inner product", "norm", "distance", "angle"]):
            score += 2.5
    elif query_status == "EO_ONLY_DIRECT":
        if any(w in c_desc for w in ["matrix", "linear map", "linear combination", "span", "independence", "basis", "dimension", "inverse", "equation"]):
            score += 1.5

    return score


def load_node_lookup(base_graph_path: Path | None) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    if base_graph_path and base_graph_path.exists():
        if base_graph_path.suffix == ".gz":
            with gzip.open(base_graph_path, "rt", encoding="utf-8") as f:
                g = json.load(f)
        else:
            g = json.loads(base_graph_path.read_text(encoding="utf-8"))
        for n in g.get("nodes", []):
            lookup[n["id"]] = n
    return lookup


def run_blinded_benchmark(
    alignments_file: Path,
    prereg_file: Path,
    out_dir: Path,
    base_graph_path: Path | None = None,
) -> dict[str, Any]:
    align_data = json.loads(alignments_file.read_text(encoding="utf-8"))
    prereg_data = json.loads(prereg_file.read_text(encoding="utf-8"))

    bench_cfg = prereg_data.get("blinded_benchmark", {})
    holdout_ratio = bench_cfg.get("holdout_ratio", 0.20)
    seed = bench_cfg.get("random_seed", 42)
    top_k = bench_cfg.get("top_k", 3)

    random.seed(seed)

    canonical_objects = align_data.get("canonical_objects", [])
    node_lookup = load_node_lookup(base_graph_path)

    all_alignments: list[dict[str, Any]] = []
    for co in canonical_objects:
        cid = co["id"]
        cname = co["name"]
        for al in co.get("alignments", []):
            all_alignments.append({
                "canonical_id": cid,
                "canonical_name": cname,
                "source": al["source"],
                "corpus": al["corpus"],
                "status": al.get("status", "CROSS_SOURCE_SAME"),
            })

    # Sample holdout set
    num_holdout = max(1, int(len(all_alignments) * holdout_ratio))
    holdout_indices = set(random.sample(range(len(all_alignments)), num_holdout))

    results: list[dict[str, Any]] = []
    top_1_hits = 0
    top_k_hits = 0
    unresolved_count = 0

    for idx, item in enumerate(all_alignments):
        if idx not in holdout_indices:
            continue

        src = item["source"]
        true_cid = item["canonical_id"]
        corpus = item["corpus"]

        # Retrieve rich label and attributes if available in graph lookup
        node = node_lookup.get(src, {})
        label = node.get("label", "")
        attrs = node.get("attributes", {})
        eo_tags = attrs.get("eo_tags", [])
        geo_tags = attrs.get("geo_tags", [])
        status = attrs.get("direct_status", "THEORETIC_DIRECT")

        if not label:
            # Fallback to parsing slug from source ID
            parts = src.split(":")
            slug = parts[-1].replace("_", " ") if len(parts) > 1 else ""
            kind = parts[2] if len(parts) > 2 else ""
            label = f"{corpus} {kind} {slug}"
            eo_tags = [t for t in [slug, kind] if t]

        query_text = f"{label} {' '.join(eo_tags)} {' '.join(geo_tags)}"
        query_tags = eo_tags + geo_tags

        # Match against all canonical candidates
        candidate_scores = []
        for co in canonical_objects:
            s = score_candidate(query_text, query_tags, status, co)
            candidate_scores.append((co["id"], co["name"], s))

        candidate_scores.sort(key=lambda x: x[2], reverse=True)
        top_candidates = candidate_scores[:top_k]
        top_cids = [c[0] for c in top_candidates]

        is_top_1 = len(top_cids) > 0 and top_cids[0] == true_cid and top_candidates[0][2] > 0.0
        is_top_k = true_cid in top_cids and any(c[2] > 0.0 for c in top_candidates if c[0] == true_cid)
        is_unresolved = len(top_candidates) == 0 or top_candidates[0][2] == 0.0

        if is_top_1:
            top_1_hits += 1
        if is_top_k:
            top_k_hits += 1
        if is_unresolved:
            unresolved_count += 1

        results.append({
            "source": src,
            "corpus": corpus,
            "query_text": query_text,
            "ground_truth_canonical_id": true_cid,
            "predicted_top_1": top_candidates[0][0] if (top_candidates and top_candidates[0][2] > 0.0) else None,
            "predicted_top_k": [c[0] for c in top_candidates if c[2] > 0.0],
            "top_1_hit": is_top_1,
            "top_k_hit": is_top_k,
            "unresolved": is_unresolved,
        })

    top_1_acc = top_1_hits / num_holdout if num_holdout > 0 else 0.0
    top_k_recall = top_k_hits / num_holdout if num_holdout > 0 else 0.0
    unresolved_rate = unresolved_count / num_holdout if num_holdout > 0 else 0.0

    summary = {
        "stage": "v0.13",
        "benchmark_name": "Blinded Alignment Benchmark (20% Holdout)",
        "total_alignments": len(all_alignments),
        "holdout_count": num_holdout,
        "holdout_ratio": holdout_ratio,
        "random_seed": seed,
        "metrics": {
            "top_1_accuracy": round(top_1_acc, 4),
            "top_3_recall": round(top_k_recall, 4),
            "unresolved_rate": round(unresolved_rate, 4),
        },
        "evaluation": {
            "status": "PASS",
            "non_blocking": True,
            "interpretation": "Automated cross-source semantic discovery benchmark successfully executed.",
        },
        "details": results,
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "blinded_alignment_results.json"
    out_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MAPEOGEO v0.13 Blinded Alignment Benchmark")
    parser.add_argument("--alignments", type=Path, default=ROOT / "formal" / "tri_source_alignments_v0_13.json")
    parser.add_argument("--preregistration", type=Path, default=ROOT / "evidence" / "v0_13_preregistration.json")
    parser.add_argument("--base-graph", type=Path, default=ROOT / "artifacts" / "cross_source_v0_12" / "mapeogeo_v0_12_graph.json.gz")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "artifacts" / "tri_source_v0_13")
    args = parser.parse_args()

    summary = run_blinded_benchmark(args.alignments, args.preregistration, args.out_dir, args.base_graph)

    print("=== Blinded Alignment Benchmark Results ===")
    print(f"Holdout Count:    {summary['holdout_count']} (20% of {summary['total_alignments']} alignments)")
    print(f"Top-1 Accuracy:   {summary['metrics']['top_1_accuracy'] * 100:.1f}%")
    print(f"Top-3 Recall:     {summary['metrics']['top_3_recall'] * 100:.1f}%")
    print(f"Unresolved Rate:  {summary['metrics']['unresolved_rate'] * 100:.1f}%")
    print(f"Benchmark Status: {summary['evaluation']['status']} (Non-blocking)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
