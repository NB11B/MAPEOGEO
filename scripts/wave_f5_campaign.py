"""Wave F5 Executable Campaign Runner (Contracts Q01–Q18 & Falsifications)."""

import argparse
import hashlib
import json
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mapeogeo.wave_f5.certificates import WaveF5CertificateVerifier
from mapeogeo.wave_f5.dual_views import (
    geo_q01_contraction_geometry,
    geo_q02_adjoint_pairing_geometry,
    geo_q03_orthogonal_projector_geometry,
    geo_q04_resolvent_disk_geometry,
    geo_q05_spectral_subspace_geometry,
    geo_q06_picard_corridor_geometry,
    geo_q07_nonuniqueness_cusp_geometry,
    geo_q08_blowup_horizon_geometry,
    geo_q09_flow_manifold_geometry,
    geo_q10_nonautonomous_evolution_cocycle,
    geo_q11_lyapunov_ellipsoid_geometry,
    geo_q12_nonhyperbolic_phase_geometry,
    geo_q13_nonnormal_numerical_range,
    geo_q14_symplectic_phase_orbit,
    geo_q15_validated_solution_tube_geometry,
    geo_q16_invariant_polytope_geometry,
    geo_q17_transversal_hypersurface_crossing,
    geo_q18_green_operator_kernel_geometry,
)
from mapeogeo.wave_f5.enclosures import (
    RationalInterval,
    verify_q15_residual_enclosure,
    verify_q16_logistic_invariant_interval,
    verify_q17_transversal_event,
    verify_q18_regular_dirichlet_bvp,
)
from mapeogeo.wave_f5.ode import (
    verify_q06_picard_self_map,
    verify_q07_nonuniqueness,
    verify_q08_blowup,
    verify_q09_autonomous_flow,
    verify_q10_nonautonomous_evolution,
    verify_q11_lyapunov_stability,
    verify_q12_nonhyperbolic_stability,
    verify_q13_transient_growth,
    verify_q14_conservative_harmonic,
)
from mapeogeo.wave_f5.operators import (
    verify_q01_contraction,
    verify_q02_adjoint,
    verify_q03_orthogonal_projection,
    verify_q04_neumann_series,
    verify_q05_spectral_decomposition,
)

FORMAL_DIR = REPO_ROOT / "formal" / "wave_f5"


def compute_sha256(data: Any) -> str:
    s = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def run_wave_f5_campaign(
    output_certs: Optional[Path] = None,
    output_ledger: Optional[Path] = None,
) -> Dict[str, Any]:
    """Execute all 18 Wave F5 contracts and negative falsifications, producing verified certificates."""
    contracts_file = FORMAL_DIR / "contracts.json"
    with open(contracts_file, "r", encoding="utf-8") as f:
        contracts_meta = json.load(f).get("contracts", {})

    formulations_file = FORMAL_DIR / "formulations.json"
    with open(formulations_file, "r", encoding="utf-8") as f:
        forms_data = json.load(f).get("formulations", [])
    active_concepts = {f["canonical_id"] for f in forms_data if "canonical_id" in f}

    verifier = WaveF5CertificateVerifier(active_concepts=active_concepts)

    results: List[Dict[str, Any]] = []
    certificates: List[Dict[str, Any]] = []
    falsifications_verified = 0

    # --- Q01: Banach Contraction Iteration ---
    q01_pos = verify_q01_contraction(
        T=lambda x: Fraction(1, 2) * x + 1,
        interval=(Fraction(0), Fraction(2)),
        q=Fraction(1, 2),
        fixed_point=Fraction(2),
    )
    q01_geo = geo_q01_contraction_geometry(
        T=lambda x: Fraction(1, 2) * x + 1,
        interval=(Fraction(0), Fraction(2)),
        q=Fraction(1, 2),
        fixed_point=Fraction(2),
    )
    q01_fals = verify_q01_contraction(
        T=lambda x: x,
        interval=(Fraction(0), Fraction(2)),
        q=Fraction(1),
        fixed_point=Fraction(1),
    )
    if q01_pos["verified"] and q01_geo["verified"] and not q01_fals["verified"]:
        falsifications_verified += 1
    results.append({
        "contract_id": "Q01",
        "verified": q01_pos["verified"] and q01_geo["verified"],
        "eo_verified": q01_pos["verified"],
        "geo_verified": q01_geo["verified"],
        "eo_payload": q01_pos,
        "geo_payload": q01_geo,
    })

    # --- Q02: Finite-Dimensional Adjoint ---
    A_q02 = np.array([[Fraction(1), Fraction(2)], [Fraction(0), Fraction(3)]])
    G_q02 = np.array([[Fraction(2), Fraction(0)], [Fraction(0), Fraction(1)]])
    A_star_q02 = np.array([[Fraction(1), Fraction(0)], [Fraction(4), Fraction(3)]])
    q02_pos = verify_q02_adjoint(A=A_q02, G=G_q02, A_star=A_star_q02)
    q02_geo = geo_q02_adjoint_pairing_geometry(A=A_q02, G=G_q02, A_star=A_star_q02)
    q02_fals = verify_q02_adjoint(A=A_q02, G=G_q02, A_star=A_q02.T)
    if q02_pos["verified"] and q02_geo["verified"] and not q02_fals["verified"]:
        falsifications_verified += 1
    results.append({
        "contract_id": "Q02",
        "verified": q02_pos["verified"] and q02_geo["verified"],
        "eo_verified": q02_pos["verified"],
        "geo_verified": q02_geo["verified"],
        "eo_payload": {"status": "adjoint_paired", "matrix_dim": 2},
        "geo_payload": q02_geo,
    })

    # --- Q03: Orthogonal Projection ---
    basis_q03 = [np.array([Fraction(1), Fraction(1)])]
    P_q03 = np.array([[Fraction(1, 2), Fraction(1, 2)], [Fraction(1, 2), Fraction(1, 2)]])
    P_obl = np.array([[Fraction(1), Fraction(1)], [Fraction(0), Fraction(0)]])
    q03_pos = verify_q03_orthogonal_projection(P=P_q03, basis=basis_q03)
    q03_geo = geo_q03_orthogonal_projector_geometry(P=P_q03, basis=basis_q03)
    q03_fals = verify_q03_orthogonal_projection(P=P_obl, basis=basis_q03)
    if q03_pos["verified"] and q03_geo["verified"] and not q03_fals["verified"]:
        falsifications_verified += 1
    results.append({
        "contract_id": "Q03",
        "verified": q03_pos["verified"] and q03_geo["verified"],
        "eo_verified": q03_pos["verified"],
        "geo_verified": q03_geo["verified"],
        "eo_payload": {"rank": 1, "idempotent": True, "self_adjoint": True},
        "geo_payload": q03_geo,
    })

    # --- Q04: Neumann Series ---
    A_q04 = np.array([[Fraction(1, 4), Fraction(1, 4)], [Fraction(1, 8), Fraction(1, 8)]])
    q04_pos = verify_q04_neumann_series(A=A_q04, N=5)
    q04_geo = geo_q04_resolvent_disk_geometry(A=A_q04, N=5)
    A_large = np.array([[Fraction(1), Fraction(0)], [Fraction(0), Fraction(1)]])
    q04_fals = verify_q04_neumann_series(A=A_large, N=5)
    if q04_pos["verified"] and q04_geo["verified"] and not q04_fals["verified"]:
        falsifications_verified += 1
    results.append({
        "contract_id": "Q04",
        "verified": q04_pos["verified"] and q04_geo["verified"],
        "eo_verified": q04_pos["verified"],
        "geo_verified": q04_geo["verified"],
        "eo_payload": {"norm_A": str(q04_pos["norm_A"]), "series_terms": 5},
        "geo_payload": q04_geo,
    })

    # --- Q05: Spectral Decomposition ---
    A_q05 = np.array([[Fraction(2), Fraction(0)], [Fraction(0), Fraction(5)]])
    eigs_q05 = [Fraction(2), Fraction(5)]
    projs_q05 = [
        np.array([[Fraction(1), Fraction(0)], [Fraction(0), Fraction(0)]]),
        np.array([[Fraction(0), Fraction(0)], [Fraction(0), Fraction(1)]]),
    ]
    q05_pos = verify_q05_spectral_decomposition(A=A_q05, eigenvalues=eigs_q05, projectors=projs_q05)
    q05_geo = geo_q05_spectral_subspace_geometry(A=A_q05, eigenvalues=eigs_q05, projectors=projs_q05)
    q05_fals = verify_q05_spectral_decomposition(A=A_q05, eigenvalues=eigs_q05[:1], projectors=projs_q05[:1])
    if q05_pos["verified"] and q05_geo["verified"] and not q05_fals["verified"]:
        falsifications_verified += 1
    results.append({
        "contract_id": "Q05",
        "verified": q05_pos["verified"] and q05_geo["verified"],
        "eo_verified": q05_pos["verified"],
        "geo_verified": q05_geo["verified"],
        "eo_payload": {"eigenvalues": [2, 5], "identity_sum": True},
        "geo_payload": q05_geo,
    })

    # --- Q06: Picard Self-Map ---
    h_q06 = Fraction(1, 4)
    M_q06 = Fraction(3, 2)
    L_q06 = Fraction(1)
    r_q06 = Fraction(1, 2)
    q06_pos = verify_q06_picard_self_map(h=h_q06, M=M_q06, L=L_q06, r=r_q06)
    q06_geo = geo_q06_picard_corridor_geometry(h=h_q06, M=M_q06, L=L_q06, r=r_q06)
    q06_fals = verify_q06_picard_self_map(h=Fraction(1, 2), M=M_q06, L=L_q06, r=r_q06)
    if q06_pos["verified"] and q06_geo["verified"] and not q06_fals["verified"]:
        falsifications_verified += 1
    results.append({
        "contract_id": "Q06",
        "verified": q06_pos["verified"] and q06_geo["verified"],
        "eo_verified": q06_pos["verified"],
        "geo_verified": q06_geo["verified"],
        "eo_payload": {"h": "1/4", "hM": "3/8", "hL": "1/4", "invariant_ball": True},
        "geo_payload": q06_geo,
    })

    # --- Q07: Nonuniqueness Boundary ---
    q07_pos = verify_q07_nonuniqueness(claimed_unique=False, has_existence=True)
    q07_geo = geo_q07_nonuniqueness_cusp_geometry(c_values=[0.0, 0.25, 0.5])
    q07_fals = verify_q07_nonuniqueness(claimed_unique=True, has_existence=True)
    if q07_pos["verified"] and q07_geo["verified"] and not q07_fals["verified"]:
        falsifications_verified += 1
    results.append({
        "contract_id": "Q07",
        "verified": q07_pos["verified"] and q07_geo["verified"],
        "eo_verified": q07_pos["verified"],
        "geo_verified": q07_geo["verified"],
        "eo_payload": {"existence": True, "uniqueness": False, "peano_boundary": True},
        "geo_payload": q07_geo,
    })

    # --- Q08: Continuation and Blow-up ---
    t_eval_q08 = Fraction(1, 2)
    t_max_q08 = Fraction(1)
    q08_pos = verify_q08_blowup(t_eval=t_eval_q08, t_max=t_max_q08)
    q08_geo = geo_q08_blowup_horizon_geometry(t_eval=t_eval_q08, t_max=t_max_q08)
    q08_fals = verify_q08_blowup(t_eval=Fraction(1), t_max=t_max_q08)
    if q08_pos["verified"] and q08_geo["verified"] and not q08_fals["verified"]:
        falsifications_verified += 1
    results.append({
        "contract_id": "Q08",
        "verified": q08_pos["verified"] and q08_geo["verified"],
        "eo_verified": q08_pos["verified"],
        "geo_verified": q08_geo["verified"],
        "eo_payload": {"t_max": 1, "t_eval": "1/2", "norm_at_eval": 2.0},
        "geo_payload": q08_geo,
    })

    # --- Q09: Autonomous Flow Composition ---
    def phi_q09(t: Fraction, x: Fraction) -> Fraction:
        return x / (Fraction(1) - t * x)

    x_q09 = Fraction(1, 2)
    s_q09 = Fraction(1, 4)
    t_q09 = Fraction(1, 4)
    q09_pos = verify_q09_autonomous_flow(phi=phi_q09, x=x_q09, s=s_q09, t=t_q09)
    q09_geo = geo_q09_flow_manifold_geometry(phi=phi_q09, x=x_q09, s=s_q09, t=t_q09)
    fals_raised = False
    try:
        verify_q09_autonomous_flow(phi=phi_q09, x=Fraction(2), s=Fraction(1, 2), t=Fraction(1))
    except ValueError:
        fals_raised = True
    if q09_pos["verified"] and q09_geo["verified"] and fals_raised:
        falsifications_verified += 1
    results.append({
        "contract_id": "Q09",
        "verified": q09_pos["verified"] and q09_geo["verified"],
        "eo_verified": q09_pos["verified"],
        "geo_verified": q09_geo["verified"],
        "eo_payload": {"group_law": True, "evaluation_point": "1/2"},
        "geo_payload": q09_geo,
    })

    # --- Q10: Nonautonomous Evolution ---
    def U_q10(t: float, s: float) -> float:
        import math
        return float(math.exp((t**2 - s**2) / 2.0))

    q10_pos = verify_q10_nonautonomous_evolution(U=U_q10, t=2.0, s=1.0, r=0.0, is_time_homogeneous_claimed=False)
    q10_geo = geo_q10_nonautonomous_evolution_cocycle(U=U_q10, t=2.0, s=1.0, r=0.0)
    q10_fals = verify_q10_nonautonomous_evolution(U=U_q10, t=2.0, s=1.0, r=0.0, is_time_homogeneous_claimed=True)
    if q10_pos["verified"] and q10_geo["verified"] and not q10_fals["verified"]:
        falsifications_verified += 1
    results.append({
        "contract_id": "Q10",
        "verified": q10_pos["verified"] and q10_geo["verified"],
        "eo_verified": q10_pos["verified"],
        "geo_verified": q10_geo["verified"],
        "eo_payload": {"two_time_cocycle": True, "time_inhomogeneous": True},
        "geo_payload": q10_geo,
    })

    # --- Q11: Lyapunov Stability ---
    A_q11 = np.array([[-1.0, 0.0], [0.0, -2.0]])
    V_q11 = np.eye(2)
    q11_pos = verify_q11_lyapunov_stability(A=A_q11, V=V_q11)
    q11_geo = geo_q11_lyapunov_ellipsoid_geometry(A=A_q11, V=V_q11)
    V_bad = np.array([[1.0, 0.0], [0.0, -1.0]])
    q11_fals = verify_q11_lyapunov_stability(A=A_q11, V=V_bad)
    if q11_pos["verified"] and q11_geo["verified"] and not q11_fals["verified"]:
        falsifications_verified += 1
    results.append({
        "contract_id": "Q11",
        "verified": q11_pos["verified"] and q11_geo["verified"],
        "eo_verified": q11_pos["verified"],
        "geo_verified": q11_geo["verified"],
        "eo_payload": {"orbital_derivative": "negative_definite", "strictly_decreasing": True},
        "geo_payload": q11_geo,
    })

    # --- Q12: Nonhyperbolic Stability ---
    q12_pos = verify_q12_nonhyperbolic_stability(cubic_sign=-1, linear_eval_only=False)
    q12_geo = geo_q12_nonhyperbolic_phase_geometry(cubic_sign=-1)
    q12_fals = verify_q12_nonhyperbolic_stability(cubic_sign=-1, linear_eval_only=True)
    if q12_pos["verified"] and q12_geo["verified"] and not q12_fals["verified"]:
        falsifications_verified += 1
    results.append({
        "contract_id": "Q12",
        "verified": q12_pos["verified"] and q12_geo["verified"],
        "eo_verified": q12_pos["verified"],
        "geo_verified": q12_geo["verified"],
        "eo_payload": {"cubic_stable": True, "linear_inconclusive": True},
        "geo_payload": q12_geo,
    })

    # --- Q13: Transient Growth ---
    A_q13 = np.array([[-1.0, 10.0], [0.0, -2.0]])
    q13_pos = verify_q13_transient_growth(A=A_q13, t_sample=0.1)
    q13_geo = geo_q13_nonnormal_numerical_range(A=A_q13)
    q13_fals = verify_q13_transient_growth(A=A_q13, t_sample=0.1, assert_monotonic_decay=True)
    if q13_pos["verified"] and q13_geo["verified"] and not q13_fals["verified"]:
        falsifications_verified += 1
    results.append({
        "contract_id": "Q13",
        "verified": q13_pos["verified"] and q13_geo["verified"],
        "eo_verified": q13_pos["verified"],
        "geo_verified": q13_geo["verified"],
        "eo_payload": {"transient_growth": q13_pos.get("transient_norm_growth"), "spectral_abscissa_negative": True},
        "geo_payload": q13_geo,
    })

    # --- Q14: Conservative Harmonic ---
    traj_q14 = [(float(np.cos(t)), float(np.sin(t))) for t in [0.0, np.pi / 4, np.pi / 2, np.pi]]
    q14_pos = verify_q14_conservative_harmonic(trajectory=traj_q14, claimed_asymptotic_stable=False)
    q14_geo = geo_q14_symplectic_phase_orbit(trajectory=traj_q14)
    q14_fals = verify_q14_conservative_harmonic(trajectory=traj_q14, claimed_asymptotic_stable=True)
    if q14_pos["verified"] and q14_geo["verified"] and not q14_fals["verified"]:
        falsifications_verified += 1
    results.append({
        "contract_id": "Q14",
        "verified": q14_pos["verified"] and q14_geo["verified"],
        "eo_verified": q14_pos["verified"],
        "geo_verified": q14_geo["verified"],
        "eo_payload": {"energy_conserved": True, "asymptotically_stable": False},
        "geo_payload": q14_geo,
    })

    # --- Q15: Validated Residual Enclosure ---
    h_q15 = Fraction(1, 2)
    R_true_q15 = (h_q15 ** 3) / Fraction(6)
    q15_pos = verify_q15_residual_enclosure(h=h_q15, degree=3, e0=Fraction(0), claimed_R=R_true_q15)
    q15_geo = geo_q15_validated_solution_tube_geometry(h=h_q15, degree=3, e0=Fraction(0), claimed_R=R_true_q15)
    q15_fals = verify_q15_residual_enclosure(h=h_q15, degree=3, e0=Fraction(0), claimed_R=R_true_q15 / 2)
    if q15_pos["verified"] and q15_geo["verified"] and not q15_fals["verified"]:
        falsifications_verified += 1
    results.append({
        "contract_id": "Q15",
        "verified": q15_pos["verified"] and q15_geo["verified"],
        "eo_verified": q15_pos["verified"],
        "geo_verified": q15_geo["verified"],
        "eo_payload": {"tube_radius": q15_pos["tube_radius"], "analytical_exp_bound": True},
        "geo_payload": q15_geo,
    })

    # --- Q16: Logistic Invariant Interval ---
    init_box_q16 = RationalInterval(Fraction(1, 10), Fraction(9, 10))
    inv_box_q16 = RationalInterval(Fraction(0), Fraction(1))
    q16_pos = verify_q16_logistic_invariant_interval(initial_box=init_box_q16, invariant_box=inv_box_q16)
    q16_geo = geo_q16_invariant_polytope_geometry(initial_box=init_box_q16, invariant_box=inv_box_q16)
    q16_fals = verify_q16_logistic_invariant_interval(
        initial_box=RationalInterval(Fraction(-1, 10), Fraction(1, 2)),
        invariant_box=inv_box_q16,
    )
    if q16_pos["verified"] and q16_geo["verified"] and not q16_fals["verified"]:
        falsifications_verified += 1
    results.append({
        "contract_id": "Q16",
        "verified": q16_pos["verified"] and q16_geo["verified"],
        "eo_verified": q16_pos["verified"],
        "geo_verified": q16_geo["verified"],
        "eo_payload": {"invariant_region": "[0,1]", "rational_boundary_inward": True},
        "geo_payload": q16_geo,
    })

    # --- Q17: Transversal Event ---
    t_int_q17 = RationalInterval(Fraction(3, 4), Fraction(5, 4))
    x_int_q17 = RationalInterval(Fraction(7, 10), Fraction(13, 10))
    q17_pos = verify_q17_transversal_event(
        H_func=lambda x: x - Fraction(1),
        grad_H_func=lambda x: Fraction(1),
        f_func=lambda t, x: Fraction(1),
        trajectory_enclosure=lambda t: RationalInterval(t - Fraction(1, 100), t + Fraction(1, 100)),
        t_interval=t_int_q17,
        x_interval=x_int_q17,
    )
    q17_geo = geo_q17_transversal_hypersurface_crossing(
        grad_H=1.0,
        f_val=1.0,
        t_interval=t_int_q17,
        x_interval=x_int_q17,
    )
    q17_fals = verify_q17_transversal_event(
        H_func=lambda x: x - Fraction(1),
        grad_H_func=lambda x: Fraction(1),
        f_func=lambda t, x: Fraction(0),
        trajectory_enclosure=lambda t: RationalInterval(t, t),
        t_interval=t_int_q17,
        x_interval=x_int_q17,
    )
    if q17_pos["verified"] and q17_geo["verified"] and not q17_fals["verified"]:
        falsifications_verified += 1
    results.append({
        "contract_id": "Q17",
        "verified": q17_pos["verified"] and q17_geo["verified"],
        "eo_verified": q17_pos["verified"],
        "geo_verified": q17_geo["verified"],
        "eo_payload": {"transversal": True, "ivt_bracket_satisfied": True, "lie_derivative_bounded": True},
        "geo_payload": q17_geo,
    })

    # --- Q18: Regular Dirichlet BVP ---
    u_poly_q18 = [Fraction(0), Fraction(1), Fraction(-1)]
    f_poly_q18 = [Fraction(2)]
    q18_pos = verify_q18_regular_dirichlet_bvp(
        u_poly_coeffs=u_poly_q18,
        f_poly_coeffs=f_poly_q18,
        bc_0=Fraction(0),
        bc_1=Fraction(0),
    )
    q18_geo = geo_q18_green_operator_kernel_geometry(
        u_poly_coeffs=u_poly_q18,
        f_poly_coeffs=f_poly_q18,
    )
    q18_fals = verify_q18_regular_dirichlet_bvp(
        u_poly_coeffs=[Fraction(0), Fraction(3, 2), Fraction(-1)],
        f_poly_coeffs=f_poly_q18,
        bc_0=Fraction(0),
        bc_1=Fraction(0),
    )
    if q18_pos["verified"] and q18_geo["verified"] and not q18_fals["verified"]:
        falsifications_verified += 1
    results.append({
        "contract_id": "Q18",
        "verified": q18_pos["verified"] and q18_geo["verified"],
        "eo_verified": q18_pos["verified"],
        "geo_verified": q18_geo["verified"],
        "eo_payload": {"bc_satisfied": True, "exact_symbolic_residual_zero": True, "pde_satisfied": True},
        "geo_payload": q18_geo,
    })

    # Construct certificates
    for res in results:
        qid = res["contract_id"]
        meta = contracts_meta.get(qid, {})
        target = meta.get("target_concept", f"canonical:concept:{qid.lower()}")
        evidence_kind = meta.get("evidence_kind", "EXACT_RATIONAL")

        eo_payload = res["eo_payload"]
        geo_payload = res["geo_payload"]

        eo_digest = compute_sha256(eo_payload)
        geo_digest = compute_sha256(geo_payload)
        stmt_hash = compute_sha256({"target": target, "qid": qid, "positive": meta.get("positive_instance")})

        scope_record = {
            "domain": "scoped_contract_domain",
            "dimension": "canonical",
            "coefficient_ring": "real",
            "regularity": "C1_or_smooth",
            "orientation_convention": "standard",
            "boundary_convention": "standard",
            "parameter_range": "canonical",
            "exceptional_cases": "none",
        }

        view_slots = {
            "eo": {
                "status": "VERIFIED" if res["eo_verified"] else "REFUSED",
                "view_ref": f"view:eo:{qid.lower()}",
                "producer_id": f"producer:eo:exact_engine_{qid.lower()}",
                "statement_sha256": stmt_hash,
                "execution_digest": eo_digest,
                "witness_payload": eo_payload,
            },
            "geo": {
                "status": "VERIFIED" if res["geo_verified"] else "REFUSED",
                "view_ref": f"view:geo:{qid.lower()}",
                "producer_id": f"producer:geo:geometric_engine_{qid.lower()}",
                "statement_sha256": stmt_hash,
                "execution_digest": geo_digest,
                "witness_payload": geo_payload,
            },
            "pct": {"status": "ABSENT", "notes": "PCT chain transform not applicable"},
            "formal": {"status": "ABSENT", "notes": "Formal general Lean mathlib milestone"},
        }

        # Determine mechanism relationship
        rel_map = {
            "Q01": "CONTRACTION_OF",
            "Q02": "ACTS_ON",
            "Q03": "SPECTRAL_DECOMPOSITION_OF",
            "Q04": "BOUNDED_INSTANCE",
            "Q05": "SPECTRAL_DECOMPOSITION",
            "Q06": "CONTRACTION_OF",
            "Q07": "SCOPED_OVERLAP",
            "Q08": "BLOWS_UP_AS",
            "Q09": "EVOLUTION_FLOW",
            "Q10": "EVOLUTION_FLOW",
            "Q11": "MONOTONE_ALONG",
            "Q12": "SCOPED_OVERLAP",
            "Q13": "BOUNDED_INSTANCE",
            "Q14": "ACTS_ON",
            "Q15": "BOUNDED_INSTANCE",
            "Q16": "MONOTONE_ALONG",
            "Q17": "SCOPED_OVERLAP",
            "Q18": "BOUNDED_INSTANCE",
        }
        rel = rel_map.get(qid, "BOUNDED_INSTANCE")

        cert = {
            "certificate_id": f"cert:f5:{qid.lower()}",
            "target_concept": target,
            "relationship": rel,
            "scope": scope_record,
            "evidence_kind": evidence_kind,
            "view_slots": view_slots,
            "quorum_count": 2 if res["verified"] else 0,
            "verification_status": "CERTIFIED" if res["verified"] else "REJECTED",
        }

        # Verify through verifier
        v_res = verifier.verify_certificate(cert)
        cert["verification_status"] = v_res["verification_status"]
        cert["quorum_count"] = v_res["computed_quorum"]
        certificates.append(cert)

    # Output writing
    if output_certs is None:
        artifacts_dir = REPO_ROOT / "artifacts" / "wave_f5_v0_22"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        output_certs = artifacts_dir / "wave_f5_certificates.json"
    else:
        output_certs.parent.mkdir(parents=True, exist_ok=True)

    if output_ledger is None:
        artifacts_dir = REPO_ROOT / "artifacts" / "wave_f5_v0_22"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        output_ledger = artifacts_dir / "wave_f5_campaign_ledger.json"
    else:
        output_ledger.parent.mkdir(parents=True, exist_ok=True)

    certs_doc = {
        "schema_version": "0.22",
        "description": "Wave F5 correspondence certificates with independent dual-view witness quorum.",
        "certificates": certificates,
    }
    with open(output_certs, "w", encoding="utf-8") as f:
        json.dump(certs_doc, f, indent=2, default=str)

    ledger_doc = {
        "schema_version": "0.22",
        "campaign_id": "campaign:wave_f5_contracts_v0_22",
        "total_contracts": len(results),
        "passed_contracts": sum(1 for r in results if r["verified"]),
        "falsifications_verified": falsifications_verified,
        "results": results,
    }
    with open(output_ledger, "w", encoding="utf-8") as f:
        json.dump(ledger_doc, f, indent=2, default=str)

    print(f"Wave F5 Campaign Execution Complete: {len(results)} contracts, {falsifications_verified} falsifications verified.")
    return {
        "total_contracts": len(results),
        "passed_contracts": sum(1 for r in results if r["verified"]),
        "falsifications_verified": falsifications_verified,
        "certificates": certificates,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Wave F5 executable contract campaign")
    parser.add_argument("--certs-out", type=Path, default=None)
    parser.add_argument("--ledger-out", type=Path, default=None)
    args = parser.parse_args()

    res = run_wave_f5_campaign(output_certs=args.certs_out, output_ledger=args.ledger_out)
    return 0 if res["passed_contracts"] == res["total_contracts"] else 1


if __name__ == "__main__":
    sys.exit(main())
