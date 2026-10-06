# MAPEOGEO Work Router v0.1

## Scope

This bounded kernel routes mathematical work over explicitly registered executable
edges. It preserves the existing MAPEOGEO evidence boundary:

- discovery edges may propose candidate routes;
- uncertified edges are never executable;
- certified route search is fail-closed;
- runtime information availability is distinct from mathematical reachability;
- materialization is distinct from observation.

The v0.1 overlay does **not** promote underlying MAPEOGEO graph relations and does
not claim whole-corpus EO/GEO equivalence.

## Outcomes

The router emits one of:

- `ANSWER` — target is already available;
- `EXECUTE` — a lowest-cost certified route is executable;
- `OBSERVE` — a certified route exists but required information is absent;
- `CERTIFY` — only a candidate/uncertified route exists;
- `MATERIALIZE` — the mathematical answer is derivable/known but a requested
  numerical representation remains to be produced;
- `UNRESOLVABLE` — no route exists from current state.

## Initial qualified routes

The bounded overlay covers the six PSMSL/MAPEOGEO workloads developed in the
associated investigation:

1. directional scale coordinates -> area expansion;
2. positive-scale/proper-rotation class -> orientation preservation;
3. local generator real part -> stability;
4. phase increments -> accumulated phase;
5. scale coordinate -> amplitude threshold;
6. vector/subspace pair -> projection membership.

An intentionally cheaper uncertified determinant shortcut is included as an
adversarial fixture. Certified Dijkstra routing must ignore it.

## Claim boundary

v0.1 tests routing mechanics and authority separation. It does not establish
that arbitrary MAPEOGEO graph paths are executable. Expansion requires explicit
endpoint-bound executable or formal contracts.
