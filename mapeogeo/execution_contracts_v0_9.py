"""Composable validity/error contracts for mathematical work routes v0.9."""
from __future__ import annotations
from dataclasses import dataclass
import heapq
from typing import Callable, Iterable, Mapping, Any

from .work_router import RouteEdge, Route


@dataclass(frozen=True)
class ExecutionContract:
    edge_id: str
    absolute_error: float
    validity: Callable[[Mapping[str, Any]], bool] = lambda _: True

    def __post_init__(self):
        if self.absolute_error < 0:
            raise ValueError("absolute_error must be nonnegative")


@dataclass(frozen=True)
class QualifiedRoute:
    route: Route
    composed_error: float


class ToleranceRouter:
    """Cheapest certified path satisfying validity and work error tolerance."""

    def __init__(self, edges: Iterable[RouteEdge], contracts: Iterable[ExecutionContract]):
        self.edges=tuple(edges)
        self.contracts={c.edge_id:c for c in contracts}
        self.by_source={}
        for e in self.edges:
            self.by_source.setdefault(e.source,[]).append(e)

    def shortest_qualified(
        self,
        starts: Iterable[str],
        target: str,
        *,
        context: Mapping[str,Any],
        tolerance: float,
    ) -> QualifiedRoute | None:
        if tolerance < 0:
            raise ValueError("tolerance must be nonnegative")
        heap=[]
        best={}
        for s in sorted(set(starts)):
            heapq.heappush(heap,(0.0,0.0,s,(s,),()))
            best[(s,0.0)]=0.0
        while heap:
            cost,error,node,nodes,used=heapq.heappop(heap)
            if node==target and error<=tolerance:
                return QualifiedRoute(Route(nodes,used,cost),error)
            for e in sorted(self.by_source.get(node,()),key=lambda x:x.edge_id):
                if not e.certified:
                    continue
                c=self.contracts.get(e.edge_id)
                if c is None or not c.validity(context):
                    continue
                new_error=error+c.absolute_error
                if new_error>tolerance:
                    continue
                new_cost=cost+e.cost
                # Pareto prune by node and rounded error bucket; preserve accuracy alternatives.
                key=(e.target,round(new_error,15))
                if new_cost>=best.get(key,float("inf")):
                    continue
                best[key]=new_cost
                heapq.heappush(heap,(new_cost,new_error,e.target,nodes+(e.target,),used+(e,)))
        return None
