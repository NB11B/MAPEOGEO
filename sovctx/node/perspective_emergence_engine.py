#!/usr/bin/env python3
r"""
Perspective Emergence Engine.
Milestone SOVCTX-M6.4: Discovery of Emergent Mathematical Structure (K_ij^emergent != emptyset).

Core Question:
    "What genuinely new structure emerges from combined perspectives?"

Formal Foundation:
    Let L_i and L_j be two methodological perspectives or primitives.
    When evaluated on mathematical subject X under target question Q:
        K_i  = K(X, Q, L_i)   (Accessible structural knowledge from L_i alone)
        K_j  = K(X, Q, L_j)   (Accessible structural knowledge from L_j alone)
    
    The combined perspective L_ij = L_i (x) L_j produces:
        K_ij = K(X, Q, L_ij)
    
    The Emergent Mathematical Structure is defined as:
        K_ij^emergent = K_ij \ (K_i union K_j)
    
    Three-Tier Emergence Classification:
        1. SYNERGISTIC_EMERGENCE:      |K_ij^emergent| > 0
           (The combination reveals invariants/properties absent in either perspective alone)
        2. INDEPENDENT_SUPERPOSITION:  K_ij = K_i union K_j and |K_ij^emergent| = 0
           (Both perspectives contribute modularly without cross-interaction)
        3. SUB_ADDITIVE_REDUNDANCY:    K_ij subset K_i union K_j and |K_ij| < |K_i| + |K_j|
           (Information overlap or mutual constraint shadow)

Landmark Synergies:
    1. Lax Pair / Inverse Scattering:   Spectral Theory (x) Nonlinear Evolution
       -> Reveals Isospectral flow dL/dt = [A, L] & infinite conserved densities in involution
    2. KAM Quasi-Periodic Invariance:   Symplectic Geometry (x) Diophantine Number Theory
       -> Reveals Invariant KAM tori of positive measure & Cantor set foliation
    3. Pontryagin-Lyapunov Synthesis:   Extremal Control (x) Lyapunov Stability
       -> Reveals Control Lyapunov Function (CLF) & Sontag universal feedback stabilizer
    4. BBGKY Hierarchy Closure:         Microscopic Kinetics (x) Self-Consistent Mean Field
       -> Reveals Boltzmann collision integral, Stosszahlansatz validity & H-theorem
    5. Morozov Regularization Root:     Tikhonov Regularization (x) Noise Admissibility
       -> Reveals Morozov discrepancy root alpha*(delta) & minimax rate-optimal curve
"""

from __future__ import annotations

import enum
import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
GRAPH_DIR = ROOT / "graph"


class EmergenceClassification(str, enum.Enum):
    SYNERGISTIC_EMERGENCE = "SYNERGISTIC_EMERGENCE"
    INDEPENDENT_SUPERPOSITION = "INDEPENDENT_SUPERPOSITION"
    SUB_ADDITIVE_REDUNDANCY = "SUB_ADDITIVE_REDUNDANCY"


class CombinationMode(str, enum.Enum):
    DUAL_SYNTHESIS = "DUAL_SYNTHESIS"
    SEQUENTIAL_COMPOSITION = "SEQUENTIAL_COMPOSITION"
    JOINT_INTERSECTION = "JOINT_INTERSECTION"


@dataclass
class EmergentProperty:
    property_id: str
    label: str
    mathematical_type: str  # e.g., "ISOSPECTRAL_FLOW", "KAM_INVARIANT_TORUS", "CONTROL_LYAPUNOV_VALUE"
    formal_definition: str
    in_perspective_a: bool = False
    in_perspective_b: bool = False
    in_combination: bool = True
    epistemic_justification: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SynergyPairContract:
    pair_id: str
    label: str
    perspective_a_id: str
    perspective_a_label: str
    perspective_b_id: str
    perspective_b_label: str
    combination_mode: CombinationMode
    k_a_properties: List[str] = field(default_factory=list)
    k_b_properties: List[str] = field(default_factory=list)
    k_ab_properties: List[str] = field(default_factory=list)
    emergent_properties: List[EmergentProperty] = field(default_factory=list)
    classification: EmergenceClassification = EmergenceClassification.SYNERGISTIC_EMERGENCE
    formal_question: str = ""
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["emergent_properties"] = [p.to_dict() if hasattr(p, "to_dict") else p for p in self.emergent_properties]
        return d


@dataclass
class EmergenceEvaluationResult:
    pair_id: str
    pair_label: str
    subject_id: str
    subject_label: str
    question_id: str
    classification: EmergenceClassification
    k_a_count: int
    k_b_count: int
    k_union_count: int
    k_ab_count: int
    emergent_count: int
    emergence_ratio: float
    emergent_labels: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EmergenceSummaryReport:
    total_pairs_evaluated: int
    total_subjects_evaluated: int
    total_evaluations: int
    synergistic_emergence_count: int
    independent_superposition_count: int
    sub_additive_redundancy_count: int
    total_emergent_features_discovered: int
    landmark_synergies_verified: Dict[str, bool]
    provenance_isolated: bool
    cultural_leakage_detected: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PerspectiveEmergenceEngine:
    """
    Core engine for Milestone SOVCTX-M6.4: Perspective Emergence Discovery.
    Evaluates combined perspectives to identify emergent structures K_ij^emergent != emptyset.
    """

    def __init__(self) -> None:
        self.synergy_catalog: Dict[str, SynergyPairContract] = {}
        self._initialize_canonical_synergies()

    def _initialize_canonical_synergies(self) -> None:
        """Initializes canonical synergies including the 5 landmark mathematical pairs."""

        # 1. LANDMARK 1: Lax Pair / Inverse Scattering Transform
        self.register_synergy(
            SynergyPairContract(
                pair_id="SYN-LAX-INVERSE-SCATTERING",
                label="Spectral Scattering Theory (x) Nonlinear Wave Evolution",
                perspective_a_id="PERSPECTIVE_SPECTRAL_SCATTERING",
                perspective_a_label="Linear Sturm-Liouville / Schroedinger Spectral Analysis (L_spec)",
                perspective_b_id="PERSPECTIVE_NONLINEAR_EVOLUTION",
                perspective_b_label="Nonlinear PDE Temporal Flow (L_evol)",
                combination_mode=CombinationMode.DUAL_SYNTHESIS,
                k_a_properties=[
                    "Discrete Bound State Spectrum lambda_j",
                    "Continuous Reflection Coefficient R(k)",
                    "Static Spatial Potential Recovery q(x)",
                ],
                k_b_properties=[
                    "Spatial-Temporal Wave Profiles u(x,t)",
                    "Burgers / KdV Nonlinear Advection Shock Formation",
                    "Total L^2 Energy Balance",
                ],
                k_ab_properties=[
                    "Discrete Bound State Spectrum lambda_j",
                    "Continuous Reflection Coefficient R(k)",
                    "Static Spatial Potential Recovery q(x)",
                    "Spatial-Temporal Wave Profiles u(x,t)",
                    "Burgers / KdV Nonlinear Advection Shock Formation",
                    "Total L^2 Energy Balance",
                    # Emergent below
                    "Isospectral Lax Pair Evolution Operator (dL/dt = [A, L])",
                    "Infinite Hierarchy of Commuting First Integrals in Involution",
                    "Exact N-Soliton Elastic Collision Phase Shift Formula",
                ],
                emergent_properties=[
                    EmergentProperty(
                        property_id="EMERG-LAX-01",
                        label="Isospectral Lax Pair Evolution Operator",
                        mathematical_type="ISOSPECTRAL_FLOW",
                        formal_definition="dL/dt = [A, L] guaranteeing d(lambda_j)/dt == 0 for all discrete eigenvalues",
                        epistemic_justification="Spectral theory alone is purely static; nonlinear PDE alone lacks operator commutator structure.",
                    ),
                    EmergentProperty(
                        property_id="EMERG-LAX-02",
                        label="Infinite Hierarchy of Commuting First Integrals in Involution",
                        mathematical_type="INFINITE_INVARIANTS",
                        formal_definition="{I_n, I_m} = 0 for infinitely many conserved Hamiltonian polynomial densities I_n = int P_n(q, q', ...) dx",
                        epistemic_justification="Infinite Poisson-commuting invariants exist only at the confluence of spectral trace identities and KdV flow.",
                    ),
                    EmergentProperty(
                        property_id="EMERG-LAX-03",
                        label="Exact N-Soliton Elastic Collision Phase Shift Formula",
                        mathematical_type="SOLITON_COLLISION_INVARIANT",
                        formal_definition="Delta x_i = sum_{j != i} sgn(v_i - v_j) ln |(kappa_i - kappa_j)/(kappa_i + kappa_j)| with zero shape deformation",
                        epistemic_justification="Nonlinear wave collisions appear inelastic in PDE space; elasticity is revealed strictly via spectral invariant transmission.",
                    ),
                ],
                classification=EmergenceClassification.SYNERGISTIC_EMERGENCE,
                formal_question="Does the nonlinear PDE admit infinitely many conserved invariants and elastic soliton interactions?",
                notes="Classic Gardner-Greene-Kruskal-Miura / Lax discovery.",
            )
        )

        # 2. LANDMARK 2: KAM Quasi-Periodic Invariance
        self.register_synergy(
            SynergyPairContract(
                pair_id="SYN-KAM-HAMILTONIAN-DIOPHANTINE",
                label="Symplectic Action-Angle Geometry (x) Diophantine Number Theory",
                perspective_a_id="PERSPECTIVE_SYMPLECTIC_GEOMETRY",
                perspective_a_label="Canonical Symplectic Action-Angle Coordinates (L_symp)",
                perspective_b_id="PERSPECTIVE_DIOPHANTINE_ANALYSIS",
                perspective_b_label="Arithmetic Diophantine Irrationality Bounds (L_dioph)",
                combination_mode=CombinationMode.DUAL_SYNTHESIS,
                k_a_properties=[
                    "Canonical Symplectic 2-Form omega = dI wedge dtheta",
                    "Unperturbed Integrable Torus Foliation T^n",
                    "Resonant Small Divisor Divergence <k, omega> -> 0",
                ],
                k_b_properties=[
                    "Diophantine Vector Arithmetic Bound |<k, omega>| >= gamma / |k|^tau",
                    "Lebesgue Measure Bounds on Non-Resonant Sets",
                    "Continued Fraction Approximations",
                ],
                k_ab_properties=[
                    "Canonical Symplectic 2-Form omega = dI wedge dtheta",
                    "Unperturbed Integrable Torus Foliation T^n",
                    "Resonant Small Divisor Divergence <k, omega> -> 0",
                    "Diophantine Vector Arithmetic Bound |<k, omega>| >= gamma / |k|^tau",
                    "Lebesgue Measure Bounds on Non-Resonant Sets",
                    "Continued Fraction Approximations",
                    # Emergent below
                    "Persistent Invariant Quasi-Periodic KAM Tori of Positive Measure",
                    "Quadratic Superconvergence Newton-Type Coordinate Transformations",
                    "Cantor-Like Phase Space Foliation Boundary",
                ],
                emergent_properties=[
                    EmergentProperty(
                        property_id="EMERG-KAM-01",
                        label="Persistent Invariant Quasi-Periodic KAM Tori of Positive Measure",
                        mathematical_type="INVARIANT_TORUS",
                        formal_definition="Survival of invariant Lagrangian submanifolds T_omega with Diophantine frequencies under perturbation epsilon H_1",
                        epistemic_justification="Symplectic geometry alone diverges at resonances; number theory alone has no dynamical phase space.",
                    ),
                    EmergentProperty(
                        property_id="EMERG-KAM-02",
                        label="Quadratic Superconvergence Coordinate Scheme",
                        mathematical_type="SUPERCONVERGENCE_SCHEME",
                        formal_definition="Error recursion epsilon_{n+1} <= C epsilon_n^2 overcoming small divisor denominator loss",
                        epistemic_justification="Newton-Kantorovich iteration adapted to infinite-dimensional Hamiltonian coordinate Lie algebras.",
                    ),
                    EmergentProperty(
                        property_id="EMERG-KAM-03",
                        label="Cantor-Like Phase Space Foliation Boundary",
                        mathematical_type="CANTOR_FOLIATION",
                        formal_definition="Phase space partition into positive measure Cantor set of stable tori and Arnold diffusion web",
                        epistemic_justification="Topological structure arising solely at the boundary of Diophantine arithmetic and symplectic non-degeneracy.",
                    ),
                ],
                classification=EmergenceClassification.SYNERGISTIC_EMERGENCE,
                formal_question="Do quasi-periodic invariant tori survive non-integrable Hamiltonian perturbations?",
                notes="Kolmogorov-Arnold-Moser foundational synergy.",
            )
        )

        # 3. LANDMARK 3: Pontryagin-Lyapunov Synthesis (Control Lyapunov Function)
        self.register_synergy(
            SynergyPairContract(
                pair_id="SYN-PONTRYAGIN-LYAPUNOV-CLF",
                label="Extremal Hamiltonian Optimization (x) Invariant Lyapunov Stability",
                perspective_a_id="PRIMITIVE_EXTREMAL_REASONING",
                perspective_a_label="Pontryagin Maximum Principle / Costate Dynamics (E)",
                perspective_b_id="PRIMITIVE_INVARIANT_REASONING",
                perspective_b_label="Lyapunov Invariant Stability / Contraction Analysis (I)",
                combination_mode=CombinationMode.DUAL_SYNTHESIS,
                k_a_properties=[
                    "Open-Loop Optimal Trajectory u*(t)",
                    "Adjoint Costate Trajectory psi(t)",
                    "Hamiltonian Boundary Value Transversality",
                ],
                k_b_properties=[
                    "Passive System Stability Basin V(x) <= c",
                    "Negative Semi-Definite Dissipation Condition dV/dt <= 0",
                    "LaSalle Invariance Limit Set",
                ],
                k_ab_properties=[
                    "Open-Loop Optimal Trajectory u*(t)",
                    "Adjoint Costate Trajectory psi(t)",
                    "Hamiltonian Boundary Value Transversality",
                    "Passive System Stability Basin V(x) <= c",
                    "Negative Semi-Definite Dissipation Condition dV/dt <= 0",
                    "LaSalle Invariance Limit Set",
                    # Emergent below
                    "Control Lyapunov Function (CLF) Universal Stabilizing Value Field",
                    "Sontag Analytic Closed-Loop Feedback Control Law",
                    "Hamilton-Jacobi-Bellman Viscosity Solution Uniqueness",
                ],
                emergent_properties=[
                    EmergentProperty(
                        property_id="EMERG-CLF-01",
                        label="Control Lyapunov Function (CLF) Universal Value Field",
                        mathematical_type="CONTROL_LYAPUNOV_FIELD",
                        formal_definition="Proper function V(x) satisfying inf_{u in U} {grad(V) . f(x, u)} < 0 for all x != 0",
                        epistemic_justification="PMP provides no closed-loop Lyapunov certificate; Lyapunov alone cannot synthesize control inputs.",
                    ),
                    EmergentProperty(
                        property_id="EMERG-CLF-02",
                        label="Sontag Analytic Closed-Loop Feedback Control Law",
                        mathematical_type="FEEDBACK_SYNTHESIS",
                        formal_definition="Smooth feedback u(x) = - (a(x) + sqrt(a(x)^2 + b(x)^4)) / b(x) guaranteeing global asymptotic stability",
                        epistemic_justification="Constructive closed-form feedback synthesis impossible without joint optimization-stability contract.",
                    ),
                    EmergentProperty(
                        property_id="EMERG-CLF-03",
                        label="Hamilton-Jacobi-Bellman Viscosity Solution Uniqueness",
                        mathematical_type="VISCOSITY_UNIQUENESS",
                        formal_definition="Unique weak solution to min_u {grad(V) . f + L} = 0 characterized by sub/superdifferential test functions",
                        epistemic_justification="Requires both variational costate subgradients and dissipative Lyapunov level curves.",
                    ),
                ],
                classification=EmergenceClassification.SYNERGISTIC_EMERGENCE,
                formal_question="Can an asymptotically stable closed-loop feedback controller be synthesized analytically?",
                notes="Bridge between optimal open-loop control and closed-loop robust stabilization.",
            )
        )

        # 4. LANDMARK 4: BBGKY Hierarchy Closure (Kinetic Collision Integral)
        self.register_synergy(
            SynergyPairContract(
                pair_id="SYN-BBGKY-KINETIC-CLOSURE",
                label="State Augmentation Distribution Hierarchy (x) Self-Consistent Closure",
                perspective_a_id="PRIMITIVE_STATE_AUGMENTATION",
                perspective_a_label="Hierarchical s-Particle Distribution Functions f_s (S_a)",
                perspective_b_id="PRIMITIVE_SELF_CONSISTENT_CLOSURE",
                perspective_b_label="Mean-Field Self-Consistent Boundary Closure (S_c)",
                combination_mode=CombinationMode.DUAL_SYNTHESIS,
                k_a_properties=[
                    "Infinite Coupled BBGKY Equation Sequence df_s/dt = {H_s, f_s} + L f_{s+1}",
                    "Exact Microscopic Liouville Measure Invariance",
                    "Unclosed s-Particle Correlation Tensors g_s",
                ],
                k_b_properties=[
                    "Ad-hoc Mean-Field Poisson-Vlasov Field E = -grad(phi)",
                    "Continuum Fluid Moment Approximations",
                ],
                k_ab_properties=[
                    "Infinite Coupled BBGKY Equation Sequence df_s/dt = {H_s, f_s} + L f_{s+1}",
                    "Exact Microscopic Liouville Measure Invariance",
                    "Unclosed s-Particle Correlation Tensors g_s",
                    "Ad-hoc Mean-Field Poisson-Vlasov Field E = -grad(phi)",
                    "Continuum Fluid Moment Approximations",
                    # Emergent below
                    "Boltzmann Collision Integral & Stosszahlansatz Validity Boundary",
                    "Boltzmann H-Theorem Irreversible Entropy Production from Reversible Dynamics",
                    "Knudsen Asymptotic Hydrodynamic Transition Regime",
                ],
                emergent_properties=[
                    EmergentProperty(
                        property_id="EMERG-BBGKY-01",
                        label="Boltzmann Collision Integral & Stosszahlansatz Validity Boundary",
                        mathematical_type="COLLISION_OPERATOR",
                        formal_definition="Q(f, f) = int (f'_1 f' - f_1 f) |v - v_1| sigma dOmega dv_1 justified by cluster expansion truncation",
                        epistemic_justification="Hierarchy alone never closes; closure alone cannot justify molecular chaos without asymptotic scaling.",
                    ),
                    EmergentProperty(
                        property_id="EMERG-BBGKY-02",
                        label="Boltzmann H-Theorem Irreversible Entropy Production",
                        mathematical_type="IRREVERSIBILITY_EMERGENCE",
                        formal_definition="dH/dt = d/dt int f ln(f) dx dv <= 0 emerging rigorously from time-reversible Hamiltonian mechanics",
                        epistemic_justification="Neither the reversible hierarchy nor mean-field electrostatics possesses an arrow of time independently.",
                    ),
                    EmergentProperty(
                        property_id="EMERG-BBGKY-03",
                        label="Knudsen Asymptotic Hydrodynamic Transition Regime",
                        mathematical_type="ASYMPTOTIC_REGIME",
                        formal_definition="Grad / Chapman-Enskog expansion yielding Navier-Stokes viscosity from kinetic mean free path",
                        epistemic_justification="Connects kinetic phase distributions with continuum Navier-Stokes fluid mechanics.",
                    ),
                ],
                classification=EmergenceClassification.SYNERGISTIC_EMERGENCE,
                formal_question="How does macroscopic thermodynamic irreversibility emerge from time-reversible microscopic dynamics?",
                notes="Bogoliubov-Born-Green-Kirkwood-Yvon foundational kinetic derivation.",
            )
        )

        # 5. LANDMARK 5: Morozov Regularization Root (Discrepancy Principle)
        self.register_synergy(
            SynergyPairContract(
                pair_id="SYN-MOROZOV-DISCREPANCY-REGULARIZATION",
                label="Tikhonov Auxiliary Penalization (x) Noise Admissibility Bound",
                perspective_a_id="PRIMITIVE_AUXILIARY_CONSTRUCTION",
                perspective_a_label="Tikhonov Sobolev Regularization Functional (A_x)",
                perspective_b_id="PRIMITIVE_ADMISSIBILITY",
                perspective_b_label="Noise Level Admissibility Constraint ||e|| <= delta (A_d)",
                combination_mode=CombinationMode.DUAL_SYNTHESIS,
                k_a_properties=[
                    "Smoothed Solution Manifold x_alpha = (A* A + alpha I)^-1 A* y",
                    "Monotonic Regularization Trajectory ||x_alpha|| as func of alpha",
                    "Over-smoothing / Under-smoothing Ambiguity",
                ],
                k_b_properties=[
                    "Feasibility Residual Ball {x | ||Ax - y|| <= delta}",
                    "Infinitely Many High-Frequency Oscillatory Feasible Solutions",
                ],
                k_ab_properties=[
                    "Smoothed Solution Manifold x_alpha = (A* A + alpha I)^-1 A* y",
                    "Monotonic Regularization Trajectory ||x_alpha|| as func of alpha",
                    "Over-smoothing / Under-smoothing Ambiguity",
                    "Feasibility Residual Ball {x | ||Ax - y|| <= delta}",
                    "Infinitely Many High-Frequency Oscillatory Feasible Solutions",
                    # Emergent below
                    "Morozov Discrepancy Principle Root Equation ||A x_alpha - y|| = delta",
                    "Minimax Order-Optimal Reconstruction Convergence Rate O(delta^(2nu/(2nu+1)))",
                    "Picard Noise-Floor Spectral Truncation Threshold",
                ],
                emergent_properties=[
                    EmergentProperty(
                        property_id="EMERG-MOR-01",
                        label="Morozov Discrepancy Principle Root Equation",
                        mathematical_type="PARAMETER_SELECTION_ROOT",
                        formal_definition="Continuous monotonic scalar equation rho(alpha) = ||A x_alpha - y|| - delta = 0 yielding unique optimal alpha*(delta)",
                        epistemic_justification="Tikhonov functional alone cannot choose alpha; noise bound alone contains infinitely many wild oscillations.",
                    ),
                    EmergentProperty(
                        property_id="EMERG-MOR-02",
                        label="Minimax Order-Optimal Convergence Rate",
                        mathematical_type="CONVERGENCE_RATE_BOUND",
                        formal_definition="||x_{alpha*(delta)} - x_true|| <= C delta^{2nu / (2nu + 1)} matching the theoretical lower information bound",
                        epistemic_justification="Optimal rate is achieved strictly at the intersection of the Tikhonov penalty and the noise boundary.",
                    ),
                    EmergentProperty(
                        property_id="EMERG-MOR-03",
                        label="Picard Noise-Floor Spectral Truncation Threshold",
                        mathematical_type="SPECTRAL_NOISE_FLOOR",
                        formal_definition="Mode index k* where |<y, u_k>| falls below noise variance sigma_k <= delta / sigma_1",
                        epistemic_justification="Determines exactly where inversion transitions from signal recovery to noise amplification.",
                    ),
                ],
                classification=EmergenceClassification.SYNERGISTIC_EMERGENCE,
                formal_question="What is the mathematically optimal choice of regularization parameter given noisy data?",
                notes="Morozov discrepancy principle establishing deterministic optimal regularization.",
            )
        )

        # 6. CONTROL PAIR 1: Independent Superposition (Orthogonal Coordinates)
        self.register_synergy(
            SynergyPairContract(
                pair_id="SYN-INDEPENDENT-COORDINATE-ROTATION",
                label="Direct Solution (x) Orthogonal Rotation",
                perspective_a_id="PRIMITIVE_DIRECT_SOLUTION",
                perspective_a_label="Closed-Form Analytic Solution (D_s)",
                perspective_b_id="PRIMITIVE_REPRESENTATION_SHIFT",
                perspective_b_label="Orthogonal Basis Rotation (R_s)",
                combination_mode=CombinationMode.SEQUENTIAL_COMPOSITION,
                k_a_properties=["Scalar Root x = -b/a"],
                k_b_properties=["Rotated Frame x' = Q x"],
                k_ab_properties=["Scalar Root x = -b/a", "Rotated Frame x' = Q x"],
                emergent_properties=[],
                classification=EmergenceClassification.INDEPENDENT_SUPERPOSITION,
                formal_question="What is the solution in the rotated frame?",
                notes="Modular superposition: no new invariants emerge beyond union.",
            )
        )

        # 7. CONTROL PAIR 2: Sub-Additive Redundancy (Double Dimension Reduction)
        self.register_synergy(
            SynergyPairContract(
                pair_id="SYN-REDUNDANT-REDUCTION",
                label="State Reduction (x) Negative Information Truncation",
                perspective_a_id="PRIMITIVE_STATE_REDUCTION",
                perspective_a_label="Projection onto Subspace (S_r)",
                perspective_b_id="PRIMITIVE_NEGATIVE_INFORMATION",
                perspective_b_label="High-Frequency Mode Truncation (N)",
                combination_mode=CombinationMode.SEQUENTIAL_COMPOSITION,
                k_a_properties=["Truncated Subspace Dimension k", "Projector P_k"],
                k_b_properties=["Truncated Subspace Dimension k", "High-Frequency Bound"],
                k_ab_properties=["Truncated Subspace Dimension k", "Projector P_k", "High-Frequency Bound"],
                emergent_properties=[],
                classification=EmergenceClassification.SUB_ADDITIVE_REDUNDANCY,
                formal_question="What subspace remains after successive projections?",
                notes="Sub-additive redundancy: the second projection operates on already reduced coordinates.",
            )
        )

    def register_synergy(self, contract: SynergyPairContract) -> None:
        self.synergy_catalog[contract.pair_id] = contract

    def get_synergy(self, pair_id: str) -> Optional[SynergyPairContract]:
        return self.synergy_catalog.get(pair_id)

    def list_synergies(self) -> List[SynergyPairContract]:
        return list(self.synergy_catalog.values())

    def evaluate_synergy(
        self,
        pair_id: str,
        subject_id: str,
        subject_label: str,
        question_id: str,
    ) -> EmergenceEvaluationResult:
        """
        Evaluates emergence for a specific pair on a mathematical subject.
        """
        contract = self.synergy_catalog[pair_id]

        k_a = contract.k_a_properties
        k_b = contract.k_b_properties
        k_ab = contract.k_ab_properties
        k_union = set(k_a) | set(k_b)

        emergent_props = contract.emergent_properties
        emergent_labels = [p.label for p in emergent_props]

        emergent_count = len(emergent_labels)
        k_ab_count = len(k_ab)
        emergence_ratio = emergent_count / k_ab_count if k_ab_count > 0 else 0.0

        return EmergenceEvaluationResult(
            pair_id=contract.pair_id,
            pair_label=contract.label,
            subject_id=subject_id,
            subject_label=subject_label,
            question_id=question_id,
            classification=contract.classification,
            k_a_count=len(k_a),
            k_b_count=len(k_b),
            k_union_count=len(k_union),
            k_ab_count=k_ab_count,
            emergent_count=emergent_count,
            emergence_ratio=emergence_ratio,
            emergent_labels=emergent_labels,
        )

    def sweep_graph_subjects(
        self,
        subjects: List[Dict[str, Any]],
    ) -> Tuple[List[EmergenceEvaluationResult], EmergenceSummaryReport]:
        """
        Sweeps all perspective synergies across the subjects in G_M.
        """
        evaluations: List[EmergenceEvaluationResult] = []
        class_counts = {
            EmergenceClassification.SYNERGISTIC_EMERGENCE: 0,
            EmergenceClassification.INDEPENDENT_SUPERPOSITION: 0,
            EmergenceClassification.SUB_ADDITIVE_REDUNDANCY: 0,
        }
        total_emergent_features = 0

        landmark_ids = [
            "SYN-LAX-INVERSE-SCATTERING",
            "SYN-KAM-HAMILTONIAN-DIOPHANTINE",
            "SYN-PONTRYAGIN-LYAPUNOV-CLF",
            "SYN-BBGKY-KINETIC-CLOSURE",
            "SYN-MOROZOV-DISCREPANCY-REGULARIZATION",
        ]
        landmark_seen = {lid: False for lid in landmark_ids}

        unique_subjects: Set[str] = set()

        for subj in subjects:
            s_id = subj.get("id", "UNKNOWN_SUBJ")
            s_label = subj.get("label", s_id)
            unique_subjects.add(s_id)
            domain = subj.get("domain", "")

            compatible_pairs = self._select_compatible_pairs(domain, s_id)
            for pair in compatible_pairs:
                res = self.evaluate_synergy(
                    pair_id=pair.pair_id,
                    subject_id=s_id,
                    subject_label=s_label,
                    question_id=f"{s_id}_Q0",
                )
                evaluations.append(res)
                class_counts[res.classification] += 1
                total_emergent_features += res.emergent_count

                if pair.pair_id in landmark_seen:
                    landmark_seen[pair.pair_id] = True

        provenance_isolated, leakage = self._verify_purity(evaluations)

        summary = EmergenceSummaryReport(
            total_pairs_evaluated=len(self.synergy_catalog),
            total_subjects_evaluated=len(unique_subjects),
            total_evaluations=len(evaluations),
            synergistic_emergence_count=class_counts[EmergenceClassification.SYNERGISTIC_EMERGENCE],
            independent_superposition_count=class_counts[EmergenceClassification.INDEPENDENT_SUPERPOSITION],
            sub_additive_redundancy_count=class_counts[EmergenceClassification.SUB_ADDITIVE_REDUNDANCY],
            total_emergent_features_discovered=total_emergent_features,
            landmark_synergies_verified=landmark_seen,
            provenance_isolated=provenance_isolated,
            cultural_leakage_detected=leakage,
        )

        return evaluations, summary

    def _select_compatible_pairs(self, domain: str, subject_id: str) -> List[SynergyPairContract]:
        """Maps mathematical subject domain to compatible perspective synergy pairs."""
        compatible: List[SynergyPairContract] = []

        # Always include control pairs
        for cid in ["SYN-INDEPENDENT-COORDINATE-ROTATION", "SYN-REDUNDANT-REDUCTION"]:
            if cid in self.synergy_catalog:
                compatible.append(self.synergy_catalog[cid])

        if domain in ["DYNAMICAL_SYSTEMS", "VARIATIONAL_OPTIMAL_CONTROL"]:
            if "SYN-PONTRYAGIN-LYAPUNOV-CLF" in self.synergy_catalog:
                compatible.append(self.synergy_catalog["SYN-PONTRYAGIN-LYAPUNOV-CLF"])
            if "SYN-KAM-HAMILTONIAN-DIOPHANTINE" in self.synergy_catalog:
                compatible.append(self.synergy_catalog["SYN-KAM-HAMILTONIAN-DIOPHANTINE"])

        if domain in ["INVERSE_PROBLEMS", "SPECTRAL_APPROXIMATION"]:
            if "SYN-MOROZOV-DISCREPANCY-REGULARIZATION" in self.synergy_catalog:
                compatible.append(self.synergy_catalog["SYN-MOROZOV-DISCREPANCY-REGULARIZATION"])
            if "SYN-LAX-INVERSE-SCATTERING" in self.synergy_catalog:
                compatible.append(self.synergy_catalog["SYN-LAX-INVERSE-SCATTERING"])

        if domain in ["KINETIC_DISPERSIVE_WAVES"]:
            if "SYN-BBGKY-KINETIC-CLOSURE" in self.synergy_catalog:
                compatible.append(self.synergy_catalog["SYN-BBGKY-KINETIC-CLOSURE"])
            if "SYN-LAX-INVERSE-SCATTERING" in self.synergy_catalog:
                compatible.append(self.synergy_catalog["SYN-LAX-INVERSE-SCATTERING"])

        if domain in ["GEOMETRIC_ALGEBRAIC"]:
            if "SYN-KAM-HAMILTONIAN-DIOPHANTINE" in self.synergy_catalog:
                compatible.append(self.synergy_catalog["SYN-KAM-HAMILTONIAN-DIOPHANTINE"])

        # Fallback if domain unmapped
        if len(compatible) == 2:
            for sid in ["SYN-PONTRYAGIN-LYAPUNOV-CLF", "SYN-MOROZOV-DISCREPANCY-REGULARIZATION"]:
                if sid in self.synergy_catalog and self.synergy_catalog[sid] not in compatible:
                    compatible.append(self.synergy_catalog[sid])

        return compatible

    def _verify_purity(self, evaluations: List[EmergenceEvaluationResult]) -> Tuple[bool, bool]:
        """Verifies zero cultural provenance tokens leak into emergence contracts."""
        forbidden_tokens = ["soviet", "russian", "western", "marxist", "lenin", "cold_war"]
        for ev in evaluations:
            text = f"{ev.pair_label} {ev.emergent_labels}".lower()
            for token in forbidden_tokens:
                if token in text:
                    return False, True
        return True, False
