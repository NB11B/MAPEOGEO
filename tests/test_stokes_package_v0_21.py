from __future__ import annotations

import json
from pathlib import Path
import jsonschema

from mapeogeo.pct.attachments.stokes_simplex import (
    Simplex,
    SimplicialComplex,
    boundary_operator,
    discrete_exterior_derivative,
    verify_stokes_duality,
    verify_nilpotency,
    verify_incidence_transpose,
)
from scripts.stokes_package_v0_21 import generate_stokes_package

ROOT = Path(__file__).resolve().parents[1]


def test_simplicial_stokes_mathematical_properties():
    # Construct standard 2-simplex and 3-simplex complexes
    K2 = SimplicialComplex.standard_simplex(2)
    K3 = SimplicialComplex.standard_simplex(3)

    # 1. Orientation reversal
    s_01 = Simplex((0, 1))
    s_10 = Simplex((1, 0))
    assert s_01.sign_relative_to(s_10) == -1

    # 2. Boundary operator nilpotency: \partial^2 = 0
    assert verify_nilpotency(K2, operator_type="boundary") is True
    assert verify_nilpotency(K3, operator_type="boundary") is True

    # 3. Exterior derivative nilpotency: d^2 = 0
    assert verify_nilpotency(K2, operator_type="coboundary") is True
    assert verify_nilpotency(K3, operator_type="coboundary") is True

    # 4. Discrete Stokes pairing: <d alpha, sigma> = <alpha, \partial sigma>
    assert verify_stokes_duality(K2) is True
    assert verify_stokes_duality(K3) is True

    # 5. Incidence transpose: B = D^T
    assert verify_incidence_transpose(K2) is True
    assert verify_incidence_transpose(K3) is True


def test_stokes_package_joints_and_certificate_generation():
    joints_file = ROOT / "formal" / "joints_stokes_v0_21.json"
    certs_file = ROOT / "formal" / "correspondence_certificates_v0_21.json"

    res = generate_stokes_package(
        joints_out=joints_file,
        certs_out=certs_file,
    )
    assert res.all_checks_passed is True

    # Validate joints against schema
    joint_schema = json.loads((ROOT / "schema" / "mapeogeo-joint.schema.json").read_text(encoding="utf-8"))
    joints_data = json.loads(joints_file.read_text(encoding="utf-8"))
    jsonschema.validate(instance=joints_data, schema=joint_schema)

    # Assert no SAME_SEMANTICS
    assert "SAME_SEMANTICS" not in json.dumps(joints_data)

    # Validate certificates against schema
    cert_schema = json.loads((ROOT / "schema" / "mapeogeo-certificate.schema.json").read_text(encoding="utf-8"))
    certs_data = json.loads(certs_file.read_text(encoding="utf-8"))
    jsonschema.validate(instance=certs_data, schema=cert_schema)

    # Find the Stokes certificate
    stokes_cert = next((c for c in certs_data["certificates"] if "stokes" in c["certificate_id"]), None)
    assert stokes_cert is not None
    assert stokes_cert["verification_status"] == "CERTIFIED"
    assert stokes_cert["quorum_count"] >= 2
    assert stokes_cert["relationship"] == "SCOPED_OVERLAP"
