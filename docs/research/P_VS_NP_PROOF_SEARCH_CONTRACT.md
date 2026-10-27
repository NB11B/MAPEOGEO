# P versus NP: MAPEOGEO proof-search research contract

Status: OPEN PROBLEM — NO PROOF CLAIMED.

## Goal
Construct a deterministic polynomial-time SAT decision algorithm and certify correctness and a uniform polynomial bound in Lean. A refutation of ETH is not sufficient.

## Source and epistemic boundaries
- Anthropic ETH source commit: 16a5ce41304fcdaea4e0be7c132e1c361dc26da5
- MAPEOGEO staged source graph: formal/external_sources/anthropic_eth_2026_graph.json
- No synthetic proof nodes, no automatic promotion from FORMAL_LINKED to KERNEL_VERIFIED.
- A finite benchmark cannot certify an asymptotic polynomial runtime.

## Proof obligations
P0: Precisely formalize SAT input encoding and size L.
P1: Prove semantic preservation for each graph rewrite G -> G'.
P2: Prove the proposed solver terminates and returns SAT(G).
P3: Prove uniform upper bound T(L) <= C*(L+1)^d for fixed C,d independent of L and the instance.
P4: Prove every intermediate tensor, graph, coefficient, branching sum and certificate is accounted for in T.
P5: Prove reduction from arbitrary SAT to the solver's supported class in polynomial time.
P6: Derive P=NP via established NP-completeness of SAT.
P7: Run Lean kernel verification, print axioms, independently compare theorem statements.

## Discovery experiments
1. Reproduce exact swap/singlet and eight-square source identities in the graph.
2. Validate rank, multiplicity, and contraction-cost accounting.
3. Search alternative grouping and recursion schedules using exact symbolic costs.
4. Compare discovered schedules to source recurrence and established contraction-order baselines.
5. Record any conjectural asymptotic improvement as CANDIDATE until fully proved.

## Explicit asymptotic gap
The source exponent n log log(n)/sqrt(log(n)) is omega(log(n)).
A polynomial algorithm requires total exponent O(log L), not just o(n).
Neither this source nor its formalization presently supplies that gap-closing theorem.

## Stop rules
Any unbounded branch count, exponential intermediate representation, unverifiable complexity bound, or unproved reduction prevents P=NP promotion.
