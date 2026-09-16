# MAPEOGEO v0.21 Rigor-First Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a large body of real foundational and connective-advanced mathematics as exact source-bound declarations while preventing invented provenance and automatic semantic promotion.

**Architecture:** A pinned source registry drives deterministic transient Git checkouts. Structured PreTeXt and LaTeX parsers extract theorem-like declarations into zero-prose metadata; a graph intake appends provenance-only source nodes in canonical quarantine. Semantic relations remain unchanged unless a separate endpoint-bound contract exists.

**Tech Stack:** Python 3.12, standard-library `xml.etree.ElementTree`, `subprocess` Git, SHA-256, JSON/gzip deterministic I/O, pytest, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-16-rigor-first-expansion-design.md`

## Global Constraints

- Never persist source statement/proof prose in graph or evidence artifacts.
- Every upstream source is pinned to an exact 40-character commit SHA.
- No v0.21 source declaration may auto-emit semantic, formal, executable, or kernel-verified status.
- Extraction and graph integration fail closed on duplicate identities, revision mismatch, parser errors, or forbidden persisted keys.
- Existing v0.20 sealed inputs are immutable.
- Mathlib remains a verifier, never a source corpus.

---

### Task 1: Pinned source registry and schema validator

**Files:**
- Create: `formal/source_registry_v0_21.json`
- Create: `scripts/source_registry_v0_21.py`
- Create: `tests/test_source_registry_v0_21.py`

**Interfaces:**
- Produces `load_source_registry(path: Path) -> list[SourceSpec]`
- Produces `validate_source_registry(specs: list[SourceSpec]) -> None`

- [ ] **Step 1: Write failing tests** asserting five expected source IDs, exact 40-character SHAs, allowed parser kinds only, immutable repo URLs, explicit licenses, and rejection of branch refs in revision fields.
- [ ] **Step 2: Run** `pytest tests/test_source_registry_v0_21.py -v` and confirm failure because module/registry do not exist.
- [ ] **Step 3: Implement** dataclass/schema validator and the five pinned source records from the design spec.
- [ ] **Step 4: Re-run** the test and require PASS.
- [ ] **Step 5: Commit** `test/feat(v0.21): add pinned source registry contracts`.

### Task 2: Deterministic structured declaration parsers

**Files:**
- Create: `scripts/structured_source_parsers_v0_21.py`
- Create: `tests/test_structured_source_parsers_v0_21.py`

**Interfaces:**
- Produces `extract_pretext_declarations(root: Path, spec: SourceSpec) -> list[ExtractedDeclaration]`
- Produces `extract_latex_declarations(root: Path, spec: SourceSpec) -> list[ExtractedDeclaration]`
- `ExtractedDeclaration.to_metadata()` must omit source text.

- [ ] **Step 1: Write failing PreTeXt tests** using synthetic XML with `<definition>`, `<theorem>`, `<statement>`, and `xml:id`; assert stable IDs/hashes/lineage and zero prose.
- [ ] **Step 2: Write failing LaTeX tests** using synthetic theorem environments with labels, aliases, comments, CRLF normalization, unlabeled fallback IDs, and malformed unbalanced environments.
- [ ] **Step 3: Run** `pytest tests/test_structured_source_parsers_v0_21.py -v` and confirm RED.
- [ ] **Step 4: Implement minimal parsers** with deterministic normalization and forbidden-key filtering.
- [ ] **Step 5: Re-run** parser tests and require PASS.
- [ ] **Step 6: Commit** `feat(v0.21): add deterministic structured source parsers`.

### Task 3: Pinned transient source fetcher and admission engine

**Files:**
- Create: `scripts/source_admission_v0_21.py`
- Create: `tests/test_source_admission_v0_21.py`

**Interfaces:**
- Produces `checkout_pinned_source(spec: SourceSpec, workspace: Path) -> Path`
- Produces `admit_sources(registry_path: Path, workspace: Path) -> AdmissionResult`

- [ ] **Step 1: Write failing tests** for SHA mismatch, duplicate `(source_id, structured_id)`, duplicate node IDs, unsupported parser type, forbidden prose persistence, and deterministic sort order.
- [ ] **Step 2: Run** targeted tests and verify RED.
- [ ] **Step 3: Implement** transient `git init` + remote + depth-1 fetch of the exact SHA, detached checkout, HEAD verification, parser dispatch, collision checks, and zero-prose metadata emission.
- [ ] **Step 4: Re-run** targeted tests and require PASS.
- [ ] **Step 5: Commit** `feat(v0.21): add fail-closed source admission engine`.

### Task 4: Quarantined graph intake

**Files:**
- Create: `scripts/rigor_expansion_v0_21.py`
- Create: `tests/test_rigor_expansion_v0_21.py`

**Interfaces:**
- Consumes accepted foundation/v0.20 graph plus `AdmissionResult`.
- Produces `artifacts/rigor_v0_21/mapeogeo_v0_21_graph.json.gz` and `source_admission_report.json`.

- [ ] **Step 1: Write failing tests** asserting new nodes are `SOURCE_DECLARATION`, carry exact provenance, have `canonical_status=UNRESOLVED`, `formal_status=UNFORMALIZED`, `executable_status=UNTESTED`, and emit provenance containment edges only.
- [ ] **Step 2: Add negative tests** proving no v0.21 node participates in `SAME_SEMANTICS`, `SCOPED_OVERLAP`, `RELATED_TO`, `FORMAL_LINKED`, `KERNEL_VERIFIED`, or `PROOF_DEPENDENCY` without an explicit endpoint-bound contract.
- [ ] **Step 3: Run** tests and verify RED.
- [ ] **Step 4: Implement** deterministic source-root/declaration insertion and provenance-only edges using existing deterministic I/O helpers.
- [ ] **Step 5: Re-run** targeted tests and require PASS.
- [ ] **Step 6: Commit** `feat(v0.21): integrate quarantined source declarations`.

### Task 5: Real upstream integration and exact-count freeze

**Files:**
- Create: `tests/test_v0_21_real_source_integration.py`
- Create: `evidence/v0_21_source_admission_manifest.json` after first successful run.

**Interfaces:**
- Integration test invokes actual pinned Git repositories.

- [ ] **Step 1: Write the integration test** to fetch all five exact commits, require nonzero admissible declarations per source, require zero persisted prose, and produce a temporary count/fingerprint manifest.
- [ ] **Step 2: Run** it in CI/networked environment and inspect the first successful extraction counts; do not guess counts.
- [ ] **Step 3: Commit the observed exact counts and canonical parser fingerprints** to `evidence/v0_21_source_admission_manifest.json`.
- [ ] **Step 4: Tighten the integration test** to require exact equality to the committed manifest on every replay.
- [ ] **Step 5: Re-run** and require PASS.
- [ ] **Step 6: Commit** `test(v0.21): freeze real source admission identities`.

### Task 6: Reconstruction and CI integration

**Files:**
- Modify: `scripts/reconstruct_pipeline.py`
- Create: `.github/workflows/rigor-expansion-v0-21.yml`
- Modify: `README.md`
- Create: `docs/V0_21_RIGOR_FIRST_EXPANSION_REPORT.md`

**Interfaces:**
- `python scripts/reconstruct_pipeline.py --target-stage v0.21`

- [ ] **Step 1: Write/extend tests** so `v0.21` is a recognized target and sealed v0.20 inputs are unchanged after reconstruction.
- [ ] **Step 2: Verify RED** before reconstruction code is changed.
- [ ] **Step 3: Add the v0.21 reconstruction step** after the accepted foundation/v0.20 baseline.
- [ ] **Step 4: Add CI** that installs dependencies, reconstructs v0.21, runs the full pytest suite, verifies exact source counts/fingerprints, and checks zero drift of v0.20 sealed inputs.
- [ ] **Step 5: Update README/report** with only observed counts; explicitly state that v0.21 increases source coverage while canonical status remains unresolved unless separately contracted.
- [ ] **Step 6: Run full verification**: `pytest -q` and `python scripts/reconstruct_pipeline.py --target-stage v0.21`.
- [ ] **Step 7: Commit** `feat(v0.21): complete rigor-first source expansion`.

### Task 7: Final verification and branch completion

- [ ] **Step 1: Freshly verify** full tests, clean reconstruction, deterministic artifact hashes, source-count manifest equality, no semantic auto-promotion, and zero v0.20 input drift.
- [ ] **Step 2: Push feature branch** and inspect the authoritative GitHub Actions run.
- [ ] **Step 3: Do not merge on partial or infrastructure-only evidence.** Merge only after the required v0.21 integrity job is green.
