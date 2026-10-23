"""Tests for Gate L3: Autonomous Constraint Discovery Engine."""
import unittest
import numpy as np

from ngc_geometry_lab.discovery_engine import (
    AutonomousDiscoveryEngine,
    SyntheticWorld,
    build_synthetic_hidden_grammar_benchmark,
    run_l3_autonomous_discovery_campaign,
    DiscoveredRuleCertificate,
    SLOCCInvariantCertificate,
    PhaseBoundaryCertificate,
    UnlabeledProblemCertificate,
    MultiInvariantClassificationCertificate,
    TwoThresholdBoundaryCertificate,
    AutonomousTheoremDiscoveryCertificate,
    ProofCertificate,
    RelationalResidualResolutionRecord,
    AutonomousProofEngineCertificate,
    TheoremCompositionRecord,
    TheoremCompositionCertificate,
    FourQubitDiscoveryCertificate,
    FourQubitRingExpansionCertificate,
    FourQubitInvariantRingCompletionCertificate,
    NovelRelationCandidateRecord,
    NovelRelationDiscoveryCertificate,
    build_unlabeled_mixed_campaign,
    run_unlabeled_mixed_campaign,
    build_6_class_three_qubit_benchmark,
    build_6_class_four_qubit_benchmark,
    build_continuous_four_qubit_collision_benchmark,
    build_ring_completion_benchmarks,
    build_two_threshold_3x3_bipartite_path,
    build_random_tripartite_pure_state_ensemble,
    compute_cayley_hyperdeterminant,
    compute_three_tangle,
    compute_2qubit_concurrence,
    compute_I2_4qubit,
    compute_L4_4qubit,
    compute_flattening_determinants_4qubit,
    compute_D6_4qubit,
    compute_4qubit_bipartition_ranks,
)


class TestAutonomousDiscoveryL3(unittest.TestCase):
    """Test suite verifying Gate L3 autonomous constraint discovery across 6 hidden-grammar worlds."""

    def setUp(self):
        self.worlds = {w.world_id: w for w in build_synthetic_hidden_grammar_benchmark()}
        self.engine = AutonomousDiscoveryEngine

    def test_world_a_quadratic_metric_discovery(self):
        """Verify L3 discovers degree-2 Euclidean quadratic norm without category cues."""
        w = self.worlds['World_A_Quadratic_Metric']
        cert = self.engine.discover_world_rule(w)
        self.assertIsInstance(cert, DiscoveredRuleCertificate)
        self.assertEqual(cert.discovered_family, "Degree-2 Invariant")
        self.assertEqual(cert.training_accuracy, 1.0)
        self.assertEqual(cert.held_out_accuracy, 1.0)
        self.assertFalse(cert.extension_required)

    def test_world_b_cubic_boundary_discovery(self):
        """Verify L3 escalates to Degree-3 when quadratic invariants fail to separate."""
        w = self.worlds['World_B_Cubic_Boundary']
        cert = self.engine.discover_world_rule(w)
        self.assertEqual(cert.discovered_family, "Degree-3 Boundary")
        self.assertEqual(cert.held_out_accuracy, 1.0)
        self.assertIn("det(rho(r))", cert.discovered_invariant)

    def test_world_c_composite_extension_discovery(self):
        """Verify L3 discovers the necessity of composite extension O |-> O (x) I when local norms pass."""
        w = self.worlds['World_C_Composite_Tensor_Extension']
        cert = self.engine.discover_world_rule(w)
        self.assertEqual(cert.discovered_family, "Composite Extension Positivity")
        self.assertTrue(cert.extension_required)
        self.assertEqual(cert.held_out_accuracy, 1.0)

    def test_world_d_hypergraph_parity_discovery(self):
        """Verify L3 discovers discrete F_2 linear consistency and minimal left-nullspace witness."""
        w = self.worlds['World_D_Discrete_Hypergraph_Parity']
        cert = self.engine.discover_world_rule(w)
        self.assertEqual(cert.discovered_family, "Discrete Cohomological Parity")
        self.assertEqual(cert.held_out_accuracy, 1.0)

    def test_world_e_invariant_subspace_discovery(self):
        """Verify L3 discovers generator commutator symmetry [Sz, O] = 0."""
        w = self.worlds['World_E_Invariant_Subspace_Holonomy']
        cert = self.engine.discover_world_rule(w)
        self.assertEqual(cert.discovered_family, "Invariant Subspace Holonomy")
        self.assertEqual(cert.held_out_accuracy, 1.0)

    def test_world_f_rate_triangle_discovery(self):
        """Verify L3 discovers rate triangle inequality on continuous open generators."""
        w = self.worlds['World_F_Rate_Triangle_Semigroup']
        cert = self.engine.discover_world_rule(w)
        self.assertEqual(cert.discovered_family, "Rate Triangle Semigroup")
        self.assertEqual(cert.held_out_accuracy, 1.0)

    def test_preregistered_l3_pass_criteria(self):
        """Verify all preregistered L3-PASS criteria are satisfied."""
        res = run_l3_autonomous_discovery_campaign()
        # 1. 100% held-out prediction accuracy across all worlds
        self.assertTrue(res['all_l3_passed'])
        # 2. All 6 synthetic worlds evaluated
        self.assertEqual(res['num_worlds_evaluated'], 6)
        # 3. At least 3 distinct rule families discovered (achieves 5 distinct families!)
        self.assertGreaterEqual(res['num_distinct_rule_families'], 3)
        # 4. At least one composite relational extension autonomously discovered
        self.assertTrue(res['extension_discovered'])

        certs = res['certificates']
        for c in certs:
            self.assertEqual(c['held_out_accuracy'], 1.0)
            self.assertIsNotNone(c['minimal_witness_name'])
            self.assertIsNotNone(c['discovered_formula'])

    def test_l3_x1_blind_slocc_orbit_invariant_discovery(self):
        """Gate L3-X1: Verify autonomous discovery of degree-4 invariant across 3-qubit SLOCC orbits."""
        campaign = build_unlabeled_mixed_campaign()
        slocc_data = campaign['Problem_1_SLOCC_Orbits']

        cert = self.engine.discover_slocc_orbit_invariant(
            train_orbits=slocc_data['orbits'],
            test_samples=slocc_data['test_samples'],
            problem_id="Gate_L3_X1_SLOCC_Invariant"
        )

        self.assertIsInstance(cert, SLOCCInvariantCertificate)
        # Verify lower-degree candidates failed
        self.assertEqual(cert.degrees_tested_and_failed, [1, 2, 3])
        # Verify degree 4 discovered
        self.assertEqual(cert.discovered_degree, 4)
        # Verify 100% training and held-out accuracy
        self.assertEqual(cert.training_accuracy, 1.0)
        self.assertEqual(cert.held_out_accuracy, 1.0)
        # Verify invariance checks
        for inv_name, status in cert.invariance_verifications.items():
            self.assertTrue(status, f"Invariance check failed: {inv_name}")

        # Direct invariant checks on adversaries
        ghz = np.zeros((2, 2, 2), dtype=complex)
        ghz[0, 0, 0] = 1.0 / np.sqrt(2.0)
        ghz[1, 1, 1] = 1.0 / np.sqrt(2.0)
        w = np.zeros((2, 2, 2), dtype=complex)
        w[0, 0, 1] = 1.0 / np.sqrt(3.0)
        w[0, 1, 0] = 1.0 / np.sqrt(3.0)
        w[1, 0, 0] = 1.0 / np.sqrt(3.0)

        # GHZ has non-zero Cayley hyperdeterminant (tau_3 = 1.0)
        self.assertAlmostEqual(compute_three_tangle(ghz), 1.0, places=10)
        # W state has zero Cayley hyperdeterminant (tau_3 = 0.0)
        self.assertAlmostEqual(compute_three_tangle(w), 0.0, places=10)

        # Biseparable states have zero hyperdeterminant
        zero = np.array([1, 0], dtype=complex)
        one = np.array([0, 1], dtype=complex)
        bell = (np.kron(zero, zero) + np.kron(one, one)) / np.sqrt(2.0)
        bisep = np.kron(zero, bell).reshape((2, 2, 2))
        self.assertAlmostEqual(compute_three_tangle(bisep), 0.0, places=10)

    def test_l3_x2_phase_boundary_discovery(self):
        """Gate L3-X2: Verify autonomous discovery of Werner state phase boundary at p = 1/3."""
        campaign = build_unlabeled_mixed_campaign()
        state_path = campaign['Problem_2_Werner_State_Path']

        cert = self.engine.discover_phase_boundary(
            state_path=state_path,
            problem_id="Gate_L3_X2_Werner_Phase_Boundary"
        )

        self.assertIsInstance(cert, PhaseBoundaryCertificate)
        # Verify local probes failed
        self.assertIn("trace_preservation", cert.local_probes_tested_and_failed)
        self.assertIn("local_positivity_min_eig", cert.local_probes_tested_and_failed)
        self.assertIn("purity", cert.local_probes_tested_and_failed)

        # Verify discovered threshold matches 1/3 with near machine precision
        self.assertAlmostEqual(cert.critical_threshold_fraction, 1.0 / 3.0, places=5)
        self.assertLess(cert.zero_crossing_error, 1e-4)

        # Verify regimes
        self.assertIn("PPT and Separable", cert.pre_crossing_regime)
        self.assertIn("NPT and Entangled", cert.post_crossing_regime)
        self.assertEqual(cert.boundary_formula, "lambda_min(rho^{T_B}) = 0")

    def test_l3_audit_choi_complete_positivity_exact_definition(self):
        """Audit test: Verify exact Choi matrix semidefiniteness J(Phi) >= 0 and L3a classification."""
        w = self.worlds['World_C_Composite_Tensor_Extension']
        cert = self.engine.discover_world_rule(w)

        self.assertEqual(cert.discovered_family, "Composite Extension Positivity")
        self.assertTrue(cert.extension_required)
        self.assertIn("Choi Matrix Semidefiniteness J(Phi)", cert.discovered_invariant)
        self.assertIn("lambda_min(J(Phi)) >= 0", cert.discovered_formula)
        self.assertIn("Gate L3a", cert.discovered_invariant)

    def test_l3_x3_combined_unlabeled_mixed_campaign(self):
        """Gate L3-X3: Verify autonomous routing and 100% discovery across mixed unlabeled problems."""
        res = run_unlabeled_mixed_campaign()

        self.assertTrue(res['all_passed'])
        self.assertEqual(res['num_problems_evaluated'], 5)
        self.assertGreaterEqual(res['num_distinct_inferred_types'], 4)

        certs = res['certificates']
        for c in certs:
            self.assertEqual(c['accuracy'], 1.0)
            self.assertIsNotNone(c['relational_operation_activated'])

    def test_l3b_search_ledger_serialization(self):
        """Verify that the L3b quartic discovery outputs an auditable hypothesis search ledger."""
        campaign = build_unlabeled_mixed_campaign()
        slocc_data = campaign['Problem_1_SLOCC_Orbits']

        cert = self.engine.discover_slocc_orbit_invariant(
            train_orbits=slocc_data['orbits'],
            test_samples=slocc_data['test_samples'],
            problem_id="Audit_L3b_Search_Ledger"
        )

        self.assertIsNotNone(cert.search_ledger)
        self.assertEqual(len(cert.search_ledger), 6)

        # Verify hypothesis progression: degrees 1, 2, 3 rejected; degree 4 accepted
        rejections = [rec for rec in cert.search_ledger if rec['verdict'] == "REJECTED"]
        acceptances = [rec for rec in cert.search_ledger if rec['verdict'] == "ACCEPTED"]

        self.assertEqual(len(rejections), 5)
        self.assertEqual(len(acceptances), 1)

        # Check explicit rejection reasons
        for r in rejections:
            self.assertIsNotNone(r['reason_for_rejection'])
            self.assertGreater(len(r['reason_for_rejection']), 10)

        # Check degree 4 accepted
        acc = acceptances[0]
        self.assertEqual(acc['degree'], 4)
        self.assertEqual(acc['class_separation_score'], 1.0)

        # Check post-discovery comparison distinguishing SL invariance from GL relative covariance
        self.assertIn("SL(2, C)", cert.post_discovery_comparison)
        self.assertIn("relative invariant", cert.post_discovery_comparison)
        self.assertIn("Det = 0 vs Det != 0", cert.post_discovery_comparison)

    def test_l3_c_multi_invariant_grammar_discovery(self):
        """Gate L3-C: Multi-invariant structural classification of 6 three-qubit classes."""
        train_classes, test_samples = build_6_class_three_qubit_benchmark()

        cert = self.engine.discover_multi_invariant_grammar(
            train_classes=train_classes,
            test_samples=test_samples,
            problem_id="Gate_L3_C_Multi_Invariant_Grammar"
        )

        self.assertIsInstance(cert, MultiInvariantClassificationCertificate)
        # Verify that scalar invariant left collisions on 5 classes
        self.assertTrue(cert.scalar_invariant_collision_detected)
        self.assertEqual(cert.number_of_unresolved_classes_under_scalar, 5)

        # Verify minimal grammar table contains 6 distinct signatures
        self.assertEqual(len(cert.discovered_grammar_table), 6)
        self.assertEqual(cert.discovered_grammar_table['GHZ'], (2, 2, 2, True))
        self.assertEqual(cert.discovered_grammar_table['W'], (2, 2, 2, False))
        self.assertEqual(cert.discovered_grammar_table['Bisep_A'], (1, 2, 2, False))
        self.assertEqual(cert.discovered_grammar_table['Bisep_B'], (2, 1, 2, False))
        self.assertEqual(cert.discovered_grammar_table['Bisep_C'], (2, 2, 1, False))
        self.assertEqual(cert.discovered_grammar_table['Fully_Separable'], (1, 1, 1, False))

        # Verify 100% training and held-out test accuracy under random GL(2, C) and permutations
        self.assertEqual(cert.training_accuracy, 1.0)
        self.assertEqual(cert.held_out_accuracy, 1.0)

    def test_l3_b2_two_threshold_boundary_discovery(self):
        """Gate L3-B2: Discover two distinct boundaries along a 3x3 bipartite path."""
        state_path = build_two_threshold_3x3_bipartite_path(num_points=21)

        cert = self.engine.discover_two_threshold_bipartite_boundary(
            state_path=state_path,
            problem_id="Gate_L3_B2_Two_Threshold_Boundary"
        )

        self.assertIsInstance(cert, TwoThresholdBoundaryCertificate)
        self.assertTrue(cert.local_probes_insufficient)
        self.assertTrue(cert.lower_order_insufficiency_detected)
        self.assertEqual(cert.distinct_boundaries_found, 2)

        # Verify Boundary 1: Separable -> PPT Entangled (~ 0.35)
        self.assertAlmostEqual(cert.discovered_boundary_1_threshold, 0.35, delta=0.06)
        self.assertIn("Range Criterion Deficiency", cert.discovered_boundary_1_witness)

        # Verify Boundary 2: PPT Entangled -> NPT Entangled (~ 0.70)
        self.assertAlmostEqual(cert.discovered_boundary_2_threshold, 0.70, delta=0.06)
        self.assertIn("Partial Transpose Zero Crossing", cert.discovered_boundary_2_witness)

        # Verify 3 distinct regimes identified
        self.assertEqual(len(cert.regimes_identified), 3)
        self.assertIn("Separable", cert.regimes_identified[0])
        self.assertIn("PPT Entangled", cert.regimes_identified[1])
        self.assertIn("NPT Entangled", cert.regimes_identified[2])

    def test_l3_t_autonomous_theorem_discovery(self):
        """Gate L3-T: Autonomous discovery of theorems relating discovered invariants."""
        states = build_random_tripartite_pure_state_ensemble(num_samples=150)

        cert = self.engine.discover_invariant_theorems(
            states=states,
            problem_id="Gate_L3_T_Autonomous_Theorems"
        )

        self.assertIsInstance(cert, AutonomousTheoremDiscoveryCertificate)
        self.assertTrue(cert.all_theorems_sound)
        self.assertEqual(cert.num_theorems_discovered, 6)

        # Verify all 3 theorem types were discovered
        self.assertIn("Logical Implication", cert.theorem_types_discovered)
        self.assertIn("Algebraic Conservation Identity", cert.theorem_types_discovered)
        self.assertIn("Persistent Inequality", cert.theorem_types_discovered)

        # Check Theorem 1: Tripartite rank maximality
        t1 = [t for t in cert.theorems if t.theorem_id == "Theorem_T1_Tripartite_Rank_Necessity"][0]
        self.assertEqual(t1.empirical_confidence, 1.0)
        self.assertEqual(t1.maximum_residual_or_violation, 0.0)

        # Check Theorem 2: Biseparable Schmidt equality
        t2 = [t for t in cert.theorems if t.theorem_id == "Theorem_T2_Biseparable_Schmidt_Equality"][0]
        self.assertEqual(t2.empirical_confidence, 1.0)

        # Check Theorem 3: Product cut annihilates tri-tangle
        t3 = [t for t in cert.theorems if t.theorem_id == "Theorem_T3_Product_Cut_TriTangle_Annihilation"][0]
        self.assertEqual(t3.empirical_confidence, 1.0)

        # Check Theorem 4: Schmidt purity conservation
        t4 = [t for t in cert.theorems if t.theorem_id == "Theorem_T4_Schmidt_Purity_Conservation"][0]
        self.assertEqual(t4.empirical_confidence, 1.0)
        self.assertLess(t4.maximum_residual_or_violation, 1e-12)

        # Check Theorem 5: Linear entropy determinant duality
        t5 = [t for t in cert.theorems if t.theorem_id == "Theorem_T5_Linear_Entropy_Determinant_Duality"][0]
        self.assertEqual(t5.empirical_confidence, 1.0)
        self.assertLess(t5.maximum_residual_or_violation, 1e-12)

        # Check Theorem 6: CKW entanglement monogamy bound
        t6 = [t for t in cert.theorems if t.theorem_id == "Theorem_T6_Entanglement_Monogamy_Bound"][0]
        self.assertEqual(t6.empirical_confidence, 1.0)
        self.assertLessEqual(t6.maximum_residual_or_violation, 1e-12)


class TestAutonomousProofAndResidualL3P(unittest.TestCase):
    """Gate L3-P: Autonomous Proof, Counterexample, and Residual-Explanation Qualification."""

    def setUp(self):
        self.engine = AutonomousDiscoveryEngine
        self.states = build_random_tripartite_pure_state_ensemble(num_samples=60)

    def test_l3_p_control_proof_t4_schmidt_purity(self):
        """Verify symbolic derivation of T4 (Schmidt purity conservation) with status PROVED."""
        cert = self.engine.prove_or_refute_conjecture("T4_Schmidt_Purity_Conservation", states=self.states)
        self.assertIsInstance(cert, ProofCertificate)
        self.assertEqual(cert.status, "PROVED")
        self.assertEqual(cert.conjecture_id, "T4_Schmidt_Purity_Conservation")
        self.assertIn("Schmidt decomposition", "".join(cert.derivation_steps))
        self.assertIn("0", cert.symbolic_residual)
        self.assertIsNone(cert.counterexample)

    def test_l3_p_control_proof_t5_linear_entropy_characteristic_identity(self):
        """Verify symbolic derivation of T5 (2x2 Cayley-Hamilton identity) with status PROVED."""
        cert = self.engine.prove_or_refute_conjecture("T5_Linear_Entropy_Characteristic_Identity", states=self.states)
        self.assertIsInstance(cert, ProofCertificate)
        self.assertEqual(cert.status, "PROVED")
        self.assertEqual(cert.conjecture_id, "T5_Linear_Entropy_Characteristic_Identity")
        self.assertIn("Cayley-Hamilton", "".join(cert.derivation_steps))
        self.assertIn("0", cert.symbolic_residual)
        self.assertIsNone(cert.counterexample)

    def test_l3_p_disproved_f1_vanishing_tangle_not_biseparable(self):
        """Verify false conjecture F1 (Delta=0 => biseparable) is DISPROVED with W-state counterexample."""
        cert = self.engine.prove_or_refute_conjecture("F1_Vanishing_Tangle_Implies_Biseparability", states=self.states)
        self.assertIsInstance(cert, ProofCertificate)
        self.assertEqual(cert.status, "DISPROVED")
        self.assertIsNotNone(cert.counterexample)
        self.assertIn("W state", cert.counterexample['state_family'])
        self.assertAlmostEqual(cert.counterexample['tangle_delta'], 0.0)
        self.assertEqual(cert.counterexample['flattening_ranks'], (2, 2, 2))
        self.assertFalse(cert.counterexample['is_biseparable'])

    def test_l3_p_disproved_f2_maximal_ranks_do_not_imply_nonzero_tangle(self):
        """Verify false conjecture F2 ((2,2,2) => Delta!=0) is DISPROVED with W-state counterexample."""
        cert = self.engine.prove_or_refute_conjecture("F2_Maximal_Flattening_Ranks_Imply_Nonzero_Tangle", states=self.states)
        self.assertIsInstance(cert, ProofCertificate)
        self.assertEqual(cert.status, "DISPROVED")
        self.assertIsNotNone(cert.counterexample)
        self.assertIn("W state", cert.counterexample['state_family'])
        self.assertEqual(cert.counterexample['flattening_ranks'], (2, 2, 2))
        self.assertAlmostEqual(cert.counterexample['tangle_delta'], 0.0)

    def test_l3_p_conditional_c1_subsystem_determinant_tangle(self):
        """Verify conditional conjecture C1 is flagged as CONDITIONAL."""
        cert = self.engine.prove_or_refute_conjecture("C1_Subsystem_Determinant_TriTangle_Equivalence", states=self.states)
        self.assertIsInstance(cert, ProofCertificate)
        self.assertEqual(cert.status, "CONDITIONAL")
        self.assertIn("pairwise concurrence", cert.counterexample['conditional_submanifold'])

    def test_l3_p_relational_residual_resolution_ckw(self):
        """MAPEOGEO first-class operation RELATIONAL_RESIDUAL_RESOLUTION:
        Discovers missing bipartite relational variables C_AB^2, C_AC^2 that upgrade
        the inequality R_A = 4*det(rho_A) - 4*|Delta| >= 0 into an exact conservation law.
        """
        record = self.engine.resolve_relational_residual("R_A", states=self.states)
        self.assertIsInstance(record, RelationalResidualResolutionRecord)
        self.assertEqual(record.reconstruction_coefficients['C_AB^2'], 1.0)
        self.assertEqual(record.reconstruction_coefficients['C_AC^2'], 1.0)
        self.assertEqual(record.reconstruction_coefficients['C_BC^2'], 0.0)
        self.assertEqual(record.reconstruction_coefficients['constant_offset'], 0.0)
        self.assertLess(record.maximum_residual, 1e-7)
        self.assertIn("4 * det(rho_A) = C_{AB}^2 + C_{AC}^2 + 4 * |Delta(psi)|", record.upgraded_conservation_law)

    def test_l3_p_full_campaign_execution(self):
        """Gate L3-P: Full campaign verification over proved, disproved, conditional, and resolved rules."""
        cert = self.engine.run_l3p_proof_and_residual_campaign(states=self.states)
        self.assertIsInstance(cert, AutonomousProofEngineCertificate)
        self.assertEqual(cert.num_conjectures_evaluated, 6)
        self.assertEqual(cert.num_proved, 2)  # T4, T5 analytically proved
        self.assertEqual(cert.num_disproved, 2)  # F1, F2 disproved with explicit counterexamples
        self.assertEqual(cert.num_conditional, 1)  # C1 conditional on vanishing pairwise concurrence
        self.assertEqual(cert.num_empirically_exact, 1)  # T6 upgraded CKW law
        self.assertEqual(cert.num_unresolved, 0)
        self.assertTrue(cert.all_conjectures_resolved)
        self.assertEqual(len(cert.residual_resolutions), 1)
        self.assertLess(cert.residual_resolutions[0].maximum_residual, 1e-7)

        # Verify epistemological distinction: upgraded CKW has empirical exact status
        t6_cert = [c for c in cert.proof_certificates if c.conjecture_id == "T6_Upgraded_Relational_Conservation_Law"][0]
        self.assertEqual(t6_cert.status, "DISCOVERED + EMPIRICALLY EXACT TO TOLERANCE + KNOWN THEOREM MATCH")


class TestTheoremCompositionL3P2(unittest.TestCase):
    """Gate L3-P2: Symbolic Closure and Theorem Composition via THEOREM_COMPOSE."""

    def setUp(self):
        self.engine = AutonomousDiscoveryEngine
        self.states = build_random_tripartite_pure_state_ensemble(num_samples=60)

    def test_l3_p2_cyclic_triad_symbolic_closure(self):
        """Verify that cyclic CKW triad closes with exact symbolic derivations."""
        cert = self.engine.run_l3p2_symbolic_closure_and_composition_campaign(states=self.states)
        self.assertIsInstance(cert, TheoremCompositionCertificate)
        self.assertTrue(cert.cyclic_triad_closure_verified)
        self.assertTrue(cert.all_derivations_exact)
        self.assertEqual(cert.num_secondary_theorems_derived, 5)

    def test_l3_p2_secondary_theorems_derivation_and_residual(self):
        """Verify THEOREM_COMPOSE elimination of variables:
        - S1: 4*(det(rho_A) - det(rho_B)) = C_AC^2 - C_BC^2 (tau_3 eliminated)
        - S2: 4*(det(rho_A) - det(rho_C)) = C_AB^2 - C_BC^2 (tau_3 eliminated)
        - S3: 4*(det(rho_B) - det(rho_C)) = C_AB^2 - C_AC^2 (tau_3 eliminated)
        - S4: Cyclic sum rule (each pairwise term appears twice, tau_3 appears three times)
        - S5: Pairwise extraction rule (isolating 2*C_AB^2 + tau_3)
        """
        cert = self.engine.run_l3p2_symbolic_closure_and_composition_campaign(states=self.states)
        for t in cert.composed_theorems:
            self.assertEqual(t.verdict, "PROVED_BY_COMPOSITION")
            self.assertIn("Symbolically exact", t.symbolic_residual)
            self.assertLess(t.empirical_residual, 1e-7)

        # Check S1
        s1 = [t for t in cert.composed_theorems if t.composition_id == "Secondary_Theorem_S1_Asymmetry_AB"][0]
        self.assertEqual(s1.operation, "ELIMINATE_VARIABLE")
        self.assertIn("tau_3", s1.eliminated_variable)
        self.assertIn("4 * (det(rho_A) - det(rho_B)) = C_{AC}^2 - C_{BC}^2", s1.derived_formula)

        # Check S4
        s4 = [t for t in cert.composed_theorems if t.composition_id == "Secondary_Theorem_S4_Cyclic_Sum_Rule"][0]
        self.assertEqual(s4.operation, "CYCLIC_SUM")
        self.assertIn("3 * tau_3", s4.derived_formula)


class TestFourQubitDiscoveryL4O(unittest.TestCase):
    """Gate L4-O: Four-Qubit Invariant Discovery and Orbit Grammar under SL(2, C)^4."""

    def setUp(self):
        self.engine = AutonomousDiscoveryEngine
        self.train_classes, self.test_samples = build_6_class_four_qubit_benchmark()

    def test_l4_o_degree2_invariant_and_sl2c_invariance(self):
        """Verify that degree-2 polynomial I_2 is strictly SL(2,C)^4 invariant."""
        ghz4 = np.zeros((2, 2, 2, 2), dtype=complex)
        ghz4[0, 0, 0, 0] = 1.0 / np.sqrt(2.0)
        ghz4[1, 1, 1, 1] = 1.0 / np.sqrt(2.0)

        val_base = compute_I2_4qubit(ghz4)
        self.assertAlmostEqual(val_base, 1.0, places=10)

        def rand_sl2():
            m = np.random.randn(2, 2) + 1j * np.random.randn(2, 2)
            return m / np.sqrt(np.linalg.det(m))

        np.random.seed(42)
        for _ in range(5):
            A, B, C, D = rand_sl2(), rand_sl2(), rand_sl2(), rand_sl2()
            psi_scrambled = np.einsum('ia,jb,kc,ld,abcd->ijkl', A, B, C, D, ghz4)
            val_scrambled = compute_I2_4qubit(psi_scrambled)
            self.assertAlmostEqual(val_scrambled, 1.0, places=10)

    def test_l4_o_degree2_collision_identification(self):
        """Verify that I_2 alone creates collisions that force multi-invariant grammar:
        - I_2 = 1.0 on both GHZ_4 and EPRxEPR
        - I_2 = 0.0 on W_4, Cluster_4, Bisep_1vs3, Separable_4.
        """
        ghz4 = self.train_classes['GHZ_4'][0]
        epr2 = self.train_classes['EPRxEPR'][0]
        w4 = self.train_classes['W_4'][0]
        cl4 = self.train_classes['Cluster_4'][0]

        # Both have I_2 = 1.0
        self.assertAlmostEqual(compute_I2_4qubit(ghz4), 1.0, places=7)
        self.assertAlmostEqual(compute_I2_4qubit(epr2), 1.0, places=7)

        # Both have I_2 = 0.0
        self.assertAlmostEqual(compute_I2_4qubit(w4), 0.0, places=7)
        self.assertAlmostEqual(compute_I2_4qubit(cl4), 0.0, places=7)

    def test_l4_o_bipartition_flattening_dets_and_ranks(self):
        """Verify that 2vs2 determinants and ranks separate collisions:
        - EPRxEPR has 2vs2 ranks (1, 4, 4) and det_22 > 0, separating from GHZ_4 ranks (2, 2, 2).
        - Cluster_4 has 2vs2 ranks (2, 4, 4) and det_22 > 0, separating from W_4 ranks (2, 2, 2).
        """
        r13_ghz, r22_ghz, d22_ghz = compute_4qubit_bipartition_ranks(self.train_classes['GHZ_4'][0])
        r13_epr, r22_epr, d22_epr = compute_4qubit_bipartition_ranks(self.train_classes['EPRxEPR'][0])
        r13_w, r22_w, d22_w = compute_4qubit_bipartition_ranks(self.train_classes['W_4'][0])
        r13_cl, r22_cl, d22_cl = compute_4qubit_bipartition_ranks(self.train_classes['Cluster_4'][0])

        self.assertEqual(r22_ghz, (2, 2, 2))
        self.assertEqual(r22_epr, (1, 4, 4))
        self.assertGreater(max(d22_epr), 1e-4)

        self.assertEqual(r22_w, (2, 2, 2))
        self.assertIn(4, r22_cl)
        self.assertGreater(max(d22_cl), 1e-4)

    def test_l4_o_full_classification_campaign(self):
        """Gate L4-O: Autonomous discovery of 4-qubit grammar with 100% held-out accuracy."""
        cert = self.engine.run_l4o_four_qubit_discovery_campaign()
        self.assertIsInstance(cert, FourQubitDiscoveryCertificate)
        self.assertTrue(cert.collision_identified_on_degree2)
        self.assertEqual(cert.training_accuracy, 1.0)
        self.assertEqual(cert.held_out_accuracy, 1.0)
        self.assertEqual(len(cert.classes_resolved), 6)
        self.assertIn("Cluster_4", cert.classes_resolved)
        self.assertIn("EPRxEPR", cert.classes_resolved)


class TestFourQubitRingExpansionL4G(unittest.TestCase):
    """Gate L4-G: Four-Qubit Invariant-Ring Expansion over Continuous Families."""

    def setUp(self):
        self.engine = AutonomousDiscoveryEngine
        self.benchmark = build_continuous_four_qubit_collision_benchmark()

    def test_l4_g_continuous_collision_identification(self):
        """Verify that frozen feature grammar F_0 = (I_2, r_13, r_22, D_22) collides on continuous Verstraete families."""
        cert = self.engine.run_l4g_ring_expansion_campaign()
        self.assertIsInstance(cert, FourQubitRingExpansionCertificate)
        self.assertTrue(cert.collisions_detected)
        self.assertGreaterEqual(len(cert.colliding_orbit_families), 2)
        self.assertIn("Verstraete_G_theta1", cert.colliding_orbit_families)
        self.assertIn("Verstraete_G_theta2", cert.colliding_orbit_families)

    def test_l4_g_search_ledger_serialization_and_candidates(self):
        """Verify auditable search ledger records failed lower-degree hypotheses and independent degree-4 acceptance."""
        cert = self.engine.run_l4g_ring_expansion_campaign()
        ledger = cert.search_ledger
        self.assertGreaterEqual(len(ledger), 3)

        # Check degree 1 rejection
        d1 = [c for c in ledger if c['degree'] == 1][0]
        self.assertEqual(d1['verdict'], "REJECTED")
        self.assertIn("variance", d1['reason_for_rejection'])

        # Check degree 3 rejection
        d3 = [c for c in ledger if c['degree'] == 3][0]
        self.assertEqual(d3['verdict'], "REJECTED")

        # Check degree 4 trivial product rejection
        d4_triv = [c for c in ledger if c['candidate_id'] == "Candidate_Deg4_Trivial_Product_P1111"][0]
        self.assertEqual(d4_triv['verdict'], "REJECTED")
        self.assertIn("dependent", d4_triv['reason_for_rejection'])

        # Check degree 4 independent tri-pairing acceptance
        d4_acc = [c for c in ledger if c['candidate_id'] == "Candidate_Deg4_Tri_Pairing_L4"][0]
        self.assertEqual(d4_acc['verdict'], "ACCEPTED")

    def test_l4_g_l4_sl2c_invariance(self):
        """Verify that newly discovered invariant L_4 is strictly invariant under local SL(2, C)^4."""
        s1 = self.benchmark['family_map']['Verstraete_G_theta1']
        val_base = compute_L4_4qubit(s1)

        def rand_sl2():
            m = np.random.randn(2, 2) + 1j * np.random.randn(2, 2)
            return m / np.sqrt(np.linalg.det(m))

        np.random.seed(42)
        for _ in range(5):
            A, B, C, D = rand_sl2(), rand_sl2(), rand_sl2(), rand_sl2()
            psi_scrambled = np.einsum('ia,jb,kc,ld,abcd->ijkl', A, B, C, D, s1)
            val_scrambled = compute_L4_4qubit(psi_scrambled)
            self.assertAlmostEqual(val_scrambled, val_base, places=10)

    def test_l4_g_collision_resolution_and_expanded_grammar(self):
        """Verify that expanding the grammar with L_4 completely eliminates the continuous collisions."""
        cert = self.engine.run_l4g_ring_expansion_campaign()
        self.assertIn("L_4", cert.expanded_feature_set)
        self.assertEqual(cert.residual_collisions_remaining, 0)
        self.assertTrue(cert.all_collisions_resolved)


class TestFourQubitInvariantRingCompletionL4R(unittest.TestCase):
    """Test suite verifying Gate L4-R: Autonomous Invariant-Ring Completion and Hilbert Structure Discovery."""

    def setUp(self):
        self.engine = AutonomousDiscoveryEngine
        self.benchmark = build_ring_completion_benchmarks()

    def test_flattening_determinants_and_syzygy(self):
        """Verify flattening determinants L, M, N are SL(2, C)^4 invariant and satisfy L + M + N = 0."""
        def rand_sl2():
            m = np.random.randn(2, 2) + 1j * np.random.randn(2, 2)
            return m / np.sqrt(np.linalg.det(m))

        np.random.seed(42)
        for _ in range(5):
            psi = np.random.randn(2, 2, 2, 2) + 1j * np.random.randn(2, 2, 2, 2)
            L, M, N = compute_flattening_determinants_4qubit(psi)
            self.assertAlmostEqual(abs(L + M + N), 0.0, places=12)

            # Invariance under local SL(2, C)^4
            A, B, C, D = rand_sl2(), rand_sl2(), rand_sl2(), rand_sl2()
            psi_sl2 = np.einsum('ia,jb,kc,ld,abcd->ijkl', A, B, C, D, psi)
            L_sl2, M_sl2, N_sl2 = compute_flattening_determinants_4qubit(psi_sl2)
            self.assertAlmostEqual(abs(L - L_sl2), 0.0, places=10)
            self.assertAlmostEqual(abs(M - M_sl2), 0.0, places=10)
            self.assertAlmostEqual(abs(N - N_sl2), 0.0, places=10)

    def test_degree6_invariant_invariance_and_algebraic_independence(self):
        """Verify degree-6 invariant D_6 is SL(2, C)^4 invariant and algebraically independent of lower invariants."""
        def rand_sl2():
            m = np.random.randn(2, 2) + 1j * np.random.randn(2, 2)
            return m / np.sqrt(np.linalg.det(m))

        np.random.seed(99)
        psi = np.random.randn(2, 2, 2, 2) + 1j * np.random.randn(2, 2, 2, 2)
        d6_base = compute_D6_4qubit(psi)

        # SL(2, C)^4 invariance
        for _ in range(3):
            A, B, C, D = rand_sl2(), rand_sl2(), rand_sl2(), rand_sl2()
            psi_sl2 = np.einsum('ia,jb,kc,ld,abcd->ijkl', A, B, C, D, psi)
            d6_sl2 = compute_D6_4qubit(psi_sl2)
            self.assertAlmostEqual(abs(d6_base - d6_sl2), 0.0, places=10)

        # Algebraic independence across basis states
        basis = self.benchmark['dimension_basis_states']
        mat_lower = []
        vec_d6 = []
        for s in basis:
            i2 = compute_I2_4qubit(s)
            l, m, _ = compute_flattening_determinants_4qubit(s)
            d6 = compute_D6_4qubit(s)
            mat_lower.append([i2**3, i2 * l, i2 * m])
            vec_d6.append(d6)

        mat_lower_arr = np.array(mat_lower)
        vec_d6_arr = np.array(vec_d6)
        coeffs, _, _, _ = np.linalg.lstsq(mat_lower_arr, vec_d6_arr, rcond=None)
        fit_error = np.linalg.norm(vec_d6_arr - mat_lower_arr @ coeffs) / np.linalg.norm(vec_d6_arr)
        self.assertGreater(fit_error, 0.5)

    def test_quartic_and_sextic_collision_detection(self):
        """Verify Stage 1 (quartic) and Stage 2 (sextic) continuous-orbit collision benchmarks."""
        q_orbs = self.benchmark['quartic_collision_orbits']
        s1A = q_orbs[0]['samples'][0]
        s1B = q_orbs[1]['samples'][0]

        # Stage 1: I_2 and L_4 collide, but M_4 splits
        i2_A = compute_I2_4qubit(s1A)
        i2_B = compute_I2_4qubit(s1B)
        l_A, m_A, _ = compute_flattening_determinants_4qubit(s1A)
        l_B, m_B, _ = compute_flattening_determinants_4qubit(s1B)
        self.assertAlmostEqual(i2_A, i2_B, places=6)
        self.assertAlmostEqual(abs(l_A), abs(l_B), places=6)
        self.assertNotAlmostEqual(abs(m_A), abs(m_B), places=4)

        # Stage 2: I_2, L_4, M_4 all collide, but D_6 splits
        s_orbs = self.benchmark['sextic_collision_orbits']
        s2A = s_orbs[0]['samples'][0]
        s2B = s_orbs[1]['samples'][0]
        i2_2A = compute_I2_4qubit(s2A)
        i2_2B = compute_I2_4qubit(s2B)
        l_2A, m_2A, _ = compute_flattening_determinants_4qubit(s2A)
        l_2B, m_2B, _ = compute_flattening_determinants_4qubit(s2B)
        d6_2A = compute_D6_4qubit(s2A)
        d6_2B = compute_D6_4qubit(s2B)

        self.assertAlmostEqual(i2_2A, i2_2B, places=6)
        self.assertAlmostEqual(abs(l_2A), abs(l_2B), places=6)
        self.assertAlmostEqual(abs(m_2A), abs(m_2B), places=6)
        self.assertNotAlmostEqual(abs(d6_2A), abs(d6_2B), places=5)

    def test_hilbert_structure_and_free_ring_inference(self):
        """Verify empirical Hilbert dimensions {1, 1, 3, 4, 7} and free generator degrees [2, 4, 4, 6]."""
        cert = self.engine.run_l4r_invariant_ring_completion_campaign(benchmark=self.benchmark)
        expected_dims = {0: 1, 2: 1, 4: 3, 6: 4, 8: 7}
        self.assertEqual(cert.observed_hilbert_dimensions, expected_dims)
        self.assertEqual(cert.inferred_generator_degrees, [2, 4, 4, 6])
        self.assertTrue(cert.is_free_polynomial_algebra)
        self.assertEqual(cert.ring_completion_status, "INFERRED_THROUGH_DEGREE_8_AND_EXTERNALLY_THEOREM_VERIFIED")
        self.assertEqual(cert.hilbert_series_generating_function, "1 / ((1 - t^2) * (1 - t^4)^2 * (1 - t^6))")

    def test_full_l4r_campaign_execution(self):
        """Execute full Gate L4-R campaign and verify end-to-end ring completion."""
        cert = self.engine.run_l4r_invariant_ring_completion_campaign()
        self.assertTrue(cert.quartic_collision_detected)
        self.assertEqual(cert.discovered_second_quartic, "M_4 = -det(X_{AC|BD})")
        self.assertLess(cert.syzygy_residual, 1e-12)
        self.assertEqual(cert.quartic_residual_collisions_remaining, 0)
        self.assertTrue(cert.sextic_collision_detected)
        self.assertEqual(cert.discovered_degree_6_invariant, "D_6 = det(B_{xy})")
        self.assertGreater(cert.degree_6_independence_residual, 0.5)
        self.assertEqual(cert.sextic_residual_collisions_remaining, 0)
        self.assertEqual(cert.ring_completion_status, "INFERRED_THROUGH_DEGREE_8_AND_EXTERNALLY_THEOREM_VERIFIED")
        self.assertTrue(cert.ring_completion_certified)


class TestNovelRelationDiscoveryL5N(unittest.TestCase):
    """Test suite verifying Gate L5-N: Novel Relation Discovery under a Frozen Grammar."""

    def setUp(self):
        self.engine = AutonomousDiscoveryEngine

    def test_l5n_conjecture_evaluations_and_verdicts(self):
        """Verify that all 6 candidate conjectures receive sound, verifiable verdicts."""
        cert = self.engine.run_l5n_novel_relation_discovery_campaign()
        self.assertEqual(cert.num_conjectures_tested, 6)
        self.assertEqual(cert.num_proved, 5)
        self.assertEqual(cert.num_refuted, 1)
        self.assertTrue(cert.all_verdicts_sound)

    def test_n4_explicit_counterexample_properties(self):
        """Verify that the counterexample refuting N4 has D_6 = 0 while retaining full rank r_22 = (4, 4, 4)."""
        cert = self.engine.run_l5n_novel_relation_discovery_campaign()
        rec_n4 = [r for r in cert.conjecture_records if r['conjecture_id'] == "Conjecture_N4_Discriminant_Vanishing_Forces_Rank_Loss"][0]
        self.assertEqual(rec_n4['verdict'], "REFUTED_WITH_COUNTEREXAMPLE")
        witness = rec_n4['counterexample_witness']
        self.assertIsNotNone(witness)
        self.assertLess(witness['D_6'], 1e-15)
        self.assertEqual(witness['r_22'], (4, 4, 4))

    def test_n2_syzygy_rank_closure(self):
        """Verify Conjecture N2: L_4 = 0 and M_4 = 0 forces complete rank deficiency across all 3 cuts."""
        cert = self.engine.run_l5n_novel_relation_discovery_campaign()
        rec_n2 = [r for r in cert.conjecture_records if r['conjecture_id'] == "Conjecture_N2_Double_Rank_Loss_Forces_Triple"][0]
        self.assertEqual(rec_n2['verdict'], "PROVED")
        self.assertLess(rec_n2['symbolic_residual'], 1e-11)

    def test_n3_disc_inequality_bound(self):
        """Verify Conjecture N3: normalized continuous orbit disc inequality |L_4| <= 0.0625."""
        cert = self.engine.run_l5n_novel_relation_discovery_campaign()
        rec_n3 = [r for r in cert.conjecture_records if r['conjecture_id'] == "Conjecture_N3_Normalized_Orbit_Disc_Bound"][0]
        self.assertEqual(rec_n3['verdict'], "PROVED")
        self.assertLessEqual(rec_n3['symbolic_residual'], 1e-10)

    def test_n5_and_n6_proved_identities(self):
        """Verify Conjectures N5 (symmetric quotient slice) and N6 (Heron triangle factorization) are proved."""
        cert = self.engine.run_l5n_novel_relation_discovery_campaign()
        rec_n5 = [r for r in cert.conjecture_records if r['conjecture_id'] == "Conjecture_N5_Symmetric_Quotient_Subspace_Collapse"][0]
        rec_n6 = [r for r in cert.conjecture_records if r['conjecture_id'] == "Conjecture_N6_Heron_Triangle_Factorization"][0]
        self.assertEqual(rec_n5['verdict'], "PROVED")
        self.assertEqual(rec_n6['verdict'], "PROVED")
        self.assertLess(rec_n5['symbolic_residual'], 1e-11)
        self.assertLess(rec_n6['symbolic_residual'], 1e-11)


if __name__ == '__main__':
    unittest.main()
