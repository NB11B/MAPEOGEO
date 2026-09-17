from __future__ import annotations

import json
from pathlib import Path
import jsonschema

from scripts.perelman_joints_v0_21 import generate_perelman_candidate_joints

ROOT = Path(__file__).resolve().parents[1]


def test_perelman_candidate_joints_structure_and_schema():
    out_file = ROOT / "formal" / "joints_perelman_v0_21.json"
    res = generate_perelman_candidate_joints(out_file)
    assert res.all_checks_passed is True
    assert res.joints_count == 6

    # Validate against schema
    schema = json.loads((ROOT / "schema" / "mapeogeo-joint.schema.json").read_text(encoding="utf-8"))
    data = json.loads(out_file.read_text(encoding="utf-8"))
    jsonschema.validate(instance=data, schema=schema)

    # 1. All 6 joints must have status CANDIDATE (none certified or active without proof)
    for j in data["joints"]:
        assert j["status"] == "CANDIDATE"

    # 2. Verify all 6 expected mechanisms
    types = {j["joint_type"] for j in data["joints"]}
    assert "METRIC_CONTRACTION" in types
    assert "GRADIENT_FLOW" in types
    assert "MONOTONICITY_FORMULA" in types
    assert "ASYMPTOTIC_BLOWUP" in types
    assert "TOPOLOGICAL_SURGERY" in types

    # 3. Check anti-identity: zero SAME_SEMANTICS
    assert "SAME_SEMANTICS" not in json.dumps(data)
    assert "EQUIVALENT_TO" not in json.dumps(data)
    assert "IDENTICAL_TO" not in json.dumps(data)


def test_perelman_joint_roles_and_relationships():
    out_file = ROOT / "formal" / "joints_perelman_v0_21.json"
    data = json.loads(out_file.read_text(encoding="utf-8"))

    by_id = {j["joint_id"]: j for j in data["joints"]}

    # Joint 1: Riemann -> Ricci
    j1 = by_id["joint:perelman:riemann_to_ricci_contraction"]
    assert j1["relationship"] == "CONTRACTION_OF"
    roles1 = {foot["role"] for foot in j1["feet"]}
    assert "ambient_tensor" in roles1
    assert "contracted_tensor" in roles1

    # Joint 2: Ricci flow -> Metric
    j2 = by_id["joint:perelman:ricci_flow_action_on_metric"]
    assert j2["relationship"] == "ACTS_ON"
    roles2 = {foot["role"] for foot in j2["feet"]}
    assert "flow_equation" in roles2
    assert "evolving_field" in roles2

    # Joint 3: W-entropy -> Ricci flow
    j3 = by_id["joint:perelman:w_entropy_monotonicity"]
    assert j3["relationship"] == "MONOTONE_ALONG"
    roles3 = {foot["role"] for foot in j3["feet"]}
    assert "functional_quantity" in roles3
    assert "flow_trajectory" in roles3

    # Joint 4: Neck singularity -> Shrinking cylinder
    j4 = by_id["joint:perelman:neck_singularity_asymptotic_blowup"]
    assert j4["relationship"] == "BLOWS_UP_AS"
    roles4 = {foot["role"] for foot in j4["feet"]}
    assert "blowup_limit" in roles4
    assert "singularity_model" in roles4

    # Joint 5: Surgery -> Neck region
    j5 = by_id["joint:perelman:topological_surgery_on_neck"]
    assert j5["relationship"] == "SURGERY_OF"
    roles5 = {foot["role"] for foot in j5["feet"]}
    assert "surgery_operation" in roles5
    assert "target_neck" in roles5

    # Joint 6: Reduced volume -> Backward Ricci flow
    j6 = by_id["joint:perelman:reduced_volume_monotonicity"]
    assert j6["relationship"] == "MONOTONE_ALONG"
    roles6 = {foot["role"] for foot in j6["feet"]}
    assert "functional_quantity" in roles6
    assert "flow_trajectory" in roles6
