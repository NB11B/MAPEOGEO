# GEO-OPGRAM-003 — Fair passive baseline and noise falsification

Correction to GEO-OPGRAM-002: the earlier passive baseline repeatedly queried state 0 and was deliberately weak. Comparing instead with balanced distinct-state coverage removes the apparent active advantage: two arbitrary four-state permutation generators each require three source observations to be identified. C4, V4, D4: active 6, balanced coverage 6, uniformly random distinct query baseline mean 6.44 across 100 seeds (range 6–7). All models correctly identified. 7/7 local tests passed. An initial implementation that exhausted one generator before moving to the next led to an erroneous 7 versus 6 difference and a failed test; corrected round-robin balancing before qualification.

Single corrupted but internally consistent observations can identify the wrong permutation with no contradiction. A conflict between two observed outputs for the same source is detected, but an isolated false report is not reliably detectable.

These are exact, noise-free active identification tests with one adversarially modified observation and no error-correction model, not a complete stochastic-noise benchmark. To establish an active advantage one would need structural constraints, unequal query costs, limited state access, or a hypothesis space where different queries have meaningfully different discriminatory value.

Run: cd experiments/geo_opgram_003 && python -m unittest discover -v && python experiment.py
