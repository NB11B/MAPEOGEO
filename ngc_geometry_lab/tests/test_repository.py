"""Independent checks of source adapters and the newly generated exact fixture."""
from collections import Counter, deque
import importlib
from itertools import combinations, permutations, product
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from numpy.testing import assert_allclose, assert_array_equal


def matrix_key(matrix):
    return tuple(tuple(int(value) for value in row) for row in matrix)


def signed_partial_permutation_family():
    """Enumerate coordinate maps directly, independently of generator products."""
    family = set()
    for rank in range(4):
        for rows in combinations(range(3), rank):
            for columns in combinations(range(3), rank):
                for image_columns in permutations(columns):
                    for signs in product((-1, 1), repeat=rank):
                        matrix = np.zeros((3, 3), dtype=np.int64)
                        for row, column, sign in zip(rows, image_columns, signs):
                            matrix[row, column] = sign
                        a, b, c = matrix
                        determinant = int(a[0]*(b[1]*c[2]-b[2]*c[1])
                                          - a[1]*(b[0]*c[2]-b[2]*c[0])
                                          + a[2]*(b[0]*c[1]-b[1]*c[0]))
                        if rank < 3 or determinant == 1:
                            family.add(matrix_key(matrix))
    return family


class RepositoryTestCase(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.find_spec("ngc_geometry_lab.repository")
        self.assertIsNotNone(spec, "repository adapter has not been implemented")
        self.repo = importlib.import_module("ngc_geometry_lab.repository")


class SourceTests(RepositoryTestCase):
    def test_imports_bind_real_modules_without_global_path_changes(self):
        before = list(sys.path)
        modules = self.repo.mapeogeo_modules()
        self.assertEqual(set(modules), {"algebra", "inverse", "observability", "work"})
        expected = {
            "algebra": "psmsl_operator_algebra_v1",
            "inverse": "latent_generator_v1",
            "observability": "latent_generator_observability_v2",
            "work": "psmsl_work_equivalence_v1",
        }
        for key, module in expected.items():
            self.assertIs(modules[key], importlib.import_module(
                "ngc_geometry_lab._vendor.mapeogeo.mapeogeo." + module))
        self.assertEqual(sys.path, before)

    def test_all_recorded_upstream_bytes_match_both_hash_algorithms(self):
        result = self.repo.verify_sources()
        self.assertEqual(result["mismatches"], [])
        self.assertEqual(set(result["manifests"]), {"mapeogeo", "mapeogeo_audit", "ngc_real"})
        expected_total = 0
        root = Path(self.repo.__file__).parent / "_vendor"
        for key, relative in (
            ("mapeogeo", "mapeogeo/SOURCE_PROVENANCE.json"),
            ("mapeogeo_audit", "mapeogeo/AUDIT_SOURCE_PROVENANCE.json"),
            ("ngc_real", "ngc_real/SOURCE_PROVENANCE.json"),
        ):
            count = len(json.loads((root / relative).read_text())["files"])
            self.assertEqual(result["manifests"][key]["verified_files"], count)
            self.assertEqual(result["manifests"][key]["mismatches"], [])
            expected_total += count
        self.assertEqual(result["verified_files"], expected_total)

    def test_changed_bytes_are_reported_without_mutating_real_source(self):
        root = Path(self.repo.__file__).parent / "_vendor"
        with tempfile.TemporaryDirectory() as temp:
            copied = Path(temp) / "sources"
            shutil.copytree(root, copied)
            changed = copied / "mapeogeo/mapeogeo/psmsl_operator_algebra_v1.py"
            changed.write_bytes(changed.read_bytes() + b"\n# test-only tampering\n")
            with patch.object(self.repo, "_VENDOR_ROOT", copied):
                result = self.repo.verify_sources()
        self.assertEqual(len(result["mismatches"]), 1)
        mismatch = result["mismatches"][0]
        self.assertEqual(mismatch["manifest"], "mapeogeo")
        self.assertEqual(mismatch["path"], "mapeogeo/psmsl_operator_algebra_v1.py")
        self.assertNotEqual(mismatch["expected_sha256"], mismatch["actual_sha256"])
        self.assertNotEqual(mismatch["expected_git_blob_sha1"], mismatch["actual_git_blob_sha1"])

    def test_missing_file_and_manifest_are_explicit_failures(self):
        root = Path(self.repo.__file__).parent / "_vendor"
        with tempfile.TemporaryDirectory() as temp:
            copied = Path(temp) / "sources"
            shutil.copytree(root, copied)
            (copied / "mapeogeo/mapeogeo/latent_generator_v1.py").unlink()
            (copied / "ngc_real/SOURCE_PROVENANCE.json").unlink()
            with patch.object(self.repo, "_VENDOR_ROOT", copied):
                result = self.repo.verify_sources()
        self.assertEqual(len(result["mismatches"]), 2)
        self.assertEqual({item["reason"] for item in result["mismatches"]},
                         {"missing_source", "unreadable_manifest"})


class DualLaneTests(RepositoryTestCase):
    def test_upstream_nonfinite_misshaped_and_unnormalized_outputs_are_rejected(self):
        bad_outputs = (
            np.array([np.nan, 0, 0, 0]),
            np.array([np.inf, 0, 0, 0]),
            np.array([1., 0]),
            np.array([[1., 0], [0, 0]]),
            np.array([2., 0, 0, 0]),
            np.array([1+1j, 0, 0, 0]),
        )
        for output in bad_outputs:
            with self.subTest(output=output):
                with patch.object(self.repo._dual_lane, 'apply_local_gate_dual_lane', return_value=output):
                    with self.assertRaisesRegex(ValueError, 'dual-lane backend output'):
                        self.repo.dual_lane_apply([1, 0], np.eye(2), [0], 1)

    def test_hadamard_and_phase_have_analytic_big_endian_results(self):
        h = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
        zero = np.array([1, 0, 0, 0], dtype=complex)
        assert_allclose(self.repo.dual_lane_apply(zero, h, [0], 2),
                        np.array([1, 0, 1, 0]) / np.sqrt(2), atol=1e-14)
        assert_allclose(self.repo.dual_lane_apply(zero, h, [1], 2),
                        np.array([1, 1, 0, 0]) / np.sqrt(2), atol=1e-14)
        theta = 0.7
        rz = np.diag([np.exp(-0.5j*theta), np.exp(0.5j*theta)])
        ket = np.array([1, 1j, -1, -1j]) / 2
        expected = ket * np.array([rz[0, 0], rz[0, 0], rz[1, 1], rz[1, 1]])
        assert_allclose(self.repo.dual_lane_apply(ket, rz, [0], 2), expected, atol=1e-14)

    def test_cnot_all_basis_vectors_and_reversed_target_order(self):
        cnot = np.array([[1, 0, 0, 0], [0, 1, 0, 0],
                         [0, 0, 0, 1], [0, 0, 1, 0]])
        basis = np.eye(4, dtype=complex)
        for targets, expected_indices in (([0, 1], [0, 1, 3, 2]),
                                           ([1, 0], [0, 3, 2, 1])):
            for index, target_index in enumerate(expected_indices):
                with self.subTest(targets=targets, index=index):
                    assert_array_equal(self.repo.dual_lane_apply(basis[:, index], cnot, targets, 2),
                                       basis[:, target_index])

    def test_complex_unitary_matches_dense_kron_without_running_oracle(self):
        rng = np.random.default_rng(2703)
        gate, _ = np.linalg.qr(rng.normal(size=(2, 2)) + 1j*rng.normal(size=(2, 2)))
        state = rng.normal(size=4) + 1j*rng.normal(size=4)
        state /= np.linalg.norm(state)
        with patch("ngc_geometry_lab.reference.local_gate",
                   side_effect=AssertionError("repository adapter must not run the oracle")):
            actual = self.repo.dual_lane_apply(state, gate, [1], 2)
        assert_allclose(actual, np.kron(np.eye(2), gate) @ state, atol=1e-13)

    def test_adapter_does_not_mutate_or_renormalize_inputs(self):
        state = np.array([1, 1j, 1, 1j]) / 2
        gate = np.array([[0, -1j], [-1j, 0]])
        saved_state, saved_gate = state.copy(), gate.copy()
        self.repo.dual_lane_apply(state, gate, [np.int64(0)], np.int64(2))
        assert_array_equal(state, saved_state)
        assert_array_equal(gate, saved_gate)
        with self.assertRaises(ValueError):
            self.repo.dual_lane_apply(2*state, gate, [0], 2)

    def test_invalid_arguments_are_rejected_before_permissive_upstream_casts(self):
        state, gate = [1, 0, 0, 0], np.eye(2)
        cases = [
            (state, gate, [0], 2.0), (state, gate, [0], True),
            (state, gate, [0], 0), (state, gate, [0], -2),
            (state, gate, [0], 10**9),
            (state, gate, [0.0], 2), (state, gate, [True], 2),
            (state, gate, [np.bool_(False)], 2), (state, gate, ["0"], 2),
            (state, gate, [], 2), (state, gate, [0, 0], 2),
            (state, gate, [2], 2), (state, gate, [-1], 2),
            (state, gate, None, 2), (state, gate, [[0]], 2),
            ([1, 0], gate, [0], 2), ([0, 0, 0, 0], gate, [0], 2),
            ([[1, 0], [0, 0]], gate, [0], 2),
            ([np.nan, 0, 0, 0], gate, [0], 2),
            ([np.inf, 0, 0, 0], gate, [0], 2),
            (state, np.eye(4), [0], 2), (state, 2*gate, [0], 2),
            (state, [[1, np.inf], [0, 1]], [0], 2),
            (state, [[1, np.nan], [0, 1]], [0], 2),
            (state, [1, 0], [0], 2), (state, [[1], [0, 1]], [0], 2),
        ]
        for arguments in cases:
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                self.repo.dual_lane_apply(*arguments)


class ConnectedDemoTests(RepositoryTestCase):
    def test_fusion_information_and_work_counterexample_match_independent_matrices(self):
        result = self.repo.connected_operator_demo()
        json.dumps(result, allow_nan=False)
        self.assertTrue(result["qualified"])
        self.assertTrue(all(result["checks"].values()))
        composition = result["composition"]
        a, b = np.array(composition["A"]), np.array(composition["B"])
        assert_array_equal(composition["fused"], b @ a)
        assert_array_equal(composition["numpy_product"], b @ a)
        self.assertEqual(composition["max_abs_error"], 0)
        info = result["information"]
        self.assertEqual(info["rank"], np.linalg.matrix_rank(info["matrix"]))
        self.assertEqual(info["nullity"], 1)
        self.assertTrue(info["information_loss"])
        work = result["work_equivalence"]
        a, b, p = (np.array(work[key], dtype=np.int64) for key in ("A", "B", "observation"))
        self.assertFalse(np.array_equal(a @ b, b @ a))
        assert_array_equal(p @ a @ b, p @ b @ a)
        self.assertTrue(work["upstream_result"]["equivalent_for_work"])
        self.assertFalse(work["upstream_test_expected_equivalent"])
        self.assertTrue(work["corrected_expected_equivalent"])

    def test_temporal_observations_recover_three_coordinates_but_duplicates_do_not(self):
        result = self.repo.connected_operator_demo()
        dynamic = result["observability"]
        a, c = np.array(dynamic["transition"]), np.array(dynamic["observation"])
        expected = np.vstack([c @ np.linalg.matrix_power(a, k) for k in range(3)])
        assert_array_equal(dynamic["matrix"], expected)
        assert_array_equal(dynamic["recovered_state"], [1, 2, 3])
        self.assertEqual(dynamic["identifiable_rank"], 3)
        self.assertEqual(dynamic["null_basis"], [])
        self.assertFalse(dynamic["source_identified"])
        duplicate = result["duplicate_observations"]
        self.assertEqual(np.linalg.matrix_rank(duplicate["matrix"]), 1)
        self.assertEqual(duplicate["identifiable_rank"], 1)
        self.assertEqual(len(duplicate["null_basis"]), 2)
        self.assertFalse(duplicate["source_identified"])


class ExactClosureTests(RepositoryTestCase):
    _result = None

    def closure(self):
        if type(self)._result is None:
            type(self)._result = self.repo.exact_closure()
        return type(self)._result

    def test_full_matrix_set_matches_independent_coordinate_map_enumeration(self):
        result = self.closure()
        expected = signed_partial_permutation_family()
        actual = {matrix_key(matrix) for matrix in result["matrices"]}
        self.assertEqual(actual, expected)
        self.assertEqual(result["size"], len(expected))
        self.assertEqual(len(result["matrices"]), len(actual))
        self.assertEqual(result["provenance"], "new qualification fixture; not recovered sealed artifact")
        for matrix in result["matrices"]:
            self.assertTrue(all(type(value) is int for row in matrix for value in row))
        json.dumps(result, allow_nan=False)

    def test_every_table_product_matches_independent_numpy_integer_multiplication(self):
        result = self.closure()
        matrices = np.asarray(result["matrices"], dtype=np.int64)
        lookup = {matrix_key(matrix): index for index, matrix in enumerate(matrices)}
        table = result["multiplication_table"]
        for left, matrix in enumerate(matrices):
            products = matrix @ matrices
            expected = [lookup[matrix_key(value)] for value in products]
            self.assertEqual(table[left], expected)
        validation = result["validation"]
        self.assertEqual(validation["product_comparisons"], len(matrices)**2)
        self.assertEqual(validation["product_mismatches"], 0)

    def test_all_associativity_triples_and_identity_zero_laws(self):
        result = self.closure()
        table = np.asarray(result["multiplication_table"], dtype=np.int64)
        size = len(table)
        for left in range(size):
            assert_array_equal(table[table[left, :], :], table[left, table])
        identity, zero = result["identity_index"], result["zero_index"]
        assert_array_equal(table[identity], np.arange(size))
        assert_array_equal(table[:, identity], np.arange(size))
        assert_array_equal(table[zero], np.full(size, zero))
        assert_array_equal(table[:, zero], np.full(size, zero))
        self.assertEqual(result["validation"]["associativity_triples"], size**3)
        self.assertEqual(result["validation"]["associativity_mismatches"], 0)

    def test_shortest_words_reconstruct_matrices_and_have_bfs_minimum_length(self):
        result = self.closure()
        generators = result["generators"]
        matrix_indices = {matrix_key(matrix): i for i, matrix in enumerate(result["matrices"])}
        generator_indices = [matrix_indices[matrix_key(generators[name])] for name in result["generator_order"]]
        table = result["multiplication_table"]
        distances = {result["identity_index"]: 0}
        queue = deque(distances)
        while queue:
            current = queue.popleft()
            for generator in generator_indices:
                target = table[current][generator]
                if target not in distances:
                    distances[target] = distances[current] + 1
                    queue.append(target)
        for index, word in enumerate(result["shortest_words"]):
            product_matrix = np.eye(3, dtype=np.int64)
            for name in word:
                product_matrix = product_matrix @ np.asarray(generators[name], dtype=np.int64)
            assert_array_equal(product_matrix, result["matrices"][index])
            self.assertEqual(len(word), distances[index])

    def test_rank_units_idempotents_nilpotents_center_and_commuting_pairs(self):
        result = self.closure()
        matrices = np.asarray(result["matrices"], dtype=np.int64)
        rank_histogram = Counter(str(np.linalg.matrix_rank(matrix)) for matrix in matrices)
        self.assertEqual(result["rank_histogram"], dict(rank_histogram))
        self.assertEqual(result["units"], [i for i, matrix in enumerate(matrices)
                                          if np.linalg.matrix_rank(matrix) == 3])
        self.assertEqual(result["idempotents"], [i for i, matrix in enumerate(matrices)
                                                if np.array_equal(matrix @ matrix, matrix)])
        self.assertEqual(result["nilpotents"], [i for i, matrix in enumerate(matrices)
                                               if not np.any(matrix @ matrix @ matrix)])
        self.assertIn(result["zero_index"], result["nilpotents"])
        commuting = np.empty((len(matrices), len(matrices)), dtype=bool)
        for i, left in enumerate(matrices):
            commuting[i] = np.all(left @ matrices == matrices @ left, axis=(1, 2))
        self.assertEqual(result["center"], np.flatnonzero(commuting.all(axis=1)).tolist())
        self.assertEqual(result["commuting_ordered_pairs"], int(commuting.sum()))

    def test_stable_indices_and_words_are_reproducible(self):
        self.assertEqual(self.closure(), self.repo.exact_closure())

    def test_unbounded_generator_hits_explicit_enumeration_guard(self):
        dilation = ((2, 0, 0), (0, 1, 0), (0, 0, 1))
        with self.assertRaisesRegex(RuntimeError, "guard.*5"):
            self.repo._enumerate_matrices({"dilation": dilation}, max_elements=5)


if __name__ == "__main__":
    unittest.main()
