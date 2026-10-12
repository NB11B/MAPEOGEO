#!/usr/bin/env python3
r"""
Representation-Shift Discovery Engine.
Milestone SOVCTX-M6.3: Discovery of Revealed and Concealed Mathematical Structure.

Core Question:
    "Which representation changes reveal structure that is absent before the change?"

Formal Foundation:
    Let a mathematical object X be represented in representation space R_A.
    Under a representation shift tau: R_A -> R_B:
        X_B = tau(X_A)
    The structural properties accessible in R are S(R).
    
    The engine computes:
        Delta S^+(tau) = S(R_B) \ S(R_A)   (Revealed / Newly Observable Structure)
        Delta S^-(tau) = S(R_A) \ S(R_B)   (Concealed / Omitted Structure)
        S^cap(tau)    = S(R_A) cap S(R_B)  (Preserved Invariant Structure)
    
    Four-Tier Epistemic Classification:
        1. STRUCTURE_REVEALING:   Delta S^+ != emptyset, target question Q becomes decidable/tractable
        2. ISOMORPHIC_TRANSLATION: Delta S^+ = emptyset, Delta S^- = emptyset (bijective isometry)
        3. ABSTRACTION_COLLAPSE:  Delta S^+ = emptyset, Delta S^- != emptyset (information loss, no gain)
        4. COMPLEMENTARY_DUALITY: Delta S^+ != emptyset, Delta S^- != emptyset (canonical conjugate trade-off)

Focus Landmarks:
    - x -> V(x):          State trajectory to Lyapunov scalar potential
    - x -> (x, psi):      Primal state to Pontryagin cotangent phase space
    - S(lambda) -> K(x,y): Scattering spectral data to Marchenko integral kernel
    - particles -> f(x,v,t): Discrete N-particle ensemble to Vlasov kinetic continuum
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


class RepresentationCategory(str, enum.Enum):
    STATE_TRAJECTORY = "STATE_TRAJECTORY"
    SCALAR_POTENTIAL = "SCALAR_POTENTIAL"
    COTANGENT_PHASE_SPACE = "COTANGENT_PHASE_SPACE"
    SCATTERING_SPECTRAL_DATA = "SCATTERING_SPECTRAL_DATA"
    INTEGRAL_KERNEL = "INTEGRAL_KERNEL"
    PARTICLE_ENSEMBLE = "PARTICLE_ENSEMBLE"
    KINETIC_DISTRIBUTION = "KINETIC_DISTRIBUTION"
    TIME_DOMAIN_SIGNAL = "TIME_DOMAIN_SIGNAL"
    GRASSMANNIAN_SUBSPACE = "GRASSMANNIAN_SUBSPACE"
    AMBIENT_MANIFOLD = "AMBIENT_MANIFOLD"
    CASIMIR_QUOTIENT = "CASIMIR_QUOTIENT"
    SPATIAL_FIELD = "SPATIAL_FIELD"
    FOURIER_HARMONICS = "FOURIER_HARMONICS"
    OPERATOR_MATRIX = "OPERATOR_MATRIX"
    SINGULAR_SPECTRUM = "SINGULAR_SPECTRUM"
    DISCRETIZED_COARSE_GRID = "DISCRETIZED_COARSE_GRID"


class ShiftClassification(str, enum.Enum):
    STRUCTURE_REVEALING = "STRUCTURE_REVEALING"
    ISOMORPHIC_TRANSLATION = "ISOMORPHIC_TRANSLATION"
    ABSTRACTION_COLLAPSE = "ABSTRACTION_COLLAPSE"
    COMPLEMENTARY_DUALITY = "COMPLEMENTARY_DUALITY"


class DecidabilityStatus(str, enum.Enum):
    INTRACTABLE_TO_DECIDABLE = "INTRACTABLE_TO_DECIDABLE"
    ILL_CONDITIONED_TO_WELL_CONDITIONED = "ILL_CONDITIONED_TO_WELL_CONDITIONED"
    EQUIVALENT_DECIDABILITY = "EQUIVALENT_DECIDABILITY"
    DECIDABLE_TO_UNDECIDABLE = "DECIDABLE_TO_UNDECIDABLE"


@dataclass
class StructuralProperty:
    property_id: str
    label: str
    mathematical_type: str  # e.g., "CONSERVATION_LAW", "BOUNDARY_CURVATURE", "OPERATOR_SPECTRUM"
    formal_definition: str
    observability_in_source: str  # "OBSERVABLE", "LATENT_CONCEALED", "INACCESSIBLE"
    observability_in_target: str  # "OBSERVABLE", "LATENT_CONCEALED", "INACCESSIBLE"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RepresentationShiftContract:
    shift_id: str
    label: str
    source_rep: RepresentationCategory
    target_rep: RepresentationCategory
    transformation_morphism: str
    is_invertible: bool
    revealed_structure: List[StructuralProperty] = field(default_factory=list)
    concealed_structure: List[StructuralProperty] = field(default_factory=list)
    preserved_invariants: List[str] = field(default_factory=list)
    target_questions: List[str] = field(default_factory=list)
    decidability_transition: DecidabilityStatus = DecidabilityStatus.EQUIVALENT_DECIDABILITY
    classification: ShiftClassification = ShiftClassification.STRUCTURE_REVEALING
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["revealed_structure"] = [p.to_dict() if hasattr(p, "to_dict") else p for p in self.revealed_structure]
        d["concealed_structure"] = [p.to_dict() if hasattr(p, "to_dict") else p for p in self.concealed_structure]
        return d


@dataclass
class ShiftEvaluationResult:
    subject_id: str
    subject_label: str
    question_id: str
    question_label: str
    shift_id: str
    shift_label: str
    classification: ShiftClassification
    decidability_transition: DecidabilityStatus
    revealed_feature_count: int
    concealed_feature_count: int
    preserved_invariant_count: int
    revealed_labels: List[str]
    concealed_labels: List[str]
    preserved_labels: List[str]
    is_falsified: bool = False
    falsification_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ShiftSummaryReport:
    total_shifts_evaluated: int
    total_subjects_evaluated: int
    total_questions_evaluated: int
    total_evaluations: int
    structure_revealing_count: int
    isomorphic_translation_count: int
    abstraction_collapse_count: int
    complementary_duality_count: int
    revealed_features_total: int
    concealed_features_total: int
    preserved_invariants_total: int
    landmark_coverage: Dict[str, bool]
    provenance_isolated: bool
    cultural_leakage_detected: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RepresentationShiftEngine:
    """
    Core engine for Milestone SOVCTX-M6.3: Representation-Shift Discovery.
    Evaluates canonical and synthetic representation shifts across the mathematical plane G_M.
    """

    def __init__(self) -> None:
        self.shift_catalog: Dict[str, RepresentationShiftContract] = {}
        self._initialize_canonical_shifts()

    def _initialize_canonical_shifts(self) -> None:
        """Initializes canonical representation shifts, including the 4 landmark transforms."""

        # 1. LANDMARK 1: State Trajectory to Scalar Potential (x -> V(x))
        self.register_shift(
            RepresentationShiftContract(
                shift_id="SHIFT-LYAPUNOV-POTENTIAL",
                label="State Trajectory to Scalar Potential (x -> V(x))",
                source_rep=RepresentationCategory.STATE_TRAJECTORY,
                target_rep=RepresentationCategory.SCALAR_POTENTIAL,
                transformation_morphism="x(t) in R^n |-> V(x) in R, with V(x) > 0 and dV/dt = grad(V) . f(x) <= 0",
                is_invertible=False,
                revealed_structure=[
                    StructuralProperty(
                        property_id="LYAP-PROP-01",
                        label="Global Basin of Attraction Boundary",
                        mathematical_type="BOUNDARY_GEOMETRY",
                        formal_definition="Level set {x in R^n | V(x) <= c} defining exact region of asymptotic stability",
                        observability_in_source="LATENT_CONCEALED",
                        observability_in_target="OBSERVABLE",
                    ),
                    StructuralProperty(
                        property_id="LYAP-PROP-02",
                        label="Uniform Contraction Metric & Decay Rate",
                        mathematical_type="METRIC_TENSOR",
                        formal_definition="Positive definite metric alpha such that dV/dt <= -alpha V, proving exponential convergence",
                        observability_in_source="INACCESSIBLE",
                        observability_in_target="OBSERVABLE",
                    ),
                    StructuralProperty(
                        property_id="LYAP-PROP-03",
                        label="LaSalle Invariant Limit Set Topology",
                        mathematical_type="TOPOLOGICAL_MANIFOLD",
                        formal_definition="Maximal invariant set M subset {x | dV/dt = 0}",
                        observability_in_source="LATENT_CONCEALED",
                        observability_in_target="OBSERVABLE",
                    ),
                ],
                concealed_structure=[
                    StructuralProperty(
                        property_id="LYAP-CONC-01",
                        label="Exact Pointwise Trajectory Coordinates",
                        mathematical_type="TEMPORAL_SERIES",
                        formal_definition="Specific coordinate evolution x_i(t) for individual degrees of freedom at time t",
                        observability_in_source="OBSERVABLE",
                        observability_in_target="INACCESSIBLE",
                    ),
                    StructuralProperty(
                        property_id="LYAP-CONC-02",
                        label="Transient Oscillatory Phase Angle",
                        mathematical_type="PHASE_ANGLE",
                        formal_definition="Instantaneous phase theta(t) of orbital rotations inside the stable basin",
                        observability_in_source="OBSERVABLE",
                        observability_in_target="LATENT_CONCEALED",
                    ),
                ],
                preserved_invariants=[
                    "Equilibrium Fixed Point Location (x* = 0)",
                    "Asymptotic Stability Class (Stable / Asymptotically Stable)",
                    "Topological Dimension of Underlying State Space",
                ],
                target_questions=[
                    "Is the dynamical system asymptotically stable around the origin?",
                    "What is the maximal invariant basin of attraction?",
                ],
                decidability_transition=DecidabilityStatus.INTRACTABLE_TO_DECIDABLE,
                classification=ShiftClassification.STRUCTURE_REVEALING,
                notes="Replaces infinite-horizon numerical trajectory integration with algebraic inequality verification.",
            )
        )

        # 2. LANDMARK 2: Primal State to Pontryagin Cotangent Phase Space (x -> (x, psi))
        self.register_shift(
            RepresentationShiftContract(
                shift_id="SHIFT-PONTRYAGIN-COSTATE",
                label="Primal State to Cotangent Phase Space (x -> (x, psi))",
                source_rep=RepresentationCategory.STATE_TRAJECTORY,
                target_rep=RepresentationCategory.COTANGENT_PHASE_SPACE,
                transformation_morphism="x(t) |-> (x(t), psi(t)) in T*M, via Hamiltonian H(x, psi, u) = psi . f(x, u) - L(x, u)",
                is_invertible=True,  # Canonical projection pi: T*M -> M recovers primal state
                revealed_structure=[
                    StructuralProperty(
                        property_id="PONT-PROP-01",
                        label="Hamiltonian Conservation First Integral",
                        mathematical_type="CONSERVATION_LAW",
                        formal_definition="Total Hamiltonian H(x(t), psi(t), u*(t)) == const along optimal trajectories",
                        observability_in_source="INACCESSIBLE",
                        observability_in_target="OBSERVABLE",
                    ),
                    StructuralProperty(
                        property_id="PONT-PROP-02",
                        label="Pointwise Extremal Control Characterization",
                        mathematical_type="OPTIMAL_ACTION",
                        formal_definition="Optimal control u*(t) = argmax_{u in U} H(x(t), psi(t), u) pointwise in time",
                        observability_in_source="LATENT_CONCEALED",
                        observability_in_target="OBSERVABLE",
                    ),
                    StructuralProperty(
                        property_id="PONT-PROP-03",
                        label="Symplectic Structure & Shadow Value Gradient",
                        mathematical_type="SYMPLECTIC_FORM",
                        formal_definition="Canonical 2-form omega = dpsi wedge dx, where psi(t) = grad_x J*(x, t)",
                        observability_in_source="INACCESSIBLE",
                        observability_in_target="OBSERVABLE",
                    ),
                ],
                concealed_structure=[],  # State augmentation retains all primal state information
                preserved_invariants=[
                    "Primal Equations of Motion (dx/dt = dH/dpsi)",
                    "Optimal Value Functional Infimum (J*)",
                    "Boundary Admissibility Constraints",
                ],
                target_questions=[
                    "What control policy minimizes the cost functional subject to constraints?",
                    "Are there conserved quantities along the optimal path?",
                ],
                decidability_transition=DecidabilityStatus.INTRACTABLE_TO_DECIDABLE,
                classification=ShiftClassification.STRUCTURE_REVEALING,
                notes="Converts non-local variational functional optimization into local pointwise Hamiltonian maximization.",
            )
        )

        # 3. LANDMARK 3: Scattering Spectral Data to Marchenko Integral Kernel (S(lambda) -> K(x,y))
        self.register_shift(
            RepresentationShiftContract(
                shift_id="SHIFT-MARCHENKO-KERNEL",
                label="Scattering Data to Integral Kernel (S(lambda) -> K(x,y))",
                source_rep=RepresentationCategory.SCATTERING_SPECTRAL_DATA,
                target_rep=RepresentationCategory.INTEGRAL_KERNEL,
                transformation_morphism="{R(k), lambda_j, c_j} |-> K(x,y) via K(x,y) + F(x+y) + int_x^infty K(x,z)F(z+y)dz = 0",
                is_invertible=True,
                revealed_structure=[
                    StructuralProperty(
                        property_id="MARC-PROP-01",
                        label="Direct Spatial Potential Profile",
                        mathematical_type="POTENTIAL_FIELD",
                        formal_definition="Exact coordinate potential q(x) = -2 d/dx K(x,x) along the kernel diagonal",
                        observability_in_source="LATENT_CONCEALED",
                        observability_in_target="OBSERVABLE",
                    ),
                    StructuralProperty(
                        property_id="MARC-PROP-02",
                        label="Soliton Multi-Bound State Geometry",
                        mathematical_type="SPATIAL_LOCALIZATION",
                        formal_definition="Spatial envelope, center-of-mass, and asymptotic velocity of discrete soliton waves",
                        observability_in_source="LATENT_CONCEALED",
                        observability_in_target="OBSERVABLE",
                    ),
                    StructuralProperty(
                        property_id="MARC-PROP-03",
                        label="Volterra Operator Triangular Factorization",
                        mathematical_type="OPERATOR_FACTORIZATION",
                        formal_definition="Causal triangular factorization (I + K) satisfying causal Volterra integral identity",
                        observability_in_source="INACCESSIBLE",
                        observability_in_target="OBSERVABLE",
                    ),
                ],
                concealed_structure=[
                    StructuralProperty(
                        property_id="MARC-CONC-01",
                        label="Far-Field Scattering Phase Shifts",
                        mathematical_type="PHASE_SPECTRUM",
                        formal_definition="Explicit asymptotic phase shifts delta(k) for high-frequency continuum modes",
                        observability_in_source="OBSERVABLE",
                        observability_in_target="LATENT_CONCEALED",
                    ),
                ],
                preserved_invariants=[
                    "Bound State Discrete Eigenvalues (lambda_j)",
                    "KdV / NLS Conserved Hamiltonian Densities (int q^n dx)",
                    "Transmission Coefficient Analyticity in Upper Half-Plane",
                ],
                target_questions=[
                    "What is the unknown spatial potential q(x) that produced the scattering data?",
                    "How many stable soliton solutions are bound in the field?",
                ],
                decidability_transition=DecidabilityStatus.ILL_CONDITIONED_TO_WELL_CONDITIONED,
                classification=ShiftClassification.STRUCTURE_REVEALING,
                notes="Transforms severe nonlinear inverse problem into linear Volterra integral equation.",
            )
        )

        # 4. LANDMARK 4: Discrete Particle Ensemble to Kinetic Phase Space (particles -> f(x,v,t))
        self.register_shift(
            RepresentationShiftContract(
                shift_id="SHIFT-VLASOV-KINETIC",
                label="Particle Ensemble to Kinetic Continuum (particles -> f(x,v,t))",
                source_rep=RepresentationCategory.PARTICLE_ENSEMBLE,
                target_rep=RepresentationCategory.KINETIC_DISTRIBUTION,
                transformation_morphism="{x_i, v_i}_{i=1}^N |-> f(x, v, t) = lim_{N -> infty} 1/N sum_{i=1}^N delta(x - x_i) delta(v - v_i)",
                is_invertible=False,
                revealed_structure=[
                    StructuralProperty(
                        property_id="VLAS-PROP-01",
                        label="Collisionless Landau Damping Resonances",
                        mathematical_type="COMPLEX_POLE",
                        formal_definition="Analytic continuation poles in complex velocity plane Res(omega/k) explaining wave attenuation without entropy creation",
                        observability_in_source="INACCESSIBLE",
                        observability_in_target="OBSERVABLE",
                    ),
                    StructuralProperty(
                        property_id="VLAS-PROP-02",
                        label="Collective Plasma Dispersion Relation",
                        mathematical_type="DISPERSION_RELATION",
                        formal_definition="Dielectric permittivity epsilon(k, omega) = 1 - (omega_p^2 / k^2) int (df_0/dv)/(v - omega/k) dv = 0",
                        observability_in_source="LATENT_CONCEALED",
                        observability_in_target="OBSERVABLE",
                    ),
                    StructuralProperty(
                        property_id="VLAS-PROP-03",
                        label="Phase-Space Filamentation Geometry",
                        mathematical_type="PHASE_MIXING",
                        formal_definition="Vortex roll-up and fine-scale filaments in (x,v) phase space preserving Casimir invariants",
                        observability_in_source="INACCESSIBLE",
                        observability_in_target="OBSERVABLE",
                    ),
                ],
                concealed_structure=[
                    StructuralProperty(
                        property_id="VLAS-CONC-01",
                        label="Microscopic Inter-Particle Trajectories",
                        mathematical_type="MICROSCOPIC_COORDINATES",
                        formal_definition="Individual trajectory coordinates (x_i(t), v_i(t)) for each particle index i",
                        observability_in_source="OBSERVABLE",
                        observability_in_target="INACCESSIBLE",
                    ),
                    StructuralProperty(
                        property_id="VLAS-CONC-02",
                        label="Sub-Debye Scale Thermal Fluctuations",
                        mathematical_type="CORRELATION_FUNCTION",
                        formal_definition="Two-particle microscopic correlation functions g(x_1, x_2) below Debye length lambda_D",
                        observability_in_source="OBSERVABLE",
                        observability_in_target="INACCESSIBLE",
                    ),
                ],
                preserved_invariants=[
                    "Total System Mass / Charge Conservation",
                    "Total Mechanical + Field Energy Conservation",
                    "Vlasov Casimir Functionals (int G(f) dx dv == const)",
                ],
                target_questions=[
                    "Does a plasma oscillation damp out in the absence of particle collisions?",
                    "What are the collective oscillation frequencies of the plasma?",
                ],
                decidability_transition=DecidabilityStatus.INTRACTABLE_TO_DECIDABLE,
                classification=ShiftClassification.STRUCTURE_REVEALING,
                notes="Replaces intractable O(N!) 6N-dimensional ODE system with 6D collisionless kinetic PDE.",
            )
        )

        # 5. ADDITIONAL CANONICAL SHIFT: Time-Domain Signal to Grassmannian Subspace
        self.register_shift(
            RepresentationShiftContract(
                shift_id="SHIFT-GRASSMANNIAN-SUBSPACE",
                label="Time-Domain Signal to Grassmannian Subspace (y(t) -> Gr(k, n))",
                source_rep=RepresentationCategory.TIME_DOMAIN_SIGNAL,
                target_rep=RepresentationCategory.GRASSMANNIAN_SUBSPACE,
                transformation_morphism="y(t) |-> Range(Hankel(y)) in Gr(k, n) via Krylov / singular subspace identification",
                is_invertible=False,
                revealed_structure=[
                    StructuralProperty(
                        property_id="GRASS-PROP-01",
                        label="Exact System McMillan Degree",
                        mathematical_type="MINIMAL_DIMENSION",
                        formal_definition="Integer rank k = dim(Span{Hankel(y)}) isolating true dynamical order",
                        observability_in_source="LATENT_CONCEALED",
                        observability_in_target="OBSERVABLE",
                    ),
                    StructuralProperty(
                        property_id="GRASS-PROP-02",
                        label="Dynamical Invariant Subspace Projector",
                        mathematical_type="SUBSPACE_PROJECTOR",
                        formal_definition="Orthogonal projector P_K on the observable subspace invariant under system transition A",
                        observability_in_source="INACCESSIBLE",
                        observability_in_target="OBSERVABLE",
                    ),
                ],
                concealed_structure=[
                    StructuralProperty(
                        property_id="GRASS-CONC-01",
                        label="High-Frequency Stochastic Sensor Measurement Noise",
                        mathematical_type="NOISE_CORRUPTION",
                        formal_definition="Orthogonal complement component (I - P_K)y containing zero dynamical order",
                        observability_in_source="OBSERVABLE",
                        observability_in_target="INACCESSIBLE",
                    ),
                ],
                preserved_invariants=[
                    "Dominant System Poles / Frequencies",
                    "Hankel Singular Values",
                ],
                target_questions=[
                    "What is the minimal order of the state-space realization generating y(t)?",
                ],
                decidability_transition=DecidabilityStatus.ILL_CONDITIONED_TO_WELL_CONDITIONED,
                classification=ShiftClassification.STRUCTURE_REVEALING,
                notes="Isolates geometric state order from noise corrupted time series.",
            )
        )

        # 6. ADDITIONAL CANONICAL SHIFT: Ambient Manifold to Casimir Quotient
        self.register_shift(
            RepresentationShiftContract(
                shift_id="SHIFT-CASIMIR-QUOTIENT",
                label="Ambient Manifold to Casimir Quotient (M -> M // G)",
                source_rep=RepresentationCategory.AMBIENT_MANIFOLD,
                target_rep=RepresentationCategory.CASIMIR_QUOTIENT,
                transformation_morphism="x in M |-> [x] in M // G via Marsden-Weinstein symplectic reduction",
                is_invertible=False,
                revealed_structure=[
                    StructuralProperty(
                        property_id="CAS-PROP-01",
                        label="Reduced Symplectic Leaf Integrability",
                        mathematical_type="INTEGRABLE_FOLIATION",
                        formal_definition="Non-degenerate Poisson leaf with exact action-angle variables",
                        observability_in_source="LATENT_CONCEALED",
                        observability_in_target="OBSERVABLE",
                    ),
                    StructuralProperty(
                        property_id="CAS-PROP-02",
                        label="Coadjoint Orbit Geometry",
                        mathematical_type="ORBIT_TOPOLOGY",
                        formal_definition="Symplectic 2-form on the coadjoint orbit O_mu satisfying Kostant-Kirillov structure",
                        observability_in_source="INACCESSIBLE",
                        observability_in_target="OBSERVABLE",
                    ),
                ],
                concealed_structure=[
                    StructuralProperty(
                        property_id="CAS-CONC-01",
                        label="Gauge / Fiber Group Coordinate Phases",
                        mathematical_type="GAUGE_COORDINATE",
                        formal_definition="Position along the symmetry group orbit G . x",
                        observability_in_source="OBSERVABLE",
                        observability_in_target="INACCESSIBLE",
                    ),
                ],
                preserved_invariants=[
                    "Casimir Invariant Functionals C(x)",
                    "Reduced Hamiltonian Energy Levels",
                ],
                target_questions=[
                    "Is the Hamiltonian system completely integrable on its invariant leaves?",
                ],
                decidability_transition=DecidabilityStatus.INTRACTABLE_TO_DECIDABLE,
                classification=ShiftClassification.STRUCTURE_REVEALING,
                notes="Eliminates ignorable symmetry coordinates to expose underlying symplectic geometry.",
            )
        )

        # 7. ADDITIONAL CANONICAL SHIFT: Spatial Field to Fourier Harmonics (Complementary Duality)
        self.register_shift(
            RepresentationShiftContract(
                shift_id="SHIFT-FOURIER-DUALITY",
                label="Spatial Field to Fourier Harmonics (u(x) -> u_hat(k))",
                source_rep=RepresentationCategory.SPATIAL_FIELD,
                target_rep=RepresentationCategory.FOURIER_HARMONICS,
                transformation_morphism="u(x) in L^2(R^n) |-> u_hat(k) = int u(x) e^{-i k . x} dx",
                is_invertible=True,
                revealed_structure=[
                    StructuralProperty(
                        property_id="FOUR-PROP-01",
                        label="Sobolev Regularity Class & Spectral Decay",
                        mathematical_type="SOBOLEV_INDEX",
                        formal_definition="Exact Sobolev index s such that int (1 + |k|^2)^s |u_hat(k)|^2 dk < infty",
                        observability_in_source="LATENT_CONCEALED",
                        observability_in_target="OBSERVABLE",
                    ),
                    StructuralProperty(
                        property_id="FOUR-PROP-02",
                        label="Differential Operator Diagonalization",
                        mathematical_type="SPECTRAL_MULTIPLIER",
                        formal_definition="Conversion of Laplace operator Delta into algebraic multiplication by -|k|^2",
                        observability_in_source="LATENT_CONCEALED",
                        observability_in_target="OBSERVABLE",
                    ),
                ],
                concealed_structure=[
                    StructuralProperty(
                        property_id="FOUR-CONC-01",
                        label="Sharp Spatial Boundary Support Localization",
                        mathematical_type="SPATIAL_SUPPORT",
                        formal_definition="Exact geometric boundary of compact support supp(u) subset Omega",
                        observability_in_source="OBSERVABLE",
                        observability_in_target="LATENT_CONCEALED",
                    ),
                ],
                preserved_invariants=[
                    "L^2 Norm / Total Signal Energy (Plancherel identity)",
                    "Inner Product Conservation",
                ],
                target_questions=[
                    "What is the smoothness / Sobolev regularity order of the solution field?",
                ],
                decidability_transition=DecidabilityStatus.ILL_CONDITIONED_TO_WELL_CONDITIONED,
                classification=ShiftClassification.COMPLEMENTARY_DUALITY,
                notes="Heisenberg-Weyl uncertainty trade-off: frequency localization conceals spatial support boundary.",
            )
        )

        # 8. ADDITIONAL CANONICAL SHIFT: Operator Matrix to Singular Spectrum
        self.register_shift(
            RepresentationShiftContract(
                shift_id="SHIFT-OPERATOR-SVD",
                label="Operator Matrix to Singular Spectrum (A -> (Sigma, U, V))",
                source_rep=RepresentationCategory.OPERATOR_MATRIX,
                target_rep=RepresentationCategory.SINGULAR_SPECTRUM,
                transformation_morphism="A in B(H_1, H_2) |-> A = U Sigma V^*",
                is_invertible=True,
                revealed_structure=[
                    StructuralProperty(
                        property_id="SVD-PROP-01",
                        label="Exact Numerical Rank and Ill-Posedness Index",
                        mathematical_type="SPECTRAL_INDEX",
                        formal_definition="Singular value decay rate sigma_i ~ i^{-alpha} classifying mild vs severe ill-posedness",
                        observability_in_source="LATENT_CONCEALED",
                        observability_in_target="OBSERVABLE",
                    ),
                    StructuralProperty(
                        property_id="SVD-PROP-02",
                        label="Picard Condition Identifiability Criteria",
                        mathematical_type="IDENTIFIABILITY_TEST",
                        formal_definition="Sum |<y, u_i>|^2 / sigma_i^2 < infty determining exact solvability",
                        observability_in_source="LATENT_CONCEALED",
                        observability_in_target="OBSERVABLE",
                    ),
                ],
                concealed_structure=[
                    StructuralProperty(
                        property_id="SVD-CONC-01",
                        label="Sparse Banded Stencil Structure",
                        mathematical_type="SPARSITY_PATTERN",
                        formal_definition="Local nearest-neighbor differential stencil sparsity in original matrix coordinates",
                        observability_in_source="OBSERVABLE",
                        observability_in_target="INACCESSIBLE",
                    ),
                ],
                preserved_invariants=[
                    "Operator Operator-Norm and Frobenius Norm",
                    "Determinant / Trace Identities",
                ],
                target_questions=[
                    "Is the inverse problem well-posed, mildly ill-posed, or severely ill-posed?",
                    "Does the measured data y satisfy the discrete Picard condition?",
                ],
                decidability_transition=DecidabilityStatus.ILL_CONDITIONED_TO_WELL_CONDITIONED,
                classification=ShiftClassification.STRUCTURE_REVEALING,
                notes="Exposes the spectral conditioning and Picard satisfiability directly.",
            )
        )

        # 9. CONTROL SHIFT: Isomorphic Translation (Unitary Basis Rotation)
        self.register_shift(
            RepresentationShiftContract(
                shift_id="SHIFT-ISOMORPHIC-ROTATION",
                label="Isometric Coordinate Rotation (Orthogonal / Unitary)",
                source_rep=RepresentationCategory.STATE_TRAJECTORY,
                target_rep=RepresentationCategory.STATE_TRAJECTORY,
                transformation_morphism="x |-> Q x where Q^T Q = I",
                is_invertible=True,
                revealed_structure=[],
                concealed_structure=[],
                preserved_invariants=[
                    "Euclidean Length / L^2 Norm",
                    "Eigenvalue Spectrum of Linear System",
                    "All Topological and Dynamical Invariants",
                ],
                target_questions=[
                    "Is the norm of the state trajectory conserved?",
                ],
                decidability_transition=DecidabilityStatus.EQUIVALENT_DECIDABILITY,
                classification=ShiftClassification.ISOMORPHIC_TRANSLATION,
                notes="Pure isometric rotation: no new qualitative invariants revealed, none destroyed.",
            )
        )

        # 10. CONTROL SHIFT: Abstraction Collapse (Unscaled Grid Downsampling)
        self.register_shift(
            RepresentationShiftContract(
                shift_id="SHIFT-ABSTRACTION-DOWNSAMPLE",
                label="Unscaled Coarse Downsampling (Sub-sampling Collapse)",
                source_rep=RepresentationCategory.SPATIAL_FIELD,
                target_rep=RepresentationCategory.DISCRETIZED_COARSE_GRID,
                transformation_morphism="u(x) |-> {u(x_j)}_{j=1}^M with M << N, without multiscale reconstruction",
                is_invertible=False,
                revealed_structure=[],
                concealed_structure=[
                    StructuralProperty(
                        property_id="DOWN-CONC-01",
                        label="Sub-Grid High Frequency Variations",
                        mathematical_type="HIGH_FREQUENCY_CONTENT",
                        formal_definition="All modes k > k_Nyquist aliased or permanently discarded",
                        observability_in_source="OBSERVABLE",
                        observability_in_target="INACCESSIBLE",
                    ),
                    StructuralProperty(
                        property_id="DOWN-CONC-02",
                        label="Differential Derivative Regularity",
                        mathematical_type="SMOOTHNESS_DIFFERENTIAL",
                        formal_definition="Continuity and Sobolev derivatives of the field",
                        observability_in_source="OBSERVABLE",
                        observability_in_target="INACCESSIBLE",
                    ),
                ],
                preserved_invariants=[
                    "Average Mean Field Value (Zero-th Moment Approximate)",
                ],
                target_questions=[
                    "What is the coarse spatial mean of the field?",
                ],
                decidability_transition=DecidabilityStatus.EQUIVALENT_DECIDABILITY,
                classification=ShiftClassification.ABSTRACTION_COLLAPSE,
                notes="Pure information destruction: no new structural insight gained, sub-grid structure destroyed.",
            )
        )

    def register_shift(self, shift: RepresentationShiftContract) -> None:
        self.shift_catalog[shift.shift_id] = shift

    def get_shift(self, shift_id: str) -> Optional[RepresentationShiftContract]:
        return self.shift_catalog.get(shift_id)

    def list_shifts(self) -> List[RepresentationShiftContract]:
        return list(self.shift_catalog.values())

    def evaluate_representation_shift(
        self,
        shift_id: str,
        subject_id: str,
        subject_label: str,
        question_id: str,
        question_label: str,
    ) -> ShiftEvaluationResult:
        """
        Evaluates a specific representation shift on a mathematical subject and question.
        Returns the formal structural partition: Delta S^+, Delta S^-, and S^cap.
        """
        shift = self.shift_catalog[shift_id]

        revealed_labels = [p.label for p in shift.revealed_structure]
        concealed_labels = [p.label for p in shift.concealed_structure]
        preserved_labels = list(shift.preserved_invariants)

        return ShiftEvaluationResult(
            subject_id=subject_id,
            subject_label=subject_label,
            question_id=question_id,
            question_label=question_label,
            shift_id=shift.shift_id,
            shift_label=shift.label,
            classification=shift.classification,
            decidability_transition=shift.decidability_transition,
            revealed_feature_count=len(revealed_labels),
            concealed_feature_count=len(concealed_labels),
            preserved_invariant_count=len(preserved_labels),
            revealed_labels=revealed_labels,
            concealed_labels=concealed_labels,
            preserved_labels=preserved_labels,
            is_falsified=False,
            falsification_reason=None,
        )

    def sweep_graph_subjects(
        self,
        subjects: List[Dict[str, Any]],
    ) -> Tuple[List[ShiftEvaluationResult], ShiftSummaryReport]:
        """
        Sweeps all representation shifts across the mathematical subjects in G_M.
        """
        evaluations: List[ShiftEvaluationResult] = []
        total_revealed = 0
        total_concealed = 0
        total_preserved = 0

        class_counts = {
            ShiftClassification.STRUCTURE_REVEALING: 0,
            ShiftClassification.ISOMORPHIC_TRANSLATION: 0,
            ShiftClassification.ABSTRACTION_COLLAPSE: 0,
            ShiftClassification.COMPLEMENTARY_DUALITY: 0,
        }

        # Track landmark shifts
        landmark_ids = [
            "SHIFT-LYAPUNOV-POTENTIAL",
            "SHIFT-PONTRYAGIN-COSTATE",
            "SHIFT-MARCHENKO-KERNEL",
            "SHIFT-VLASOV-KINETIC",
        ]
        landmark_seen = {lid: False for lid in landmark_ids}

        unique_subjects: Set[str] = set()
        unique_questions: Set[str] = set()

        for subj in subjects:
            s_id = subj.get("id", "UNKNOWN_SUBJ")
            s_label = subj.get("label", s_id)
            unique_subjects.add(s_id)
            domain = subj.get("domain", "")

            questions = subj.get("questions", [])
            if not questions:
                # Synthesize default domain question
                questions = [{"id": f"{s_id}_Q0", "label": f"Characteristic property of {s_label}"}]

            for q in questions:
                q_id = q.get("id", "UNKNOWN_Q")
                q_label = q.get("label", q_id)
                unique_questions.add(q_id)

                # Select compatible shifts based on subject domain / representation
                compatible_shifts = self._select_compatible_shifts(domain, s_id)
                for shift in compatible_shifts:
                    res = self.evaluate_representation_shift(
                        shift_id=shift.shift_id,
                        subject_id=s_id,
                        subject_label=s_label,
                        question_id=q_id,
                        question_label=q_label,
                    )
                    evaluations.append(res)

                    class_counts[res.classification] += 1
                    total_revealed += res.revealed_feature_count
                    total_concealed += res.concealed_feature_count
                    total_preserved += res.preserved_invariant_count

                    if shift.shift_id in landmark_seen:
                        landmark_seen[shift.shift_id] = True

        # Check provenance isolation: ensure no cultural tokens in evaluation results
        provenance_isolated, leakage = self._verify_purity(evaluations)

        summary = ShiftSummaryReport(
            total_shifts_evaluated=len(self.shift_catalog),
            total_subjects_evaluated=len(unique_subjects),
            total_questions_evaluated=len(unique_questions),
            total_evaluations=len(evaluations),
            structure_revealing_count=class_counts[ShiftClassification.STRUCTURE_REVEALING],
            isomorphic_translation_count=class_counts[ShiftClassification.ISOMORPHIC_TRANSLATION],
            abstraction_collapse_count=class_counts[ShiftClassification.ABSTRACTION_COLLAPSE],
            complementary_duality_count=class_counts[ShiftClassification.COMPLEMENTARY_DUALITY],
            revealed_features_total=total_revealed,
            concealed_features_total=total_concealed,
            preserved_invariants_total=total_preserved,
            landmark_coverage=landmark_seen,
            provenance_isolated=provenance_isolated,
            cultural_leakage_detected=leakage,
        )

        return evaluations, summary

    def _select_compatible_shifts(self, domain: str, subject_id: str) -> List[RepresentationShiftContract]:
        """Maps subject domain to mathematically compatible representation shifts."""
        compatible: List[RepresentationShiftContract] = []

        # Always include the control shifts
        if "SHIFT-ISOMORPHIC-ROTATION" in self.shift_catalog:
            compatible.append(self.shift_catalog["SHIFT-ISOMORPHIC-ROTATION"])

        # Domain mappings
        if domain in ["DYNAMICAL_SYSTEMS", "VARIATIONAL_OPTIMAL_CONTROL"]:
            if "SHIFT-LYAPUNOV-POTENTIAL" in self.shift_catalog:
                compatible.append(self.shift_catalog["SHIFT-LYAPUNOV-POTENTIAL"])
            if "SHIFT-PONTRYAGIN-COSTATE" in self.shift_catalog:
                compatible.append(self.shift_catalog["SHIFT-PONTRYAGIN-COSTATE"])
            if "SHIFT-CASIMIR-QUOTIENT" in self.shift_catalog:
                compatible.append(self.shift_catalog["SHIFT-CASIMIR-QUOTIENT"])

        if domain in ["INVERSE_PROBLEMS", "SPECTRAL_APPROXIMATION"]:
            if "SHIFT-MARCHENKO-KERNEL" in self.shift_catalog:
                compatible.append(self.shift_catalog["SHIFT-MARCHENKO-KERNEL"])
            if "SHIFT-OPERATOR-SVD" in self.shift_catalog:
                compatible.append(self.shift_catalog["SHIFT-OPERATOR-SVD"])
            if "SHIFT-GRASSMANNIAN-SUBSPACE" in self.shift_catalog:
                compatible.append(self.shift_catalog["SHIFT-GRASSMANNIAN-SUBSPACE"])

        if domain in ["KINETIC_DISPERSIVE_WAVES"]:
            if "SHIFT-VLASOV-KINETIC" in self.shift_catalog:
                compatible.append(self.shift_catalog["SHIFT-VLASOV-KINETIC"])
            if "SHIFT-FOURIER-DUALITY" in self.shift_catalog:
                compatible.append(self.shift_catalog["SHIFT-FOURIER-DUALITY"])

        if domain in ["GEOMETRIC_ALGEBRAIC"]:
            if "SHIFT-CASIMIR-QUOTIENT" in self.shift_catalog:
                compatible.append(self.shift_catalog["SHIFT-CASIMIR-QUOTIENT"])
            if "SHIFT-GRASSMANNIAN-SUBSPACE" in self.shift_catalog:
                compatible.append(self.shift_catalog["SHIFT-GRASSMANNIAN-SUBSPACE"])

        # Default fallback if domain unmapped
        if len(compatible) == 1:
            for sid in ["SHIFT-LYAPUNOV-POTENTIAL", "SHIFT-FOURIER-DUALITY", "SHIFT-OPERATOR-SVD"]:
                if sid in self.shift_catalog and self.shift_catalog[sid] not in compatible:
                    compatible.append(self.shift_catalog[sid])

        return compatible

    def _verify_purity(self, evaluations: List[ShiftEvaluationResult]) -> Tuple[bool, bool]:
        """Verifies zero cultural provenance tokens leak into mathematical shift contracts."""
        forbidden_tokens = ["soviet", "russian", "western", "marxist", "lenin", "cold_war"]
        for ev in evaluations:
            text = f"{ev.shift_label} {ev.revealed_labels} {ev.concealed_labels}".lower()
            for token in forbidden_tokens:
                if token in text:
                    return False, True
        return True, False
