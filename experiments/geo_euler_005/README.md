# GEO-EULER-005 — Proof-carrying grammar selection

Takes the **actual** GEO-EULER-004 `run()` result, validates operator-role provenance, the exact known recurrence AST, and positive, zero-error held-out evidence. Outputs a fresh Lean file defining the selected recurrence operations and proving the universal recurrence contract by definitional equality. No finite-data match is accepted as universal proof.

## Reproduce
```bash
cd experiments/geo_euler_005
python -m unittest discover -v
python bridge.py
cd ../..
lake build MAPEOGEOFormal.GeoEuler MAPEOGEOFormal.GeoEulerCertificate
lake env lean MAPEOGEOFormal/GeoEulerSelected.lean
```

The source AST vocabulary is strictly allowlisted. Unknown or modified rule schemes fail closed. Tests include candidate corruption, role ambiguity, missing holdout evidence, malformed identifiers and attempted injection.

## Critical scope
This certifies only **structurally recognized, preapproved recursion schemes**. The bridge does not prove the empirical learner can discover any arbitrary recurrence, and a malicious/fabricated discovery result using the accepted scheme remains outside cryptographic provenance verification. The candidate grammar is a two-operation fragment with no general recursive AST compiler. There is no formal inference-soundness theorem or kernel verification of the learner's finite-data adequacy.

We do not conflate the discovered opaque operator table with an unbounded total function: the emitted Lean functions are the total extension of the **selected grammar**, justified only when that grammar is allowed and its four recurrence laws are proven.
