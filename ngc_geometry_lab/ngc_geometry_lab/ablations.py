"""Controlled ablation experiments testing the explanatory necessity of geometric structures.

This module evaluates the full geometric model against five degraded alternatives:
1. Temporal Ordering Ablation: Ordered composition vs unordered/commutative operations.
2. Plane Orientation Ablation: Full geometric product (dot + wedge) vs scalar-only dot product.
3. Phase / Dual-Lane Ablation: Phase-coherent dual-lane coupling vs incoherent mixture.
4. Joint Correlation Subspace Ablation: Full joint tensor T_ij vs local marginals only.
5. Path Geometry Ablation: Closed-loop holonomy (Berry phase) vs endpoint-only description.
"""

from __future__ import annotations

import itertools
import math
from typing import Any, Dict, List, Tuple

import numpy as np

from . import geometry as geo
from . import reference as ref


def _require_finite(array: np.ndarray, name: str) -> np.ndarray:
    arr = np.asarray(array)
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} contains nonfinite values")
    return arr


# -----------------------------------------------------------------------------
# 1. Temporal Ordering Ablation
# -----------------------------------------------------------------------------
def ablate_temporal_order(
    rotations: List[Tuple[np.ndarray, float]],
    initial_state: np.ndarray,
) -> Dict[str, Any]:
    """Compare ordered rotation sequence with commutative/unordered composition.

    In the ordered model, U = R_k ... R_2 R_1.
    In the ablated model, rotations are executed in arbitrary/sorted order or
    generators are treated as commuting: exp(sum theta_i J_i).
    Also tests initial-state recovery: U^T U s_0 = s_0, whereas the unordered
    inverse U_unordered^T U s_0 fails to restore s_0.
    """
    s0 = _require_finite(np.asarray(initial_state, dtype=float), "initial_state")
    if s0.shape != (3,):
        raise ValueError("initial_state must have shape (3,)")

    # 1. Full ordered evolution
    current = s0.copy()
    ordered_matrices = []
    for axis, angle in rotations:
        r_mat = geo.rotation(axis, angle)
        ordered_matrices.append(r_mat)
        current = r_mat @ current
    s_ordered = current

    # 2. Ablated: reversed order
    current_rev = s0.copy()
    for r_mat in reversed(ordered_matrices):
        current_rev = r_mat @ current_rev
    s_reversed = current_rev

    # 3. Ablated: generator sum (commutative Baker-Campbell-Hausdorff order 0)
    # Generator for rotation about axis n by angle theta is theta * hat(n)_x
    total_generator = np.zeros((3, 3))
    for axis, angle in rotations:
        u_axis = axis / np.linalg.norm(axis)
        # cross-product matrix [u]_x
        ux = np.array([
            [0.0, -u_axis[2], u_axis[1]],
            [u_axis[2], 0.0, -u_axis[0]],
            [-u_axis[1], u_axis[0], 0.0],
        ])
        total_generator += angle * ux
    # matrix exponential via Rodrigues
    gen_norm = np.linalg.norm([total_generator[2, 1], total_generator[0, 2], total_generator[1, 0]])
    if gen_norm > 1e-12:
        eff_axis = np.array([total_generator[2, 1], total_generator[0, 2], total_generator[1, 0]]) / gen_norm
        r_commutative = geo.rotation(eff_axis, gen_norm)
    else:
        r_commutative = np.eye(3)
    s_commutative = r_commutative @ s0

    # 4. Inversion / history recovery
    # Exact ordered inverse: R_1^T ... R_k^T
    inv_ordered = s_ordered.copy()
    for r_mat in reversed(ordered_matrices):
        inv_ordered = r_mat.T @ inv_ordered

    # Inversion with wrong order: R_k^T ... R_1^T
    inv_wrong_order = s_ordered.copy()
    for r_mat in ordered_matrices:
        inv_wrong_order = r_mat.T @ inv_wrong_order

    order_discrepancy = float(np.linalg.norm(s_ordered - s_reversed))
    comm_discrepancy = float(np.linalg.norm(s_ordered - s_commutative))
    recovery_error_exact = float(np.linalg.norm(inv_ordered - s0))
    recovery_error_wrong = float(np.linalg.norm(inv_wrong_order - s0))

    return {
        "ordered_final_state": s_ordered.tolist(),
        "reversed_final_state": s_reversed.tolist(),
        "commutative_final_state": s_commutative.tolist(),
        "reversed_order_discrepancy": order_discrepancy,
        "commutative_discrepancy": comm_discrepancy,
        "exact_recovery_error": recovery_error_exact,
        "unordered_recovery_error": recovery_error_wrong,
        "order_matters": order_discrepancy > 1e-4,
        "recovery_requires_order": recovery_error_wrong > 1e-4,
    }


# -----------------------------------------------------------------------------
# 2. Plane Orientation Ablation (Bivector Wedge vs Scalar Dot)
# -----------------------------------------------------------------------------
def ablate_plane_orientation(
    vector_a: np.ndarray,
    vector_b: np.ndarray,
    vector_c: np.ndarray,
) -> Dict[str, Any]:
    """Compare full geometric product ab = a.b + a^b with scalar-only dot product.

    The scalar dot product a.b = |a||b|cos(theta) retains only relative angle.
    The bivector wedge product a^b represents the oriented plane of rotation.
    Under spatial reflection r -> -r (parity reversal):
    - All dot products a.b, b.c, c.a are strictly invariant.
    - The oriented triple product (a ^ b) . c changes sign (handedness/chirality).
    A scalar-only model cannot distinguish a right-handed coordinate frame or
    rotation sequence from a left-handed (reflected) one.
    """
    a = _require_finite(np.asarray(vector_a, dtype=float), "vector_a")
    b = _require_finite(np.asarray(vector_b, dtype=float), "vector_b")
    c = _require_finite(np.asarray(vector_c, dtype=float), "vector_c")

    # Full Geometric Algebra quantities
    dot_ab = float(np.dot(a, b))
    dot_bc = float(np.dot(b, c))
    dot_ca = float(np.dot(c, a))

    # Wedge product bivector in R^3 dual to cross product
    wedge_ab = np.cross(a, b)
    oriented_volume = float(np.dot(wedge_ab, c))  # (a ^ b) . c = det([a, b, c])

    # Parity-reversed vectors: r' = -r
    a_ref, b_ref, c_ref = -a, -b, -c
    dot_ab_ref = float(np.dot(a_ref, b_ref))
    dot_bc_ref = float(np.dot(b_ref, c_ref))
    dot_ca_ref = float(np.dot(c_ref, a_ref))

    wedge_ab_ref = np.cross(a_ref, b_ref)
    oriented_volume_ref = float(np.dot(wedge_ab_ref, c_ref))

    scalar_invariant_change = max(
        abs(dot_ab - dot_ab_ref),
        abs(dot_bc - dot_bc_ref),
        abs(dot_ca - dot_ca_ref),
    )
    chiral_volume_change = abs(oriented_volume - oriented_volume_ref)

    # Chiral rotation: rotation in oriented plane a^b by +theta vs -theta
    # Probe vector must have a non-zero component orthogonal to the rotation axis
    theta = np.pi / 3
    axis_norm = np.linalg.norm(wedge_ab)
    if axis_norm > 1e-12:
        axis = wedge_ab / axis_norm
        probe = a / (np.linalg.norm(a) + 1e-15)
        rot_pos = geo.rotation(axis, theta) @ probe
        rot_neg = geo.rotation(axis, -theta) @ probe
        chiral_rotation_separation = float(np.linalg.norm(rot_pos - rot_neg))
    else:
        chiral_rotation_separation = 0.0

    return {
        "scalar_dot_products": {"ab": dot_ab, "bc": dot_bc, "ca": dot_ca},
        "scalar_parity_delta": scalar_invariant_change,
        "oriented_volume": oriented_volume,
        "reflected_volume": oriented_volume_ref,
        "chiral_volume_delta": chiral_volume_change,
        "chiral_rotation_separation": chiral_rotation_separation,
        "scalar_model_blind_to_parity": scalar_invariant_change < 1e-12 and chiral_volume_change > 1e-6,
    }


# -----------------------------------------------------------------------------
# 3. Phase / Dual-Lane Ablation (Interference vs Incoherent Mixture)
# -----------------------------------------------------------------------------
def ablate_phase_interference(num_angles: int = 48) -> Dict[str, Any]:
    """Compare dual-lane phase-coherent evolution with incoherent dephased mixture.

    In a Ramsey / Mach-Zehnder interferometer:
    |0> -> H -> R_z(theta) -> H -> measure |0>
    Full coherent model: P(0) = cos^2(theta / 2).
    Interference fringe visibility V = (P_max - P_min) / (P_max + P_min) = 1.0.

    Phase-ablated model (incoherent dephasing where off-diagonal phase is dropped):
    rho = H |0><0| H -> diag(rho) = 0.5 |0><0| + 0.5 |1><1|.
    Under R_z(theta), diag(rho) is invariant.
    Second H produces P(0) = 0.5 for all theta.
    Fringe visibility collapses to V = 0.0.
    """
    angles = np.linspace(0, 2 * np.pi, num_angles, endpoint=False)
    coherent_p0 = []
    incoherent_p0 = []

    h_gate = np.array([[1.0, 1.0], [1.0, -1.0]]) / np.sqrt(2)

    for theta in angles:
        # Coherent dual-lane path
        psi0 = np.array([1.0, 0.0], dtype=complex)
        psi1 = h_gate @ psi0
        rz = ref.rotation_unitary([0, 0, 1], theta)
        psi2 = rz @ psi1
        psi3 = h_gate @ psi2
        p0_coh = float(np.abs(psi3[0]) ** 2)
        coherent_p0.append(p0_coh)

        # Incoherent ablated path: dephase after first beam splitter
        rho1 = np.outer(psi1, psi1.conj())
        rho1_dephased = np.diag(np.diag(rho1))  # drop off-diagonal phase
        rho2_dephased = rz @ rho1_dephased @ rz.conj().T
        rho3_dephased = h_gate @ rho2_dephased @ h_gate.conj().T
        p0_incoh = float(rho3_dephased[0, 0].real)
        incoherent_p0.append(p0_incoh)

    coherent_p0 = np.array(coherent_p0)
    incoherent_p0 = np.array(incoherent_p0)

    vis_coherent = float((coherent_p0.max() - coherent_p0.min()) / (coherent_p0.max() + coherent_p0.min() + 1e-15))
    vis_incoherent = float((incoherent_p0.max() - incoherent_p0.min()) / (incoherent_p0.max() + incoherent_p0.min() + 1e-15))

    return {
        "num_angles": num_angles,
        "coherent_fringe_visibility": vis_coherent,
        "incoherent_fringe_visibility": vis_incoherent,
        "fringe_destruction": float(vis_coherent - vis_incoherent),
        "incoherent_probabilities_flat": bool(np.allclose(incoherent_p0, 0.5, atol=1e-10)),
    }


# -----------------------------------------------------------------------------
# 4. Joint Correlation Subspace Ablation (T_ij vs Local Marginals)
# -----------------------------------------------------------------------------
def ablate_joint_correlations() -> Dict[str, Any]:
    """Compare 15-parameter joint space (r_A, r_B, T_ij) with local marginal model.

    The local marginal model retains only (r_A, r_B) and assumes T = r_A r_B^T.
    For the Bell singlet state:
    - True parameters: r_A = 0, r_B = 0, T = -I.
    - True joint tetrahedral distribution has TV distance 0.375 from the mixed state.
    - True CHSH = 2*sqrt(2) ~ 2.8284.

    Ablated marginal model:
    - Retains only r_A = 0, r_B = 0.
    - Imputes T_ablated = r_A r_B^T = 0.
    - Makes the singlet state completely indistinguishable from maximally mixed noise!
    - Collapses CHSH value to 0.0.
    """
    r_a = np.zeros(3)
    r_b = np.zeros(3)
    t_singlet = -np.eye(3)
    t_ablated = np.zeros((3, 3))  # r_a * r_b^T

    p_singlet = geo.joint_probabilities(r_a, r_b, t_singlet)
    p_ablated = geo.joint_probabilities(r_a, r_b, t_ablated)

    tv_distance = float(0.5 * np.sum(np.abs(p_singlet - p_ablated)))

    # Evaluate CHSH for optimal axes
    z = np.array([0.0, 0.0, 1.0])
    x = np.array([1.0, 0.0, 0.0])
    a0, a1 = z, x
    b0, b1 = (z + x) / np.sqrt(2), (z - x) / np.sqrt(2)

    chsh_singlet = float(abs(geo.chsh_value(t_singlet, a0, a1, b0, b1)))
    chsh_ablated = float(abs(geo.chsh_value(t_ablated, a0, a1, b0, b1)))

    return {
        "true_singlet_chsh": chsh_singlet,
        "ablated_marginal_chsh": chsh_ablated,
        "joint_tv_distance": tv_distance,
        "singlet_indistinguishable_from_noise_under_marginals": bool(np.allclose(t_ablated, 0)),
        "chsh_collapse": float(chsh_singlet - chsh_ablated),
    }


# -----------------------------------------------------------------------------
# 5. Path Geometry Ablation (Loop Holonomy / Berry Phase vs Endpoints)
# -----------------------------------------------------------------------------
def ablate_path_geometry(solid_angle_fraction: float = 0.125) -> Dict[str, Any]:
    """Compare cyclic transport (enclosing solid angle Omega) with endpoint-only model.

    In parallel transport of a spin-1/2 state around a spherical octant loop
    (e.g., North Pole (Z) -> Equator (X) -> Equator (Y) -> North Pole (Z)):
    - Solid angle enclosed: Omega = pi/2 steradians (1/8 of sphere = 4*pi / 8 = pi/2).
    - Acquired geometric holonomy phase: gamma = -Omega / 2 = -pi / 4.
    - An endpoint-only description observes r_initial = (0, 0, 1) and r_final = (0, 0, 1),
      thus predicting Delta phi = 0.
    - In an interference experiment with an unrotated reference arm:
      I_full = cos^2(gamma / 2) = cos^2(pi / 8) ~ 0.8535.
      I_ablated = cos^2(0) = 1.0.
    """
    # Construct a spherical triangle loop: Z -> X -> Y -> Z
    # Solid angle of octant is Omega = pi / 2
    omega = np.pi / 2
    gamma_geometric = -omega / 2  # -pi/4

    # Execute discrete unitary path:
    # 1. Rotate around Y by pi/2: Z -> X
    # 2. Rotate around Z by pi/2: X -> Y
    # 3. Rotate around X by pi/2: Y -> Z
    ry = ref.rotation_unitary([0, 1, 0], np.pi / 2)
    rz = ref.rotation_unitary([0, 0, 1], np.pi / 2)
    rx = ref.rotation_unitary([1, 0, 0], np.pi / 2)

    u_loop = rx @ rz @ ry

    initial_state = np.array([1.0, 0.0], dtype=complex)  # |0> (Z-pole)
    final_state = u_loop @ initial_state

    # Check that state returns to same ray on Bloch sphere
    density_initial = np.outer(initial_state, initial_state.conj())
    density_final = np.outer(final_state, final_state.conj())
    bloch_initial = ref.bloch_from_density(density_initial)
    bloch_final = ref.bloch_from_density(density_final)
    bloch_endpoint_distance = float(np.linalg.norm(bloch_final - bloch_initial))

    # Phase acquired
    phase_factor = final_state[0] / initial_state[0]
    extracted_phase = float(math.atan2(phase_factor.imag, phase_factor.real))

    # Superposition interference with reference arm: (|0>_ref + |psi_final>) / sqrt(2)
    p_interfere_full = float(0.5 * np.abs(1.0 + phase_factor) ** 2 / 2.0)
    p_interfere_endpoint = 1.0  # endpoint model assumes no phase change

    return {
        "solid_angle_omega": float(omega),
        "theoretical_berry_phase": float(gamma_geometric),
        "measured_holonomy_phase": float(extracted_phase),
        "bloch_endpoint_distance": bloch_endpoint_distance,
        "interference_probability_full": p_interfere_full,
        "interference_probability_endpoint_only": p_interfere_endpoint,
        "phase_prediction_error": float(abs(p_interfere_endpoint - p_interfere_full)),
        "loop_closed_on_bloch_sphere": bloch_endpoint_distance < 1e-10,
    }


# -----------------------------------------------------------------------------
# Master Ablation Suite Runner
# -----------------------------------------------------------------------------
def run_all_ablations(seed: int = 20261022) -> Dict[str, Any]:
    """Execute all five ablation experiments and return comparative results."""
    rng = np.random.default_rng(seed)

    # 1. Temporal Ordering
    rot_axes = [rng.normal(size=3) for _ in range(4)]
    rot_angles = rng.uniform(0.2, 1.5, 4).tolist()
    rotations = list(zip(rot_axes, rot_angles))
    init_state = rng.normal(size=3)
    init_state /= np.linalg.norm(init_state)
    res_order = ablate_temporal_order(rotations, init_state)

    # 2. Plane Orientation
    va, vb, vc = [rng.normal(size=3) for _ in range(3)]
    res_orientation = ablate_plane_orientation(va, vb, vc)

    # 3. Phase / Dual-Lane
    res_phase = ablate_phase_interference(48)

    # 4. Joint Correlations
    res_joint = ablate_joint_correlations()

    # 5. Path Geometry
    res_path = ablate_path_geometry()

    return {
        "seed": seed,
        "temporal_order": res_order,
        "plane_orientation": res_orientation,
        "phase_interference": res_phase,
        "joint_correlations": res_joint,
        "path_geometry": res_path,
        "summary": {
            "temporal_order_divergence": res_order["reversed_order_discrepancy"],
            "parity_chiral_delta": res_orientation["chiral_volume_delta"],
            "fringe_visibility_loss": res_phase["fringe_destruction"],
            "chsh_correlation_loss": res_joint["chsh_collapse"],
            "berry_phase_shift_error": res_path["phase_prediction_error"],
        },
    }
