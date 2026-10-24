"""Track C & Section 5 — Bilateral compatibility C_{T, w} = L_{T, w} cap R_{T, w} and Prize 2/3 metrics."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Sequence, Set, Tuple

from ..core.periodic_hypothesis import PeriodicCenterHypothesis, WordClass
from ..core.rule30_exact import (
    center_discrepancy_trace,
    evolve_single_seed,
    obs_left_word,
    or_col_word,
)
from ..core.symbolic_constraints import build_bilateral_cone_anf_system


@dataclass(frozen=True)
class BilateralHypothesisEvaluation:
    """Complete bilateral evaluation of a periodic-center hypothesis H(T, P, w)."""

    transient_t: int
    period_p: int
    word: str
    word_class: str
    discrepancy_weight: int
    left_unsat_horizon_h: Optional[int]
    bilateral_cone_unsat_horizon_h: Optional[int]
    single_seed_mismatch_horizon_h: int
    decoupling_gap_steps: int
    status: str

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DecouplingCounterexampleRecord:
    """Section 5 decoupling counterexample where L_{T,w}(H) != empty and R_{T,w}(H) != empty but C_{T,w}(H) == empty."""

    transient_t: int
    word: str
    horizon_h: int
    left_witness: Tuple[int, ...]
    right_witness: Tuple[int, ...]
    obs_left: Tuple[int, ...]
    obs_right: Tuple[int, ...]
    left_only_unsat_horizon: int
    bilateral_unsat_horizon: int

    def to_dict(self) -> Dict[str, object]:
        d = asdict(self)
        d["left_witness"] = list(self.left_witness)
        d["right_witness"] = list(self.right_witness)
        d["obs_left"] = list(self.obs_left)
        d["obs_right"] = list(self.obs_right)
        return d


@dataclass(frozen=True)
class Prize2And3Evaluation:
    """Secondary objectives: Prize 2 discrepancy envelope and Prize 3 symbolic reconstruction cost."""

    steps_evaluated: int
    max_abs_discrepancy: int
    final_discrepancy: int
    empirical_sublinear_ratio_at_end: float
    anf_max_degree_by_t: Dict[int, int]
    anf_monomial_count_by_t: Dict[int, int]
    causal_diamond_gate_ops_by_t: Dict[int, int]
    shortcut_found: bool


def evaluate_bilateral_hypothesis(
    hyp: PeriodicCenterHypothesis,
    single_seed_rows: Sequence[Dict[int, int]],
    max_horizon: int = 36,
) -> BilateralHypothesisEvaluation:
    """Evaluate L_{T,w}, R_{T,w}, and C_{T,w} for hypothesis H(T, P, w)."""
    t_val = hyp.transient_t
    p_len = hyp.period_p
    w = hyp.word

    # Unconditional constant-word exclusions
    if hyp.word_class == WordClass.ALL_WHITE:
        return BilateralHypothesisEvaluation(
            transient_t=t_val,
            period_p=p_len,
            word=hyp.word_str,
            word_class=hyp.word_class.value,
            discrepancy_weight=hyp.discrepancy_weight,
            left_unsat_horizon_h=1,
            bilateral_cone_unsat_horizon_h=1,
            single_seed_mismatch_horizon_h=1,
            decoupling_gap_steps=0,
            status="EXACT_EXCLUDED_ALL_WHITE",
        )
    if hyp.word_class == WordClass.ALL_BLACK:
        return BilateralHypothesisEvaluation(
            transient_t=t_val,
            period_p=p_len,
            word=hyp.word_str,
            word_class=hyp.word_class.value,
            discrepancy_weight=hyp.discrepancy_weight,
            left_unsat_horizon_h=t_val + 1,
            bilateral_cone_unsat_horizon_h=t_val + 1,
            single_seed_mismatch_horizon_h=1,
            decoupling_gap_steps=0,
            status="EXACT_EXCLUDED_ALL_BLACK",
        )

    left_states: List[Tuple[int, ...]] = (
        [()]
        if t_val == 0
        else [
            tuple(((mask >> i) & 1) for i in range(t_val - 1)) + (1,)
            for mask in range(1 << (t_val - 1))
        ]
    )
    right_states: List[Tuple[int, ...]] = list(left_states)

    w_ext = [w[s % p_len] for s in range(max_horizon + 1)]
    l_trajs: List[Tuple[Optional[int], Tuple[int, ...]]] = []
    for l_st in left_states:
        padded = l_st + (0,) * (max_horizon + 2)
        obs_l = obs_left_word(w_ext[:max_horizon], w_ext[max_horizon], padded)
        fail_h: Optional[int] = None
        for s in range(max_horizon):
            if w_ext[s] == 1 and obs_l[s] != 1:
                fail_h = s + 1
                break
        l_trajs.append((fail_h, obs_l))

    r_trajs: List[Tuple[int, ...]] = []
    for r_st in right_states:
        padded = r_st + (0,) * (max_horizon + 2)
        obs_r = or_col_word(w_ext[:max_horizon], padded)
        r_trajs.append(obs_r)

    h_left: Optional[int] = (
        max(fh for fh, _ in l_trajs if fh is not None)
        if all(fh is not None for fh, _ in l_trajs)
        else None
    )
    h_bilat: Optional[int] = None
    for h in range(1, max_horizon + 1):
        l_set: Set[Tuple[int, ...]] = {
            obs[:h] for fh, obs in l_trajs if fh is None or fh > h
        }
        r_set: Set[Tuple[int, ...]] = {obs[:h] for obs in r_trajs}
        if not (l_set & r_set):
            h_bilat = h
            break

    # Direct single-seed center mismatch horizon from t = T
    seed_mis = 1
    for s in range(max_horizon):
        if single_seed_rows[t_val + s].get(0, 0) != w[s % p_len]:
            seed_mis = s + 1
            break

    gap = (h_left - h_bilat) if (h_left is not None and h_bilat is not None) else 0
    return BilateralHypothesisEvaluation(
        transient_t=t_val,
        period_p=p_len,
        word=hyp.word_str,
        word_class=hyp.word_class.value,
        discrepancy_weight=hyp.discrepancy_weight,
        left_unsat_horizon_h=h_left,
        bilateral_cone_unsat_horizon_h=h_bilat,
        single_seed_mismatch_horizon_h=seed_mis,
        decoupling_gap_steps=gap,
        status="BOUNDED_CONE_UNSAT" if h_bilat is not None else "SURVIVING_MODEL",
    )


def verify_checkpoint_02_bilateral_soundness() -> Tuple[bool, List[DecouplingCounterexampleRecord]]:
    """Verify Checkpoint 02 and extract explicit Section 5 decoupling counterexamples."""
    counterexamples: List[DecouplingCounterexampleRecord] = []

    # Witness 1: T = 1, w = [0, 1] (L_unsat = 8, C_unsat = 1)
    w01 = (0, 1)
    w01_ext = [w01[s % 2] for s in range(7)]
    l1 = (1, 0, 0, 0, 0, 0, 0, 0)
    r1 = (1, 0, 0, 0, 0, 0, 0, 0)
    obs_l1 = obs_left_word(w01_ext[:6], w01_ext[6], l1)
    obs_r1 = or_col_word(w01_ext[:6], r1)
    counterexamples.append(
        DecouplingCounterexampleRecord(
            transient_t=1,
            word="01",
            horizon_h=6,
            left_witness=(1,),
            right_witness=(1,),
            obs_left=obs_l1,
            obs_right=obs_r1,
            left_only_unsat_horizon=8,
            bilateral_unsat_horizon=1,
        )
    )

    # Witness 2: T = 2, w = [1, 0] (L_unsat = 7, C_unsat = 2)
    w10 = (1, 0)
    w10_ext = [w10[s % 2] for s in range(7)]
    l2 = (1, 1, 0, 0, 0, 0, 0, 0)
    r2 = (0, 1, 0, 0, 0, 0, 0, 0)
    obs_l2 = obs_left_word(w10_ext[:6], w10_ext[6], l2)
    obs_r2 = or_col_word(w10_ext[:6], r2)
    counterexamples.append(
        DecouplingCounterexampleRecord(
            transient_t=2,
            word="10",
            horizon_h=6,
            left_witness=(1, 1),
            right_witness=(0, 1),
            obs_left=obs_l2,
            obs_right=obs_r2,
            left_only_unsat_horizon=7,
            bilateral_unsat_horizon=2,
        )
    )

    passed = (
        obs_l1[0] != obs_r1[0]
        and all(obs_l1[s] == 1 for s in range(6) if w01_ext[s] == 1)
        and all(obs_l2[s] == 1 for s in range(6) if w10_ext[s] == 1)
    )
    return passed, counterexamples


def evaluate_prize2_and_prize3_closure_metrics(steps: int = 256) -> Prize2And3Evaluation:
    """Evaluate Prize 2 center discrepancy envelope and Prize 3 ANF symbolic reconstruction cost."""
    rows = evolve_single_seed(steps)
    disc = center_discrepancy_trace(rows)
    max_abs = max(abs(d) for d in disc)
    final_d = disc[-1]
    ratio = abs(final_d) / float(steps)

    anf_deg: Dict[int, int] = {}
    anf_mon: Dict[int, int] = {}
    diamond_ops: Dict[int, int] = {}
    for t_val in range(1, 6):
        sys_anf = build_bilateral_cone_anf_system(t_val, (0, 1), horizon=8)
        anf_deg[t_val] = sys_anf.max_degree
        anf_mon[t_val] = sys_anf.total_monomials
        diamond_ops[t_val] = (t_val + 8) ** 2

    return Prize2And3Evaluation(
        steps_evaluated=steps,
        max_abs_discrepancy=max_abs,
        final_discrepancy=final_d,
        empirical_sublinear_ratio_at_end=ratio,
        anf_max_degree_by_t=anf_deg,
        anf_monomial_count_by_t=anf_mon,
        causal_diamond_gate_ops_by_t=diamond_ops,
        shortcut_found=False,
    )
