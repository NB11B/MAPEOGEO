# Geometric Qualification Implementation Plan

> For agentic workers: execute the authorized plan continuously with test-first implementation, scoped parallel tasks, and independent final review.

**Goal:** Carry actual NGC/MAPEOGEO operators through a reproducible geometry, reconstruction, and prediction qualification.

**Architecture:** Separate geometric candidate, complex reference, repository adapters, observation/calibration layer, and experiment runner. Source snapshots are immutable and hashed.

**Tech Stack:** Python, NumPy, SciPy, stdlib unittest; Markdown/JSON/CSV evidence.

**Spec:** `docs/superpowers/specs/2026-10-22-geometric-qualification-design.md`.

## Global Constraints

Synthetic evidence stays labeled. Candidate code does not call its oracle. Preserve test failures and source discrepancies. No GPU claim without a GPU run. Hold-out truth never enters calibration or estimation. Complete runnable package; no remote writes.

## Review Focus

Check tensor ordering, metric identifiability, physical-state boundaries, readout assumptions, detector calibration rank, finite-shot estimator bias, local-vs-joint correlations, independent reference construction, exact source provenance, and truthful claim scope.

## Tasks

1. **Source and baseline:** pin actual NGC and MAPEOGEO sources, licenses and hashes; inspect baseline behavior; make import-only adapters and tests. Owner: root with source investigator.
2. **Geometry:** tests first, then real tetrahedral operators and inversion, compatible metric inference, centers, projection/readout, joint coordinates. Owner: geometry worker; files `geometry.py`, `tests/test_geometry.py`, task report.
3. **Complex reference:** tests first, then independent density-matrix and local-gate oracle. Owner: reference worker; files `reference.py`, `tests/test_reference.py`, task report.
4. **Observation pipeline:** tests first, then detector calibration and blind held-out reconstruction/prediction; strict external JSON schema and sample generation. Owner: root; `observations.py`, `tests/test_observations.py`.
5. **Campaign integration:** implement source-backed comparisons, all frozen experiment gates, per-case logs, manifests, deterministic replay, CLI and report; test the full workflow. Owner: root; `campaign.py`, `__main__.py`, integration tests.
6. **Independent review:** spec/code/scientific audit by a separate worker; fix verified issues with regression tests and preserve original evidence.
7. **Delivery:** full test suite, fresh campaign, clean archive extraction/replay, hashes, complete documentation and saved deliverables.

## Progress

See `docs/progress.md`; no task is complete based only on a worker assertion.
