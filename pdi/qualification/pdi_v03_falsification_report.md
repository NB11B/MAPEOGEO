# PDI-135M-v0.3: Scientific Falsification Report

**Experiment:** PDI-135M-v0.3 (Prospective $K=8$ Menu Selection with Minimal State Projection)  
**Date:** 2026-10-08  
**Baseline Git Commit:** `c4c502c`  
**Branch:** `experiment/pdi-135m-v0.3-k8`  
**Dataset:** 49 Frozen Holdout Scenarios (`pdi-corpus-v0.1`)  
**Evaluator:** Candidate Oracle (`CandidateOracle`), RTL Simulation (`tb_pdi_k8_selected_work.sv`)

---

## 1. Core Scientific Questions & Hypotheses

| Hypothesis | Proposition | Test Method | Verdict |
| :--- | :--- | :--- | :--- |
| **H1: Menu Coverage** | An 8-slot deterministic machine menu $\mathcal A(S)$ constructed without oracle knowledge can contain the optimal work proposal $\ge 95\%$ of the time. | `DeterministicCandidateGenerator` evaluated by `CandidateOracle` on 49 holdouts. | **CONFIRMED** (100.00% Coverage@8) |
| **H2: Zero-Shot Selector** | Frozen SmolLM2-135M can reliably select the optimal candidate from an 8-slot menu without fine-tuning ($\ge 80\%$). | Greedy constrained decoding on permuted menus (seeds 42, 137, 2026). | **FALSIFIED** (1.36% Top-1, 1.36% Useful) |
| **H3: Projection Impact** | Compact PSMSL multivector projection (E2) or memory snapshots (E3) improve model selection over minimal context (E0). | Context arm ablation (E0 vs E1 vs E2 vs E3 vs E4). | **FALSIFIED** (Flat 1.36% accuracy across all arms) |
| **H4: Generation Latency** | Combinatorial candidate generation in software introduces substantial latency overhead relative to model inference. | High-resolution wall-clock timer profiling (`LatencyProfiler`). | **FALSIFIED** (Candidate Gen p50: 0.02ms vs Inference p50: 61.87ms) |
| **H5: Model vs Heuristic** | Learned frozen model selector outperforms simple deterministic keyword/operand heuristics. | Comparative benchmark against `DeterministicHeuristicSelector`. | **FALSIFIED** (Heuristic: 14.97% useful vs SmolLM2: 1.36%) |
| **H6: Authority Invariance** | Dispatching menu-selected proposals to the RTL fabric maintains zero unauthorized state mutation and identical disposition semantics. | R01–R15 differential equivalence suite on Verilog simulation (`tb_pdi_k8_selected_work.sv`). | **CONFIRMED** (15/15 passed, 100% equivalence) |

---

## 2. Detailed Findings

### H1: Candidate Menu Coverage ($\mathcal A(S)$)
- **Result:** **100.00%** (49/49 holdouts).
- **Mechanism:** The deterministic candidate generator analyzes observable state ($S$) and goal prompts without seeing target output labels. By systematically generating arity-appropriate actions with visible operands and providing an explicit abstention slot (`Slot 8`), optimal proposals were present in all 49 frozen scenarios.
- **Scientific Implication:** The search space for execution on the FPGA can be strictly bounded to $K=8$ candidate slots without sacrificing expressiveness or task coverage.

### H2 & H5: Frozen SmolLM2-135M vs Baseline Selectors
Evaluating 735 total model selections (49 scenarios $\times$ 3 seeds $\times$ 5 arms) yielded:

| Selector | Conditional Top-1 (%) | End-to-End Useful (%) | Permutation Consistency (%) | Selection Latency p50 (ms) |
| :--- | :---: | :---: | :---: | :---: |
| **Oracle (Upper Bound)** | 10.20% | 100.00% | 95.92% | 0.00 ms |
| **Uniform Random** | 2.72% | 2.72% | 0.00% | 0.01 ms |
| **First-Eligible** | 1.36% | 1.36% | 0.00% | 0.00 ms |
| **Deterministic Heuristic** | 6.80% | **14.97%** | **79.59%** | 0.01 ms |
| **Frozen SmolLM2-135M** | 1.36% | 1.36% | 0.00% | 63.71 ms |

- **Falsification of H2:** Frozen SmolLM2-135M fails to identify optimal candidates zero-shot. In v0.2, apparent menu selection accuracy was inflated because ground truth was always placed at Option 1. When menus are permuted across seeds `42`, `137`, and `2026`, the frozen model displays severe positional bias and 0.00% permutation consistency (100% order sensitivity).
- **Falsification of H5:** The simple deterministic heuristic achieved **14.97% useful selection** with **79.59% permutation consistency**, outperforming the frozen 135M model by $>10\times$ while running in $10\,\mu\text{s}$ ($>6000\times$ faster).

### H3: State Projection Ablation (E0 through E4)

| Context Arm | Prompt Tokens (mean) | Model Top-1 (%) | Useful Selection (%) | Latency p50 (ms) | E2E Latency p50 (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **E0: Minimal (Goal only)** | 291.82 | 1.36% | 1.36% | 117.16 ms | 117.20 ms |
| **E1: Bounded Slots** | 330.61 | 1.36% | 1.36% | 61.87 ms | 61.91 ms |
| **E2: PSMSL Symbolic** | 338.39 | 1.36% | 1.36% | 62.26 ms | 62.30 ms |
| **E3: Memory Snapshot** | 421.39 | 1.36% | 1.36% | 63.89 ms | 63.94 ms |
| **E4: Graph + Causal** | 367.31 | 1.36% | 1.36% | 119.32 ms | 119.36 ms |

- **Finding:** For an untrained/frozen selector, increasing context sophistication (from 291 tokens in E0 to 421 tokens in E3) provides zero improvement in decision quality (holding constant at 1.36%). Richer context merely incurs additional tokenization overhead.

### H4: Latency Breakdown Analysis
- **Candidate Generation:** Mean 0.02 ms, p50 0.02 ms, p95 0.03 ms.
- **State Projection:** Mean 0.03 ms, p50 0.03 ms, p95 0.04 ms.
- **Model Inference:** Mean 63–117 ms, p50 61.87–119.32 ms.
- **Conclusion:** Candidate generation represents $<0.05\%$ of total turnaround time. Bounding the FPGA proposal space via machine-generated menus introduces essentially zero computational overhead on the host.

### H6: Hardware Authority Invariance (R01–R15 Matrix)
- 15/15 test vectors passed identically in RTL simulation (`iverilog`/`vvp`).
- Valid arithmetic proposals (`OP_ADD`, `OP_SUB`, `OP_MUL`, `OP_CL20_PRODUCT`, `OP_REVERSE`, `OP_GRADE_INVOLUTION`, `OP_CLIFFORD_CONJUGATE`, `OP_VECTOR_DOT`, `OP_VECTOR_WEDGE`, `OP_COMPARE`, `OP_NOP`) executed and committed in exactly 60 clock cycles.
- Hardware validator intercepted unregistered opcodes, unauthorized capabilities, stale versions, and out-of-bounds references at ingress in 51 clock cycles without mutating state memory.
- **Zero unauthorized state mutations** observed.

---

## 3. Core Architectural Takeaways
1. **The deterministic menu framing ($K=8$) is highly successful:** Bounding work proposals to 8 machine-generated choices preserves 100% of optimal actions while guaranteeing syntactic validity and hardware safety.
2. **Frozen LLMs cannot rank candidates without tuning:** SmolLM2-135M cannot perform zero-shot candidate menu selection. Fine-tuning directly on candidate ranking / preference pairs is mandatory for v0.4.
3. **Deterministic heuristics provide a strong immediate baseline:** A rule-based keyword/operand heuristic achieves $11\times$ higher accuracy than the frozen model at $6000\times$ lower latency.
