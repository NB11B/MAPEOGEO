# E25B/E25C executable multipath audit

This package extends the frozen E25 graph audit.

- `audit.py` audits the frozen semantic trust projection and executes four source-bound EO/GEO/FORMAL contract closures.
- `test_audit.py` freezes the topology counts, closure scopes, corruption ladder, and evidence reproducibility.
- `../../evidence/pct_e25b_trust_projection.json` is a reduced trust projection derived from the accepted v0.9 artifact identified inside the file. It contains no source prose.

Run:

```bash
python -m pytest -q experiments/pct_e25bc/test_audit.py
```

The tests intentionally stop at C2 for the four real mathematical cycles. C3/C4 are not meaningful for these scalar/decision contracts and C5 is not established.
