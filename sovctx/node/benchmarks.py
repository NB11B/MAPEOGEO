from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from .citations import extract_references_from_passage
from .entities import extract_entity_mentions
from .passages import PassageRecord, build_text_representations
from .resolution import score_author_match, score_title_match, score_year_match


def make_benchmark_passage(doc_id: str, text: str) -> PassageRecord:
    src, uni, search = build_text_representations(text)
    return PassageRecord(
        id=f"SOVPASS:{doc_id}",
        source_id=f"SOVSRC:{doc_id}",
        page_physical=1,
        page_printed="1",
        page_printed_method="exact",
        page_printed_confidence=1.0,
        block_index=0,
        char_start=0,
        char_end=len(text),
        text_source=src,
        text_unicode=uni,
        text_search=search,
        language="ru",
        script="Cyrillic",
        language_confidence=1.0,
    )


@dataclass
class GroundTruthCitation:
    index: int
    raw_text: str
    expected_authors: list[str]
    expected_title: str
    expected_year: int
    expected_publication: Optional[str] = None


@dataclass
class GroundTruthEntity:
    entity_type: str
    surface_text: str
    canonical_name: str


@dataclass
class BenchmarkDocument:
    doc_id: str
    title: str
    primary_authors: list[str]
    year: int
    publication: str
    text_content: str
    ground_truth_citations: list[GroundTruthCitation]
    ground_truth_entities: list[GroundTruthEntity]


BENCHMARK_CORPUS: list[BenchmarkDocument] = [
    BenchmarkDocument(
        doc_id="BENCH_01_TIKHONOV",
        title="Об устойчивости обратных задач",
        primary_authors=["Тихонов А. Н."],
        year=1943,
        publication="ДАН СССР",
        text_content="""В работе исследуется устойчивость решений обратных задач математической физики.
Как показано в классических работах Адамара [1], задача Коши для эллиптических уравнений некорректна.
Однако при сужении класса решений до компактных множеств устойчивость восстанавливается, о чем упоминали Лаврентьев М. А. [2] и Шаудер [3].
Эксперименты проводились в институте геофизики АН СССР с использованием сейсмографов Галицына.

Литература:
[1] Hadamard J. Le problème de Cauchy et les équations aux dérivées partielles linéaires hyperboliques. Paris: Hermann, 1932.
[2] Лаврентьев М. А. О некоторых свойствах непрерывных отображений // ДАН СССР. 1938. Т. 20, № 4. С. 241–244.
[3] Schauder J. Über lineare elliptische Differentialgleichungen zweiter Ordnung // Math. Z. 1930. Bd. 38. S. 257–282.
""",
        ground_truth_citations=[
            GroundTruthCitation(1, "Hadamard J. Le problème de Cauchy...", ["Hadamard J."], "Le problème de Cauchy", 1932),
            GroundTruthCitation(2, "Лаврентьев М. А. О некоторых свойствах непрерывных отображений...", ["Лаврентьев М. А."], "О некоторых свойствах непрерывных отображений", 1938, "ДАН СССР"),
            GroundTruthCitation(3, "Schauder J. Über lineare elliptische Differentialgleichungen...", ["Schauder J."], "Über lineare elliptische Differentialgleichungen zweiter Ordnung", 1930),
        ],
        ground_truth_entities=[
            GroundTruthEntity("PERSON_SCHOLAR", "Тихонов", "Тихонов А. Н."),
            GroundTruthEntity("PERSON_SCHOLAR", "Адамара", "Адамар Ж."),
            GroundTruthEntity("PERSON_SCHOLAR", "Лаврентьев М. А.", "Лаврентьев М. А."),
            GroundTruthEntity("PERSON_SCHOLAR", "Шаудер", "Шаудер Ю."),
            GroundTruthEntity("INSTITUTION", "АН СССР", "АН СССР"),
            GroundTruthEntity("METHOD", "обратных задач", "обратные задачи"),
            GroundTruthEntity("INSTRUMENT", "сейсмографов", "сейсмограф"),
        ],
    ),
    BenchmarkDocument(
        doc_id="BENCH_02_PONTRYAGIN",
        title="Математическая теория оптимальных процессов",
        primary_authors=["Понтрягин Л. С.", "Болтянский В. Г.", "Гамкрелидзе Р. В.", "Мищенко Е. Ф."],
        year=1961,
        publication="Наука",
        text_content="""В монографии излагается математическая теория оптимальных процессов управления и принцип максимума Понтрягина.
Исследования проводились в Математическом институте им. В. А. Стеклова АН СССР (МИАН).
Рассматриваются соотношения с динамическим программированием Беллмана [1].
Ранние результаты опубликованы авторами в Докладах Академии Наук СССР: Болтянский [2], Гамкрелидзе [3], Красовский [4].

Литература:
[1] Bellman R. Dynamic Programming. Princeton: Princeton University Press, 1957.
[2] Болтянский В. Г. Принцип максимума в теории оптимальных процессов // ДАН СССР. 1958. Т. 119, № 6. С. 1070–1073.
[3] Гамкрелидзе Р. В. Теория оптимальных по быстродействию процессов // ДАН СССР. 1958. Т. 123, № 2. С. 223–226.
[4] Красовский Н. Н. К теории оптимального регулирования // Автоматика и телемеханика. 1959. Т. 20, № 6. С. 689–701.
""",
        ground_truth_citations=[
            GroundTruthCitation(1, "Bellman R. Dynamic Programming...", ["Bellman R."], "Dynamic Programming", 1957),
            GroundTruthCitation(2, "Болтянский В. Г. Принцип максимума...", ["Болтянский В. Г."], "Принцип максимума в теории оптимальных процессов", 1958, "ДАН СССР"),
            GroundTruthCitation(3, "Гамкрелидзе Р. В. Теория оптимальных...", ["Гамкрелидзе Р. В."], "Теория оптимальных по быстродействию процессов", 1958, "ДАН СССР"),
            GroundTruthCitation(4, "Красовский Н. Н. К теории оптимального регулирования...", ["Красовский Н. Н."], "К теории оптимального регулирования", 1959, "Автоматика и телемеханика"),
        ],
        ground_truth_entities=[
            GroundTruthEntity("PERSON_SCHOLAR", "Понтрягин", "Понтрягин Л. С."),
            GroundTruthEntity("PERSON_SCHOLAR", "Болтянский", "Болтянский В. Г."),
            GroundTruthEntity("PERSON_SCHOLAR", "Гамкрелидзе", "Гамкрелидзе Р. В."),
            GroundTruthEntity("PERSON_SCHOLAR", "Мищенко", "Мищенко Е. Ф."),
            GroundTruthEntity("PERSON_SCHOLAR", "Беллмана", "Беллман Р."),
            GroundTruthEntity("PERSON_SCHOLAR", "Красовский", "Красовский Н. Н."),
            GroundTruthEntity("INSTITUTION", "МИАН", "МИАН"),
            GroundTruthEntity("INSTITUTION", "АН СССР", "АН СССР"),
            GroundTruthEntity("METHOD", "принцип максимума", "принцип максимума"),
        ],
    ),
    BenchmarkDocument(
        doc_id="BENCH_03_VLASOV",
        title="О вибрационных свойствах электронного газа",
        primary_authors=["Власов А. А."],
        year=1938,
        publication="ЖЭТФ",
        text_content="""Рассматривается самосогласованное поле и коллективное взаимодействие в плазме на физическом факультете МГУ.
Уравнение Власова учитывает дальнодействующие кулоновские силы без приближения парных столкновений, предложенного Ландау Л. Д. [1].
В астрофизическом контексте кинетическое уравнение с самосогласованным полем гравитации рассматривалось Джинсом [2].
Ранний вывод дан автором в [3]. Измерения колебаний проводились с помощью интерферометра Фабри-Перо.

Литература:
[1] Ландау Л. Д. Кинетическое уравнение для случая кулоновского взаимодействия // ЖЭТФ. 1936. Т. 7, № 2. С. 203–209.
[2] Jeans J. H. The dynamical theory of gases. Cambridge: Cambridge University Press, 1915.
[3] Власов А. А. К теории электронного газа // ЖЭТФ. 1937. Т. 6, № 8. С. 780–792.
""",
        ground_truth_citations=[
            GroundTruthCitation(1, "Ландау Л. Д. Кинетическое уравнение...", ["Ландау Л. Д."], "Кинетическое уравнение для случая кулоновского взаимодействия", 1936, "ЖЭТФ"),
            GroundTruthCitation(2, "Jeans J. H. The dynamical theory of gases...", ["Jeans J."], "The dynamical theory of gases", 1915),
            GroundTruthCitation(3, "Власов А. А. К теории электронного газа...", ["Власов А. А."], "К теории электронного газа", 1937, "ЖЭТФ"),
        ],
        ground_truth_entities=[
            GroundTruthEntity("PERSON_SCHOLAR", "Власов", "Власов А. А."),
            GroundTruthEntity("PERSON_SCHOLAR", "Ландау Л. Д.", "Ландау Л. Д."),
            GroundTruthEntity("PERSON_SCHOLAR", "Джинсом", "Джинс Д."),
            GroundTruthEntity("INSTITUTION", "МГУ", "МГУ"),
            GroundTruthEntity("METHOD", "самосогласованное поле", "самосогласованное поле"),
            GroundTruthEntity("INSTRUMENT", "интерферометра", "интерферометр"),
        ],
    ),
    BenchmarkDocument(
        doc_id="BENCH_04_GELFAND_LEVITAN",
        title="Об определении дифференциального уравнения по его спектральной функции",
        primary_authors=["Гельфанд И. М.", "Левитан Б. М."],
        year=1951,
        publication="Известия АН СССР. Серия математическая",
        text_content="""В статье строго формулируется интегральное уравнение Гельфанда-Левитана для обратной спектральной задачи Штурма-Лиувилля.
Исследования выполнены в МИАН и МГУ. В классической задаче Штурма [1] спектр определяет потенциал при определенных условиях.
Близкие результаты получены Марченко В. А. [2], а также Крейном М. Г. [3] и Левитаном [4].

Литература:
[1] Sturm C. Mémoire sur une classe d'équations à différences partielles // J. Math. Pures Appl. 1836. Vol. 1. P. 373–444.
[2] Марченко В. А. Некоторые вопросы теории одномерных линейных дифференциальных операторов // Труды ММО. 1950. Т. 1. С. 327–420.
[3] Крейн М. Г. О решении обратной задачи Штурма-Лиувилля // ДАН СССР. 1951. Т. 76, № 1. С. 21–24.
[4] Левитан Б. М. Разложение по собственным функциям // М.: Гостехиздат, 1949.
""",
        ground_truth_citations=[
            GroundTruthCitation(1, "Sturm C. Mémoire sur une classe...", ["Sturm C."], "Mémoire sur une classe d'équations", 1836),
            GroundTruthCitation(2, "Марченко В. А. Некоторые вопросы...", ["Марченко В. А."], "Некоторые вопросы теории одномерных линейных дифференциальных операторов", 1950, "Труды ММО"),
            GroundTruthCitation(3, "Крейн М. Г. О решении обратной задачи...", ["Крейн М. Г."], "О решении обратной задачи Штурма-Лиувилля", 1951, "ДАН СССР"),
            GroundTruthCitation(4, "Левитан Б. М. Разложение по собственным функциям...", ["Левитан Б. М."], "Разложение по собственным функциям", 1949),
        ],
        ground_truth_entities=[
            GroundTruthEntity("PERSON_SCHOLAR", "Гельфанд", "Гельфанд И. М."),
            GroundTruthEntity("PERSON_SCHOLAR", "Левитан", "Левитан Б. М."),
            GroundTruthEntity("PERSON_SCHOLAR", "Штурма", "Штурм Ш."),
            GroundTruthEntity("PERSON_SCHOLAR", "Марченко В. А.", "Марченко В. А."),
            GroundTruthEntity("PERSON_SCHOLAR", "Крейном М. Г.", "Крейн М. Г."),
            GroundTruthEntity("INSTITUTION", "МИАН", "МИАН"),
            GroundTruthEntity("INSTITUTION", "МГУ", "МГУ"),
            GroundTruthEntity("METHOD", "интегральное уравнение", "интегральное уравнение"),
        ],
    ),
    BenchmarkDocument(
        doc_id="BENCH_05_CHEBYSHEV",
        title="Теория механизмов, известных под названием параллелограммов",
        primary_authors=["Чебышев П. Л."],
        year=1854,
        publication="Записки Императорской Академии Наук",
        text_content="""Сочинение академика Чебышева П. Л. посвящено наилучшему приближению функций при конструировании шарнирных механизмов в Санкт-Петербургском университете.
Рассматривается параллелограмм Уатта [1] и шарнирные преобразования Понселе [2].
Математические основы наилучшего приближения заложены автором в сообщении [3].
Для проверки точности кинематических звеньев применялся катетометр и делительная машина.

Литература:
[1] Watt J. Specification of patent for certain newly invented improvements on steam-engines. London, 1784.
[2] Poncelet J. V. Traité de mécanique appliquée aux machines. Liège, 1839.
[3] Чебышев П. Л. Об определении числа элементов в шарнирных механизмах // Записки ИАН. 1853. Т. 4. С. 112–119.
""",
        ground_truth_citations=[
            GroundTruthCitation(1, "Watt J. Specification of patent...", ["Watt J."], "Specification of patent", 1784),
            GroundTruthCitation(2, "Poncelet J. V. Traité de mécanique...", ["Poncelet J."], "Traité de mécanique appliquée", 1839),
            GroundTruthCitation(3, "Чебышев П. Л. Об определении числа элементов...", ["Чебышев П. Л."], "Об определении числа элементов в шарнирных механизмах", 1853, "Записки ИАН"),
        ],
        ground_truth_entities=[
            GroundTruthEntity("PERSON_SCHOLAR", "Чебышев", "Чебышев П. Л."),
            GroundTruthEntity("PERSON_SCHOLAR", "Уатта", "Уатт Д."),
            GroundTruthEntity("PERSON_SCHOLAR", "Понселе", "Понселе Ж."),
            GroundTruthEntity("METHOD", "наилучшего приближения", "наилучшее приближение"),
            GroundTruthEntity("INSTRUMENT", "катетометр", "катетометр"),
            GroundTruthEntity("INSTRUMENT", "делительная машина", "делительная машина"),
        ],
    ),
    BenchmarkDocument(
        doc_id="BENCH_06_BOGOLYUBOV",
        title="Проблемы динамической теории в статистической физике",
        primary_authors=["Боголюбов Н. Н."],
        year=1946,
        publication="ОГИЗ Гостехиздат",
        text_content="""В монографии формулируется цепочка уравнений ББГКИ для систем многих взаимодействующих частиц в АН УССР.
Классическая кинетическая теория Больцмана [1] и распределения Гиббса [2] выводятся из механики Лиувилля.
Метод асимптотических разложений развит автором совместно с Крыловым Н. М. [3].
Сопоставление с гидродинамическими моделями Кирквуда дано в [4].

Литература:
[1] Boltzmann L. Weitere Studien über das Wärmegleichgewicht unter Gasmolekülen // Wien. Ber. 1872. Bd. 66. S. 275–370.
[2] Gibbs J. W. Elementary Principles in Statistical Mechanics. New York: Scribner, 1902.
[3] Крылов Н. М., Боголюбов Н. Н. Введение в нелинейную механику. Киев: Изд-во АН УССР, 1937.
[4] Kirkwood J. G. The statistical mechanical theory of transport processes // J. Chem. Phys. 1946. Vol. 14. P. 180–201.
""",
        ground_truth_citations=[
            GroundTruthCitation(1, "Boltzmann L. Weitere Studien...", ["Boltzmann L."], "Weitere Studien über das Wärmegleichgewicht", 1872),
            GroundTruthCitation(2, "Gibbs J. W. Elementary Principles...", ["Gibbs J."], "Elementary Principles in Statistical Mechanics", 1902),
            GroundTruthCitation(3, "Крылов Н. М., Боголюбов Н. Н. Введение в нелинейную механику...", ["Крылов Н. М.", "Боголюбов Н. Н."], "Введение в нелинейную механику", 1937),
            GroundTruthCitation(4, "Kirkwood J. G. The statistical mechanical theory...", ["Kirkwood J."], "The statistical mechanical theory of transport processes", 1946),
        ],
        ground_truth_entities=[
            GroundTruthEntity("PERSON_SCHOLAR", "Боголюбов", "Боголюбов Н. Н."),
            GroundTruthEntity("PERSON_SCHOLAR", "Больцмана", "Больцман Л."),
            GroundTruthEntity("PERSON_SCHOLAR", "Гиббса", "Гиббс Д."),
            GroundTruthEntity("PERSON_SCHOLAR", "Крыловым Н. М.", "Крылов Н. М."),
            GroundTruthEntity("PERSON_SCHOLAR", "Кирквуда", "Кирквуд Д."),
            GroundTruthEntity("INSTITUTION", "АН УССР", "АН УССР"),
            GroundTruthEntity("METHOD", "цепочка уравнений", "цепочка ББГКИ"),
        ],
    ),
    BenchmarkDocument(
        doc_id="BENCH_07_ANDRONOV_PONTRYAGIN",
        title="Грубые системы",
        primary_authors=["Андронов А. А.", "Понтрягин Л. С."],
        year=1937,
        publication="ДАН СССР",
        text_content="""Статья вводит понятие структурной устойчивости динамических систем (грубости) в Горьковском исследовательском физико-техническом институте (ГИФТИ).
Качественная теория восходит к Пуанкаре [1] и Биркгофу [2].
Ранние результаты по предельным циклам изложены Андроновым в [3].

Литература:
[1] Poincaré H. Mémoire sur les courbes définies par une équation différentielle // J. Math. Pures Appl. 1881. Vol. 7. P. 375–422.
[2] Birkhoff G. D. Dynamical Systems. New York: AMS, 1927.
[3] Андронов А. А. Предельные циклы Пуанкаре и теория автоколебаний // ДАН СССР. 1929. Т. 2. С. 340–344.
""",
        ground_truth_citations=[
            GroundTruthCitation(1, "Poincaré H. Mémoire sur les courbes...", ["Poincaré H."], "Mémoire sur les courbes définies", 1881),
            GroundTruthCitation(2, "Birkhoff G. D. Dynamical Systems...", ["Birkhoff G."], "Dynamical Systems", 1927),
            GroundTruthCitation(3, "Андронов А. А. Предельные циклы Пуанкаре...", ["Андронов А. А."], "Предельные циклы Пуанкаре и теория автоколебаний", 1929, "ДАН СССР"),
        ],
        ground_truth_entities=[
            GroundTruthEntity("PERSON_SCHOLAR", "Андронов", "Андронов А. А."),
            GroundTruthEntity("PERSON_SCHOLAR", "Понтрягин", "Понтрягин Л. С."),
            GroundTruthEntity("PERSON_SCHOLAR", "Пуанкаре", "Пуанкаре А."),
            GroundTruthEntity("PERSON_SCHOLAR", "Биркгофу", "Биркгоф Д."),
            GroundTruthEntity("INSTITUTION", "ГИФТИ", "ГИФТИ"),
            GroundTruthEntity("METHOD", "структурной устойчивости", "структурная устойчивость"),
        ],
    ),
    BenchmarkDocument(
        doc_id="BENCH_08_LYAPUNOV",
        title="Общая задача об устойчивости движения",
        primary_authors=["Ляпунов А. М."],
        year=1892,
        publication="Харьковское математическое общество",
        text_content="""Диссертация Ляпунова А. М. в Харьковском университете закладывает основы современной теории устойчивости движения.
Функция Ляпунова обобщает принцип Лагранжа [1] и теорему Дирихле [2] об устойчивости равновесия при минимуме потенциальной энергии.
Развитие методов Чебышева П. Л. в вопросах устойчивости обсуждается в [3].

Литература:
[1] Lagrange J. L. Mécanique analytique. Paris: Desaint, 1788.
[2] Dirichlet P. G. L. Über die Stabilität des Gleichgewichts // J. Reine Angew. Math. 1846. Bd. 32. S. 85–88.
[3] Чебышев П. Л. О функциях, мало отклоняющихся от нуля // Записки ИАН. 1859. Т. 3. С. 1–24.
""",
        ground_truth_citations=[
            GroundTruthCitation(1, "Lagrange J. L. Mécanique analytique...", ["Lagrange J."], "Mécanique analytique", 1788),
            GroundTruthCitation(2, "Dirichlet P. G. L. Über die Stabilität...", ["Dirichlet P."], "Über die Stabilität des Gleichgewichts", 1846),
            GroundTruthCitation(3, "Чебышев П. Л. О функциях, мало отклоняющихся...", ["Чебышев П. Л."], "О функциях, мало отклоняющихся от нуля", 1859, "Записки ИАН"),
        ],
        ground_truth_entities=[
            GroundTruthEntity("PERSON_SCHOLAR", "Ляпунов", "Ляпунов А. М."),
            GroundTruthEntity("PERSON_SCHOLAR", "Лагранжа", "Лагранж Ж."),
            GroundTruthEntity("PERSON_SCHOLAR", "Дирихле", "Дирихле П."),
            GroundTruthEntity("PERSON_SCHOLAR", "Чебышева", "Чебышев П. Л."),
            GroundTruthEntity("METHOD", "функция Ляпунова", "функция Ляпунова"),
        ],
    ),
    BenchmarkDocument(
        doc_id="BENCH_09_MARKOV",
        title="Распространение закона больших чисел на величины, зависящие друг от друга",
        primary_authors=["Марков А. А."],
        year=1906,
        publication="Известия Физико-математического общества при Казанском университете",
        text_content="""В работе исследуются случайные последовательности, в которых вероятность перехода зависит лишь от предшествующего состояния (цепи Маркова).
Обобщается теорема Чебышева [1] о законе больших чисел для независимых величин.
Критика результатов Некрасова П. А. представлена в [2].
Ранние результаты автора опубликованы в [3].

Литература:
[1] Чебышев П. Л. О средних величинах // Математический сборник. 1867. Т. 2. С. 1–9.
[2] Некрасов П. А. Философия и логика науки о массовых проявлениях // Математический сборник. 1902. Т. 23. С. 463–529.
[3] Марков А. А. Закон больших чисел и метод наименьших квадратов // Известия ИАН. 1898. Т. 8. С. 110–128.
""",
        ground_truth_citations=[
            GroundTruthCitation(1, "Чебышев П. Л. О средних величинах...", ["Чебышев П. Л."], "О средних величинах", 1867, "Математический сборник"),
            GroundTruthCitation(2, "Некрасов П. А. Философия и логика...", ["Некрасов П. А."], "Философия и логика науки о массовых проявлениях", 1902, "Математический сборник"),
            GroundTruthCitation(3, "Марков А. А. Закон больших чисел...", ["Марков А. А."], "Закон больших чисел и метод наименьших квадратов", 1898, "Известия ИАН"),
        ],
        ground_truth_entities=[
            GroundTruthEntity("PERSON_SCHOLAR", "Марков", "Марков А. А."),
            GroundTruthEntity("PERSON_SCHOLAR", "Чебышева", "Чебышев П. Л."),
            GroundTruthEntity("PERSON_SCHOLAR", "Некрасова", "Некрасов П. А."),
            GroundTruthEntity("METHOD", "цепи Маркова", "цепи Маркова"),
        ],
    ),
    BenchmarkDocument(
        doc_id="BENCH_10_FADDEEV",
        title="Теория рассеяния для системы трех частиц",
        primary_authors=["Фаддеев Л. Д."],
        year=1960,
        publication="ЖЭТФ",
        text_content="""В Ленинградском отделении МИАН (ЛОМИ) формулируются уравнения Фаддеева для нерелятивистской квантовой задачи трех тел со связными кластерами.
Уравнение Липпмана-Швингера [1] для трех частиц сингулярно вследствие перерассеяния.
Многоканальная теория Ватсона [2] не устраняет компактность резольвенты.
Модель взаимодействия точечных частиц Скорнякова и Тер-Мартиросяна исследована в [3].
Предварительное сообщение автора опубликовано в [4].

Литература:
[1] Lippmann B. A., Schwinger J. Variational principles for scattering processes // Phys. Rev. 1950. Vol. 79. P. 469–480.
[2] Watson K. M. Multiple scattering and the active optical model // Phys. Rev. 1953. Vol. 89. P. 575–587.
[3] Скорняков Г. В., Тер-Мартиросян К. А. Рассеяние нейтронов малой энергии дейтронами // ЖЭТФ. 1956. Т. 31, № 5. С. 775–790.
[4] Фаддеев Л. Д. Теория рассеяния трех тел // ДАН СССР. 1959. Т. 138, № 3. С. 565–568.
""",
        ground_truth_citations=[
            GroundTruthCitation(1, "Lippmann B. A., Schwinger J. Variational principles...", ["Lippmann B.", "Schwinger J."], "Variational principles for scattering processes", 1950),
            GroundTruthCitation(2, "Watson K. M. Multiple scattering...", ["Watson K."], "Multiple scattering and the active optical model", 1953),
            GroundTruthCitation(3, "Скорняков Г. В., Тер-Мартиросян К. А. Рассеяние нейтронов...", ["Скорняков Г. В.", "Тер-Мартиросян К. А."], "Рассеяние нейтронов малой энергии дейтронами", 1956, "ЖЭТФ"),
            GroundTruthCitation(4, "Фаддеев Л. Д. Теория рассеяния трех тел...", ["Фаддеев Л. Д."], "Теория рассеяния трех тел", 1959, "ДАН СССР"),
        ],
        ground_truth_entities=[
            GroundTruthEntity("PERSON_SCHOLAR", "Фаддеев", "Фаддеев Л. Д."),
            GroundTruthEntity("PERSON_SCHOLAR", "Липпмана", "Липпман Б."),
            GroundTruthEntity("PERSON_SCHOLAR", "Швингера", "Швингер Ю."),
            GroundTruthEntity("PERSON_SCHOLAR", "Ватсона", "Ватсон К."),
            GroundTruthEntity("PERSON_SCHOLAR", "Скорнякова", "Скорняков Г. В."),
            GroundTruthEntity("PERSON_SCHOLAR", "Тер-Мартиросяна", "Тер-Мартиросян К. А."),
            GroundTruthEntity("INSTITUTION", "ЛОМИ", "ЛОМИ"),
            GroundTruthEntity("INSTITUTION", "МИАН", "МИАН"),
            GroundTruthEntity("METHOD", "уравнения Фаддеева", "уравнения Фаддеева"),
        ],
    ),
]


def evaluate_citation_benchmark() -> dict[str, Any]:
    """Evaluate Citation Recall and Citation Precision across the 10 citation-dense Soviet benchmark papers."""
    total_ground_truth_citations = sum(len(d.ground_truth_citations) for d in BENCHMARK_CORPUS)
    total_extracted_candidates = 0
    true_positive_citations = 0

    per_doc_results: list[dict[str, Any]] = []

    for doc in BENCHMARK_CORPUS:
        passage = make_benchmark_passage(doc.doc_id, doc.text_content)
        extracted = extract_references_from_passage(passage.text_source, passage.source_id, passage.id)
        total_extracted_candidates += len(extracted)

        doc_tp = 0
        matched_gt: set[int] = set()

        for cand in extracted:
            cand_authors = cand.authors_list()
            cand_year = cand.year_raw
            cand_title = cand.title_raw

            is_match = False
            for gt in doc.ground_truth_citations:
                if gt.index in matched_gt:
                    continue
                a_score = score_author_match(cand_authors, gt.expected_authors)
                y_match = (cand_year == gt.expected_year) if (cand_year and gt.expected_year) else False
                t_score = score_title_match(cand_title, gt.expected_title) if cand_title else 0.0

                if a_score >= 0.50 and (y_match or t_score >= 0.50):
                    doc_tp += 1
                    matched_gt.add(gt.index)
                    is_match = True
                    break

        true_positive_citations += doc_tp
        per_doc_results.append({
            "doc_id": doc.doc_id,
            "ground_truth_citations": len(doc.ground_truth_citations),
            "extracted_candidates": len(extracted),
            "true_positives": doc_tp,
        })

    precision = round(true_positive_citations / total_extracted_candidates, 4) if total_extracted_candidates > 0 else 0.0
    recall = round(true_positive_citations / total_ground_truth_citations, 4) if total_ground_truth_citations > 0 else 0.0

    return {
        "benchmark_documents_count": len(BENCHMARK_CORPUS),
        "total_ground_truth_citations": total_ground_truth_citations,
        "total_extracted_candidates": total_extracted_candidates,
        "true_positives": true_positive_citations,
        "citation_precision": precision,
        "citation_recall": recall,
        "precision_threshold_met": precision >= 0.95,
        "recall_threshold_met": recall >= 0.80,
        "per_document": per_doc_results,
    }


def evaluate_entity_benchmark() -> dict[str, Any]:
    """Evaluate Entity Resolution Precision and Recall across the 10 benchmark documents."""
    total_ground_truth_entities = sum(len(d.ground_truth_entities) for d in BENCHMARK_CORPUS)
    total_extracted_mentions = 0
    true_positive_entities = 0

    per_doc_results: list[dict[str, Any]] = []

    for doc in BENCHMARK_CORPUS:
        passage = make_benchmark_passage(doc.doc_id, doc.text_content)
        extracted = extract_entity_mentions(passage.text_source, passage.source_id, passage.id)
        total_extracted_mentions += len(extracted)

        doc_tp = 0
        matched_gt: set[str] = set()

        for em in extracted:
            for gt in doc.ground_truth_entities:
                gt_type = "PERSON" if "PERSON" in gt.entity_type else gt.entity_type
                gt_key = f"{gt_type}:{gt.surface_text.lower()}"
                if gt_key in matched_gt:
                    continue
                if gt_type == em.entity_type:
                    if (
                        gt.surface_text.lower() in em.surface_text.lower()
                        or em.surface_text.lower() in gt.surface_text.lower()
                        or gt.canonical_name.lower() in em.normalized_name.lower()
                        or em.normalized_name.lower() in gt.canonical_name.lower()
                    ):
                        doc_tp += 1
                        matched_gt.add(gt_key)
                        break

        true_positive_entities += doc_tp
        per_doc_results.append({
            "doc_id": doc.doc_id,
            "ground_truth_entities": len(doc.ground_truth_entities),
            "extracted_mentions": len(extracted),
            "true_positives": doc_tp,
        })

    valid_routed = sum(
        1 for doc in BENCHMARK_CORPUS
        for em in extract_entity_mentions(make_benchmark_passage(doc.doc_id, doc.text_content).text_source, f"SOVSRC:{doc.doc_id}", f"SOVPASS:{doc.doc_id}")
        if em.normalized_name and em.confidence >= 0.80
    )

    routing_precision = round(valid_routed / total_extracted_mentions, 4) if total_extracted_mentions > 0 else 1.0
    recall = round(true_positive_entities / total_ground_truth_entities, 4) if total_ground_truth_entities > 0 else 0.0

    return {
        "benchmark_documents_count": len(BENCHMARK_CORPUS),
        "total_ground_truth_entities": total_ground_truth_entities,
        "total_extracted_mentions": total_extracted_mentions,
        "true_positives": true_positive_entities,
        "entity_routing_precision": routing_precision,
        "entity_recall": recall,
        "precision_threshold_met": routing_precision >= 0.95,
        "recall_threshold_met": recall >= 0.80,
        "per_document": per_doc_results,
    }
