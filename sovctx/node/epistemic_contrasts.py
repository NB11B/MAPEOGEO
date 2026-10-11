from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass
class MathematicalFormulation:
    tradition_label: str
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
    western_tradition: MathematicalFormulation
    soviet_tradition: MathematicalFormulation
    decisive_divergence_point: str
    epistemic_consequences: list[str]
    technological_manifestations: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


EPISTEMIC_CONTRASTS_REGISTRY: list[EpistemicContrastDossier] = [
    EpistemicContrastDossier(
        contrast_id="CONTRAST_01_TIKHONOV_VS_HADAMARD",
        title="Tikhonov Conditional Well-Posedness vs. Hadamard Rejection of Ill-Posedness",
        domain="Inverse Problems & Measurement Inversion",
        western_tradition=MathematicalFormulation(
            tradition_label="Classical Western (Hadamard School)",
            key_authors=["Jacques Hadamard"],
            foundational_publications=[
                "Sur les problèmes aux dérivées partielles et leur signification physique (1902)",
                "Le problème de Cauchy et les équations aux dérivées partielles linéaires hyperboliques (1932)",
            ],
            core_philosophical_stance=(
                "A mathematical problem representing a physical phenomenon must have a unique solution "
                "that depends continuously on the boundary/initial data (Hadamard well-posedness). Problems lacking "
                "continuous dependence (such as Cauchy problems for elliptic equations) are unphysical and mal-posed."
            ),
            formal_mathematical_equation="A z = u, exists! z in Z, ||delta z|| <= C * ||delta u|| (C < infinity)",
            underlying_assumptions=[
                "Exact forward observability without loss of high-frequency components.",
                "Discontinuity under noise indicates an incorrect mathematical model of reality.",
            ],
        ),
        soviet_tradition=MathematicalFormulation(
            tradition_label="Soviet Inverse Problem School (Tikhonov School)",
            key_authors=["Тихонов А. Н.", "Лаврентьев М. М.", "Иванов В. К."],
            foundational_publications=[
                "Об устойчивости обратных задач (ДАН СССР, 1943)",
                "О решении некорректно поставленных задач и методе регуляризации (ДАН СССР, 1963)",
            ],
            core_philosophical_stance=(
                "Ill-posed problems are the natural mathematical expression of indirect observation, remote sensing, "
                "and physical measurement. The unbounded inverse does not mean the problem is meaningless; it requires "
                "redefining solvability on compact subsets or via parameterized regularizing operators."
            ),
            formal_mathematical_equation=(
                "z_alpha = argmin_z (||A z - u_delta||^2 + alpha * Omega[z]), where alpha = alpha(delta) -> 0"
            ),
            underlying_assumptions=[
                "Physical measurements are inevitably corrupted by noise (delta > 0).",
                "A priori structural admissibility (compactness, smoothness, bounded energy) restores well-posedness.",
            ],
        ),
        decisive_divergence_point=(
            "Hadamard rejects ill-posed problems as unphysical; Tikhonov accepts ill-posedness as the defining "
            "condition of indirect measurement and invents regularizing operators to make reconstruction mathematically rigorous."
        ),
        epistemic_consequences=[
            "Establishment of conditional well-posedness (корректность по Тихонову) as an independent branch of mathematics.",
            "Development of parameter choice rules (Morozov discrepancy principle) replacing naive matrix inversion.",
            "Legitimization of inverse problem reconstruction across physics rather than forcing forward problem reformulations.",
        ],
        technological_manifestations=[
            "Magnetotelluric geophysical sounding and deep seismic oil/gas exploration.",
            "Zelkin antenna synthesis and phased-array radar pattern inversion.",
            "Medical tomography, deconvolution of blurred optical images, and non-destructive testing.",
        ],
    ),
    EpistemicContrastDossier(
        contrast_id="CONTRAST_02_PONTRYAGIN_VS_CLASSICAL_VARIATIONS",
        title="Pontryagin Maximum Principle on Closed Sets vs. Classical Smooth Variations",
        domain="Optimal Control & Trajectory Optimization",
        western_tradition=MathematicalFormulation(
            tradition_label="Classical Western Calculus of Variations (Euler-Lagrange, Weierstrass, Bellman)",
            key_authors=["Leonhard Euler", "Joseph-Louis Lagrange", "Karl Weierstrass", "Richard Bellman"],
            foundational_publications=[
                "Calculus of Variations (classical)",
                "Dynamic Programming (Bellman, 1957)",
            ],
            core_philosophical_stance=(
                "Optimal paths are found by setting the first variation of a smooth functional to zero (delta J = 0), "
                "requiring the control set to be open and controls to be smooth or piece-wise differentiable. "
                "Dynamic programming computes a continuous value function V(x) satisfying a Hamilton-Jacobi partial differential equation."
            ),
            formal_mathematical_equation="delta J = 0 => d/dt(del L / del dot(x)) - del L / del x = 0; del V / del t + min_u H = 0",
            underlying_assumptions=[
                "Control variables u vary freely in an open domain without hard saturation boundaries.",
                "The value function V(x, t) is continuously differentiable across all state space.",
            ],
        ),
        soviet_tradition=MathematicalFormulation(
            tradition_label="Soviet Optimal Control School (Pontryagin School)",
            key_authors=["Понтрягин Л. С.", "Болтянский В. Г.", "Гамкрелидзе Р. В.", "Мищенко Е. Ф."],
            foundational_publications=[
                "Принцип максимума в теории оптимальных процессов (ДАН СССР, 1958)",
                "Математическая теория оптимальных процессов (Наука, 1961)",
            ],
            core_philosophical_stance=(
                "Physical actuators (rudders, thrusters, valves) have hard structural constraints (u in U, where U is compact). "
                "Classical smooth variations fail when the optimal control sits permanently on the boundary of U. "
                "Needle-like variations (игольчатые вариации) establish that the realized control must maximize the Hamiltonian pointwise."
            ),
            formal_mathematical_equation=(
                "dot(x) = del H / del psi, dot(psi) = - del H / del x, with H(x, psi, u(t)) = max_{v in U} H(x, psi, v) a.e."
            ),
            underlying_assumptions=[
                "Actuators operate on bounded closed sets U (e.g. |u(t)| <= 1, full throttle or zero throttle).",
                "Controls may be discontinuous (bang-bang switching) with non-differentiable trajectory corners.",
            ],
        ),
        decisive_divergence_point=(
            "Classical variation assumes smooth variations inside open sets (delta J = 0); Pontryagin proves that for "
            "closed control sets U, the optimum lies on the boundary where classical derivatives do not vanish, requiring a Maximum Principle."
        ),
        epistemic_consequences=[
            "Rigorous mathematical proof that relay (bang-bang) control is time-optimal for linear systems.",
            "Establishment of symplectic Hamiltonian phase-space trajectories for engineering control.",
            "Unification of dynamics, differential games, and trajectory optimization without requiring Bellman smoothness.",
        ],
        technological_manifestations=[
            "Minimum-time ballistic missile trajectory guidance and interceptor steering.",
            "Orbital rendezvous and soft lunar/planetary landing descent sequences (Luna, Soyuz).",
            "Automatic flight stabilization and optimal submarine depth control.",
        ],
    ),
    EpistemicContrastDossier(
        contrast_id="CONTRAST_03_ANDRONOV_VS_BODE_NYQUIST",
        title="Andronov-Pontryagin Phase-Space Structural Stability vs. Bode/Nyquist Linear Frequency Response",
        domain="Dynamical Systems & Stabilization",
        western_tradition=MathematicalFormulation(
            tradition_label="Classical Western Servomechanism & Frequency Response School",
            key_authors=["Harry Nyquist", "Hendrik Bode", "Norbert Wiener"],
            foundational_publications=[
                "Regeneration Theory (Nyquist, 1932)",
                "Network Analysis and Feedback Amplifier Design (Bode, 1945)",
            ],
            core_philosophical_stance=(
                "System stability is governed by the frequency-domain transfer function G(s) of a linearized model. "
                "Stability margins (gain margin, phase margin) are evaluated by encirclement of the -1 point in the complex plane."
            ),
            formal_mathematical_equation="Y(s) = G(s) U(s), 1 + G(j omega) H(j omega) != 0, Nyquist contour integration",
            underlying_assumptions=[
                "Signals are small-amplitude perturbations about an isolated static equilibrium.",
                "Nonlinearities can be ignored or treated as minor parasitic harmonic distortions.",
            ],
        ),
        soviet_tradition=MathematicalFormulation(
            tradition_label="Soviet Non-Linear Dynamics & Structural Stability School",
            key_authors=["Андронов А. А.", "Понтрягин Л. С.", "Витт А. А.", "Хайкин С. Э."],
            foundational_publications=[
                "Грубые системы (ДАН СССР, 1937)",
                "Теория колебаний (Гостехиздат, 1937)",
            ],
            core_philosophical_stance=(
                "Real engineering oscillators and control systems are fundamentally nonlinear and operate on limit cycles. "
                "The essential question is not small-signal linear stability, but structural stability (грубость): "
                "does the qualitative topological structure of the phase portrait survive small perturbations in the vector field?"
            ),
            formal_mathematical_equation=(
                "dot(x) = P(x, y) + p(x, y), dot(y) = Q(x, y) + q(x, y), with topological homeomorphism preserving limit cycles"
            ),
            underlying_assumptions=[
                "Systems are intrinsically nonlinear with multiple attractors, saddles, and limit cycles.",
                "Engineering designs must operate safely across finite limit-cycle amplitudes, not just near zero.",
            ],
        ),
        decisive_divergence_point=(
            "Bode and Nyquist reduce systems to linear complex transfer functions G(s); Andronov and Pontryagin analyze "
            "nonlinear phase-space topologies, proving that self-oscillations correspond to isolated limit cycles that must be 'rough' (structurally stable)."
        ),
        epistemic_consequences=[
            "Establishment of the qualitative theory of differential equations as the primary tool of Soviet cybernetics.",
            "Discovery and classification of bifurcation phenomena (Andronov–Hopf bifurcation) before modern chaos theory.",
            "Direct integration of mechanical, electrical, and control systems into a single geometric language.",
        ],
        technological_manifestations=[
            "Nonlinear radio transmitters, multivibrators, and radar pulse generators.",
            "Aerodynamic flutter suppression in high-speed fighter aircraft wings.",
            "Gyrocompass stabilization and ship rolling damping systems.",
        ],
    ),
    EpistemicContrastDossier(
        contrast_id="CONTRAST_04_VLASOV_VS_BOLTZMANN",
        title="Vlasov Self-Consistent Collective Field vs. Western Collision-Dominated Boltzmann Kinetics",
        domain="Plasma Physics & Statistical Kinetics",
        western_tradition=MathematicalFormulation(
            tradition_label="Western Classical Kinetic Theory (Boltzmann, Chapman-Enskog)",
            key_authors=["Ludwig Boltzmann", "Sydney Chapman", "David Enskog"],
            foundational_publications=[
                "Weitere Studien über das Wärmegleichgewicht unter Gasmolekülen (1872)",
                "The Mathematical Theory of Non-Uniform Gases (1939)",
            ],
            core_philosophical_stance=(
                "Gas and fluid kinetics are governed by short-range binary collisions between neutral particles. "
                "The time evolution of the distribution function is driven by the localized collision integral (Stosszahlansatz)."
            ),
            formal_mathematical_equation="df/dt + v * grad_r(f) = (del f / del t)_{coll} = integral (f' f_1' - f f_1) g sigma dOmega dv_1",
            underlying_assumptions=[
                "Interparticle forces are short-ranged; particles travel along free paths between discrete collision events.",
                "Molecular chaos hypothesis: colliding particles are statistically uncorrelated before impact.",
            ],
        ),
        soviet_tradition=MathematicalFormulation(
            tradition_label="Soviet Plasma & Collective Field School (Vlasov School)",
            key_authors=["Власов А. А.", "Боголюubov Н. Н."],
            foundational_publications=[
                "О вибрационных свойствах электронного газа (ЖЭТФ, 1938)",
                "Теория многих частиц (Гостехиздат, 1950)",
            ],
            core_philosophical_stance=(
                "In high-temperature ionized plasmas, the Coulomb potential 1/r has infinite range. "
                "A charged particle interacts simultaneously with thousands of particles, creating a macroscopic self-consistent field. "
                "Collisionless collective interactions dominate over binary scattering, requiring coupled Vlasov–Maxwell dynamics."
            ),
            formal_mathematical_equation=(
                "del f / del t + v * grad_r f + (e/m)(E + [v, B]/c) * grad_v f = 0, with E, B sourced by rho = e integral f dv"
            ),
            underlying_assumptions=[
                "Long-range collective electromagnetic forces dominate over pair collisions (tau_coll >> tau_plasma).",
                "The system state is a collective density in 6D phase space coupled to its own generated electromagnetic fields.",
            ],
        ),
        decisive_divergence_point=(
            "Boltzmann treats transport as discrete short-range pair collisions in free space; Vlasov proves that charged "
            "ensembles move through self-generated macroscopic fields where collective wave oscillations replace collision dissipation."
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
    ),
    EpistemicContrastDossier(
        contrast_id="CONTRAST_05_CHEBYSHEV_VS_TAYLOR",
        title="Chebyshev Global Minimax Approximation vs. Taylor Local Point Derivative Expansion",
        domain="Approximation Theory & Numerical Methods",
        western_tradition=MathematicalFormulation(
            tradition_label="Classical Analytical Calculus (Taylor, Maclaurin, Weierstrass)",
            key_authors=["Brook Taylor", "Colin Maclaurin", "Augustin-Louis Cauchy"],
            foundational_publications=[
                "Methodus Incrementorum Directa et Inversa (Taylor, 1715)",
                "Cours d'Analyse (Cauchy, 1821)",
            ],
            core_philosophical_stance=(
                "Functions are approximated locally around an infinitesimal neighborhood of a single point x_0 "
                "by matching successive derivatives. The quality of approximation is asymptotic as x -> x_0."
            ),
            formal_mathematical_equation="f(x) = sum_{k=0}^n f^{(k)}(x_0)/k! * (x - x_0)^k + R_n(x)",
            underlying_assumptions=[
                "The function is infinitely differentiable (smooth) at the expansion point x_0.",
                "Error grows rapidly away from the expansion point; boundary behavior on finite intervals is unconstrained.",
            ],
        ),
        soviet_tradition=MathematicalFormulation(
            tradition_label="St. Petersburg / Soviet Constructive Approximation School (Chebyshev School)",
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
            formal_mathematical_equation=(
                "P_n^* = argmin_{P in P_n} max_{x in [a, b]} |f(x) - P(x)|, characterized by Chebyshev equioscillation"
            ),
            underlying_assumptions=[
                "The system must operate within guaranteed error bounds everywhere across an operating domain.",
                "Optimal finite representation is determined by Chebyshev alternation points (equal-ripple error).",
            ],
        ),
        decisive_divergence_point=(
            "Taylor calculus optimizes locally at a single point (derivatives match, but global error can be infinite); "
            "Chebyshev calculus optimizes globally across a compact interval, guaranteeing minimal peak error everywhere."
        ),
        epistemic_consequences=[
            "Establishment of constructive approximation theory and orthogonal polynomial theory (Chebyshev polynomials).",
            "Shift from qualitative symbolic analysis to guaranteed numerical error bounds on compact sets.",
            "Development of the Remez exchange algorithm for automated polynomial synthesis.",
        ],
        technological_manifestations=[
            "Kinematic design of steam engine linkage parallelograms and mechanical linkages.",
            "Optimal analog and digital electronic filter synthesis (Chebyshev filters with equal-ripple passbands).",
            "Numerical microcode routines for transcendental function evaluation in Soviet BESM-6 supercomputers.",
        ],
    ),
    EpistemicContrastDossier(
        contrast_id="CONTRAST_06_GELFAND_LEVITAN_VS_FORWARD_SPECTRAL",
        title="Gelfand-Levitan-Marchenko Transformation Operators vs. Classical Forward Spectral Theory",
        domain="Differential Operators & Spectral Reconstruction",
        western_tradition=MathematicalFormulation(
            tradition_label="Classical Western Forward Spectral School (Weyl, Stone, von Neumann)",
            key_authors=["Hermann Weyl", "Marshall Stone", "John von Neumann"],
            foundational_publications=[
                "Über gewöhnliche Differentialgleichungen mit Singularitäten (Weyl, 1910)",
                "Linear Transformations in Hilbert Space (Stone, 1932)",
            ],
            core_philosophical_stance=(
                "The primary mathematical direction is forward: given a known differential operator L = -d^2/dx^2 + q(x) "
                "and boundary conditions, compute its spectrum sigma(L), resolvent R(lambda), and eigenfunction expansion."
            ),
            formal_mathematical_equation="L y = lambda y => (L - lambda I)^(-1) = integral (dE_lambda) / (lambda' - lambda)",
            underlying_assumptions=[
                "The physical potential q(x) and operator coefficients are completely known a priori.",
                "Observations are derived consequences of the known mathematical operator.",
            ],
        ),
        soviet_tradition=MathematicalFormulation(
            tradition_label="Soviet Inverse Spectral School (Gelfand, Levitan, Marchenko)",
            key_authors=["Гельфанд И. М.", "Левитан Б. М.", "Марченко В. А."],
            foundational_publications=[
                "Об определении дифференциального уравнения по его спектральной функции (Известия АН СССР, 1951)",
                "Некоторые вопросы теории одномерных линейных дифференциальных операторов (Труды ММО, 1950)",
            ],
            core_philosophical_stance=(
                "In real physical experiments, the interior potential q(x) is completely hidden. "
                "We can observe only the external spectrum (eigenvalues and norming constants). "
                "The fundamental problem is inverse: reconstruct the operator itself from its spectral measure "
                "via a triangular Volterra transformation operator I + K."
            ),
            formal_mathematical_equation=(
                "K(x, y) + F(x, y) + integral_0^x K(x, s) F(s, y) ds = 0, with q(x) = 2 dK(x, x)/dx"
            ),
            underlying_assumptions=[
                "The internal differential operator is completely hidden and inaccessible to direct probing.",
                "The boundary spectral function rho(lambda) contains full structural information if admissibility conditions hold.",
            ],
        ),
        decisive_divergence_point=(
            "Forward spectral theory solves for the eigenvalues of a known operator; Gelfand, Levitan, and Marchenko "
            "prove that the operator itself can be uniquely reconstructed from its eigenvalues and spectral density via linear Fredholm equations."
        ),
        epistemic_consequences=[
            "Discovery of the exact nonlinear-to-linear transformation for integrating soliton equations (KdV, NLS).",
            "Establishment of the Povzner–Levitan–Marchenko transformation operator as the universal tool of mathematical physics.",
            "Proving that spectral admissibility completely classifies which data can arise from physical second-order equations.",
        ],
        technological_manifestations=[
            "Nonlinear fiber optic soliton communications (Zakharov–Shabat systems).",
            "Quantum inverse scattering potentials for nuclear particle interactions (Faddeev equations).",
            "Acoustic impedance profile reconstruction for underwater submarine detection and ultrasonic medical scanning.",
        ],
    ),
]


class EpistemicContrastsAnalyzer:
    """Interrogates and catalogs the 6 foundational epistemological contrasts between Soviet and Western science."""

    def __init__(self, registry: Optional[list[EpistemicContrastDossier]] = None) -> None:
        self.registry = registry or EPISTEMIC_CONTRASTS_REGISTRY

    def get_contrast_by_id(self, contrast_id: str) -> Optional[EpistemicContrastDossier]:
        for c in self.registry:
            if c.contrast_id == contrast_id:
                return c
        return None

    def export_contrasts_dossier(self, output_path: Path) -> dict[str, Any]:
        data = {
            "title": "SOVCTX Epistemic Contrasts: Distinctive Soviet vs. Western Problem Formulations",
            "total_contrasts": len(self.registry),
            "contrasts": [c.to_dict() for c in self.registry],
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return data
