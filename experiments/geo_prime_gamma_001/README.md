# GEO-PRIME-GAMMA-001 — Compact permutation-group invariant

For a verified finite group G with at least two elements, define Gamma(G)=min(ord(g):g!=e)/|G|. Standard Lagrange and Cauchy theorems imply Gamma(G)=spf(|G|)/|G|, so Gamma(G)=1 iff the group order is prime. No new primality theorem or algorithmic speedup is claimed.

The Python implementation accepts a **complete, faithful permutation group**, validates the identity, uniqueness, permutation bijections, and composition closure before computing the scalar. It refuses incomplete or non-group input. The independent spf formula is used **only as a reference after calculating permutation orders**. The method therefore does not infer G from mixed, unlabelled observations. Tests: 11/11 local, includes n=2..40 cyclic groups; C9, C12, V4, S3, D4; input/refusal controls. C4 and V4 have the same scalar gamma=1/2 but different order signatures: this scalar is not a complete structural invariant.

Reproduce: `cd experiments/geo_prime_gamma_001 && python -m unittest discover -v && python gamma.py`.

Next: formal Lean theorem for arbitrary finite groups with explicit finite/card≥2 hypothesis; connect to PSMSL operator closure certificates; preservation under faithful conjugation; prospective tests under mixed stream observations and identifiability refusal.
