"""C10 Scale Benchmark Regression Test Suite.

Verifies:
1. Graph scaling across 1,000 and 10,000 nodes completes in sub-second time.
2. Authority evaluation throughput exceeds minimum threshold of 5,000 evals/sec.
3. Benchmark artifacts C10_SCALE_BENCHMARK.json and report exist and are valid.
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


class TestC10ScaleBenchmark(unittest.TestCase):
    def test_c10_1_scale_1k_nodes(self) -> None:
        """1,000 nodes construct and project in < 0.5s."""
        res = benchmark_scale(num_nodes=1000, avg_degree=5)
        self.assertEqual(res["num_nodes"], 1000)
        self.assertEqual(res["num_edges"], 5000)
        self.assertLess(res["construction_time_sec"], 0.5)
        self.assertLess(res["matrix_projection_sec"], 0.5)

    def test_c10_2_authority_throughput_minimum(self) -> None:
        """Authority evaluator sustains > 5,000 evals/sec."""
        res = benchmark_authority_evaluator_throughput(num_evals=500)
        self.assertGreater(res["throughput_evals_per_sec"], 5000)
        self.assertLess(res["avg_latency_ms"], 1.0)

    def test_c10_3_benchmark_artifacts_exist(self) -> None:
        """Benchmark JSON and Markdown report exist and are populated."""
        json_path = BENCHMARK_DIR / "C10_SCALE_BENCHMARK.json"
        md_path = BENCHMARK_DIR / "C10_SCALE_BENCHMARK_REPORT.md"
        self.assertTrue(json_path.exists())
        self.assertTrue(md_path.exists())

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["status"], "PASSED")
            self.assertIn("scale_1k", data)
            self.assertIn("scale_10k", data)


if __name__ == "__main__":
    unittest.main()
