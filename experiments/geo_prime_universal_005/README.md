# GEO-PRIME-UNIVERSAL-005 — Identifiability counterexample

Unlabeled source→destination transition multisets of regular C4 and V4 actions are **identical**: all sixteen ordered source/target pairs occur exactly once. Their group operator-order signatures differ: C4=(1,2,4,4), V4=(1,2,2,2). Thus the unlabelled aggregate is not enough to infer *which underlying operator family* generated it. The appropriate inference verdict is refusal, not a forced cyclic model.

Local sandbox verification: 8/8 Python unit tests pass, including relabeling invariance and invalid-operator controls. A complete but *unlabelled* transition multiset does not supply the operator assignments or their compositions.

This does NOT show the two groups give conflicting primality for the order: both have four elements and four is composite. It shows failure of structural identifiability. The prior Lean theorem about known cyclic operators is unaffected.

Reproduce: `cd experiments/geo_prime_universal_005 && python -m unittest discover -v && python ambiguity.py`.

Next gates: augment observations with repeated-action chains and intervention identifiers; determine minimal distinguishing evidence; prove refusal on observational equivalence; assess known-versus-unknown graph order; benchmark under missing events and noise. Keep identification separate from primality certification.
