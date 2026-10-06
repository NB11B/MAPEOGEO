"""Build executable router primitives from endpoint contracts plus implementations.

Endpoint evidence certifies semantic identity.  It never supplies executable
code by itself.  An edge becomes executable only when its semantic_id is also
present in an explicit implementation registry.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Iterable, Mapping, Any

from .work_router import RouteEdge, WorkRouter


@dataclass(frozen=True)
class PrimitiveImplementation:
    semantic_id: str
    source: str
    target: str
    operation: str
    cost: float
    function: Callable[..., Any] | None = None
    materializes: bool = False


@dataclass(frozen=True)
class LoadedPrimitive:
    semantic_id: str
    contract_digest: str
    edge: RouteEdge
    executable: bool


def contract_index(overlay: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    result={}
    for contract in overlay.get("contracts", ()):
        if (
            contract.get("evidence", {}).get("status") == "PASS"
            and contract.get("semantic_id")
            and contract.get("contract_digest")
        ):
            result[str(contract["semantic_id"])]=contract
    return result


def load_primitives(
    overlay: Mapping[str, Any],
    implementations: Iterable[PrimitiveImplementation],
) -> tuple[LoadedPrimitive, ...]:
    contracts=contract_index(overlay)
    loaded=[]
    for impl in implementations:
        contract=contracts.get(impl.semantic_id)
        certified=contract is not None and impl.function is not None
        edge=RouteEdge(
            edge_id=f"contract:{impl.semantic_id}",
            source=impl.source,
            target=impl.target,
            cost=impl.cost,
            certified=certified,
            operation=impl.operation,
            materializes=impl.materializes,
        )
        loaded.append(LoadedPrimitive(
            semantic_id=impl.semantic_id,
            contract_digest="" if contract is None else str(contract["contract_digest"]),
            edge=edge,
            executable=certified,
        ))
    return tuple(loaded)


def router_from_contracts(
    overlay: Mapping[str, Any],
    implementations: Iterable[PrimitiveImplementation],
) -> WorkRouter:
    return WorkRouter(item.edge for item in load_primitives(overlay, implementations))
