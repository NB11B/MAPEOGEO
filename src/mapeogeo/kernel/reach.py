"""First-class formal definitions of Ability and Learning reach.

Ability:
    Ability_t(Q) = ReachableCertifiedWork(Q | G_t)
    Quantified as the sum of weights of work requirements whose required
    functional capabilities are completely covered by certified state G_t.

Learning:
    Learning: G_t -> G_{t+1} iff Reach(G_{t+1}) strictly supersets Reach(G_t)
    An acquisition is a genuine learning event iff it strictly expands the
    universe of certified reachable work.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mapeogeo.kernel.deficiency import WorkRequirement


def compute_ability(
    requirements: list[WorkRequirement],
    certified_signatures: set[str] | frozenset[str],
) -> float:
    """Compute Ability_t(Q) = ReachableCertifiedWork(Q | G_t).

    Returns total weight of work requirements that are 100% covered.
    """
    total_reachable_weight = 0.0
    for req in requirements:
        req_sigs = set(req.required_signatures)
        if req_sigs.issubset(certified_signatures):
            total_reachable_weight += req.weight
    return round(total_reachable_weight, 4)


def is_learning_event(
    prev_reach: set[str] | frozenset[str],
    curr_reach: set[str] | frozenset[str],
) -> bool:
    """Check if transition represents genuine learning: Reach(G_{t+1}) supersets Reach(G_t).

    Returns True iff curr_reach is a strict superset of prev_reach.
    """
    return prev_reach.issubset(curr_reach) and len(curr_reach) > len(prev_reach)
