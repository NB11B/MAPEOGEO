# GEO-PRIME-UNIVERSAL-006 — unlabeled exact-cover operator inference

No operator identity or k index is given. Given an aggregate multiset of directed transitions on n observable vertices, enumerate all n-element subfamilies of permutation actions, require matching observations and closure under composition, then report all distinct order signatures. For C4/V4 both groups fit exactly, so the result is ambiguous (four labeled completions, two abstract signatures), never forced cyclic. n=3 has a single signature. The hypothesis class assumes a complete regular action, n operators, every source–target pair exactly once. Reject missing and conflicting evidence, and bound n to four because brute force is factorial/combinatorial.

Local execution: 5/5 unit tests passed. This is bounded identifiability analysis, not scalable unsupervised discovery or novel primality mathematics.

Run: `cd experiments/geo_prime_universal_006 && python -m unittest discover -v && python inference.py`.

Next research gates: identify minimal interventions that distinguish candidate families, implement branch-and-bound/constraint solving, model partial data and confidence, enforce prospective unseen transition validation, and bridge recovered structure into PSMSL semantics.
