# GEO-BSL-003: Blind candidate-family discovery

Local execution: 2026-10-25. Eight unit tests passed. Candidate powers p=0..4 for digit-power sums were supplied; the inference routine chose p=2 with fitted scale 1 and zero training error.

Training: integer values 1..320 across bases 3,5,7,10,12. Independent held-out tests: integers 321..640 on both seen and unseen bases (2,4,8,11,16); 1600/1600 exact in each cohort. Affine non-digit-feature baseline unseen RMSE 52.218858; shuffled-label training minimum RMSE 42.945597.

This is **restricted hypothesis-class selection**, not fully blind free-form grammar learning, not native MAPEOGEO inference, and not proof of geometric reconstruction. Crucially, digits(n,b) is a supplied primitive and the correct square exponent is in the candidate family. Future gates must withhold both operator family and suitable features; apply native UoW/NGC operator-contract discovery and controls with adversarially distinct rules.

Run: `python -m unittest discover -s experiments/geo_bsl_003 -p 'test_*.py' -v`; `python experiments/geo_bsl_003/discovery.py`.
