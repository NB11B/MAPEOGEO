# Collatz three-track falsification campaign

Parent: certified equivalence checkpoint `fbf5d2b`. This branch MUST NOT assert the Collatz conjecture.

1. **Recurrence:** `orbit(n,cap)` distinguishes observed arrival at 1, a detected nontrivial cycle, and a bound-exhausted trajectory. A cap result is NOT a divergence proof. Global beep recurrence remains unproved.
2. **Canonical geometry:** `S=u+v` is exactly conserved by the even-input phase (`u` odd). In the odd-input phase it is nondecreasing: the reservoir is exhausted when `v<k+1`, producing **strict growth**. Thus S is NOT a global descending potential. Preserve this counterexample to any naive Lyapunov claim.
3. **Parity composition:** A valid length-r accelerated parity word yields an affine map `(A*n+B)/2^r`. Prefix parity validity is checked separately. This is an exact arithmetic identity on its parity cylinder; it does not imply all orbits terminate.

Run `python -m unittest -v test_three_tracks.py` and `python three_tracks.py --starts 10000 --cap 10000 --depth 8`.

Next Lean gate: prove `S` conservation/nondecrease and parity affine composition for arbitrary natural inputs; retain explicit parity preconditions. Any recurrence potential must reject observed cycles and be well-founded.

## Lean 4 Certification (`ThreeTracks.lean`)

`ThreeTracks.lean` formally proves all three next-gate obligations over all natural numbers without `sorry` or non-standard axioms:

- **Track B (Canonical High-Water Resource Geometry)**:
  - `evenPhase_highWater_eq`: $S' = S$ on every even-Collatz phase ($u = 2k+1$).
  - `oddPhase_highWater_eq_max`: $S' = \max(S, 3k+1)$ on every odd-Collatz phase ($u = 2k$).
  - `oddPhase_highWater_strict_growth_iff`: $S' > S \iff v < k + 1$ (explaining all $\sum_{k=1}^{63}(k+1) = 2079$ strict-growth cases in `1 ≤ u < 128, 0 ≤ v < 128` and formally falsifying $S$ as a descending Lyapunov potential).
  - `posReg_highWater_nondecreasing`: $S' \ge S$ across all positive-register phases ($u > 0$).
  - `resetPhase_highWater_eq_max`: $S' = \max(v, j+1)$ on reset phases ($u = 0$).
- **Track C (Affine Parity-Word Operator Composition & Residue Periodicity)**:
  - `parityWord_affine_identity`: $2^{|w|} \cdot \operatorname{applyParityWord}(m, w) = 3^{\operatorname{ones}(w)} \cdot m + B(w)$ for every `validParityWord m w`.
  - `parityWord_divisibility`: $(A(w)\cdot m + B(w)) \bmod 2^{|w|} = 0$.
  - `parityWord_residue_shift`: Shifting $m \mapsto m + q \cdot 2^{|w|}$ preserves `validParityWord` and shifts the output by $q \cdot 3^{\operatorname{ones}(w)}$.
- **Track A (Cycle Algebra & Conditional Well-Founded Potential Gate)**:
  - `parityWord_cycle_equation` & `no_cycle_when_wordA_ge_wordD`: Any cycle of a valid parity word satisfies $D(w) \cdot m = A(w) \cdot m + B(w)$, ruling out cycles whenever $A(w) \ge D(w)$ ($3^a \ge 2^r$) and $B(w) > 0$.
  - `wellFounded_potential_forces_reset`: Any potential $V : \mathbb{N} \to \mathbb{N}$ that strictly decreases after finitely many positive-register steps forces `RegReachesZero u` for all $u$, `CollatzConjecture`, and `¬ Quasihalts`.
