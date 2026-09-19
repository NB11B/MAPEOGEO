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