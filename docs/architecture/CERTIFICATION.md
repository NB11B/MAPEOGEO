# Certification Subsystem Architecture

The Certification Subsystem (`mapeogeo.proof` and `mapeogeo.kernel.certification`) establishes an immutable, fail-closed verification perimeter.

---

## 1. Architectural Principle: Separation of Generation and Admission

A fundamental architectural boundary in MAPEOGEO v2 is:

$$\boxed{\text{Generation Audit} \neq \text{Admission Audit}}$$

- **Generation Audit**: Heuristic search, generative model proposals, prospective planning, and exploratory candidate generation. These processes are inherently speculative and non-authoritative.
- **Admission Audit**: Independent, deterministic, fail-closed verification. No candidate may enter the certified state $G$ without passing all admission gates.

---

## 2. The 4-Gate Kernel Certification Boundary

Every candidate unit of work $M$ must successfully clear four sequential verification gates:

```text
       Candidate Machinery Package M
                     │
                     ▼
       ┌───────────────────────────┐
       │ Gate 1: Prerequisites     │ ── Unmet Dependencies ──► REJECT
       └───────────────────────────┘
                     │ Valid
                     ▼
       ┌───────────────────────────┐
       │ Gate 2: Witnesses         │ ── Invalid Proof/Trace ──► REJECT
       └───────────────────────────┘
                     │ Valid
                     ▼
       ┌───────────────────────────┐
       │ Gate 3: Invariants        │ ── Conservation Breach ──► REJECT
       └───────────────────────────┘
                     │ Valid
                     ▼
       ┌───────────────────────────┐
       │ Gate 4: Reproducibility   │ ── Non-Deterministic ──► REJECT
       └───────────────────────────┘
                     │ Valid
                     ▼
       Admitted into Certified State G
```

1. **Gate 1 (Prerequisites)**: Verifies all declared input dependencies are reachable in current certified state $G_t$.
2. **Gate 2 (Witness Certificates)**: Validates cryptographic or formal proof witnesses demonstrating validity of claimed work.
3. **Gate 3 (Conservation Invariants)**: Verifies deficiency conservation ($\Delta D = 0$) and structural graph constraints.
4. **Gate 4 (Reproducibility)**: Confirms execution trace determinism and hash integrity.

---

## 3. Adversarial Robustness: $N_{\rm false\ acceptance} = 0$

Certification is strictly fail-closed. Incomplete witness data, malformed hashes, cyclic references, or boundary violations immediately reject the candidate. Across the entire release qualification suite, the count of false acceptances is strictly zero.
