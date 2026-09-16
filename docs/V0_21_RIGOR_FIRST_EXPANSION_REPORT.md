# MAPEOGEO v0.21 — Rigor-First Mathematical Source Expansion

## Objective

v0.21 expands mathematical coverage while deliberately refusing automatic mathematical authority.

> **Coverage may grow quickly; authority may grow only with evidence.**

The stage admits exact source-bound theorem/definition occurrences from pinned open mathematical corpora, but all newly admitted declarations remain semantically quarantined until separately reviewed endpoint-bound contracts exist.

This stage therefore does **not** claim that newly admitted source declarations are already canonicalized, formally verified, executable, or proof-connected to the historical MAPEOGEO graph.

## Pinned source corpora

| Source ID | Corpus | Exact upstream revision | Parser | Scope |
|---|---|---|---|---|
| `OPEN_LOGIC_PROJECT` | Open Logic Project | `1e960beff9ed7835bf3e3f1335e21af3439cd107` | structured LaTeX | logic, set theory, proof theory, computability |
| `LEVIN_DISCRETE` | Oscar Levin, *Discrete Mathematics: An Open Introduction* | `e258a377b4ef7ab63c647457430e98fbb4c7c3bb` | PreTeXt XML | discrete mathematics, combinatorics, graph theory, elementary number theory |
| `JUDSON_AATA` | Thomas Judson, *Abstract Algebra: Theory and Applications* | `3069910e3ded72ff5e18837a97a0e810c92790e2` | PreTeXt XML | groups, rings, fields, quotient structures, Galois theory |
| `LEBL_BASIC_ANALYSIS` | Jiří Lebl, *Basic Analysis* | `e21ec524ca7d54f800c693b948020c188d21d01f` | structured LaTeX | rigorous real analysis, metric spaces, multivariable analysis |
| `LEBL_DIFFYQS` | Jiří Lebl, *Notes on Diffy Qs* | `658bcae9fb710f3fae2c9da4ca4524ce157453af` | structured LaTeX | ordinary differential equations and dynamical systems |

Upstream checkout is fail-closed: the transient checkout `HEAD` must equal the exact pinned 40-character SHA before parsing begins.

## Observed source-admission results

The first accepted live extraction from the exact pinned revisions produced the following source **occurrences**:

| Source | Admitted occurrences | Unique statement bodies |
|---|---:|---:|
| Open Logic Project | **1,244** | **1,182** |
| Judson AATA | **275** | **274** |
| Lebl Basic Analysis | **440** | **440** |
| Lebl DiffyQs | **48** | **47** |
| Levin Discrete | **68** | **67** |
| **Total** | **2,075** | **2,010** |

The 2,075 occurrences contain 41 duplicate statement-hash groups accounting for 65 repeated occurrences beyond the 2,010 unique statement bodies. These repetitions remain distinct source locations; they are **not** counted as independent mathematical evidence merely because the same statement text appears more than once.

The frozen zero-prose identity set is bound by:

- declaration metadata SHA-256: `1d4298f5e385e75fb276d70690b55e1a4d403a302921dcfaf3a9a3e45e6560f1`
- frozen declaration gzip SHA-256: `80028e7a53da6a05c2badb669cc0a826bad609de0c2fd208a42fedc068ab8c41`
- frozen declaration payload SHA-256: `29d48891ce88f95c2225e28e57cb4a4968356b01d4f800d4af96d1a8e393368b`
- source-registry projection SHA-256: `7ad95ffc0d20111afeb83a1371ca64c678cdab94eec4fb1ccdee70e22a95dbce`

## Zero-prose persistence and formulation boundary

The parser reads theorem-like source bodies only in memory. Persisted declaration records contain metadata such as:

- source ID;
- repository and exact revision;
- structured source identifier;
- declaration kind;
- repository path and line range;
- SHA-256 of the parsed declaration statement/body;
- character count;
- parser version and extraction method.

Source statement text, proof text, page images, and source prose are forbidden persisted keys.

This means the graph can always return to an exact source revision and locator to review formulation, while copyrighted/source prose is not copied into graph artifacts.

## Semantic quarantine

Every new declaration is admitted with exactly:

```text
canonical_status  = UNRESOLVED
formal_status     = UNFORMALIZED
executable_status = UNTESTED
```

Observed counts are therefore:

```text
UNRESOLVED:   2,075 / 2,075
UNFORMALIZED: 2,075 / 2,075
UNTESTED:     2,075 / 2,075
```

No v0.21 parser or intake path is permitted to infer any of the following relations from title similarity, keywords, embeddings, source proximity, graph neighborhoods, or model-generated paraphrase:

```text
SAME_SEMANTICS
SCOPED_OVERLAP
RELATED_TO
REPRESENTS
FORMAL_LINKED
KERNEL_VERIFIED
PROOF_DEPENDENCY
```

The only new edge type emitted by v0.21 source admission is:

```text
SOURCE_CONTAINS_DECLARATION
```

from an exact pinned source-corpus root to its admitted source occurrence.

## Why this is a mathematical expansion despite zero automatic canonicalization

The prior graph had broad canonical coverage but thin source-grounded support in several foundational and connective areas. v0.21 adds exact, addressable mathematical declarations across logic, set theory, combinatorics, graph theory, number theory, abstract algebra, rigorous analysis, ODEs, and dynamical systems.

The important distinction is that **source coverage and semantic authority are now separate growth axes**:

```text
real source mathematics
        |
        v
SOURCE_DECLARATION (exact revision + locator + statement hash)
        |
        +-- canonical_status = UNRESOLVED
        +-- formal_status = UNFORMALIZED
        +-- executable_status = UNTESTED
        |
        v
future explicit semantic/formal/executable review
```

A later stage can promote selected high-value declarations into canonical objects or existing canonical objects only through explicit endpoint-bound semantic contracts with scope review.

## Rigor contracts

v0.21 fails closed on:

- moving or non-SHA upstream revisions;
- upstream checkout revision mismatch;
- malformed supported theorem environments;
- unsupported parser families;
- duplicate source identities or node IDs;
- forbidden persisted prose fields;
- source provenance mismatch;
- status auto-promotion;
- semantic/proof/formal edges emitted from quarantined declarations;
- live pinned-source extraction differing byte-for-byte from the frozen identity manifests.

## Reconstruction architecture

Network access is used only in the dedicated source-admission verification gate. Standard graph reconstruction is offline and consumes the frozen zero-prose declaration identity file:

```text
accepted v0.20 / foundation graph
        |
        +-- formal/source_registry_v0_21.json
        +-- formal/source_declarations_v0_21.json.gz
        |
        v
v0.21 provenance-only graph expansion
```

The dedicated CI gate separately refetches all five exact upstream commits and requires the regenerated frozen declaration gzip and evidence manifest to match the committed files byte-for-byte.

## Current acceptance state

The exact source-admission identities above have been observed and frozen. Final acceptance additionally requires the branch-level CI gate to complete the offline graph reconstruction, quarantine artifact checks, full repository regression suite, exact live-source replay, deterministic double reconstruction, and sealed-input immutability checks. Until those gates are green, v0.21 remains an unmerged feature-stage candidate.
