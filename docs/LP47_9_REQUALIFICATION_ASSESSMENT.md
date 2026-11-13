# Theorem 47.9: pagination diagnostic and bounded-contract hardening

This assessment is diagnostic, not acceptance of a new source edition. Original
source-file and statement pins, thresholds, manifests, and Lean declarations
remain unchanged. The mandatory whole-PDF identity guard still fails closed.

## What changed

The accepted PDF was 24,629,575 bytes and 2,204 pages, SHA256
`a1f91e337445851d27f2f4adb61e8ccc0f8fac941f9e0254ad94ba6b91c7c49b`.
The observed PDF is 25,323,685 bytes and 2,238 pages, SHA256
`9c7574c8880b463a113c332ecc80b759d700f8dfe9f6d2e0db6cfbee9ef52af2`.
The three other v0.7 target statement hashes match their original pins.

The v0.6 extractor's 787-character normalized span for Theorem 47.9 includes a
trailing section running header and page number. Changing only that final page
number from 1655 to the baseline graph's 1621 reproduces the accepted statement
SHA256 exactly. Independent review reproduced both hashes. Under standard
SHA256 collision resistance this establishes equality of the normalized span
apart from that page token, including the theorem's wording and assumptions.
It does not establish raw-PDF equality, equivalence of other declarations, or
whole-edition qualification. The historical PDF was subsequently recovered privately from an existing archive
snapshot and its original identity verified; see the accepted-edition replay
in `TESTING.md`. This diagnostic remains a separate record of the changed live
edition, not a qualification of that edition.

`evidence/lp47_9_pagination_diagnostic_v1.json` records only hashes and metadata.
`scripts/audit_lp_pagination_binding.py` implements the deliberately narrow
`LP47_9_TRAILING_RUNNING_HEADER_PAGE_V1` diagnostic. It requires the exact
terminal running header and explicit page metadata; it does not strip arbitrary
numbers or mathematical content. It is not called by any qualification gate.
The raw historical and observed hashes remain the authoritative raw identities.

For replay, use the unchanged v0.6 `v05.extract_line_stream` and
`statement_text_candidates` on the observed PDF; select Theorem 47.9, and pass
its normalized `statement_text` to `audit_span` with the accepted hash from
`data/mapeogeo_v0_11_graph.json.gz`, current page end 1655 and accepted page end
1621. The helper returns no source prose. The checked-in diagnostic records the
exact baseline graph hash. Never redistribute the transient PDF or source text.

## What the executable contract establishes

The source theorem describes four-case duality for general finite-dimensional
linear programs. The existing Python contract enumerates only 2,457 positive
one-variable rational instances: one to three constraints and coefficients in
{1,2,3}. Previously it checked an arithmetic identity that also held when a
wrong constraint supplied an infeasible candidate optimizer.

The strengthened checker preserves that enumeration and verifies exact rational
primal feasibility, dual feasibility, nonnegative witnesses, and equality of
objectives. By weak duality these conditions certify the particular bounded
instances. A mutation selecting the largest rather than smallest ratio now
fails. The explicit counterexample a=(1,1), b=(1,2), c=1 with x=2 formerly passed
objective equality despite violating the first primal constraint.

The Lean declaration remains a separate scoped result: existence of a primal
maximum with one scalar positive constraint and nonnegative b,c. Neither this
Lean result nor the bounded Python checks prove the source's full four-case
theorem. No such stronger claim is made here.

## Remaining requalification work

A new edition requires its own reviewed preregistration and corpus-wide replay,
not replacement of the old acceptance pins. Holdout edges already changed from
126 to 123. Preserve the old baseline, audit changes beyond these four targets,
and keep the source guard and all existing thresholds. Authentic missing Python
dependencies and import-root conflicts remain separate CI blockers.
