# MAPEOGEO PCT Computational Evidence Architecture — Design

Copyright © 2026 NB11B. All rights reserved. See `LICENSE.md`.

## Status

Design specification for the next executable-evidence subsystem. This document does not promote any mathematical claim by itself and does not alter the existing meanings of `DUAL_CANDIDATE`, `EQUIVALENT_TO`, `SAME_SEMANTICS`, or `KERNEL_VERIFIED`.

Working subsystem name: **Probe–Chain Transform (PCT)**. The name is descriptive. The implementation must not claim that the underlying mathematical ingredients are novel; it composes established ideas from chain complexes, homology, persistence, integral geometry, geometric probing, and reconstruction into a MAPEOGEO evidence architecture.

## Governing goal

MAPEOGEO already separates source provenance, EO operator structure, GEO relational geometry, executable certificates, FORMAL representations, and kernel verification. PCT adds a reusable executable-evidence machine between EO/GEO and FORMAL.

```text
source / mathematical object
        |
        +--> EO representation --------+
        |                              |
        +--> GEO representation -------+--> PCT executable evidence
                                           |
                                           +--> evidence graph / certificates
                                           |
                                           +--> FORMAL candidate scope
                                                    |
                                                    +--> kernel verification
```

PCT answers a narrower question than FORMAL:

> Does a declared representation, transformation, probe family, or reconstruction satisfy its preregistered executable mathematical contract?

FORMAL remains responsible for proof-assistant statements and trusted kernel verification. A PCT `PASS` is executable evidence, not proof-kernel acceptance.

## Design principles

1. **Fail closed.** A theorem-backed test is never counted as PASS when its applicability conditions are unknown or false.
2. **Exact mathematics stays exact.** Integer/rational/finite-field identities are checked exactly wherever practical. Floating tolerances are used only for genuinely numerical geometry.
3. **Object state and transformation state are separate.** Equal invariants do not imply a valid correspondence.
4. **Maps are first-class evidence.** PCT stores not only observations but the maps connecting observations.
5. **Loss is explicit.** Euler characteristic, Betti vectors, persistence, and scalar geometry are projections of a richer chain-valued representation.
6. **Provenance survives cancellation.** The canonical object is the chain complex and its maps; optional signed-incidence ledgers retain which generators participated in cancellations.
7. **Applicability is data.** `NOT_APPLICABLE` is a valid scientific result and is distinct from `FAIL`.
8. **Engine validity and scientific outcome are separate.** A valid experiment may reject the hypothesis.
9. **No silent semantic promotion.** PCT evidence may support a graph promotion only through an explicit contract; it never upgrades a node merely because an invariant matches.
10. **Determinism before optimization.** CPU reference behavior is authoritative for v0.10. Acceleration may be added later without changing the scientific contracts.

## Scope

The first implementation is a Python reference subsystem inside MAPEOGEO. It must support analytically controlled 2-D fixtures and the interfaces required to extend to 3-D, graphs, meshes, voxels, and other relational objects later.

The first stage does **not** attempt universal topology, arbitrary CAD robustness, whole-corpus application, GPU acceleration, automatic Lean theorem generation, or integer-homology torsion recovery.

## Mathematical core

For an object `X`, a probe state is

```text
alpha = (probe_shape, scale, pose, direction, threshold, observation_operator, coefficient_field, equivalence_contract)
```

The probed object is conceptually

```text
Y_alpha = Observe(Transform(X, alpha), alpha)
```

with the canonical geometric specialization

```text
Y_alpha = (X ⊕ sL) ∩ Q_p
```

when Minkowski dilation and intersection probes are applicable.

PCT assigns a chain complex

```text
T_X(alpha) = C_*(Y_alpha; F)
```

and, when two probe states are related, a map

```text
F_alpha_beta : C_*(Y_alpha) -> C_*(Y_beta).
```

The full computational object is therefore not a dense tensor of scalar measurements but a parameter graph:

```text
PCT(X) = ({C_alpha}, {d_alpha}, {F_alpha_beta}).
```

Nodes hold observation states. Edges hold declared or induced correspondences.

Derived projections include:

```text
chain complex -> homology -> Betti data -> Euler characteristic
              -> persistence along ordered parameter paths
              -> geometric valuations where applicable
              -> reconstruction / consistency residuals
```

## Repository integration

PCT is a first-class MAPEOGEO subsystem, not a replacement for MAP, EO, GEO, or FORMAL.

Proposed source layout:

```text
mapeogeo/
  pct/
    __init__.py
    contracts.py
    models.py
    adapters/
    probes/
    cell/
    chain/
    topology/
    persistence/
    maps/
    geometry/
    reconstruction/
    validation/
    artifacts/

scripts/
  pct_v0_10.py
  validate_pct_v0_10.py

tests/
  pct/
    unit/
    contracts/
    controls/
    adversarial/

evidence/
  v0_10_pct_preregistration.json
  v0_10_pct_acceptance_manifest.json   # created only after an accepted run

docs/
  V0_10_PCT_SPEC.md                    # scientific preregistration derived from this design
  V0_10_PCT_REPORT.md                  # created only after execution

.github/workflows/
  pct-v0-10.yml
```

The implementation plan may adjust package naming to fit repository conventions discovered during coding, but the interfaces and evidence contracts below are frozen by this design unless amended visibly.

## Existing graph conventions

PCT must preserve the current MAPEOGEO graph model. Existing node types such as `OBJECT`, `STATEMENT`, `OPERATOR`, `PROOF_STEP`, `REPRESENTATION`, `CERTIFICATE`, and `SOURCE` remain valid. Existing semantics such as `REPRESENTS`, `SAME_SEMANTICS`, `EQUIVALENT_TO`, `VERIFIED_BY`, `DEPENDS_ON`, and `COMPOSES_WITH` are not redefined.

PCT adds evidence-specific records only where needed. Preferred additions are:

```text
PCT_RUN
PCT_OBSERVATION
PCT_MAP
PCT_EVENT
WOUND
```

and certificate classes such as:

```text
EXECUTABLE_PCT_VALIDITY
EXECUTABLE_PCT_SCIENTIFIC_RESULT
EXECUTABLE_PCT_RECONSTRUCTION
```

These additions must be introduced through the same graph-integrity rules already used by MAPEOGEO: unique IDs, existing endpoints, explicit scope, explicit provenance, and no semantic promotion by naming alone.

## Core data models

### ObjectRecord

Required fields:

```text
object_id
semantic_id
adapter_type
source_hash
ambient_dimension
representation_kind
orientation_policy
equivalence_contract
metadata
```

### ProbeState

Required fields:

```text
probe_id
probe_family
parameters
scale
pose
observation_operator
coefficient_backend
applicability_contract
```

### ChainComplexRecord

Required fields:

```text
observation_id
generators_by_degree
boundary_operators
coefficient_backend
orientation_metadata
exactness_class
```

### ChainMapRecord

Required fields:

```text
map_id
source_observation_id
target_observation_id
maps_by_degree
construction_method
exact_or_numeric
residuals
```

### EventRecord

Required fields:

```text
event_id
parameter_location
event_type
degree
source_generators
target_generators
signed_weight
provenance
```

Event records support persistence births/deaths, critical topology changes, explicit cancellation provenance, and correspondence failures.

### VerdictRecord

Required fields:

```text
check_id
applicability
verdict
measured
expected
tolerance_or_exact_rule
provenance
```

Allowed verdicts:

```text
PASS
FAIL
NOT_APPLICABLE
INVALID
ERROR
INCONCLUSIVE
```

`NOT_APPLICABLE` is never silently converted to PASS. `ERROR` is never interpreted scientifically.

## Exact and numerical backends

The authoritative v0.10 chain/homology backends are fields:

- `GF(2)` for fast orientation-independent topology controls;
- `Q` for oriented exact calculations that require signs, induced maps, degrees, or exact rational rank.

Boundary incidence may be serialized with integer coefficients, but v0.10 does not claim integral homology or torsion detection. A later stage may add a `Z`/Smith-normal-form backend under a separate contract.

The implementation may use established sparse linear-algebra libraries, but exact contract checks must not be reduced to approximate floating comparisons.

Geometric calculations use double precision by default and report normalized residuals plus the tolerance used. Every numerical threshold must be present in the frozen experiment manifest.

## Canonical validity gates

Every PCT scientific run executes validity gates before scientific hypothesis gates.

### V0 — Determinism

Same input hashes, manifest, code revision, and seed must reproduce all exact results and numerically equivalent floating results within frozen tolerances.

### V1 — Chain validity

For every chain complex:

```text
d_{k-1} d_k = 0
```

exactly for exact backends.

### V2 — Euler–Poincaré

For finite complexes:

```text
sum (-1)^k dim C_k = sum (-1)^k dim H_k.
```

This is an exact integer gate.

### V3 — Chain-map validity

For every declared correspondence:

```text
d_Y F_k = F_{k-1} d_X.
```

Exact maps require exact equality. Numerically inferred maps use a preregistered normalized residual.

### V4 — Filtration / order validity

Every claimed inclusion, nesting, or ordered probe path must be true under the adapter's contract.

### V5 — Declared representation invariance

Subdivision, relabeling, rigid transform, or other transformations declared equivalent by the manifest must preserve the invariants required by that equivalence contract.

### V6 — Analytic controls

Known analytic fixtures must reproduce their expected topology and geometry.

### V7 — Applicability

Every theorem-backed channel records and verifies the hypotheses required for its use. Tube/Steiner, convex mixed-volume, Crofton, Gauss–Bonnet, and related formulas are tested only in their declared admissible regimes.

### V8 — Provenance completeness

Every reported scalar, map, reconstruction, event, and verdict must trace to object hash, probe state, code revision, coefficient backend, and parameters.

A mandatory validity-gate failure suppresses downstream scientific PASS claims. Results may still be emitted for debugging, but they are marked invalid.

## Scientific test matrix

The first PCT stage tests whether richer relational structure earns its cost over collapsed invariants.

### S1 — Separation

Can PCT distinguish objects that collide under Euler characteristic or Betti summaries?

### S2 — Equivalence preservation

Do remeshings, subdivisions, relabelings, and allowed rigid transformations remain equivalent under the frozen equivalence contract?

### S3 — Correspondence detection

Can a deliberately corrupted map be detected by the chain-map residual while state-level invariants remain unchanged?

### S4 — Reconstruction

Can selected probe families reconstruct benchmark objects up to the manifest's declared equivalence?

### S5 — Probe ablation

How many probes can be removed before separation, stability, or reconstruction fails?

### S6 — Noise stability

How rapidly do geometric and reconstruction errors grow under controlled perturbations?

### S7 — Erasure robustness

How many missing probe observations can be tolerated before the declared reconstruction criterion fails?

### S8 — Corruption detection and localization

Can an inconsistent observation or correspondence be detected and, when possible, localized to the responsible probe/map/event?

### S9 — Scale-event recovery

Are analytically known hole-closing and component-merging scales detected without inventing extra topological events?

### S10 — Transformation-history discrimination

Can equal endpoint states with different induced maps or orientation behavior be distinguished at the appropriate information layer?

## Baseline hierarchy

PCT must be compared against simpler representations, not only against failure.

Required baselines:

```text
B0 single Euler characteristic
B1 Betti vector
B2 persistence summary / barcode channel
B3 parameterized Euler-response field
B4 chain-valued PCT without map edges
B5 full chain-valued PCT with map edges and provenance
```

For fairness, B0-B5 are derived from the **same frozen objects and probe schedule** whenever the baseline is defined. The distinction is the amount of structure retained, not a more favorable set of probes for the richer model. Where a baseline intrinsically uses no parameterized probes (for example a single global Euler characteristic), that limitation is explicit in the result table rather than repaired after inspection.

The full architecture is scientifically justified only if B5 adds measurable capability on at least one preregistered task that the simpler baseline cannot solve under the same declared object/probe/equivalence contract, or if it materially improves preregistered fault localization or robustness.

If B3 or B2 solves all preregistered tasks with no material disadvantage, the claim must narrow accordingly.

## Initial control corpus

The first corpus is deliberately analytic and adversarial rather than large.

2-D fixtures include:

- filled disk / circle boundary;
- equal-area square and equilateral triangle, both filled and boundary-only;
- multiple subdivisions and vertex relabelings of the same loop;
- annulus with known inner radius and therefore known hole-closing offset;
- two separated disks/components with a known merger scale;
- one loop versus two disjoint loops where coarse Euler information collides but Betti structure differs;
- same homology with different geometry;
- valid orientation-preserving correspondence;
- orientation-reversing correspondence;
- valid subdivision chain map;
- deliberately corrupted subdivision map;
- a non-positive-reach / reentrant-corner case used specifically to verify applicability refusal rather than to force a tube-law result.

A later stage may add 3-D sphere, shell, torus, two components, bridge, and cavity controls. Those are not required for the first accepted PCT run unless added by explicit preregistration amendment before execution.

## Equivalence contracts

Every experiment declares what `same` means. Allowed initial contracts include:

```text
EXACT
RELABELING
SUBDIVISION
RIGID_MOTION_2D
RIGID_MOTION_AND_SCALE_2D
HOMEOMORPHISM_CONTROL
CHAIN_HOMOTOPY_CONTROL
```

These are not interchangeable. Reconstruction and loop residuals are scored only against the selected contract.

No run may report `same` without naming the equivalence contract.

## Geometry channels

Geometry channels are optional per test and never override topology.

The initial implementation may support:

```text
area
perimeter
Hausdorff distance
support-function samples
parallel-set area response
```

Tube-law, mixed-area, or Crofton-derived claims require their own applicability flags. Concave/singular cases may be valuable negative controls precisely because the regular formula is not applicable.

## Persistence channel

Persistence is computed only along a declared ordered parameter path or valid filtration. It records feature births/deaths and preserves more information than the Euler curve.

The engine must retain the pairing/event provenance needed to compare:

```text
persistence -> Betti curve -> Euler curve
```

without pretending that the reverse arrows are generally unique.

## Cancellation provenance

The canonical evidence is the exact chain complex and its maps. For debugging and fault localization, an oriented boundary operator may also be decomposed as

```text
D_k = D_k^+ - D_k^-.
```

This signed decomposition is basis/orientation dependent and must never be promoted as a representation-independent invariant. It is a provenance ledger showing which signed incidences produced a cancellation.

Persistent pairings and map-residual support should also be retained as provenance rather than collapsed into one scalar.

## Reconstruction interface

A reconstruction experiment receives a frozen subset of probe observations and emits:

```text
reconstruction object
reconstruction equivalence contract
geometric error metrics
topological comparison
consistency residual
used probes
unused / erased probes
```

A reconstruction is PASS only if every metric required by the manifest passes. A geometrically close result with incorrect topology is a failure when topology is part of the contract. A topologically correct result with excessive geometric error is likewise a failure when geometry is required.

The first implementation should favor deterministic reconstruction methods with analytic controls over learned reconstruction.

## Probe sufficiency and robustness

Once the full probe set establishes separation/reconstruction, PCT runs deterministic ablations.

The target is not the minimum probe count at any cost. A useful finite probe set must satisfy:

1. **separation** — inequivalent controls remain distinguishable;
2. **stability** — bounded perturbations yield bounded output error under preregistered thresholds;
3. **redundancy** — selected probe erasures do not immediately destroy the contract.

These measurements connect the transform architecture to frame/sampling ideas without assuming in advance that a particular finite frame theorem applies to every object class.

## Run manifest

Every run is frozen by a JSON manifest containing at minimum:

```text
run_id
stage
repository_commit
object hashes
probe definitions
probe schedule
equivalence contracts
coefficient backends
random seeds
numeric tolerances
applicability contracts
baseline definitions
validity gates
scientific gates
negative-control mutations
reconstruction criteria
artifact policy
```

No scientifically relevant threshold may be introduced after results are inspected. Amendments must be committed as visible preregistration amendments before the corresponding run.

## Atomic execution model

A scientific campaign executes as one sealed run:

```text
1. Validate manifest and input hashes.
2. Materialize control objects.
3. Generate all frozen probe states.
4. Build chain complexes and maps.
5. Compute derived topology / persistence / geometry.
6. Run V0-V8 validity gates.
7. If mandatory validity passes, run S1-S10 scientific tests.
8. Execute frozen negative controls, corruptions, and probe ablations.
9. Attempt reconstruction where preregistered.
10. Emit immutable artifacts.
11. Issue separate ENGINE_VALIDITY and SCIENTIFIC_RESULT verdicts.
```

Scientific code must not branch on whether an observed result is favorable.

## Artifact layout

A completed run artifact should be self-auditing:

```text
pct_run/
  manifest.json
  hashes.json
  objects/
  probes/
  complexes/
    generators/
    boundary_matrices/
  maps/
  homology/
  persistence/
  geometry/
  event_ledger/
  reconstruction/
  negative_controls/
  residuals/
  validity.json
  scientific_result.json
  summary.md
```

Nothing required to reproduce the verdict may exist only in console output.

Repository acceptance manifests should store hashes and result summaries, not unnecessarily large generated artifacts.

## MAPEOGEO graph emission

An accepted PCT run may emit graph records representing:

- the source mathematical object or existing semantic object;
- EO and GEO representations already in the graph;
- the scoped PCT executable contract;
- the PCT run/certificate;
- wounds or refused applicability;
- links to FORMAL candidates when a formalization scope is explicitly selected later.

A PCT certificate supports executable evidence only. It cannot create `KERNEL_VERIFIED`. `SAME_SEMANTICS` remains subject to the repository's explicit equivalence contract and must not be inferred from equal Euler/Betti data alone.

## First scientific hypothesis

The initial null hypothesis is intentionally strong:

> **H0:** The full parameterized chain/map representation provides no material identification, reconstruction, robustness, or fault-localization advantage over simpler collapsed invariant channels on the preregistered control corpus.

The alternative is:

> **H1:** Retaining parameterized chain structure and transition maps solves at least one preregistered task that simpler invariant channels cannot solve under the same declared object/probe/equivalence contract, while preserving required invariances and stability.

The architecture passes engineering validity independently of whether H1 is supported.

## Required negative controls

At minimum:

1. break one edge in a closed cycle;
2. corrupt one subdivision correspondence while preserving object-level Betti data;
3. reverse orientation where orientation is part of the contract;
4. relabel generators where relabeling is declared equivalent;
5. perturb geometry without changing topology;
6. trigger a known hole-closing scale;
7. trigger a known component-merging scale;
8. present a non-applicable singular case to a regular tube-law test and require `NOT_APPLICABLE`;
9. erase selected probes;
10. inject one inconsistent probe observation and require detection.

## Acceptance criteria for the first stage

### ENGINE_VALIDITY = PASS only if

- V0-V8 all pass or are explicitly allowed `NOT_APPLICABLE` by the preregistered manifest;
- exact checks remain exact;
- every negative control expected to invalidate a relation is detected;
- graph IDs are unique and endpoints valid;
- all emitted evidence is provenance-complete;
- run artifacts are deterministic under rerun;
- repository copyright / source-provenance policy is preserved.

### SCIENTIFIC_RESULT

The scientific result is reported separately as one of:

```text
H1_SUPPORTED
H1_NOT_SUPPORTED
INCONCLUSIVE
```

`H1_SUPPORTED` requires a preregistered B5 advantage on at least one capability test plus no mandatory invariance/stability failure.

The result must identify the lowest-complexity baseline that achieves each capability. No credit is given to B5 for tasks already solved equally well by a simpler baseline.

## Performance and implementation policy

The reference implementation prioritizes correctness and auditability over throughput.

- sparse matrices are preferred for chain operators;
- object/probe artifacts are generated deterministically;
- caches are content-addressed by input + probe + code contract where useful;
- concurrency is allowed only where it cannot change deterministic outputs;
- GPU/CUDA work is deferred until the CPU reference results are sealed;
- optimization must preserve serialized evidence semantics and pass the same control suite.

## Failure taxonomy

PCT distinguishes:

```text
MATHEMATICAL_CONTRACT_FAIL
CORRESPONDENCE_FAIL
RECONSTRUCTION_FAIL
STABILITY_FAIL
APPLICABILITY_REFUSAL
INPUT_INVALID
TOOLING_ERROR
ARTIFACT_INTEGRITY_FAIL
```

These classifications supplement, rather than replace, the verdict enum. A run may be valid while its scientific hypothesis fails.

## Claim boundary

A successful first PCT stage would establish a reusable, fail-closed executable evidence architecture on a controlled finite corpus. It would show which levels of representation are needed for separation, correspondence checking, reconstruction, and fault localization on those controls.

It would **not** establish universal invertibility of the proposed transform, universal topological reconstruction, whole-corpus applicability, a new theorem of integral geometry, a replacement for formal proof, or a claim that all MAPEOGEO objects admit the same probe family.

## Planned transition after approval

After this design is approved, implementation planning should decompose the work into test-driven increments while preserving the atomic scientific run as the acceptance target. The implementation plan should begin with the exact contracts and controlled fixtures, then add maps, persistence, scalar probe baselines, reconstruction, adversarial controls, artifact sealing, graph emission, and CI. No scientific run is accepted until the complete preregistered gate set is available.