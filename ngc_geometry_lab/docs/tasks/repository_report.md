# Repository adapter and exact closure qualification

## Result

Implemented `ngc_geometry_lab/repository.py` and 18 meaningful tests in `tests/test_repository.py`. The initial test run recorded 18 expected failures because the adapter did not exist. After implementation, all 18 pass. The tests use independent analytic gate results, integer matrix products, direct coordinate-map enumeration, and source-byte tampering in temporary copies.

No vendored file was modified. No global `sys.path` mutation, repository commit, or source checkout mutation was performed. The root campaign remains responsible for its full integration run and the original upstream baseline tests.

## Implemented interfaces

- `mapeogeo_modules()` returns the actual packaged `algebra`, `inverse`, `observability`, and `work` modules.
- `dual_lane_apply(state, gate, targets, num_qubits)` validates finite normalized states, finite unitary gates, dimensions, and nonempty unique integer targets, then calls unchanged NGC `apply_local_gate_dual_lane`. It uses the upstream stacked real representation and returns a complex vector. Qubit zero is the most significant tensor factor; caller-supplied target order is preserved. It does not call the complex reference during validation or execution.
- `verify_sources()` checks SHA-256 and Git blob SHA-1 against each listed source manifest. Its aggregate and per-manifest records expose missing or changed bytes explicitly. Packaging namespace initializers are not treated as upstream files.
- `connected_operator_demo()` executes actual MAPEOGEO functions and returns JSON-friendly measurements, independent comparisons, and `qualified`.
- `exact_closure()` computes the new finite fixture described below, with a deterministic BFS, an explicit 10,000-element guard, shortest words, stable indices, a complete multiplication table, structural statistics, and exhaustive product/associativity checks.

State normalization and gate unitarity checks use absolute tolerance `1e-10`, with relative tolerance zero. The adapter rejects floating-point and Boolean qubit/target indices rather than allowing the permissive upstream integer casts to reinterpret them. Valid NumPy integer indices are accepted. Inputs are neither changed nor normalized by the adapter.

## Source verification

| Manifest | Verified files | Mismatches |
|---|---:|---:|
| MAPEOGEO implementation, tests, and notices | 15 | 0 |
| MAPEOGEO historical diagnostic sources | 4 | 0 |
| NGC real backend source bundle | 22 | 0 |
| **Total** | **41** | **0** |

This validates the recorded bytes, including their exact line endings. It does not promote historical diagnostic artifacts into measured operator evidence. A test changes source bytes in a temporary copy and confirms that both checksum disagreements are reported. Another removes a source file and a manifest and confirms explicit failure records.

## Connected operator results

The demo independently verifies all seven measurement checks:

1. MAPEOGEO `fuse(A, B)` agrees with NumPy `B @ A`, preserving execution order.
2. A two-row projection from three coordinates has rank two and nullity one.
3. The preserved upstream work-equivalence example has `AB != BA` while `PAB == PBA`. The upstream operator correctly reports observable equivalence; the original test's opposite expectation remains documented as a test defect.
4. The cyclic transition `((0,1,0),(0,0,1),(1,0,0))` with observation `C=(1,0,0)` produces the three-step observability matrix `I3`.
5. Actual upstream dynamic inversion reconstructs `(1,2,3)`, with rank three, empty null basis, and zero residual.
6. Duplicate and antipodal rows `(C,C,-C)` retain rank one and a two-dimensional null space.
7. Coordinate recovery does not identify a physical source: the source's `source_identified` remains false.

`connected_operator_demo()["qualified"]` is true from these executed comparisons.

## Newly computed exact closure

The fixture starts with identity and closes under right multiplication by the integer matrices

```text
Rx90 = ((1,0,0),(0,0,-1),(0,1,0))
Rz90 = ((0,-1,0),(1,0,0),(0,0,1))
Pxy  = ((1,0,0),(0,1,0),(0,0,0))
```

Every generated product uses unchanged MAPEOGEO `algebra.matmul` with Python integers. The closure's cardinality was measured rather than supplied as an expected output. Exact rational elimination supplies its rank statistics without a numerical rank threshold.

| Measured property | Result |
|---|---:|
| Elements | **115** |
| Rank zero / one / two / three | **1 / 18 / 72 / 24** |
| Units | 24 |
| Idempotents | 8 |
| Nilpotents, including zero | 37 |
| Center | 2 elements: identity and zero |
| Commuting ordered pairs | 2,017 |
| Maximum shortest generator-word length | 9 |
| Identity / zero BFS index | 0 / 95 |
| Independently compared products | 13,225 |
| Product mismatches | **0** |
| Checked associativity triples | 1,520,875 |
| Associativity mismatches | **0** |

The tests enumerate a second matrix family without using generator multiplication: all signed partial permutation matrices of rank below three, together with all determinant-positive full signed permutation matrices. That independently enumerated set exactly equals the BFS result. Its rank counts follow `1`, `C(3,1)^2 * 2 = 18`, `C(3,2)^2 * 2! * 2^2 = 72`, and `3! * 2^2 = 24`, respectively.

Every multiplication table entry is compared with a NumPy integer matrix product. Every associativity triple is checked by table lookup. Tests independently repeat those checks, validate identity and zero laws, reconstruct every element from its word, and check shortest-word lengths against graph distances. A growing dilation fixture verifies that the enumeration guard raises an explicit exception instead of truncating the set. A second complete execution produces the same indices, words, table, and statistics.

The output explicitly carries:

```text
provenance = "new qualification fixture; not recovered sealed artifact"
```

This successful 115-element computation is separate from the unresolved location of the historical sealed closure artifact. Agreement with the hypothesized count does not establish identity or provenance of that earlier artifact. Matrix words are written as left-to-right products; their rightmost operator acts first on column vectors.

## Verification and artifacts

Command used for the red and green runs:

```bash
python -m unittest tests.test_repository -v
```

The green run completed all 18 tests successfully. Root requested focused verification while the campaign was being developed, so no claim about the entire changing suite is made here.

Development evidence is retained in:

- `evidence/development/repository_red.log` and `repository_red.json`
- `evidence/development/repository_red_contract.log`
- `evidence/development/repository_green.log` and `repository_green.json`
- `evidence/development/repository_sources.json`
- `evidence/development/repository_connected_demo.json`
- `evidence/development/repository_exact_closure.json`
- `evidence/development/repository_summary.json`

The closure JSON contains all matrices, shortest words, and all 13,225 multiplication-table entries. No source computation, diagnostic failure, or historical provenance distinction is omitted from the report's claimed scope.
