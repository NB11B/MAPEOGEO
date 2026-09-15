# MAPEOGEO E1–E25 Computational Experiment Campaign

**Campaign status:** COMPLETE

**Experiments executed:** 25 / 25

## Results index

| Experiment | Status | Main result |
|---|---|---|
| E1 | EXPLORATORY_COMPLETE | 7,625 canonical 4x4 cell objects: Euler left 8,708,406 collision pairs; 32 directional Euler sweeps left 0. |
| E2 | EXACT_OPTIMUM_CERTIFIED | Exact MILP certified a global minimum of 2 directions, within the frozen 32-direction bank, to separate all 7,625 E1 objects given B2. |
| E3 | COMPLETE | Exact erasure optima followed 2,4,6,...,16 probes for tolerating 0..7 arbitrary erasures; 30 of 496 two-probe choices separate the entire E1 corpus. |
| E4 | PASS | 1,500 deterministic perturbation trials satisfied the support-function perturbation bound. |
| E5 | COMPLETE | 36/36 single-entry map corruptions were caught by dF-Fd, but 26/26 cycle-injection adversaries remained chain-map valid; 20 changed H1 degree. |
| E6 | PASS | Same circle state invariants, different induced degrees/Lefschetz numbers; rotations remain homologically invisible. |
| E7 | PASS | A closed loop in coefficients of z^2=w returned to the same polynomial while continuously transported roots swapped. |
| E8 | PASS | All 6 analytic hole-closure/component-merger scales were recovered. |
| E9 | PASS | Convex Steiner controls passed; reentrant, holed, and disconnected cases were correctly refused as NOT_APPLICABLE. |
| E10 | PASS | All 20 three-point probes on a six-point space gave exact Euler-Radon inversion; a restricted family exposed an explicit null space. |
| E11 | PASS | Exact null-space dimensions quantified what each 4x4 scalar-field probe family cannot see. |
| E12 | PASS | Good-cover nerve recovered circle H1; deliberately disconnected intersection violated the hypothesis and produced the wrong nerve topology. |
| E13 | PASS | Boolean-lattice zeta transform was inverted exactly by Möbius inversion; cumulative event signals were exactly differenced back to events. |
| E14 | PASS | 1,770 small barcodes demonstrated strict barcode -> Betti curve -> Euler curve information loss. |
| E15 | PASS | For Boolean posets B1..B5, exact restricted-Hom minima were n probes for 2^n objects. |
| E16 | PASS | All 56 incorrect EO/GEO D4 pairings passed internal EO validity but failed the cross-view commutative diagram. |
| E17 | PASS | Exactly nonsingular Hilbert matrices were under-ranked first at n=6 in float32 and n=11 in float64 under the runtime's default rank heuristic. |
| E18 | PASS | 24/24 single incidence-sign corruptions were detected and uniquely localized by chain residual provenance; Euler/cell counts detected none. |
| E19 | PASS | Regular polygon support spectra obeyed n-fold harmonic selection rules under commensurate sampling. |
| E20 | PASS | Mixed-area relative defect was zero for self-probes and positive for every tested nonhomothetic cross-probe. |
| E21 | PASS | 2D and 3D parallel-body generators were symbolically nilpotent and preserved the derived polynomial invariants. |
| E22 | PASS | A blind two-term search recovered P^2 - 4πχA with coefficient error below 1e-10. |
| E23 | PASS | Bounded search generated explicit counterexamples to four overstrong invariant/correspondence claims. |
| E24 | PASS | Across 1,252 graph-atlas objects, chi/Betti collided heavily; richer relational signatures progressively resolved them; exact network chain controls carried over. |
| E25 | PASS | Latest successful remote v0.9 graph artifact: 2,250 nodes / 23,338 edges; 24 equivalence components, 4 cycles, 0 identity/hash conflicts; all 16 audit gates passed. |

## Cross-experiment conclusions

- Individual invariants are aggressively lossy, but small structured probe families can become separating on bounded classes.
- Probe redundancy can be posed as an exact multi-cover/error-erasure problem.
- State identification and correspondence validation are different problems; a valid chain map is not by itself a semantic-equivalence certificate.
- Induced homology action, Lefschetz/degree information, cross-view commutative diagrams, and provenance each catch failure classes invisible to coarser layers.
- Applicability refusal must remain a first-class verdict; theorem hypotheses cannot be replaced by numerical failure.
- Exact algebraic gates should remain exact because ordinary floating rank heuristics can change algebraic conclusions on ill-conditioned inputs.
- Möbius inversion, Euler-Radon inversion, nerve reconstruction, and restricted-Yoneda probes provide rigorous versions of the same broad pattern: individually lossy local observations can collectively recover global structure.
- Counterexample search and conservation-law discovery are viable computational services for MAPEOGEO, not only post-hoc analysis tools.

## Recommended MAPEOGEO contract changes

- Make probe-family null-space/separation metadata explicit in executable evidence.
- Add erasure coverage / redundancy certificates for finite probe families.
- Split correspondence evidence into: chain-map validity, induced homology action, homotopy/degree/Lefschetz scope, and exact/provenance scope.
- Require EO/GEO semantic promotion to include a cross-view commutative-diagram contract when an explicit morphism is available.
- Keep exact GF(2)/Q algebraic validity separate from floating geometric tolerances.
- Treat NOT_APPLICABLE as a nonfailure result and record which hypothesis failed.
- Add bounded counterexample search before promoting new invariant/equivalence claims.
- Add invariant-discovery search as a candidate generator only; promote discovered laws only after independent validation/formalization.
- Extend graph consistency audits from identity/hash/certificate path checks to executable morphism commutation as PCT map data becomes available.

## Global claim boundary

These are controlled finite or symbolic computational experiments. Several results are exact within their stated finite domains, but the campaign does not establish universal injectivity, universal minimal probe counts, arbitrary-shape reconstruction, or new general theorems beyond the established mathematics instantiated by the tests.
