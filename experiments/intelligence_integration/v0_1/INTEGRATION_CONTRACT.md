# MAPEOGEO Intelligence Integration Contract (v0.1)

## 1. Executive Summary

This contract establishes the formal semantic mapping rules, layer assignments, representation distinctions, authority boundaries, and timeline clock domain semantics required to translate a declared subset of MAPEOGEO graph records into an attributed intelligence analysis case under the `intel_uow` reference model (v0.3).

**Governing Question:**
> *Can a declared subset of MAPEOGEO records be translated into an intelligence analysis case without changing identity, interpretation, evidence status, uncertainty, authority, or causal ordering?*

The v0.1 read-only adapter demonstrates that the answer is **affirmative** for the declared finite capacity and continuity domain, preserving all substantive analytical conclusions, uncertainty states, and provenance lineages while strictly enforcing architectural boundaries.

---

## 2. Architectural Boundary Mappings

### 2.1 Identity and Revision
- Pinned identifiers (`id`, `revision`) are strictly preserved.
- Similar labels, textual aliases, or homonymous names cannot establish identity.
- Entity bindings retain exact scope (`subject`, `window`).

### 2.2 Graph Layers
MAPEOGEO nodes and records are mapped to declared reference graph layers as follows:

| MAPEOGEO Node Type | Target Graph Layer | Semantic Invariant |
|---|---|---|
| `SOURCE`, `STATEMENT`, `PROOF_STEP`, `PROOF_PATH`, `WOUND` | `source` | Source assertions remain strictly informational; never treated as reviewed grants or actual causal occurrences. |
| `OBJECT`, `OPERATOR`, `REPRESENTATION` | `subject_hypothesis` | Model and representation candidates; subject to analytical derivation. |
| `CERTIFICATE`, `DERIVATION` | `analytical_derivation` | Verified certificates and bounded analytical products. |
| `SCENARIO`, `OBSERVATION` | `scenario` | Hypothetical state spaces; explicitly barred from mutating actual UoW state. |
| `UOW_TASK`, `ADMISSION_RECORD`, `JOURNAL_ENTRY`, `TRANSACTION` | `actual_uow` | Governed actual operational history, reservations, duties, and completion knowledge. |
| `POLICY`, `CONTRACT`, `OPERATION_DEF` | `registry` | Pinned contracts, policies, and operational vocabulary definitions. |

### 2.3 Operational Grammar
- Versioned source conventions and vocabulary contexts (`meaning-context`, `review-language`) are explicitly carried.
- Candidate readings and attributed reviews (`disposition: accepted/rejected/deferred`) remain tied to their witness evidence.
- An author's judgment is kept separate from evidence for the underlying claim.

### 2.4 Representation Relations
- `CANDIDATE_REPRESENTS`, `CANDIDATE_EO`, and `CANDIDATE_GEO` edges represent detection or candidate profile views.
- **Strict Invariant:** Candidate edges must NEVER be automatically or implicitly promoted to `SAME_SEMANTICS` or `EQUIVALENT_TO`.
- Semantic equivalence requires an explicit, accepted semantic contract overlay.

### 2.5 Evidence Lineage & Corroboration
- Report identity (`id`) and reviewed origin lineage (`origin`) are strictly decoupled.
- Multiple report records sharing a single reviewed origin contribute only **one** independent evidential origin.
- Report counting and origin counting remain distinct operations, preventing false corroboration.

### 2.6 Analytical Model Bindings & Host Grounding
- Explicitly named model: `uow.intelligence.meaningful_gaps.carrier_continuity.v0_3`.
- Reference parameters and state spaces are extracted directly from host graph nodes with recorded field provenance (`HostFieldProvenance`):
  - `demand`: extracted from `src:service_contract:v1.attributes.demand_units` (value: 10).
  - `regular_capacity`: extracted from `src:carrier_schedule:v1.attributes.regular_capacity` (value: 4).
  - `bridge_capacity`: extracted from `src:carrier_schedule:v1.attributes.bridge_capacity` (value: 6).
  - `loading_capacity`: extracted from `src:carrier_schedule:v1.attributes.loading_capacity` (value: 10).
  - Finite state space: extracted from `obj:carrier_capacity_model:v1.attributes.capacity_values` (`[3, 6]`) and `availability_values` (`[0, 1]`).
- Supported output questions: capability support/refutation, minimax shortfall upper bounds, robust preferred options, and meaningful information gaps (`C`, `A`).

### 2.7 Authority Separation & Scope for v0.1
- Reviewed authority views (specifying actor, actions, purpose, scope, resource limits, and recipients) are strictly separated from claims about authority in source material.
- Source assertions claiming authority or grants within scenarios cannot admit proposals or release reservations.
- **Scope Boundary:** Actual lifecycle projection (dynamic grant expiry invalidation, cancellation release of reservations, and runtime mutation of actual UoW state) is explicitly declared unsupported in v0.1.

---

## 3. Resolution of Timeline Clock Domain Ownership & Identity

### 3.1 Clarification of System Identities
The contract distinguishes four distinct identities:

| Identity Class | Definition & Responsibility |
|---|---|
| **Participant / Principal** | The human agent, organization, or system actor associated with work or authority (e.g., `analyst`, `owner`). |
| **UoW (Unit of Work)** | The particular governed task instance bounded by an admitted proposal and contract (e.g., `uow:task:review_01`). |
| **Execution Boundary** | The security/enforcement perimeter where operations are admitted, executed, or recorded. |
| **Clock Domain** | The specific stream that owns a monotonically increasing sequence counter (`seq`). |

### 3.2 The Concrete Problem in `workflow.py`
The reference implementation of `event_relation(left_id, right_id, events)` constructs a partial order graph where events sharing the same `actor` string are sorted and totally ordered by their local sequence number `seq`:

```python
for seqs in by_actor.values():
    seqs.sort()
    for (_, earlier), (_, later) in zip(seqs, seqs[1:]):
        graph[earlier].add(later)
```

If MAPEOGEO maps a participant directly to `actor` across two independent UoWs, two failure modes arise:
1. **Colliding Sequence Identifiers:** Both UoWs emitting `seq = 1` cause a duplicate key error in `actor_sequences[(e['actor'], e['seq'])]`.
2. **Spurious Causal Ordering:** Events across independent, concurrent UoWs are falsely chained into a linear timeline (`seq 1 -> seq 2`), manufacturing an ordering where none exists.

### 3.3 The Adapter Resolution & Canonical JSON Clock Identity
The adapter enforces explicit clock domain namespacing via canonical JSON encoding:
- **Sequence Ownership:** The sequence counter is owned by the stream `(domain_id, local_actor)`.
- **Unambiguous Canonical Encoding:**
  `event_actor = f"uow-clock:v1:{json.dumps([domain_id, local_actor], ensure_ascii=False, separators=(',', ':'))}"`
- **Invertible Representation:** The codec strictly satisfies $D(E(d, a)) = (d, a)$. Decoding validates that re-encoding reproduces the exact string.
- **Boundary Overlap Immunity:** Component boundaries are preserved cleanly across all character contents (including colons, quotes, slashes, whitespace, combining characters, and arbitrary Unicode scalar values). Pairs like `("ops:", "analyst")` and `("ops", ":analyst")` produce distinct encodings (`uow-clock:v1:["ops:","analyst"]` and `uow-clock:v1:["ops",":analyst"]`), eliminating the boundary-overlap collision.
- **Causal Parent Preservation:** Unrelated UoWs remain completely concurrent. When comparing events across independent clock domains with no causal dependency, **no causal order is established from the supplied history (relation remains `unknown`)**. Order across clock domains is established **only** if an explicit causal parent link (`parents: ["evt-earlier"]`) connects them.

---

## 4. The Three Projection Conditions

The adapter explicitly classifies each candidate case into one of three statuses:

1. **`SUPPORTED_CASE` / `SUPPORTED_WITH_UNKNOWNS`**:
   The input records match the declared schema and finite model. Missing facts remain explicitly `None` or `'unknown'` (zero-fabrication) and propagate as genuine intelligence uncertainty.
2. **`UNSUPPORTED_PROJECTION`**:
   The host records express semantics outside the finite reference capability:
   - Continuous probability densities or unbounded state spaces.
   - Cross-domain global clock synchronization without causal edges.
   - Actual lifecycle projection (dynamic grant expiry invalidation, cancellation release of reservations).
   Diagnosed explicitly without crashing.
3. **`INVALID_INPUT`**:
   The proposed case violates structural contracts (e.g., empty state spaces, duplicate record keys, or missing envelope attributes).

---

## 5. Attributed Analytical Output Contract

The adapter returns an `AttributedAnalysisResult` that explicitly includes:
- Target question reference and revision.
- SHA-256 digest of the pinned input graph snapshot.
- Source record references and model assumptions.
- Field provenance linking reference model parameters to host node IDs and attributes.
- Baseline evaluation (capability, preferred options, minimax shortfall).
- Meaningful information gaps identified.
- Hypothetical observation consequences (`actual_world_changed=False`).
- Retained unknowns (fields that remained unresolved).
- Immutability verification certificate (asserting input snapshot and workflow state were not modified).
