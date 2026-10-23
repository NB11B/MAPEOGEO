r"""Unit and Integration Tests for Program GEO-X1: Prospective Geometric Reconstruction Qualification.

Validates:
1. Gate G0: Baseline preservation.
2. Gate G1: Structural identification (>=90% correct family on Tier A).
3. Gate G2: Fail-closed zero false metric claims on adversarial controls.
4. Gate G3: Exact symbolic reconstruction (residual = 0.0).
5. Gate G4: Predictive geometry (>=95% accuracy on withheld predictions).
6. Gate G5: Coordinate scrambling robustness.
7. Gate G6: Representation ablation compression advantage (R0 vs R1).
8. Gate G7: Cross-domain transfer outside quantum theory (distance geometry, rigidity, covariance).
9. Gate G8: Prospective novelty verification.
"""
import unittest

from qualification.geometric_reconstruction_v1.campaign_runner import run_geox1_campaign
from qualification.geometric_reconstruction_v1.verifier import verify_geox1_results
from ngc_geometry_lab.prospective_geometric_synthesis import structure_synthesize


class TestGeoX1ProspectiveCampaign(unittest.TestCase):
    """Test suite for GEO-X1 prospective qualification campaign."""

    @classmethod
    def setUpClass(cls):
        """Run campaign once for all test assertions."""
        cls.campaign_report = run_geox1_campaign()

    def test_geox1_all_gates_pass(self):
        """Verify that all 9 quantitative gates (G0 - G8) pass."""
        self.assertTrue(self.campaign_report["all_gates_passed"])
        gates = self.campaign_report["gate_evaluations"]
        for g_name, g_info in gates.items():
            self.assertTrue(g_info["passed"], f"Gate {g_name} failed: {g_info}")

    def test_gate_g1_structural_identification_rate(self):
        """Verify Gate G1: Structural identification >= 90% on Tier A targets."""
        g1 = self.campaign_report["gate_evaluations"]["G1_Structural_Identification"]
        self.assertTrue(g1["passed"])
        self.assertGreaterEqual(g1["rate"], 0.90)

    def test_gate_g2_fail_closed_zero_false_metrics(self):
        """Verify Gate G2: Exactly 0 false metric claims on adversarial controls."""
        g2 = self.campaign_report["gate_evaluations"]["G2_Fail_Closed"]
        self.assertTrue(g2["passed"])
        self.assertEqual(g2["false_metric_claims"], 0)

    def test_gate_g4_predictive_geometry_accuracy(self):
        """Verify Gate G4: Mean predictive accuracy on withheld tests >= 95%."""
        g4 = self.campaign_report["gate_evaluations"]["G4_Predictive_Geometry"]
        self.assertTrue(g4["passed"])
        self.assertGreaterEqual(g4["mean_accuracy"], 0.95)

    def test_gate_g6_ablation_advantage(self):
        """Verify Gate G6: Reconstructed geometry R1 compresses representation over raw R0."""
        g6 = self.campaign_report["gate_evaluations"]["G6_Ablation_Advantage"]
        self.assertTrue(g6["passed"])
        self.assertGreater(g6["mean_compression"], 1.0)

    def test_gate_g7_cross_domain_transfer(self):
        """Verify Gate G7: Unchanged grammar succeeds on non-quantum Tier C targets."""
        g7 = self.campaign_report["gate_evaluations"]["G7_Cross_Domain_Transfer"]
        self.assertTrue(g7["passed"])
        self.assertEqual(g7["tier_c_correct"], 3)

    def test_geox1_verifier_certification(self):
        """Verify that the independent verifier certifies the campaign ledger."""
        res = verify_geox1_results()
        self.assertEqual(res["status"], "QUALIFIED")
        self.assertTrue(res["all_gates_satisfied"])
        self.assertEqual(res["total_targets"], 17)


if __name__ == "__main__":
    unittest.main()
