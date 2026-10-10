"""Qualification and Unit Test Suite for Task T03: Condition and Applicability.

Verifies:
1. AQ49: Bilateral 4-state logic over all 16 AND pairs, 16 OR pairs, and 4 NOT values.
2. AQ49: Quantitative comparisons with unit checking and conflict isolation.
3. AQ49 & AQ38: Leaf proposition resolves across all aligned evidence reports.
4. AQ03: Known-unmet condition yields conditions_unmet, unknown yields unresolved.
5. AQ14: Scope dimensions (territory, person, subject matter, action) must align.
6. AQ15: Intersection of multiple scopes preserves strictest prohibitions and duties.
7. AQ42: Statutory effective time intervals are separate from UoW counters.
"""

from __future__ import annotations

import unittest

from experiments.authority_assessment.v0_1.intel_authority.condition_verifier import (
    BilateralState,
    ConditionVerifier,
    EvidenceState,
    evaluate_four_state_and,
    evaluate_four_state_not,
    evaluate_four_state_or,
)


class TestT03ConditionAndApplicability(unittest.TestCase):

    # --------------------------------------------------------------------------
    # 1. AQ49: 16 AND, 16 OR, 4 NOT TRUTH TABLES
    # --------------------------------------------------------------------------
    def test_aq49_four_state_truth_tables(self) -> None:
        """Enumerate all 16 AND pairs, 16 OR pairs, and 4 NOT values (AQ49 Subcase 1)."""
        states = [EvidenceState.SUPPORTED, EvidenceState.REFUTED, EvidenceState.UNKNOWN, EvidenceState.CONFLICTING]

        # 4 NOT values
        self.assertEqual(evaluate_four_state_not(EvidenceState.SUPPORTED), EvidenceState.REFUTED)
        self.assertEqual(evaluate_four_state_not(EvidenceState.REFUTED), EvidenceState.SUPPORTED)
        self.assertEqual(evaluate_four_state_not(EvidenceState.UNKNOWN), EvidenceState.UNKNOWN)
        self.assertEqual(evaluate_four_state_not(EvidenceState.CONFLICTING), EvidenceState.CONFLICTING)

        # 16 AND pairs: (s1 & s2, r1 | r2)
        expected_and = {
            (EvidenceState.SUPPORTED, EvidenceState.SUPPORTED): EvidenceState.SUPPORTED,
            (EvidenceState.SUPPORTED, EvidenceState.REFUTED): EvidenceState.REFUTED,
            (EvidenceState.SUPPORTED, EvidenceState.UNKNOWN): EvidenceState.UNKNOWN,
            (EvidenceState.SUPPORTED, EvidenceState.CONFLICTING): EvidenceState.CONFLICTING,
            (EvidenceState.REFUTED, EvidenceState.SUPPORTED): EvidenceState.REFUTED,
            (EvidenceState.REFUTED, EvidenceState.REFUTED): EvidenceState.REFUTED,
            (EvidenceState.REFUTED, EvidenceState.UNKNOWN): EvidenceState.REFUTED,
            (EvidenceState.REFUTED, EvidenceState.CONFLICTING): EvidenceState.REFUTED,
            (EvidenceState.UNKNOWN, EvidenceState.SUPPORTED): EvidenceState.UNKNOWN,
            (EvidenceState.UNKNOWN, EvidenceState.REFUTED): EvidenceState.REFUTED,
            (EvidenceState.UNKNOWN, EvidenceState.UNKNOWN): EvidenceState.UNKNOWN,
            (EvidenceState.UNKNOWN, EvidenceState.CONFLICTING): EvidenceState.REFUTED,
            (EvidenceState.CONFLICTING, EvidenceState.SUPPORTED): EvidenceState.CONFLICTING,
            (EvidenceState.CONFLICTING, EvidenceState.REFUTED): EvidenceState.REFUTED,
            (EvidenceState.CONFLICTING, EvidenceState.UNKNOWN): EvidenceState.REFUTED,
            (EvidenceState.CONFLICTING, EvidenceState.CONFLICTING): EvidenceState.CONFLICTING,
        }

        for (left, right), expected in expected_and.items():
            actual = evaluate_four_state_and(left, right)
            self.assertEqual(
                actual, expected,
                f"AND failed for ({left.value}, {right.value}): expected {expected.value}, got {actual.value}",
            )

        # 16 OR pairs: (s1 | s2, r1 & r2)
        expected_or = {
            (EvidenceState.SUPPORTED, EvidenceState.SUPPORTED): EvidenceState.SUPPORTED,
            (EvidenceState.SUPPORTED, EvidenceState.REFUTED): EvidenceState.SUPPORTED,
            (EvidenceState.SUPPORTED, EvidenceState.UNKNOWN): EvidenceState.SUPPORTED,
            (EvidenceState.SUPPORTED, EvidenceState.CONFLICTING): EvidenceState.SUPPORTED,
            (EvidenceState.REFUTED, EvidenceState.SUPPORTED): EvidenceState.SUPPORTED,
            (EvidenceState.REFUTED, EvidenceState.REFUTED): EvidenceState.REFUTED,
            (EvidenceState.REFUTED, EvidenceState.UNKNOWN): EvidenceState.UNKNOWN,
            (EvidenceState.REFUTED, EvidenceState.CONFLICTING): EvidenceState.CONFLICTING,
            (EvidenceState.UNKNOWN, EvidenceState.SUPPORTED): EvidenceState.SUPPORTED,
            (EvidenceState.UNKNOWN, EvidenceState.REFUTED): EvidenceState.UNKNOWN,
            (EvidenceState.UNKNOWN, EvidenceState.UNKNOWN): EvidenceState.UNKNOWN,
            (EvidenceState.UNKNOWN, EvidenceState.CONFLICTING): EvidenceState.SUPPORTED,
            (EvidenceState.CONFLICTING, EvidenceState.SUPPORTED): EvidenceState.SUPPORTED,
            (EvidenceState.CONFLICTING, EvidenceState.REFUTED): EvidenceState.CONFLICTING,
            (EvidenceState.CONFLICTING, EvidenceState.UNKNOWN): EvidenceState.SUPPORTED,
            (EvidenceState.CONFLICTING, EvidenceState.CONFLICTING): EvidenceState.CONFLICTING,
        }

        for (left, right), expected in expected_or.items():
            actual = evaluate_four_state_or(left, right)
            self.assertEqual(
                actual, expected,
                f"OR failed for ({left.value}, {right.value}): expected {expected.value}, got {actual.value}",
            )

    # --------------------------------------------------------------------------
    # 2. AQ49: QUANTITATIVE COMPARISONS AND UNIT CHECKS
    # --------------------------------------------------------------------------
    def test_aq49_quantitative_comparisons_and_units(self) -> None:
        """Case parameter 4 units <= 5 units evaluates supported; incompatible units fail (AQ49 Subcase 2)."""
        verifier = ConditionVerifier()

        # 4 units <= 5 units (same unit)
        state_le, err_le = verifier.evaluate_quantitative_comparison("le", 4, "days", 5, "days")
        self.assertEqual(state_le, EvidenceState.SUPPORTED)
        self.assertIsNone(err_le)

        # 6 units <= 5 units
        state_ref, _ = verifier.evaluate_quantitative_comparison("le", 6, "days", 5, "days")
        self.assertEqual(state_ref, EvidenceState.REFUTED)

        # Incompatible units
        state_incompat, err_incompat = verifier.evaluate_quantitative_comparison("le", 4, "hours", 5, "days")
        self.assertEqual(state_incompat, EvidenceState.UNKNOWN)
        self.assertIn("Incompatible units", err_incompat)

    # --------------------------------------------------------------------------
    # 3. AQ49 & AQ38: LEAF RESOLUTION ACROSS ALIGNED EVIDENCE
    # --------------------------------------------------------------------------
    def test_aq49_leaf_proposition_resolves_all_aligned_evidence(self) -> None:
        """A proposition resolves across all aligned evidence facts; conflicting reports produce conflicting (AQ49 Subcase 4)."""
        # Scenario 1: Only supporting facts
        verifier_sup = ConditionVerifier([
            {"predicate_ref": {"id": "cond:has_license"}, "subject_ref": {"id": "actor:gamma"}, "value": "supported"},
            {"predicate_ref": {"id": "cond:has_license"}, "subject_ref": {"id": "actor:gamma"}, "value": "supported"},
        ])
        state, matching = verifier_sup.evaluate_leaf_proposition("cond:has_license", "actor:gamma")
        self.assertEqual(state, EvidenceState.SUPPORTED)
        self.assertEqual(len(matching), 2)

        # Scenario 2: Contradictory reports (one support, one refutation) produce CONFLICTING without exploding
        verifier_conf = ConditionVerifier([
            {"predicate_ref": {"id": "cond:has_license"}, "subject_ref": {"id": "actor:gamma"}, "value": "supported"},
            {"predicate_ref": {"id": "cond:has_license"}, "subject_ref": {"id": "actor:gamma"}, "value": "refuted"},
        ])
        state_c, matching_c = verifier_conf.evaluate_leaf_proposition("cond:has_license", "actor:gamma")
        self.assertEqual(state_c, EvidenceState.CONFLICTING)
        self.assertEqual(len(matching_c), 2)

    # --------------------------------------------------------------------------
    # 4. AQ03: KNOWN-UNMET VS UNKNOWN CONDITION
    # --------------------------------------------------------------------------
    def test_aq03_known_unmet_differs_from_unknown(self) -> None:
        """Indispensable refuted prerequisite yields conditions_unmet; unknown yields unresolved."""
        # 1. Condition is explicitly REFUTED
        verifier_ref = ConditionVerifier([
            {"predicate_ref": {"id": "cond:consent"}, "subject_ref": {"id": "actor:subject"}, "value": "refuted"},
        ])
        state_ref = verifier_ref.evaluate_condition_expr({
            "op": "fact",
            "fact_ref": {"id": "cond:consent"},
            "subject_ref": {"id": "actor:subject"},
        })
        self.assertEqual(state_ref, EvidenceState.REFUTED, "Refuted prerequisite must evaluate to REFUTED")

        # 2. Condition is UNKNOWN (no facts on record)
        verifier_unk = ConditionVerifier([])
        state_unk = verifier_unk.evaluate_condition_expr({
            "op": "fact",
            "fact_ref": {"id": "cond:consent"},
            "subject_ref": {"id": "actor:subject"},
        })
        self.assertEqual(state_unk, EvidenceState.UNKNOWN, "Missing prerequisite must evaluate to UNKNOWN")

        # In legal disposition, REFUTED -> conditions_unmet; UNKNOWN -> unresolved
        self.assertNotEqual(state_ref, state_unk)

    # --------------------------------------------------------------------------
    # 5. AQ14: ALL REQUIRED SCOPE DIMENSIONS MUST ALIGN
    # --------------------------------------------------------------------------
    def test_aq14_all_required_scope_dimensions_must_align(self) -> None:
        """Mismatch on territory, person, subject matter, or action excludes rule (AQ14)."""
        required = {
            "territory": "jurisdiction:state_alpha",
            "person": "capacity:licensee",
            "subject_matter": "scope:telecom_records",
            "action": "op:share_record",
        }

        # Matching scope
        matched, errs = ConditionVerifier.verify_scope_alignment(required, required)
        self.assertTrue(matched)
        self.assertEqual(len(errs), 0)

        # Mismatched territory
        presented_wrong_territory = dict(required, territory="jurisdiction:foreign_state")
        matched_t, errs_t = ConditionVerifier.verify_scope_alignment(required, presented_wrong_territory)
        self.assertFalse(matched_t)
        self.assertTrue(any("territory" in e for e in errs_t))

        # Mismatched subject matter
        presented_wrong_sm = dict(required, subject_matter="scope:environmental_waste")
        matched_sm, errs_sm = ConditionVerifier.verify_scope_alignment(required, presented_wrong_sm)
        self.assertFalse(matched_sm)
        self.assertTrue(any("subject_matter" in e for e in errs_sm))

    # --------------------------------------------------------------------------
    # 6. AQ15: MULTIPLE APPLICABLE SCOPES PRESERVE CONSTRAINTS
    # --------------------------------------------------------------------------
    def test_aq15_multiple_applicable_scopes_preserve_constraints(self) -> None:
        """Intersecting scopes with differing duties/prohibitions preserves strictest constraints (AQ15)."""
        scope_broad_permission = {
            "permissions": ["op:share_record", "op:request_record"],
            "prohibitions": [],
            "duties": [],
        }
        scope_narrow_privacy = {
            "permissions": ["op:request_record"],
            "prohibitions": ["op:share_record"],  # Prohibits commercial sharing
            "duties": ["op:retain_record"],
        }

        intersection = ConditionVerifier.intersect_applicable_scopes([scope_broad_permission, scope_narrow_privacy])

        # Prohibition survives and defeats permission for op:share_record
        self.assertIn("op:share_record", intersection["prohibitions"])
        self.assertNotIn("op:share_record", intersection["permissions"])
        self.assertIn("op:retain_record", intersection["duties"])
        self.assertIn("op:request_record", intersection["permissions"])
        self.assertTrue(intersection["has_conflicting_prohibition"])

    # --------------------------------------------------------------------------
    # 7. AQ38: EVIDENCE ALIGNMENT AND LINEAGE PRESERVED
    # --------------------------------------------------------------------------
    def test_aq38_evidence_alignment_and_lineage_are_preserved(self) -> None:
        """Misaligned evidence cannot satisfy conditions; repeated origin is not independent corroboration (AQ38)."""
        # Misalignment on subject or predicate
        facts = [
            {
                "predicate_ref": {"id": "cond:license_active"},
                "subject_ref": {"id": "actor:operator_a"},
                "source_artifact_ref": {"id": "src:report_1"},
                "value": "supported",
            },
            {
                "predicate_ref": {"id": "cond:license_active"},
                "subject_ref": {"id": "actor:operator_a"},
                "source_artifact_ref": {"id": "src:report_1"},  # Same origin!
                "value": "supported",
            },
        ]
        verifier = ConditionVerifier(facts)

        # Misaligned query (different actor) -> UNKNOWN
        state_wrong_subj, matching_wrong = verifier.evaluate_leaf_proposition("cond:license_active", "actor:operator_b")
        self.assertEqual(state_wrong_subj, EvidenceState.UNKNOWN)
        self.assertEqual(len(matching_wrong), 0)

        # Misaligned query (different predicate) -> UNKNOWN
        state_wrong_pred, matching_pred = verifier.evaluate_leaf_proposition("cond:tax_cleared", "actor:operator_a")
        self.assertEqual(state_wrong_pred, EvidenceState.UNKNOWN)
        self.assertEqual(len(matching_pred), 0)

        # Lineage check: require 2 independent sources, but both facts are from src:report_1
        state_corr, origins, _ = verifier.evaluate_corroborated_leaf_proposition(
            "cond:license_active", "actor:operator_a", min_independent_sources=2
        )
        self.assertEqual(state_corr, EvidenceState.UNKNOWN, "Repeated origin cannot satisfy multi-source corroboration")
        self.assertEqual(len(origins), 1)

    # --------------------------------------------------------------------------
    # 8. AQ42: LEGAL EFFECTIVE TIME IS NOT A UOW COUNTER
    # --------------------------------------------------------------------------
    def test_aq42_legal_effective_time_is_not_a_uow_counter(self) -> None:
        """Applicability remains unresolved until declared mapping or calendar evidence establishes relation (AQ42)."""
        eff_from = "2026-01-01T00:00:00Z"
        eff_to = "2026-12-31T23:59:59Z"

        # Raw UoW counter without clock mapping -> UNKNOWN
        state_raw, err = ConditionVerifier.verify_effective_time_interval(
            eff_from, eff_to, case_time="seq:1054", has_calibrated_mapping=False
        )
        self.assertEqual(state_raw, EvidenceState.UNKNOWN)
        self.assertIn("Raw UoW counter", err)

        # Calibrated timestamp inside window -> SUPPORTED
        state_valid, _ = ConditionVerifier.verify_effective_time_interval(
            eff_from, eff_to, case_time="2026-06-15T12:00:00Z", has_calibrated_mapping=True
        )
        self.assertEqual(state_valid, EvidenceState.SUPPORTED)

        # Calibrated timestamp outside window -> REFUTED
        state_expired, err_exp = ConditionVerifier.verify_effective_time_interval(
            eff_from, eff_to, case_time="2027-01-01T00:00:00Z", has_calibrated_mapping=True
        )
        self.assertEqual(state_expired, EvidenceState.REFUTED)
        self.assertIn("exceeds statutory effective_to", err_exp)

    # --------------------------------------------------------------------------
    # ALIASES MATCHING EXACT AQ SUBCASE INDEX NAMES
    # --------------------------------------------------------------------------
    def test_aq03_known_unmet_condition_differs_from_unknown_condition(self) -> None:
        self.test_aq03_known_unmet_differs_from_unknown()

    def test_aq49_four_state_logic_preserves_nonexplosive_uncertainty(self) -> None:
        self.test_aq49_four_state_truth_tables()
        self.test_aq49_quantitative_comparisons_and_units()
        self.test_aq49_leaf_proposition_resolves_all_aligned_evidence()


if __name__ == "__main__":
    unittest.main()
