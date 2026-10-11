from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class TransferNode:
    entity: str
    entity_type: str  # MATHEMATICIAN, INSTITUTION, PUBLICATION, ENGINEERING_FIELD
    year: int
    role: str
    evidentiary_support: str = "DOCUMENTED"  # DOCUMENTED, CANDIDATE, SYNTHESIS


@dataclass
class EngineeringTransferLine:
    line_id: str
    label: str
    foundation_school: str
    foundational_authors: list[str]
    core_mathematical_formulation: str
    intermediate_transmission_institutes: list[str]
    applied_engineering_domains: list[str]
    operator_bridges: list[str]
    lineage_status: str  # DOCUMENTED_LINEAGE, HYPOTHESIZED_LINEAGE
    evidentiary_confidence: str  # HIGH, MEDIUM, CANDIDATE
    lineage_milestones: list[TransferNode]
    documented_sources: list[str]
    next_acquisition_targets: list[str]
    historical_summary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


ENGINEERING_TRANSFER_REGISTRY: list[EngineeringTransferLine] = [
    EngineeringTransferLine(
        line_id="LINE_01_INVERSE_GEOPHYSICS_RADAR",
        label="Tikhonov Inverse Theory to Geophysics & Radar Antenna Synthesis",
        foundation_school="TIKHONOV",
        foundational_authors=["Тихонов А. Н.", "Самарский А. А."],
        core_mathematical_formulation="A z = u (Fredholm first-kind) => min ||Az - u||^2 + alpha * Omega[z]",
        intermediate_transmission_institutes=[
            "МГУ им. Ломоносова",
            "ИПМ им. Келдыша АН СССР",
            "Институт физики Земли АН СССР",
        ],
        applied_engineering_domains=[
            "Магнитотеллурическое зондирование (МТЗ) в геофизике",
            "Синтез диаграмм направленности антенн и фазированных решеток (РЛС)",
            "Вычислительная газовая динамика и теплозащита космических аппаратов (гипотеза)",
        ],
        operator_bridges=["OP:INVERSE", "OP:REGULARIZE", "OP:FIELD_SYNTHESIS", "OP:INVERSE_DESIGN"],
        lineage_status="DOCUMENTED_LINEAGE",
        evidentiary_confidence="HIGH",
        lineage_milestones=[
            TransferNode("Тихонов А. Н.", "MATHEMATICIAN", 1943, "Formulates stability of inverse problems for geophysics in DAN SSSR", "DOCUMENTED"),
            TransferNode("ИФЗ / МГУ", "INSTITUTION", 1950, "Applies regularization to magnetotelluric geological prospecting", "DOCUMENTED"),
            TransferNode("Зелкин Е. Г.", "MATHEMATICIAN", 1963, "Publishes monograph 'Constructing a Radiating System from a Specified Radiation Pattern'", "DOCUMENTED"),
            TransferNode("ИПМ им. Келдыша", "INSTITUTION", 1965, "Samarsky and Tikhonov regularize finite-difference hydrocodes for re-entry and nuclear physics", "CANDIDATE"),
        ],
        documented_sources=["PUB:TIKHONOV_1943_ILLPOSED", "PUB:TIKHONOV_1963_ILLPOSED", "PUB:ZELKIN_1963"],
        next_acquisition_targets=[
            "Zelkin 1963 monograph full text (Сов. радио) for direct equation concordance",
            "IPM Keldysh technical reports on re-entry boundary layer finite difference schemes",
        ],
        historical_summary=(
            "Tikhonov's regularization arose directly from geophysical sounding where surface measurements "
            "must invert electromagnetic diffusion to recover underground conductivity layers. By 1963, this exact Fredholm "
            "operator framework was transferred by E. G. Zelkin into Soviet radar engineering to synthesize antenna "
            "apertures from desired radiation patterns without producing infinite reactive fields. The transfer to "
            "spacecraft heat-shield hydrocodes remains a plausible candidate lineage requiring bureau archival evidence."
        ),
    ),
    EngineeringTransferLine(
        line_id="LINE_02_DYNAMICS_AEROSPACE_CONTROL",
        label="Chebyshev-Lyapunov-Andronov-Pontryagin to Optimal Flight & Guidance Control",
        foundation_school="PONTRYAGIN",
        foundational_authors=["Чебышев П. Л.", "Ляпунов А. М.", "Андронов А. А.", "Понтрягин Л. С."],
        core_mathematical_formulation="dot(x) = f(x, u), u in U => H(x, psi, u) = (psi, f) => max_{u in U} H",
        intermediate_transmission_institutes=[
            "МИАН им. Стеклова",
            "ГИФТИ (Горький)",
            "Институт проблем управления (ИАТ АН СССР)",
        ],
        applied_engineering_domains=[
            "Теория оптимального управления летательными аппаратами",
            "Релейные системы ориентации спутников (bang-bang control)",
            "Траекторная оптимизация сближения на орбите (NASA Apollo 1963 / ОКБ-1)",
            "Теория дуального управления Фельдбаума",
        ],
        operator_bridges=["OP:STATE", "OP:STABILITY", "OP:CONTROL", "OP:OPTIMIZE", "OP:STRUCTURAL_ROBUSTNESS"],
        lineage_status="HYPOTHESIZED_LINEAGE",
        evidentiary_confidence="MEDIUM",
        lineage_milestones=[
            TransferNode("Ляпунов А. М.", "MATHEMATICIAN", 1892, "General Problem of the Stability of Motion", "DOCUMENTED"),
            TransferNode("Андронов А. А. & Понтрягин Л. С.", "MATHEMATICIAN", 1937, "Introduction of structural stability (rough systems)", "DOCUMENTED"),
            TransferNode("Понтрягин, Болтянский, Гамкрелидзе, Мищенко", "MATHEMATICIAN", 1956, "Discovery of the Maximum Principle with bounded control sets", "DOCUMENTED"),
            TransferNode("Красовский Н. Н.", "MATHEMATICIAN", 1959, "Theory of optimal regulation for aircraft and rocket trajectories", "CANDIDATE"),
            TransferNode("NASA MSC", "INSTITUTION", 1963, "Application of Pontryagin Maximum Principle to Apollo lunar orbit rendezvous trajectories", "DOCUMENTED"),
            TransferNode("ОКБ-1 / НИИ-885", "INSTITUTION", 1964, "Implementation of relay attitude control in lunar/interplanetary probes", "SYNTHESIS"),
        ],
        documented_sources=["HIST:LYAPUNOV_2007_KRYLOV", "PUB:PONTRYAGIN_1960_MAXIMUM", "BENCH_02_PONTRYAGIN", "BENCH_07_ANDRONOV_PONTRYAGIN"],
        next_acquisition_targets=[
            "Krasovskii N. N. 1959-1962 monographs on stabilization and flight dynamics",
            "NII-885 / OKB-1 technical documentation for Vostok/Soyuz orientation logic",
            "Feldbaum A. A. 1960 papers on dual control theory in Avtomatika i Telemekhanika",
        ],
        historical_summary=(
            "Starting from Lyapunov's phase-space stability and Andronov's non-linear oscillations, Pontryagin "
            "formalized optimal control with hard actuator constraints (u in U). While international adoption for space "
            "trajectories is documented (e.g. NASA's 1963 Apollo rendezvous studies), specific Soviet design bureau "
            "transfer chains to OKB-1/NII-885 guidance micro-logic remain candidate hypotheses awaiting primary source acquisition."
        ),
    ),
    EngineeringTransferLine(
        line_id="LINE_03_COLLECTIVE_PLASMA_FUSION",
        label="Vlasov-Bogolyubov Kinetic Theory to Tokamak Equilibrium & Plasma Confinement",
        foundation_school="VLASOV",
        foundational_authors=["Власов А. А.", "Боголюбов Н. Н."],
        core_mathematical_formulation="df/dt + v * grad_r(f) + (e/m)(E + [v, B]/c) * grad_v(f) = 0",
        intermediate_transmission_institutes=[
            "МГУ им. Ломоносова (физфак)",
            "ОИЯИ (Дубна)",
            "Институт атомной энергии им. Курчатова (ИАЭ)",
        ],
        applied_engineering_domains=[
            "Магнитное удержание плазмы в установках Токамак (Т-3, Т-4, Т-10)",
            "Равновесие плазменного шнура (уравнение Града — Шафранова)",
            "Высокочастотный нагрев плазмы и гиротроны NIRFI (гипотеза)",
        ],
        operator_bridges=["OP:SELF_CONSISTENT_FIELD", "OP:SELF_OSCILLATE", "OP:DYNAMIC_PARTITION"],
        lineage_status="DOCUMENTED_LINEAGE",
        evidentiary_confidence="HIGH",
        lineage_milestones=[
            TransferNode("Власов А. А.", "MATHEMATICIAN", 1938, "Formulates collisionless kinetic equation with self-consistent field", "DOCUMENTED"),
            TransferNode("Боголюбов Н. Н.", "MATHEMATICIAN", 1946, "Derives kinetic equations from BBGKY hierarchy of classical mechanics", "DOCUMENTED"),
            TransferNode("Шафранов В. Д.", "MATHEMATICIAN", 1958, "Derives Grad–Shafranov MHD equilibrium for toroidal plasma pinches", "DOCUMENTED"),
            TransferNode("Курчатов И. В. & Арцимович Л. А.", "INSTITUTION", 1968, "T-3 Tokamak achieves thermonuclear temperatures confirming magnetic confinement", "DOCUMENTED"),
            TransferNode("НИРФИ (Горький) / Салют", "INSTITUTION", 1970, "Development of gyrotrons for ECRH plasma heating", "CANDIDATE"),
        ],
        documented_sources=["PUB:VLASOV_1967_REPRODUCTION", "BENCH_03_VLASOV", "BENCH_06_BOGOLYUBOV"],
        next_acquisition_targets=[
            "Shafranov V. D. 1958 Atomnaya Energiya papers on toroidal plasma equilibrium",
            "Artsimovich L. A. 1969 IAEA Novosibirsk conference reports on T-3 Tokamak",
            "Gaponov-Grekhov A. V. NIRFI technical reports on relativistic gyrotrons",
        ],
        historical_summary=(
            "Vlasov's realization that long-range Coulomb interactions dominate over local pair collisions "
            "provided the macroscopic foundation for high-temperature plasma dynamics. Grounded by Bogolyubov's BBGKY "
            "hierarchy, this theory transferred directly through Shafranov and Artsimovich into Tokamak magnetic "
            "equilibrium and stability analysis, making this one of the most rigorously documented Soviet scientific transfers."
        ),
    ),
    EngineeringTransferLine(
        line_id="LINE_04_INVERSE_SPECTRAL_SOLITONS",
        label="Gelfand-Levitan-Marchenko Inverse Spectra to Solitons & Nonlinear Wave Optics",
        foundation_school="GELFAND",
        foundational_authors=["Гельфанд И. М.", "Левитан Б. М.", "Марченко В. А.", "Фаддеев Л. Д."],
        core_mathematical_formulation="K(x,y) + F(x,y) + integral_0^x K(x,s) F(s,y) ds = 0 => q(x) = 2 dK(x,x)/dx",
        intermediate_transmission_institutes=[
            "МИАН им. Стеклова",
            "ЛОМИ АН СССР (Ленинград)",
            "ФТИНТ АН УССР (Харьков)",
            "ИТФ им. Ландау (Черноголовка)",
        ],
        applied_engineering_domains=[
            "Нелинейная волоконная оптика и оптические солитоны",
            "Интегрирование нелинейных эволюционных уравнений (КдФ, НУШ)",
            "Синтез акустических и гидроакустических профилей скорости",
            "Квантовая обратная задача рассеяния",
        ],
        operator_bridges=["OP:INVERSE", "OP:SPECTRAL_INVERSE", "OP:SCATTER_INVERSE", "OP:CLASS_ADMISSIBILITY"],
        lineage_status="DOCUMENTED_LINEAGE",
        evidentiary_confidence="HIGH",
        lineage_milestones=[
            TransferNode("Гельфанд И. М. & Левитан Б. М.", "MATHEMATICIAN", 1951, "Derives linear integral equation reconstructing Sturm–Liouville operator", "DOCUMENTED"),
            TransferNode("Марченко В. А.", "MATHEMATICIAN", 1952, "Solves inverse problem of scattering theory for one-dimensional Schrodinger operator", "DOCUMENTED"),
            TransferNode("Фаддеев Л. Д.", "MATHEMATICIAN", 1959, "Establishes multi-dimensional inverse scattering and quantum three-body equations", "DOCUMENTED"),
            TransferNode("Gardner, Greene, Kruskal, Miura / Lax", "MATHEMATICIAN", 1968, "US discovery of inverse scattering transform for KdV", "DOCUMENTED"),
            TransferNode("Захаров В. Е. & Шабат А. Б.", "MATHEMATICIAN", 1971, "Applies inverse scattering transform (IST) to integrate nonlinear Schrodinger equation", "DOCUMENTED"),
        ],
        documented_sources=["PUB:GELFAND_LEVITAN_1951", "PUB:FADDEEV_1959", "PUB:GONCHAR_NOVIKOVA_HENKIN_1991"],
        next_acquisition_targets=[
            "Zakharov V. E., Shabat A. B. 1971 ZhETF paper on exact theory of 2D self-focusing",
            "Faddeev L. D., Takhtajan L. A. Hamiltonian Methods in the Theory of Solitons (1986)",
        ],
        historical_summary=(
            "The transformation operator method developed by Gelfand, Levitan, and Marchenko proved that "
            "an inaccessible spatial potential can be reconstructed exactly from boundary spectral data. "
            "In 1971, Zakharov and Shabat at the Landau Institute proved that this inverse spectral apparatus "
            "integrates nonlinear wave equations, establishing modern soliton theory in close, productive interaction "
            "with contemporary Western discoveries by Lax, Gardner, Greene, Kruskal, and Miura."
        ),
    ),
    EngineeringTransferLine(
        line_id="LINE_05_COMPLEX_CONTROL_CYBERNETICS",
        label="Bernstein-Gelfand-Tsetlin to Adaptive Automata & Variable-Structure Systems",
        foundation_school="GELFAND",
        foundational_authors=["Бернштейн Н. А.", "Гельфанд И. М.", "Цетлин М. Л.", "Глушков В. М."],
        core_mathematical_formulation="Dynamic partition of variables + non-local search tactics in complex state spaces",
        intermediate_transmission_institutes=[
            "Институт биофизики АН СССР",
            "Институт проблем передачи информации (ИППИ АН СССР)",
            "Институт кибернетики АН УССР (Киев)",
        ],
        applied_engineering_domains=[
            "Адаптивные конечные автоматы в случайных средах (автоматы Цетлина)",
            "Дискретные самоорганизующиеся системы с переменной структурой (Глушков)",
            "Алгоритмы координации многозвенных робототехнических манипуляторов",
        ],
        operator_bridges=["OP:TASK_REPRESENT", "OP:DYNAMIC_PARTITION", "OP:NONLOCAL_MOVE", "OP:STRUCTURAL_ADAPT"],
        lineage_status="DOCUMENTED_LINEAGE",
        evidentiary_confidence="HIGH",
        lineage_milestones=[
            TransferNode("Бернштейн Н. А.", "MATHEMATICIAN", 1947, "Formulates physiological levels of movement construction and motor synergy", "DOCUMENTED"),
            TransferNode("Гельфанд И. М. & Цетлин М. Л.", "MATHEMATICIAN", 1961, "Nonlocal search principles for complex multi-degree systems", "DOCUMENTED"),
            TransferNode("Цетлин М. Л.", "MATHEMATICIAN", 1961, "Automaton behavior in random media published in Avtomatika i Telemekhanika", "DOCUMENTED"),
            TransferNode("Глушков В. М.", "MATHEMATICIAN", 1962, "Self-organizing discrete systems with variable structure in Kiev Cybernetics Institute", "DOCUMENTED"),
        ],
        documented_sources=["PUB:GELFAND_TSETLIN_1961_NONLOCAL", "PUB:GELFAND_TSETLIN_1962", "PUB:GLUSHKOV_1962_SELF_ORGANIZING"],
        next_acquisition_targets=[
            "Tsetlin M. L. Complete collected works on automata theory (Nauka, 1969)",
            "Glushkov V. M. Synthesis of Digital Automata (Fizmatgiz, 1962)",
        ],
        historical_summary=(
            "Confronted with high degrees of freedom in physiological motor control, Gelfand and Tsetlin "
            "adapted Bernstein's motor synergies into a mathematical theory of non-local search and dynamic partitioning. "
            "This directly influenced Tsetlin's adaptive finite automata in random environments and Glushkov's "
            "variable-structure cybernetic architectures, supported by unambiguous primary documentary citations."
        ),
    ),
    EngineeringTransferLine(
        line_id="LINE_06_MINIMAX_APPROXIMATION_COMPUTING",
        label="Chebyshev-Markov Approximation to Soviet Digital Filters & Numerical Engines",
        foundation_school="CHEBYSHEV",
        foundational_authors=["Чебышев П. Л.", "Марков А. А."],
        core_mathematical_formulation="min_{P_n} max_{x in [a,b]} |f(x) - P_n(x)| => equioscillation alternation",
        intermediate_transmission_institutes=[
            "Санкт-Петербургский университет",
            "Императорская Академия Наук",
            "Математический институт им. В. А. Стеклова",
            "ИТМиВТ АН СССР (Лебедев)",
        ],
        applied_engineering_domains=[
            "Синтез кинематических шарнирных механизмов станков и двигателей",
            "Оптимальные аналоговые и цифровые фильтры с равномерной пульсацией",
            "Таблично-полиномиальные аппроксимации функций в ЭВМ БЭСМ (гипотеза)",
        ],
        operator_bridges=["OP:MINIMAX_APPROXIMATE", "OP:OPTIMIZE"],
        lineage_status="HYPOTHESIZED_LINEAGE",
        evidentiary_confidence="MEDIUM",
        lineage_milestones=[
            TransferNode("Чебышев П. Л.", "MATHEMATICIAN", 1853, "Theory of mechanisms known as parallelograms and uniform approximation", "DOCUMENTED"),
            TransferNode("Чебышев П. Л.", "MATHEMATICIAN", 1859, "Functions least deviating from zero and orthogonal polynomials", "DOCUMENTED"),
            TransferNode("Ремез Е. Я.", "MATHEMATICIAN", 1934, "Constructive exchange algorithms for Chebyshev polynomial approximation", "DOCUMENTED"),
            TransferNode("ИТМиВТ АН СССР", "INSTITUTION", 1967, "BESM-6 mathematical software library development", "CANDIDATE"),
        ],
        documented_sources=["PUB:CHEBYSHEV_1854_PARALLELOGRAMS", "BENCH_05_CHEBYSHEV", "BENCH_09_MARKOV"],
        next_acquisition_targets=[
            "BESM-6 standard subroutine library documentation (VTS AN SSSR)",
            "Remez E. Ya. 1935 monograph on Chebyshev numerical methods (AN USSR, Kyiv)",
            "Soviet radio engineering textbooks on Chebyshev passive/active filter synthesis",
        ],
        historical_summary=(
            "Chebyshev's uniform approximation originated in Watt steam engine linkage design. In the 20th century, "
            "his minimax equioscillation polynomials became foundational for analog and digital filter synthesis "
            "worldwide. While BESM-6 served as the premier scientific supercomputer for the Soviet space and nuclear "
            "programs, the specific claim that Chebyshev polynomials formed its core microcode remains a candidate "
            "hypothesis requiring verified compiler/microcode assembly listings."
        ),
    ),
]


class EngineeringTransferAnalyzer:
    """Traces and maps the transmission lines from pure mathematical schools to applied technology bureaus."""

    def __init__(self, registry: Optional[list[EngineeringTransferLine]] = None) -> None:
        self.registry = registry or ENGINEERING_TRANSFER_REGISTRY

    def get_line_by_id(self, line_id: str) -> Optional[EngineeringTransferLine]:
        for line in self.registry:
            if line.line_id == line_id:
                return line
        return None

    def export_transfer_dossier(self, output_path: Path) -> dict[str, Any]:
        data = {
            "title": "SOVCTX Mathematical Foundation to Applied Engineering Transfer Graph",
            "evidentiary_policy": (
                "Lines are strictly divided between DOCUMENTED_LINEAGE (supported by primary citations) "
                "and HYPOTHESIZED_LINEAGE (plausible mathematical foundations requiring primary bureau records)."
            ),
            "total_lines": len(self.registry),
            "documented_lines_count": sum(1 for line in self.registry if line.lineage_status == "DOCUMENTED_LINEAGE"),
            "hypothesized_lines_count": sum(1 for line in self.registry if line.lineage_status == "HYPOTHESIZED_LINEAGE"),
            "transfer_lines": [line.to_dict() for line in self.registry],
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return data
