# GEO-BSL-007: unknown generator reconstruction
Reconstruct three previously undisclosed 2x2 generator matrices from input/output trajectories, including one redundant (twice the first), using the actual GEO-BSL-006 native PSMSL operator-basis adapter. Independent test streams check generalization. Rank-deficient observations and nonlinear sine transitions should be rejected.

Run `cd experiments/geo_bsl_007 && python -m unittest discover -v && python trajectory.py`.

**Limits**: vector coordinate system and per-generator stream segmentation are given, and all accepted targets are linear with no observation noise. This tests unknown operator coefficients and basis independence, not unknown observation coordinates, latent-state inference, nonlinear synthesis, or unsupervised mode segmentation. CI result should be recorded independently.