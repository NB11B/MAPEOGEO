"""Causal Ordering and Legal Reference Time Primitives for Task T07.

================================================================================
REUSE SPECIFICATION (Amendment 1, Page 4):
1. Existing Component Extended:
   - intel_uow.workflow (event relations, causal parents, sequence numbers)
   - intel_uow.catalog (Record envelope, Reference, EventRef)
2. Interface Reused:
   - ClockStreamAdapter (intel_authority.adapters)
   - Reference and TypedValue adapters (intel_authority.adapters)
3. Additional Semantic Responsibility:
   - AQ39: Unrelated local counters establish no order; stream ownership stays explicit.
   - AQ40: Causal receipts preserve local knowledge; valid parent links establish
     causal order; causal cycles and invalid snapshots produce diagnostics.
   - AQ42: Legal reference time is not a UoW counter; relates occurrence events
     to statutory intervals only via an explicit ReferenceTimeMapping.
4. Qualification Evidence Delta:
   - AQ39, AQ40, AQ42 qualification assertions.
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


class EventRelationKind(str, Enum):
    BEFORE = "before"
    AFTER = "after"
    SAME = "same"
    UNKNOWN = "unknown"
    CONTEXT_OR_MODEL_ERROR = "context_or_model_error"


class LegalTimeRelationKind(str, Enum):
    BEFORE = "before"
    WITHIN = "within"
    AFTER = "after"
    OVERLAP = "overlap"
    UNKNOWN = "unknown"
    CONTEXT_OR_MODEL_ERROR = "context_or_model_error"


def _ref_id(ref_val: Any) -> str:
    if isinstance(ref_val, dict):
        return str(ref_val.get("id", ref_val.get("stream_id", "")))
    return str(ref_val)


def _event_key(event_ref: Dict[str, Any]) -> Tuple[str, int]:
    stream = str(event_ref.get("stream_id", ""))
    seq = int(event_ref.get("sequence", 0))
    return stream, seq


class PlatformCausalDAG:
    """Platform causal DAG owning event sequencing, cross-stream parent reachability, and cycle detection."""

    def __init__(self, events: List[Dict[str, Any]]) -> None:
        self.events = events
        self.event_map: Dict[Tuple[str, int], Dict[str, Any]] = {
            (ev.get("stream_id", ""), ev.get("sequence", 0)): ev
            for ev in events
        }

    @classmethod
    def from_snapshot(cls, snapshot: Dict[str, Any]) -> PlatformCausalDAG:
        return cls(events=snapshot.get("events", []))

    def detect_cycles(self) -> bool:
        """Returns True if any cycle exists in the causal parent graph."""
        visited_all: Set[Tuple[str, int]] = set()
        rec_stack: Set[Tuple[str, int]] = set()

        def has_cycle(node: Tuple[str, int]) -> bool:
            visited_all.add(node)
            rec_stack.add(node)
            curr_ev = self.event_map.get(node)
            if curr_ev:
                for p in curr_ev.get("causal_parent_refs", []):
                    p_key = (p.get("stream_id", ""), p.get("sequence", 0))
                    if p_key not in visited_all:
                        if has_cycle(p_key):
                            return True
                    elif p_key in rec_stack:
                        return True
            rec_stack.remove(node)
            return False

        for node in list(self.event_map.keys()):
            if node not in visited_all:
                if has_cycle(node):
                    return True
        return False

    def is_ancestor(self, ancestor_key: Tuple[str, int], target_key: Tuple[str, int]) -> bool:
        """Checks reachability from target_key back to ancestor_key through causal parents."""
        visited: Set[Tuple[str, int]] = set()
        queue = [target_key]
        while queue:
            curr = queue.pop(0)
            if curr in visited:
                continue
            visited.add(curr)
            curr_ev = self.event_map.get(curr)
            if not curr_ev:
                continue
            parents = curr_ev.get("causal_parent_refs", [])
            for p in parents:
                p_key = (p.get("stream_id", ""), p.get("sequence", 0))
                if p_key[0] == ancestor_key[0] and p_key[1] >= ancestor_key[1]:
                    return True
                if p_key == ancestor_key:
                    return True
                queue.append(p_key)
        return False

    def relate_events(
        self,
        left_ref: Dict[str, Any],
        right_ref: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evaluates causal order between two events (AQ39, AQ40)."""
        left_stream = left_ref.get("stream_id")
        right_stream = right_ref.get("stream_id")
        left_seq = left_ref.get("sequence", 0)
        right_seq = right_ref.get("sequence", 0)

        # 1. Same stream
        if left_stream == right_stream:
            if left_seq < right_seq:
                return {"relation": EventRelationKind.BEFORE.value, "witness_refs": [left_ref, right_ref], "diagnostics": []}
            elif left_seq > right_seq:
                return {"relation": EventRelationKind.AFTER.value, "witness_refs": [left_ref, right_ref], "diagnostics": []}
            else:
                return {"relation": EventRelationKind.SAME.value, "witness_refs": [left_ref], "diagnostics": []}

        # 2. Cycle check
        if self.detect_cycles():
            return {
                "relation": EventRelationKind.CONTEXT_OR_MODEL_ERROR.value,
                "witness_refs": [],
                "diagnostics": [{"code": "CAUSAL_CYCLE", "message": "Cycle detected in causal graph", "severity": "fatal"}],
            }

        # 3. Cross-stream ancestor check
        left_key = (left_stream, left_seq)
        right_key = (right_stream, right_seq)

        if self.is_ancestor(left_key, right_key):
            return {"relation": EventRelationKind.BEFORE.value, "witness_refs": [left_ref, right_ref], "diagnostics": []}

        if self.is_ancestor(right_key, left_key):
            return {"relation": EventRelationKind.AFTER.value, "witness_refs": [left_ref, right_ref], "diagnostics": []}

        # No justified causal order (AQ39: unrelated counters establish no order)
        return {
            "relation": EventRelationKind.UNKNOWN.value,
            "witness_refs": [],
            "diagnostics": [],
        }


def relate_events(
    left_ref: Dict[str, Any],
    right_ref: Dict[str, Any],
    snapshot: Dict[str, Any],
) -> Dict[str, Any]:
    """[DELEGATING ADAPTER] Evaluates causal ordering between two events across causal streams (AQ39, AQ40).
    
    Delegates generic DAG reachability and cycle detection to PlatformCausalDAG.
    """
    dag = PlatformCausalDAG.from_snapshot(snapshot)
    return dag.relate_events(left_ref, right_ref)



def compare_legal_reference(
    mapping: Dict[str, Any],
    occurrence_ref: Dict[str, Any],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """Relates an event occurrence to a statutory legal interval using ReferenceTimeMapping (AQ42).

    A raw causal counter without mapping returns UNKNOWN.
    """
    map_ref = mapping.get("ref", {"id": "map:default", "revision": 1})
    covered_events = mapping.get("covered_event_refs", [])

    # Check if event is covered by mapping
    occ_key = _event_key(occurrence_ref)
    covered_keys = {_event_key(e) for e in covered_events}

    if occ_key not in covered_keys:
        return {
            "relation": LegalTimeRelationKind.UNKNOWN.value,
            "mapping_ref": map_ref,
            "occurrence_ref": occurrence_ref,
            "evidence_refs": [],
            "diagnostics": [
                {
                    "code": "EVENT_NOT_COVERED_BY_MAPPING",
                    "message": f"Occurrence {occ_key} is not covered by ReferenceTimeMapping '{_ref_id(map_ref)}'",
                    "severity": "warning",
                }
            ],
        }

    rel = mapping.get("relation", LegalTimeRelationKind.UNKNOWN.value)
    return {
        "relation": rel,
        "mapping_ref": map_ref,
        "occurrence_ref": occurrence_ref,
        "evidence_refs": mapping.get("evidence_refs", []),
        "diagnostics": [],
    }
