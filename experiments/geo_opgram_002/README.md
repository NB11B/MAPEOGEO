# GEO-OPGRAM-002 — Active black-box permutation identification

Exact version-space enumeration, not approximate learning. Permutation hypothesis class with four known states and two named unknown generators (each initially 24 candidate actions). Active probes select the state/operator pair maximizing worst-case candidate elimination, versus a deliberately weak passive baseline that repeatedly probes only state zero.

**Locally executed:** 10/10 tests passed; C4, V4, and D4 active learner identified both primitive actions using six observations per system, while repetitive passive queries remained ambiguous after eight. Held-out predictions on all operator words of lengths 1..5 and four starting states: 0/248 errors per system.

No generator-relationship prior is supplied to the learner; the fully labeled state set, named elementary operations, bijective permutation hypothesis and ability to query arbitrary states **are** supplied. Identifiability after three distinct source observations for each permutation is expected under bijectivity. The baseline is not an optimized passive learner. This is not a cryptanalytic method or a statement about ciphertext leakage.

Run: cd experiments/geo_opgram_002 && python -m unittest discover -v && python experiment.py

Next: stronger randomized/coverage passive baselines, noisy and adversarial observations, action labels hidden, limited-access states, nonfaithful group actions; dynamically infer relations and compare against independent held-out action paths.
