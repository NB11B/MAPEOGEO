"""Relation types and evidentiary ordering for graph connections.

Enforces the strict hierarchy:
    CANDIDATE_REPRESENTS < REPRESENTS < SAME_SEMANTICS
    (and SCOPED_OVERLAP, EQUIVALENT_TO)

In accordance with global invariant G2 and joint layer specifications:
- Evidentiary strength is an ordering on evidentiary burden, NOT an automatic promotion.
- Candidate representation cannot masquerade as representation.
- Representation cannot masquerade as semantic identity.
- Uncertified equivalence is strictly rejected fail-closed.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Final


class RelationType(StrEnum):
    """Enumeration of canonical relational connections."""

    CANDIDATE_REPRESENTS = "CANDIDATE_REPRESENTS"
    SCOPED_OVERLAP = "SCOPED_OVERLAP"
    REPRESENTS = "REPRESENTS"
    EQUIVALENT_TO = "EQUIVALENT_TO"
    SAME_SEMANTICS = "SAME_SEMANTICS"

    @property
    def evidentiary_level(self) -> int:
        """Evidentiary weight required to assert this relationship."""
        levels: Final[dict[RelationType, int]] = {
            RelationType.CANDIDATE_REPRESENTS: 1,
            RelationType.SCOPED_OVERLAP: 2,
            RelationType.REPRESENTS: 3,
            RelationType.EQUIVALENT_TO: 4,
            RelationType.SAME_SEMANTICS: 5,
        }
        return levels[self]

    def allows_weaker_demand(self, demand: RelationType) -> bool:
        """Check if this asserted relation satisfies a required contract demand.

        An asserted relation of higher level may satisfy a contract requiring
        equal or lower evidentiary burden, BUT a weaker relation can NEVER satisfy
        a stronger demand.
        """
        return self.evidentiary_level >= demand.evidentiary_level


def check_relation_strength_invariance(
    asserted: RelationType,
    demanded: RelationType,
    *,
    is_certified: bool = False,
) -> bool:
    """Fail-closed relation verification.

    Rules:
    1. Weak relations cannot satisfy strong demands.
    2. Strong semantic claims (EQUIVALENT_TO, SAME_SEMANTICS) ALWAYS require explicit certification.
    3. CANDIDATE_REPRESENTS cannot be promoted to REPRESENTS or SAME_SEMANTICS
       without certification.
    """
    if not asserted.allows_weaker_demand(demanded):
        return False

    # Demands of EQUIVALENT_TO or SAME_SEMANTICS require certified backing
    if demanded in (RelationType.EQUIVALENT_TO, RelationType.SAME_SEMANTICS) and not is_certified:
        return False

    return True
