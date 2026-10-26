# GEO-PRIME-UNIVERSAL-003: opaque operator-family qualification

Given a complete family of unlabeled permutation operators over n vertices, infer whether it forms a cyclic group of order n and whether all nonidentity operators have a single full-length orbit. Neither vertex labels nor operator step sizes are supplied. Classification is compared only after inference with an independent primality oracle.

**Sandbox qualification (2026-10-25):** 10/10 corrected tests passed; n=2..35 yielded 0 classification disagreements. Joint vertex permutation does not affect the result. Incomplete and duplicate operator families, a noncyclic Klein-four action, non-permutation transitions, and a single full-cycle operator are refused. For n=9, the classifier identifies a three-cycle partition witness.

**Original failure preserved conceptually:** first generator incorrectly relabeled only outputs rather than conjugating input/output relations; it failed 2 of 10 tests. Corrected fixture conjugates every transition consistently. That failure does not represent a discovered counterexample.

**Trust boundary:** The complete cyclic permutation family is supplied, and the algorithm searches its closure and orbit partitions. This is *not* unknown-operator discovery from arbitrary time series, and n is still observable as the number of vertices. No prime labels, gcd, division, or step indices enter classification. The resulting result is a computational embodiment of the existing Lean-verified cyclic-prime characterization, not a new mathematical theorem or superior prime algorithm.

Run: `cd experiments/geo_prime_universal_003 && python -m unittest discover -v && python discovery.py`.

Next gates: recover missing family members from generators under bounded closure; distinguish complete evidence from insufficient observations; simulate timestamped transitions with latent labels, and require refusal under observationally equivalent models.
