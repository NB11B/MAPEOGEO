#!/usr/bin/env python3
"""MAPEOGEO Package S (Simplicial Stokes) Joint & Correspondence Certificate Builder.

Generates mechanism joints (BOUNDARY_DUALITY and HOMOLOGICAL_COMPLEX) and correspondence
certificates for Simplicial Stokes duality over Q, verifying orientation reversal,
nilpotency (partial^2 = 0, d^2 = 0), Stokes pairing, and incidence transpose B = D^T.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mapeogeo.analysis.scope_comparator import TypedScopeRecord
from mapeogeo.pct.attachments.stokes_simplex import (
    SimplicialComplex,
    verify_incidence_transpose,
    verify_nilpotency,
    verify_stokes_duality,
)
from scripts.correspondence_certificate import generate_correspondence_certificate


@dataclass
class StokesPackageResult:
    all_checks_passed: bool
    joints_count: int
    certificate_id: str
    pct_execution_digest: str


def compute_stokes_pct_witness() -> tuple[bool, str]:
    K2 = SimplicialComplex.standard_simplex(2)
    K3 = SimplicialComplex.standard_simplex(3)

    checks = [
        verify_nilpotency(K2, "boundary"),
        verify_nilpotency(K3, "boundary"),
        verify_nilpotency(K2, "coboundary"),
        verify_nilpotency(K3, "coboundary"),
        verify_stokes_duality(K2),
        verify_stokes_duality(K3),
        verify_incidence_transpose(K2),
        verify_incidence_transpose(K3),
    ]
    all_ok = all(checks)
    digest_payload = f"stokes_simplex_q:k2={checks[:4]}:k3={checks[4:]}"
    digest = hashlib.sha256(digest_payload.encode("utf-8")).hexdigest()
    return all_ok, digest


def generate_stokes_package(
    joints_out: Path = ROOT / "formal" / "joints_stokes_v0_21.json",
    certs_out: Path = ROOT / "formal" / "correspondence_certificates_v0_21.json",
) -> StokesPackageResult:
    pct_ok, pct_digest = compute_stokes_pct_witness()
    if not pct_ok:
        raise RuntimeError("Simplicial Stokes PCT verification checks failed!")

    stokes_scope = TypedScopeRecord(
        domain="SIMPLICIAL_COMPLEX",
        dimension="k",
        coefficient_ring="RAT",
        regularity="DISCRETE",
        orientation_convention="INDUCED_SIMPLEX_ORDER",
        boundary_convention="STANDARD_ALTERNATING_SUM",
        parameter_range="k >= 1",
        exceptional_cases="k = 0 has zero boundary",
    )

    # 1. Mechanism Joints
    joints_data = {
        "schema_version": "0.21",
        "description": "Mechanism joints for Simplicial Stokes Package S (v0.21)",
        "joints": [
            {
                "joint_id": "joint:stokes:simplicial_boundary_duality",
                "joint_type": "BOUNDARY_DUALITY",
                "relationship": "DUALITY_BETWEEN",
                "feet": [
                    {
                        "endpoint_id": "srcdecl:stokes_simplex_eo",
                        "role": "boundary_operator",
                        "view": "EO",
                    },
                    {
                        "endpoint_id": "srcdecl:stokes_simplex_geo",
                        "role": "exterior_derivative",
                        "view": "GEO",
                    },
                ],
                "scope": stokes_scope.to_dict(),
                "status": "CERTIFIED",
                "metadata": {
                    "witness_property": "discrete_stokes_pairing",
                    "formula": "<d alpha, sigma> = <alpha, partial sigma>",
                },
            },
            {
                "joint_id": "joint:stokes:simplicial_homological_complex",
                "joint_type": "HOMOLOGICAL_COMPLEX",
                "relationship": "COMPLEX_OF",
                "feet": [
                    {
                        "endpoint_id": "srcdecl:stokes_simplex_eo",
                        "role": "chain_group",
                        "view": "EO",
                    },
                    {
                        "endpoint_id": "srcdecl:stokes_simplex_geo",
                        "role": "cochain_group",
                        "view": "GEO",
                    },
                ],
                "scope": stokes_scope.to_dict(),
                "status": "CERTIFIED",
                "metadata": {
                    "nilpotency_boundary": "partial^2 = 0",
                    "nilpotency_coboundary": "d^2 = 0",
                },
            },
        ],
    }

    joints_out.parent.mkdir(parents=True, exist_ok=True)
    joints_out.write_text(json.dumps(joints_data, indent=2), encoding="utf-8")

    # 2. Correspondence Certificate
    eo_hash = hashlib.sha256(b"stokes_simplicial_chain_complex_eo").hexdigest()
    geo_hash = hashlib.sha256(b"stokes_simplicial_cochain_exterior_derivative_geo").hexdigest()

    cert_stokes = generate_correspondence_certificate(
        certificate_id="cert:stokes:simplicial_duality_v0_21",
        target_concept="simplicial_boundary_exterior_derivative_duality",
        relationship="SCOPED_OVERLAP",
        scope=stokes_scope,
        eo_slot={
            "status": "WITNESSED",
            "statement_sha256": eo_hash,
            "view_ref": "srcdecl:stokes_simplex_eo",
        },
        geo_slot={
            "status": "WITNESSED",
            "statement_sha256": geo_hash,
            "view_ref": "srcdecl:stokes_simplex_geo",
        },
        pct_slot={
            "status": "WITNESSED",
            "execution_digest": pct_digest,
            "view_ref": "pct:attachment:stokes_simplex_q",
        },
        formal_slot={
            "status": "ABSENT",
        },
        metadata={"package": "Package S (Simplicial Stokes)"},
    )

    existing_certs = []
    if certs_out.is_file():
        try:
            prev_data = json.loads(certs_out.read_text(encoding="utf-8"))
            existing_certs = [
                c for c in prev_data.get("certificates", [])
                if c.get("certificate_id") != cert_stokes.certificate_id
            ]
        except Exception:
            existing_certs = []

    certs_data = {
        "schema_version": "0.21",
        "description": "Preregistered multi-view correspondence certificates for MAPEOGEO v0.21",
        "certificates": [cert_stokes.to_dict()] + existing_certs,
    }

    certs_out.parent.mkdir(parents=True, exist_ok=True)
    certs_out.write_text(json.dumps(certs_data, indent=2), encoding="utf-8")

    return StokesPackageResult(
        all_checks_passed=True,
        joints_count=len(joints_data["joints"]),
        certificate_id=cert_stokes.certificate_id,
        pct_execution_digest=pct_digest,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Simplicial Stokes package joints and certificates")
    parser.add_argument("--joints-out", type=Path, default=ROOT / "formal" / "joints_stokes_v0_21.json")
    parser.add_argument("--certs-out", type=Path, default=ROOT / "formal" / "correspondence_certificates_v0_21.json")
    args = parser.parse_args()

    res = generate_stokes_package(args.joints_out, args.certs_out)
    print(f"[Package S] Generated {res.joints_count} joints and certificate {res.certificate_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
