# MAPEOGEO v0.21 Rigor-First Expansion Design

## Objective

Expand MAPEOGEO substantially at both the foundational and connective-advanced levels without admitting invented mathematics, paraphrase-as-provenance, or automatically promoted semantic relations.

The governing rule is:

> Coverage may grow quickly; authority may grow only with evidence.

An honest unresolved declaration is preferable to a fabricated canonical bridge.

## Scope

v0.21 is a source-admission wave, not an automatic ontology-generation wave. It adds real source-bound mathematical declarations from five open, machine-readable corpora:

1. **Open Logic Project** — logic, set theory, proof theory, computability foundations.
   - Repository: `OpenLogicProject/OpenLogic`
   - Pinned commit: `1e960beff9ed7835bf3e3f1335e21af3439cd107`
   - License: CC BY 4.0 except where upstream marks material otherwise.
   - Parser: structured LaTeX theorem environments.

2. **Oscar Levin, Discrete Mathematics: An Open Introduction** — proof, counting, sequences, graph theory, combinatorics, introductory number theory.
   - Repository: `oscarlevin/discrete-book`
   - Pinned commit: `e258a377b4ef7ab63c647457430e98fbb4c7c3bb`
   - License: CC BY-SA 4.0.
   - Parser: PreTeXt XML.

3. **Thomas Judson, Abstract Algebra: Theory and Applications** — groups, homomorphisms, quotient groups, rings, ideals, fields, Galois theory.
   - Repository: `twjudson/aata`
   - Pinned commit: `3069910e3ded72ff5e18837a97a0e810c92790e2`
   - License: GNU Free Documentation License.
   - Parser: PreTeXt XML.

4. **Jiří Lebl, Basic Analysis** — rigorous real analysis, metric spaces, multivariable analysis, inverse/implicit function theorems.
   - Repository: `jirilebl/ra`
   - Pinned commit: `e21ec524ca7d54f800c693b948020c188d21d01f`
   - License: CC BY-SA 4.0 / CC BY-NC-SA 4.0 dual license.
   - Parser: structured LaTeX theorem environments.

5. **Jiří Lebl, Notes on Diffy Qs** — ODEs and dynamical systems, giving v0.21 an advanced connective layer between calculus, linear algebra, flows, and differential geometry.
   - Repository: `jirilebl/diffyqs`
   - Pinned commit: `658bcae9fb710f3fae2c9da4ca4524ce157453af`
   - License: CC BY-SA 4.0 / CC BY-NC-SA 4.0 dual license.
   - Parser: structured LaTeX theorem environments.

Future advanced corpora (functional analysis, algebraic topology, numerical analysis, stochastic processes) are intentionally not admitted in this stage until their source/licensing/parser contracts receive the same review.

## Source admission contract

A v0.21 source declaration is admissible only when all of the following hold:

- the upstream repository and exact commit SHA are pinned;
- checkout HEAD exactly equals the pinned SHA;
- the declaration occurs inside an explicitly supported structured environment (`definition`, `theorem`, `proposition`, `lemma`, `corollary`, `axiom`, or registered aliases);
- the source locator is reproducible as repository path plus line range and structured source identifier when one exists;
- the declaration payload is hashed deterministically after parser-specific normalization;
- no statement body, proof body, page image, or source prose is persisted in graph/evidence artifacts;
- duplicate source identities fail closed;
- hash collisions fail closed;
- extraction failures remain visible and cannot silently synthesize replacement declarations.

Every admitted record stores only metadata such as source ID, repository, pinned revision, locator, declaration type, structured identifier, statement SHA-256, character count, parser version, and admission state.

## Canonicalization quarantine

New v0.21 declarations enter with:

`canonical_status = UNRESOLVED`

No parser, keyword detector, embedding similarity, shared graph neighborhood, title similarity, or LLM-generated paraphrase may emit `SAME_SEMANTICS`, `SCOPED_OVERLAP`, `RELATED_TO`, `FORMAL_LINKED`, or `KERNEL_VERIFIED`.

A later semantic review may promote a declaration only through an explicit endpoint-bound contract. The contract must name the source declaration identity, target canonical object, relation type, scope statement or machine-readable scope metadata, reviewer status, and supporting evidence class.

This design deliberately increases source coverage faster than canonical coverage.

## Extraction architecture

`scripts/source_admission_v0_21.py` owns five responsibilities:

1. validate the source registry schema and reject moving refs;
2. fetch each pinned upstream commit into a temporary workspace using Git;
3. extract structured declarations using one of two deterministic parser families;
4. emit zero-prose declaration metadata;
5. produce an admission report including counts, rejected blocks, duplicate checks, and parser provenance.

### PreTeXt parser

The PreTeXt parser uses XML structure rather than prose heuristics. It recognizes declaration elements with explicit `<statement>` children and obtains identifiers from `xml:id` where present. Statement identity is the SHA-256 of a deterministic UTF-8 normalization of the statement subtree text. The extraction method/version is recorded.

### LaTeX parser

The LaTeX parser recognizes only registered theorem-like environments. It strips comments for structural scanning, balances matching environment boundaries, finds an in-block `\\label{...}` where present, and otherwise uses path plus declaration ordinal. Hashing uses the exact declaration body with CRLF normalized to LF; no body text is written to outputs.

## Graph integration

`scripts/rigor_expansion_v0_21.py` loads the accepted v0.20/foundation graph and appends:

- one source-root node per v0.21 corpus;
- one `SOURCE_DECLARATION` node per admitted declaration;
- provenance containment edges only.

It does **not** create semantic correspondence edges. Existing v0.20 canonical objects and amendments remain untouched.

All new source nodes are tagged with `canonical_status: UNRESOLVED`, `formal_status: UNFORMALIZED`, and `executable_status: UNTESTED` unless a separately registered evidence object says otherwise.

## Evidence and tests

The stage must fail closed on:

- branch names or unpinned upstream refs;
- checkout SHA mismatch;
- unsupported parser kind;
- duplicate node IDs;
- duplicate `(source_id, structured_id)` identities;
- persisted forbidden prose keys;
- semantic edges emitted from v0.21 nodes without an explicit admission contract;
- mutation of sealed v0.20 scientific inputs.

Tests are written before implementation. The first CI run is expected to fail because the new intake modules do not yet exist. Production code is then added until the tests pass.

A networked integration test fetches all pinned sources and enforces nonzero extraction from each corpus. After the first successful extraction, exact per-source declaration counts and source-tree fingerprints are frozen in the committed evidence manifest; subsequent runs must match exactly.

## Success criteria

v0.21 is accepted only when:

- all five pinned source repositories are fetched and verified at exact commits;
- all structured declarations are deterministically extracted with zero-prose persistence;
- no automatic semantic relation is emitted;
- the graph reconstructs from the accepted v0.20 baseline plus v0.21 source declarations;
- exact extraction counts are frozen after first successful integration and replay identically;
- the full repository tests pass;
- clean reconstruction is byte-deterministic for v0.21 artifacts;
- sealed v0.20 inputs remain byte-identical.

This is intentionally a high-coverage, low-authority expansion: source mathematics enters broadly, while semantic and formal authority remain conservative.