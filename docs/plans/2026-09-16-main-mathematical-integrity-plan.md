# Main Mathematical-Integrity Implementation Plan

> Execute every task test-first. Record the failing test command before changing production code. Keep `data/mapeogeo_v0_11_graph.json.gz` byte-identical.

## Task 1: Freeze correction identities

**Files:** `formal/mathematical_integrity_amendments_v0_20.json`, `tests/test_mathematical_integrity_amendments.py`.

1. Add failing schema tests for lowercase SHA-256, unique amendment IDs, old/new identity inequality, rejected Axler edge, four statement corrections, and Dolbeault reference correction.
2. Run `pytest -q tests/test_mathematical_integrity_amendments.py` and capture RED.
3. Add the manifest with explicit `historical_identity`, `corrected_identity`, reason, evidence scope, and `REJECTED`/`ACTIVE_AMENDMENT` status.
4. Re-run to GREEN. Commit `prereg(rigor): freeze mathematical integrity amendments`.

## Task 2: Correct and validate v0.19 source material

**Files:** `scripts/import_complex_analysis_v0_19.py`, `scripts/generate_alignments_v0_19.py`, `scripts/complex_analysis_intake_v0_19.py`, `formal/cross_source_alignments_v0_19.json`, `tests/test_complex_analysis_integrity.py`, existing v0.19 tests.

1. Add failing tests for the four corrected statements/hashes, `THEOREM:2.2`, absence of the Axler eigenvector alignment, endpoint/corpus/hash validation, dangling references, and deterministic contract-scoped bridge IDs.
2. Run the focused tests and preserve RED output.
3. Correct the curated statements and alignment generator; introduce strict identity and referential validators; reject conflicting endpoint-pair relations.
4. Regenerate the v0.19 alignment file only from the corrected generator.
5. Run `pytest -q tests/test_complex_analysis_integrity.py tests/test_complex_analysis_expansion_v0_19.py`.
6. Commit `fix(v0.19): correct source identities and semantic alignments`.

## Task 3: Replace vacuous foundation contracts

**Files:** `scripts/foundation_contracts.py`, `scripts/foundation_intake.py`, `tests/test_foundation_contract_rigor.py`, `tests/test_foundation_backfill.py`.

1. Add adversarial tests for broken implication logic, out-of-domain relations, empty/one-sided inverse samples, NaN/infinity, exact Pell-neighbor Dedekind fractions, invalid denominators, unequal/empty vectors, finite-window semantics, and `n=0,x=0`.
2. Add tests proving an empty evidence registry and an unbound declaration cannot pass, and that evidence digests change when subject/hash/witness changes.
3. Run the focused tests and capture RED.
4. Implement `ContractEvidence` and a versioned subject-binding registry. Rewrite helpers with exact/domain-safe semantics and include the chain-rule check.
5. Update the dashboard to report registered contracts, passed contracts, bound subjects, and unverified declarations separately; remove the 176-declaration/full-verification claim.
6. Run `pytest -q tests/test_foundation_contract_rigor.py tests/test_foundation_backfill.py`.
7. Commit `fix(foundation): bind fail-closed executable evidence to declarations`.

## Task 4: Separate topology from proof-eligible grounding

**Files:** `scripts/compute_foundation_depth.py`, `scripts/foundation_intake.py`, `tests/test_foundation_grounding_rigor.py`, `tests/test_foundation_backfill.py`.

1. Add failing mutation tests where reachability exists only through `HAS_WOUND`, rejected/superseded relations, reverse dependency edges, dangling endpoints, or unverified `RELATED_TO`.
2. Add a positive verified-chain test and a registry-partition test covering `decl:AHLFORS...` nodes.
3. Run focused tests for RED.
4. Implement separate raw and proof-eligible adjacency builders with explicit edge policy and provenance diagnostics. Replace prefix-only corpus accounting with source-ID registry accounting.
5. Run focused tests to GREEN. Commit `fix(foundation): distinguish topology from verified grounding`.

## Task 5: Make reconstruction deterministic and side-effect safe

**Files:** `scripts/io_utils.py`, affected v0.12-v0.19 intake writers, `scripts/reconstruct_pipeline.py`, `tests/test_reconstruction_integrity.py`, evidence/report files.

1. Add failing tests for deterministic gzip bytes, atomic interrupted writes, canonical JSON/newlines, explicit evidence paths, and two identical reconstruction digests.
2. Implement atomic temporary-file replacement and deterministic gzip headers; stop library functions from writing repository evidence unless an explicit evidence path is supplied.
3. Reconstruct into two fresh temporary directories and compare SHA-256 manifests.
4. Regenerate current, nonsealed evidence and documentation. Record corrected counts rather than preserving old thresholds. Verify the v0.11 digest is unchanged.
5. Commit `fix(pipeline): make mathematical evidence reconstruction deterministic`.

## Task 6: Correct claims and CI

**Files:** `README.md`, `docs/FOUNDATION_BACKFILL_REPORT.md`, `docs/V0_19_COMPLEX_ANALYSIS_REPORT.md`, `.github/workflows/foundation-backfill.yml`, `.github/workflows/complex-analysis-v0-19.yml`, evidence JSON.

1. Add tests that reject `100%`/`fully verified` language unless the report denominator and eligible evidence justify it.
2. Update reports with historical-discrepancy tables, raw versus proof-eligible metrics, contract coverage, amendment IDs, and input digests.
3. Make CI regenerate in temporary directories and compare committed evidence byte-for-byte.
4. Commit `docs(ci): publish corrected fail-closed mathematical claims`.

## Final verification

Run:

```bash
pytest -q
python scripts/reconstruct_pipeline.py --out-root /tmp/mapeogeo-rigor-a
python scripts/reconstruct_pipeline.py --out-root /tmp/mapeogeo-rigor-b
sha256sum data/mapeogeo_v0_11_graph.json.gz
git diff --exit-code -- data/mapeogeo_v0_11_graph.json.gz
git status --short
```

Then request an independent mathematical-integrity review. Fix every P0/P1 finding, rerun the complete matrix, push `agent/main-math-rigor-v0-20`, and do not merge it.
