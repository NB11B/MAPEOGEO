# Erdős #19 Replayable Generation Ledger v10

v10 replaces repeated labeled-universe rediscovery with durable local generation
state.

For every partial canonical node, the ledger records every admissible line
augmentation and classifies it as:
- ACCEPT: first child encountered for that exact canonical child digest;
- DUPLICATE: an augmentation whose child canonicalizes to an already accepted
  child digest.

Each node is sealed by a SHA-256 digest over its complete decision table.
The full ledger manifest binds every node digest to its node seal.

Replay recomputes every admissible augmentation, canonical child digest,
disposition table, node seal, and global manifest.  A missing augmentation,
changed disposition, altered child, or tampered manifest fails replay.

Independent brute-force exact-cover enumeration remains in qualification tests
for n=3,4; once ledger semantics are qualified, larger runs can verify local
branch accounting without rediscovering the full labeled universe.
