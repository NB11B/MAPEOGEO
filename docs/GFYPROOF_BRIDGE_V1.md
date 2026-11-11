# GFYProof Bridge v1

## Role

GFYProof is integrated as an independent executable verifier for MAPEOGEO.

The bridge has two return channels:

1. **Executable evidence enrichment** — a verified GFYProof result is attached as an `EXECUTABLE_EVIDENCE` node without changing source identity.
2. **Proof-eligible relation promotion** — only supported proof families may materialize registered edge evidence for an existing MAPEOGEO relation.

The second channel is deliberately narrower.

## Why this matters

MAPEOGEO currently distinguishes raw graph reachability from proof-eligible grounding. Raw paths are not proofs. Proof grounding requires validated roots and endpoint-bound registered edge evidence.

GFYProof now has a deterministic certificate stack capable of producing that missing edge evidence for selected relation families.

This permits GFYProof to help fill MAPEOGEO in a way that remains compatible with the existing mathematical-integrity rules.

## Certificate binding

A bridge certificate is bound to:

- exact endpoint node IDs;
- exact endpoint full-node SHA-256 identities;
- relation type;
- claim scope;
- GFYProof proof family;
- proof-payload digest;
- GFYProof commit;
- verifier ID;
- certificate digest.

A certificate is invalid after either endpoint changes.

## Initially authorized proof families

| GFYProof family | MAPEOGEO relations |
|---|---|
| E085 DFA equivalence | `REPRESENTS`, `SAME_SEMANTICS` |
| E091 ROBDD equivalence | `REPRESENTS`, `SAME_SEMANTICS` |
| E093 Farkas implication | `UPWARD_FOUNDATION_DEPENDENCY`, `PROOF_DEPENDENCY` |
| E094 polynomial ideal membership | `UPWARD_FOUNDATION_DEPENDENCY`, `PROOF_DEPENDENCY` |

The mapping is closed and fail-closed.

## Graph materialization

A successful proof-eligible certificate produces:

- one existing-type mathematical relation edge with registered evidence;
- one `EXECUTABLE_EVIDENCE` node recording the GFYProof certificate;
- one `EXECUTABLE_EVIDENCE_FOR` attachment edge.

The registered evidence contract digest incorporates the GFYProof certificate digest, so a different proof certificate produces a different MAPEOGEO evidence identity.

## Non-promotion rules

GFYProof output does not create or imply:

- `SOURCE_DECLARATION`;
- source authorship;
- source statement identity;
- `FORMAL_LINKED`;
- `KERNEL_VERIFIED`.

New mathematical objects produced by future GFYProof discovery must remain explicitly derived/candidate objects until MAPEOGEO's normal source/canonical identity process promotes them.

## First integration gate

The bridge test constructs a synthetic graph whose proof-eligible grounding is initially zero.

After ingesting:

    source root
      -> GFYProof-certified REPRESENTS
      -> foundation canonical object
      -> GFYProof-certified UPWARD_FOUNDATION_DEPENDENCY
      -> advanced canonical object

the existing `compute_foundation_metrics` implementation reports one proof-grounded advanced object.

No grounding rule is bypassed or special-cased.

Mutation tests require rejection of:

- changed endpoint identity;
- forged producer repository;
- tampered certificate body;
- unsupported proof family;
- proof-family / relation-type mismatch.

## Backfill strategy

The first real campaign should target existing MAPEOGEO objects rather than inventing new source claims.

Priority:

1. executable foundation declarations already carrying exact contracts;
2. existing EO/GEO dual representations with exact finite semantics;
3. existing linear/convex/algebraic relationships that map to E093/E094;
4. existing proof paths with a small number of missing registered edges;
5. evidence-only enrichment for objects that cannot yet support a promotable relation certificate.

This lets the proof-eligible grounding numerator rise only when GFYProof has actually closed the missing certificate chain.

## Repository-local replay and CI

The bridge now independently replays the following bounded payload families in
`mapeogeo/gfyproof_replay.py`, without downloading the private GFYProof engine:

- Boolean equivalence: exhaustive truth assignments for the `var`, `not`, `and`
  and `or` expression subset of `GFY.ROBDD_EQUIVALENCE.v1`. This is not an ROBDD
  implementation or a claim of identical acceptance behavior.
- Farkas implication: exact rational nonnegative multipliers, `lambda A = c`
  and `lambda b <= d`. Only implication certificates are supported locally.
- The eight frozen v0.3 fixture families: cyclic group composition, SO(3),
  eigenpairs, graph Laplacian equivalence, projective homogeneous equivalence,
  one-dimensional LP duality, orthogonal projection and Gaussian-kernel PSD.

Exact arithmetic accepts integers and rational strings, not silently truncated
floats. SO(3), eigenpairs, projection and Gaussian PSD are explicitly numerical
checks, not exact or kernel-verified proofs. Numerical absolute tolerances cannot
exceed 1e-6 (1e-12 for PSD), and approximate inputs are finite with magnitude at
most 1e6. Local replay intentionally rejects unsupported shapes and workloads:
10 Boolean variables, depth 32, 256 expression nodes, matrices up to 32x32,
512-bit rational components, 10,000 LP grid cases and cyclic order up to 10,000.
Projective replay requires an invertible matrix; Gaussian variance is at least
1e-6. These limits are conservative, not a complete implementation of GFYProof.

Unknown semantic IDs remain rejected. Registered families outside the local
subset still require `math2.bridge.mapeogeo`; an absent engine is an error, never
an automatic PASS. A rejected local proof is not retried against a more permissive
external backend. Evidence records identify `MAPEOGEO_LOCAL_FINITE_V1` versus
`GFYPROOF_EXTERNAL` separately from the certificate's claimed producer.

When endpoint semantic contracts exist, the certificate's semantic ID, endpoint
roles and replay payload must match one common contract and its payload hash.
An unrelated true payload cannot replace that bound witness. Incomplete contract
metadata cannot override endpoint checks. Reapplying the same certificate to an
already promoted candidate preserves its original metadata and is idempotent.

Trust limits remain explicit: certificate hashes provide integrity, not producer
authentication. A claimed repository or commit is not a cryptographic signature.
Legacy source-hash-only endpoints do not themselves prove correspondence between
natural-language statements and the supplied mathematical payload. Callers must
establish that correspondence and trust the graph/overlay provenance; this repair
does not solve arbitrary statement formalization or promote new source identities.

The required CI command is runnable from a clean checkout:

```bash
python -m pip install pytest numpy pandas sympy scipy pymupdf
python -m pytest -q \
  tests/test_gfyproof_bridge.py \
  tests/test_gfyproof_replay.py \
  tests/test_gfyproof_real_demorgan_roundtrip.py \
  tests/test_foundation_grounding_rigor.py \
  tests/test_gfyproof_endpoint_contracts_v03.py \
  tests/audit/test_gfyproof_ingestion_known_gap.py
python scripts/reconstruct_pipeline.py --target-stage foundation
python -m pytest -q tests/test_gfyproof_farkas_endpoint_contracts.py
```

The local De Morgan integration case uses real foundation declarations and a
synthetic certificate envelope, replays its detached payload and promotes only
the supported edge. It does not increase advanced grounding through an unverified
upward dependency. A separate optional case invokes the real GFYProof producer
when installed and is explicitly skipped otherwise. Neither case implies a Lean
kernel check. The audit suite rejects rehashed false proofs, missing/mismatched
payloads, unsupported semantics, incomplete/mismatched endpoint contracts and
collisions, and checks atomic rejection, non-promotion and idempotence.
