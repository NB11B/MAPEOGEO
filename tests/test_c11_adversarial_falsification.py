"""C11 Adversarial Robustness & Falsification Test Suite.

Verifies:
1. Circular delegation detection: Cycle terminates deterministically without stack overflow (AQ10).
2. Scope escalation prevention: Delegate cannot exceed attenuated grant scope (AQ10).
3. Antinomy and unknown exception: Unknown material exception blocks unconditional support (AQ50).
4. No Law by Silence: Unmapped operations yield UNRESOLVED, never default liberty (AQ24).
5. Self-assertion rejection: Actor self-granting authority without reviewed instrument is rejected (AQ12).
"""

from __future__ import annotations

import json
from pathlib import Path
import unittest

from mapeogeo.domains.authority import (
    AuthorityCertificateWitness,
    AuthorityDisposition,
    AuthorityEvaluator,
    CertificateOutcome,
    DelegationChainEvaluator,
    LegalPackIntake,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = REPO_ROOT / "experiments" / "authority_assessment" / "v0_1" / "fixtures" / "synthetic"


class TestC11AdversarialRobustness(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with open(FIXTURES_DIR / "rule_pack_commercial_privacy.json", "r", encoding="utf-8") as f:
            cls.pack_privacy = json.load(f)
        with open(FIXTURES_DIR / "source_artifacts_and_reviews.json", "r", encoding="utf-8") as f:
            cls.sources_and_reviews = json.load(f)

    # --------------------------------------------------------------------------
    # 1. CIRCULAR DELEGATION DETECTION (AQ10)
    # --------------------------------------------------------------------------
    def test_c11_1_circular_delegation_cycle_detection(self) -> None:
        """Circular delegation A -> B -> C -> A is detected and rejected without recursion error."""
        grants = [
            {
                "ref": {"id": "grant:01", "revision": 1},
                "issuer_ref": {"id": "actor:corp:alpha", "revision": 1},
                "grantee_ref": {"id": "actor:agent:beta", "revision": 1},
                "parent_grant_ref": {"id": "grant:03", "revision": 1},
                "redelegation_allowed": True,
            },
            {
                "ref": {"id": "grant:02", "revision": 1},
                "issuer_ref": {"id": "actor:agent:beta", "revision": 1},
                "grantee_ref": {"id": "actor:subagent:gamma", "revision": 1},
                "parent_grant_ref": {"id": "grant:01", "revision": 1},
                "redelegation_allowed": True,
            },
            {
                "ref": {"id": "grant:03", "revision": 1},
                "issuer_ref": {"id": "actor:subagent:gamma", "revision": 1},
                "grantee_ref": {"id": "actor:corp:alpha", "revision": 1},
                "parent_grant_ref": {"id": "grant:02", "revision": 1},
                "redelegation_allowed": True,
            },
        ]
        evaluator = DelegationChainEvaluator(grants=grants)
        res = evaluator.verify_grant_chain("grant:02", "actor:subagent:gamma", "op:execute_trade")
        self.assertEqual(res.state.value, "defeated")
        self.assertTrue(any(d["code"] == "DELEGATION_CYCLE" for d in res.diagnostics))

    # --------------------------------------------------------------------------
    # 2. SCOPE ESCALATION REJECTION (AQ10)
    # --------------------------------------------------------------------------
    def test_c11_2_scope_escalation_rejection(self) -> None:
        """Delegate with attenuated scope cannot exceed parent quantity limits or operations."""
        parent_scope = {
            "operation_refs": [{"id": "op:request_record"}],
            "quantity_limits": {"max_records": 100},
        }
        child_escalated_scope = {
            "operation_refs": [{"id": "op:request_record"}, {"id": "op:compel_record"}],
            "quantity_limits": {"max_records": 500},
        }
        evaluator = DelegationChainEvaluator()
        valid, errors = evaluator.verify_scope_attenuation(parent_scope, child_escalated_scope)
        self.assertFalse(valid)
        self.assertTrue(any("Delegation expansion" in e for e in errors))

    # --------------------------------------------------------------------------
    # 3. UNKNOWN MATERIAL EXCEPTION BLOCKS UNCONDITIONAL SUPPORT (AQ50)
    # --------------------------------------------------------------------------
    def test_c11_3_unknown_exception_blocks_unconditional_support_aq50(self) -> None:
        """AQ50: Unknown material exception prevents unconditional support; yields UNRESOLVED."""
        pack_with_unknown_exception = {
            "ref": "pack:aq50_test",
            "name": "Pack with Unknown Material Exception",
            "rules": [
                {
                    "ref": "rule:liberty_with_exception",
                    "name": "Conditional Liberty",
                    "norm_kind": "permission",
                    "operation_ref": "op:inspect_telemetry",
                    "performer_capacities": ["auditor"],
                    "target_capacities": ["licensee"],
                    "priority": 100,
                    "indispensable_conditions": [],
                    "exceptions": [
                        {
                            "id": "exc:national_security",
                            "condition": {
                                "op": "fact",
                                "fact_ref": {"id": "cond:classified_embargo"},
                                "subject_ref": {"id": "actor:licensee:gamma"},
                            },
                        }
                    ],
                }
            ],
        }

        context = {
            "ref": {"id": "ctx:aq50", "revision": 1},
            "packs": [pack_with_unknown_exception],
            "evidence": {},  # No evidence provided for exception -> UNKNOWN
        }
        evaluator = AuthorityEvaluator(context)

        case = {
            "id": "case:inspect_with_unknown_exception",
            "actor_ref": {"id": "actor:auditor:delta"},
            "capacity_ref": {"id": "cap:auditor"},
            "affected_scope": {
                "bindings": [{"entity_ref": {"id": "actor:licensee:gamma"}}]
            },
            "operation_ref": {"id": "op:inspect_telemetry"},
        }

        res = evaluator.assess_case(case)
        self.assertEqual(res.get("disposition"), "unresolved")
        witness = evaluator.certify_work(case)
        self.assertEqual(witness.outcome, CertificateOutcome.UNRESOLVED)
        self.assertTrue(witness.is_unresolved)

    # --------------------------------------------------------------------------
    # 4. NO LAW BY SILENCE (AQ24)
    # --------------------------------------------------------------------------
    def test_c11_4_no_law_by_silence(self) -> None:
        """Unmapped operations yield UNRESOLVED; silence is never permissive authorization."""
        context = {
            "ref": {"id": "ctx:silence", "revision": 1},
            "packs": [self.pack_privacy],
            "evidence": self.sources_and_reviews,
        }
        evaluator = AuthorityEvaluator(context)

        # Completely unmentioned operation
        case_unmapped_op = {
            "id": "case:silence:expropriate_frequency",
            "actor_ref": {"id": "actor:regulator:alpha"},
            "capacity_ref": {"id": "cap:regulator"},
            "affected_scope": {
                "bindings": [{"entity_ref": {"id": "actor:licensee:gamma"}}]
            },
            "operation_ref": {"id": "op:unmapped_novel_kinetic_action"},
        }

        res = evaluator.assess_case(case_unmapped_op)
        self.assertEqual(res.get("disposition"), "unresolved")
        witness = evaluator.certify_work(case_unmapped_op)
        self.assertEqual(witness.outcome, CertificateOutcome.UNRESOLVED)
        self.assertFalse(witness.is_certified)

    # --------------------------------------------------------------------------
    # 5. SELF-ASSERTION WITHOUT AUTHORITY (AQ12)
    # --------------------------------------------------------------------------
    def test_c11_5_self_assertion_rejection(self) -> None:
        """Actor declaring its own authority without reviewed rule pack is rejected."""
        empty_context = {
            "ref": {"id": "ctx:empty", "revision": 1},
            "packs": [],  # No reviewed packs
            "evidence": {},
        }
        evaluator = AuthorityEvaluator(empty_context)

        case = {
            "id": "case:self_asserted_order",
            "actor_ref": {"id": "actor:rogue:operator"},
            "capacity_ref": {"id": "cap:self_declared_commander"},
            "affected_scope": {
                "bindings": [{"entity_ref": {"id": "actor:licensee:gamma"}}]
            },
            "operation_ref": {"id": "op:compel_record"},
        }

        res = evaluator.assess_case(case)
        self.assertEqual(res.get("disposition"), "unresolved")
        witness = evaluator.certify_work(case)
        self.assertFalse(witness.is_certified)


if __name__ == "__main__":
    unittest.main()
