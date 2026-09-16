# Foundation Mathematical Amendment v0.20

This amendment corrects the active in-memory foundation declaration projection. It does not rewrite sealed historical graphs, evidence files, or alignment artifacts.

## Exact amendment boundary

The machine-readable registry at `formal/foundation_mathematical_amendments_v0_20.json` contains the complete 176-row historical identity registry and 84 exact declaration identity amendments. Each amendment binds the old and new label, declaration type, statement SHA-256, structural references, a reason, and a canonical amendment digest.

The active loader binds the complete historical table to its canonical digest and exact source commit identity. It fails closed if history is rewritten, a changed row is absent, an unchanged row is falsely listed, an old or new identity differs, an amendment ID is noncanonical, a reason is missing, or an amendment digest is forged.

These are statement and metadata corrections, not proof certificates. Corrected declarations retain `ACTIVE_STATEMENT_AMENDMENT_UNVERIFIED`; they do not become executable-verified or kernel-verified merely because their wording is repaired.

## Mathematical corrections

- Logic now states its classical bivalent valuation scope and identifies the classical steps in contraposition, reductio, double-negation elimination, and quantifier negation. Excluded middle is an axiom schema distinct from noncontradiction.
- Set theory treats membership as primitive and makes Extensionality, Empty Set, Pairing, Union, Separation, Power Set, and set-sized Choice assumptions explicit. Operations now state their existence domains, fixed universes, and nonempty-index requirements.
- Relations explicitly define the equivalence relation induced by a partition.
- Number-system constructions state the Peano/order framework, quotient operations, total divisibility, Archimedean density dependency, real existence versus rational nonexistence of `sqrt(2)`, exact completeness/categoricity scope, cut and Cauchy operations, nonnegative complex modulus, and the trigonometric dependency of polar form.
- Algebra, sequences, geometry, trigonometry, and calculus now state the missing structure, zero-remainder, index, domain, regularity, endpoint, integrability, radian, and nondegeneracy hypotheses identified by the v0.20 audit.

The existing 176 declaration identities and downstream source counts are preserved. Missing foundations were made explicit in their corresponding existing nodes rather than silently changing the corpus cardinality.

## Reference-edge policy

`structural_refs` now emit typed `STRUCTURAL_REFERENCE` edges with `UNVERIFIED_CANDIDATE` status. A curator-authored reference is not automatically a `PROOF_DEPENDENCY`.

`PROOF_DEPENDENCY` is permitted in the proof-eligible channel only when the edge is present in the closed registry and its evidence digest binds the exact edge type, direction, endpoint identities, and contract digest. Unregistered, self-asserted, stale-endpoint, or malformed proof edges remain ineligible.

## Helper scope

Public numerical helpers are sample or residual checks only. The amendment rejects malformed domains, removes the convergence-verdict alias, validates claimed derivative callbacks independently at sampled points, and checks the antiderivative obligation at interior samples before an FTC quadrature comparison. These checks still are not universal theorem proofs.

## Evidence status

| Channel | Active result |
|---|---:|
| Foundation declarations | 176 |
| Executable declaration evidence | 1 / 176 |
| Kernel-verified foundation declarations | 0 / 176 |

The sole executable declaration evidence remains the exhaustive four-row Boolean De Morgan check. No wording correction, numerical check, structural reference, or amendment digest increases that count.
