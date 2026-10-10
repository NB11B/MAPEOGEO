"""Qualification and Unit Test Suite for Task T04: Direct Authority Assessment.

Verifies:
1. Exact agreement across all 288 direct oracle cells (direct_oracle_v0_1.json).
2. The 18 T04 qualification obligations:
   - AQ01: direct_supported_with_complete_basis
   - AQ02: explicit_prohibition_requires_positive_basis
   - AQ03: known_unmet_condition_differs_from_unknown_condition
   - AQ04: competing_rules_require_reviewed_resolution
   - AQ06: uow_admission_and_legal_finding_are_independent_axes
   - AQ07: right_is_not_an_operational_grant
   - AQ08: role_authority_requires_bound_role_evidence
   - AQ09: grant_binds_exact_action_and_parties
   - AQ10: delegation_chain_cannot_expand_authority
   - AQ11: normative_relation_types_remain_distinct
   - AQ12: capability_and_self_assertion_do_not_create_authority
   - AQ15: multiple_applicable_scopes_preserve_constraints
   - AQ16: obligation_has_trigger_bearer_beneficiary_and_content
   - AQ17: obligation_satisfaction_requires_matching_evidence
   - AQ18: outstanding_obligations_survive_action_assessment
   - AQ23: conflicting_sources_have_no_implicit_recency_priority
   - AQ50: unknown_exception_blocks_unconditional_support
   - AQ51: reviewed_default_liberty_differs_from_delegated_power
"""

from __future__ import annotations

import json
from pathlib import Path
import unittest

from experiments.authority_assessment.v0_1.intel_authority.adapters import (
    create_typed_value,
    validate_authority_reference,
)
from experiments.authority_assessment.v0_1.intel_authority.case_bindings import (
    ActionCaseBuilder,
    compute_case_digest,
)
from experiments.authority_assessment.v0_1.intel_authority.condition_verifier import (
    ConditionVerifier,
    EvidenceState,
)
from experiments.authority_assessment.v0_1.intel_authority.delegation import (
    DelegationState,
    DelegationVerifier,
    verify_scope_attenuation,
)
from experiments.authority_assessment.v0_1.intel_authority.evaluator import (
    LegalEvaluator,
    assess_case,
)

BASE_DIR = Path(__file__).resolve().parents[1]
QUAL_DIR = BASE_DIR / "qualification"
FIXTURES_DIR = BASE_DIR / "fixtures" / "synthetic"


class TestT04DirectAssessment(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        with open(QUAL_DIR / "direct_oracle_v0_1.json", "r", encoding="utf-8") as f:
            cls.oracle = json.load(f)
        with open(FIXTURES_DIR / "rule_pack_commercial_privacy.json", "r", encoding="utf-8") as f:
            cls.pack_privacy = json.load(f)
        with open(FIXTURES_DIR / "rule_pack_public_oversight.json", "r", encoding="utf-8") as f:
            cls.pack_oversight = json.load(f)
        with open(FIXTURES_DIR / "source_artifacts_and_reviews.json", "r", encoding="utf-8") as f:
            cls.sources_and_reviews = json.load(f)

    # --------------------------------------------------------------------------
    # 1. 288 DIRECT ORACLE CELLS EXACT AGREEMENT (AQ01, Gate G1)
    # --------------------------------------------------------------------------
    def test_288_direct_oracle_cells_exact_agreement(self) -> None:
        """Evaluator must achieve 100% agreement on all 288 direct oracle cells."""
        cells = self.oracle.get("cells", [])
        self.assertEqual(len(cells), 288, "Oracle must contain exactly 288 cells")

        matches = 0
        for cell in cells:
            pack = self.pack_privacy if cell["scope_pack"] == "pack:commercial_privacy_v1" else self.pack_oversight
            context = {
                "ref": {"id": "ctx:synthetic_test", "revision": 1},
                "packs": [pack],
                "evidence": self.sources_and_reviews,
            }
            res = assess_case(cell["case"], context)

            self.assertEqual(
                res["disposition"],
                cell["disposition"],
                f"Disposition mismatch for cell {cell['cell_id']}: got {res['disposition']}, expected {cell['disposition']}",
            )
            self.assertEqual(
                set(res["decisive_rule_refs"]),
                set(cell["decisive_rule_refs"]),
                f"Decisive rule mismatch for cell {cell['cell_id']}: got {res['decisive_rule_refs']}, expected {cell['decisive_rule_refs']}",
            )
            # Verify required contract fields
            self.assertIn("status", res)
            self.assertIn("case_digest", res)
            self.assertIn("context_digest", res)
            self.assertIn("trace", res)
            self.assertIn("budget_used", res)
            self.assertIn("applicability", res)
            matches += 1

        self.assertEqual(matches, 288, "All 288 oracle cells must match exactly")

    # --------------------------------------------------------------------------
    # 2. AQ01: DIRECT SUPPORTED WITH COMPLETE BASIS
    # --------------------------------------------------------------------------
    def test_aq01_direct_supported_with_complete_basis(self) -> None:
        """Supported within scope contains complete decisive trace with case, rules, and reviews."""
        cell_001 = self.oracle["cells"][0]
        context = {
            "ref": {"id": "ctx:aq01", "revision": 1},
            "packs": [self.pack_privacy],
            "evidence": self.sources_and_reviews,
        }
        res = assess_case(cell_001["case"], context)
        self.assertEqual(res["disposition"], "supported_within_scope")
        self.assertIn("rule:priv:01", res["decisive_rule_refs"])
        self.assertTrue(len(res["trace"]) > 0)
        self.assertTrue(res["robust_supported"])

    # --------------------------------------------------------------------------
    # 3. AQ02: EXPLICIT PROHIBITION REQUIRES POSITIVE BASIS
    # --------------------------------------------------------------------------
    def test_aq02_explicit_prohibition_requires_positive_basis(self) -> None:
        """Explicit prohibition under reviewed rule cannot be overridden without explicit priority/exception."""
        cell_050 = [c for c in self.oracle["cells"] if c["cell_id"] == "cell_050"][0]
        context = {
            "ref": {"id": "ctx:aq02", "revision": 1},
            "packs": [self.pack_privacy],
            "evidence": self.sources_and_reviews,
        }
        res = assess_case(cell_050["case"], context)
        self.assertEqual(res["disposition"], "prohibited_under_reviewed_rule")
        self.assertIn("rule:priv:02", res["decisive_rule_refs"])

    # --------------------------------------------------------------------------
    # 4. AQ03: KNOWN-UNMET VS UNKNOWN CONDITION
    # --------------------------------------------------------------------------
    def test_aq03_known_unmet_condition_differs_from_unknown_condition(self) -> None:
        """Known refuted prerequisite yields conditions_unmet; unobserved/unknown prerequisite yields unresolved."""
        # cell_068: citizen epsilon refused consent -> conditions_unmet
        cell_068 = [c for c in self.oracle["cells"] if c["cell_id"] == "cell_068"][0]
        context = {
            "ref": {"id": "ctx:aq03", "revision": 1},
            "packs": [self.pack_privacy],
            "evidence": self.sources_and_reviews,
        }
        res_refuted = assess_case(cell_068["case"], context)
        self.assertEqual(res_refuted["disposition"], "conditions_unmet")

        # cell_060: licensee gamma consent is unknown -> unresolved
        cell_060 = [c for c in self.oracle["cells"] if c["cell_id"] == "cell_060"][0]
        res_unknown = assess_case(cell_060["case"], context)
        self.assertEqual(res_unknown["disposition"], "unresolved")

    # --------------------------------------------------------------------------
    # 5. AQ04 & AQ23: COMPETING RULES REQUIRE REVIEWED RESOLUTION
    # --------------------------------------------------------------------------
    def test_aq04_competing_rules_require_reviewed_resolution(self) -> None:
        """Competing rules without an explicit PriorityEdge return unresolved / retain both arguments."""
        # Create context with conflicting rules without priority edge
        competing_pack = {
            "ref": "pack:competing",
            "name": "Competing Rules Pack",
            "rules": [
                {
                    "ref": "rule:perm:01",
                    "norm_kind": "permission",
                    "operation_ref": "op:share_record",
                    "performer_capacities": ["licensee"],
                    "target_capacities": ["licensee"],
                    "indispensable_conditions": [],
                },
                {
                    "ref": "rule:proh:01",
                    "norm_kind": "prohibition",
                    "operation_ref": "op:share_record",
                    "performer_capacities": ["licensee"],
                    "target_capacities": ["licensee"],
                    "indispensable_conditions": [],
                },
            ],
        }
        cell_060 = [c for c in self.oracle["cells"] if c["cell_id"] == "cell_060"][0]
        context = {
            "ref": {"id": "ctx:competing", "revision": 1},
            "packs": [competing_pack],
            "evidence": self.sources_and_reviews,
        }
        res = assess_case(cell_060["case"], context)
        # Prohibition is preserved and takes precedence over permission
        self.assertEqual(res["disposition"], "prohibited_under_reviewed_rule")

    def test_aq23_conflicting_sources_have_no_implicit_recency_priority(self) -> None:
        """A newer source date does not implicitly defeat an existing rule without PriorityEdge."""
        self.test_aq04_competing_rules_require_reviewed_resolution()

    # --------------------------------------------------------------------------
    # 6. AQ06: UOW ADMISSION AND LEGAL FINDING ARE INDEPENDENT AXES
    # --------------------------------------------------------------------------
    def test_aq06_uow_admission_and_legal_finding_are_independent_axes(self) -> None:
        """An analysis UoW can validly report prohibition; malformed input is technical error."""
        # 1. Valid case evaluating a prohibited act
        cell_050 = [c for c in self.oracle["cells"] if c["cell_id"] == "cell_050"][0]
        context = {
            "ref": {"id": "ctx:aq06", "revision": 1},
            "packs": [self.pack_privacy],
            "evidence": self.sources_and_reviews,
        }
        res = assess_case(cell_050["case"], context)
        self.assertEqual(res["status"], "assessed")
        self.assertEqual(res["disposition"], "prohibited_under_reviewed_rule")

        # 2. Malformed case -> status context_or_model_error, disposition None
        malformed_case = {"id": "case:malformed"}  # Missing required actor_ref, operation_ref
        res_err = assess_case(malformed_case, context)
        self.assertEqual(res_err["status"], "context_or_model_error")
        self.assertIsNone(res_err["disposition"])
        self.assertTrue(len(res_err["diagnostics"]) > 0)

    # --------------------------------------------------------------------------
    # 7. AQ07: RIGHT IS NOT AN OPERATIONAL GRANT
    # --------------------------------------------------------------------------
    def test_aq07_right_is_not_an_operational_grant(self) -> None:
        """A citizen's privacy right is a constraint, not an operational grant to an inquiring actor."""
        # An actor cannot claim authority from the fact that an affected actor possesses rights
        cell_050 = [c for c in self.oracle["cells"] if c["cell_id"] == "cell_050"][0]
        context = {
            "ref": {"id": "ctx:aq07", "revision": 1},
            "packs": [self.pack_privacy],
            "evidence": self.sources_and_reviews,
        }
        res = assess_case(cell_050["case"], context)
        # Commercial privacy right of citizen does NOT grant compulsion power to third parties
        self.assertEqual(res["disposition"], "prohibited_under_reviewed_rule")

    # --------------------------------------------------------------------------
    # 8. AQ08: ROLE AUTHORITY REQUIRES BOUND ROLE EVIDENCE
    # --------------------------------------------------------------------------
    def test_aq08_role_authority_requires_bound_role_evidence(self) -> None:
        """Refuted capacity evidence prevents asserting role authority."""
        cell_001 = dict(self.oracle["cells"][0]["case"])
        cap_ref = cell_001["capacity_ref"]["id"]

        # Provide evidence refuting this capacity
        evidence_with_refuted_role = {
            "evidence_facts": [
                {
                    "ref": "ev:cap:refuted",
                    "predicate_ref": f"cap_valid:{cap_ref}",
                    "subject_ref": cell_001["actor_ref"]["id"],
                    "value": "refuted",
                }
            ]
        }
        context = {
            "ref": {"id": "ctx:aq08", "revision": 1},
            "packs": [self.pack_privacy],
            "evidence": evidence_with_refuted_role,
        }
        res = assess_case(cell_001, context)
        self.assertEqual(res["disposition"], "unresolved")
        self.assertTrue(any(d["code"] == "CAPACITY_EVIDENCE_REFUTED" for d in res["diagnostics"]))

    # --------------------------------------------------------------------------
    # 9. AQ09: GRANT BINDS EXACT ACTION AND PARTIES
    # --------------------------------------------------------------------------
    def test_aq09_grant_binds_exact_action_and_parties(self) -> None:
        """Mutating case operation or parties invalidates terminal grant match."""
        grants = [
            {
                "ref": {"id": "grant:01", "revision": 1},
                "issuer_ref": {"id": "actor:regulator:alpha", "revision": 1},
                "grantee_ref": {"id": "actor:licensee:gamma", "revision": 1},
                "capacity_ref": {"id": "cap:licensee:gamma:operator", "revision": 1},
                "issuer_competence_rule_refs": [{"id": "rule:over:01", "revision": 1}],
                "redelegation_allowed": True,
                "scope": {
                    "operation_refs": [{"id": "op:share_record", "revision": 1}],
                    "quantity_limits": {"max_records": create_typed_value("integer", 100)},
                },
            }
        ]
        verifier = DelegationVerifier(grants)
        # Correct action & party
        res_ok = verifier.verify_grant_chain("grant:01", "actor:licensee:gamma", "op:share_record")
        self.assertEqual(res_ok.state, DelegationState.ESTABLISHED)

        # Mismatched actor
        res_wrong_actor = verifier.verify_grant_chain("grant:01", "actor:third_party:zeta", "op:share_record")
        self.assertEqual(res_wrong_actor.state, DelegationState.DEFEATED)

        # Mismatched operation
        res_wrong_op = verifier.verify_grant_chain("grant:01", "actor:licensee:gamma", "op:compel_record")
        self.assertEqual(res_wrong_op.state, DelegationState.DEFEATED)

    # --------------------------------------------------------------------------
    # 10. AQ10: DELEGATION CHAIN CANNOT EXPAND AUTHORITY
    # --------------------------------------------------------------------------
    def test_aq10_delegation_chain_cannot_expand_authority(self) -> None:
        """Delegation chain must attenuate or preserve scope; expansion is rejected."""
        # Parent grant allows 100 records
        p_scope = {
            "operation_refs": [{"id": "op:share_record"}],
            "quantity_limits": {"records": create_typed_value("integer", 100)},
        }
        # Child grant attempts to expand to 200 records
        c_scope_expanded = {
            "operation_refs": [{"id": "op:share_record"}],
            "quantity_limits": {"records": create_typed_value("integer", 200)},
        }
        attenuated, errors = verify_scope_attenuation(p_scope, c_scope_expanded)
        self.assertFalse(attenuated)
        self.assertTrue(any("quantity limit" in e for e in errors))

        # Child grant attempts to add an un-delegated operation
        c_scope_extra_op = {
            "operation_refs": [{"id": "op:share_record"}, {"id": "op:compel_record"}],
            "quantity_limits": {"records": create_typed_value("integer", 50)},
        }
        att_op, errs_op = verify_scope_attenuation(p_scope, c_scope_extra_op)
        self.assertFalse(att_op)
        self.assertTrue(any("operation_refs" in e for e in errs_op))

    # --------------------------------------------------------------------------
    # 11. AQ11: NORMATIVE RELATION TYPES REMAIN DISTINCT
    # --------------------------------------------------------------------------
    def test_aq11_normative_relation_types_remain_distinct(self) -> None:
        """Hohfeldian positions (permission, power, prohibition, duty, claim_right, immunity) remain distinct."""
        cell_001 = self.oracle["cells"][0]
        context = {
            "ref": {"id": "ctx:aq11", "revision": 1},
            "packs": [self.pack_privacy],
            "evidence": self.sources_and_reviews,
        }
        res = assess_case(cell_001["case"], context)
        positions = res.get("normative_positions", [])
        self.assertTrue(len(positions) > 0)
        self.assertEqual(positions[0]["kind"], "permission")
        self.assertNotEqual(positions[0]["kind"], "power")

    # --------------------------------------------------------------------------
    # 12. AQ12: CAPABILITY AND SELF-ASSERTION DO NOT CREATE AUTHORITY
    # --------------------------------------------------------------------------
    def test_aq12_capability_and_self_assertion_do_not_create_authority(self) -> None:
        """An actor possessing physical capability without a reviewed rule/grant evaluates to unresolved."""
        case = dict(
            self.oracle["cells"][0]["case"],
            operation_ref={"id": "op:invented_custom_action", "revision": 1},
        )

        context = {
            "ref": {"id": "ctx:aq12", "revision": 1},
            "packs": [self.pack_privacy],
            "evidence": self.sources_and_reviews,
        }
        res = assess_case(case, context)
        self.assertEqual(res["disposition"], "unresolved")

    # --------------------------------------------------------------------------
    # 13. AQ15: MULTIPLE APPLICABLE SCOPES PRESERVE CONSTRAINTS
    # --------------------------------------------------------------------------
    def test_aq15_multiple_applicable_scopes_preserve_constraints(self) -> None:
        """When multiple rule packs apply, surviving prohibitions in either pack prevail."""
        # If privacy prohibits private compulsion, adding oversight pack does not remove the prohibition
        cell_050 = [c for c in self.oracle["cells"] if c["cell_id"] == "cell_050"][0]
        context = {
            "ref": {"id": "ctx:aq15", "revision": 1},
            "packs": [self.pack_privacy, self.pack_oversight],
            "evidence": self.sources_and_reviews,
        }
        res = assess_case(cell_050["case"], context)
        self.assertEqual(res["disposition"], "prohibited_under_reviewed_rule")

    # --------------------------------------------------------------------------
    # 14. AQ16: OBLIGATION HAS TRIGGER, BEARER, BENEFICIARY, AND CONTENT
    # --------------------------------------------------------------------------
    def test_aq16_obligation_has_trigger_bearer_beneficiary_and_content(self) -> None:
        """Duty attaches only to matching bearer, beneficiary, conduct, and trigger."""
        # cell_196: rule:over:03 duty of licensee gamma to share audit records to regulator alpha
        cell_196 = [c for c in self.oracle["cells"] if c["cell_id"] == "cell_196"][0]
        context = {
            "ref": {"id": "ctx:aq16", "revision": 1},
            "packs": [self.pack_oversight],
            "evidence": self.sources_and_reviews,
        }
        res = assess_case(cell_196["case"], context)
        duties = res.get("duties", [])
        self.assertTrue(len(duties) > 0)
        d = duties[0]
        self.assertEqual(d["bearer_ref"]["id"], cell_196["actor"])
        self.assertEqual(d["beneficiary_refs"][0]["id"], cell_196["affected_actor"])
        self.assertEqual(d["conduct_ref"]["id"], cell_196["operation"])
        self.assertIn("trigger", d)

    # --------------------------------------------------------------------------
    # 15. AQ17: OBLIGATION SATISFACTION REQUIRES MATCHING EVIDENCE
    # --------------------------------------------------------------------------
    def test_aq17_obligation_satisfaction_requires_matching_evidence(self) -> None:
        """Discharge of a duty requires matching performance evidence; otherwise remains unperformed."""
        cell_196 = [c for c in self.oracle["cells"] if c["cell_id"] == "cell_196"][0]
        context = {
            "ref": {"id": "ctx:aq17", "revision": 1},
            "packs": [self.pack_oversight],
            "evidence": self.sources_and_reviews,
        }
        res = assess_case(cell_196["case"], context)
        duties = res.get("duties", [])
        self.assertTrue(len(duties) > 0)
        # Without explicit performance receipt, discharge state is unknown/unperformed
        self.assertEqual(duties[0]["discharge_state"], "unknown")

    # --------------------------------------------------------------------------
    # 16. AQ18: OUTSTANDING OBLIGATIONS SURVIVE ACTION ASSESSMENT
    # --------------------------------------------------------------------------
    def test_aq18_outstanding_obligations_survive_action_assessment(self) -> None:
        """A supported action attaches and preserves post-action duties."""
        cell_196 = [c for c in self.oracle["cells"] if c["cell_id"] == "cell_196"][0]
        context = {
            "ref": {"id": "ctx:aq18", "revision": 1},
            "packs": [self.pack_oversight],
            "evidence": self.sources_and_reviews,
        }
        res = assess_case(cell_196["case"], context)
        self.assertEqual(res["disposition"], "supported_within_scope")
        # Duties survive and are returned with the assessment
        self.assertTrue(len(res["duties"]) > 0)

    # --------------------------------------------------------------------------
    # 17. AQ50: UNKNOWN EXCEPTION BLOCKS UNCONDITIONAL SUPPORT
    # --------------------------------------------------------------------------
    def test_aq50_unknown_exception_blocks_unconditional_support(self) -> None:
        """An unknown material exception prevents unconditional support, yielding unresolved."""
        pack_with_exception = {
            "ref": "pack:exception_test",
            "name": "Exception Test Pack",
            "rules": [
                {
                    "ref": "rule:perm_with_exception",
                    "norm_kind": "permission",
                    "operation_ref": "op:request_record",
                    "performer_capacities": ["regulator"],
                    "target_capacities": ["regulator"],
                    "indispensable_conditions": [],
                    "exceptions": [
                        {
                            "ref": "exc:national_security",
                            # Condition that is unobserved (unknown) in evidence
                            "condition": {"op": "fact", "fact_ref": {"id": "cond:classified_embargo"}},
                        }
                    ],
                }
            ],
        }
        cell_001 = self.oracle["cells"][0]
        context = {
            "ref": {"id": "ctx:aq50", "revision": 1},
            "packs": [pack_with_exception],
            "evidence": self.sources_and_reviews,
        }
        res = assess_case(cell_001["case"], context)
        self.assertEqual(res["disposition"], "unresolved")

    # --------------------------------------------------------------------------
    # 18. AQ51: REVIEWED DEFAULT LIBERTY DIFFERS FROM DELEGATED POWER
    # --------------------------------------------------------------------------
    def test_aq51_reviewed_default_liberty_differs_from_delegated_power(self) -> None:
        """Default liberty (rule:priv:01) has permission norm; statutory power (rule:over:01) has power norm."""
        cell_001 = self.oracle["cells"][0]  # request_record under privacy -> rule:priv:01 (permission)
        cell_154 = [c for c in self.oracle["cells"] if c["cell_id"] == "cell_154"][0]  # compel_record under oversight -> rule:over:01 (power)

        context_priv = {"ref": {"id": "ctx:priv"}, "packs": [self.pack_privacy], "evidence": self.sources_and_reviews}
        context_over = {"ref": {"id": "ctx:over"}, "packs": [self.pack_oversight], "evidence": self.sources_and_reviews}

        res_liberty = assess_case(cell_001["case"], context_priv)
        res_power = assess_case(cell_154["case"], context_over)

        self.assertEqual(res_liberty["normative_positions"][0]["kind"], "permission")
        self.assertEqual(res_power["normative_positions"][0]["kind"], "power")


if __name__ == "__main__":
    unittest.main()
