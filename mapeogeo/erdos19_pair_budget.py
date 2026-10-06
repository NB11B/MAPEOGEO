"""Pair-budget identities for linear incidence families in Erdős #19."""
from __future__ import annotations
from math import comb


def pair_consumption(family)->int:
    return sum(comb(len(e),2) for e in family)


def pair_slack(n:int,family)->int:
    return comb(n,2)-pair_consumption(family)


def pair_budget_valid(n:int,family)->bool:
    return pair_consumption(family)<=comb(n,2)


def high_rank_credit(family)->int:
    """Pair slots removed relative to replacing each hyperedge by one rank-2 edge."""
    return sum(comb(len(e),2)-1 for e in family if len(e)>=3)
