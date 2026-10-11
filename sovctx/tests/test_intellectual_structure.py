from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from sovctx.node.engineering_transfer import (
    ENGINEERING_TRANSFER_REGISTRY,
    EngineeringTransferAnalyzer,
)
from sovctx.node.epistemic_contrasts import (
    EPISTEMIC_CONTRASTS_REGISTRY,
    EpistemicContrastsAnalyzer,
)
from sovctx.node.operator_vocabulary import (
    OPERATOR_VOCABULARY_REGISTRY,
    OperatorVocabularyAnalyzer,
)
from sovctx.tools.analyze_intellectual_structure import (
    render_intellectual_structure_markdown,
)


def test_operator_vocabulary_registry() -> None:
    analyzer = OperatorVocabularyAnalyzer()
    assert len(analyzer.registry) == 13

    expected_roots = [
        "оператор", "преобразован", "отображен", "функционал",
        "состояни", "траектори", "устойчивост", "инвариант",
        "допустим", "краев", "обратн", "регуляриз", "приближен"
    ]
    for root in expected_roots:
        term = analyzer.get_term_by_root(root)
        assert term is not None, f"Term root '{root}' must be present in registry"
        assert len(term.transition_phases) >= 2, f"Term '{root}' must have >= 2 evolutionary phases"
        assert len(term.primary_schools) >= 1, f"Term '{root}' must be linked to at least 1 school"


def test_engineering_transfer_lines() -> None:
    analyzer = EngineeringTransferAnalyzer()
    assert len(analyzer.registry) == 6

    expected_line_ids = [
        "LINE_01_INVERSE_GEOPHYSICS_RADAR",
        "LINE_02_DYNAMICS_AEROSPACE_CONTROL",
        "LINE_03_COLLECTIVE_PLASMA_FUSION",
        "LINE_04_INVERSE_SPECTRAL_SOLITONS",
        "LINE_05_COMPLEX_CONTROL_CYBERNETICS",
        "LINE_06_MINIMAX_APPROXIMATION_COMPUTING",
    ]
    for lid in expected_line_ids:
        line = analyzer.get_line_by_id(lid)
        assert line is not None, f"Transfer line '{lid}' must exist"
        assert len(line.foundational_authors) >= 1
        assert len(line.applied_engineering_domains) >= 2
        assert len(line.operator_bridges) >= 2
        assert len(line.lineage_milestones) >= 3


def test_epistemic_contrasts() -> None:
    analyzer = EpistemicContrastsAnalyzer()
    assert len(analyzer.registry) == 6

    expected_contrasts = [
        "CONTRAST_01_TIKHONOV_VS_HADAMARD",
        "CONTRAST_02_PONTRYAGIN_VS_CLASSICAL_VARIATIONS",
        "CONTRAST_03_ANDRONOV_VS_BODE_NYQUIST",
        "CONTRAST_04_VLASOV_VS_BOLTZMANN",
        "CONTRAST_05_CHEBYSHEV_VS_TAYLOR",
        "CONTRAST_06_GELFAND_LEVITAN_VS_FORWARD_SPECTRAL",
    ]
    for cid in expected_contrasts:
        contrast = analyzer.get_contrast_by_id(cid)
        assert contrast is not None, f"Epistemic contrast '{cid}' must exist"
        assert len(contrast.western_tradition.key_authors) >= 1
        assert len(contrast.soviet_tradition.key_authors) >= 1
        assert len(contrast.decisive_divergence_point) > 20
        assert len(contrast.epistemic_consequences) >= 2
        assert len(contrast.technological_manifestations) >= 2


def test_markdown_synthesis_rendering() -> None:
    with tempfile.TemporaryDirectory() as td:
        temp_dir = Path(td)
        v_analyzer = OperatorVocabularyAnalyzer()
        t_analyzer = EngineeringTransferAnalyzer()
        c_analyzer = EpistemicContrastsAnalyzer()

        v_data = v_analyzer.export_vocabulary_dossier(temp_dir / "v.json")
        t_data = t_analyzer.export_transfer_dossier(temp_dir / "t.json")
        c_data = c_analyzer.export_contrasts_dossier(temp_dir / "c.json")

        md = render_intellectual_structure_markdown(v_data, t_data, c_data)
        assert "# SOVCTX Intellectual Structure & Epistemic Synthesis Report" in md
        assert "Axis A: Core Operator Vocabulary" in md
        assert "Axis B: Science-to-Engineering Transmission Lines" in md
        assert "Axis C: Distinctive Epistemological Contrasts" in md
        assert "CONTRAST_01_TIKHONOV_VS_HADAMARD" in md
