"""C9 Tertiary Impact & Counterparty Interest Modeling Test Suite.

Verifies:
1. Mathematical involution and correctness of Hohfeldian Jural Correlatives and Opposites.
2. Invariant AQ07: Counterparty right/interest is a constraint, not an operational grant.
3. Third-party statutory immunity blocks operational admission (BLOCKED_BY_IMMUNITY).
4. Third-party claim-right imposes affirmative duty and required safeguards (CONSTRAINED_SAFEGUARD_REQUIRED).
"""

from __future__ import annotations

import unittest

from mapeogeo.domains.authority import (
    CounterpartyInterestEvaluator,
    HOHFELDIAN_CORRELATIVES,
    HOHFELDIAN_OPPOSITES,
    HohfeldianModality,
    ImpactAssessmentReport,
    ImpactConstraintStatus,
    TertiaryExposureRecord,
)


class TestC9TertiaryImpact(unittest.TestCase):
    def test_c9_1_hohfeldian_system_involutions(self) -> None:
        """Asserts that Jural Correlatives and Opposites form involutive bijections over all 8 modalities."""
        modalities = list(HohfeldianModality)
        self.assertEqual(len(modalities), 8)

        for m in modalities:
            # Involution of correlatives: Correlative(Correlative(m)) == m
            corr = HOHFELDIAN_CORRELATIVES[m]
            self.assertEqual(HOHFELDIAN_CORRELATIVES[corr], m, f"Correlative not involutive for {m}")

            # Involution of opposites: Opposite(Opposite(m)) == m
            opp = HOHFELDIAN_OPPOSITES[m]
            self.assertEqual(HOHFELDIAN_OPPOSITES[opp], m, f"Opposite not involutive for {m}")

            # Correlative and Opposite are distinct
            self.assertNotEqual(corr, opp, f"Correlative and opposite collapsed for {m}")

        # Canonical pairs
        self.assertEqual(HOHFELDIAN_CORRELATIVES[HohfeldianModality.RIGHT], HohfeldianModality.DUTY)
        self.assertEqual(HOHFELDIAN_CORRELATIVES[HohfeldianModality.PRIVILEGE], HohfeldianModality.NO_RIGHT)
        self.assertEqual(HOHFELDIAN_CORRELATIVES[HohfeldianModality.POWER], HohfeldianModality.LIABILITY)
        self.assertEqual(HOHFELDIAN_CORRELATIVES[HohfeldianModality.IMMUNITY], HohfeldianModality.DISABILITY)

        self.assertEqual(HOHFELDIAN_OPPOSITES[HohfeldianModality.RIGHT], HohfeldianModality.NO_RIGHT)
        self.assertEqual(HOHFELDIAN_OPPOSITES[HohfeldianModality.PRIVILEGE], HohfeldianModality.DUTY)
        self.assertEqual(HOHFELDIAN_OPPOSITES[HohfeldianModality.POWER], HohfeldianModality.DISABILITY)
        self.assertEqual(HOHFELDIAN_OPPOSITES[HohfeldianModality.IMMUNITY], HohfeldianModality.LIABILITY)

    def test_c9_2_aq07_immunity_blocks_operational_action(self) -> None:
        """Third party holding statutory IMMUNITY creates DISABILITY in actor, blocking operation."""
        evaluator = CounterpartyInterestEvaluator()
        evaluator.register_interest(
            entity_id="actor:citizen:whistleblower",
            interest_ref="interest:whistleblower_statutory_immunity",
            modality=HohfeldianModality.IMMUNITY,
        )

        case = {
            "id": "case:subpoena_telecom_data",
            "actor_ref": {"id": "actor:investigator:beta"},
            "affected_scope": {
                "bindings": [
                    {"entity_ref": {"id": "actor:telecom:provider"}},
                    {"entity_ref": {"id": "actor:citizen:whistleblower"}},
                ]
            },
        }

        report = evaluator.assess_impact(case)
        self.assertEqual(report.overall_constraint_status, ImpactConstraintStatus.BLOCKED_BY_IMMUNITY)
        self.assertFalse(report.can_proceed)
        self.assertEqual(len(report.exposures), 1)
        exp = report.exposures[0]
        self.assertEqual(exp.third_party_id, "actor:citizen:whistleblower")
        self.assertEqual(exp.protected_modality, HohfeldianModality.IMMUNITY)
        self.assertEqual(exp.correlative_actor_modality, HohfeldianModality.DISABILITY)

    def test_c9_3_claim_right_imposes_safeguard_constraint(self) -> None:
        """Third party holding claim-right imposes correlative duty and mandatory safeguard."""
        evaluator = CounterpartyInterestEvaluator()
        evaluator.register_interest(
            entity_id="actor:client:enterprise_co",
            interest_ref="interest:trade_secret_confidentiality",
            modality=HohfeldianModality.RIGHT,
        )

        case = {
            "id": "case:routine_inspection",
            "actor_ref": {"id": "actor:auditor:delta"},
            "affected_scope": {
                "bindings": [
                    {"entity_ref": {"id": "actor:client:enterprise_co"}}
                ]
            },
        }

        report = evaluator.assess_impact(case)
        self.assertEqual(report.overall_constraint_status, ImpactConstraintStatus.CONSTRAINED_SAFEGUARD_REQUIRED)
        self.assertTrue(report.can_proceed)
        self.assertEqual(len(report.exposures), 1)
        exp = report.exposures[0]
        self.assertEqual(exp.protected_modality, HohfeldianModality.RIGHT)
        self.assertEqual(exp.correlative_actor_modality, HohfeldianModality.DUTY)
        self.assertIsNotNone(exp.required_safeguard)

    def test_c9_4_unconstrained_action_without_tertiary_exposure(self) -> None:
        """Action touching no protected third-party interests evaluates to UNCONSTRAINED."""
        evaluator = CounterpartyInterestEvaluator()
        case = {
            "id": "case:internal_carrier_telemetry",
            "actor_ref": {"id": "actor:carrier:alpha"},
            "affected_scope": {
                "bindings": [
                    {"entity_ref": {"id": "actor:carrier:alpha"}}
                ]
            },
        }
        report = evaluator.assess_impact(case)
        self.assertEqual(report.overall_constraint_status, ImpactConstraintStatus.UNCONSTRAINED)
        self.assertTrue(report.can_proceed)
        self.assertEqual(len(report.exposures), 0)


if __name__ == "__main__":
    unittest.main()
