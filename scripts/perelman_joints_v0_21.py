#!/usr/bin/env python3
"""MAPEOGEO Package P (Perelman Mechanisms) Candidate Joint Builder (v0.21).

Constructs the 6 preregistered candidate mechanism joints for Perelman's geometrization
mechanisms for grammar and anti-identity testing.
Strictly candidate-only: produces 0 identity edges and 0 Hamilton/Perelman PDF ingestion.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mapeogeo.analysis.scope_comparator import TypedScopeRecord


@dataclass
class PerelmanJointsResult:
    all_checks_passed: bool
    joints_count: int
    out_file: Path


def generate_perelman_candidate_joints(
    out_file: Path = ROOT / "formal" / "joints_perelman_v0_21.json",
) -> PerelmanJointsResult:
    scope_3d = TypedScopeRecord(
        domain="SMOOTH_MANIFOLD",
        dimension="3",
        coefficient_ring="REAL",
        regularity="C_INFINITY",
        orientation_convention="ORIENTED_RIEMANNIAN_METRIC",
        boundary_convention="CLOSED_WITHOUT_BOUNDARY",
        parameter_range="t in [0, T_sing)",
        exceptional_cases="finite_time_neck_singularities",
    )

    joints = [
        {
            "joint_id": "joint:perelman:riemann_to_ricci_contraction",
            "joint_type": "METRIC_CONTRACTION",
            "relationship": "CONTRACTION_OF",
            "feet": [
                {
                    "endpoint_id": "srcdecl:riemann_curvature_tensor",
                    "role": "ambient_tensor",
                    "view": "EO",
                },
                {
                    "endpoint_id": "srcdecl:ricci_curvature_tensor",
                    "role": "contracted_tensor",
                    "view": "GEO",
                },
            ],
            "scope": scope_3d.to_dict(),
            "status": "CANDIDATE",
            "metadata": {
                "operation": "Ric_ij = g^{kl} R_kijl",
                "notes": "Metric contraction mapping rank-4 curvature to rank-2 Ricci tensor",
            },
        },
        {
            "joint_id": "joint:perelman:ricci_flow_action_on_metric",
            "joint_type": "GRADIENT_FLOW",
            "relationship": "ACTS_ON",
            "feet": [
                {
                    "endpoint_id": "srcdecl:ricci_flow_pde",
                    "role": "flow_equation",
                    "view": "EO",
                },
                {
                    "endpoint_id": "srcdecl:riemannian_metric_tensor",
                    "role": "evolving_field",
                    "view": "GEO",
                },
            ],
            "scope": scope_3d.to_dict(),
            "status": "CANDIDATE",
            "metadata": {
                "equation": "partial_t g_ij = -2 Ric_ij",
                "notes": "Parabolic geometric flow deforming metric tensor over time",
            },
        },
        {
            "joint_id": "joint:perelman:w_entropy_monotonicity",
            "joint_type": "MONOTONICITY_FORMULA",
            "relationship": "MONOTONE_ALONG",
            "feet": [
                {
                    "endpoint_id": "srcdecl:perelman_w_entropy",
                    "role": "functional_quantity",
                    "view": "EO",
                },
                {
                    "endpoint_id": "srcdecl:ricci_flow_pde",
                    "role": "flow_trajectory",
                    "view": "GEO",
                },
            ],
            "scope": scope_3d.to_dict(),
            "status": "CANDIDATE",
            "metadata": {
                "formula": "d/dt W(g(t), f(t), tau(t)) >= 0",
                "notes": "Entropy functional monotonically non-decreasing along conjugate heat/Ricci flow",
            },
        },
        {
            "joint_id": "joint:perelman:neck_singularity_asymptotic_blowup",
            "joint_type": "ASYMPTOTIC_BLOWUP",
            "relationship": "BLOWS_UP_AS",
            "feet": [
                {
                    "endpoint_id": "srcdecl:neck_singularity_region",
                    "role": "blowup_limit",
                    "view": "GEO",
                },
                {
                    "endpoint_id": "srcdecl:shrinking_cylinder_soliton",
                    "role": "singularity_model",
                    "view": "EO",
                },
            ],
            "scope": scope_3d.to_dict(),
            "status": "CANDIDATE",
            "metadata": {
                "limit_model": "S^2 x R round shrinking cylinder",
                "notes": "Parabolic rescaling of developing neck singularities",
            },
        },
        {
            "joint_id": "joint:perelman:topological_surgery_on_neck",
            "joint_type": "TOPOLOGICAL_SURGERY",
            "relationship": "SURGERY_OF",
            "feet": [
                {
                    "endpoint_id": "srcdecl:perelman_surgery_procedure",
                    "role": "surgery_operation",
                    "view": "EO",
                },
                {
                    "endpoint_id": "srcdecl:neck_singularity_region",
                    "role": "target_neck",
                    "view": "GEO",
                },
            ],
            "scope": scope_3d.to_dict(),
            "status": "CANDIDATE",
            "metadata": {
                "procedure": "Cut along standard S2 x (-delta, delta) neck and glue standard hemispherical caps",
                "notes": "Topological surgery continuing Ricci flow beyond finite-time pinching singularities",
            },
        },
        {
            "joint_id": "joint:perelman:reduced_volume_monotonicity",
            "joint_type": "MONOTONICITY_FORMULA",
            "relationship": "MONOTONE_ALONG",
            "feet": [
                {
                    "endpoint_id": "srcdecl:perelman_reduced_volume",
                    "role": "functional_quantity",
                    "view": "EO",
                },
                {
                    "endpoint_id": "srcdecl:backward_ricci_flow_pde",
                    "role": "flow_trajectory",
                    "view": "GEO",
                },
            ],
            "scope": scope_3d.to_dict(),
            "status": "CANDIDATE",
            "metadata": {
                "formula": "d/d_tau V_tilde(tau) <= 0",
                "notes": "Reduced volume monotonically non-increasing along backward Ricci flow",
            },
        },
    ]

    data = {
        "schema_version": "0.21",
        "description": "Preregistered candidate mechanism joints for Package P (Perelman mechanisms) testing in v0.21",
        "joints": joints,
    }

    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    return PerelmanJointsResult(
        all_checks_passed=True,
        joints_count=len(joints),
        out_file=out_file,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Perelman candidate mechanism joints")
    parser.add_argument("--out-file", type=Path, default=ROOT / "formal" / "joints_perelman_v0_21.json")
    args = parser.parse_args()

    res = generate_perelman_candidate_joints(args.out_file)
    print(f"[Package P] Generated {res.joints_count} candidate mechanism joints -> {res.out_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
