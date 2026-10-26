# GEO-PRIME-STRUCTURAL-001 — Prior-sensitive spectral identifiability

Exact local benchmark: 10/10 unit tests passed on Python 3.13. With n=5 and one observed edge 0→1: arbitrary permutation hypothesis gives 24 candidate operators and six cycle spectra; known modular coordinates and assumption that the operator is a primitive translation gives one candidate; latent coordinates with a **supplied full-cycle (5-cycle) assumption** gives six candidates but a single cycle spectrum. Zero observations with that same assumption already determine the spectrum; this is prior knowledge, not structural discovery!

Earlier GEO-PRIME-SPECTRAL-002 assertion that spectral uniqueness requires operator uniqueness applies only to **unrestricted arbitrary permutation completions** and fails under a restricted n-cycle hypothesis class. Do not generalize across model classes. No learning/discovery of the full-cycle prior is demonstrated here. Exact search factorially expensive, n<=6 in tests.

Run: cd experiments/geo_prime_structural_001 && python -m unittest discover -v && python experiment.py.

Next: compare multiple constrained classes against genuinely held-out transitions, penalize class assumptions, discover constraints only when distinguishable by interventions, and abstain on observational equivalence.
