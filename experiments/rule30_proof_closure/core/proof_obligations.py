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
            name="Rule30ProofClosure.universal_column_onset_signature",
            module="Rule30LeftReconstruction",
            classification=DeclarationClass.EXACT,
            obligation_id="M3",
            track="Track A",
            dependencies=(
                "Rule30ProofClosure.left_diag_D2_eq_false",
                "Rule30ProofClosure.left_diag_D4_eq_true",
                "Rule30ProofClosure.left_diag_D5_eq_not_D3",
            ),
            summary="New in R30-TRANSPORT-001: every left column p = -k starts with the exact 6-step vertical onset signature (true, true, false, s, true, s) at times t = k .. k + 5, proving cell (k+5) (-k) = cell (k+3) (-k).",
            source_attribution="R30_TRANSPORT_001_NEW",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.cell_neg_eq_center_xor_characteristicFlux",
            module="Rule30LeftReconstruction",
            classification=DeclarationClass.EXACT,
            obligation_id="M1",
            track="Track A",
            dependencies=("Rule30MaskedJen.cell_left'",),
            summary="New in R30-SPATIOTEMPORAL-001: universal arbitrary-depth spatiotemporal transport identity cell t (-d) = xor (center (t + d)) (leftCharacteristicFlux t d) and dual leftCharacteristicFlux t d = xor (center (t + d)) (cell t (-d)).",
            source_attribution="R30_SPATIOTEMPORAL_001_NEW",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.universal_characteristic_flux_onset_laws",
            module="Rule30LeftReconstruction",
            classification=DeclarationClass.EXACT,
            obligation_id="M3",
            track="Track A",
            dependencies=(
                "Rule30ProofClosure.cell_neg_eq_center_xor_characteristicFlux",
                "Rule30ProofClosure.universal_column_onset_signature",
            ),
            summary="New in R30-SPATIOTEMPORAL-001: fixes leftCharacteristicFlux (k + m) k at the single-seed column onset (m in {0,1,2,4} and xor of m=3,5) in terms of center (2k + m) for every depth k.",
            source_attribution="R30_SPATIOTEMPORAL_001_NEW",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.periodic_center_forces_characteristic_flux_depth_periodicity",
            module="Rule30LeftReconstruction",
            classification=DeclarationClass.EXACT,
            obligation_id="M3",
            track="Track A/C",
            dependencies=("Rule30ProofClosure.universal_characteristic_flux_onset_laws",),
            summary="New in R30-SPATIOTEMPORAL-001: independent spatiotemporal transport theorem proving that any P-periodic center tail (t >= T) forces leftCharacteristicFlux (k + m) k to be strictly periodic in spatial depth k with period P for all k >= T.",
            source_attribution="R30_SPATIOTEMPORAL_001_NEW",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.spatiotemporal_101010_quadratic_cancellation_depth5",
            module="Rule30LeftReconstruction",
            classification=DeclarationClass.EXACT,
            obligation_id="M2",
            track="Track A/B",
            dependencies=(
                "Rule30ProofClosure.local_101_pattern_conserved_left_xor",
                "Rule30ProofClosure.local_1010_complement_cancellation_depth4",
            ),
            summary="New in R30-SPATIOTEMPORAL-001: proves that the degree-2 cross-term cell (t+1) (-4) = (!cell (t+1) (-1)) && (!cell (t+3) (-1)) cancels identically against cell t (-4) || cell t (-3) at depth -5, restoring degree-1 linearity cell t (-5) = cell (t+1) (-1) = cell t (-3).",
            source_attribution="R30_SPATIOTEMPORAL_001_NEW",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.characteristicFlux_decomp_leading_orCol",
            module="Rule30LeftReconstruction",
            classification=DeclarationClass.EXACT,
            obligation_id="M1",
            track="Track A/B",
            dependencies=("Rule30ProofClosure.cell_neg_eq_center_xor_characteristicFlux",),
            summary="New in R30-FLUX-CORR-001: proves by induction on d that leftCharacteristicFlux t (d+1) = xor (orCol 0 (t+d)) (interiorCharacteristicFlux t d), isolating the leading PSMSL right-boundary observation at apex time t+d.",
            source_attribution="R30_FLUX_CORR_001_NEW",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.spatiotemporal_leading_orCol_onset_isolation",
            module="Rule30LeftReconstruction",
            classification=DeclarationClass.EXACT,
            obligation_id="M2",
            track="Track A/B",
            dependencies=(
                "Rule30ProofClosure.characteristicFlux_decomp_leading_orCol",
                "Rule30ProofClosure.universal_column_onset_signature",
            ),
            summary="New in R30-FLUX-CORR-001: proves for all k that orCol 0 (2k+1) = xor (!center (2k+2)) (interiorCharacteristicFlux (k+1) k) and orCol 0 (2k+2) = xor (!center (2k+3)) (interiorCharacteristicFlux (k+2) k) at the left wavefront onset.",
            source_attribution="R30_FLUX_CORR_001_NEW",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.spatiotemporal_black_white_apex_dichotomy",
            module="Rule30LeftReconstruction",
            classification=DeclarationClass.EXACT,
            obligation_id="M2",
            track="Track A/B/C",
            dependencies=("Rule30ProofClosure.spatiotemporal_leading_orCol_onset_isolation",),
            summary="New in R30-FLUX-CORR-001: proves the exact PSMSL black-step screening law (center tau = true => interiorCharacteristicFlux = center (tau+1)) and white-step linear isolation law (center tau = false => cell tau 1 = xor (!center (tau+1)) interiorCharacteristicFlux).",
            source_attribution="R30_FLUX_CORR_001_NEW",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.right_history_characteristic_flux_incompatibility_implies_problem1",
            module="Rule30PrizeClosure",
            classification=DeclarationClass.CONDITIONAL,
            obligation_id="M5",
            track="Track A/B/C",
            dependencies=(
                "Rule30ProofClosure.periodic_center_has_black_and_white_in_every_period",
                "Rule30ProofClosure.spatiotemporal_leading_orCol_onset_isolation",
                "Rule30ProofClosure.spatiotemporal_black_white_apex_dichotomy",
                "UNRESOLVED.M4_spatial_bridge_from_near_center_to_left_diagonals",
            ),
            summary="New in R30-FLUX-CORR-001: reduces Problem1 to the incompatibility between the finite-support right-half evolution (cell T T = true, cell T p = false for p > T) and the characteristic-flux onset isolation law at k >= T.",
            source_attribution="R30_FLUX_CORR_001_NEW",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.universal_column_onset_exact_6step",
            module="Rule30LeftReconstruction",
            classification=DeclarationClass.EXACT,
            obligation_id="M3",
            track="Track A",
            dependencies=(
                "Rule30ProofClosure.universal_column_onset_signature",
                "Rule30ProofClosure.left_diag_D3_parity",
            ),
            summary="New in R30-UNIVERSAL-001: upgrades the column onset signature with exact parity cell (k+3) (-k) = decide (k % 2 = 0) and cell (k+5) (-k) = decide (k % 2 = 0) for all k.",
            source_attribution="R30_UNIVERSAL_001_NEW",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.odd_period_forces_characteristic_flux_anti_periodicity",
            module="Rule30LeftReconstruction",
            classification=DeclarationClass.EXACT,
            obligation_id="M3",
            track="Track A/C",
            dependencies=(
                "Rule30ProofClosure.cell_neg_eq_center_xor_characteristicFlux",
                "Rule30ProofClosure.universal_column_onset_exact_6step",
            ),
            summary="New in R30-UNIVERSAL-001: proves that under any odd period P (P % 2 = 1) and k >= T, leftCharacteristicFlux (k+3) k and leftCharacteristicFlux (k+5) k are strictly anti-periodic under k -> k + P.",
            source_attribution="R30_UNIVERSAL_001_NEW",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.double_white_step_depth2_forcing",
            module="Rule30LeftReconstruction",
            classification=DeclarationClass.EXACT,
            obligation_id="M2",
            track="Track A/B",
            dependencies=("Rule30ProofClosure.left_white_step_xor_conservation",),
            summary="New in R30-UNIVERSAL-001 (Law L4): proves that at any double-white step (center t = false, center (t+1) = false), cell t 1 = true forces cell (t+1) 1 = true (PSMSL screening at col 1) and locks cell (t+1) (-1) = !center (t+2) and cell t (-2) = center (t+2).",
            source_attribution="R30_UNIVERSAL_001_NEW",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.right_rowAt_single_seed_frontier_realization",
            module="Rule30BilateralCompatibility",
            classification=DeclarationClass.EXACT,
            obligation_id="M1",
            track="Track B/C",
            dependencies=(
                "Rule30ProofClosure.right_diag_R1_parity",
                "Rule30ProofClosure.rowAt_eq_replicate_false_of_gt",
            ),
            summary="New in R30-UNIVERSAL-001 (Section 3/4 Modeling Audit): proves that every single-seed right-half row at time T >= 2 has exact frontier cell T T = true, sub-leading parity cell T (T-1) = decide (T % 2 = 1), and zero exterior rowAt T (T+1) H = List.replicate H false.",
            source_attribution="R30_UNIVERSAL_001_NEW",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.symbolic_right_evolution_realizes_cell_and_orCol",
            module="Rule30BilateralCompatibility",
            classification=DeclarationClass.EXACT,
            obligation_id="M2",
            track="Track B/C",
            dependencies=(
                "Rule30Bilateral.runWord_rowAt",
                "Rule30ProofClosure.orColWord_rowAt",
            ),
            summary="New in R30-UNIVERSAL-001 (Section 3/4 Modeling Audit): proves that evolving rowAt T 1 (H+1) under runWord and orColWord realizes the exact cellular bit cell (T+s) 1 and PSMSL observation orCol 0 (T+s) for all s < H.",
            source_attribution="R30_UNIVERSAL_001_NEW",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.no_white_run_single_black_all_transients",
            module="Rule30PrizeClosure",
            classification=DeclarationClass.EXACT,
            obligation_id="M3",
            track="Track A/B/C",
            dependencies=(
                "Rule30ProofClosure.period_lock_single_black",
                "Rule30ProofClosure.period_late_single_black",
                "Rule30BlackRuns.period_far",
                "Rule30BlackRuns.not_adjacent",
            ),
            summary="New in R30-UNIVERSAL-001 (Section 5 Acceptance Test): unconditionally refutes the infinite 11-free white-run family 0^r 1 for every symbolic period P = r + 1 >= 15 (all r >= 14), every transient T, and every phase t0 >= T without enumerating period words.",
            source_attribution="R30_UNIVERSAL_001_NEW",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.runSchedule_compositional_semantics",
            module="Rule30ClosureCore",
            classification=DeclarationClass.EXACT,
            obligation_id="M1",
            track="Track A/B/C",
            dependencies=(
                "Rule30ProofClosure.runSchedule_eq_runWord",
                "Rule30ProofClosure.scheduleWord_append",
                "Rule30Bilateral.runWord_rowAt",
                "Rule30ProofClosure.orColWord_rowAt",
            ),
            summary="New in R30-EXHAUST-001 (Obligation 2): proves that arbitrary compositions of white/black run blocks (runBlock r b = runBlack b ∘ runWhite r) compose homomorphically via runSchedule and preserve exact cellular and PSMSL observational semantics.",
            source_attribution="R30_EXHAUST_001_NEW",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.spatiotemporal_001001_and_011011_depth4_constant_collapse",
            module="Rule30LeftReconstruction",
            classification=DeclarationClass.EXACT,
            obligation_id="M2",
            track="Track A/C",
            dependencies=("Rule30MaskedJen.cell_left'",),
            summary="New in R30-EXHAUST-001 (Obligation 3): proves that under the fundamental period-3 short-run blocks 0010010 and 0110110, all boundary variables cancel identically at depth -4 to force degree-0 constants (cell (t+2) (-4) = false for 0010010, and cell (t+1) (-4) = false and cell (t+2) (-4) = true for 0110110).",
            source_attribution="R30_EXHAUST_001_NEW",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.single_seed_spatiotemporal_state_completeness",
            module="Rule30PrizeClosure",
            classification=DeclarationClass.EXACT,
            obligation_id="M1",
            track="Track A/B/C",
            dependencies=(
                "Rule30ProofClosure.periodic_center_has_black_and_white_in_every_period",
                "Rule30ProofClosure.right_rowAt_single_seed_frontier_realization",
                "Rule30ProofClosure.symbolic_right_evolution_realizes_cell_and_orCol",
                "Rule30ProofClosure.obsLeftWord_rowAtLeft_eq_orColWord_rowAt",
                "Rule30ProofClosure.universal_characteristic_flux_onset_laws",
            ),
            summary="New in R30-EXHAUST-001 (Obligation 1): proves that every hypothetical periodic single-seed trajectory PeriodicCenter T P is represented by a unified bilateral spatiotemporal state carrying mixed center runs, the exact right-half frontier/exterior state, bilateral observation coupling, and the 6-step characteristic-flux onset laws.",
            source_attribution="R30_EXHAUST_001_NEW",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.no_white_run_101_all_transients",
            module="Rule30PrizeClosure",
            classification=DeclarationClass.EXACT,
            obligation_id="M3",
            track="Track A/B/C",
            dependencies=(
                "Rule30ProofClosure.period_lock_101",
                "Rule30ProofClosure.period_late_101",
                "Rule30ProofClosure.period_z1_101",
                "Rule30ProofClosure.period_z2_ge_101",
                "Rule30BlackRuns.period_far",
                "Rule30BlackRuns.not_adjacent",
            ),
            summary="New in R30-EXHAUST-001 (Obligation 3): unconditionally refutes the infinite 4-run composite 11-free family 0^r 1 0 1 = scheduleWord [(r, 1), (1, 1)] (r >= 14, P = r + 3 >= 17) for every transient T and every phase t0 >= T via PSMSL right-screening regeneration and two-class observational absorption.",
            source_attribution="R30_EXHAUST_001_NEW",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.absorption_or_flux_violation_dichotomy_excludes_periodic_center",
            module="Rule30PrizeClosure",
            classification=DeclarationClass.EXACT,
            obligation_id="M3",
            track="Track A/B/C",
            dependencies=(
                "Rule30ProofClosure.periodic_center_distinct_futureWork_classes_at_linear_horizon",
                "Rule30ProofClosure.universal_characteristic_flux_onset_laws",
                "Rule30BlackRuns.not_adjacent",
            ),
            summary="New in R30-EXHAUST-001 (Obligation 3): proves unconditionally that for any (T, P) satisfying PeriodicCenter T P, entering ObservationalAbsorptionAt T P, LinearHorizonCollisionAt T P, or CharacteristicFluxOnsetViolationAt T P yields an immediate contradiction.",
            source_attribution="R30_EXHAUST_001_NEW",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.spatial_transport_step_dichotomy",
            module="Rule30LeftReconstruction",
            classification=DeclarationClass.EXACT,
            obligation_id="M1",
            track="Track A",
            dependencies=("Rule30MaskedJen.cell_left'",),
            summary="New in R30-TRANSPORT-001: 6-case spatial relation transport step law (T_black_left, T_black_right, T_white_left, T_white_right, T_comp, T_idemp) from column (p, p+1) to p-1.",
            source_attribution="R30_TRANSPORT_001_NEW",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.transport_onset_excludes_1010_at_t3",
            module="Rule30LeftReconstruction",
            classification=DeclarationClass.EXACT,
            obligation_id="M3",
            track="Track A/C",
            dependencies=(
                "Rule30ProofClosure.local_101_pattern_conserved_left_xor",
                "Rule30ProofClosure.universal_column_onset_signature",
            ),
            summary="New in R30-TRANSPORT-001: zero-decide structural refutation of (center 3, center 4, center 5, center 6) = (1, 0, 1, 0) by colliding Law L3 with the universal column onset signature at k=2, 3.",
            source_attribution="R30_TRANSPORT_001_NEW",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.universal_adjacent_xor_onset_law",
            module="Rule30PrizeClosure",
            classification=DeclarationClass.EXACT,
            obligation_id="M3",
            track="Track A/C",
            dependencies=("Rule30ProofClosure.universal_column_onset_signature",),
            summary="New in R30-TRANSPORT-001: for every depth k, adjacent-column XOR satisfies xor (cell (k+1) (-k)) (cell (k+1) (-(k+1))) = false and xor (cell (k+2) (-k)) (cell (k+2) (-(k+1))) = true.",
            source_attribution="R30_TRANSPORT_001_NEW",
        ),
        FormalDeclarationRecord(
            name="Rule30ProofClosure.transport_adjacent_xor_to_onset_implies_problem1",
            module="Rule30PrizeClosure",
            classification=DeclarationClass.CONDITIONAL,
            obligation_id="M5",
            track="Track A/C",
            dependencies=(
                "Rule30ProofClosure.periodic_center_has_black_and_white_in_every_period",
                "Rule30ProofClosure.left_black_step_screened_forcing",
                "Rule30ProofClosure.universal_adjacent_xor_onset_law",
                "UNRESOLVED.M4_spatial_bridge_from_near_center_to_left_diagonals",
            ),
            summary="New in R30-TRANSPORT-001: non-tautological spatial-transport closure reduction that proves the base case cell (T+sb+m*P) (-1) = !center (T+sb+1) and exposes the exact surviving spatial-transport parity goal at the light-cone onset.",
            source_attribution="R30_TRANSPORT_001_NEW",
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
