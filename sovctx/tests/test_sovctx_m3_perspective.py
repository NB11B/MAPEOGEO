#!/usr/bin/env python3
"""
Unit tests for Milestone SOVCTX-M3: Epistemic Perspective Transfer.
Verifies the four-realm separation, 3-arm comparative evaluation, and K_C > K_B > K_A.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from sovctx.node.perspective_transfer import (
    PerspectiveTransferEngine,
    TransferArm,
    InsightType,
)
from sovctx.tools.graph_io import load_records, split_records

ROOT = Path(__file__).resolve().parents[1]


def test_four_realm_separation_and_non_implication() -> None:
    """Verifies that G = G_H U G_M U G_P U G_E and strict non-implication boundaries hold."""
    records = load_records()
    nodes, edges = split_records(records)
    node_map = {n["id"]: n for n in nodes}

    # Verify realms on edges
    realms = {e.get("relation_realm") for e in edges}
    assert realms == {
        "HISTORICAL",
        "MATHEMATICAL",
        "METHODOLOGICAL_PERSPECTIVE",
        "EXPERIMENTAL_APPLICATION",
    }

    # Verify non-implication boundaries: G_H !=> G_P and G_P !=> G_H
    historical_types = {"PERSON", "PUBLICATION", "ARCHIVAL_DOCUMENT", "CLAIM"}
    for e in edges:
        realm = e.get("relation_realm")
        src = node_map.get(e["source"])
        tgt = node_map.get(e["target"])
        assert src is not None and tgt is not None

        if realm == "METHODOLOGICAL_PERSPECTIVE":
            # Neither source nor target can be pure historical citation/person entity
            assert src.get("type") not in historical_types or src.get("type") == "METHOD_EPISODE"
            assert tgt.get("type") not in historical_types or tgt.get("type") == "METHOD_EPISODE"
        elif realm == "EXPERIMENTAL_APPLICATION":
            # Pure experimental application edges cannot connect to historical entities or method episodes
            assert src.get("type") not in historical_types and src.get("type") != "METHOD_EPISODE"
            assert tgt.get("type") not in historical_types and tgt.get("type") != "METHOD_EPISODE"


def test_problem_nodes_cultural_neutrality() -> None:
    """Verifies all 10 problem nodes have zero cultural, national, or provenance tags."""
    pfile = ROOT / "graph" / "problems.jsonl"
    lines = pfile.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 10

    cultural_words = ["soviet", "russian", "leningrad", "moscow", "steklov", "ussr", "western", "american"]
    for l in lines:
        if not l.strip():
            continue
        p = json.loads(l)
        assert p["type"] == "PROBLEM"
        serialized = json.dumps(p).lower()
        for kw in cultural_words:
            assert kw not in serialized, f"Problem {p['id']} contains cultural tag '{kw}'"


def test_method_lenses_and_16d_primitives() -> None:
    """Verifies all 7 method lenses declare valid structural primitives and negative information linkages."""
    lfile = ROOT / "graph" / "method_lenses.jsonl"
    lines = lfile.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 7

    allowed_primitives = {
        "ADMISSIBILITY_CONSTRAINING",
        "AUXILIARY_CONSTRUCTION",
        "CONTROL_INTERVENTION",
        "EXTREMAL_REASONING",
        "GLOBAL_REASONING",
        "INDIRECT_INFERENCE",
        "INVARIANT_REASONING",
        "INVERSE_REASONING",
        "LOCAL_REASONING",
        "NEGATIVE_INFORMATION",
        "REPRESENTATION_SHIFT",
        "SELF_CONSISTENT_CLOSURE",
        "STATE_AUGMENTATION",
        "STATE_REDUCTION",
    }

    for l in lines:
        if not l.strip():
            continue
        lens = json.loads(l)
        assert lens["type"] == "METHOD_LENS"
        assert len(lens["method_primitives"]) >= 4
        for prim in lens["method_primitives"]:
            assert prim in allowed_primitives
        assert len(lens["avoided_operations"]) >= 1
        assert len(lens["enables_omission_of_ids"]) >= 1
        assert lens["derived_from_episode_id"].startswith("EP:")


def test_negative_information_nodes() -> None:
    """Verifies the 7 explicit graph-addressable negative information nodes."""
    nfile = ROOT / "graph" / "negative_information.jsonl"
    lines = nfile.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 7

    for l in lines:
        if not l.strip():
            continue
        neg = json.loads(l)
        assert neg["type"] == "NEGATIVE_INFORMATION"
        assert neg["id"].startswith("NEG:")
        assert len(neg["description"]) > 10
        assert len(neg["bypassed_by"]) > 5


def test_perspective_projections_and_insights() -> None:
    """Verifies all 10 perspective projections map to valid problems, lenses, and insights."""
    pr_file = ROOT / "graph" / "perspective_projections.jsonl"
    ins_file = ROOT / "graph" / "insights.jsonl"

    projs = [json.loads(l) for l in pr_file.read_text(encoding="utf-8").splitlines() if l.strip()]
    insights = [json.loads(l) for l in ins_file.read_text(encoding="utf-8").splitlines() if l.strip()]

    assert len(projs) == 10
    assert len(insights) == 20

    ins_map = {i["id"]: i for i in insights}
    for pr in projs:
        assert pr["problem_id"].startswith("PROBLEM:")
        assert pr["method_lens_id"].startswith("LENS:")
        assert len(pr["resulting_insight_ids"]) == 2
        for iid in pr["resulting_insight_ids"]:
            assert iid in ins_map
            assert ins_map[iid]["target_problem_id"] == pr["problem_id"]
            assert ins_map[iid]["generated_by_projection_id"] == pr["id"]


def test_perspective_transfer_engine_study_execution() -> None:
    """Tests full execution of the 3-arm comparative perspective transfer study."""
    engine = PerspectiveTransferEngine()
    result = engine.run_study()

    assert result.total_problems == 10
    assert result.total_lenses == 7
    assert len(result.evaluations) == 10

    # Arm A, B, C hierarchy
    assert result.mean_k_arm_a == 0.0
    assert result.mean_k_arm_b > 5.0
    assert result.mean_k_arm_c > result.mean_k_arm_b + 4.0

    # 100% confirmation of K_C > K_A and K_C > K_B
    assert result.k_c_greater_than_k_a_ratio == 1.0
    assert result.k_c_greater_than_k_b_ratio == 1.0

    # Zero false insight rate
    assert result.overall_false_insight_rate == 0.0

    # Speedups
    assert result.mean_speedup_arm_b > 100.0
    assert result.mean_speedup_arm_c > result.mean_speedup_arm_b

    # Verify per-problem monotonic progression
    for pid, arms in result.evaluations.items():
        k_a = arms["ARM_A"].epistemic_knowledge_score
        k_b = arms["ARM_B"].epistemic_knowledge_score
        k_c = arms["ARM_C"].epistemic_knowledge_score
        assert k_c > k_b > k_a
        assert arms["ARM_A"].arm == TransferArm.ARM_A_CONVENTIONAL
        assert arms["ARM_B"].arm == TransferArm.ARM_B_SINGLE_LENS
        assert arms["ARM_C"].arm == TransferArm.ARM_C_MULTI_PERSPECTIVE


def test_complementarity_matrix_synergy() -> None:
    """Verifies that the canonical method lenses exhibit structural complementarity."""
    engine = PerspectiveTransferEngine()
    pairs = engine.compute_complementarity_matrix()

    assert len(pairs) >= 6
    for pair in pairs:
        assert pair.lens_a.startswith("LENS:")
        assert pair.lens_b.startswith("LENS:")
        assert pair.synergy_score >= 0.85
        assert pair.relationship in {"COMPLEMENTS", "ENABLES", "REVEALS"}
        assert len(pair.composite_primitives) >= 2
