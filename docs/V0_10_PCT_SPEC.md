# MAPEOGEO PCT v0.10 Specification

## Governing Question

Can a finite chain complex representation together with declared chain maps and geometric projections (the Probe–Chain Transform architecture) provide a fail-closed, correspondence-sensitive foundation for mathematical geometry without collapsing algebraic invariants, conflating disparate semantic categories, or misattributing capabilities across representations?

## Architectural Invariants & Separation of Views

1. **Separation of Evidence and Kernel Verification**: Executable certificates produced by the PCT reference subsystem are recorded as executable evidence and never labeled `KERNEL_VERIFIED`. Formal verifications remain within Lean 4.
2. **Strict Semantics**: `SAME_SEMANTICS` is never inferred from equal Euler characteristic, equal Betti vectors, or reconstruction similarity alone.
3. **Exact vs Numerical Arithmetic**: Simplicial boundaries, homology ranks over $\text{GF}(2)$ and $\mathbb{Q}$, chain map residuals, and Euler–Poincaré identities are exact. Numerical approximations are confined to planar geometric operations with frozen tolerances.
4. **Distinct Applicability**: `NOT_APPLICABLE` is strictly separated from `PASS`, `FAIL`, `INVALID`, `ERROR`, and `INCONCLUSIVE`. Non-convex geometries refuse convex Steiner checks before evaluating.
5. **Lowest Capable Attribution**: Scientific capability is attributed strictly to the lowest sufficient baseline in the hierarchy $B0 \prec B1 \prec B2 \prec B3 \prec B4 \prec B5$.

## Frozen Corpus

The 2-D control corpus consists of 9 deterministic fixtures:
1. `triangle_loop`: 1-D combinatorial loop ($b=(1,1), \chi=0$).
2. `triangle_loop_subdivided`: 6-edge barycentrically subdivided 1-D loop.
3. `two_loops`: Disjoint union of two triangle loops ($b=(2,2), \chi=0$).
4. `filled_triangle`: 2-D simplicial 2-simplex with boundary ($b=(1,0,0), \chi=1$).
5. `equal_area_square`: Convex polygon with side $\sqrt{\pi}$, area $\pi$.
6. `equal_area_triangle`: Convex equilateral triangle with area $\pi$.
7. `square_annulus`: Non-convex domain with 1 hole ($\chi=0$), topological hole closure event at scale $s=1.0$.
8. `two_separated_squares`: Non-convex disjoint domain ($\chi=2$), component merger event at scale $s=1.0$.
9. `reentrant_control`: Non-convex L-shaped polygon refusing convex Steiner tube laws.

## Baseline Hierarchy

- **B0**: Global Euler characteristic $\chi$.
- **B1**: Ordered Betti tuple $(\beta_0, \beta_1, \dots)$.
- **B2**: Persistent homology pairing ledger.
- **B3**: Parameterized directional Euler response field.
- **B4**: Exact chain complex $(C_*, \partial_*)$ without maps.
- **B5**: Exact chain complex with chain maps $(F_*)$, residual support localization, and event provenance.

## Validity Gates (V0–V8)

- **V0**: Deterministic reproducibility of in-memory results across independent runs.
- **V1**: Boundary square condition $\partial^2 = 0$ holds identically for all complexes.
- **V2**: Exact Euler–Poincaré equality $\chi_{\text{chains}} = \chi_{\text{homology}}$ over $\text{GF}(2)$ and $\mathbb{Q}$.
- **V3**: Valid declared chain maps commute ($\partial F - F \partial = 0$) and corrupted maps are rejected.
- **V4**: Persistence filtration strictly orders faces before cofaces.
- **V5**: Subdivisions preserve homology and Euler characteristics.
- **V6**: Analytic geometric measurements match theoretical limits within $10^{-9}$.
- **V7**: Inapplicable geometric theorems return `NOT_APPLICABLE`.
- **V8**: Complete provenance tracking on all records.

## Scientific Hypotheses & Tests (S1–S10)

- **S1**: Separation of B0 Euler collision by B1 Betti numbers.
- **S2**: Invariant preservation under valid subdivision.
- **S3**: Detection and localization of corrupted correspondence by B5 where B0–B4 are blind.
- **S4**: Sub-nanometer convex reconstruction Hausdorff accuracy.
- **S5**: Comprehensive 1-probe ablation metrics and minimal passing probe subset search.
- **S6**: Lipschitz stability of support function under vertex perturbation.
- **S7**: Robustness of shape discrimination under probe erasure.
- **S8**: Localization of probe field response corruptions.
- **S9**: Recovery of scale-event topological transitions at $s=1.0 \pm 0.011$.
- **S10**: Discrimination of orientation-reversing maps via chain maps.

## Claim Boundary

A passing run demonstrates the soundness and fail-closed integrity of the PCT computational reference architecture. It does not claim universal transform injectivity, non-convex reconstruction, integral torsion recovery, or replacement of Lean 4 kernel verification.
