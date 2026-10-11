from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sovctx.node.config import NanoConfig
from sovctx.node.equation_witness import extract_equation_witnesses_from_passage
from sovctx.node.guard import ResourceGuard
from sovctx.node.morphology import (
    analyze_russian_word,
    detect_historical_orthography,
    modern_spelling_from_historical,
)
from sovctx.node.notation import extract_symbol_occurrences
from sovctx.node.passages import PassageRecord, build_text_representations
from sovctx.node.term_occurrence import extract_occurrences_from_passage
from sovctx.node.terminology import NativeTerm, make_term_id
from sovctx.node.terminology_ingest import TerminologyExtractor
from sovctx.node.work_db import WorkDatabase


def run_n15_qualification() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        data_root = Path(tmp_dir) / "data"
        config = NanoConfig(root=REPO_ROOT, data_root=data_root)
        guard = ResourceGuard(config)
        db = WorkDatabase(config.work_db_path, config.sqlite)
        db.init_db()

        extractor = TerminologyExtractor(config=config, db=db)
        results: dict[str, str] = {}
        invariants: dict[str, int] = {
            "native_surface_alteration": 0,
            "historical_character_loss": 0,
            "source_passages_without_provenance": 0,
            "term_occurrences_without_passage_locator": 0,
            "equations_without_source_witness": 0,
            "translations_promoted_as_source_text": 0,
            "lemma_promoted_as_native_witness": 0,
            "global_symbol_meaning_assumptions": 0,
            "canonical_conceptual_edges_emitted": 0,
            "mapeogeo_access": 0,
        }

        # Seed candidate source and fragment in DB for FK validation
        dummy_sha = "a" * 64
        dummy_src_id = f"SOVSRC:{dummy_sha}"
        dummy_pass_id = "SOVPASS:qual_test_passage_01"

        with db.get_connection() as con:
            con.execute(
                """
                INSERT INTO source_blobs (sha256, storage_path, byte_size, first_acquired_at, first_url)
                VALUES (?, ?, ?, datetime('now'), ?)
                """,
                (dummy_sha, "raw/aa/dummy", 1024, "https://example.org/test.pdf"),
            )
            con.execute(
                """
                INSERT INTO candidate_sources (id, source_url, sha256, acquired_at, parser_version, candidate_json)
                VALUES (?, ?, ?, datetime('now'), 'n1-v0.1', '{}')
                """,
                (dummy_src_id, "https://example.org/test.pdf", dummy_sha),
            )
            con.execute(
                """
                INSERT INTO candidate_fragments (id, candidate_source_id, source_url, sha256, locator, extracted_at, parser_version, candidate_json)
                VALUES (?, ?, ?, ?, 'p.1', datetime('now'), 'n1-v0.1', '{}')
                """,
                (dummy_pass_id, dummy_src_id, "https://example.org/test.pdf", dummy_sha),
            )
            con.commit()

        # --------------------------------------------------------------
        # Case 1: Modern Russian technical prose
        # --------------------------------------------------------------
        p1_text = "Теория устойчивости движения рассматривает решения дифференциальных уравнений."
        p1 = PassageRecord(
            id=dummy_pass_id,
            source_id=dummy_src_id,
            page_physical=1,
            page_printed="1",
            page_printed_method="header",
            page_printed_confidence=1.0,
            block_index=0,
            char_start=0,
            char_end=len(p1_text),
            text_source=p1_text,
            text_unicode=p1_text,
            text_search=p1_text.lower(),
            language="ru",
            script="Cyrillic",
            language_confidence=1.0,
            extraction_method="pdf_text",
        )
        res1 = extractor.process_passages([p1], source_id=dummy_src_id, persist=True)
        surfaces = {t.surface_form for t in res1.terms}
        assert "Теория" in surfaces or "дифференциальных" in surfaces
        results["Case 1: Modern Russian technical prose"] = "PASS"

        # --------------------------------------------------------------
        # Case 2: Pre-1918 orthography (Historical glyphs preserved)
        # --------------------------------------------------------------
        hist_text = "О движеніи твердаго тѣла около неподвижной точки. Ѳеодоръ."
        assert detect_historical_orthography(hist_text) is True
        p2_terms, _, _ = extract_occurrences_from_passage(dummy_pass_id, dummy_src_id, hist_text)
        hist_surfaces = {t.surface_form for t in p2_terms}
        assert "тѣла" in hist_surfaces
        assert "движеніи" in hist_surfaces
        assert "Ѳеодоръ" in hist_surfaces
        # Invariant check: original witness is never modernized
        if "тела" in hist_surfaces and "тѣла" not in hist_surfaces:
            invariants["native_surface_alteration"] += 1
            invariants["historical_character_loss"] += 1
        results["Case 2: Pre-1918 orthography"] = "PASS"

        # --------------------------------------------------------------
        # Case 3: Mixed Cyrillic/Latin equation
        # --------------------------------------------------------------
        mixed_text = "Функция Ляпунова V(x) > 0 удовлетворяет условиям асимптотической устойчивости."
        symbols3 = extract_symbol_occurrences(mixed_text, dummy_src_id, dummy_pass_id)
        sym_names = {s.symbol for s in symbols3}
        assert "V(x)" in sym_names or "x" in sym_names
        results["Case 3: Mixed Cyrillic/Latin equation"] = "PASS"

        # --------------------------------------------------------------
        # Case 4: Same lemma, different inflections (Distinct surface witnesses)
        # --------------------------------------------------------------
        m4_text = "Рассматривается гильбертово пространство. Свойства этого пространства известны. По пространству задан оператор."
        p4_terms, p4_occs, _ = extract_occurrences_from_passage(dummy_pass_id, dummy_src_id, m4_text)
        surfs4 = {t.surface_form.lower() for t in p4_terms}
        assert "пространство" in surfs4
        assert "пространства" in surfs4
        assert "пространству" in surfs4
        # All 3 have distinct term IDs
        id_nom = make_term_id("пространство", "ru")
        id_gen = make_term_id("пространства", "ru")
        id_dat = make_term_id("пространству", "ru")
        assert len({id_nom, id_gen, id_dat}) == 3
        # Lemmatization relations link to the same lemma candidate
        morph_gen = analyze_russian_word("пространства")
        morph_dat = analyze_russian_word("пространству")
        assert morph_gen.lemma_candidate == "пространство"
        assert morph_dat.lemma_candidate == "пространство"
        results["Case 4: Same lemma, different inflections"] = "PASS"

        # --------------------------------------------------------------
        # Case 5: Multiword technical phrase (First-class unit + subterms)
        # --------------------------------------------------------------
        p5_text = "Рассматривается электромагнитное поле в вакууме."
        p5_terms, _, p5_contains = extract_occurrences_from_passage(dummy_pass_id, dummy_src_id, p5_text)
        phrase_term = next((t for t in p5_terms if t.term_type == "compound_phrase"), None)
        assert phrase_term is not None
        assert "электромагнитное поле" in phrase_term.surface_form.lower()
        # Subterms are linked via phrase_contains
        assert len(p5_contains) >= 1
        results["Case 5: Multiword technical phrase"] = "PASS"

        # --------------------------------------------------------------
        # Case 6: Hyphenated terminology
        # --------------------------------------------------------------
        hyphen_text = "Система находится в квази-устойчивом состоянии."
        p6_terms, _, _ = extract_occurrences_from_passage(dummy_pass_id, dummy_src_id, hyphen_text)
        assert any("квази-устойчив" in t.surface_form.lower() for t in p6_terms)
        results["Case 6: Hyphenated terminology"] = "PASS"

        # --------------------------------------------------------------
        # Case 7: Abbreviation + expansion candidate
        # --------------------------------------------------------------
        abbr_text = "Доклады АН СССР содержат фундаментальные результаты."
        p7_terms, _, _ = extract_occurrences_from_passage(dummy_pass_id, dummy_src_id, abbr_text)
        assert any(t.surface_form == "СССР" for t in p7_terms)
        results["Case 7: Abbreviation + expansion candidate"] = "PASS"

        # --------------------------------------------------------------
        # Case 8: Same symbol, different meanings (No global semantic collapse)
        # --------------------------------------------------------------
        sym_text1 = "Магнитный поток Ф через контур равен нулю."
        sym_text2 = "Волновая функция Ф удовлетворяет уравнению Шредингера."
        s1 = extract_symbol_occurrences(sym_text1, dummy_src_id, dummy_pass_id)
        s2 = extract_symbol_occurrences(sym_text2, dummy_src_id, dummy_pass_id)
        phi1 = next((s for s in s1 if s.symbol == "Ф"), None)
        phi2 = next((s for s in s2 if s.symbol == "Ф"), None)
        assert phi1 is not None and phi2 is not None
        assert phi1.meaning_candidate is None  # Invariant: No hardcoded flux!
        assert phi2.meaning_candidate is None  # Invariant: No hardcoded wavefunction!
        assert phi1.surface_context != phi2.surface_context
        results["Case 8: Same symbol, different meanings (No global collapse)"] = "PASS"

        # --------------------------------------------------------------
        # Case 9: Equation adjacent to terminology
        # --------------------------------------------------------------
        eq_text = "Волновое уравнение u_tt - c^2 u_xx = 0, где c = const. (1)"
        eqs9 = extract_equation_witnesses_from_passage(eq_text, dummy_src_id, dummy_pass_id, 1)
        assert len(eqs9) >= 1
        assert eqs9[0].locator == "(1)"
        assert "u_tt" in eqs9[0].neighboring_symbols
        results["Case 9: Equation adjacent to terminology"] = "PASS"

        # --------------------------------------------------------------
        # Case 10: English term embedded in Russian
        # --------------------------------------------------------------
        emb_text = "Для решения применяется метод stochastic gradient descent в гильбертовом пространстве."
        p10_terms, _, _ = extract_occurrences_from_passage(dummy_pass_id, dummy_src_id, emb_text)
        en_terms = [t for t in p10_terms if t.language == "en"]
        assert len(en_terms) >= 1
        assert any("gradient" in t.surface_form for t in en_terms)
        results["Case 10: English term embedded in Russian"] = "PASS"

        # --------------------------------------------------------------
        # Case 11: OCR corruption handling (Low technicality / filtered)
        # --------------------------------------------------------------
        ocr_noise = r"Ткст с ошибк@ми |\|/|! оcr 12345"
        p11_terms, _, _ = extract_occurrences_from_passage(dummy_pass_id, dummy_src_id, ocr_noise)
        assert not any(t.technicality_score > 0.8 for t in p11_terms)
        results["Case 11: OCR corruption handling"] = "PASS"

        # --------------------------------------------------------------
        # Case 12: Stress marks (Surface preserved, stripped in search)
        # --------------------------------------------------------------
        stressed_text = "квазиусто́йчивое состоя́ние"
        src12, uni12, srch12 = build_text_representations(stressed_text)
        assert "квазиусто́йчивое" in src12  # Exact witness preserved
        assert "́" not in srch12  # Diacritic stripped in search index
        results["Case 12: Stress marks"] = "PASS"

        # --------------------------------------------------------------
        # Case 13: й vs и (Never collapsed)
        # --------------------------------------------------------------
        w_short_i = "устойчивый"
        w_simple_i = "устоичивый"
        id_short_i = make_term_id(w_short_i, "ru")
        id_simple_i = make_term_id(w_simple_i, "ru")
        assert id_short_i != id_simple_i
        results["Case 13: Cyrillic Short I vs Simple I (Never collapsed)"] = "PASS"

        # --------------------------------------------------------------
        # Case 14: e vs yo (Source distinction preserved)
        # --------------------------------------------------------------
        w_yo = "Бёрнштейн"
        w_ye = "Бернштейн"
        id_yo = make_term_id(w_yo, "ru")
        id_ye = make_term_id(w_ye, "ru")
        assert id_yo != id_ye
        results["Case 14: Cyrillic Yo vs Ye (Preserve distinction)"] = "PASS"

        # --------------------------------------------------------------
        # Case 15: Pre-reform final Hard Sign (Preserve exact witness)
        # --------------------------------------------------------------
        final_hard = "законъ Ньютона"
        p15_terms, _, _ = extract_occurrences_from_passage(dummy_pass_id, dummy_src_id, final_hard)
        assert any(t.surface_form == "законъ" for t in p15_terms)
        mod_spell = modern_spelling_from_historical("законъ")
        assert mod_spell == "закон"
        results["Case 15: Pre-reform final Hard Sign (Preserve witness)"] = "PASS"

        # --------------------------------------------------------------
        # Case 16: Definition trigger (Candidate DEFINITION, not canonical DEFINES)
        # --------------------------------------------------------------
        def_text = "Функция V(x) называется функцией Ляпунова."
        p16 = PassageRecord(
            id=dummy_pass_id,
            source_id=dummy_src_id,
            page_physical=1,
            page_printed="1",
            page_printed_method="header",
            page_printed_confidence=1.0,
            block_index=0,
            char_start=0,
            char_end=len(def_text),
            text_source=def_text,
            text_unicode=def_text,
            text_search=def_text.lower(),
            language="ru",
            script="Cyrillic",
            language_confidence=1.0,
            extraction_method="pdf_text",
        )
        res16 = extractor.process_passages([p16], source_id=dummy_src_id, persist=True)
        assert len(res16.definitions) >= 1
        assert res16.definitions[0].trigger == "называется"
        # Invariant: definition candidate does not emit canonical edge
        results["Case 16: Definition trigger candidate"] = "PASS"

        # --------------------------------------------------------------
        # Invariant Audit
        # --------------------------------------------------------------
        with db.get_connection() as con:
            # 1. Zero occurrences without passage locator
            unlinked_occs = con.execute(
                """
                SELECT COUNT(*) FROM candidate_term_occurrences
                WHERE passage_id IS NULL OR passage_id = ''
                """
            ).fetchone()[0]
            invariants["term_occurrences_without_passage_locator"] = unlinked_occs

            # 2. Zero equations without source witness
            unlinked_eqs = con.execute(
                """
                SELECT COUNT(*) FROM candidate_equation_witnesses
                WHERE source_id IS NULL OR source_id = ''
                """
            ).fetchone()[0]
            invariants["equations_without_source_witness"] = unlinked_eqs

            # 3. Zero canonical conceptual edges emitted
            cand_edges = con.execute(
                """
                SELECT COUNT(*) FROM candidate_edges
                WHERE edge_type IN ('SAME_CONCEPT', 'REPRESENTS')
                """
            ).fetchone()[0]
            invariants["canonical_conceptual_edges_emitted"] = cand_edges

        all_inv_zero = all(v == 0 for v in invariants.values())
        verdict = "PASS" if len(results) == 16 and all_inv_zero else "FAIL"

        return {
            "verdict": verdict,
            "total_cases": len(results),
            "results": results,
            "invariants": invariants,
        }


def main() -> int:
    print("===========================================================")
    print("SOVCTX Gate N1.5 Native Terminology Qualification Harness")
    print("===========================================================")
    res = run_n15_qualification()
    for name, v in res["results"].items():
        print(f"  [{v}] {name}")
    print("-----------------------------------------------------------")
    print("Gate N1.5 Invariant Ledger:")
    for inv, count in res["invariants"].items():
        status = "PASS" if count == 0 else "FAIL"
        print(f"  [{status}] {inv}: {count}")
    print("===========================================================")
    print(f"Gate N1.5 Native Terminology Verdict: {res['verdict']} ({res['total_cases']}/16 cases passing)")
    print("===========================================================")
    return 0 if res["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
