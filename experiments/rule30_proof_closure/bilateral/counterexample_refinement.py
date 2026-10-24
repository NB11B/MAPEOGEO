"""Section 8 — Diagnostic classification of failed conjectures and incomplete abstractions."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Dict, List


class FailureCategory(str, Enum):
    """Six mandatory Section 8 diagnostic failure categories."""

    INSUFFICIENT_STATE_REPRESENTATION = "INSUFFICIENT_STATE_REPRESENTATION"
    FALSE_PROPOSED_INVARIANT = "FALSE_PROPOSED_INVARIANT"
    MISSING_RECONSTRUCTION_LEMMA = "MISSING_RECONSTRUCTION_LEMMA"
    INCOMPLETE_CONSTRAINT_MODEL = "INCOMPLETE_CONSTRAINT_MODEL"
    COMPUTATIONAL_EXPLOSION = "COMPUTATIONAL_EXPLOSION"
    GENUINE_UNRESOLVED_GLOBAL_STATEMENT = "GENUINE_UNRESOLVED_GLOBAL_STATEMENT"


@dataclass(frozen=True)
class FailedClaimDiagnostic:
    """Structured diagnostic record for a refuted conjecture or unresolved global proof obligation."""

    claim_id: str
    category: FailureCategory
    proposed_statement: str
    minimal_witness_or_obstruction: str
    formal_refutation_or_reduction: str
    diagnosis: str

    def to_dict(self) -> Dict[str, object]:
        d = asdict(self)
        d["category"] = self.category.value
        return d


def build_failed_claims_ledger() -> List[FailedClaimDiagnostic]:
    """Return the complete Section 8 diagnostic ledger across G3-G11 and R30-CLOSE-001."""
    return [
        FailedClaimDiagnostic(
            claim_id="FAIL-01-SCALAR-DEPTH-CLOSURE",
            category=FailureCategory.INSUFFICIENT_STATE_REPRESENTATION,
            proposed_statement="Scalar right-boundary depth ell alone deterministically closes white-black event cycles.",
            minimal_witness_or_obstruction="Single-seed white onsets w1=38 vs w2=115 share ell=0 and cycle (r,b)=(1,1) but transition to ell'=2 vs ell'=1.",
            formal_refutation_or_reduction="Rule30Submission.g7_p1_depth_alone_not_closed_under_cycle_01",
            diagnosis="Resolved in G8 by introducing variable-length symbolic tail tau (RealizesSymbolicState t ell tau).",
        ),
        FailedClaimDiagnostic(
            claim_id="FAIL-02-ONE-PERIOD-MASKED-EQUIV-STABILITY",
            category=FailureCategory.FALSE_PROPOSED_INVARIANT,
            proposed_statement="1-period MaskedPeriodEquiv (orColWord w sigma1 = orColWord w sigma2) is invariant under F_w = runWord w.",
            minimal_witness_or_obstruction="Under w=[1,0], sigma1=[1,0,0,0,0] and sigma2=[1,1,1,1,0] share MaskedPeriodEquiv in period 1 but diverge in period 2.",
            formal_refutation_or_reduction="Rule30Submission.g9_p1_masked_equiv_diverges_after_one_period",
            diagnosis="Resolved in G10 by introducing multi-horizon FutureWorkEquiv and PersistentWorkEquiv.",
        ),
        FailedClaimDiagnostic(
            claim_id="FAIL-03-SINGLE-BLOCK-ETHER-INFINITE-SCREENING",
            category=FailureCategory.FALSE_PROPOSED_INVARIANT,
            proposed_statement="A single finitely supported 7-cell Ether block E_0 = {6} screens arbitrary right-tail perturbations forever under w=[0,1].",
            minimal_witness_or_obstruction="Flipping column p=9 ({6,9} vs {6}) stays invisible for 7 periods (14 steps) and re-enters observation at exact horizon tau_w = 7.",
            formal_refutation_or_reduction="Rule30Submission.g11_p1_single_block_ether_reentry_at_horizon_seven",
            diagnosis="Resolved in G11.1: each 7-cell block E_0 peels in 2 periods (4 steps), so m+1 blocks screen for 2m+2 periods.",
        ),
        FailedClaimDiagnostic(
            claim_id="FAIL-04-DECOUPLED-ONE-SIDED-CONES",
            category=FailureCategory.INCOMPLETE_CONSTRAINT_MODEL,
            proposed_statement="Left and right half-histories L_{T,w} and R_{T,w} can be analyzed independently without bilateral observation coupling.",
            minimal_witness_or_obstruction="At T=1, w=[0,1], L_1=[1] survives 7 steps in L_{1,[0,1]} and R_1=[1] survives all steps in R_{1,[0,1]}, but C_{1,[0,1]} fails at step H=1.",
            formal_refutation_or_reduction="Rule30ProofClosure.decoupled_halves_consistent_but_bilaterally_incompatible",
            diagnosis="Resolved in R30-CLOSE-001 by coupling obsLeftWord and orColWord via bilateral_center_conservation.",
        ),
        FailedClaimDiagnostic(
            claim_id="FAIL-05-ANF-POLYNOMIAL-DEGREE-EXPLOSION",
            category=FailureCategory.COMPUTATIONAL_EXPLOSION,
            proposed_statement="Symbolic ANF elimination over the 2T-2 cone variables provides a sub-quadratic shortcut for center evaluation.",
            minimal_witness_or_obstruction="Interior cone variables enter through iterated degree-2 disjunctions l xor (c or r), driving ANF degree to 2T-2 and monomial count exponentially.",
            formal_refutation_or_reduction="experiments.rule30_proof_closure.core.symbolic_constraints.build_bilateral_cone_anf_system",
            diagnosis="Confirms that exact polynomial elimination over cone variables experiences exponential monomial growth vs O(t^2) causal-diamond evaluation.",
        ),
        FailedClaimDiagnostic(
            claim_id="FAIL-06-UNIVERSAL-LIFTING-M4-GAP",
            category=FailureCategory.GENUINE_UNRESOLVED_GLOBAL_STATEMENT,
            proposed_statement="Lift bounded-horizon bilateral cone unsatisfiability C_{T,w}(H) = empty and linear re-entry bounds to all (T, P) simultaneously.",
            minimal_witness_or_obstruction="window_jen forces Omega(M) distinct FutureWorkEquiv classes over M periods, whereas the uncoupled right-half observation capacity is 2^{(k+1)*#{w_i=0}}.",
            formal_refutation_or_reduction="Rule30ProofClosure.bilateral_cone_unsat_implies_problem1 & Rule30ProofClosure.linear_horizon_quotient_collision_implies_problem1",
            diagnosis="Exact surviving global mathematical obligation M4: requires either an F_2 non-vanishing proof on the overdetermined degree-2 cone polynomials in 2T-2 variables, or a sub-linear upper bound on realizable FutureWorkEquiv classes.",
        ),
    ]
