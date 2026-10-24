# Collatz three-track falsification campaign

Parent: certified equivalence checkpoint `fbf5d2b`. This branch MUST NOT assert the Collatz conjecture.

1. **Recurrence:** `orbit(n,cap)` distinguishes observed arrival at 1, a detected nontrivial cycle, and a bound-exhausted trajectory. A cap result is NOT a divergence proof. Global beep recurrence remains unproved.
2. **Canonical geometry:** `S=u+v` is exactly conserved by the even-input phase (`u` odd). In the odd-input phase it is nondecreasing: the reservoir is exhausted when `v<k+1`, producing **strict growth**. Thus S is NOT a global descending potential. Preserve this counterexample to any naive Lyapunov claim.
3. **Parity composition:** A valid length-r accelerated parity word yields an affine map `(A*n+B)/2^r`. Prefix parity validity is checked separately. This is an exact arithmetic identity on its parity cylinder; it does not imply all orbits terminate.

Run `python -m unittest -v test_three_tracks.py` and `python three_tracks.py --starts 10000 --cap 10000 --depth 8`.

Next Lean gate: prove `S` conservation/nondecrease and parity affine composition for arbitrary natural inputs; retain explicit parity preconditions. Any recurrence potential must reject observed cycles and be well-founded.
