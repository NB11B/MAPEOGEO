"""Formal-frontier proof-obligation decomposition for selected Erdős statements."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class ProofObligation:
    problem: str
    target_kind: str
    available_lemmas: tuple[str,...]
    missing_bridge: str
    machinery_outcome: str


OBLIGATIONS={
 "19": ProofObligation(
   "19","universal graph coloring",
   ("le_chromaticNumber","colorable_of_sharedColoring","card_sharedSet_le"),
   "construct an n-coloring of shared vertices satisfying clique-wise injectivity for arbitrary EFLConfig",
   "IMPLEMENT_OR_PROVE_LEMMA",
 ),
 "23": ProofObligation(
   "23","extremal graph deletion bound",
   ("n1_tight","n5","n5_tight","blowupC5_tight"),
   "upper bound: every triangle-free graph on 5n vertices admits bipartite subgraph after <= n^2 deletions",
   "IMPLEMENT_OR_PROVE_LEMMA",
 ),
 "60": ProofObligation(
   "60","asymptotic extremal counting",
   ("he_ma_yang","two_copies"),
   "upgrade finite/special-family C4 counts to uniform eventual c*sqrt(n) lower bound above ex(n,C4)",
   "ASYMPTOTIC_BRIDGE_MISSING",
 ),
 "89": ProofObligation(
   "89","asymptotic geometric lower bound",
   ("n_dvd_log_n","grid_upper_bound","implies_n_dvd_log_n"),
   "strengthen minimalDistinctDistances lower bound from n/log n to n/sqrt(log n)",
   "ASYMPTOTIC_BRIDGE_MISSING",
 ),
 "97": ProofObligation(
   "97","universal convex metric exclusion",
   ("three_equidistant","three_unit_distance","three_unit_distance_cut_min"),
   "prove every finite convex-independent planar set has a vertex lacking four equal-distance neighbors",
   "GEOMETRIC_UNIVERSAL_BRIDGE_MISSING",
 ),
 "128": ProofObligation(
   "128","induced-density implies triangle",
   (),
   "derive a triangle from the edge-density hypothesis on every subset of at least half the vertices",
   "EXTREMAL_GRAPH_BRIDGE_MISSING",
 ),
}


def obligation(problem:str)->ProofObligation:
    return OBLIGATIONS[problem]
