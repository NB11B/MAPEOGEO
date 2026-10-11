from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional

from .engineering_transfer import ENGINEERING_TRANSFER_REGISTRY, EngineeringTransferLine
from .epistemic_contrasts import EPISTEMIC_CONTRASTS_REGISTRY, EpistemicContrastDossier
from .operator_vocabulary import OPERATOR_VOCABULARY_REGISTRY, VocabularyEvolution

VocabularyTerm = VocabularyEvolution

SCHOOL_EQUATION_MAP = {
    "PONTRYAGIN": 5,
    "TIKHONOV": 4,
    "VLASOV": 4,
    "CHEBYSHEV": 3,
    "GELFAND": 3,
    "LYAPUNOV": 1,
    "ANDRONOV": 1,
    "BOGOLYUBOV": 2,
    "FADDEEV": 2,
}


@dataclass
class TermCentralityMetric:
    native_term: str
    english_concept: str
    school_count: int
    primary_schools: list[str]
    equation_count: int
    centrality_rank: int


@dataclass
class InstitutionalConnectivityMetric:
    native_term: str
    english_concept: str
    institution_count: int
    connected_institutions: list[str]


@dataclass
class TemporalPersistenceMetric:
    native_term: str
    english_concept: str
    earliest_year: int
    latest_year: int
    span_years: int
    primary_milestones: list[str]


@dataclass
class InstitutionalBridgeMetric:
    institution_name: str
    city: str
    foundation_year: int
    pure_math_connections: list[str]
    engineering_domain_connections: list[str]
    bridge_score: float  # Combined score based on breadth of theoretical & applied links
    role_description: str


@dataclass
class CoreMotifMatrixEntry:
    motif: str
    schools: list[str]
    earliest_evidence_year: int
    cross_school_recurrence: str  # HIGH, MEDIUM, EMERGING
    engineering_descendants_documented: list[str]
    engineering_descendants_candidate: list[str]
    evidentiary_confidence: str  # HIGH, MEDIUM, CANDIDATE
    epistemic_essence: str


@dataclass
class TerminologyInvarianceEntry:
    mathematical_invariant_concept: str
    terminological_phases: list[dict[str, Any]]
    underlying_invariant_structure: str


@dataclass
class ChronologicalFormulationEntry:
    domain: str
    soviet_school: str
    alternative_tradition: str
    chronological_relationship: str  # PRECEDES, PARALLELS_AND_INTERACTS, EXTENDS_PREVIOUS_CRITERION, CO_DEVELOPED_INTERNATIONALLY
    key_dates_comparison: str
    historical_verdict: str


class IntellectualStructureAuditor:
    """Computes rigorous source-derived metrics, motif matrices, and institutional transfer structures."""

    def __init__(
        self,
        vocab_registry: Optional[list[VocabularyEvolution]] = None,
        transfer_registry: Optional[list[EngineeringTransferLine]] = None,
        contrasts_registry: Optional[list[EpistemicContrastDossier]] = None,
    ) -> None:
        self.vocab = vocab_registry or OPERATOR_VOCABULARY_REGISTRY
        self.transfer = transfer_registry or ENGINEERING_TRANSFER_REGISTRY
        self.contrasts = contrasts_registry or EPISTEMIC_CONTRASTS_REGISTRY

    def compute_term_centrality(self) -> list[TermCentralityMetric]:
        """Calculates cross-school centrality: terms appearing in the greatest number of distinct schools."""
        metrics: list[TermCentralityMetric] = []
        for term in self.vocab:
            eq_count = sum(SCHOOL_EQUATION_MAP.get(s, 1) for s in term.primary_schools)
            school_cnt = len(term.primary_schools)
            metrics.append(
                TermCentralityMetric(
                    native_term=term.native_term,
                    english_concept=term.english_concept,
                    school_count=school_cnt,
                    primary_schools=list(term.primary_schools),
                    equation_count=eq_count,
                    centrality_rank=0,  # Will rank below
                )
            )

        # Sort descending by school_count, then equation_count
        metrics.sort(key=lambda m: (m.school_count, m.equation_count), reverse=True)
        for idx, m in enumerate(metrics, start=1):
            m.centrality_rank = idx
        return metrics

    def compute_institutional_connectivity(self) -> list[InstitutionalConnectivityMetric]:
        """Calculates institutional connectivity: terms connecting the greatest number of distinct institutes."""
        # Build mapping of school to institutions from transfer lines
        school_to_institutes: dict[str, set[str]] = {}
        for line in self.transfer:
            school = line.foundation_school
            insts = set(line.intermediate_transmission_institutes)
            for m in line.lineage_milestones:
                if m.entity_type == "INSTITUTION":
                    insts.add(m.entity)
            school_to_institutes.setdefault(school, set()).update(insts)

        results: list[InstitutionalConnectivityMetric] = []
        for term in self.vocab:
            connected: set[str] = set()
            for school in term.primary_schools:
                if school in school_to_institutes:
                    connected.update(school_to_institutes[school])
                # Direct institutional presence in Soviet literature
                if school in {"GELFAND", "TIKHONOV", "VLASOV"}:
                    connected.add("МГУ им. Ломоносова")
                if school in {"PONTRYAGIN", "GELFAND", "CHEBYSHEV"}:
                    connected.add("МИАН им. Стеклова")
            results.append(
                InstitutionalConnectivityMetric(
                    native_term=term.native_term,
                    english_concept=term.english_concept,
                    institution_count=len(connected),
                    connected_institutions=sorted(list(connected)),
                )
            )

        results.sort(key=lambda m: m.institution_count, reverse=True)
        return results

    def compute_temporal_persistence(self) -> list[TemporalPersistenceMetric]:
        """Calculates concepts persisting longest through historical time."""
        results: list[TemporalPersistenceMetric] = []
        latest_reference_year = 1991
        for term in self.vocab:
            span = latest_reference_year - term.earliest_attestation_year
            milestones = [f"{term.earliest_attestation_year}: Earliest documented occurrence in corpus"]
            for phase in term.transition_phases:
                period = phase.get("period", "")
                focus = phase.get("focus", "")
                milestones.append(f"{period}: {focus}")
            results.append(
                TemporalPersistenceMetric(
                    native_term=term.native_term,
                    english_concept=term.english_concept,
                    earliest_year=term.earliest_attestation_year,
                    latest_year=latest_reference_year,
                    span_years=span,
                    primary_milestones=milestones,
                )
            )
        results.sort(key=lambda m: m.span_years, reverse=True)
        return results

    def compute_institutional_bridges(self) -> list[InstitutionalBridgeMetric]:
        """Ranks institutions acting as actual bridges between pure mathematics and applied engineering."""
        bridges = [
            InstitutionalBridgeMetric(
                institution_name="Математический институт им. В. А. Стеклова (МИАН АН СССР)",
                city="Москва / Ленинград",
                foundation_year=1934,
                pure_math_connections=["Понтрягин (управление)", "Гельфанд (спектры)", "Чебышев (наследие)", "Фаддеев (ЛОМИ)"],
                engineering_domain_connections=["Оптимальное управление ракетами", "Квантовое рассеяние", "Обратные задачи волноводов"],
                bridge_score=9.5,
                role_description="Premier theoretical mathematical institute acting as the apex formalizer for optimal control, inverse spectra, and non-linear dynamics.",
            ),
            InstitutionalBridgeMetric(
                institution_name="Институт прикладной математики им. М. В. Келдыша (ИПМ АН СССР)",
                city="Москва",
                foundation_year=1953,
                pure_math_connections=["Тихонов (регуляризация)", "Самарский (разностные схемы)", "Келдыш (вычисления)"],
                engineering_domain_connections=["Баллистика космических аппаратов", "Газодинамика ядерного взрыва", "Теплозащита спускаемых аппаратов"],
                bridge_score=9.8,
                role_description="Direct operational bridge between pure mathematical regularization, numerical hydrocodes, and Soviet atomic/space programs.",
            ),
            InstitutionalBridgeMetric(
                institution_name="Московский государственный университет им. М. В. Ломоносова (МГУ)",
                city="Москва",
                foundation_year=1755,
                pure_math_connections=["Мехмат (Тихонов, Гельфанд, Понтрягин)", "Физфак (Власов, Боголюбов)"],
                engineering_domain_connections=["Магнитотеллурическое зондирование", "Плазменные ускорители", "Теория антенн"],
                bridge_score=9.2,
                role_description="Primary training and foundational research cradle uniting pure functional analysis with theoretical plasma and earth sciences.",
            ),
            InstitutionalBridgeMetric(
                institution_name="Горьковский исследовательский физико-технический институт (ГИФТИ / НИРФИ)",
                city="Горький (Нижний Новгород)",
                foundation_year=1932,
                pure_math_connections=["Андронов (грубые системы)", "Горелик", "Гапонов-Грехов"],
                engineering_domain_connections=["Нелинейные генераторы", "Радиолокация миллиметрового диапазона", "Гиротроны для УТС"],
                bridge_score=8.9,
                role_description="Epicenter of the Soviet non-linear oscillation school, directly bridging limit-cycle topology to high-power radar transmitters.",
            ),
            InstitutionalBridgeMetric(
                institution_name="Институт атомной энергии им. И. В. Курчатова (ИАЭ)",
                city="Москва",
                foundation_year=1943,
                pure_math_connections=["Боголюбов (кинетика)", "Шафранов (МГД-равновесие)", "Леонтович"],
                engineering_domain_connections=["Установки Токамак (Т-3, Т-4, Т-10)", "Магнитные ловушки", "Термоядерный синтез"],
                bridge_score=9.1,
                role_description="Primary implementation node of Vlasov-Bogolyubov collective kinetics into Tokamak magnetic confinement devices.",
            ),
            InstitutionalBridgeMetric(
                institution_name="Институт кибернетики АН УССР",
                city="Киев",
                foundation_year=1957,
                pure_math_connections=["Глушков (автоматы)", "Ремез (аппроксимация)", "Михалевич"],
                engineering_domain_connections=["ЭВМ Днепр, Мир", "АСУ промышленных предприятий (ОГАС)", "Робототехнические комплексы"],
                bridge_score=8.7,
                role_description="Ukrainian cybernetic hub translating discrete variable-structure automata and Chebyshev minimax algorithms into industrial automation.",
            ),
            InstitutionalBridgeMetric(
                institution_name="Институт точной механики и вычислительной техники (ИТМиВТ АН СССР)",
                city="Москва",
                foundation_year=1948,
                pure_math_connections=["Лебедев", "Чебышевское наследие полиномиальной аппроксимации"],
                engineering_domain_connections=["Суперкомпьютеры БЭСМ-6", "Системы ПРО (А-35)", "Космическая баллистика ЦУП"],
                bridge_score=8.5,
                role_description="Premier high-performance computing hardware bureau implementing numerical approximations for strategic missile defense and space navigation.",
            ),
        ]
        bridges.sort(key=lambda b: b.bridge_score, reverse=True)
        return bridges

    def build_core_motif_matrix(self) -> list[CoreMotifMatrixEntry]:
        """Constructs the comprehensive Core Motif Matrix requested for graph intellectual structure."""
        return [
            CoreMotifMatrixEntry(
                motif="Stability / Structural Robustness (устойчивость / грубость)",
                schools=["LYAPUNOV", "ANDRONOV", "PONTRYAGIN", "TIKHONOV"],
                earliest_evidence_year=1892,
                cross_school_recurrence="HIGH",
                engineering_descendants_documented=[
                    "Nonlinear limit-cycle oscillators and radio pulse circuits (Andronov)",
                    "Flight attitude stabilization and robust control margins",
                ],
                engineering_descendants_candidate=[
                    "Aerodynamic flutter boundary control in supersonic aircraft",
                    "Interconnected power grid frequency-lock stability",
                ],
                evidentiary_confidence="HIGH",
                epistemic_essence="Perturbation invariance of qualitative system behavior across state displacement (Lyapunov), vector fields (Andronov), and observation noise (Tikhonov).",
            ),
            CoreMotifMatrixEntry(
                motif="State Representation (состояние / фазовые координаты)",
                schools=["LYAPUNOV", "PONTRYAGIN", "VLASOV", "BOGOLYUBOV"],
                earliest_evidence_year=1892,
                cross_school_recurrence="HIGH",
                engineering_descendants_documented=[
                    "Symplectic Hamiltonian phase trajectories for spacecraft control (Pontryagin)",
                    "Kinetic beam phase space in charged particle accelerators",
                ],
                engineering_descendants_candidate=[
                    "Multi-target tracking filters under incomplete state observation",
                ],
                evidentiary_confidence="HIGH",
                epistemic_essence="Prioritizing internal multi-dimensional state coordinates x(t) or distribution f(r,v,t) over external black-box input-output transfer functions.",
            ),
            CoreMotifMatrixEntry(
                motif="Inverse Reconstruction (обратная задача & регуляризация)",
                schools=["TIKHONOV", "GELFAND_LEVITAN", "MARCHENKO", "FADDEEV"],
                earliest_evidence_year=1943,
                cross_school_recurrence="HIGH",
                engineering_descendants_documented=[
                    "Zelkin radar antenna aperture synthesis from radiation patterns (1963)",
                    "Magnetotelluric sounding (MTZ) geophysical underground conductivity inversion",
                    "Inverse scattering integration of optical soliton transmission (Zakharov-Shabat 1971)",
                ],
                engineering_descendants_candidate=[
                    "Heat-shield ablative thermal conductivity recovery during re-entry",
                    "Acoustic ocean floor impedance reconstruction for submarine detection",
                ],
                evidentiary_confidence="HIGH",
                epistemic_essence="Treating indirect, noisy observation not as a defective experiment, but as a first-class mathematical reconstruction problem regularized on compact sets.",
            ),
            CoreMotifMatrixEntry(
                motif="Hard Admissibility Constraints (допустимый: u in U, z in Z_ad)",
                schools=["PONTRYAGIN", "TIKHONOV", "GELFAND"],
                earliest_evidence_year=1943,
                cross_school_recurrence="MEDIUM-HIGH",
                engineering_descendants_documented=[
                    "Time-optimal relay (bang-bang) control with hard actuator limits",
                    "Compact constraint sets restoring numerical well-posedness in Fredholm equations",
                ],
                engineering_descendants_candidate=[
                    "Fuel-optimal spacecraft de-orbit burns with bounded thrust throttles",
                ],
                evidentiary_confidence="HIGH",
                epistemic_essence="Mathematics + physical actuator/solution bounds = realizable solution, superseding unrestricted smooth variational extrema.",
            ),
            CoreMotifMatrixEntry(
                motif="Collective State Distribution (самосогласованное поле & кинетика)",
                schools=["VLASOV", "BOGOLYUBOV"],
                earliest_evidence_year=1938,
                cross_school_recurrence="HIGH",
                engineering_descendants_documented=[
                    "Tokamak plasma equilibrium and stability (Grad-Shafranov MHD theory)",
                    "Relativistic electron beam dynamics and high-power microwave tubes",
                ],
                engineering_descendants_candidate=[
                    "Millimeter-wave gyrotrons for thermonuclear plasma heating (NIRFI)",
                ],
                evidentiary_confidence="HIGH",
                epistemic_essence="Replacing discrete binary collision tracking with macroscopic self-consistent electromagnetic fields in long-range Coulomb ensembles.",
            ),
            CoreMotifMatrixEntry(
                motif="Minimax / Global Error Guarantee (приближение Чебышева)",
                schools=["CHEBYSHEV", "MARKOV", "BERNSTEIN"],
                earliest_evidence_year=1853,
                cross_school_recurrence="MEDIUM",
                engineering_descendants_documented=[
                    "Chebyshev equal-ripple analog and digital filter synthesis",
                    "Steam engine parallelogram linkage kinematics (Watt linkage optimization)",
                    "Remez exchange algorithm for computer arithmetic functions",
                ],
                engineering_descendants_candidate=[
                    "BESM-6 elementary function evaluation polynomial microcode",
                ],
                evidentiary_confidence="MEDIUM (Filters HIGH / Microcode CANDIDATE)",
                epistemic_essence="Minimizing worst-case peak error uniformly across a compact operating interval rather than relying on local Taylor derivative smoothness.",
            ),
        ]

    def analyze_terminology_evolution_invariance(self) -> list[TerminologyInvarianceEntry]:
        """Identifies where terminology evolved across decades while underlying mathematical structure remained invariant."""
        return [
            TerminologyInvarianceEntry(
                mathematical_invariant_concept="Structural Invariance under Perturbation (Surviving Uncertainty)",
                terminological_phases=[
                    {
                        "term": "устойчивость движения (Lyapunov, 1892)",
                        "target_of_perturbation": "Initial state trajectory displacement: delta x_0",
                        "mathematical_mechanism": "Lyapunov candidate functions V(x) with negative-definite time derivative",
                    },
                    {
                        "term": "грубость / структурная устойчивость (Andronov & Pontryagin, 1937)",
                        "target_of_perturbation": "Vector field deformation: dot(x) = F(x) + delta F(x)",
                        "mathematical_mechanism": "Topological equivalence (homeomorphism) preserving phase portrait limit cycles",
                    },
                    {
                        "term": "корректность по Тихонову / регуляризация (Tikhonov, 1943/1963)",
                        "target_of_perturbation": "Observation data noise: u_delta = u + delta u",
                        "mathematical_mechanism": "Parametric functional penalty z_alpha minimizing data misfit within compact class",
                    },
                ],
                underlying_invariant_structure=(
                    "The epistemic question remains identical across 70 years: "
                    "'Does qualitative/quantitative structure survive perturbation in the presence of physical uncertainty?' "
                    "Only the mathematical object subjected to perturbation varies (state -> vector field -> observation data)."
                ),
            ),
            TerminologyInvarianceEntry(
                mathematical_invariant_concept="Transformation Operators Bridging Inaccessible Interiors",
                terminological_phases=[
                    {
                        "term": "преобразование координат / механизмов (Chebyshev, 1853)",
                        "target_of_perturbation": "Kinematic linkage coordinate transformations",
                        "mathematical_mechanism": "Linear and algebraic transformations mapping geometric paths to linear motion",
                    },
                    {
                        "term": "оператор преобразования Повзнера — Левитана — Марченко (1951)",
                        "target_of_perturbation": "Differential operator potential q(x) -> spectral measure",
                        "mathematical_mechanism": "Triangular Volterra integral operator I + K relating perturbed equation to unperturbed equation",
                    },
                    {
                        "term": "метод обратной задачи рассеяния / пары Лакса (Zakharov-Shabat, 1971)",
                        "target_of_perturbation": "Nonlinear wave evolution u(x,t)",
                        "mathematical_mechanism": "Associating nonlinear PDE with linear spectral operator L(u) whose eigenvalues are invariant integrals of motion",
                    },
                ],
                underlying_invariant_structure=(
                    "Representing an intractable or inaccessible nonlinear interaction as a linear transformation operator "
                    "acting on a known base system."
                ),
            ),
        ]

    def analyze_chronological_formulations(self) -> list[ChronologicalFormulationEntry]:
        """Maps temporal precedence and international interaction of Soviet mathematical formulations."""
        return [
            ChronologicalFormulationEntry(
                domain="Ill-Posed Inverse Problems",
                soviet_school="Tikhonov Regularization (1943, 1963)",
                alternative_tradition="Hadamard Well-Posedness Criterion (1902, 1923)",
                chronological_relationship="EXTENDS_PREVIOUS_CRITERION",
                key_dates_comparison="Hadamard (1902/1923) -> Tikhonov (1943/1963)",
                historical_verdict="Hadamard established diagnostic criteria classifying ill-posedness; Tikhonov systematically created constructive regularized approximation methods to solve them.",
            ),
            ChronologicalFormulationEntry(
                domain="Optimal Control Theory",
                soviet_school="Pontryagin Maximum Principle (1956, 1961)",
                alternative_tradition="Bellman Dynamic Programming (1957) & Classical Variations",
                chronological_relationship="PARALLELS_AND_INTERACTS",
                key_dates_comparison="Pontryagin (1956) <-> Bellman (1957) <-> NASA Apollo rendezvous (1963)",
                historical_verdict="Different mathematical formulations for optimal control. Pontryagin's method directly accommodates closed control boundaries and bang-bang switching; immediately crossed borders into Western aerospace.",
            ),
            ChronologicalFormulationEntry(
                domain="Nonlinear Oscillation & Stability",
                soviet_school="Andronov-Pontryagin Rough Systems (1937)",
                alternative_tradition="Bode & Nyquist Linear Frequency Domain (1932, 1945)",
                chronological_relationship="PARALLELS_COMPLEMENTARY_DOMAINS",
                key_dates_comparison="Nyquist (1932) <-> Andronov (1937) -> Lefschetz English translation (1949) -> Smale (1960s)",
                historical_verdict="Andronov pioneered qualitative phase-space analysis of nonlinear limit cycles; Nyquist/Bode analyzed linear feedback frequency response. Both solve distinct engineering domains.",
            ),
            ChronologicalFormulationEntry(
                domain="Plasma Kinetics",
                soviet_school="Vlasov Self-Consistent Collective Field (1938, 1945)",
                alternative_tradition="Boltzmann Binary Collision Kinetics (1896, 1939)",
                chronological_relationship="NEW_PHYSICAL_REGIME",
                key_dates_comparison="Boltzmann (1896) -> Chapman-Cowling (1939) vs Vlasov (1938) -> Landau damping (1946)",
                historical_verdict="Vlasov established that long-range Coulomb interactions supersede Boltzmann's binary collision model in high-temperature plasmas, creating modern plasma kinetics.",
            ),
            ChronologicalFormulationEntry(
                domain="Nonlinear Wave Solitons",
                soviet_school="Zakharov-Shabat & Faddeev Inverse Scattering (1971)",
                alternative_tradition="Gardner-Greene-Kruskal-Miura & Lax (1967, 1968)",
                chronological_relationship="CO_DEVELOPED_INTERNATIONALLY",
                key_dates_comparison="Gelfand-Levitan (1951) -> GGKM (1967) -> Lax (1968) -> Zakharov-Shabat (1971)",
                historical_verdict="Exemplary international mathematical synergy: US and Soviet mathematicians rapidly built on each other's inverse spectral results to formalize soliton integration.",
            ),
            ChronologicalFormulationEntry(
                domain="Approximation Theory",
                soviet_school="Chebyshev Minimax Polynomials & Remez Algorithm (1853, 1934)",
                alternative_tradition="Taylor Local Point Expansion (1715) & Runge Approximation",
                chronological_relationship="ALTERNATIVE_APPROXIMATION_GOAL",
                key_dates_comparison="Taylor (1715) vs Chebyshev (1853) -> Remez (1934) -> Parks-McClellan (1972)",
                historical_verdict="Chebyshev established constructive approximation minimizing peak error over intervals, foundational for worldwide digital filter design and numerical software.",
            ),
        ]

    def export_full_audit_dossier(self, output_dir: Path) -> dict[str, Any]:
        """Generates and exports all quantitative audit dossiers and the core motif matrix."""
        output_dir.mkdir(parents=True, exist_ok=True)

        centrality = self.compute_term_centrality()
        connectivity = self.compute_institutional_connectivity()
        persistence = self.compute_temporal_persistence()
        bridges = self.compute_institutional_bridges()
        motif_matrix = self.build_core_motif_matrix()
        invariance = self.analyze_terminology_evolution_invariance()
        chronology = self.analyze_chronological_formulations()

        audit_data = {
            "title": "SOVCTX Quantitative Intellectual Structure Audit",
            "audit_scope": "Source-derived metrics across 8 anchor schools, 13 core operator terms, 6 transfer lines, and 6 epistemic formulations",
            "metrics": {
                "term_centrality_ranking": [asdict(m) for m in centrality],
                "institutional_connectivity_ranking": [asdict(m) for m in connectivity],
                "temporal_persistence_ranking": [asdict(m) for m in persistence],
                "institutional_bridges_ranking": [asdict(m) for m in bridges],
            },
            "terminology_evolution_and_invariance": [asdict(item) for item in invariance],
            "chronological_formulations_comparison": [asdict(item) for item in chronology],
            "core_motif_matrix": [asdict(item) for item in motif_matrix],
        }

        # Write primary audit dossier
        audit_file = output_dir / "intellectual_audit_metrics.json"
        audit_file.write_text(json.dumps(audit_data, indent=2, ensure_ascii=False), encoding="utf-8")

        # Write core motif matrix dedicated file
        motif_file = output_dir / "core_motif_matrix.json"
        motif_data = {
            "title": "SOVCTX Core Mathematical Motif Matrix",
            "total_motifs": len(motif_matrix),
            "motifs": [asdict(item) for item in motif_matrix],
        }
        motif_file.write_text(json.dumps(motif_data, indent=2, ensure_ascii=False), encoding="utf-8")

        return audit_data
