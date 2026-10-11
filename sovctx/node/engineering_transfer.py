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
    lineage_milestones: list[TransferNode]
    documented_sources: list[str]
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
            "Вычислительная газовая динамика и теплозащита космических аппаратов",
        ],
        operator_bridges=["OP:INVERSE", "OP:REGULARIZE", "OP:FIELD_SYNTHESIS", "OP:INVERSE_DESIGN"],
        lineage_milestones=[
            TransferNode("Тихонов А. Н.", "MATHEMATICIAN", 1943, "Formulates stability of inverse problem for geophysics in DAN SSSR"),
            TransferNode("ИФЗ / МГУ", "INSTITUTION", 1950, "Applies regularization to magnetotelluric geological prospecting"),
            TransferNode("Зелкин Е. Г.", "MATHEMATICIAN", 1963, "Publishes monograph 'Constructing a Radiating System from a Specified Radiation Pattern'"),
            TransferNode("ИПМ им. Келдыша", "INSTITUTION", 1965, "Samarsky and Tikhonov regularize finite-difference hydrocodes for re-entry and nuclear physics"),
        ],
        documented_sources=["PUB:TIKHONOV_1943_ILLPOSED", "PUB:TIKHONOV_1963_ILLPOSED", "PUB:ZELKIN_1963"],
        historical_summary=(
            "Tikhonov's regularization arose directly from geophysical sounding where surface measurements "
            "must invert electromagnetic diffusion to recover underground conductivity layers. Because high-frequency "
            "spatial modes decay exponentially, inversion is numerically catastrophic. By 1963, this exact Fredholm "
            "operator framework was transferred by E. G. Zelkin into Soviet radar engineering to synthesize antenna "
            "apertures from desired radiation patterns without producing infinite reactive fields."
        ),
    ),
    EngineeringTransferLine(
        line_id="LINE_02_DYNAMICS_AEROSPACE_CONTROL",
        label="Chebyshev-Lyapunov-Andronov-Pontryagin to Aerospace & Missile Guidance",
        foundation_school="PONTRYAGIN",
        foundational_authors=["Чебышев П. Л.", "Ляпунов А. М.", "Андронов А. А.", "Понтрягин Л. С."],
        core_mathematical_formulation="dot(x) = f(x, u), u in U => H(x, psi, u) = (psi, f) => max_{u in U} H",
        intermediate_transmission_institutes=[
            "МИАН им. Стеклова",
            "ГИФТИ (Горький)",
            "Институт проблем управления (ИАТ АН СССР)",
        ],
        applied_engineering_domains=[
            "Оптимальное управление ракетами-носителями и спускаемыми аппаратами",
            "Рандеву и стыковка космических кораблей (Восток, Союз)",
            "Теория дуального управления и самонастраивающиеся следящие приводы",
            "Релейные системы ориентации спутников (bang-bang control)",
        ],
        operator_bridges=["OP:STATE", "OP:STABILITY", "OP:CONTROL", "OP:OPTIMIZE", "OP:STRUCTURAL_ROBUSTNESS"],
        lineage_milestones=[
            TransferNode("Ляпунов А. М.", "MATHEMATICIAN", 1892, "General Problem of the Stability of Motion"),
            TransferNode("Андронов А. А. & Понтрягин Л. С.", "MATHEMATICIAN", 1937, "Introduction of structural stability (rough systems)"),
            TransferNode("Понтрягин, Болтянский, Гамкрелидзе, Мищенко", "MATHEMATICIAN", 1956, "Discovery of the Maximum Principle with bounded control sets"),
            TransferNode("Красовский Н. Н.", "MATHEMATICIAN", 1959, "Theory of optimal regulation for aircraft and rocket trajectories"),
            TransferNode("Фейльдбаум А. А.", "MATHEMATICIAN", 1960, "Dual control theory under incomplete information in IAT"),
        ],
        documented_sources=["HIST:LYAPUNOV_2007_KRYLOV", "PUB:PONTRYAGIN_1960_MAXIMUM", "BENCH_02_PONTRYAGIN", "BENCH_07_ANDRONOV_PONTRYAGIN"],
        historical_summary=(
            "Starting from Lyapunov's phase-space stability and Andronov's non-linear oscillations, the Steklov "
            "Institute team under Pontryagin broke with Western variational smoothness to handle bounded actuator limits "
            "(u in U). The resulting Maximum Principle and relay (bang-bang) control provided the direct mathematical "
            "foundation for Soviet ballistic missile guidance, optimal burn scheduling for orbital insertion, and "
            "spacecraft attitude control."
        ),
    ),
    EngineeringTransferLine(
        line_id="LINE_03_COLLECTIVE_PLASMA_FUSION",
        label="Vlasov-Bogolyubov Kinetic Theory to Tokamak Fusion & High-Current Beams",
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
            "Релятивистские электронные пучки и гиротроны миллиметрового диапазона",
            "Высокочастотный нагрев плазмы и бесстолкновительное поглощение волн",
        ],
        operator_bridges=["OP:SELF_CONSISTENT_FIELD", "OP:SELF_OSCILLATE", "OP:DYNAMIC_PARTITION"],
        lineage_milestones=[
            TransferNode("Власов А. А.", "MATHEMATICIAN", 1938, "Formulates collisionless kinetic equation with self-consistent field"),
            TransferNode("Боголюбов Н. Н.", "MATHEMATICIAN", 1946, "Derives kinetic equations from BBGKY hierarchy of classical mechanics"),
            TransferNode("Курчатов И. В. & Арцимович Л. А.", "INSTITUTION", 1956, "Construct first Tokamak devices based on collective plasma equilibrium"),
            TransferNode("Шафранов В. Д.", "MATHEMATICIAN", 1966, "Develops Grad–Shafranov magnetohydrodynamic equilibrium from Vlasov moments"),
        ],
        documented_sources=["PUB:VLASOV_1967_REPRODUCTION", "BENCH_03_VLASOV", "BENCH_06_BOGOLYUBOV"],
        historical_summary=(
            "Vlasov's realization that long-range Coulomb interactions dominate over local pair collisions "
            "replaced the Boltzmann gas paradigm with self-consistent collective fields. When rigorous microscopic "
            "backing was supplied by Bogolyubov's BBGKY hierarchy, this framework became the primary computational "
            "and analytical foundation of the Soviet magnetic fusion program, leading directly to the Tokamak design."
        ),
    ),
    EngineeringTransferLine(
        line_id="LINE_04_INVERSE_SPECTRAL_SOLITONS",
        label="Gelfand-Levitan-Marchenko Inverse Spectra to Solitons & Non-Invasive Sounding",
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
            "Синтез акустических и гидроакустических профилей скорости",
            "Неразрушающий контроль слоистых композитных материалов",
        ],
        operator_bridges=["OP:INVERSE", "OP:SPECTRAL_INVERSE", "OP:SCATTER_INVERSE", "OP:CLASS_ADMISSIBILITY"],
        lineage_milestones=[
            TransferNode("Гельфанд И. М. & Левитан Б. М.", "MATHEMATICIAN", 1951, "Derives linear integral equation reconstructing Sturm–Liouville operator"),
            TransferNode("Марченко В. А.", "MATHEMATICIAN", 1952, "Solves inverse problem of scattering theory for one-dimensional Schrodinger operator"),
            TransferNode("Фаддеев Л. Д.", "MATHEMATICIAN", 1959, "Establishes multi-dimensional inverse scattering and quantum three-body equations"),
            TransferNode("Захаров В. Е. & Шабат А. Б.", "MATHEMATICIAN", 1971, "Applies inverse scattering transform (IST) to integrate nonlinear Schrodinger equation"),
        ],
        documented_sources=["PUB:GELFAND_LEVITAN_1951", "PUB:FADDEEV_1959", "PUB:GONCHAR_NOVIKOVA_HENKIN_1991"],
        historical_summary=(
            "The transformation operator method developed by Gelfand, Levitan, and Marchenko proved that "
            "an inaccessible spatial potential can be reconstructed exactly from its boundary spectral response. "
            "In 1971, Zakharov and Shabat at the Landau Institute realized that this inverse spectral linear apparatus "
            "could integrate completely nonlinear wave equations, establishing the modern theory of optical solitons "
            "and acoustic profile inversion."
        ),
    ),
    EngineeringTransferLine(
        line_id="LINE_05_COMPLEX_CONTROL_CYBERNETICS",
        label="Bernstein-Gelfand-Tsetlin to Adaptive Automata & Industrial Cybernetics",
        foundation_school="GELFAND",
        foundational_authors=["Бернштейн Н. А.", "Гельфанд И. М.", "Цетлин М. Л.", "Глушков В. М."],
        core_mathematical_formulation="Dynamic partition of variables + non-local search tactics in complex state spaces",
        intermediate_transmission_institutes=[
            "Институт биофизики АН СССР",
            "Институт проблем передачи информации (ИППИ АН СССР)",
            "Институт кибернетики АН УССР (Киев)",
        ],
        applied_engineering_domains=[
            "Адаптивные конечные автоматы в случайных средах",
            "Дискретные самоорганизующиеся системы с переменной структурой",
            "Алгоритмы координации многозвенных робототехнических манипуляторов",
        ],
        operator_bridges=["OP:TASK_REPRESENT", "OP:DYNAMIC_PARTITION", "OP:NONLOCAL_MOVE", "OP:STRUCTURAL_ADAPT"],
        lineage_milestones=[
            TransferNode("Бернштейн Н. А.", "MATHEMATICIAN", 1947, "Formulates physiological levels of movement construction and motor synergy"),
            TransferNode("Гельфанд И. М. & Цетлин М. Л.", "MATHEMATICIAN", 1961, "Nonlocal search principles for complex multi-degree systems"),
            TransferNode("Гельфанд И. М. & Цетлин М. Л.", "MATHEMATICIAN", 1962, "Task-relative representation in complex control systems"),
            TransferNode("Глушков В. М.", "MATHEMATICIAN", 1962, "Self-organizing discrete systems with variable structure in Kiev Cybernetics Institute"),
        ],
        documented_sources=["PUB:GELFAND_TSETLIN_1961_NONLOCAL", "PUB:GELFAND_TSETLIN_1962", "PUB:GLUSHKOV_1962_SELF_ORGANIZING"],
        historical_summary=(
            "Confronted with the curse of dimensionality in physiological motor control, Gelfand and Tsetlin "
            "adapted Bernstein's motor synergies into a mathematical theory of non-local search and dynamic partitioning. "
            "Rather than maintaining full isomorphic representations, systems represent only task-relevant coordinates. "
            "This became the foundation of Tsetlin's adaptive automata in random environments and Glushkov's "
            "variable-structure cybernetic architectures."
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
            "Оптимальные цифровые фильтры с равномерной пульсацией (Чебышевские фильтры)",
            "Таблично-полиномиальные аппроксимации элементарных функций в ЭВМ БЭСМ",
        ],
        operator_bridges=["OP:MINIMAX_APPROXIMATE", "OP:OPTIMIZE"],
        lineage_milestones=[
            TransferNode("Чебышев П. Л.", "MATHEMATICIAN", 1853, "Theory of mechanisms known as parallelograms and uniform approximation"),
            TransferNode("Чебышев П. Л.", "MATHEMATICIAN", 1859, "Functions least deviating from zero and orthogonal polynomials"),
            TransferNode("Марков А. А.", "MATHEMATICIAN", 1898, "Least squares and method of moments for probability bounds"),
            TransferNode("ИТМиВТ АН СССР", "INSTITUTION", 1958, "Chebyshev polynomials hard-coded in BESM-6 scientific microcode routines"),
        ],
        documented_sources=["PUB:CHEBYSHEV_1854_PARALLELOGRAMS", "BENCH_05_CHEBYSHEV", "BENCH_09_MARKOV"],
        historical_summary=(
            "Chebyshev's uniform approximation originated directly in steam engine mechanical linkage design "
            "(Watt's parallelogram). By demanding minimal peak deviation over a compact interval rather than local "
            "Taylor convergence, Chebyshev created a constructive theory of finite approximation. In the 20th century, "
            "this became the standard design methodology for Soviet analog/digital filter synthesis and mathematical "
            "function libraries in BESM supercomputers."
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
            "total_lines": len(self.registry),
            "transfer_lines": [line.to_dict() for line in self.registry],
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return data
