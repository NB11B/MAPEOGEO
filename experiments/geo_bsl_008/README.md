# GEO-BSL-008 — Mixed Generator and Latent Gauge Qualification

## Objective
Given unlabeled observations x -> y from two unknown linear mechanisms, infer their observed-coordinate operators and memberships; identify structural independence using the repository's actual PSMSL operator-basis API. Explicitly reject rank-deficient, nonlinear, identical-generator, and under-sampled cases.

## Architecture
1. Collect paired transitions with no generator labels. Do not use ground truth in fitting.
2. Fit candidate 2x2 operators from randomly sampled independent observation pairs.
3. Choose candidate pair by aggregate minimum residual.
4. Alternate assignment and least-squares matrix inference.
5. Reject poor residual, weak support, rank deficiency, or indistinguishable generators.
6. Hand qualified inferred operators into native PSMSL `discover_linear_operator_basis`.
7. Compare independent held-out transitions and separately verify gauge equivalence using the withheld simulation oracle.

## Qualification and proof limits
- Unknown Q cannot be uniquely determined; only conjugate operators Q A Q^-1 can be identified without anchors.
- No guarantees of global optimality, cluster number discovery, arbitrary nonlinear rules, or robustness to measurement noise.
- Exactly two transition classes and two-dimensional observed coordinates are assumed.
- Synthetic noiseless data; a blind real-data gate and noise calibration are still required.
- Adversarial rejection is for specified controls, not universal OOD adequacy.
- Random seed fixed and deterministic for reproducibility.

## Run
```bash
cd experiments/geo_bsl_008
python -m unittest discover -v
python mixture.py
```

## Program roadmap
G8a unlabeled 2x2 linear mixture (this gate); G8b state-space dimension and generator-count selection; G8c measurement noise and uncertainty-calibrated abstention; G8d partially observed latent systems and observability certificates; G8e nonlinear grammar synthesis; G8f chronological observational streams and causal intervention controls; G8g blind cross-domain qualification and independent formal certificates. Preserve failures, patches, reruns and external validations independently.
