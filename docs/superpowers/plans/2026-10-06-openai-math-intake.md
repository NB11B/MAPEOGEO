# Complete OpenAI Math Intake Implementation Plan

> **For agentic workers:** Use subagent-driven-development or executing-plans to implement these tasks. User authorized the complete repository intake.

**Goal:** Add every upstream resource and its extracted source structure to the current MAPEOGEO graph.

**Architecture:** A conservative lexical scanner feeds a streamed additive graph writer. Repository/catalogue/configuration metadata bind every record to a frozen source revision; existing mathematical and proof registries remain intact.

**Tech Stack:** Python, Git, gzip JSON, pytest, PyYAML, ijson for streamed audits.

**Spec:** `docs/OPENAI_MATH_INTAKE_DESIGN.md`

## Global Constraints

- Source commit: adc7f1241b42e322a6451854ab7e4b4c146bf78a.
- Preserve historical graph payloads and zero-prose persistence.
- No proof, semantic equivalence, or kernel promotion from source ingestion.
- Every tracked file must receive a disposition, including binary/support files.
- Source declarations are lexical candidates until separately admitted.
- Stream the several-million-record import and write deterministic atomic output.

## Review Focus

- Comments/string literals must not create spurious Lean declarations.
- Unicode must preserve byte locators and hashes.
- The full tree and the catalogue have different coverage denominators.
- Dirty/mismatched source content must fail its Git/SHA-256 binding.
- Existing graph identities and proof statuses must survive unchanged.

## Task 1: Source scanner

Files: `mapeogeo/openai_math_source.py`, `tests/test_openai_math_source.py`.

Interface: `scan_source(path: str, data: bytes) -> dict` returning
`records`, `references`, `disposition`, and `diagnostics`.
Each record contains `kind`, `name`, `start_byte`, `end_byte`, `start_line`,
`end_line`, `span_sha256`, `header_sha256`, and optional `qualified_name`.
No raw source strings are returned. References have `kind`, `target`,
`start_line`, and optional `record_start_byte`.

- [x] Write failing tests for real source syntax, comments, Unicode, source spans,
      explicit imports/TeX references, and unknown-format dispositions.
- [x] Implement bounded lexical extraction; do not claim elaborated Lean identity.
- [x] Run focused scanner tests and review the actual-source scan dispositions.

## Task 2: Streamed complete graph intake

Files: `scripts/openai_math_intake.py`, `tests/test_openai_math_intake.py`,
`formal/openai_math_source_pin.json`.

Interface: CLI `--source-repo PATH --base-graph PATH --out-dir PATH`.
Use Git's frozen tree as exact resource inventory, validate source bytes,
parse catalogue/configuration records, scan all source files, and stream
the merged graph plus resource manifest and coverage report.

- [x] Write failing tests for pin/content mismatch, source coverage, collision,
      historical preservation, recursive zero-prose, and nonpromotion.
- [x] Implement deterministic IDs, additive merge, references and deficits.
- [x] Reconstruct foundation and execute the entire source import.
- [x] Audit serialized graph endpoints, counts, hashes and preserved base.

## Task 3: Integration and delivery

Files: `scripts/reconstruct_pipeline.py`, `README.md`,
`docs/OPENAI_MATH_INTAKE.md`, new workflow and test requirements as needed.

- [x] Add the final source intake target while retaining existing targets.
- [x] Verify repeatability and run the existing relevant integrity suites.
- [x] Obtain independent source/schema/code review and resolve findings.
Delivery: commit code/evidence, open a reviewable change, and provide the complete graph.
