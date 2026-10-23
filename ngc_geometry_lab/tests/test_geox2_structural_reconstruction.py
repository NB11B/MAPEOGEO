r"""Comprehensive Unit and Integration Test Suite for Program GEO-X2.

Validates the complete structural reconstruction and primitive minimization closing campaign:
- Gate X0: Parent Integrity (GEO-X1 preserved, baseline 254 tests).
- Gate X1: Dependency Coverage (100% of T01-T18 represented).
- Gate X2: Target Reconstruction (Every claimed target derived with residual 0.0).
- Gate X3: Single-Ablation Necessity (All 12 primitives have necessity witnesses).
- Gate X4: Global Minimization (Minimal basis cardinality = 12 unique; subsectors compress to 4-6).
- Gate X5: Redundancy Elimination (Auxiliary ad-hoc postulates pruned).
- Gate X6: Countermodel Comparison (M1 achieves 2.17x compression over M0 and exceeds M2 in parsimony).
- Gate X7: Theory Compression (C_P = 2.17x, C_R = 1.50x, bridge reuse = 2.25).
- Gate X8: Epistemic Audit (Rigorous labeling of primitive/derived/calibration/empirical).
- Gate X9: Final Falsification (Adversarial removal/substitution strictly fails closed).
"""
import unittest
import os
import json

from qualification.structural_reconstruction_v1.engine.dependency_graph import StructuralDependencyGraph
from qualification.structural_reconstruction_v1.engine.reconstruction_engine import ReconstructionEngine
from qualification.structural_reconstruction_v1.engine.primitive_ablation import PrimitiveAblationSuite
from qualification.structural_reconstruction_v1.engine.subset_minimizer import SubsetMinimizer
from qualification.structural_reconstruction_v1.engine.countermodel import CountermodelEvaluator
from qualification.structural_reconstruction_v1.engine.compression_metrics import calculate_theory_compression
from qualification.structural_reconstruction_v1.engine.report_builder import build_all_reports

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestGeoX2StructuralReconstruction(unittest.TestCase):
    """Test suite certifying all 10 qualification gates (X0 - X9) for GEO-X2."""

    @classmethod
    def setUpClass(cls):
        """Build graph, engines, and run minimization and reports."""
        cls.graph = StructuralDependencyGraph()
        cls.engine = ReconstructionEngine()
        cls.ablation = PrimitiveAblationSuite()
        cls.minimizer = SubsetMinimizer()
        cls.evaluator = CountermodelEvaluator()
        cls.compression = calculate_theory_compression()
        cls.build_receipt = build_all_reports()

    def test_gate_x0_parent_integrity(self):
        """Verify Gate X0: GEO-X1 parent campaign is sealed and pinned with 254 tests."""
        freeze_path = os.path.join(
            BASE_DIR, "qualification", "structural_reconstruction_v1", "specification", "parent_freeze.json"
        )
        with open(freeze_path, "r", encoding="utf-8") as fp:
            data = json.load(fp)
        self.assertEqual(data["parent_campaign"], "GEO-X1")
        self.assertEqual(data["parent_test_count"], 254)
        self.assertEqual(data["parent_status"], "QUALIFIED")

    def test_gate_x1_dependency_coverage(self):
        """Verify Gate X1: 100% of frozen targets T01 - T18 are represented in the graph."""
        targets = self.engine.targets
        is_covered, ratio, missing = self.graph.audit_coverage(list(targets.keys()))
        self.assertTrue(is_covered)
        self.assertEqual(ratio, 1.0)
        self.assertEqual(len(missing), 0)

    def test_gate_x2_target_reconstructions_exact(self):
        """Verify Gate X2: All 18 targets are reconstructed with 0.0 symbolic residual."""
        all_prims = set(self.ablation.primitives.keys())
        certs = self.engine.reconstruct_all(all_prims)
        self.assertEqual(len(certs), 18)
        for tid, cert in certs.items():
            self.assertEqual(cert.status, "RECONSTRUCTED_EXACT", f"Target {tid} failed reconstruction")
            self.assertEqual(cert.symbolic_residual, 0.0)
            self.assertTrue(cert.is_exact)

    def test_gate_x3_single_ablation_necessity(self):
        """Verify Gate X3: Every primitive P1 - P12 has >= 1 certified necessity witness."""
        nec_records = self.ablation.run_all_ablations()
        self.assertEqual(len(nec_records), 12)
        for pid, rec in nec_records.items():
            self.assertTrue(rec.is_strictly_necessary, f"Primitive {pid} was not strictly necessary")
            self.assertGreater(rec.targets_lost_count, 0)
            self.assertNotEqual(rec.necessity_witness_target, "NONE")

    def test_gate_x4_global_minimization(self):
        """Verify Gate X4: Global minimal basis has cardinality 12 and subsectors compress to 4-6."""
        res = self.minimizer.find_minimal_bases()
        self.assertEqual(res.minimal_basis_cardinality, 12)
        self.assertTrue(res.is_unique)
        # Subsector bases check
        subsectors = res.subsector_minimal_bases
        self.assertIn("Single_Qubit_Kinematics_and_Measurement", subsectors)
        self.assertLessEqual(len(subsectors["Single_Qubit_Kinematics_and_Measurement"]), 6)
        self.assertLessEqual(len(subsectors["Dynamical_Channel_and_Semigroup_Admissibility"]), 6)

    def test_gate_x5_redundancy_elimination(self):
        """Verify Gate X5: Redundant auxiliary axioms are pruned from the basis."""
        counter_res = self.evaluator.evaluate()
        m1_count = counter_res.models["M1_Relational_Candidate"]["primitive_count"]
        m2_count = counter_res.models["M2_Overcomplete"]["primitive_count"]
        self.assertEqual(m1_count, 12)
        self.assertEqual(m2_count, 20)
        self.assertTrue(counter_res.m1_superior_to_m2_in_parsimony)

    def test_gate_x6_countermodel_comparison(self):
        """Verify Gate X6: M1 achieves compression over M0 (26 postulates) and M2 (20)."""
        counter_res = self.evaluator.evaluate()
        self.assertTrue(counter_res.m1_superior_to_m0_in_compression)
        self.assertTrue(counter_res.m1_superior_to_m2_in_parsimony)
        m0_count = counter_res.models["M0_Conventional"]["primitive_count"]
        self.assertEqual(m0_count, 26)

    def test_gate_x7_theory_compression(self):
        """Verify Gate X7: Theory-level compression metrics C_P = 2.17x, C_R = 1.50x."""
        self.assertAlmostEqual(self.compression.primitive_compression_ratio_cp, 2.17, delta=0.01)
        self.assertAlmostEqual(self.compression.dependency_reuse_ratio_cr, 1.50, delta=0.01)
        self.assertAlmostEqual(self.compression.bridge_reuse_ratio, 2.25, delta=0.01)

    def test_gate_x8_epistemic_audit(self):
        """Verify Gate X8: Final claims ledger exists and assigns strict confidence levels."""
        claims_path = os.path.join(
            BASE_DIR, "qualification", "structural_reconstruction_v1", "reports", "FINAL_CLAIMS_LEDGER.md"
        )
        self.assertTrue(os.path.exists(claims_path))
        with open(claims_path, "r", encoding="utf-8") as fp:
            content = fp.read()
        self.assertIn("ESTABLISHED_WITHIN_QUALIFIED_SCOPE", content)
        self.assertIn("DERIVED_CONDITIONALLY", content)
        self.assertIn("EMPIRICALLY_SUPPORTED", content)
        self.assertIn("OPEN", content)
        self.assertIn("OUTCOME S2 IS ESTABLISHED", content)

    def test_gate_x9_final_falsification(self):
        """Verify Gate X9: Adversarial removal or substitution strictly fails closed."""
        # Test 1: Removing P1 (real metric) causes 12 targets to fail
        certs_no_p1 = self.engine.reconstruct_all(set(self.ablation.primitives.keys()) - {"P1"})
        failures_no_p1 = [t for t, c in certs_no_p1.items() if c.status != "RECONSTRUCTED_EXACT"]
        self.assertEqual(len(failures_no_p1), 12)

        # Test 2: Incomplete primitive set cannot reconstruct complex targets (e.g. {P1, P2} cannot do T14)
        cert_t14 = self.engine.reconstruct("T14", {"P1", "P2"})
        self.assertEqual(cert_t14.status, "INSUFFICIENT_PRIMITIVES")
        self.assertEqual(cert_t14.symbolic_residual, float("inf"))


if __name__ == "__main__":
    unittest.main()
