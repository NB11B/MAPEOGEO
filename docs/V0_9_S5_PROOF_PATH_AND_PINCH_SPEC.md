# MAPEOGEO v0.9 — S5 Proof-Path + Pinch Audit

Copyright © 2026 NB11B. All rights reserved. See `LICENSE.md`.

## Governing goal

The architecture is frozen. Coverage changes; the machine does not.

```text
source declaration
  -> EO / GEO candidate views
  -> executable test (optional, scoped)
  -> FORMAL statement
  -> kernel check
  -> graph promotion or refusal
```

Mathematics enters only as source-bound objects. Prose is not a graph truth layer.

## Intake invariant

Every source object must carry, or explicitly refuse, four fields:

1. **Identity** — source locator plus frozen statement hash.
2. **Deps** — explicit source references only; unresolved reference rate remains visible.
3. **Views** — EO and/or GEO candidates; candidate views never imply truth.
4. **Test** — executable contract, kernel certificate, or explicit `UNTESTED`.

`UNTESTED` is legal. Silent confidence is not.

The semantic states remain distinct for the entire expansion:

- `DUAL_CANDIDATE`
- `EQUIVALENT_TO`
- `SAME_SEMANTICS`
- `KERNEL_VERIFIED`

## S5 question

v0.8 kernel-verified four source-bound endpoints. v0.9 asks whether the cited support structure can itself become a checked path rather than leaving only verified endpoints.

A proof path has three independent evidence channels:

- **source-reference evidence** — which source node explicitly cites which support node;
- **formal-node evidence** — a source-bound Lean statement with a frozen source hash and declared formal scope;
- **kernel evidence** — successful Lean checking of every formal node admitted to the checked path.

These channels are never collapsed. Lean verifies mathematics; it does not certify that a source author cited a particular theorem. Source-reference provenance is checked separately.

### Verified-frontier rule

S5 traversal may stop at a cited support node once that support node has its own source-bound kernel certificate. We do not recursively reproduce every historical human proof down to foundations merely to call the parent path checked. A downstream source proof may be audited later as its own path.

Therefore a `KERNEL_ACCEPTED` S5 path means:

1. every path vertex required by the frozen S5 path scope has a source identity/hash;
2. every source-reference edge in that path scope is explicitly frozen as provenance evidence;
3. every mathematical claim at the verified frontier has a Lean kernel certificate at its declared scope;
4. every gap or correction encountered during traversal remains visible as a wound.

It does **not** mean the Lean proof term has been forced to reproduce the source author's proof syntax.

## Frozen v0.9 rank-nullity path

The S5 audit scope for Gallier–Quaintance Theorem 6.16 is frozen as:

```text
Theorem 6.16
  -> Proposition 6.15
     -> Proposition 6.11
        -> Proposition 3.15
        -> Theorem 3.7
           -> Lemma 3.6
  -> Proposition 6.7
```

The exact node IDs, hashes, edge set, Lean declarations, and formal scopes are frozen in `formal/proof_paths_v0_9.json`.

### Pre-registered dependency wound

The accepted v0.8 graph contains a resolved edge

```text
Proposition 6.11 -> Proposition 3.18
```

but direct source-reference audit identifies the cited support as **Proposition 3.15**. v0.9 must not silently overwrite history. It must:

- retain the legacy edge in the derived graph;
- mark that edge `REJECTED_REFERENCE_MISMATCH` for v0.9 path use;
- add the corrected source-reference edge to Proposition 3.15;
- create an explicit `WOUND` record documenting the repair.

This correction is part of the result, not a parser detail to hide.

## Four v0.8 targets under S5

- **Theorem 6.16** — audited multi-node proof path above; target outcome may be `KERNEL_ACCEPTED`, `KERNEL_ACCEPTED_WITH_REPAIRED_WOUND`, or fail-closed.
- **Definition 44.6** — definition/formal leaf; no cited proof path is required for S5. Record `LEAF_NO_CITED_PROOF_PATH`.
- **Theorem 47.9** — the accepted source graph contains no parsed proof block or explicit proof-reference path. Record `WOUND_NO_PARSED_SOURCE_PROOF_PATH`; do not invent dependencies.
- **Definition 53.4** — definition/formal leaf; record `LEAF_NO_CITED_PROOF_PATH`.

## Support formalizations

The S5 support frontier is formalized conservatively. Each Lean theorem is bound to the source node hash and carries an explicit scope. A scoped support theorem does not promote the entire source declaration beyond that scope.

The planned support scopes are:

- Lemma 3.6 — linear-independence insertion contract;
- Theorem 3.7 — basis-extension-between-independent-and-spanning-sets contract;
- Proposition 3.15 — basis-determines-a-unique-linear-map contract;
- Proposition 6.11 — linear retraction/section existence contract;
- Proposition 6.7 — finite external direct-sum/product finrank additivity contract;
- Proposition 6.15 — section-induced kernel/range complement contract.

## Pinch quartet

After adding the S5 certificates, choose the next four **uncertified** source declarations by the frozen fused score

```text
pinch_score(v) = normalized_dependency_betweenness(v) * view_shear(v)
```

with

```text
view_shear(v) = |#EO_direct_families - #GEO_direct_families|
                / (#EO_direct_families + #GEO_direct_families)
```

and `view_shear = 0` when both counts are zero.

The dependency graph uses source `DEPENDS_ON` edges after rejecting any edge explicitly marked as a v0.9 source-reference mismatch. Nodes already carrying a formal/kernel certificate are excluded. Ties are resolved deterministically by source ID.

This ranking is a routing rule, not a truth score.

## Batch metrics

The v0.9 artifact must emit the same intake ledger fields used for future strata:

1. source declarations added / source proof blocks added / unresolved-reference rate;
2. EO-direct / GEO-direct / dual-direct coverage;
3. held-out dual-union dependency recall, with fallback retained;
4. certificates added by class;
5. kernel-accepted proof paths, not merely verified nodes.

For v0.9, source intake counts may be zero because this stage promotes existing graph objects rather than importing a new corpus. Carry-forward corpus metrics must be explicitly labeled as carry-forward, not newly measured ingestion.

## Fail-closed gates

v0.9 passes only if:

- every frozen support source ID and statement hash matches the regenerated graph;
- every frozen support Lean declaration is present and checks under pinned Lean/Mathlib;
- no `sorry`, `admit`, custom `axiom`, or `unsafe` declaration exists in the S5 formalization file;
- all six support frontier claims receive scoped kernel certificates;
- the rank-nullity S5 path is emitted with every frozen edge accounted for;
- the 6.11 dependency mismatch is recorded as a wound and corrected without deleting the historical edge;
- Theorem 47.9 remains a wound rather than receiving invented proof dependencies;
- definitions 44.6 and 53.4 are recorded as S5 leaves, not synthetic proof paths;
- the post-S5 pinch quartet is deterministic and excludes newly certified support nodes;
- graph IDs remain unique and all edge endpoints exist;
- source prose/page images are not persisted.

## Claim boundary

A PASS establishes an S5 mechanism on the existing source corpus and one checked proof-path scope. It does not establish whole-corpus proof-path reconstruction, universal dependency correctness, whole-corpus autoformalization, or complete formalization of every support declaration's full source statement.
