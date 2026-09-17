# PCT E1-E25 experiment campaign

This directory preserves the computational experiments that followed the PCT v0.10 architecture design.
It is intentionally independent of the local `mapeogeo/pct` implementation so that the evidence can be
cherry-picked or compared without changing the core PCT interfaces.

## What is tested

`test_campaign.py` contains regression coverage for every experiment E1-E25. The default CI suite live-recomputes
the compact exact/numerical controls and validates sealed evidence for experiments whose original run was
exhaustive, solver-heavy, or bound to a particular remote artifact.

- **E1-E3**: validate the sealed exhaustive collision-atlas / exact optimization findings from the original campaign.
- **E4-E22, E24**: compact controls are recomputed live.
- **E23**: the explicit counterexample witnesses are frozen as evidence and checked by the harness.
- **E25**: the remote v0.9 graph audit is frozen to the audited commit/workflow artifact; it is not silently
  reinterpreted as an audit of future commits.

Run the standard regression suite with:

```bash
python -m pip install -r requirements-pct-e1-e25.txt
python -m pytest -q experiments/pct_e1_e25/test_campaign.py
```

The sealed E1-E25 campaign evidence is stored in `evidence/pct_e1_e25_campaign.json`. E23 and E25 retain their
own witness/audit evidence because their scientific meaning depends on those specific bounded inputs.

## Evidence boundary

The campaign establishes controlled finite/symbolic computational results. It does not establish universal
Euler-transform injectivity, universal minimal probe counts, arbitrary-shape reconstruction, or a replacement
for MAPEOGEO's FORMAL/kernel-verification layer.
