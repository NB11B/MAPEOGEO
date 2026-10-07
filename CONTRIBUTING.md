# Contributing to MAPEOGEOv2

## Governing Principles

Development and migration in `MAPEOGEOv2` are governed by one fundamental invariant:

$$\boxed{\text{Nothing enters v2 because it is newer; it enters because it is canonical, traceable, and requalified.}}$$

### Invariants for All Contributions

1. **Global Invariant G1 (Scientific Immutability)**:
   Never modify frozen upstream artifacts or reinterpret historical research outcomes. Historical custody resides in `NB11B/MAPEOGEO`.
2. **Global Invariant G2 (Semantic Preservation)**:
   No relationship, proof, physical result, or experiment becomes stronger merely through migration.
3. **Global Invariant G3 (Domain Neutrality)**:
   $$\boxed{\texttt{kernel} \not\rightarrow \texttt{domains}, \quad \texttt{grammar} \not\rightarrow \texttt{domains}, \quad \texttt{graph} \not\rightarrow \texttt{domains}}$$
   The kernel, grammar, and graph layers must never import from any domain adapter.
4. **Global Invariant G4 (Qualification Independence)**:
   $$\boxed{\text{source qualified} \not\Rightarrow \text{v2 qualified}}$$
   Every ported component enters as `PENDING_V2_QUALIFICATION` and must pass its explicit v2 qualification gate before promotion to `V2_QUALIFIED`.
5. **Global Invariant G5 (Deficiency Conservation)**:
   $$D_t = D_{\text{resolved}} \sqcup D_{\text{reduced}} \sqcup D_{\text{unchanged}} \sqcup D_{\text{newly-exposed}}$$
   No required work may silently disappear during transformation or adaptation.
6. **Global Invariant G6 (Fail Closed)**:
   Unknown or ambiguous semantics remain unknown or ambiguous.
7. **Global Invariant G7 (Reproducibility)**:
   Every retained scientific claim must be backed by a reproduction fixture or an explicit provenance pointer to `NB11B/MAPEOGEO`.
8. **Global Invariant G8 (No History in Production Abstractions)**:
   Historical names (`gen1`..`gen12`, `wave_*`, `kernel_v*`, `experiment.*`, `portfolio_*`) are strictly forbidden in production module paths, class names, and public APIs.

---

## Verification Gates

All contributions must pass:
```bash
ruff format --check .
ruff check .
mypy
pytest
```
No PR will be merged if any architectural AST test fails.
