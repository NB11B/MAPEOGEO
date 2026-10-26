# GEO-OPGRAM-001 — black-box finite operational grammar

Input: oracle of labeled elementary actions on observable states. Reconstruct each primitive permutation from a full query matrix, enumerate finite closure by BFS and give a shortest representative word for each distinct transformation. Independently check all compositions of length 3–5 from every initial state. C4, V4, D4 exact 10/10 tests, 224 composed test cases per system, zero mismatches, and refusal if any state is unobserved.

D4 discovers eight transformations from rotation r and reflection f; its relations include r^4=e, f²=e, frf=r⁻¹. The test checks those relations but does not independently infer a minimal *presentation* or prove that those are a complete set of defining relations. Generator actions are fully observed before longer-sequence holdout: this is compositional prediction, NOT sparse/latent operator discovery. No cryptographic security claim.

Reproduce: cd experiments/geo_opgram_001 && python -m unittest discover -v && python experiment.py

Next: partial-action version-space enumeration, active experiment design distinguishing candidate presentations, retrospective failures preserved, prospective unseen elementary actions, stronger controls such as duplicate generators, nonfaithful actions, corrupted observations and finite-depth presentations.
