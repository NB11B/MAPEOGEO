# C10 Scale Benchmark & Ground-Truth Oracle Report

## Executive Summary
- **Stage**: C10 Scale Benchmark
- **Status**: **PASSED**
- **Authority Evaluator Throughput**: **33365.48 evaluations/second** (0.03 ms/eval)
- **Ground-Truth Oracle**: **PASSED** across all tiers (1k, 10k, 100k nodes)

## Network Intelligence Graph Benchmarks

| Metric | Scale 1 (1,000 Nodes) | Scale 2 (10,000 Nodes) | Scale 3 (100,000 Nodes) |
| :--- | :---: | :---: | :---: |
| **Node Count** | 1,000 | 10,000 | 100,000 |
| **Edge Count** | 1,001 | 10,001 | 100,001 |
| **Graph Construction Time** | 0.0032 s | 0.0154 s | 0.2348 s |
| **Matrix Projection Time** | 0.0007 s | 0.0072 s | 0.0804 s |
| **Path Finding Time** | 1.1e-05 s | 1.4e-05 s | 2.1e-05 s |
| **Chokepoint Detection Time** | 0.0003 s | 0.0028 s | 0.0425 s |
| **Ground-Truth Oracle** | **PASSED** | **PASSED** | **PASSED** |

## Ground-Truth Oracle Invariants Verified
1. **Exact Articulation Recovery**: Seeded chokepoints (`chokepoint_alpha`, `chokepoint_beta1`, `chokepoint_beta2`) exactly identified at all scales with 0 false positives.
2. **Negative Control Rejection**: Intra-functional and boundary nodes (`ingress`, `egress`, `leaf`, background nodes) strictly excluded.
3. **Exact Multi-Hop Traversal**: Recovered exactly 2 paths of length 3 hops connecting ingress to egress.
4. **Sub-second Scalability**: Graph construction, matrix projection, path finding, and chokepoint analysis for 100,000 nodes execute in < 0.5s total.
