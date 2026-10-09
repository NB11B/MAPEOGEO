#!/usr/bin/env python3
"""Verification harness for canonical clock identity codec against frozen reference model.

Verifies:
1. 256 ordered identifier pairs roundtrip and maintain bijectivity.
2. Invalid inputs (surrogates, empty, non-strings) fail closed.
3. Non-canonical representations fail closed on decode.
4. Reference workflow check 1: boundary-overlap counterexample remains two distinct streams (relation 'unknown').
5. Reference workflow check 2: explicit causal parent connects streams (relation 'before').
6. Reference workflow check 3: same stream sequential ordering (relation 'before').
7. Reference workflow check 4: same participant in independent domains at seq 1 remains 'unknown'.
8. Preserves original counterexample (old concatenation collision yielding 'before').
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

# Ensure experiments module can be imported
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR
if not (REPO_ROOT / "experiments").exists():
    REPO_ROOT = SCRIPT_DIR.parents[2]  # If run from experiments/intelligence_integration/v0_1

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.intelligence_integration.v0_1.clock_identity import (
    CLOCK_IDENTITY_PREFIX,
    decode_clock_identity,
    encode_clock_identity,
)


def run_checks(reference_dir: Path) -> dict:
    if str(reference_dir) not in sys.path:
        sys.path.insert(0, str(reference_dir))

    from intel_uow.workflow import event_relation

    results = {
        "status": "PASS",
        "codec_checks": {},
        "reference_workflow_checks": {},
        "preserved_counterexample": {},
    }

    # 1. 256 ordered pairs
    sample_components = [
        "ops",
        "ops:",
        ":analyst",
        "analyst",
        "worker::01",
        "domain with spaces",
        'quotes"and\\slashes',
        "colon:and::double",
        "unicode:éàü",
        "combining:e\u0301",
        "astral:😀",
        "astral:🦀",
        "math:∑∫dx",
        "tabs\tand\nnewlines",
        "boundary.node-42",
        "root/sub/path",
    ]
    assert len(sample_components) == 16, "Need 16 elements for 16x16 = 256 pairs"

    seen_encodings = {}
    pair_count = 0
    for d in sample_components:
        for a in sample_components:
            pair_count += 1
            enc = encode_clock_identity(d, a)
            dec_d, dec_a = decode_clock_identity(enc)
            if (dec_d, dec_a) != (d, a):
                raise AssertionError(f"Roundtrip failed for ({d!r}, {a!r}): got ({dec_d!r}, {dec_a!r})")
            if enc in seen_encodings and seen_encodings[enc] != (d, a):
                raise AssertionError(f"Collision between {seen_encodings[enc]} and {(d, a)}: {enc}")
            seen_encodings[enc] = (d, a)

    results["codec_checks"]["test_256_ordered_pairs"] = {
        "pairs_tested": pair_count,
        "unique_encodings": len(seen_encodings),
        "status": "PASS",
    }

    # 2. Invalid inputs
    invalid_inputs = [
        ("", "analyst", ValueError),
        ("ops", "", ValueError),
        (123, "analyst", TypeError),
        ("ops", None, TypeError),
        ("surrogate\uD800", "analyst", ValueError),
        ("ops", "surrogate\uDFFF", ValueError),
    ]
    invalid_passed = 0
    for d, a, exc_type in invalid_inputs:
        try:
            encode_clock_identity(d, a)  # type: ignore
        except exc_type:
            invalid_passed += 1
        else:
            raise AssertionError(f"Expected {exc_type.__name__} for ({d!r}, {a!r})")

    results["codec_checks"]["test_invalid_inputs_rejected"] = {
        "cases_tested": len(invalid_inputs),
        "rejected_correctly": invalid_passed,
        "status": "PASS",
    }

    # 3. Noncanonical decode inputs
    noncanonical_inputs = [
        'uow-clock:v0:["ops","analyst"]',  # bad prefix
        'uow-clock:v1:not-json',  # non-json
        'uow-clock:v1:["ops"]',  # len != 2
        'uow-clock:v1:["ops","analyst","extra"]',  # len != 2
        'uow-clock:v1:["ops", "analyst"]',  # non-canonical whitespace
        'uow-clock:v1:{"domain":"ops"}',  # dict instead of list
        'uow-clock:v1:[1,2]',  # non-string elements
        'uow-clock:v1:["ops",""]',  # empty string
    ]
    noncanon_passed = 0
    for payload in noncanonical_inputs:
        try:
            decode_clock_identity(payload)
        except (ValueError, TypeError):
            noncanon_passed += 1
        else:
            raise AssertionError(f"Expected decode rejection for: {payload!r}")

    results["codec_checks"]["test_noncanonical_decode_rejected"] = {
        "cases_tested": len(noncanonical_inputs),
        "rejected_correctly": noncanon_passed,
        "status": "PASS",
    }

    # 4. Preserved legacy counterexample
    d1, a1 = "ops:", "analyst"
    d2, a2 = "ops", ":analyst"
    legacy_actor1 = d1 + "::" + a1
    legacy_actor2 = d2 + "::" + a2
    legacy_events = {
        "e1": {"id": "e1", "actor": legacy_actor1, "seq": 1, "parents": []},
        "e2": {"id": "e2", "actor": legacy_actor2, "seq": 2, "parents": []},
    }
    legacy_relation = event_relation("e1", "e2", legacy_events)
    results["preserved_counterexample"] = {
        "d1": d1,
        "a1": a1,
        "d2": d2,
        "a2": a2,
        "legacy_actor1": legacy_actor1,
        "legacy_actor2": legacy_actor2,
        "collided": legacy_actor1 == legacy_actor2,
        "observed_relation": legacy_relation,
        "explanation": "Legacy concatenation '::' caused boundary overlap collision, manufacturing artificial 'before' relation.",
    }
    assert legacy_actor1 == legacy_actor2 == "ops:::analyst"
    assert legacy_relation == "before"

    # 5. Canonical Workflow Checks
    enc1 = encode_clock_identity(d1, a1)
    enc2 = encode_clock_identity(d2, a2)
    assert enc1 != enc2, f"Expected distinct encodings, got {enc1}"

    # Check 1: Boundary overlap example remains distinct streams -> unknown
    evts_distinct = {
        "e1": {"id": "e1", "actor": enc1, "seq": 1, "parents": []},
        "e2": {"id": "e2", "actor": enc2, "seq": 2, "parents": []},
    }
    rel1 = event_relation("e1", "e2", evts_distinct)
    assert rel1 == "unknown", f"Expected unknown, got {rel1}"
    results["reference_workflow_checks"]["boundary_overlap_distinct_streams"] = {
        "enc1": enc1,
        "enc2": enc2,
        "observed_relation": rel1,
        "status": "PASS",
    }

    # Check 2: Explicit causal parent connects the two streams -> before
    evts_parent = {
        "e1": {"id": "e1", "actor": enc1, "seq": 1, "parents": []},
        "e2": {"id": "e2", "actor": enc2, "seq": 2, "parents": ["e1"]},
    }
    rel2 = event_relation("e1", "e2", evts_parent)
    assert rel2 == "before", f"Expected before, got {rel2}"
    results["reference_workflow_checks"]["explicit_causal_parent_orders_streams"] = {
        "observed_relation": rel2,
        "status": "PASS",
    }

    # Check 3: Two events belong to same stream with seq 1 and 2 -> before
    evts_same = {
        "e1": {"id": "e1", "actor": enc1, "seq": 1, "parents": []},
        "e2": {"id": "e2", "actor": enc1, "seq": 2, "parents": []},
    }
    rel3 = event_relation("e1", "e2", evts_same)
    assert rel3 == "before", f"Expected before, got {rel3}"
    results["reference_workflow_checks"]["same_stream_sequential_ordering"] = {
        "observed_relation": rel3,
        "status": "PASS",
    }

    # Check 4: Same participant in independent domains, both at seq 1 -> unknown
    enc_domA = encode_clock_identity("uow:01", "alice")
    enc_domB = encode_clock_identity("uow:02", "alice")
    evts_independent = {
        "e1": {"id": "e1", "actor": enc_domA, "seq": 1, "parents": []},
        "e2": {"id": "e2", "actor": enc_domB, "seq": 1, "parents": []},
    }
    rel4 = event_relation("e1", "e2", evts_independent)
    assert rel4 == "unknown", f"Expected unknown, got {rel4}"
    results["reference_workflow_checks"]["independent_domains_same_participant_seq1"] = {
        "observed_relation": rel4,
        "status": "PASS",
    }

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify clock identity codec against frozen reference model")
    parser.add_argument("--reference-dir", type=Path, required=True, help="Path to reference package directory")
    parser.add_argument("--output", type=Path, default=Path("local_clock_identity_results.json"), help="Output path")
    args = parser.parse_args()

    results = run_checks(args.reference_dir)
    args.output.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps({
        "status": results["status"],
        "codec_checks_passed": len(results["codec_checks"]),
        "reference_workflow_checks_passed": len(results["reference_workflow_checks"]),
        "preserved_counterexample": results["preserved_counterexample"]["observed_relation"],
        "output_file": str(args.output.resolve()),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
