from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass
class MathematicalFormulation:
    formulation_label: str
    key_authors: list[str]
    foundational_publications: list[str]
    core_philosophical_stance: str
    formal_mathematical_equation: str
    underlying_assumptions: list[str]


@dataclass
class EpistemicContrastDossier:
    contrast_id: str
    title: str
    domain: str
    soviet_emphasized_formulation: MathematicalFormulation
    alternative_contemporary_formulation: MathematicalFormulation
    relationship_nature: str
    chronological_relationship: str
    decisive_distinction: str
    epistemic_consequences: list[str]
    technological_manifestations: list[str]
    international_cross_pollination: list[str]

    # Backward-compatibility accessors
    @property
    def soviet_tradition(self) -> MathematicalFormulation:
        return self.soviet_emphasized_formulation

    @property
    def western_tradition(self) -> MathematicalFormulation:
        return self.alternative_contemporary_formulation

    @property
    def decisive_divergence_point(self) -> str:
        return self.decisive_distinction

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["soviet_tradition"] = asdict(self.soviet_emphasized_formulation)
        d["western_tradition"] = asdict(self.alternative_contemporary_formulation)
        d["decisive_divergence_point"] = self.decisive_distinction
        return d


EPISTEMIC_CONTRASTS_REGISTRY: list[EpistemicContrastDossier] = [
    EpistemicContrastDossier(
        contrast_id="CONTRAST_01_TIKHONOV_VS_HADAMARD",
        title="Tikhonov Constructive Regularization vs. Hadamard Well-Posedness Criterion",
        domain="Inverse Problems & Measurement Inversion",
        soviet_emphasized_formulation=MathematicalFormulation(
            formulation_label="Soviet Inverse Problem School (Tikhonov School)",
            key_authors=["Тихонов А. Н.", "Лаврентьев М. М.", "Иванов В. К."],
            foundational_publications=[
                "Об устойчивости обратных задач (ДАН СССР, 1943)",
                "О решении некорректно поставленных задач и методе регуляризации (ДАН СССР, 1963)",
                "О регуляризации некорректно поставленных задач (ДАН СССР, 1963)",
            ],
            core_philosophical_stance=(
                "Ill-posed problems are the natural mathematical expression of indirect observation, remote sensing, "
                "and physical measurement. The unbounded inverse does not mean the problem is meaningless or 'mal posé'; "
                "it requires a systematic constructive theory for obtaining stable approximate solutions on compact "
                "admissible subsets or via parameterized regularizing operators."
            ),
            formal_mathematical_equation=(
                "z_alpha = argmin_z (||A z - u_delta||^2 + alpha * Omega[z]), where alpha = alpha(delta) -> 0"
            ),
            underlying_assumptions=[
                "Physical measurements are inevitably corrupted by noise (delta > 0).",
                "A priori structural admissibility (compactness, smoothness, bounded energy) restores stability.",
                "Indirect observation is a reconstruction problem, not a defective experiment.",
            ],
        ),
        alternative_contemporary_formulation=MathematicalFormulation(
            formulation_label="Hadamard Well-Posedness Diagnostic Criterion",
            key_authors=["Jacques Hadamard"],
            foundational_publications=[
                "Sur les problèmes aux dérivées partielles et leur signification physique (1902)",
                "Lectures on Cauchy's Problem in Linear Partial Differential Equations (1923)",
            ],
            core_philosophical_stance=(
                "A mathematical problem representing a physical phenomenon must have a unique solution "
                "that depends continuously on the boundary/initial data (Hadamard well-posedness). Problems lacking "
                "continuous dependence (such as Cauchy problems for elliptic equations) are classified as ill-posed."
            ),
            formal_mathematical_equation="A z = u, exists! z in Z, ||delta z|| <= C * ||delta u|| (C < infinity)",
            underlying_assumptions=[
                "Exact forward observability without loss of high-frequency components.",
                "Discontinuity under noise indicates an incomplete or defective mathematical model.",
            ],
        ),
        relationship_nature="CLASSIFICATION_TO_CONSTRUCTIVE_TREATMENT",
        chronological_relationship="EXTENDS_PREVIOUS_CRITERION",
        decisive_distinction=(
            "Hadamard provided the influential diagnostic criterion classifying well-posedness; "
            "Tikhonov developed a systematic constructive theory for obtaining stable approximate solutions "
            "when that criterion fails, transforming ill-posedness from a rejection boundary into a fertile field."
        ),
        epistemic_consequences=[
            "Establishment of conditional well-posedness (корректность по Тихонову) as an independent branch of mathematics.",
            "Development of parameter choice rules (Morozov discrepancy principle) replacing naive matrix inversion.",
            "Legitimization of inverse problem reconstruction across physics rather than forcing forward problem reformulations.",
        ],
        technological_manifestations=[
            "Magnetotelluric geophysical sounding (MTZ) and deep seismic oil/gas exploration.",
            "Zelkin antenna synthesis and phased-array radar pattern inversion.",
            "Medical tomography, deconvolution of blurred optical images, and non-destructive testing.",
        ],
        international_cross_pollination=[
            "Tikhonov regularization became an international standard (known in the West as Tikhonov-Phillips regularization).",
            "Broadly adopted in modern statistical learning theory, ridge regression, and machine learning.",
        ],
    ),
    EpistemicContrastDossier(
        contrast_id="CONTRAST_02_PONTRYAGIN_VS_CLASSICAL_VARIATIONS",
        title="Pontryagin Maximum Principle on Closed Sets vs. Classical Variations & Dynamic Programming",
        domain="Optimal Control & Trajectory Optimization",
        soviet_emphasized_formulation=MathematicalFormulation(
            formulation_label="Pontryagin Optimal Control School (Steklov MIAN)",
            key_authors=["Понтрягин Л. С.", "Болтянский В. Г.", "Гамкрелидзе Р. В.", "Мищенко Е. Ф."],
            foundational_publications=[
                "К теории оптимальных процессов (ДАН СССР, 1956)",
                "Математическая теория оптимальных процессов (1961)",
            ],
            core_philosophical_stance=(
                "Physical actuators (rudders, thrusters, valves) have hard structural constraints (u in U, where U is compact/closed). "
                "Classical smooth variations fail when the optimal control sits permanently on the boundary of U. "
                "Needle-like variations (игольчатые вариации) prove that the realized control must maximize the Hamiltonian pointwise."
            ),
            formal_mathematical_equation=(
                "dot(x) = del H / del psi, dot(psi) = - del H / del x, with H(x, psi, u(t)) = max_{v in U} H(x, psi, v) a.e."
            ),
            underlying_assumptions=[
                "Actuator limits are hard physical boundaries, not soft quadratic penalties.",
                "Optimal controls are frequently discontinuous switching functions (relay / bang-bang control).",
            ],
        ),
        alternative_contemporary_formulation=MathematicalFormulation(
            formulation_label="Classical Calculus of Variations & Dynamic Programming (Bellman)",
            key_authors=["Leonhard Euler", "Joseph-Louis Lagrange", "Karl Weierstrass", "Richard Bellman"],
            foundational_publications=[
                "Dynamic Programming (Princeton University Press, 1957)",
                "Calculus of Variations (classical treatises)",
            ],
            core_philosophical_stance=(
                "Optimal paths are found by setting the first variation of a smooth functional to zero (delta J = 0), "
                "or by computing a continuous value function V(x) satisfying the Hamilton-Jacobi-Bellman partial differential equation."
            ),
            formal_mathematical_equation="del V / del t + min_{u} H(x, del V / del x, u) = 0",
            underlying_assumptions=[
                "Control sets are open or penalties are differentiable quadratic forms.",
                "The value function V(x, t) possesses sufficient differentiability everywhere.",
            ],
        ),
        relationship_nature="ALTERNATIVE_OPTIMAL_CONTROL_FRAMEWORK",
        chronological_relationship="PARALLELS_AND_INTERACTS",
        decisive_distinction=(
            "Pontryagin's method directly accommodates closed control sets and discontinuous switching controls "
            "via needle variations on symplectic phase trajectories, whereas dynamic programming constructs global "
            "value functions via PDEs and classical variations assume open interior extrema."
        ),
        epistemic_consequences=[
            "Rigorous mathematical proof that relay (bang-bang) control is time-optimal for linear systems.",
            "Establishment of symplectic Hamiltonian phase-space trajectories for engineering control.",
            "Unification of dynamics, differential games, and trajectory optimization without requiring Bellman smoothness.",
        ],
        technological_manifestations=[
            "Minimum-time missile trajectory guidance and interceptor steering.",
            "Spacecraft attitude orientation and reaction wheel / jet switching.",
            "Orbital rendezvous and soft lunar/planetary landing descent sequences.",
        ],
        international_cross_pollination=[
            "Pontryagin's Maximum Principle crossed geopolitical boundaries immediately upon publication.",
            "Adopted by NASA by 1963 for Apollo lunar orbital rendezvous studies alongside dynamic programming.",
        ],
    ),
    EpistemicContrastDossier(
        contrast_id="CONTRAST_03_ANDRONOV_VS_BODE_NYQUIST",
        title="Andronov Phase-Space Structural Stability vs. Bode/Nyquist Linear Frequency Response",
        domain="Dynamical Systems & Stabilization",
        soviet_emphasized_formulation=MathematicalFormulation(
            formulation_label="Andronov-Pontryagin Nonlinear Dynamics School (Gorky GIFTI / MIAN)",
            key_authors=["Андронов А. А.", "Понтрягин Л. С.", "Витт А. А.", "Хайкин С. Э."],
            foundational_publications=[
                "Грубые системы (ДАН СССР, 1937)",
                "Теория колебаний (1937)",
            ],
            core_philosophical_stance=(
                "Real engineering oscillators and feedback systems are fundamentally nonlinear and operate on limit cycles. "
                "The essential question is not small-signal linear stability, but structural stability (грубость): does the "
                "qualitative topological structure of the phase portrait survive small perturbations in the vector field?"
            ),
            formal_mathematical_equation="dot(x) = P(x, y) + p(x, y), dot(y) = Q(x, y) + q(x, y), with topological homeomorphism",
            underlying_assumptions=[
                "Nonlinearities cannot be ignored or linearized around an equilibrium without losing limit cycle phenomena.",
                "System robustness requires topological stability under vector-field deformation.",
            ],
        ),
        alternative_contemporary_formulation=MathematicalFormulation(
            formulation_label="Classical Linear Frequency-Domain Analysis (Nyquist, Bode, Wiener)",
            key_authors=["Harry Nyquist", "Hendrik Bode", "Norbert Wiener"],
            foundational_publications=[
                "Regeneration Theory (Bell System Technical Journal, 1932)",
                "Network Analysis and Feedback Amplifier Design (1945)",
            ],
            core_philosophical_stance=(
                "System stability is governed by the frequency-domain transfer function G(s) of a linearized model. "
                "Stability margins (gain margin, phase margin) are evaluated by contour encirclement in the complex plane."
            ),
            formal_mathematical_equation="Y(s) = G(s) U(s), 1 + G(j omega) H(j omega) != 0, Nyquist criterion",
            underlying_assumptions=[
                "Linear or small-signal operating regime around a single setpoint.",
                "Input-output frequency transfer representation suffices without modeling internal state topologies.",
            ],
        ),
        relationship_nature="NONLINEAR_PHASE_SPACE_VS_LINEAR_FREQUENCY",
        chronological_relationship="PARALLELS_COMPLEMENTARY_DOMAINS",
        decisive_distinction=(
            "Linear frequency response evaluates transfer functions of linearized single-input single-output systems; "
            "Andronov phase-space analysis evaluates the global topological robustness of nonlinear limit cycles."
        ),
        epistemic_consequences=[
            "Establishment of the qualitative theory of differential equations as the primary tool of Soviet cybernetics.",
            "Discovery and classification of bifurcation phenomena (Andronov–Hopf bifurcation) decades before modern chaos theory.",
            "Direct integration of mechanical, electrical, and control systems into a single geometric language.",
        ],
        technological_manifestations=[
            "Nonlinear radio transmitters, multivibrators, and radar pulse generators.",
            "Aerodynamic flutter suppression in high-speed fighter aircraft wings.",
            "Gyrocompass stabilization and ship rolling damping systems.",
        ],
        international_cross_pollination=[
            "Solomon Lefschetz championed Andronov's work in the US, translating the 1937 monograph into English in 1949.",
            "Directly influenced Stephen Smale and the American dynamical systems revolution in the 1960s.",
        ],
    ),
    EpistemicContrastDossier(
        contrast_id="CONTRAST_04_VLASOV_VS_BOLTZMANN",
        title="Vlasov Self-Consistent Collective Field vs. Boltzmann Collision-Dominated Kinetics",
        domain="Plasma Physics & Statistical Kinetics",
        soviet_emphasized_formulation=MathematicalFormulation(
            formulation_label="Vlasov-Bogolyubov Collective Kinetics School (MSU / Dubna)",
            key_authors=["Власов А. А.", "Боголюбов Н. Н."],
            foundational_publications=[
                "О вибрационных свойствах электронного газа (ЖЭТФ, 1938)",
                "Проблемы динамической теории в статистической физике (1946)",
            ],
            core_philosophical_stance=(
                "In high-temperature ionized plasmas, the Coulomb potential 1/r has infinite range. A charged particle "
                "interacts simultaneously with thousands of particles, creating a macroscopic self-consistent field. "
                "Collisionless collective interactions dominate over binary scattering, requiring coupled Vlasov–Maxwell dynamics."
            ),
            formal_mathematical_equation=(
                "del f / del t + v * grad_r f + (e/m)(E + [v, B]/c) * grad_v f = 0, with E, B sourced by rho = e integral f dv"
            ),
            underlying_assumptions=[
                "Long-range collective forces dominate over short-range binary collisions.",
                "The fundamental state is a continuous distribution function f(r, v, t) in 6-dimensional phase space.",
            ],
        ),
        alternative_contemporary_formulation=MathematicalFormulation(
            formulation_label="Boltzmann Binary Collision Transport Theory",
            key_authors=["Ludwig Boltzmann", "Sydney Chapman", "David Enskog"],
            foundational_publications=[
                "Vorlesungen über Gastheorie (1896)",
                "The Mathematical Theory of Non-Uniform Gases (Chapman & Cowling, 1939)",
            ],
            core_philosophical_stance=(
                "Gas and fluid kinetics are governed by short-range binary collisions between neutral particles. "
                "The time evolution of the distribution function is driven by the localized collision integral (Stosszahlansatz)."
            ),
            formal_mathematical_equation=(
                "df/dt + v * grad_r(f) = (del f / del t)_{coll} = integral (f' f_1' - f f_1) g sigma dOmega dv_1"
            ),
            underlying_assumptions=[
                "Dilute gas assumption: particles travel freely between brief pairwise elastic collisions.",
                "Molecular chaos (Stosszahlansatz): particle velocities before collision are completely uncorrelated.",
            ],
        ),
        relationship_nature="COLLECTIVE_FIELD_VS_COLLISION_KINETICS",
        chronological_relationship="NEW_PHYSICAL_REGIME",
        decisive_distinction=(
            "Boltzmann treats transport as discrete short-range pair collisions in free space; "
            "Vlasov proves that charged ensembles move through self-generated macroscopic fields where collective wave oscillations replace collision dissipation."
        ),
        epistemic_consequences=[
            "Discovery of collisionless plasma waves (Langmuir oscillations, ion-acoustic modes).",
            "Establishment of phase-space kinetic equations without a collision integral as fundamental physics.",
            "Development of the BBGKY hierarchy (Bogolyubov) providing exact microscopic closure for collective kinetics.",
        ],
        technological_manifestations=[
            "Tokamak magnetic confinement fusion reactors (Artsimovich, Shafranov).",
            "Relativistic gyrotrons, magnetrons, and traveling-wave tubes (TWT) for high-power military radar.",
            "Ionospheric radio wave propagation and over-the-horizon radar detection.",
        ],
        international_cross_pollination=[
            "Initially debated (including Landau's celebrated 1946 collisionless damping correction).",
            "Became the universally adopted worldwide foundation for modern plasma physics, fusion energy, and astrophysics.",
        ],
    ),
    EpistemicContrastDossier(
        contrast_id="CONTRAST_05_CHEBYSHEV_VS_TAYLOR",
        title="Chebyshev Global Minimax Approximation vs. Taylor Local Point Derivative Expansion",
        domain="Approximation Theory & Numerical Methods",
        soviet_emphasized_formulation=MathematicalFormulation(
            formulation_label="Chebyshev-Markov-Bernstein Constructive Approximation School",
            key_authors=["Чебышев П. Л.", "Марков А. А.", "Бернштейн С. Н."],
            foundational_publications=[
                "Теория механизмов, известных под названием параллелограммов (1854)",
                "О функциях, наименее уклоняющихся от нуля (1859)",
            ],
            core_philosophical_stance=(
                "Engineering mechanisms and numerical algorithms operate over finite, compact intervals [a, b]. "
                "Local derivatives at one point are irrelevant if peak error blows up at the edges. "
                "Optimal approximation must minimize the maximum error uniformly across the entire operating range (minimax)."
            ),
            formal_mathematical_equation="P_n^* = argmin_{P in P_n} max_{x in [a, b]} |f(x) - P(x)|, characterized by equioscillation",
            underlying_assumptions=[
                "Performance is evaluated by worst-case peak error on a compact domain, not asymptotic smoothness at a point.",
                "Equioscillation alternation theorem guarantees unique optimal polynomial representation.",
            ],
        ),
        alternative_contemporary_formulation=MathematicalFormulation(
            formulation_label="Taylor Local Derivative Series Expansion",
            key_authors=["Brook Taylor", "Colin Maclaurin", "Augustin-Louis Cauchy"],
            foundational_publications=[
                "Methodus Incrementorum Directa et Inversa (1715)",
                "Cours d'Analyse (1821)",
            ],
            core_philosophical_stance=(
                "Functions are approximated locally around an infinitesimal neighborhood of a single point x_0 "
                "by matching successive derivatives. The quality of approximation is asymptotic as x -> x_0."
            ),
            formal_mathematical_equation="f(x) = sum_{k=0}^n f^{(k)}(x_0)/k! * (x - x_0)^k + R_n(x)",
            underlying_assumptions=[
                "The function is infinitely differentiable in an open neighborhood around x_0.",
                "Local infinitesimal behavior accurately represents global function properties.",
            ],
        ),
        relationship_nature="GLOBAL_MINIMAX_VS_LOCAL_TAYLOR",
        chronological_relationship="ALTERNATIVE_APPROXIMATION_GOAL",
        decisive_distinction=(
            "Taylor calculus optimizes locally at a single point (derivatives match, but global error can be infinite); "
            "Chebyshev calculus optimizes globally across a compact interval, guaranteeing minimal peak error everywhere."
        ),
        epistemic_consequences=[
            "Establishment of constructive approximation theory and orthogonal polynomial theory (Chebyshev polynomials).",
            "Shift from qualitative symbolic analysis to guaranteed numerical error bounds on compact sets.",
            "Development of the Remez exchange algorithm (Kyiv, 1934) for automated polynomial synthesis.",
        ],
        technological_manifestations=[
            "Kinematic design of steam engine linkage parallelograms and mechanical linkages.",
            "Optimal analog and digital electronic filter synthesis (Chebyshev filters with equal-ripple passbands).",
            "Numerical microcode routines for transcendental function evaluation in Soviet BESM-6 supercomputers.",
        ],
        international_cross_pollination=[
            "Chebyshev's work became the bedrock of modern international approximation theory (e.g. Davis, Rivlin, Trefethen).",
            "Remez exchange algorithm forms the core of the international Parks-McClellan digital filter design standard.",
        ],
    ),
    EpistemicContrastDossier(
        contrast_id="CONTRAST_06_GELFAND_LEVITAN_VS_FORWARD_SPECTRAL",
        title="Gelfand-Levitan-Marchenko Transformation Operators vs. Classical Forward Spectral Theory",
        domain="Differential Operators & Spectral Reconstruction",
        soviet_emphasized_formulation=MathematicalFormulation(
            formulation_label="Gelfand-Levitan-Marchenko Inverse Spectral School (MIAN / LOMI / FTINT)",
            key_authors=["Гельфанд И. М.", "Левитан Б. М.", "Марченко В. А."],
            foundational_publications=[
                "Об определении дифференциального уравнения по его спектральной функции (ДАН СССР, 1951)",
                "Некоторые вопросы теории одномерных линейных дифференциальных операторов второго порядка (1952)",
            ],
            core_philosophical_stance=(
                "In real physical experiments, the interior potential q(x) is completely hidden. We can observe only "
                "the external spectrum (eigenvalues and norming constants). The fundamental problem is inverse: "
                "reconstruct the operator itself from its spectral measure via a triangular Volterra transformation operator I + K."
            ),
            formal_mathematical_equation=(
                "K(x, y) + F(x, y) + integral_0^x K(x, s) F(s, y) ds = 0, with q(x) = 2 dK(x, x)/dx"
            ),
            underlying_assumptions=[
                "The internal differential operator cannot be inspected directly, only external spectral data is accessible.",
                "Transformation operators translate the nonlinear problem of potential recovery into a linear integral equation.",
            ],
        ),
        alternative_contemporary_formulation=MathematicalFormulation(
            formulation_label="Classical Forward Resolvent & Spectral Theory",
            key_authors=["Hermann Weyl", "Marshall Stone", "John von Neumann"],
            foundational_publications=[
                "Über gewöhnliche Differentialgleichungen mit Singularitäten (1910)",
                "Linear Transformations in Hilbert Space (1932)",
            ],
            core_philosophical_stance=(
                "The primary mathematical direction is forward: given a known differential operator L = -d^2/dx^2 + q(x) "
                "and boundary conditions, compute its spectrum sigma(L), resolvent R(lambda), and eigenfunction expansion."
            ),
            formal_mathematical_equation="L y = lambda y => (L - lambda I)^(-1) = integral (dE_lambda) / (lambda' - lambda)",
            underlying_assumptions=[
                "The differential operator L and boundary conditions are completely specified a priori.",
                "The goal is characterizing the operator's forward spectral decomposition and functional calculus.",
            ],
        ),
        relationship_nature="INVERSE_TRANSFORMATION_VS_FORWARD_RESOLVENT",
        chronological_relationship="CO_DEVELOPED_INTERNATIONALLY",
        decisive_distinction=(
            "Forward spectral theory solves for the eigenvalues of a known operator; "
            "Gelfand, Levitan, and Marchenko prove that the operator itself can be uniquely reconstructed from its external eigenvalues and spectral density via linear Fredholm equations."
        ),
        epistemic_consequences=[
            "Discovery of the exact nonlinear-to-linear transformation for integrating soliton equations (KdV, NLS).",
            "Establishment of the Povzner–Levitan–Marchenko transformation operator as a universal tool of mathematical physics.",
            "Proving that spectral admissibility completely classifies which data can arise from physical second-order equations.",
        ],
        technological_manifestations=[
            "Nonlinear fiber optic soliton communications (Zakharov–Shabat systems).",
            "Quantum inverse scattering potentials for nuclear particle interactions (Faddeev equations).",
            "Acoustic impedance profile reconstruction for underwater submarine detection and ultrasonic medical scanning.",
        ],
        international_cross_pollination=[
            "Direct international co-development: Gardner, Greene, Kruskal, and Miura (1967) and Peter Lax (1968) in the US, "
            "working in fruitful interaction with Zakharov, Shabat, and Faddeev in the USSR, created the Inverse Scattering Transform (IST).",
        ],
    ),
]


class EpistemicContrastsAnalyzer:
    """Analyzes mathematical formulations emphasizing Soviet traditions compared with contemporary alternative formulations."""

    def __init__(self, registry: Optional[list[EpistemicContrastDossier]] = None) -> None:
        self.registry = registry or EPISTEMIC_CONTRASTS_REGISTRY

    def get_contrast_by_id(self, contrast_id: str) -> Optional[EpistemicContrastDossier]:
        for c in self.registry:
            if c.contrast_id == contrast_id:
                return c
        return None

    def export_contrasts_dossier(self, output_path: Path) -> dict[str, Any]:
        data = {
            "title": "SOVCTX Mathematical Formulations & Epistemic Contrasts Dossier",
            "perspective_note": (
                "Contrasts represent distinct mathematical and problem-solving formulations "
                "rather than national exclusivities. Soviet-emphasized formulations frequently "
                "interacted with and spread into international practice."
            ),
            "total_contrasts": len(self.registry),
            "contrasts": [c.to_dict() for c in self.registry],
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return data
