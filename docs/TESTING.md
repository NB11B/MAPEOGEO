# Test contexts and reproducibility

## MAPEOGEO regression checks

The GFYProof Bridge workflow runs the local replay, ingestion audit, endpoint
binding and real-foundation integration checks, reconstructs the foundation
graph, and checks Farkas bindings. It also exercises the supporting import,
CLI, pinch-intake orchestration and integrity-provenance regressions. See
`.github/workflows/gfyproof_bridge_v1.yml` for the exact commands and dependencies.

The root test suite can be inspected without hiding collection failures:

```bash
python -m pytest -q tests --continue-on-collection-errors
```

This command still exits nonzero if any test fails to collect. At the time of
this repair, `tests/test_bcig_sovctx_integration.py` cannot import
`bcig.ontology.adaptive_closure` and `bcig.ontology.descendant_state`. Those source
modules are not included in this checkout. Their authoritative implementations
and provenance must be restored before claiming the root suite is green; the
stored BCIG audit output is not a substitute for executable source.

The experimental intelligence adapter separately requires the `intel_uow`
reference package at the location declared in
`experiments/intelligence_integration/v0_1/adapter.py`. Clock and contract helpers
are independent of that optional adapter. Explicit adapter use still fails if
the reference runtime is absent, instead of returning a fabricated result.

## Simulated orchestration versus actual proof verification

The pinch-intake tests use a clearly labeled temporary simulated `lake` process
to exercise graph transitions on synthetic fixtures. They test both acceptance
and refusal, including missing/failed-kernel behavior despite checker overrides.
All simulated certificates remain in pytest temporary directories. These tests
do not run Lean and do not constitute mathematical proof evidence.

Actual pinned Anthropic Lean compilation, axiom inspection, comparator and
nanoda checks run in `.github/workflows/anthropic-eth-proof.yml`. Passing the
Python orchestration tests must never be described as passing those checks.

The v0.11 intake workflow in `.github/workflows/math-intake-v0-11.yml`
runs unrestricted root `pytest` and real source/proof verification as separate,
independent jobs. Python discovery failures stay visible and fail qualification,
but cannot prevent the separate source/proof job from starting. That job builds
Lean and runs leanchecker before downloading the source and regenerating
v0.6–v0.11 evidence. After v0.9 regeneration and validation, the source-binding
audit receives that exact fresh graph via `--graph`; an existence check prevents
the auditor from falling back to an older checked-in graph. This audit checks
graph identities, detector states and dependencies, not the PDF argument that its
CLI ignores. All audits and downstream validators remain required and stop the
job on failure; moving Lean earlier does not certify those gates. The original
`math-intake-v0-11` check succeeds only when **both** jobs succeed; failure,
cancellation or a skipped dependency does not qualify evidence. Preserve that
aggregate check in branch protection.

The pinned Lean action alone sets `LEAN_NUM_THREADS: "1"` to reduce concurrent
module replay. This is a resource-pressure experiment after repeated hosted
runner shutdowns, not a proven fix or evidence of out-of-memory failure. The
checker, complete default project module discovery, required source/proof checks,
and fail-closed qualification are unchanged. Local workflow regressions do not
establish that hosted Lean verification now completes.

Only the proof job builds Lean. It transfers derived v0.11 output through a
one-day `mapeogeo-pinch-intake-v0.11-unqualified-<run attempt>` staging artifact.
This staging artifact can exist after a Python failure and is **not qualified
workflow evidence**. The aggregate downloads the exact artifact ID emitted by
the successful proof job, so rerunning only failed jobs does not accidentally
look for evidence under a new run-attempt name. Missing or malformed artifact IDs
fail qualification rather than letting the downloader select unrelated artifacts.
The original `mapeogeo-pinch-intake-v0.11` artifact is
published only after both jobs pass. This transfer avoids a second expensive
proof build; it uploads neither the transient source PDF nor the Lean build tree
and does not rewrite generated certificate contents or hashes.

The legacy best-effort leanchecker log-collection command is unchanged. Its log
is not an additional trusted validation; the required pinned Lean action still
performs the build and kernel-replay checker before downstream evidence generation.
Lean's bundled leanchecker detects environment manipulation; it is not an external
verifier.
The workflow regression tests inspect job dependencies, preserved scientific
commands and artifact routing, and execute the real aggregate shell gate for all
success/failure/cancelled/skipped/missing-result combinations. They are included
in the GFYProof supporting regressions and can be run independently:

```bash
python -m pip install pytest 'pyyaml>=6,<7'
python -m pytest -q tests/test_math_intake_workflow.py
```

The integrity report is generated rather than edited by hand:

```bash
python scripts/generate_mathematical_integrity_report.py \
  --out evidence/v0_20_mathematical_integrity_report.json
python -m pytest -q tests/test_mathematical_integrity_provenance.py
```

The generator validates the scientific body before refreshing the current
producer-file provenance. A refreshed file inventory is not a new scientific
result or a new kernel-verification claim.

## Geometry Lab and pinned upstream code

Geometry Lab is a separate package with a vendored package also named
`mapeogeo`. Run its documented suite from its own project directory, not inside
a single root pytest discovery process that mixes both package identities:

```bash
cd ngc_geometry_lab
python -m pip install -r requirements.txt
python -W error -m unittest discover -s tests -v
```

The original pinned upstream suites are retained byte-for-byte. Their isolated
collection commands, using the same absolute Python executable, are:

```bash
PYTHON="$(command -v python)"
(cd ngc_geometry_lab/ngc_geometry_lab/_vendor/mapeogeo && \
  "$PYTHON" -m pytest --collect-only -q --confcutdir=.)
(cd ngc_geometry_lab/ngc_geometry_lab/_vendor/ngc_real && \
  "$PYTHON" -m pytest --collect-only -q --confcutdir=.)
```

Run these subshell commands from the repository root. The upstream
MAPEOGEO snapshot deliberately retains one known incorrect assertion; Geometry
Lab's existing baseline runner records that failure with exact hash/location
checks and an independent countercalculation. See its README and
`ngc_geometry_lab/docs/RELEASE_VERIFICATION.md`. Do not replace pinned vendor
sources, globally redirect imports or broadly suppress tests to manufacture a
green monolithic pytest run.

## Accepted source identity and upstream drift

The v0.11 replay now checks the downloaded PDF against the SHA-256 and byte
count in `evidence/v0_7_acceptance_manifest.json` before regenerating v0.6.
A mismatch stops reconstruction explicitly; it does not change the accepted
statement bindings or lower the four-certificate threshold. Real Lean checking
still runs independently before source acquisition.

On 2026-11-12, the upstream URL served SHA-256
`9c7574c8880b463a113c332ecc80b759d700f8dfe9f6d2e0db6cfbee9ef52af2`
(25,323,685 bytes, 2,238 pages), rather than accepted SHA-256
`a1f91e337445851d27f2f4adb61e8ccc0f8fac941f9e0254ad94ba6b91c7c49b`
(24,629,575 bytes, 2,204 pages). Fresh extraction found that Theorem 47.9's
statement hash differs from its accepted binding. The other three target
statement hashes match; all four recognizers and executable contracts pass.
That explains the three-of-four certificate result without treating it as a
mathematical counterexample. The guard deliberately does not accept the new
source merely because its bounded contract passes.

Reproducing the accepted campaign requires the exact original source bytes.
Using a new edition requires a separate reviewed requalification of source
bindings and downstream evidence; do not overwrite historical acceptance
manifests or substitute hashes to obtain a green run. No source PDF is committed
or uploaded by this change.

### Replaying the accepted source edition

The accepted PDF was recovered from the Internet Archive snapshot dated
2025-04-29 16:25:47 UTC. The v0.11 workflow now retrieves that existing archived
copy directly into `RUNNER_TEMP`, rather than downloading the changed live
edition. The original SHA256 and byte-count guard remains mandatory before any
source processing. Retrieval is not permission to repost the book: the PDF must
not be committed, cached, or uploaded as an artifact. The existing `always()`
cleanup removes the runner's transient copy. Only derived, prose-free evidence
is eligible for the existing artifact stages, and the aggregate Python/proof
gate remains unchanged. Archive outages or incorrect bytes fail closed.

The extraction dependency is pinned to PyMuPDF 1.28.2, the version recorded in
the original accepted CI run. With identical source bytes, local 1.26.6 produced
636 resolved references and failed the unchanged minimum of 638. Version
1.28.2 reproduced v0.6 exactly: 1,355 declarations, 638 resolved references,
66 unresolved references. v0.7 and both artifact validators passed, with all
reported baseline retrieval/filter metrics exactly matching acceptance:
126 holdout edges, 4/4 original-hash certificates, 2 SAME_SEMANTICS promotions,
recall 0.8888888888888888, reduction 0.36026705118285623, and graph 2226/23305.
The strengthened bounded LP witness checker was used in that replay.

This local replay verifies v0.6/v0.7 source qualification only. It does not stand
in for a new hosted Lean run or resolve unrelated full-Python collection errors.
No source-file pin, statement binding, or scientific threshold was changed.
