# Independent complex reference implementation report

## Result

Implemented every interface in `docs/tasks/reference_brief.md` in `ngc_geometry_lab/reference.py`. The module imports only NumPy and the standard-library `numbers.Integral`; it does not import geometric reconstruction, detector calibration, NGC, MAPEOGEO, or source adapters. Expected values in the 22 reference tests come from explicit complex matrices, elementary analytic expressions, Kronecker products, and hand-derived computational-basis mappings.

## Design and validation

- Density validation accepts arbitrary nonempty square dimensions, checks all entries are finite, Hermiticity, unit trace, and positive semidefiniteness, and returns a complex copy. Caller-controlled `atol` must be a finite nonnegative real scalar. Every approximate comparison explicitly uses `rtol=0`.
- Single-qubit construction uses the Pauli expansion; extraction uses Pauli traces. Tetrahedral probabilities use direct Born traces against the four effects in the required order.
- Rotations use complex SU(2) matrices with normalized finite nonzero real axes. Axis normalization first scales by the maximum component to avoid overflow/underflow for extreme finite axis magnitudes.
- Evolution validates both the density matrix and the dimension-matched unitary, then validates the resulting density matrix.
- Random density matrices use caller-supplied NumPy RNGs and normalized complex Wishart matrices, with one Gaussian column for pure states and square Gaussian matrices otherwise.
- Local gate application uses reshape, target-axis permutation, matrix multiplication, and inverse axis permutation. Qubit zero is the first tensor factor. Reversed and nonadjacent target lists preserve their supplied local basis order. Inputs require a normalized finite state, a matching unitary, positive integer qubit count, and nonempty unique integer targets in range. Boolean indices and qubit counts are rejected.
- Joint probabilities use traces of tensor-product effects. Joint parameters use tensor-product Pauli traces. Joint reconstruction uses the full Pauli expansion followed by density validation; it rejects the nonphysical `a=b=0, C=I` example despite that example's positive formal tetrahedral probabilities.

## Test coverage

Analytic cases cover `|0>`, `|1>`, `|+>`, `|+i>`, maximally mixed states, product `|01>`, and the singlet. Tests check Pauli order, effect positivity/completeness, probability ordering, density trace, `RX(pi)` inversion, `RZ(pi/2)` phase, direct dense Kronecker agreement for a seeded arbitrary unitary, explicit nonadjacent and reversed CNOT mappings, mixed/pure random densities, and singlet CHSH expectation `-2 sqrt(2)` for explicitly declared settings. Invalid shapes, normalization, target indices, nonfinite values, complex real-only parameters, nonunitary gates, and non-PSD inputs are rejected.

## Commands and preserved results

All commands ran from `/workspace/scratch/f4c8fe3fa7f4/ngc_geometry_lab`.

1. Tests were written before `reference.py` existed. Command:

   ```bash
   python -m unittest tests.test_reference -v > evidence/development/reference_red.txt 2>&1
   ```

   Exit **1**. **22 tests, 22 expected assertion failures** stating that the independent reference module was missing. The test setup converts the missing-feature import into a clear assertion failure. Complete red evidence is preserved.

2. After implementing the independent module:

   ```bash
   python -m unittest tests.test_reference -v > evidence/development/reference_green.txt 2>&1
   ```

   Exit **0**. **22 tests passed**, no failures/errors. Complete green evidence is preserved.

3. Whole repository snapshot verification:

   ```bash
   python -m unittest discover -s tests -v > evidence/development/reference_suite.txt 2>&1
   ```

   Exit **1**. **64 tests ran**, with **96 errors** including subtest errors. The reference tests passed. Errors were in concurrent workers' geometry and observations implementations, which were `NotImplementedError` stubs at the time of this snapshot. Those files were not changed by this task. Full details, including all subtest cases and tracebacks, are preserved in the suite log. Unique affected test methods were:

- `test_geometry.OperationTests.test_active_rodrigues.test_active_rodrigues`
- `test_observations.ObservationTests.test_blind_dataset_workflow.test_blind_dataset_workflow`
- `test_observations.ObservationTests.test_calibration_recovers_known_detector_from_counts.test_calibration_recovers_known_detector_from_counts`
- `test_geometry.JointTests.test_chsh_singlet.test_chsh_singlet`
- `test_observations.ObservationTests.test_counts_validation.test_counts_validation`
- `test_geometry.OperationTests.test_crossed_and_inserted_polarizers.test_crossed_and_inserted_polarizers`
- `test_observations.ObservationTests.test_detector_validation_rejects_invalid_matrices.test_detector_validation_rejects_invalid_matrices`
- `test_geometry.ObservabilityTests.test_duplicate_directions_and_sequence_rank.test_duplicate_directions_and_sequence_rank`
- `test_geometry.MetricTests.test_empty_family_and_other_dimension.test_empty_family_and_other_dimension`
- `test_geometry.OperationTests.test_exponents_and_no_projection.test_exponents_and_no_projection`
- `test_geometry.MetricTests.test_failed_high_nullity_witness_is_unresolved.test_failed_high_nullity_witness_is_unresolved`
- `test_geometry.JointTests.test_generic_probability_coordinates_do_not_claim_quantum_physicality.test_generic_probability_coordinates_do_not_claim_quantum_physicality`
- `test_geometry.CenterAndGeometryTests.test_gram_edges_and_volume.test_gram_edges_and_volume`
- `test_geometry.CenterAndGeometryTests.test_inconsistent_centers.test_inconsistent_centers`
- `test_geometry.MetricTests.test_inconsistent_dilation_has_no_metric.test_inconsistent_dilation_has_no_metric`
- `test_geometry.MetricTests.test_insufficient_family_returns_spd_witness_with_ambiguity.test_insufficient_family_returns_spd_witness_with_ambiguity`
- `test_geometry.CenterAndGeometryTests.test_invalid_centers.test_invalid_centers`
- `test_geometry.ObservabilityTests.test_invalid_observability.test_invalid_observability`
- `test_geometry.OperationTests.test_invalid_operations.test_invalid_operations`
- `test_geometry.TetraTests.test_invalid_probabilities_are_not_normalized.test_invalid_probabilities_are_not_normalized`
- `test_geometry.TetraTests.test_invalid_state.test_invalid_state`
- `test_geometry.CenterAndGeometryTests.test_invalid_tetrahedron.test_invalid_tetrahedron`
- `test_observations.ObservationTests.test_inversion_uses_counts_and_frozen_detector.test_inversion_uses_counts_and_frozen_detector`
- `test_geometry.JointTests.test_joint_invalid_inputs.test_joint_invalid_inputs`
- `test_geometry.MetricTests.test_metric_invalid_inputs.test_metric_invalid_inputs`
- `test_geometry.TetraTests.test_mixed_state_and_vertex_probabilities.test_mixed_state_and_vertex_probabilities`
- `test_geometry.MetricTests.test_non_euclidean_metric_recovered_from_conjugated_cubic_family.test_non_euclidean_metric_recovered_from_conjugated_cubic_family`
- `test_geometry.CenterAndGeometryTests.test_nonunique_center_is_least_norm_representative.test_nonunique_center_is_least_norm_representative`
- `test_geometry.TetraTests.test_one_hot_distribution_is_not_physical.test_one_hot_distribution_is_not_physical`
- `test_geometry.JointTests.test_product_coordinates.test_product_coordinates`
- `test_observations.ObservationTests.test_rank_deficient_calibration_rejected.test_rank_deficient_calibration_rejected`
- `test_geometry.OperationTests.test_rotation_order_matters.test_rotation_order_matters`
- `test_observations.ObservationTests.test_rotation_prediction_has_correct_sign_and_order.test_rotation_prediction_has_correct_sign_and_order`
- `test_observations.ObservationTests.test_schema_rejects_embedded_truth_and_duplicate_ids.test_schema_rejects_embedded_truth_and_duplicate_ids`
- `test_observations.ObservationTests.test_schema_requires_explicit_provenance.test_schema_requires_explicit_provenance`
- `test_geometry.ObservabilityTests.test_single_observation_vector.test_single_observation_vector`
- `test_geometry.JointTests.test_singlet_joint_probabilities_and_inverse.test_singlet_joint_probabilities_and_inverse`
- `test_observations.ObservationTests.test_uninformative_detector_rejected.test_uninformative_detector_rejected`
- `test_geometry.CenterAndGeometryTests.test_unique_common_center.test_unique_common_center`
- `test_geometry.MetricTests.test_unique_indefinite_metric_is_definitively_rejected.test_unique_indefinite_metric_is_definitively_rejected`
- `test_observations.ObservationTests.test_unphysical_sampling_estimate_preserves_raw_record.test_unphysical_sampling_estimate_preserves_raw_record`
- `test_geometry.TetraTests.test_vertices_and_fresh_storage.test_vertices_and_fresh_storage`

## Concerns and boundaries

The reference implementation has no known failing test. The repository snapshot was not globally green while the other workers were implementing their modules; the parent should run fresh integration verification after all workers finish. Validators use an absolute tolerance of `1e-10` unless a density validation caller provides a different tolerance. Tiny negative eigenvalues within the specified tolerance are accepted and preserved; the reference never silently clips or projects an input into the physical set. Probabilities are direct trace results without clipping/renormalization. This is an explicit NumPy reference for small Hilbert spaces rather than a sparse or large-system simulator.

No remote writes or commits were performed. Only owned source, test, report, and evidence files were written.
