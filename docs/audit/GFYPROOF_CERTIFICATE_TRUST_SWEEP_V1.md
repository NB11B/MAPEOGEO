# GFYProof Certificate Ingestion Trust Sweep v1

Status: known critical gap documented on audit branch.

## Finding

The current MAPEOGEO bridge schema v2 provides strong envelope integrity but does not provide independent proof authenticity.

MAPEOGEO validates certificate digest, endpoint identities, claim digest, verifier/edge-family compatibility, producer field shapes, proof verdict, and a SHA-shaped proof payload digest.

It does not receive or replay the proof payload.

The producer repository and commit are data inside the same self-hashed certificate; they are not an independent signature or trust root.

Therefore a caller can construct a structurally valid PASS envelope without presenting the mathematical proof that allegedly produced it.

## Why this matters for neural mathematical search

A neural or heuristic proposer must never be able to cross the graph authority boundary by manufacturing certificate metadata.

The intended trust chain is:

    candidate proposal
        -> source-grounded endpoint payloads
        -> GFYProof relation verifier
        -> replayable proof bundle
        -> independent MAPEOGEO validation
        -> graph promotion

Certificate metadata alone is insufficient.

## Certificate v3 requirement

A replacement protocol should require one of:

1. independent MAPEOGEO-side replay of a full proof payload through a trusted verifier plugin; or
2. a cryptographically authenticated GFYProof attestation with a trust root outside the certificate itself.

For local scientific work, independent replay is preferred because it also detects GFYProof-side implementation mistakes.

## Required tests

- valid replayable proof promotes;
- envelope-only PASS refuses;
- proof payload digest mismatch refuses;
- verifier result mismatch refuses;
- unrelated endpoint relation refuses;
- producer-field spoofing refuses;
- endpoint mutation refuses;
- certificate mutation refuses;
- replay under a second implementation agrees on verdict where available.

The strict-xfail audit test in tests/audit/test_gfyproof_ingestion_known_gap.py encodes the first missing gate.
