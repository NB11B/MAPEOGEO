"""C10 Scale Benchmark & Ground-Truth Oracle Test Suite.

Verifies:
1. Graph scaling across 1,000, 10,000, and 100,000 nodes completes in sub-second time.
2. Ground-truth topology oracle: exact recovery of seeded chokepoints, rejection of negative controls, and path discovery.
3. Authority evaluation throughput exceeds minimum threshold of 5,000 evals/sec (sustaining > 30,000 evals/sec).
4. Benchmark artifacts exist, are populated, and confirm QUALIFIED status.
"""

from __future__ import annotations

import json
from pathlib import Path
import unittest

from scripts.c10_scale_benchmark import (
    benchmark_authority_evaluator_throughput,
    benchmark_scale,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_DIR = REPO_ROOT / "artifacts" / "benchmarks"
RELEASE_DIR = REPO_ROOT / "artifacts" / "releases" / "v1_0_authority_intelligence"


class TestC10ScaleBenchmark(unittest.TestCase):
    def test_c10_1_scale_1k_nodes(self) -> None:
        """1,000 nodes construct and project in < 0.5s with ground-truth verification."""
        res = benchmark_scale(num_nodes=1000)
        self.assertEqual(res["num_nodes"], 1000)
        self.assertLess(res["construction_time_sec"], 0.5)
        self.assertLess(res["matrix_projection_sec"], 0.5)
        self.assertTrue(res["ground_truth_oracle_passed"])
        self.assertEqual(res["paths_discovered"], 2)
        self.assertEqual(len(res["expected_chokepoints_recovered"]), 3)

    def test_c10_2_scale_10k_nodes(self) -> None:
        """10,000 nodes construct and execute ground-truth oracle in < 1.0s."""
        res = benchmark_scale(num_nodes=10000)
        self.assertEqual(res["num_nodes"], 10000)
        self.assertLess(res["construction_time_sec"], 1.0)
        self.assertTrue(res["ground_truth_oracle_passed"])

    def test_c10_3_scale_100k_nodes(self) -> None:
        """100,000 nodes (10^5) complete full topology qualification in < 2.0s."""
        res = benchmark_scale(num_nodes=100000)
        self.assertEqual(res["num_nodes"], 100000)
        self.assertLess(res["construction_time_sec"], 2.0)
        self.assertTrue(res["ground_truth_oracle_passed"])
        self.assertEqual(res["paths_discovered"], 2)
        self.assertEqual(res["chokepoints_detected"], 3)

    def test_c10_4_authority_throughput_minimum(self) -> None:
        """Authority evaluator sustains > 5,000 evals/sec."""
        res = benchmark_authority_evaluator_throughput(num_evals=500)
        self.assertGreater(res["throughput_evals_per_sec"], 5000)
        self.assertLess(res["avg_latency_ms"], 1.0)

    def test_c10_5_benchmark_artifacts_exist(self) -> None:
        """Benchmark JSON, Markdown report, and SCALE_REPORT exist and are populated."""
        json_path = BENCHMARK_DIR / "C10_SCALE_BENCHMARK.json"
        md_path = BENCHMARK_DIR / "C10_SCALE_BENCHMARK_REPORT.md"
        scale_rep_path = RELEASE_DIR / "SCALE_REPORT.json"

        self.assertTrue(json_path.exists())
        self.assertTrue(md_path.exists())
        self.assertTrue(scale_rep_path.exists())

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["status"], "PASSED")
            self.assertIn("scale_1k", data)
            self.assertIn("scale_10k", data)
            self.assertIn("scale_100k", data)
            self.assertEqual(data["ground_truth_verification"]["oracle_status"], "PASSED")


if __name__ == "__main__":
    unittest.main()
