# GEO-BSL-005 — Constrained operator-family discovery

## Result (local sandbox, 2026-10-25)
9/9 unit tests passed. Hidden additive, positional, pair and combined rules each selected their corresponding family with held-out RMSE below 3e-13. A parity-augmented adversarial rule returned no acceptable model (refusal).

## Dataset / leakage controls
Train bases (5,7,10,12), integers 120..420; test bases (6,8,11,14), integers 421..720. 1200 held-out observations for each rule. Candidate selection depends **only** on training residual and full-column-rank qualification, never test scores.

## Execute
```bash
cd experiments/geo_bsl_005
python -m unittest discover -v
python grammar.py > results.json
```

## Qualification limit
This is restricted operator-family selection, **not** unrestricted symbolic generation or MAPEOGEO-native discovery. Digit parsing and four handcrafted bases are provided. Data are synthetic, with no observation noise; rejection tolerance is fixed at 1e-8. Cross-base feature support differs and identifiability may fail in new regimes. No claim of practical physical-mechanism discovery.

## Next gate
Implement native MAPEOGEO adapter plus MD2 adequacy and independent holdout seed/shape provenance; then examine structure under basis changes and unknown finite-state operators.
