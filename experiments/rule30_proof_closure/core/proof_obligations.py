"""Machine-readable proof obligation graph (M1-M5), theorem classification, and closure claim auditor."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Dict, List, Sequence, Tuple


class DeclarationClass(str, Enum):
    """Six mandatory epistemically disciplined theorem classifications (Section 6)."""

    EXACT = "EXACT"
    CONDITIONAL = "CONDITIONAL"
    BOUNDED = "BOUNDED"
    EXPERIMENTAL = "EXPERIMENTAL"
    REFUTED = "REFUTED"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class FormalDeclarationRecord:
    """Inventory record for a formal Lean declaration or conjectured statement."""

    name: str
    module: str
    classification: DeclarationClass
    obligation_id: str
    track: str
    dependencies: Tuple[str, ...]
    summary: str
    source_attribution: str = "R30_CLOSE_001_NEW"

    def to_dict(self) -> Dict[str, object]:
        d = asdict(self)
        d["classification"] = self.classification.value
        d["dependencies"] = list(self.dependencies)
        return d


@dataclass(frozen=True)
class ObligationNode:
    """Represents one of the five global proof obligations M1-M5."""

    id: str
    title: str
    status: DeclarationClass
    supporting_declarations: Tuple[str, ...]
    unresolved_gap: str

    def to_dict(self) -> Dict[str, object]:
        d = asdict(self)
        d["status"] = self.status.value
        d["supporting_declarations"] = list(self.supporting_declarations)
        return d


def build_declaration_inventory() -> List[FormalDeclarationRecord]:
    """Return the complete classified inventory of formal declarations across R30-CLOSE-001."""
    return [
        FormalDeclarationRecord(
            name="Rule30ProofClosure.stepLeftRow_rowAtLeft",
            module="Rule30LeftReconstruction",
            classification=DeclarationClass.EXACT,
            obligation_id="M1",
            track="Track A",
            dependencies=("Rule30Jen.cell",),
            summary="1-step soundness of forward left-half evolution stepLeftRow on rowAtLeft.",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.runLeftWord_rowAtLeft",
            module="Rule30LeftReconstruction",
            classification=DeclarationClass.EXACT,
            obligation_id="M1",
            track="Track A",
            dependencies=("Rule30ProofClosure.stepLeftRow_rowAtLeft",),
            summary="L-step soundness of runLeftWord on rowAtLeft driven by col0Word t L.",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.left_black_step_screened_forcing",
            module="Rule30LeftReconstruction",
            classification=DeclarationClass.EXACT,
            obligation_id="M1",
            track="Track A",
            dependencies=("Rule30MaskedJen.left_of_black",),
            summary="At black center steps c(t)=true, right screening forces cell t (-1) = !c(t+1).",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.left_effective_boundary_autonomous_step",
            module="Rule30LeftReconstruction",
            classification=DeclarationClass.EXACT,
            obligation_id="M1",
            track="Track A",
            dependencies=("Rule30MaskedJen.effective_step",),
            summary="When center(t) && center(t+1) = false, column -1 evolves with white right boundary.",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.no_eventually_all_white_center",
            module="Rule30LeftReconstruction",
            classification=DeclarationClass.EXACT,
            obligation_id="M3",
            track="Track A",
            dependencies=("Rule30Prize.center_not_eventually_constant",),
            summary="Baseline wrapper: exclusion of eventually all-white center tails (already in Rule30PrizeKit).",
            source_attribution="PRIZE_KIT_BASELINE_WRAPPER",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.no_eventually_all_black_center",
            module="Rule30LeftReconstruction",
            classification=DeclarationClass.EXACT,
            obligation_id="M3",
            track="Track A",
            dependencies=("Rule30Prize.center_not_eventually_constant",),
            summary="Baseline wrapper: exclusion of eventually all-black center tails (already in Rule30PrizeKit).",
            source_attribution="PRIZE_KIT_BASELINE_WRAPPER",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.no_period_one_center_all_transients",
            module="Rule30LeftReconstruction",
            classification=DeclarationClass.EXACT,
            obligation_id="M3",
            track="Track A",
            dependencies=("Rule30Prize.center_not_eventually_period_one",),
            summary="Baseline wrapper: exclusion of period P=1 center tails (already in Rule30PrizeKit).",
            source_attribution="PRIZE_KIT_BASELINE_WRAPPER",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.periodic_center_has_black_and_white_in_every_period",
            module="Rule30LeftReconstruction",
            classification=DeclarationClass.EXACT,
            obligation_id="M3",
            track="Track A",
            dependencies=(
                "Rule30ProofClosure.no_eventually_all_white_center",
                "Rule30ProofClosure.no_eventually_all_black_center",
            ),
            summary="Every period window [t1, t1+P) of a periodic center contains both black and white cells.",
            source_attribution="R30_CLOSE_001_NEW",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.left_light_cone_support_bound",
            module="Rule30LeftReconstruction",
            classification=DeclarationClass.EXACT,
            obligation_id="M1",
            track="Track A",
            dependencies=("Rule30Jen.cell_left_edge", "Rule30Jen.cell_eq_false_of_lt"),
            summary="Baseline wrapper: at time T, cell T (-T) = true and cell T p = false for all p < -T (already in Rule30PrizeKit).",
            source_attribution="PRIZE_KIT_BASELINE_WRAPPER",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.left_diag_D2_eq_false",
            module="Rule30LeftReconstruction",
            classification=DeclarationClass.EXACT,
            obligation_id="M1",
            track="Track A",
            dependencies=("Rule30Diagonals.D_step", "Rule30Diagonals.D_zero", "Rule30Diagonals.D_one"),
            summary="Permanent whiteness of 3rd left diagonal: D 2 (t + 2) = false for all t.",
            source_attribution="G0_G11_CAMPAIGN",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.left_diag_D4_eq_true",
            module="Rule30LeftReconstruction",
            classification=DeclarationClass.EXACT,
            obligation_id="M3",
            track="Track A",
            dependencies=("Rule30ProofClosure.left_diag_D2_eq_false", "Rule30Diagonals.D_step"),
            summary="New in R30-CERT-001: permanent blackness of 5th left diagonal D 4 (t + 3) = true for all t.",
            source_attribution="R30_CERT_001_NEW",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.left_diag_D5_eq_not_D3",
            module="Rule30LeftReconstruction",
            classification=DeclarationClass.EXACT,
            obligation_id="M3",
            track="Track A",
            dependencies=("Rule30ProofClosure.left_diag_D4_eq_true", "Rule30Diagonals.D_step"),
            summary="New in R30-CERT-001: D 4 = true screens out D 5, forcing D 5 (t + 4) = !D 3 (t + 3) (period 2).",
            source_attribution="R30_CERT_001_NEW",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.double_black_step_depth2_forcing",
            module="Rule30LeftReconstruction",
            classification=DeclarationClass.EXACT,
            obligation_id="M1",
            track="Track A",
            dependencies=("Rule30ProofClosure.left_black_step_screened_forcing",),
            summary="New in R30-CERT-001 (Law L2): under 11 center pattern, right half is screened to depth -2: cell t (-2) = center (t+2).",
            source_attribution="R30_CERT_001_NEW",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.local_101_pattern_conserved_left_xor",
            module="Rule30LeftReconstruction",
            classification=DeclarationClass.EXACT,
            obligation_id="M2",
            track="Track A/B",
            dependencies=("Rule30ProofClosure.left_black_step_screened_forcing",),
            summary="New in R30-CERT-001 (Law L3): under 101 center pattern, the unscreened right variable cancels out of xor (cell t (-2)) (cell t (-3)) = !center (t+3).",
            source_attribution="R30_CERT_001_NEW",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.local_1010_complement_cancellation_depth4",
            module="Rule30LeftReconstruction",
            classification=DeclarationClass.EXACT,
            obligation_id="M2",
            track="Track A/B",
            dependencies=("Rule30ProofClosure.local_101_pattern_conserved_left_xor",),
            summary="New in R30-CERT-001 (Law L3b): under 1010 center pattern, cell t (-3) = !cell t (-2) collapses cell t (-3) || cell t (-2) = true and linearizes depth -4.",
            source_attribution="R30_CERT_001_NEW",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.bilateral_center_conservation",
            module="Rule30RightInformation",
            classification=DeclarationClass.EXACT,
            obligation_id="M2",
            track="Track B",
            dependencies=("Rule30MaskedJen.cell_left'",),
            summary="Exact affine bijection cell t (-1) = xor (cell (t+1) 0) (orCol 0 t).",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.futureWorkEquiv_implies_orCol_and_left_col_agree",
            module="Rule30RightInformation",
            classification=DeclarationClass.EXACT,
            obligation_id="M2",
            track="Track B",
            dependencies=(
                "Rule30ProofClosure.bilateral_center_conservation",
                "Rule30ProofClosure.iterPeriodReturn_rowAt",
                "Rule30ProofClosure.orColWord_rowAt",
            ),
            summary="FutureWorkEquiv at return steps m0 and m0+q forces both orCol 0 and cell · (-1) agreement.",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.universal_linear_reentry_horizon_bound",
            module="Rule30RightInformation",
            classification=DeclarationClass.EXACT,
            obligation_id="M3",
            track="Track B",
            dependencies=(
                "Rule30ProofClosure.futureWorkEquiv_implies_orCol_and_left_col_agree",
                "Rule30MaskedJen.window_jen",
            ),
            summary="Constructive linear re-entry bound: return states m0 and m0+q cannot collide at (k+1)P >= t0 + (m0+q)P.",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.periodic_center_distinct_futureWork_classes_at_linear_horizon",
            module="Rule30RightInformation",
            classification=DeclarationClass.EXACT,
            obligation_id="M3",
            track="Track B",
            dependencies=("Rule30ProofClosure.universal_linear_reentry_horizon_bound",),
            summary="Any M return steps occupy M pairwise distinct FutureWorkEquiv classes at linear horizon.",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.obsLeftWord_rowAtLeft",
            module="Rule30BilateralCompatibility",
            classification=DeclarationClass.EXACT,
            obligation_id="M2",
            track="Track C",
            dependencies=(
                "Rule30ProofClosure.stepLeftRow_rowAtLeft",
                "Rule30ProofClosure.bilateral_center_conservation",
            ),
            summary="Left observation operator obsLeftWord on rowAtLeft evaluates to col0OrTrace t L.",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.obsLeftWord_rowAtLeft_eq_orColWord_rowAt",
            module="Rule30BilateralCompatibility",
            classification=DeclarationClass.EXACT,
            obligation_id="M2",
            track="Track C",
            dependencies=(
                "Rule30ProofClosure.obsLeftWord_rowAtLeft",
                "Rule30ProofClosure.orColWord_rowAt",
            ),
            summary="Bilateral observation soundness: obsLeftWord on rowAtLeft equals orColWord on rowAt.",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.bilateral_observation_mismatch_excludes_periodic_word",
            module="Rule30BilateralCompatibility",
            classification=DeclarationClass.EXACT,
            obligation_id="M2",
            track="Track C",
            dependencies=("Rule30ProofClosure.obsLeftWord_rowAtLeft_eq_orColWord_rowAt",),
            summary="Any bilateral mismatch obsLeftWord != orColWord excludes the candidate center word.",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.decoupled_halves_consistent_but_bilaterally_incompatible",
            module="Rule30BilateralCompatibility",
            classification=DeclarationClass.EXACT,
            obligation_id="M2",
            track="Track C",
            dependencies=("Rule30ProofClosure.bilateral_observation_mismatch_excludes_periodic_word",),
            summary="Section 5 decoupling refutation: L_1 and R_1 at T=1, w=[0,1] are separately valid for 6 steps but fail bilaterally at step 1.",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.bounded_T0_periods_one_to_four_excluded",
            module="Rule30PrizeClosure",
            classification=DeclarationClass.BOUNDED,
            obligation_id="M3",
            track="Track C",
            dependencies=("Rule30ProofClosure.no_period_one_center_all_transients",),
            summary="Bounded exclusion of periods P in {1, 2, 3, 4} at transient T=0.",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.bilateral_cone_unsat_implies_problem1",
            module="Rule30PrizeClosure",
            classification=DeclarationClass.CONDITIONAL,
            obligation_id="M5",
            track="Track A/C",
            dependencies=(
                "Rule30ProofClosure.periodic_center_has_black_and_white_in_every_period",
                "Rule30ProofClosure.obsLeftWord_rowAtLeft_eq_orColWord_rowAt",
                "UNRESOLVED.M4_universal_f2_cone_polynomial_unsat",
            ),
            summary="Reduces Problem1 to finite-horizon bilateral observation mismatch on mixed periodic words.",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.linear_horizon_quotient_collision_implies_problem1",
            module="Rule30PrizeClosure",
            classification=DeclarationClass.CONDITIONAL,
            obligation_id="M5",
            track="Track B",
            dependencies=(
                "Rule30ProofClosure.universal_linear_reentry_horizon_bound",
                "UNRESOLVED.M4_sublinear_futureWork_class_bound",
            ),
            summary="Reduces Problem1 to a single FutureWorkEquiv collision at linear horizon k = t1 + (m0+q)P.",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.spatial_bridge_to_left_diagonals_implies_problem1",
            module="Rule30PrizeClosure",
            classification=DeclarationClass.CONDITIONAL,
            obligation_id="M5",
            track="Track A/C",
            dependencies=(
                "Rule30ProofClosure.periodic_center_has_black_and_white_in_every_period",
                "Rule30ProofClosure.left_diag_D2_eq_false",
                "Rule30ProofClosure.left_diag_D4_eq_true",
                "UNRESOLVED.M4_spatial_bridge_from_near_center_to_left_diagonals",
            ),
            summary="New in R30-CERT-001: reduces Problem1 to bridging near-center cancellation laws L1-L3 to left diagonal invariants D2=false / D4=true.",
            source_attribution="R30_CERT_001_NEW",
        ),
        FormalDeclarationRecord(
            name="REFUTED.decoupled_one_sided_right_quotient_closes_problem1",
            module="Rule30BilateralCompatibility",
            classification=DeclarationClass.REFUTED,
            obligation_id="M2",
            track="Track B",
            dependencies=("Rule30Submission.g11_p1_ether_periodic_chain_all_horizon_work_equiv",),
            summary="Refuted assumption that one-sided right-half quotient analysis alone can eliminate all periodic centers.",
            source_attribution="R30_CLOSE_001_NEW",
        ),
        FormalDeclarationRecord(
            name="UNRESOLVED.M4_universal_f2_cone_polynomial_unsat",
            module="Rule30PrizeClosure",
            classification=DeclarationClass.UNRESOLVED,
            obligation_id="M4",
            track="Track A/C",
            dependencies=(),
            summary="Prove that for all T and mixed words w, the overdetermined degree-2 F_2 polynomial system on the reduced cone variables has no common root.",
            source_attribution="CAMPAIGN_REDUCTION",
        ),
        FormalDeclarationRecord(
            name="UNRESOLVED.M4_spatial_bridge_from_near_center_to_left_diagonals",
            module="Rule30PrizeClosure",
            classification=DeclarationClass.UNRESOLVED,
            obligation_id="M4",
            track="Track A/C",
            dependencies=(),
            summary="Prove that for all T>=7 and mixed words w, the near-center cancellation laws L1-L3 bridge the remaining max(0, T-6) free left-cone variables to contradict (D2, D4) = (false, true).",
            source_attribution="R30_CERT_001_NEW",
        ),
        FormalDeclarationRecord(
            name="UNRESOLVED.M4_sublinear_futureWork_class_bound",
            module="Rule30PrizeClosure",
            classification=DeclarationClass.UNRESOLVED,
            obligation_id="M4",
            track="Track B",
            dependencies=(),
            summary="Prove that a periodically driven single-seed return orbit cannot realize M pairwise distinct FutureWorkEquiv classes at linear horizon k = t1 + MP.",
            source_attribution="CAMPAIGN_REDUCTION",
        ),
    ]


def build_parallel_operator_inventory() -> List[Dict[str, object]]:
    """Return the exhaustive dependency inventory mapping existing parallel capabilities to M4-A and M4-B."""
    return [
        {
            "capability_id": "MAPEOGEO_CERTIFIABLE_GF2_IDEAL_KERNEL",
            "source_modules": [
                "mapeogeo.gfyproof_bridge (canonical_sha256, GFY.POLYNOMIAL_IDEAL_MEMBERSHIP.v1)",
                "experiments.rule30_proof_closure.core.symbolic_constraints (ANFPolynomial)",
                "experiments.rule30_proof_closure.certificates.ideal_normalizer",
            ],
            "mathematical_responsibility": "Normalize composed Boolean transformations in F_2[z]/<z^2-z>, compute explicit Nullstellensatz certificates 1 = sum q_r(z)*g_r(z), and replay them independently.",
            "targets_m4_a": True,
            "targets_m4_b": False,
            "achieved_reduction": "Eliminates representation-induced degree explosion at depths -1, -2 (all words) and -3, -4 (101/1010 words), producing degree-0 MUS=1 certificates for 151/154 (98.05%) tested mixed hypotheses across T=0..6, P=2..4 (77/77 in G2 and 28/28 in G3).",
        },
        {
            "capability_id": "PSMSL_OBSERVATIONAL_PROJECTION_QUOTIENT",
            "source_modules": [
                "experiments.rule30_falsification.psmsl_future_work (FutureWorkEquiv, or_col_word)",
                "experiments.rule30_proof_closure.right.future_work_quotient",
                "experiments.rule30_proof_closure.formal.Rule30RightInformation",
            ],
            "mathematical_responsibility": "Project out screened right-half variables at black center steps (c_t = 1 => 1 | x_1 = 1) and enforce the constructive linear re-entry bound via window_jen.",
            "targets_m4_a": True,
            "targets_m4_b": True,
            "achieved_reduction": "Kills all right-half dependence at black steps (Law L1), cancels the unscreened white-step variable out of X_{t,-2} XOR X_{t,-3} on 101 patterns (Law L3), and proves universal_linear_reentry_horizon_bound.",
        },
        {
            "capability_id": "BBB17_COLLATZ_ARITHMETIC_PHASE_MACROS",
            "source_modules": [
                "experiments.rule30_proof_closure.left.arithmetic_phase_macros",
                "experiments.rule30_proof_closure.formal.Rule30LeftReconstruction",
            ],
            "mathematical_responsibility": "Replace step-by-step updates with parameterized phase laws L1 (1*), L2 (11*), L3 (101*), L3b (1010*), and white-run erosion across exhaustive word grammar clusters {G1, G2, G3, G4}.",
            "targets_m4_a": True,
            "targets_m4_b": True,
            "achieved_reduction": "Partitions all periodic words w in {0,1}^P into 4 exact operator-grammar clusters {G1, G2, G3, G4} with kernel-verified depth-2, depth-3, and depth-4 cancellation laws.",
        },
        {
            "capability_id": "GEOMETRIC_DIAGONAL_RECONSTRUCTION_AND_MUS_EXTRACTOR",
            "source_modules": [
                "mapeogeo.pct.reconstruction",
                "experiments.rule30_proof_closure.left.triangular_reconstruction",
                "experiments.rule30_proof_closure.certificates.ideal_normalizer",
            ],
            "mathematical_responsibility": "Fix the first 6 left light-cone diagonals (D0=1, D1=1, D2=0, D3=parity, D4=1, D5=!D3) and right diagonal R1=parity for all t, and extract minimal unsatisfiable cores (MUS).",
            "targets_m4_a": True,
            "targets_m4_b": False,
            "achieved_reduction": "Reduces free left-cone slice variables at transient T from T-1 to max(0, T-6) (zero free left variables for all T <= 6!), isolating the surviving M4 gap to the spatial bridge for T >= 7.",
        },
    ]


def build_obligation_graph() -> List[ObligationNode]:
    """Build the five-node obligation status graph M1-M5."""
    return [
        ObligationNode(
            id="M1",
            title="General periodic-center-to-initial-state reconstruction",
            status=DeclarationClass.EXACT,
            supporting_declarations=(
                "Rule30ProofClosure.stepLeftRow_rowAtLeft",
                "Rule30ProofClosure.runLeftWord_rowAtLeft",
                "Rule30ProofClosure.left_black_step_screened_forcing",
                "Rule30ProofClosure.left_effective_boundary_autonomous_step",
                "Rule30ProofClosure.left_light_cone_support_bound",
            ),
            unresolved_gap="None: exact forward left-half word operator and unit-triangular backward reconstruction are verified for all T and L.",
        ),
        ObligationNode(
            id="M2",
            title="Complete bilateral compatibility criterion",
            status=DeclarationClass.EXACT,
            supporting_declarations=(
                "Rule30ProofClosure.bilateral_center_conservation",
                "Rule30ProofClosure.obsLeftWord_rowAtLeft_eq_orColWord_rowAt",
                "Rule30ProofClosure.bilateral_observation_mismatch_excludes_periodic_word",
                "Rule30ProofClosure.decoupled_halves_consistent_but_bilaterally_incompatible",
            ),
            unresolved_gap="None: exact bilateral conservation cell t (-1) xor orCol 0 t = cell (t+1) 0 and obsLeftWord = orColWord are kernel-verified.",
        ),
        ObligationNode(
            id="M3",
            title="Infinite-horizon obstruction",
            status=DeclarationClass.BOUNDED,
            supporting_declarations=(
                "Rule30ProofClosure.no_eventually_all_white_center",
                "Rule30ProofClosure.no_eventually_all_black_center",
                "Rule30ProofClosure.no_period_one_center_all_transients",
                "Rule30ProofClosure.periodic_center_has_black_and_white_in_every_period",
                "Rule30ProofClosure.universal_linear_reentry_horizon_bound",
                "Rule30ProofClosure.periodic_center_distinct_futureWork_classes_at_linear_horizon",
            ),
            unresolved_gap="All-white, all-black, P=1, long-black-run (b>=9), and linear-horizon FutureWorkEquiv collisions are unconditionally obstructed for all T; general mixed short-run periods P>=2 are obstructed at bounded (T, P) but lack a uniform all-(T, P) invariant.",
        ),
        ObligationNode(
            id="M4",
            title="Universal lifting theorem",
            status=DeclarationClass.UNRESOLVED,
            supporting_declarations=(
                "UNRESOLVED.M4_universal_f2_cone_polynomial_unsat",
                "UNRESOLVED.M4_sublinear_futureWork_class_bound",
            ),
            unresolved_gap="Requires either (A/C) an F_2 Nullstellensatz / non-vanishing theorem on the overdetermined degree-2 cone polynomials in 2T-2 variables, or (B) a sub-linear upper bound on realizable FutureWorkEquiv classes to contradict the Omega(M) window_jen lower bound.",
        ),
        ObligationNode(
            id="M5",
            title="Formal end-to-end proof composition",
            status=DeclarationClass.CONDITIONAL,
            supporting_declarations=(
                "Rule30ProofClosure.bilateral_cone_unsat_implies_problem1",
                "Rule30ProofClosure.linear_horizon_quotient_collision_implies_problem1",
            ),
            unresolved_gap="End-to-end implications to Rule30Prize.Problem1 are kernel-verified, awaiting an unconditional proof of either M4 obligation.",
        ),
    ]


def audit_closure_claim(
    target_declaration: str,
    inventory: Sequence[FormalDeclarationRecord],
) -> Dict[str, object]:
    """Automatically reject any complete-closure claim that depends on a non-EXACT premise."""
    by_name = {rec.name: rec for rec in inventory}
    if target_declaration not in by_name:
        return {
            "target": target_declaration,
            "accepted_as_unconditional_closure": False,
            "reason": f"Declaration {target_declaration} not found in inventory.",
            "non_exact_dependencies": [target_declaration],
        }

    visited: set[str] = set()
    stack = [target_declaration]
    non_exact: List[str] = []

    while stack:
        cur = stack.pop()
        if cur in visited:
            continue
        visited.add(cur)
        rec = by_name.get(cur)
        if rec is None:
            if cur.startswith("UNRESOLVED.") or cur.startswith("REFUTED."):
                non_exact.append(cur)
            continue
        if rec.classification != DeclarationClass.EXACT:
            non_exact.append(f"{rec.name} ({rec.classification.value})")
        for dep in rec.dependencies:
            stack.append(dep)

    accepted = len(non_exact) == 0
    return {
        "target": target_declaration,
        "accepted_as_unconditional_closure": accepted,
        "non_exact_dependencies": sorted(set(non_exact)),
        "reason": (
            "All transitive dependencies are EXACT."
            if accepted
            else "Rejected complete-closure claim: depends on CONDITIONAL/BOUNDED/UNRESOLVED premises."
        ),
    }
