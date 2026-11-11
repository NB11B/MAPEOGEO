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
