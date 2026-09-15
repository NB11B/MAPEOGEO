# MAPEOGEO v0.11 — Pinch-Driven Mathematics Intake Design

Copyright © 2026 NB11B. All rights reserved. See `LICENSE.md`.

## Status

Design specification for the first deliberate mathematics-growth stage after v0.9 S5 proof-path validation.

This stage changes **coverage, not architecture**. It does not redefine MAPEOGEO, EO, GEO, PCT, FORMAL, Lean verification, or existing promotion semantics.

The governing objective remains:

> Build one source-grounded mathematical graph in which provenance, proof topology, EO operator structure, GEO relational structure, executable evidence, formal statements, and trusted proof verification are interoperable layers over the same mathematics.

## Relationship to v0.10 PCT

Two lanes proceed in parallel:

```text
Lane A — v0.10 PCT
  reusable S3 executable-evidence subsystem

Lane B — v0.11 Mathematics Intake
  source-bound mathematical growth through existing S0-S5 gates
```

v0.11 does **not** wait for PCT to finish.

PCT is an optional computational tester for mathematical objects whose declared contract is naturally expressed through chain complexes, topology, geometric probing, reconstruction, or correspondence maps. PCT is not a mandatory representation layer and cannot write `KERNEL_VERIFIED`.

If a v0.11 node has no justified PCT contract, it may proceed from source/EO/GEO directly to an executable contract, `UNTESTED`, or FORMAL/Lean as appropriate.

## Intake invariant

Every admitted source-bound mathematical object must carry four explicit fields, or it does not enter the accepted intake batch:

1. **Identity** — source locator + frozen statement SHA-256.
2. **Deps** — explicit source references only; unresolved references remain visible and measured.
3. **Views** — EO and/or GEO candidate representations; candidates are not truth claims.
4. **Test** — one of:
   - scoped executable contract,
   - scoped PCT contract,
   - kernel certificate,
   - explicit `UNTESTED`.

`UNTESTED` is a legal state. Silent confidence is not.

## Promotion states remain distinct

The following states and edge meanings remain separate for the entire project:

```text
DUAL_CANDIDATE
EQUIVALENT_TO
SAME_SEMANTICS
KERNEL_VERIFIED
KERNEL_ACCEPTED_PATH
WOUND
UNTESTED
```

No stage may collapse these into a single confidence score.

A node may skip states when the corresponding evidence class is not applicable. A Lean proof does not retroactively create a GEO view. An executable equality on a finite domain does not become theorem-wide `SAME_SEMANTICS`. Equal invariants do not create semantic identity.

## Frozen v0.11 intake quartet

The next batch is selected by the accepted v0.9 pinch audit, not by page order or manual preference.

| Priority | Source node | Statement SHA-256 | v0.9 direct state | Dependency betweenness | View shear | Pinch score |
|---:|---|---|---|---:|---:|---:|
| 1 | `srcdecl:proposition:3_14` | `6e09e18756aefdaf8cdd2c03aca61548d1126fb3d30d70b49c58359f37c64b8e` | `EO_ONLY_DIRECT` | 0.0001359198498658815 | 1.0 | 0.0001359198498658815 |
| 2 | `srcdecl:proposition:3_13` | `0eef6ce3b699ddef7c209eb28b500b75aab07d9e540b7746b631f8db653addac` | `EO_ONLY_DIRECT` | 0.00007341855344161069 | 1.0 | 0.00007341855344161069 |
| 3 | `srcdecl:theorem:27_10` | `d205d7c5313b841e6afafc9d619fa059dfe50a2f6c11a48ca2cff466cc84d4fa` | `DUAL_DIRECT` | 0.00010480566736646284 | 0.5 | 0.00005240283368323142 |
| 4 | `srcdecl:proposition:4_4` | `37e5dc6afdbd3d026c4f7ef71c3531fc74eaeb04bf21ed45c4a9add39fcb6ecf` | `EO_ONLY_DIRECT` | 0.00004612541089826099 | 1.0 | 0.00004612541089826099 |

These identities are immutable for the stage. If regeneration does not produce the same IDs and hashes, v0.11 fails closed before mathematical promotion begins.

## Central scientific question

v0.11 asks:

> When the graph chooses its own highest-value unresolved interface nodes, can those nodes be promoted through scoped executable and formal verification without silently manufacturing missing EO/GEO structure?

The experiment is therefore not "can Lean prove four statements?"

It measures whether formalization and executable testing legitimately change the state of the graph.

## Per-node intake procedure

Each of the four nodes executes the same state machine:

```text
frozen source identity/hash
        ↓
explicit dependency audit
        ↓
existing EO/GEO candidate views
        ↓
S3 tester selection
        ↓
executable contract | PCT contract | UNTESTED
        ↓
FORMAL candidate scope
        ↓
Lean kernel check
        ↓
promotion | refusal | wound
```

### Identity gate

The source node must exist and its independently regenerated statement hash must equal the frozen v0.9 hash.

No formalization may be attached to a different source statement under the same source ID.

### Dependency gate

Only explicit source references are admitted as source proof dependencies.

Implicit mathematical prerequisites may be represented separately as formal/library dependencies, but must not be rewritten as source citations.

Resolution mismatches are emitted as `WOUND` records rather than repaired invisibly.

### View gate

The v0.9 independent EO/GEO detector outputs are the starting state.

Three nodes begin `EO_ONLY_DIRECT`; one begins `DUAL_DIRECT`.

Formalization may reveal mathematically useful additional structure, but any new EO or GEO representation must be introduced as a newly justified candidate with its own evidence and provenance. Formal success alone cannot change detector history.

### S3 tester gate

Tester selection is explicit per node:

- use an exact executable contract where a finite/algebraic identity can be scoped without overclaim;
- use PCT only when its applicability contract is genuinely satisfied;
- use a numerical residual-bounded contract only when the object is intrinsically numerical;
- otherwise record `UNTESTED`.

`UNTESTED` does not block S4 formalization.

### S4 FORMAL gate

Each node receives a scoped Lean statement bound to the frozen source identity/hash.

Requirements:

- pinned repository toolchain `leanprover/lean4:v4.33.1`;
- pinned Mathlib `v4.33.1`;
- no `sorry`, `admit`, custom `axiom`, or `unsafe` declaration;
- normal Lean build succeeds;
- `leanchecker` succeeds in CI;
- local Windows build is expected to reproduce the same formal declarations under the same pins.

Only the kernel-verifier path may create a certificate with class `KERNEL_VERIFIED`.

## Three testers remain independent

The project retains three non-collapsed testers:

1. **Locality tester** — source/page/proof-topology prior. Useful for navigation; never proof.
2. **Computational tester** — EO/GEO/PCT executable contract on an explicitly declared domain. May justify scoped `EQUIVALENT_TO` or `SAME_SEMANTICS` only under its frozen contract.
3. **Kernel tester** — Lean statement on the frozen source binding. Only this writes `KERNEL_VERIFIED`.

Every certificate must state:

```text
tester
scope/domain
applicability
verdict
what was not tested
source hash
code/toolchain provenance
```

## Required v0.11 outputs

The accepted run must produce, at minimum:

```text
pinch_v0_11_manifest.json
pinch_v0_11_results.json
pinch_v0_11_certificates.json
pinch_v0_11_wounds.json
mapeogeo_v0_11_graph.json.gz
V0_11_SUMMARY.md
```

Repository acceptance records store hashes and compact summaries; large generated graph artifacts remain CI artifacts unless small enough and already consistent with repository artifact policy.

## Batch metrics

Every accepted intake batch reports the same five families of numbers:

1. declarations/proofs added and unresolved-reference rate;
2. EO-direct, GEO-direct, and dual-direct coverage;
3. held-out dependency recall of the dual-union routing filter, with fallback retained;
4. certificates added, separated by certificate class;
5. kernel-accepted paths, not just kernel-verified endpoint nodes.

Existing accepted metrics are carried forward as historical baselines and are not silently recomputed into more favorable values.

## v0.11 acceptance criteria

The batch is accepted only if all mandatory gates below pass:

### Identity and provenance

- all four source IDs are present;
- all four statement hashes match the frozen v0.9 values;
- no source prose or source page images are added to repository artifacts;
- all generated records preserve `LICENSE.md` / `THIRD_PARTY_NOTICES.md` boundaries.

### Mathematical state discipline

- all four nodes have explicit `Test` state, including `UNTESTED` where appropriate;
- no EO/GEO view is promoted solely because Lean formalization succeeded;
- no finite/numerical contract is reported beyond its domain;
- `EQUIVALENT_TO`, `SAME_SEMANTICS`, and `KERNEL_VERIFIED` remain distinct.

### Formal verification

- all four scoped FORMAL candidates are attempted;
- every successful Lean declaration has zero prohibited proof escape hatches;
- every accepted `KERNEL_VERIFIED` certificate is backed by Lean build success and CI `leanchecker` success;
- failed formalization leaves the source node in place without promotion and records the failure/wound.

### Graph integrity

- node IDs unique;
- edge IDs unique;
- all edge endpoints exist;
- source identity nodes remain distinct from canonical semantic objects and FORMAL representations;
- previous wounds remain visible.

### Scientific interpretation

The stage may legitimately finish with fewer than four kernel promotions.

A valid fail-closed refusal is preferable to a fabricated promotion.

The scientific result is reported as a state transition table, not a single success percentage.

## Cross-platform reproducibility

The local workstation now resolves the same pinned Lean/Mathlib stack as CI:

```text
Lean 4.33.1
Lake 5.0.0-src+819816b
Mathlib v4.33.1
```

v0.11 should therefore record both:

```text
LOCAL_WINDOWS_VERIFICATION
CI_LINUX_VERIFICATION
```

when both are available for the exact same commit and formal source files.

Cross-platform agreement strengthens reproducibility but does not create a stronger mathematical certificate class than kernel verification itself.

## Second-source gate

A second mathematical source is intentionally deferred until the pinch quartet completes v0.11 intake.

The second source begins at S0/S1 and does not enter as trusted mathematics by default.

Its first scientific purpose is cross-source semantic identity:

```text
source declaration A ──┐
                       ├──> canonical semantic object M
source declaration B ──┘
```

Source nodes retain independent provenance and independent statement hashes even when they express the same mathematical content.

A shared FORMAL node may be reused only when the declared formal scope genuinely covers both source-bound statements.

Mathlib remains a verifier/library dependency, not a source corpus.

## Growth metrics for "adding mathematics"

MAPEOGEO distinguishes at least three growth counts:

```text
N_source         source-bound declarations present
N_formal         source declarations with accepted FORMAL/kernel certificates
N_verified_path  source proof paths accepted as checked chains
```

A large increase in `N_source` without corresponding tested/formal state is not reported as equivalent mathematical growth.

The long-run coverage objective is whole-corpus autoformalization, but the method remains pinch-driven, fail-closed intake.

## Non-goals

v0.11 does not attempt:

- mass ingestion of a new corpus;
- automatic whole-book theorem proving;
- universal EO closure;
- universal GEO closure;
- mandatory PCT representation for every object;
- replacement of Lean by PCT or EO/GEO;
- conversion of implicit prerequisites into fake source citations;
- elimination of `UNTESTED` states;
- exact-safe pruning from the current dual-union routing filter.

## Branching and integration

Development is isolated from PCT:

```text
main
├── agent/pct-computational-architecture   # v0.10 PCT
└── agent/math-intake-v0-11                # v0.11 mathematics intake
```

The branches may merge independently once their own acceptance gates pass.

If PCT v0.10 is accepted before v0.11 completes, v0.11 may consume its stable public executable-contract interface through a visible merge/rebase and preregistration amendment. No v0.11 scientific threshold or source binding may be changed after observing v0.11 results.

## Claim boundary

A successful v0.11 would establish that graph-selected mathematical pinch nodes can be processed through the same source-bound, fail-closed intake law already demonstrated on earlier hand-selected nodes, while preserving detector history, evidence scope, wounds, and kernel-verifier authority.

It would not establish that every mathematical declaration is formalizable automatically or that EO, GEO, or PCT are complete representations of mathematics.
