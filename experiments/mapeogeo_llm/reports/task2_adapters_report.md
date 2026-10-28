# Task 2 operator and evidence adapters

Date: 2026-10-28  
Scope: `geo_adapter.py`, `graph_adapter.py`, `lean_adapter.py`, their focused tests and fixture, and `scripts/build_geo.ps1` only.

## Dependency provenance

- GeometricElementaryOperators checkout: `C:\Users\nateb\Documents\GeometricElementaryOperators`
- GEO source commit: `c590bd7a01f316971722053faf8626458958f820`
- GEO public header: `include/geo/operator_kernel.h`
- GEO ABI: `0x00050100`
- GEO maximum dimension/blades: 6 / 64
- MAPEOGEOv2 checkout: `C:\Users\nateb\Documents\MAPEOGEOv2`
- MAPEOGEOv2 source commit: `64a36dce10000e47bc4c651e7b92f14e28c68652`
- Graph schema source: `src/mapeogeo/graph/{node,edge,relation,serialization,transaction}.py`
- Lean: `4.33.1`, commit `819816b2e0a3bf405af45ae5c7af2491d8f5bee6`, x86_64 Windows release

Both dependency SHAs were read from the live local checkouts during final verification. The MAPEOGEOv2 checkout contained unrelated untracked certification artifacts; Task 2 did not modify either dependency checkout.

## Supported interfaces

### GEO

```python
GeoAdapter(
    library_path: str | Path | None = None,
    *,
    allow_reference: bool = False,
    expected_digest: str | None = None,
)
GeoAdapter.gp(a: list[float], b: list[float], signature: list[int]) -> list[float]
GeoAdapter.grade(a: list[float], grade: int, signature: list[int]) -> list[float]
GeoAdapter.metadata() -> dict[str, object]
```

Dense coefficient position is the blade bit mask, from scalar blade `0` through blade `2^n - 1`. Signatures contain exactly `n` integer entries, each `+1` or `-1`, with `1 <= n <= 6`. Inputs must contain exactly `2^n` finite real coefficients. Native loading is fail-closed by default and checks the exported ABI at runtime. The Python reference backend is available only through explicit `allow_reference=True`; its metadata says `development_reference` and `native_qualified=false`.

An ABI-compatible native DLL remains executable without provenance, but its metadata returns `native_qualified=false` and `source_commit=null`. Native qualification requires both an explicit caller-supplied `expected_digest` matching the loaded DLL and a matching adjacent `geo_operator_kernel.receipt.json`. The receipt binds the DLL digest, ABI, pinned source commit, exact hashes of `include/geo/operator_kernel.h` and `src/operator_kernel.c`, and compiler identity. A receipt is declared build provenance, not an external signature or cryptographic trust root; `qualification_reason` states that qualification rests on the caller's expected digest plus the matching receipt.

The build script pins the exact GEO commit and header ABI, builds only `src/operator_kernel.c`, and emits:

- DLL: `experiments/mapeogeo_llm/artifacts/geo/geo_operator_kernel.dll`
- receipt: `experiments/mapeogeo_llm/artifacts/geo/geo_operator_kernel.receipt.json`
- final SHA-256: `03eaa7778f53ccedaa1dc36a9e3872c4d95fea97d5967349094d4d40f58df963`
- compiler: MinGW-W64 GCC 13.2.0

The DLL and receipt are ignored build outputs, not committed source artifacts. Before compilation, the script verifies that both compiled source inputs are byte-identical to the pinned Git revision and rejects dirty inputs. The build is byte-reproducible across different output directories by suppressing the PE timestamp and fixing the link image base; ASLR remains enabled by the PE `DYNAMIC_BASE` characteristic.

### Graph

```python
GraphAdapter(
    snapshot_path: str | Path,
    *,
    source_commit: str,
    source_repository: str = "NB11B/MAPEOGEOv2",
)
GraphAdapter.query(
    node_id: str,
    relation: str | None = None,
    max_results: int = 32,
) -> dict[str, object]
```

The adapter accepts the actual MAPEOGEOv2 snapshot envelope:

```json
{
  "schema": "mapeogeo.graph.snapshot",
  "schema_version": 1,
  "snapshot_id": "...",
  "state_hash": "...",
  "nodes": [
    {"node_id": "...", "kind": "QUERY", "role": "ATOMIC_JUDGMENT", "scope_hash": "...", "metadata": {}}
  ],
  "edges": [
    {
      "source_id": "...",
      "target_id": "...",
      "relation": "CANDIDATE_REPRESENTS",
      "port_binding": "default",
      "contract": null,
      "metadata": {}
    }
  ]
}
```

Fixture: `experiments/mapeogeo_llm/tests/fixtures/graph_snapshot.json`.

On construction it validates schema/version, node/edge types, unique IDs, endpoints, relations, strong-relation certification metadata, and the exact MAPEOGEOv2 topology `state_hash`. It also records SHA-256 of the full snapshot bytes, which covers metadata omitted from the upstream topology hash. The loaded snapshot is deep-copied and queries never reread or mutate its source file.

Every returned edge preserves its declared relation and adds an evidence classification:

- `candidate`: `CANDIDATE_REPRESENTS`;
- `declared`: a non-candidate relation without certified contract metadata;
- `certified_metadata`: a contract declares certification.

All three classes return `proof_replayed=false` and `proof_verified=false`. The adapter does not replay proof certificates and cannot promote graph metadata to independent proof. A live integration test creates and serializes a snapshot through the pinned MAPEOGEOv2 implementation, then queries it through this adapter.

### Lean

```python
LeanAdapter(lean_executable: str | Path = "lean")
LeanAdapter.verify(
    proposition: str,
    proof: str,
    timeout_seconds: float = 10,
) -> dict[str, object]
```

Accepted propositions are one-line closed natural-number comparisons: decimal numerals and parentheses, `+`, `-`, `*`, and exactly one of `=`, `<`, `<=`, `>`, `>=`. Accepted proof text is exactly `by rfl` or `by decide`. Identifiers, declarations, newlines, arrows, hypotheses, arbitrary tactics, `sorry`, `admit`, and `axiom` are rejected before process launch.

The adapter generates one fixed theorem named `mapeogeo_checked`, adds only `#print axioms mapeogeo_checked`, and calls Lean with a fixed argv list and `shell=False`. `VERIFIED` requires Lean exit code 0 and an explicit axiom-free audit message. Returned evidence includes Lean version, theorem name, source digest, proof family, and empty assumptions. Timeouts are non-verifying and the temporary source is removed.

After the restricted grammar accepts a proposition, a Lean compiler rejection is labelled `UNSOLVED`, with `kernel_checked=false` and `negation_checked=false`. The adapter never reports `REFUTED` because it does not independently check a negation theorem.

## Tests and independent references

GEO tests cover:

- native ABI and backend metadata;
- all Cl(3,0) and Cl(2,1) basis-blade products against independently constructed complex Pauli matrices;
- mixed-metric basis squares and anticommutation;
- random integer associativity and bilinearity;
- dense results against the independent matrix representation;
- grade projection;
- zero/invalid dimension, signature, shape, finite-value and explicit reference-backend boundaries;
- byte-reproducible native builds in different output directories.
- source-bound build receipts, unqualified alternate same-ABI artifacts, receipt tampering, and dirty-source rejection in a temporary checkout.

Graph tests cover candidate versus certified metadata, no proof promotion, relation filters, bounds, immutable snapshot loading, schema/hash/dangling-edge rejection, missing-node behavior, and the live MAPEOGEOv2 serializer integration.

Lean tests use the real installed Lean process for valid, false, malformed, timeout, `sorry`, `admit`, source injection, axiom injection, hypothesis smuggling and invalid-timeout cases.

## Commands and results

```powershell
python -m pytest -q experiments/mapeogeo_llm/tests/test_geo.py experiments/mapeogeo_llm/tests/test_graph.py experiments/mapeogeo_llm/tests/test_lean.py
```

Result after the proof-status and native-provenance corrections: `39 passed in 5.70s`.

```powershell
python -m pytest -q experiments/mapeogeo_llm/tests
```

Latest result after the native-provenance correction and concurrent integration additions: `148 passed, 3 failed, 3 warnings in 14.36s`. The three failures are outside Task 2: `test_end_to_end.py::{test_fresh_process_cli_loads_actual_trained_checkpoint_and_returns_json,test_cli_rejects_unsupported_free_text_without_fabricating_answer}` and `test_train_smoke.py::test_real_training_updates_weights_and_checkpoint_reloads_equivalently`; their generated complete public states tokenize to 672 or 808 tokens while the concurrent training configuration limits `max_seq_len` to 512. Warnings were third-party PyTorch `pynvml` deprecation and SWIG type deprecations. No full MAPEOGEO-LLM PASS is claimed for this latest shared-tree run.

```powershell
python -m py_compile experiments/mapeogeo_llm/geo_adapter.py experiments/mapeogeo_llm/graph_adapter.py experiments/mapeogeo_llm/lean_adapter.py
```

Result: exit 0, no diagnostics.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_geo.ps1
```

Result: exit 0; source commit and ABI matched; final DLL SHA-256 `03eaa7778f53ccedaa1dc36a9e3872c4d95fea97d5967349094d4d40f58df963`.

A repository-root unscoped `python -m pytest -q` was also attempted before final scoped verification. Collection stopped on 17 unrelated missing-package/import errors involving `intel_uow`, vendored legacy `mapeogeo` modules, `ngc_rq`, `bcig.ontology`, and top-level `tests` imports. No unscoped repository-wide PASS is claimed.

## Evidence limits

- GEO results are native floating-point numerical evidence, not symbolic proof. Exact-domain identities in tests use independent matrix or literal references, with explicit floating tolerances where matrix multiplication is involved.
- The pure-Python GEO backend is a development reference and is never native qualification.
- Graph snapshot integrity and declared certification metadata are evidence about stored data, not proof replay or theorem certification.
- Lean verification covers only the stated closed-Nat subset and the two fixed proof families. It is not an arbitrary Lean source interface.
- No proof source, graph candidate, model output, parser transcription, or floating comparison is promoted to independent formal proof.
