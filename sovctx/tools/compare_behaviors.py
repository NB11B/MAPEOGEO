from __future__ import annotations

import argparse
import json
from itertools import combinations

from build_behavior_signatures import build_signatures


FEATURE_FIELDS = ("operator_ids", "behavioral_test_types")


def feature_set(signature: dict[str, object]) -> set[str]:
    out: set[str] = set()
    for field in FEATURE_FIELDS:
        for value in signature.get(field, []):
            out.add(f"{field}:{value}")
    return out


def jaccard(a: set[str], b: set[str]) -> float:
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare SOVCTX equations by behavioral signature.")
    parser.add_argument("--min-score", type=float, default=0.25)
    parser.add_argument("--equation")
    args = parser.parse_args()

    signatures = build_signatures()
    if args.equation:
        target = next((s for s in signatures if s["equation_id"] == args.equation), None)
        if target is None:
            raise SystemExit(f"unknown equation: {args.equation}")
        pairs = [(target, other) for other in signatures if other["equation_id"] != target["equation_id"]]
    else:
        pairs = list(combinations(signatures, 2))

    results = []
    for left, right in pairs:
        lf, rf = feature_set(left), feature_set(right)
        score = jaccard(lf, rf)
        if score < args.min_score:
            continue
        results.append({
            "left": left["equation_id"],
            "right": right["equation_id"],
            "score": score,
            "shared_features": sorted(lf & rf),
            "interpretation": "candidate_structural_analogy_only",
        })

    results.sort(key=lambda x: (-x["score"], x["left"], x["right"]))
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
