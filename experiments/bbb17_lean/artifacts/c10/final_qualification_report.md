# COLLATZ-C10: Unified Proof-Closure Campaign — Final Qualification Report

## 1. Executive Summary & Terminal Disposition

- **Active Campaign Branch**: `research/collatz-c10-proof-closure`
- **Preserved Checkpoints**:
  - `research/bbb17-lean-proof` at `fbf5d2b`
  - `research/collatz-three-tracks` at `dbf40bb`
  - `research/collatz-c6-adaptive-descent` at `48e6502`
- **Lean 4 Toolchain**: `leanprover/lean4:v4.29.0-rc8` (42 new C10 theorems across 6 modular Lean files, compiled with zero `sorry` and standard axioms only: `propext`, `Classical.choice`, `Quot.sound`)
- **Terminal Disposition**: **Option B — Exact Structural Reduction & Finite-Depth Unconditional Obstruction**.
  - **What is Unconditionally Proved in Lean 4**:
    1. **Universal Non-Descent Multiplicative Power Bound (`nondescent_prefix_power_bound`)** and **Two-Sided Non-Descent Diophantine Sandwich (`nondescent_diophantine_sandwich`)**:
       For *any* positive integer $n > 0$ and *any* depth $r \ge 1$ such that $\forall i \le r,\ F^i(n) \ge n$ (requiring **no** spectral assumptions and holding across arbitrarily many spectral crossings):
       $$(2^r - 3^{a_r}) n \le B(w_r), \qquad n^{a_r}\bigl(3^{a_r} n + B(w_r)\bigr) \le n (3 n + 1)^{a_r}, \qquad 2^r \cdot n^{a_r} \le (3 n + 1)^{a_r}.$$
    2. **Eventual Power Threshold Criterion (`power_threshold_forces_descent`, `eventual_power_threshold_implies_collatz`)**:
       The moment any depth $r \ge 1$ satisfies $2^r \cdot n^{a_r} > (3 n + 1)^{a_r}$, the trajectory of $n$ is guaranteed to have strictly descended below $n$ at some step $1 \le i \le r$.
    3. **Strict Necessity of Obligation A (`collatz_implies_everyNatCrossesSpectrally`)**:
       Every non-crossing prefix strictly grows (`noncrossing_prefix_strict_growth`), so any descent step $r$ is preceded by a first spectral crossing $t \le r$ (`descent_forces_prior_firstCrossing`).
    4. **Exact 2-Adic Lifting Recurrences & Pre-Crossing Criterion (`even_step_lift_deficit_recurrence`, `odd_step_lift_deficit_recurrence`, `firstCrossing_descent_iff_preCrossing_bound`)**:
       For every first-crossing word $w = w_1 \mathbin{+\!+} [\mathrm{false}]$, strict descent $y' < m'$ holds if and only if $y_1 < 2 m_1 + \ell (2 D_1 - A_1)$.
    5. **Universal Peak Drawdown & Reservoir Activation (`every_nat_experiences_peak_drawdown`)**:
       No positive integer $n > 0$ can have a monotonically non-decreasing trajectory forever; within $t \le n$ steps, $F^{t+1}(n) < F^t(n)$.
    6. **Unconditional Exclusion of Contracting Depths & Cycles up to $r = 64$ (`infinite_nondescent_diophantine_obstruction_system`, `no_nontrivial_cycle_length_le_64`)**:
       For any hypothetical never-descending integer $n > 1$, $n \ge 1024$ (`descent_of_lt_1024`) and $2^r \cdot 1024^{a_r} \le 3073^{a_r}$ for all $r \ge 1$. Because the Eliahou window $3^a < 2^r \land 2^r \cdot 1024^a \le 3073^a$ is kernel-certified empty for all $1 \le r \le 64$ (`checkEliahouWindow1024_64`), **no never-descending integer $n > 1$ can experience spectral contraction ($2^r > 3^{a_r}$) or periodicity ($F^r(n) = n$) at any depth $1 \le r \le 64$**.
  - **What Remains Open Asymptotically**:
    For $r \ge 65$ (beginning at $(r, a) = (65, 41)$ for $N_0 = 1024$), rational convergents of $\log_2 3$ satisfy $3^a < 2^r \le (3 + 1/N_0)^a$. Closing the full Collatz conjecture requires either proving that no integer trajectory can sustain $2^r n^{a_r} \le (3n + 1)^{a_r}$ for all $r \ge 1$, or simultaneously closing `EveryNatCrossesSpectrally` and `MinimalCrossingDeficitPositive` for arbitrary depths $r > 64$.

---

## 2. Gate Evaluation Summary (`G0`–`G6`)

| Gate | Scope | Status | Verification Evidence |
| :--- | :--- | :--- | :--- |
| **G0** | Baseline freeze & modular architecture | **PASSED** | `fbf5d2b`, `dbf40bb`, `48e6502` preserved; 6 Lean modules in `CollatzProofClosure/` |
| **G1** | 2-adic step lifting identities | **PASSED** | `even_step_lift_deficit_recurrence`, `odd_step_lift_deficit_recurrence`, `odd_step_lift_expansion_recurrence` |
| **G2** | Pre-crossing minimal-crossing descent law | **PASSED** | `firstCrossing_descent_iff_preCrossing_bound`; 0 true deficit exceptions across 65,534 words ($r \le 18$) and $n \le 100{,}000$ |
| **G3** | Spectral crossing necessity & band | **PASSED** | `collatz_implies_everyNatCrossesSpectrally`, `descent_forces_prior_firstCrossing`, `returnMap_expanding_strict_inequality` |
| **G4** | Global descent sandwich & cycle obstructions | **PASSED** | `nondescent_diophantine_sandwich`, `every_nat_experiences_peak_drawdown`, `oneCircuitWord_steiner_obstruction`, `no_nontrivial_cycle_length_le_64` |
| **G5** | Independent exact-integer falsification | **PASSED** | 7/7 Python test suites in `test_c10_all.py`; 4 intermediate hypotheses falsified & recorded in `counterexamples.jsonl` |
| **G6** | Unified synthesis & axiom audit | **PASSED** | `infinite_nondescent_diophantine_obstruction_system`, `c10_unified_convergence_criteria`; standard axioms only in `formal_axiom_audit.txt` |

---

## 3. Falsified Intermediate Hypotheses (`counterexamples.jsonl`)

1. **`CE-C10-01` (Coarse C8 Pincer `3 * m_min(w) * Delta(w) > a(w) * A(w)`)**:
   Falsified at `m_min in {27, 47, 63}` (`r = 59, 54, 54`), where $3 m_{\min} \Delta \le a A$ even though all three strictly descend (`27 -> 23`, `47 -> 46`, `63 -> 61`). Replaced by the exact 2-adic pre-crossing bound `y_1 < 2 m_1 + l * (2 D_1 - A_1)`.
2. **`CE-C10-02` (Single-Step Monotonicity of `v_2(n + 1)`)**:
   Falsified by `n = 62 -> 31`, where $v_2(62 + 1) = v_2(63) = 0$ jumps to $v_2(31 + 1) = v_2(32) = 5$ (`v2_succ_potential_even_step_jump_witness`). Replaced by `every_nat_exits_allTrue_branch` and `every_nat_experiences_peak_drawdown`.
3. **`CE-C10-03` (Single-Phase Linear `(u, v)` Potentials `alpha*u + beta*v` with `alpha > 0`)**:
   Falsified by `(j, u, v) = (0, 2, 0) -> (0, 4, 0)` (`positive_linear_uv_potential_strict_increase`). Replaced by the multiplicative prefix power bound `nondescent_prefix_power_bound`.
4. **`CE-C10-04` (Naive Cycle Exclusion without Minimum-Element Scaling)**:
   Replaced exponential $O(2^r)$ parity-word enumeration with the $O(r^2)$ Eliahou/C10 power-ratio window (`checkEliahouWindow1024_64`), certifying $1 \le r \le 64$ in the Lean 4 kernel.
