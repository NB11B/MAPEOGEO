# v0.20 macro authority boundary

Macro proposals are calibration-derived search hints. They are not solver
authority and are never evaluated on the authoritative `solve()` path.

The current proposal schema does not bind all information required for a sound
runtime certificate:

- the complete executable closure, including referenced globals and transitive
  dependencies;
- the exact runtime goal, routing configuration, registry, and search budget;
- a replay ledger with typed applicability, execution, verifier, lineage, and
  work receipts.

For that reason production replay and efficiency credit are disabled
fail-closed. `solve(..., macros=...)` returns the exact primitive trace and does
not iterate the supplied macro object. `audit_macro_proposals()` is an optional
post-solve side channel; it executes no proposal, grants no credit, claims zero
actual savings, and charges the complete primitive work ledger.

The standalone `macro_certification.py` experiment is not imported by the
planner and does not grant production authority. Its certificates and replay
assessments are diagnostic artifacts only.

Future replay may be enabled only after an exact typed certificate, request,
registry, configuration, and budget binding is implemented and a replay is
shown to preserve the full canonical candidate, verdict, refusal identity,
obligation multiset (including witnesses), verifier/routing/lineage receipts,
and complete work counters. The primitive trace must still remain authoritative
and total observed work must charge both baseline and replay. Any smaller replay
search may be reported only as counterfactual compression, never as actual
runtime savings.
