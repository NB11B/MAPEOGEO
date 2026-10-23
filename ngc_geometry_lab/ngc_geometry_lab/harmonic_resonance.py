r"""Three-Mode Quantum Harmonic Dynamics and CP^2 vs Local Chart Geometry.

Analyzes the physical and geometric meaning of three coupled wavefunctions / harmonic modes:
  psi_k(t) = A_k * exp(i * (omega_k * t + phi_k)),  k = 1, 2, 3.

Key Geometric Insights:
1. Global Geometry vs Local Coordinate Chart:
   - For three normalized complex mode amplitudes modulo a common global phase,
     the exact global state space is the complex projective plane:
       CP^2 \cong SU(3) / U(2),   dim_R(CP^2) = 4.
   - Writing c_k = A_k exp(i phi_k) with A_1^2 + A_2^2 + A_3^2 = 1 and A_k >= 0
     shows that S^2_+ x T^2 is a useful local/interior coordinate chart for three modes
     (where S^2_+ is the positive octant of the 2-sphere and T^2 is the 2-torus of
     relative phases theta_1 = phi_2 - phi_1, theta_2 = phi_3 - phi_1).
   - On the boundaries where one or more A_k = 0, the associated phase is singular
     and the torus fibers collapse. CP^2 is the global relational quotient manifold.
2. The Controlled Information Loss Principle:
   - Representing the system purely by sphere coordinates (A_1, A_2, A_3) in S^2 discards T^2,
     causing severe observational collisions: identical sphere coordinates produce
     constructive (I = 3.0) vs destructive (I = 0.0) interference depending solely
     on relative phase differences.
3. Phase Recurrence / Commensurability Geometry vs Physical Resonance:
   - For an uncoupled phase-flow model theta(t) = theta_0 + Delta_omega * t (mod 2pi),
     the topological structure is characterized by the dimension of the orbit closure dim(O_bar):
       dim(O_bar) = 0: Delta_omega = 0 (phase-locked fixed point).
       dim(O_bar) = 1: one rational relation / periodic closure (closed torus knot, e.g. 1:2:3).
       dim(O_bar) = 2: rationally independent relative frequencies (dense ergodic flow on T^2).
   - Physical resonance in general requires dynamical coupling, forcing, or energy exchange;
     frequency commensurability provides the kinematic phase-recurrence condition.
4. Composite Rotor Formulation:
   - Composite operator R_comp(t) = R_3(t) R_2(t) R_1(t) in Spin(3) \cong SU(2).
   - For 1:2:3 commensurability, R_comp(2pi) = (-I)(+I)(-I) = +I, giving exact topological recurrence.
5. Observability Hierarchy:
   - 3D Spatial-Vector Observability: rank(sum v_k v_k^T) = 3 reconstructs a 3D real vector.
   - Coherent Three-Mode (Qutrit) Observability: requires phase-sensitive measurements;
     an informationally complete qutrit POVM requires d^2 = 9 independent outcomes
     (e.g. the 9-outcome Hesse SIC POVM), whereas the tetrahedral POVM is optimal for a qubit (d=2).
"""
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Tuple, Optional
import numpy as np


@dataclass(frozen=True)
class ThreeModeHarmonicSystem:
    """A three-mode harmonic wavefunction system: psi_k(t) = A_k exp(i (omega_k t + phi_k))."""
    amplitudes: Tuple[float, float, float]
    frequencies: Tuple[float, float, float]
    phases: Tuple[float, float, float]

    def __post_init__(self):
        norm_sq = sum(a**2 for a in self.amplitudes)
        if abs(norm_sq - 1.0) > 1e-6:
            raise ValueError(f"Amplitudes must be normalized to sum of squares = 1.0; got {norm_sq}")

    def to_sphere_coordinates(self) -> Tuple[float, float, float]:
        """Map normalized amplitudes to coordinates on the positive octant of S^2."""
        return self.amplitudes

    def relative_phases(self, t: float) -> Tuple[float, float]:
        """Compute relative phases (theta_1(t), theta_2(t)) on the torus T^2 = S^1 x S^1."""
        w1, w2, w3 = self.frequencies
        p1, p2, p3 = self.phases
        th1 = float(((w2 - w1) * t + (p2 - p1)) % (2.0 * np.pi))
        th2 = float(((w3 - w1) * t + (p3 - p1)) % (2.0 * np.pi))
        return th1, th2

    def resultant_wavefunction(self, t: float) -> complex:
        """Total scalar superposition: psi_tot(t) = sum_{k=1}^3 A_k exp(i (omega_k t + phi_k))."""
        val = 0.0 + 0.0j
        for A, w, p in zip(self.amplitudes, self.frequencies, self.phases):
            val += A * np.exp(1j * (w * t + p))
        return complex(val)

    def resultant_intensity(self, t: float) -> float:
        """Interference intensity / detector output: I(t) = |psi_tot(t)|^2."""
        return float(abs(self.resultant_wavefunction(t))**2)

    def composite_rotor(self, t: float) -> np.ndarray:
        """Composite evolution operator R_comp(t) = R_3(t) R_2(t) R_1(t) in SU(2).

        Rotations around orthogonal Pauli axes (x, y, z) by angles alpha_k(t) = omega_k t + phi_k.
        """
        def pauli_rotor(axis: str, angle: float) -> np.ndarray:
            sig = {
                'x': np.array([[0, 1], [1, 0]], dtype=complex),
                'y': np.array([[0, -1j], [1j, 0]], dtype=complex),
                'z': np.array([[1, 0], [0, -1]], dtype=complex)
            }[axis]
            return np.cos(angle / 2.0) * np.eye(2, dtype=complex) - 1j * np.sin(angle / 2.0) * sig

        w1, w2, w3 = self.frequencies
        p1, p2, p3 = self.phases
        R1 = pauli_rotor('x', w1 * t + p1)
        R2 = pauli_rotor('y', w2 * t + p2)
        R3 = pauli_rotor('z', w3 * t + p3)
        return R3 @ R2 @ R1


@dataclass(frozen=True)
class HarmonicResonanceAnalysisResult:
    """Certified analysis record for a three-mode harmonic system."""
    regime_id: str
    frequency_ratio_label: str
    sphere_point: Tuple[float, float, float]
    orbit_closure_dimension: int
    torus_orbit_closed: bool
    torus_return_residual: float
    rotor_orbit_closed: bool
    rotor_return_residual: float
    min_intensity: float
    max_intensity: float
    phase_locking_active: bool
    summary: str

    @property
    def torus_dimension(self) -> int:
        """Legacy alias for orbit_closure_dimension."""
        return self.orbit_closure_dimension

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def analyze_harmonic_resonance(
    system: ThreeModeHarmonicSystem,
    eval_time: float = 2.0 * np.pi,
    regime_id: str = "custom_harmonic_regime",
    frequency_ratio_label: str = "custom"
) -> HarmonicResonanceAnalysisResult:
    """Analyze phase recurrence, orbit closure, rotor recurrence, and interference behavior."""
    w1, w2, w3 = system.frequencies
    dw21 = w2 - w1
    dw31 = w3 - w1

    # Check phase-locking (dw = 0)
    is_phase_locked = bool(abs(dw21) < 1e-10 and abs(dw31) < 1e-10)

    # Torus closure at eval_time
    th1_0, th2_0 = system.relative_phases(0.0)
    th1_T, th2_T = system.relative_phases(eval_time)
    diff_th1 = min(abs(th1_T - th1_0), 2*np.pi - abs(th1_T - th1_0))
    diff_th2 = min(abs(th2_T - th2_0), 2*np.pi - abs(th2_T - th2_0))
    torus_res = float(np.sqrt(diff_th1**2 + diff_th2**2))
    torus_closed = bool(torus_res < 1e-10)

    # Rotor closure at eval_time
    R_0 = system.composite_rotor(0.0)
    R_T = system.composite_rotor(eval_time)
    rotor_res = float(np.linalg.norm(R_T - R_0))
    rotor_closed = bool(rotor_res < 1e-10)

    # Phase trajectory orbit closure dimension dim(O_bar):
    # dim(O_bar) = 0 for Delta_omega = 0 (fixed point)
    # dim(O_bar) = 1 for periodic closure (closed 1D torus knot)
    # dim(O_bar) = 2 for incommensurate frequencies (dense ergodic winding on T^2)
    if is_phase_locked:
        orbit_closure_dim = 0
    elif torus_closed:
        orbit_closure_dim = 1
    else:
        orbit_closure_dim = 2

    # Measure intensity range over fine time grid
    t_grid = np.linspace(0.0, eval_time, 200)
    intensities = [system.resultant_intensity(t) for t in t_grid]
    min_I = float(min(intensities))
    max_I = float(max(intensities))

    summary = (
        f"Regime {regime_id} ({frequency_ratio_label}): Orbit Closure Dim={orbit_closure_dim}, "
        f"Torus Closed={torus_closed} (res={torus_res:.2e}), "
        f"Rotor Closed={rotor_closed} (res={rotor_res:.2e}), "
        f"Intensity Range=[{min_I:.4f}, {max_I:.4f}]."
    )

    return HarmonicResonanceAnalysisResult(
        regime_id=regime_id,
        frequency_ratio_label=frequency_ratio_label,
        sphere_point=system.to_sphere_coordinates(),
        orbit_closure_dimension=orbit_closure_dim,
        torus_orbit_closed=torus_closed,
        torus_return_residual=torus_res,
        rotor_orbit_closed=rotor_closed,
        rotor_return_residual=rotor_res,
        min_intensity=min_I,
        max_intensity=max_I,
        phase_locking_active=is_phase_locked,
        summary=summary
    )


def run_three_mode_resonance_campaign() -> Dict[str, Any]:
    """Execute the 3-regime phase recurrence benchmark, information loss test, and observability audit.

    Evaluates:
      1. Case 1: Identical frequency (1:1:1) -> Phase-locked fixed point (Orbit Closure Dim 0).
      2. Case 2: Integer commensurability (1:2:3) -> Closed periodic torus knot (Orbit Closure Dim 1, Period = 2pi).
      3. Case 3: Incommensurate flow (1:sqrt(2):pi) -> Dense ergodic flow on T^2 (Orbit Closure Dim 2).
      4. Information-Loss Collision: Identical positive-octant S^2 point with constructive (I=3.0) vs destructive (I=0.0) interference.
      5. Observability Audit:
         - 3D Spatial-Vector Observability: rank(sum v_k v_k^T) = 3 reconstructs real 3D vector.
         - Coherent Qutrit Informational Completeness: requires d^2 = 9 outcomes (Hesse SIC POVM).
    """
    A_sym = (1.0 / np.sqrt(3.0), 1.0 / np.sqrt(3.0), 1.0 / np.sqrt(3.0))

    # Case 1: Identical frequency (1:1:1)
    sys_identical = ThreeModeHarmonicSystem(
        amplitudes=A_sym,
        frequencies=(1.0, 1.0, 1.0),
        phases=(0.0, 0.5, 1.0)
    )
    res_identical = analyze_harmonic_resonance(
        sys_identical,
        eval_time=2.0 * np.pi,
        regime_id="Case_1_Identical_Frequency",
        frequency_ratio_label="1:1:1"
    )

    # Case 2: Integer commensurability (1:2:3)
    sys_resonant = ThreeModeHarmonicSystem(
        amplitudes=A_sym,
        frequencies=(1.0, 2.0, 3.0),
        phases=(0.0, 0.0, 0.0)
    )
    res_resonant = analyze_harmonic_resonance(
        sys_resonant,
        eval_time=2.0 * np.pi,
        regime_id="Case_2_Integer_Commensurability",
        frequency_ratio_label="1:2:3"
    )

    # Case 3: Incommensurate flow (1:sqrt(2):pi)
    sys_incommensurate = ThreeModeHarmonicSystem(
        amplitudes=A_sym,
        frequencies=(1.0, float(np.sqrt(2)), float(np.pi)),
        phases=(0.0, 0.0, 0.0)
    )
    res_incommensurate = analyze_harmonic_resonance(
        sys_incommensurate,
        eval_time=2.0 * np.pi,
        regime_id="Case_3_Incommensurate_Flow",
        frequency_ratio_label="1:sqrt(2):pi"
    )

    # Controlled Information Loss Collision Test
    # Two states with IDENTICAL amplitude coordinates on S^2_+:
    sys_constructive = ThreeModeHarmonicSystem(
        amplitudes=A_sym,
        frequencies=(1.0, 1.0, 1.0),
        phases=(0.0, 0.0, 0.0)  # In phase -> I = (1/sqrt(3) * 3)^2 = 3.0
    )
    sys_destructive = ThreeModeHarmonicSystem(
        amplitudes=A_sym,
        frequencies=(1.0, 1.0, 1.0),
        phases=(0.0, 2.0 * np.pi / 3.0, 4.0 * np.pi / 3.0)  # 120 deg symmetry -> I = 0.0
    )

    sphere_pt_A = sys_constructive.to_sphere_coordinates()
    sphere_pt_B = sys_destructive.to_sphere_coordinates()
    sphere_coords_identical = bool(np.allclose(sphere_pt_A, sphere_pt_B))
    intensity_A = sys_constructive.resultant_intensity(0.0)
    intensity_B = sys_destructive.resultant_intensity(0.0)
    information_loss_collision_certified = bool(sphere_coords_identical and abs(intensity_A - 3.0) < 1e-10 and abs(intensity_B) < 1e-10)

    # Observability Hierarchy Test:
    # 1. 3D spatial-vector projection frame
    n_ortho = np.eye(3)
    rank_ortho = int(np.linalg.matrix_rank(n_ortho))

    # Coplanar projection frame (rank deficient for 3D real vectors)
    n_coplanar = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [1.0 / np.sqrt(2.0), 1.0 / np.sqrt(2.0), 0.0]
    ])
    rank_coplanar = int(np.linalg.matrix_rank(n_coplanar))

    # 2. Coherent qutrit state reconstruction requirements
    qutrit_hilbert_dim = 3
    qutrit_density_matrix_real_dim = qutrit_hilbert_dim**2 - 1  # 8 Gell-Mann parameters
    qutrit_sic_povm_outcomes_required = qutrit_hilbert_dim**2   # 9 Hesse SIC outcomes
    qubit_tetrahedral_outcomes = 4  # Valid for qubit (d=2), insufficient for qutrit (d=3)

    return {
        'case_1_identical': res_identical.to_dict(),
        'case_2_commensurate': res_resonant.to_dict(),
        'case_3_incommensurate': res_incommensurate.to_dict(),
        'global_geometry': {
            'exact_quotient_space': 'CP^2',
            'exact_quotient_real_dim': 4,
            'local_chart': 'S^2_+ x T^2',
            'boundary_fiber_collapse': True
        },
        'information_loss_test': {
            'sphere_point': sphere_pt_A,
            'intensity_constructive': intensity_A,
            'intensity_destructive': intensity_B,
            'sphere_coords_identical': sphere_coords_identical,
            'collision_certified': information_loss_collision_certified
        },
        'observability_test': {
            'orthogonal_rank': rank_ortho,
            'orthogonal_reconstructible': (rank_ortho == 3),
            'coplanar_rank': rank_coplanar,
            'coplanar_reconstructible': (rank_coplanar == 3),
            'rank_condition_certified': (rank_ortho == 3 and rank_coplanar == 2)
        },
        'observability_hierarchy': {
            'spatial_3d_vector': {
                'orthogonal_rank': rank_ortho,
                'orthogonal_reconstructible': (rank_ortho == 3),
                'coplanar_rank': rank_coplanar,
                'coplanar_reconstructible': (rank_coplanar == 3),
                'rank_condition_certified': (rank_ortho == 3 and rank_coplanar == 2)
            },
            'coherent_qutrit_state': {
                'hilbert_dimension': qutrit_hilbert_dim,
                'independent_real_parameters': qutrit_density_matrix_real_dim,
                'sic_outcomes_required': qutrit_sic_povm_outcomes_required,
                'qubit_tetrahedral_outcomes': qubit_tetrahedral_outcomes,
                'tetrahedral_sufficient_for_qutrit': False,
                'sic_9_sufficient_for_qutrit': True
            }
        },
        'campaign_passed': bool(
            res_identical.phase_locking_active and
            res_resonant.torus_orbit_closed and
            res_resonant.rotor_orbit_closed and
            (not res_incommensurate.torus_orbit_closed) and
            information_loss_collision_certified and
            (rank_ortho == 3 and rank_coplanar == 2)
        )
    }

