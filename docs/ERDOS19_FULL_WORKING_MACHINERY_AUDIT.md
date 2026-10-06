# Full-Working Machinery Audit — Erdős #19 finite frontier

## Implemented and qualified

1. Exact witnessed target-class predicate for n=13, 33<=m<=54.
2. Sound partial pruning for invalid lines, pair reuse, m>54, and inability to
   reach m>=33.
3. Exact coloring constructor and independent coloring verifier.
4. Per-instance SHA-256 coloring co-certificates.
5. Symmetry refinement plus bounded exact individualization/refinement.
6. Replayable parent/child canonical augmentation certificates.
7. Replayable generation ledger with complete local augmentation accounting.
8. Finite-class exhaustion manifests and composition with coloring certificates.
9. Independent small-n generator qualification against labeled exact-cover
   enumeration.

## Additional machinery required for a full n=13 universal computation

A. Scalable exact canonical labeling.
The bounded Python individualization/refinement implementation is an authority
prototype, not a viable n=13 backend. Integrate a mature canonical-labeling
engine (e.g. nauty/Traces-style) behind the same digest/certificate contract.

B. Target-class canonical augmentation generator.
Generation must construct exactly the witnessed reduced class, not all linear
spaces followed by filtering. It needs partial completion constraints for pair
coverage, final line-count bucket, and existence of a valid degree-13 core.

C. Sound future-core feasibility bounds.
Current core degree cannot prune a partial state because later lines may add
neighbors. Need certified upper bounds on the maximum degree/core membership
attainable by any completion.

D. Bucket-aware search scheduling and durable checkpoints.
The 22 m-buckets have very different costs. Each bucket needs independent UoW
leases/checkpoints/manifests so interruption does not invalidate completed work.

E. Proof-producing coloring backend at scale.
The exact Python backtracker is a verifier/qualification tool. A SAT/CP-SAT or
specialized coloring proposer should emit explicit colorings or UNSAT proofs;
the trusted verifier must remain separate.

F. Proof-producing non-colorability handling.
If a generated representative has no 13-coloring, that is a candidate
counterexample and requires an independently checkable UNSAT certificate before
any mathematical claim.

G. Generator-completeness certificate.
The ledger verifies local decisions, but the augmentation schema itself must be
proved complete for the exact target class. This can be a formal theorem,
proof-producing exact-cover encoding, or independently verified canonical
construction theorem.

H. Formal theorem bridge.
To turn finite class closure into a proof of n=13 EFL, encode/check the published
EFL/EFL' equivalence, outside-bucket SAT results, and degree-13-core reduction
as explicit named authority dependencies (preferably Lean or another small
proof checker).

I. Global EFL closure remains separate.
Even a complete n=13 proof does not settle all n. The Annals sufficiently-large
theorem has no practical explicit cutoff, so full original-problem closure
requires an effective cutoff plus all intervening n, or a new uniform proof.
