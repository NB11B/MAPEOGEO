# v0.20 evidence invalidated

The previous `SUPPORTED (10/10)` report was produced before the current
mathematical, lineage, registry-binding, macro-conservation, and campaign-credit
checks existed. It is intentionally removed because it is not valid evidence
under the repaired protocol.

After the complete local regression matrix passes, regenerate the report with:

```bash
python -m experiments.pct_goal_solver.generate_v0_20_report --out-dir evidence
```

The repaired campaign is expected to report its actual gate vector without
promoting a partial result to `SUPPORTED`. Commit the generated JSON and SHA-256
sidecar only after deterministic regeneration and hash verification.
