# Execution Math Supplement

This supplement maps runtime identities to implementations and tests. It is intentionally compact so it can be updated as the executable proof harness grows.

## M15. Real-phase gate constructor validity

Standard gates can be represented as realified block operators while preserving unitary norm geometry and canonical phase geometry:

```text
G_R^T G_R = I
G_R^T J G_R = J
```

Implementation: `ngc_rq/gates.py`.

Tested by: `tests/test_gates.py`.

## M16. Real-only local gate update equivalence

For a local gate `G=A+iB`, the real-lane update is:

```text
q_block' = A q_block - B p_block
p_block' = B q_block + A p_block
```

Implementation: `apply_local_gate`, `RealPhaseCircuit.run`.

Tested by: `tests/test_circuit.py`, `benchmarks/bench_backend_compare.py`.

## M17. Circuit-level probability equivalence

```text
Pr_R(x) = q_x^2 + p_x^2 = |psi_x|^2 = Pr_C(x)
```

Implementation: `RealPhaseCircuit.probabilities`, `probability_dict`.

Tested by: circuit tests and backend benchmarks.

## M18. Dual-lane backend equivalence

The same local update can be split into scheduled q-lane and p-lane paths:

```text
q_lane: A q - B p
p_lane: B q + A p
sync:   [q_lane, p_lane]
```

Implementation: `apply_local_gate_dual_lane`, `RealPhaseCircuit.run(backend="dual_lane")`.

Tested by: `tests/test_dual_lane_backend.py`, backend benchmarks.

## M19. Marginal probability and Z expectation extraction

```text
Pr(x) = q_x^2 + p_x^2
E[Z_k] = sum_x (-1)^{x_k} Pr(x)
```

Implementation: `marginal_probabilities`, `expectation_z`.

Tested by: `tests/test_observables_sampling.py`.

## M20. Sampling from real-phase probabilities

```text
samples ~ Pr_R(x)
```

Implementation: `RealPhaseCircuit.sample_counts`.

Tested by: `tests/test_observables_sampling.py`.

## M21. Pauli-string expectation equivalence

For Pauli string `P`:

```text
<P>_R = <psi|P|psi>
```

Implementation: `expectation_pauli_string_real_phase`, `RealPhaseCircuit.expectation_pauli`.

Tested by: `tests/test_pauli_observables.py`.

## M22. Backend sweep measurement

Backend comparison tracks runtime, error, and peak memory proxy over qubit sweeps.

Implementation: `benchmarks/bench_backend_sweep.py`, `benchmarks/benchmark_artifact.json`.

Tested by: CI backend sweep smoke command and artifact schema test.

## M23. Controlled and multi-controlled gate equivalence

A controlled one-qubit gate is:

```text
|0><0| tensor I + |1><1| tensor U
```

A multi-controlled one-qubit gate extends the same projector structure to the all-controls-one subspace:

```text
(I - |11...1><11...1|)_controls tensor I_target
+ |11...1><11...1|_controls tensor U_target
```

`MCPHASE(theta, k)` is the diagonal all-ones phase specialization, while `MCONTROLLED(PHASE(theta), k)` is the arbitrary-gate constructor route to the same operator.

Implementation: `CONTROLLED`, `MCONTROLLED`, `CRX`, `CRY`, `CRZ`, `MCX`, `TOFFOLI`, `CCNOT`, `CPHASE`, `MCPHASE`, `MCPHASE_SINGLE`.

Tested by: `tests/test_controlled_gates.py`, `tests/test_multicontrolled_general_gates.py`.

## M24. Vectorized local backend equivalence

Batching local blocks gives:

```text
Q' = A Q - B P
P' = B Q + A P
```

This remains real-valued, local-block based, and avoids dense global operators.

Implementation: `apply_local_gate_vectorized`, `RealPhaseCircuit.run(backend="vectorized")`.

Tested by: `tests/test_vectorized_backend.py`, `tests/test_premise_guardrails.py`, backend benchmarks.

## M25. Premise guardrail equivalence

All execution backends must agree on canonical finite-dimensional outputs:

```text
state_local = state_dual_lane = state_vectorized
Pr_R(x) = Pr_C(x)
observable_R in R
```

Implementation: `docs/premise_alignment.md`, `tests/test_premise_guardrails.py`.

Tested by: `tests/test_premise_guardrails.py`.

## M26. Arbitrary local observable equivalence

For a local Hermitian observable `O=A+iB` acting on selected target qubits:

```text
<O>_R = z^T R(O_local) z
<O>_R = Re(<psi|O_local|psi>)
```

Implementation: `expectation_local_operator_real_phase`, `RealPhaseCircuit.expectation_local_operator`.

Tested by: `tests/test_local_observables.py`.

## M27. Reduced density output equivalence

For a pure state `psi=q+ip`, reduced density on kept subsystem indices is computed directly from q/p lane blocks:

```text
Re(rho_ij) = sum_e q_ie q_je + p_ie p_je
Im(rho_ij) = sum_e p_ie q_je - q_ie p_je
```

The output is returned as a `RealPhaseOperator`, preserving the real-phase representation at the API boundary.

Implementation: `reduced_density_real_phase`, `RealPhaseCircuit.reduced_density`.

Tested by: `tests/test_reduced_density_outputs.py`.

## M28. Phase-gradient gate equivalence

A phase-gradient gate applies diagonal phases over computational basis index `k`:

```text
|k> -> exp(i theta k / 2^n) |k>
```

Realification turns each diagonal complex phase into a real 2D lane rotation while preserving probabilities and phase-sensitive observables.

Implementation: `PHASE`, `PHASE_GRADIENT`, `QFT_PHASES`.

Tested by: `tests/test_phase_gradient_gates.py`.
