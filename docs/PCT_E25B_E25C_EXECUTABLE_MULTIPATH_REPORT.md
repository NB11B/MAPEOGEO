# PCT E25B/E25C — Multipath and Executable Cycle Consistency

## Scope

This extension deepens E25 without changing MAPEOGEO semantic relations. E25B audits the frozen v0.9 trust projection made from `SAME_SEMANTICS`, `EQUIVALENT_TO`, `REPRESENTS`, and associated `VERIFIED_BY` evidence. E25C attaches executable contract adapters only to the four existing source-bound EO/GEO/FORMAL cycles whose v0.7 contracts and v0.8 formal scopes are already persisted.

## E25B — full multipath trust audit

- Trust components: **24**
- Component sizes: **20 × 3-node**, **4 × 4-node**
- Independent cycle rank after source anchors are included: **32**
- Unordered endpoint pairs in trust components: **84**
- Endpoint pairs with at least two simple paths: **84/84**
- Distinct simple-path pair comparisons: **300**
- Bridges / single-path trust bottlenecks inside this projection: **0 / 0**
- Identity/hash conflicts: **0**
- Certificate conflicts: **0**

### Important refinement of E25

E25 reported four cycles because it counted cycles inside the equivalence-only subgraph. E25B adds the `REPRESENTS` edges back to the source/object anchors. Under that trust projection, **all 24 equivalence components are cyclic**, not only four. The twenty original EO/GEO test pairs form triangles with their semantic object anchors; the four source-bound EO/GEO/FORMAL components form complete four-node trust graphs. The total independent cycle rank is 32.

This means the existing graph already contains more redundant closure than the equivalence-only count suggested. Within the frozen trust projection there are no bridges and no endpoint pairs with only one simple path.

## E25C — executable closure on the four real EO/GEO/FORMAL cycles

- Cycles executed: **4**
- Exact finite/symbolic inputs: **3419**
- Pairwise EO/GEO/FORMAL path equalities checked: **10257**

| Contract | Source anchor | Exact inputs | Formal scope | Result |
|---|---|---:|---|---|
| `rank` | `srcdecl:theorem:6_16` | 682 | `GENERAL_FINITE_DIMENSIONAL_DIVISION_RING` | PASS |
| `convex` | `srcdecl:definition:44_6` | 279 | `TWO_POINT_REAL_CONVEX_COMBINATION` | PASS |
| `lp` | `srcdecl:theorem:47_9` | 2457 | `POSITIVE_ONE_DIMENSIONAL_LINEAR_PROGRAM` | PASS |
| `gauss` | `srcdecl:definition:53_4` | 1 | `SCALAR_REAL_GAUSSIAN_EXPONENT_IDENTITY` | PASS |

The four executable adapters are not new semantic edges. They instantiate the already-persisted v0.7 contracts (`rank`, `convex`, `lp`, `gauss`) against the existing node IDs and v0.8 formal scopes, and compare EO, GEO, and FORMAL routes in a common semantic codomain.

## Layered corruption controls

| Synthetic corruption | C0 identity | C1 certificate | C2 executable |
|---|---|---|---|
| Wrong representation→source anchor | FAIL | NOT_REACHED | NOT_REACHED |
| Certificate changed to FAIL | PASS | FAIL | NOT_REACHED |
| Rank GEO executable route mutated with metadata untouched | PASS | PASS | FAIL |

The attack ladder demonstrates why closure level must be explicit: a wrong anchor is caught at C0, a certificate corruption is invisible to C0 but caught at C1, and a wrong executable transformation can leave C0/C1 intact while failing C2.

## Closure levels established

- **C0 — identity/hash consistency:** established over the frozen trust projection.
- **C1 — certificate consistency:** established over the frozen trust projection.
- **C2 — executable contract agreement:** established for the four source-bound v0.7/v0.8 cycles listed above.
- **C3 — chain-map commutation:** not applicable to these four scalar/decision contracts.
- **C4 — induced homology agreement:** not applicable to these four scalar/decision contracts.
- **C5 — exact morphism/provenance equivalence:** not established.

## Claim boundary

E25B is exhaustive only over the frozen semantic trust projection, not the full concept/proof-dependency graph. E25C executes contract adapters for four existing source-bound cycles; it does not claim that all current repository edges carry executable morphisms, nor does it promote C3–C5 evidence.
