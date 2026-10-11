from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class VocabularyEvolution:
    root: str
    native_term: str
    english_concept: str
    earliest_attestation_year: int
    primary_schools: list[str]
    transition_phases: list[dict[str, Any]]
    operator_role: str
    formal_symbol_mapping: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# Comprehensive registry of the 13 core Soviet operator vocabulary terms
OPERATOR_VOCABULARY_REGISTRY: list[VocabularyEvolution] = [
    VocabularyEvolution(
        root="оператор",
        native_term="оператор",
        english_concept="Operator",
        earliest_attestation_year=1935,
        primary_schools=["GELFAND", "TIKHONOV", "FADDEEV"],
        operator_role="Primary mathematical agent of system transformation (T: X -> Y).",
        formal_symbol_mapping="T, L, A, R_alpha",
        transition_phases=[
            {
                "period": "1935–1945",
                "focus": "Abstract functional analysis and normed rings (Gelfand). Operators as elements of algebraic structures.",
                "context": "Classical differential and integral operators in functional spaces.",
            },
            {
                "period": "1951–1959",
                "focus": "Transformation operators (операторы преобразования, Povzner–Levitan–Marchenko).",
                "context": "Integral kernels mapping unperturbed differential operators to perturbed physical systems.",
            },
            {
                "period": "1960–1975",
                "focus": "Ill-posed operator equations and regularizing operators (Tikhonov). Resolvent operators in scattering (Faddeev).",
                "context": "Operators that invert noisy data into physical parameters subject to compactness and stability.",
            },
        ],
    ),
    VocabularyEvolution(
        root="преобразован",
        native_term="преобразование",
        english_concept="Transformation / Transform",
        earliest_attestation_year=1853,
        primary_schools=["CHEBYSHEV", "GELFAND", "FADDEEV", "PONTRYAGIN"],
        operator_role="Action mapping one coordinate, state, or operator representation into another.",
        formal_symbol_mapping="K(x,y), I + K",
        transition_phases=[
            {
                "period": "1853–1890",
                "focus": "Kinematic mechanism transformations (Chebyshev).",
                "context": "Geometric transformations of mechanical linkages preserving rectilinear or circular paths.",
            },
            {
                "period": "1937–1960",
                "focus": "Canonical transformations in phase space and Hamiltonian control (Pontryagin).",
                "context": "Coordinate transforms that preserve symplectic structure and Hamiltonian equations.",
            },
            {
                "period": "1951–1970",
                "focus": "Volterra transformation operator in inverse spectral theory (Gelfand–Levitan).",
                "context": "Mapping solutions of y'' + q(x)y = lambda y into cos(sqrt(lambda) x) via triangular kernel.",
            },
        ],
    ),
    VocabularyEvolution(
        root="отображен",
        native_term="отображение",
        english_concept="Mapping",
        earliest_attestation_year=1853,
        primary_schools=["CHEBYSHEV", "TIKHONOV"],
        operator_role="Preservation of geometric, topological, or analytical properties under domain deformation.",
        formal_symbol_mapping="f: Omega -> Omega'",
        transition_phases=[
            {
                "period": "1853–1938",
                "focus": "Chebyshev interval mapping and Lavrentyev continuous/quasiconformal mappings.",
                "context": "Minimizing maximum distortion under continuous geometric mappings.",
            },
            {
                "period": "1943–1965",
                "focus": "Forward and inverse mappings between state and data spaces (Tikhonov).",
                "context": "Mapping compact sets in metric spaces to establish conditional continuous invertibility.",
            },
        ],
    ),
    VocabularyEvolution(
        root="функционал",
        native_term="функционал",
        english_concept="Functional",
        earliest_attestation_year=1943,
        primary_schools=["TIKHONOV", "PONTRYAGIN"],
        operator_role="Scalar-valued mapping on infinite-dimensional state spaces governing selection and optimization.",
        formal_symbol_mapping="J[u], M^alpha[z], Omega[z]",
        transition_phases=[
            {
                "period": "1943–1963",
                "focus": "Tikhonov smoothing functional: M^alpha[z] = ||Az - u||^2 + alpha * Omega[z].",
                "context": "Balancing fidelity to noisy observation with a stabilizing penalty on solution roughness.",
            },
            {
                "period": "1956–1961",
                "focus": "Pontryagin cost functional: J = integral f^0(x, u) dt.",
                "context": "Integral objective minimized over non-smooth admissible control paths.",
            },
        ],
    ),
    VocabularyEvolution(
        root="состояни",
        native_term="состояние / фазовые координаты",
        english_concept="State / Phase Coordinates",
        earliest_attestation_year=1892,
        primary_schools=["LYAPUNOV", "PONTRYAGIN", "VLASOV", "BOGOLYUBOV"],
        operator_role="Minimal complete coordinate set characterizing system configuration and memory at time t.",
        formal_symbol_mapping="x(t) in R^n, f(r, v, t)",
        transition_phases=[
            {
                "period": "1892–1930",
                "focus": "Lyapunov perturbed and unperturbed state trajectories.",
                "context": "Deviation variables x_k(t) describing displacement from a reference motion.",
            },
            {
                "period": "1938–1946",
                "focus": "Collective state in phase space: distribution function f(r, v, t) (Vlasov, Bogolyubov).",
                "context": "Abandoning individual particle states in favor of continuous probability density in 6D phase space.",
            },
            {
                "period": "1956–1961",
                "focus": "Pontryagin phase state x(t) and conjugate momentum psi(t).",
                "context": "Evolution of internal state under external admissible control inputs.",
            },
        ],
    ),
    VocabularyEvolution(
        root="траектори",
        native_term="траектория",
        english_concept="Trajectory",
        earliest_attestation_year=1892,
        primary_schools=["LYAPUNOV", "ANDRONOV", "PONTRYAGIN"],
        operator_role="Parameterized curve x(t) traced by a dynamical system in phase space.",
        formal_symbol_mapping="{x(t)}_{t >= 0}",
        transition_phases=[
            {
                "period": "1892–1937",
                "focus": "Lyapunov stability of trajectories and Andronov phase-space limit cycles.",
                "context": "Topological partitioning of phase space into stable, unstable, and periodic trajectories.",
            },
            {
                "period": "1956–1961",
                "focus": "Pontryagin optimal trajectory connecting initial state x_0 to target set X_1.",
                "context": "Curves driven by piecewise continuous controls with trajectory corners.",
            },
        ],
    ),
    VocabularyEvolution(
        root="устойчивост",
        native_term="устойчивость / грубость",
        english_concept="Stability / Structural Robustness",
        earliest_attestation_year=1892,
        primary_schools=["LYAPUNOV", "ANDRONOV", "TIKHONOV"],
        operator_role="Invariance of qualitative behavior under state perturbations or model/data uncertainties.",
        formal_symbol_mapping="V(x), dV/dt <= 0, ||z_alpha - z_exact|| -> 0",
        transition_phases=[
            {
                "period": "1892–1920",
                "focus": "Lyapunov stability: boundedness of trajectories under initial perturbations.",
                "context": "Construction of scalar Lyapunov functions V(x) without explicit solution integration.",
            },
            {
                "period": "1937–1955",
                "focus": "Andronov–Pontryagin structural stability (грубость).",
                "context": "Preservation of topological phase portrait under small perturbations of the vector field itself.",
            },
            {
                "period": "1943–1963",
                "focus": "Tikhonov stability of inverse operators under observation noise.",
                "context": "Continuous dependence of reconstructed state on measurement errors in metric topologies.",
            },
        ],
    ),
    VocabularyEvolution(
        root="инвариант",
        native_term="инвариант",
        english_concept="Invariant",
        earliest_attestation_year=1892,
        primary_schools=["LYAPUNOV", "VLASOV", "ANDRONOV", "FADDEEV"],
        operator_role="Quantity, subspace, or topological property preserved under system evolution.",
        formal_symbol_mapping="I(x) = const, div(v) = 0",
        transition_phases=[
            {
                "period": "1892–1938",
                "focus": "First integrals of motion (Lyapunov) and Liouville phase-volume invariance (Vlasov).",
                "context": "Conservation of Hamiltonian energy, momentum, and 6D phase space volume df/dt = 0.",
            },
            {
                "period": "1937–1970",
                "focus": "Topological invariants of dynamical systems and gauge invariants in field theory (Faddeev).",
                "context": "Betti numbers of phase portraits and gauge-fixing invariants via Faddeev–Popov ghosts.",
            },
        ],
    ),
    VocabularyEvolution(
        root="допустим",
        native_term="допустимый",
        english_concept="Admissible",
        earliest_attestation_year=1943,
        primary_schools=["TIKHONOV", "PONTRYAGIN", "GELFAND"],
        operator_role="Enforcement of physical realizability constraints on states, controls, or spectra.",
        formal_symbol_mapping="u in U, z in Z_ad, rho(lambda) in M",
        transition_phases=[
            {
                "period": "1943–1963",
                "focus": "Tikhonov admissible class of solutions (допустимое множество).",
                "context": "Restricting inverse search to compact or bounded subsets where uniqueness and continuity hold.",
            },
            {
                "period": "1951–1960",
                "focus": "Gelfand–Levitan admissible spectral functions.",
                "context": "Monotonicity and asymptotic behavior required for a function to generate a physical potential.",
            },
            {
                "period": "1956–1961",
                "focus": "Pontryagin admissible control (допустимое управление).",
                "context": "Controls restricted to closed, bounded sets U reflecting actuator saturation and physical thrust limits.",
            },
        ],
    ),
    VocabularyEvolution(
        root="краев",
        native_term="краевое условие",
        english_concept="Boundary Condition",
        earliest_attestation_year=1853,
        primary_schools=["GELFAND", "TIKHONOV", "CHEBYSHEV"],
        operator_role="Specification of system constraints at spatial or temporal boundaries determining operator domain.",
        formal_symbol_mapping="y'(0) - h*y(0) = 0, y(T) in S_1",
        transition_phases=[
            {
                "period": "1853–1930",
                "focus": "Endpoint extrema in Chebyshev approximation and classical Sturm–Liouville boundary values.",
                "context": "Equal-ripple deviations at interval endpoints and boundary constraints of vibrating strings.",
            },
            {
                "period": "1951–1965",
                "focus": "Normalization of transformation kernels via boundary conditions (Gelfand–Levitan).",
                "context": "Determining the integral kernel K(x,y) along the diagonal y = x from potential q(x) and boundary parameter h.",
            },
        ],
    ),
    VocabularyEvolution(
        root="обратн",
        native_term="обратная задача",
        english_concept="Inverse Problem",
        earliest_attestation_year=1943,
        primary_schools=["TIKHONOV", "GELFAND", "FADDEEV"],
        operator_role="Deduction of internal system structure or causes from observable external consequences.",
        formal_symbol_mapping="A z = u => z, rho(lambda) => q(x), S => V(r)",
        transition_phases=[
            {
                "period": "1943–1950",
                "focus": "Geophysical potential field inversion and Cauchy problem for elliptic equations (Tikhonov).",
                "context": "Reconstructing subsurface density or conductivity distributions from surface measurements.",
            },
            {
                "period": "1951–1959",
                "focus": "Inverse Sturm–Liouville spectral problem (Gelfand–Levitan, Marchenko).",
                "context": "Reconstructing a differential operator from its discrete and continuous spectra.",
            },
            {
                "period": "1959–1970",
                "focus": "Quantum inverse scattering theory (Faddeev).",
                "context": "Reconstructing quantum interaction potentials from asymptotic scattering amplitudes and phase shifts.",
            },
        ],
    ),
    VocabularyEvolution(
        root="регуляриз",
        native_term="регуляризация",
        english_concept="Regularization",
        earliest_attestation_year=1963,
        primary_schools=["TIKHONOV"],
        operator_role="Family of well-behaved operators converging to the unbounded inverse as noise vanishes.",
        formal_symbol_mapping="R_alpha = (A* A + alpha * C)^(-1) A*",
        transition_phases=[
            {
                "period": "1963–1965",
                "focus": "Foundational Tikhonov regularization of Fredholm integral equations of the first kind.",
                "context": "Introduction of stabilizer functional Omega[z] guaranteeing compact convergence.",
            },
            {
                "period": "1966–1980",
                "focus": "Discrepancy principle (принцип невязки, Morozov) and regularized numerical algorithms (Samarsky).",
                "context": "Adaptive selection of regularization parameter alpha = alpha(delta) matching observation noise.",
            },
        ],
    ),
    VocabularyEvolution(
        root="приближен",
        native_term="приближение",
        english_concept="Approximation",
        earliest_attestation_year=1853,
        primary_schools=["CHEBYSHEV", "LYAPUNOV", "BOGOLYUBOV"],
        operator_role="Constructive finite representation of complex infinite-dimensional behavior with controlled error.",
        formal_symbol_mapping="min max |f - P_n|, dx/dt = A x + o(||x||)",
        transition_phases=[
            {
                "period": "1853–1890",
                "focus": "Chebyshev uniform approximation (наилучшее приближение) on compact intervals.",
                "context": "Equioscillation alternation theorem producing optimal polynomials for mechanism synthesis.",
            },
            {
                "period": "1892–1937",
                "focus": "Lyapunov first-order approximation in stability theory.",
                "context": "Inferring nonlinear trajectory stability from spectrum of the linearized Jacobian matrix.",
            },
            {
                "period": "1937–1960",
                "focus": "Asymptotic Krylov–Bogolyubov–Mitropolsky averaging and perturbation approximations.",
                "context": "Rigorous multi-scale expansions for nonlinear oscillatory systems without secular divergence.",
            },
        ],
    ),
]


class OperatorVocabularyAnalyzer:
    """Interrogates and maps the 13 core Soviet operator vocabulary terms across sources and schools."""

    def __init__(self, registry: Optional[list[VocabularyEvolution]] = None) -> None:
        self.registry = registry or OPERATOR_VOCABULARY_REGISTRY

    def get_term_by_root(self, root: str) -> Optional[VocabularyEvolution]:
        for item in self.registry:
            if item.root == root or item.native_term == root:
                return item
        return None

    def export_vocabulary_dossier(self, output_path: Path) -> dict[str, Any]:
        data = {
            "title": "SOVCTX Operator Vocabulary & Semantic Evolution Index",
            "total_core_terms": len(self.registry),
            "vocabulary_terms": [t.to_dict() for t in self.registry],
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return data
