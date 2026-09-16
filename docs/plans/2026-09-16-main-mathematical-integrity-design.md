# Main Mathematical-Integrity Repair Design

**Branch:** `agent/main-math-rigor-v0-20`
**Frozen base:** `54c9af6348e52380c229fd6b1d527136a2bbe01c`
**Integration rule:** this branch remains unmerged until independent review.

## Purpose

This repair removes claims that are not supported by their source identities or by executable mathematics. It does not rewrite the sealed v0.11 checkpoint. Historical defects are retained as rejected wounds or amendments with their original identity and a corrected identity.

## Integrity invariants

1. A declaration is identified by source/corpus, declaration kind and number, and a 64-character lowercase hexadecimal statement SHA-256.
2. `DUAL_CANDIDATE`, `SCOPED_OVERLAP`, `SAME_SEMANTICS`, and `KERNEL_VERIFIED` are distinct states. A detector hit or shared canonical parent cannot promote an edge.
3. A proof-eligible edge has existing endpoints, an allowed direction, a non-wound status, and evidence bound to both endpoint identities. Wounds remain visible but never establish grounding.
4. Empty evidence, missing bindings, unknown verifier classes, malformed hashes, NaN/infinity, and verifier exceptions fail closed.
5. A finite numerical experiment is described as finite numerical evidence. It does not establish a universal theorem.
6. Historical files remain immutable when sealed. Corrections are additive records containing old/new hashes, reason, status, and supersession policy.

## v0.19 corrections

- Remove the Axler `Definition 5.8` eigenvector declaration from the Liouville/FTA `SAME_SEMANTICS` alignment. Add a rejected historical-alignment wound naming the exact old edge and source hash.
- Correct the four curated complex-analysis statements: higher Cauchy derivatives, Schwarz equality, Harnack principle, and Weierstrass factorization zeros. Preserve each prior hash in the amendment registry and issue a new statement identity.
- Correct the Dolbeault structural reference from `DEFINITION:2.2` to `THEOREM:2.2` and reject every dangling structural reference.
- Make bridge identity include the canonical contract and relation type. Conflicting relations for the same endpoint pair are rejected, not silently collapsed by iteration order.
- Validate every alignment source against the graph node registry, expected corpus, declaration identity, source ID, and statement hash before an edge is emitted.

## Foundation executable evidence

The eight existing group booleans are replaced by typed evidence records. Each record contains a contract ID/version, exact subject declaration IDs and hashes, input-domain statement, witness cases, verifier ID, result, and evidence digest. Only named subjects receive executable evidence. The remaining declarations stay `UNVERIFIED`; a passing representative contract does not imply that all 176 curated declarations were proved.

The mathematical helpers are tightened as follows:

- Boolean implication checks truth tables rather than trusting an implication flag.
- Relation predicates reject pairs outside the declared domain.
- Inverse checks require nonempty finite domains, finite real values, both compositions, and explicit domain/codomain samples.
- Dedekind comparisons use exact integer arithmetic on `p^2` and `2q^2`, require integral `p,q`, and reject `q <= 0` and equality.
- Sequence checks are renamed as finite-window checks and reject empty windows, invalid epsilon/thresholds, and nonfinite terms.
- Vector operations require equal, nonzero finite dimensions.
- Calculus checks cover power, product, and chain rules; the `n=0,x=0` power rule is handled exactly. Numerical checks carry their finite scope and error tolerance.

## Grounding metrics

The dashboard reports two channels:

- **raw topology reachability** over declared graph connectivity; and
- **proof-eligible grounding** over an allowlist of verified directional edges.

`HAS_WOUND`, rejected/superseded edges, unverified `RELATED_TO`, dangling edges, and reverse dependency traversal cannot establish proof-eligible grounding. Counts are partitioned by the node registry, including Ahlfors/Krantz declarations, rather than string-prefix guesses.

The report must show numerators and denominators and may report less than 100%. No threshold is changed merely to preserve a historical headline.

## Evidence and reproducibility

Generated JSON is canonical (`sort_keys`, stable separators, trailing newline). Gzip artifacts use deterministic metadata and atomic replacement. Intake functions accept explicit output/evidence paths, so tests never rewrite tracked evidence. Reports bind the input graph digest, alignment digest, declaration-manifest digests, contract-registry digest, and producing commit.

## Acceptance

The branch is acceptable only if adversarial tests demonstrate rejection of the known false alignment, malformed hashes, dangling references, edge collisions, vacuous/empty contracts, forged contract bindings, nonfinite values, vector dimension mismatch, exact Dedekind near-boundary cases, and wound-only reachability. The full main regression suite and a clean reconstruction must then pass without modifying the sealed v0.11 graph.
