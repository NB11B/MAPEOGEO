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
from sovctx.node.intellectual_audit import (
    IntellectualStructureAuditor,
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
        assert line.lineage_status in {"DOCUMENTED_LINEAGE", "HYPOTHESIZED_LINEAGE"}
        assert line.evidentiary_confidence in {"HIGH", "MEDIUM", "CANDIDATE"}
        assert len(line.next_acquisition_targets) >= 1


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
        assert len(contrast.alternative_contemporary_formulation.key_authors) >= 1
        assert len(contrast.soviet_emphasized_formulation.key_authors) >= 1
        assert len(contrast.decisive_distinction) > 20
        assert len(contrast.epistemic_consequences) >= 2
        assert len(contrast.international_cross_pollination) >= 1

        # Check backward-compatibility accessors
        assert contrast.western_tradition == contrast.alternative_contemporary_formulation
        assert contrast.soviet_tradition == contrast.soviet_emphasized_formulation
        assert contrast.decisive_divergence_point == contrast.decisive_distinction


def test_intellectual_structure_auditor() -> None:
    auditor = IntellectualStructureAuditor()

    centrality = auditor.compute_term_centrality()
    assert len(centrality) == 13
    assert centrality[0].school_count >= centrality[-1].school_count
    assert centrality[0].centrality_rank == 1

    connectivity = auditor.compute_institutional_connectivity()
    assert len(connectivity) == 13
    assert connectivity[0].institution_count >= 1

    persistence = auditor.compute_temporal_persistence()
    assert len(persistence) == 13
    assert any(p.span_years > 100 for p in persistence)

    bridges = auditor.compute_institutional_bridges()
    assert len(bridges) >= 5
    assert any("Стеклова" in b.institution_name for b in bridges)
    assert any("Келдыша" in b.institution_name for b in bridges)

    matrix = auditor.build_core_motif_matrix()
    assert len(matrix) == 6
    motifs = {m.motif for m in matrix}
    assert any("Stability" in m for m in motifs)
    assert any("State" in m for m in motifs)
    assert any("Inverse" in m for m in motifs)
    assert any("Admissibility" in m for m in motifs)
    assert any("Collective" in m for m in motifs)
    assert any("Minimax" in m for m in motifs)


def test_markdown_synthesis_rendering() -> None:
    with tempfile.TemporaryDirectory() as td:
        temp_dir = Path(td)
        v_analyzer = OperatorVocabularyAnalyzer()
        t_analyzer = EngineeringTransferAnalyzer()
        c_analyzer = EpistemicContrastsAnalyzer()
        auditor = IntellectualStructureAuditor()

        v_data = v_analyzer.export_vocabulary_dossier(temp_dir / "v.json")
        t_data = t_analyzer.export_transfer_dossier(temp_dir / "t.json")
        c_data = c_analyzer.export_contrasts_dossier(temp_dir / "c.json")
        a_data = auditor.export_full_audit_dossier(temp_dir)

        md = render_intellectual_structure_markdown(v_data, t_data, c_data, a_data)
        assert "# SOVCTX Intellectual Structure & Epistemic Synthesis Report" in md
        assert "Core Mathematical Motif Matrix" in md
        assert "Cross-School Term Centrality" in md
        assert "Institutional Bridges" in md
        assert "Terminology Evolution vs. Mathematical Invariance" in md
        assert "Science-to-Engineering Transmission Lines" in md
        assert "DOCUMENTED_LINEAGE" in md
        assert "CONTRAST_01_TIKHONOV_VS_HADAMARD" in md
        assert "International Cross-Pollination" in md
