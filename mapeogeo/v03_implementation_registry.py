"""Executable implementation registry for the frozen v0.3 endpoint contracts."""
from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Any, Callable, Sequence

from .contract_primitive_loader import PrimitiveImplementation


def cyclic_compose(payload: dict[str, Any]) -> int:
    return (int(payload["val_a"]) * int(payload["val_b"])) % int(payload["modulus"])


def so3_apply(matrix: Sequence[Sequence[float]], vector: Sequence[float]) -> tuple[float, float, float]:
    return tuple(sum(float(matrix[i][j])*float(vector[j]) for j in range(3)) for i in range(3))


def eigenpair_residual(matrix, value: float, vector) -> float:
    av=[sum(float(matrix[i][j])*float(vector[j]) for j in range(len(vector))) for i in range(len(matrix))]
    return math.sqrt(sum((av[i]-value*float(vector[i]))**2 for i in range(len(vector))))


def graph_laplacian(adjacency) -> tuple[tuple[float, ...], ...]:
    n=len(adjacency)
    return tuple(tuple((sum(adjacency[i]) if i==j else 0.0)-float(adjacency[i][j]) for j in range(n)) for i in range(n))


def projective_normalize(point, *, tolerance: float=1e-15) -> tuple[float, ...]:
    p=tuple(float(v) for v in point)
    pivot=next((v for v in reversed(p) if abs(v)>tolerance),None)
    if pivot is None:
        raise ValueError("zero homogeneous representative has no projective point")
    return tuple(v/pivot for v in p)


def strong_duality_gap(primal_value: float, dual_value: float) -> float:
    return abs(float(primal_value)-float(dual_value))


def orthogonal_project(matrix, vector) -> tuple[float, ...]:
    return tuple(sum(float(matrix[i][j])*float(vector[j]) for j in range(len(vector))) for i in range(len(matrix)))


def gaussian_gram(points, sigma_sq: float) -> tuple[tuple[float, ...], ...]:
    if sigma_sq<=0:
        raise ValueError("sigma_sq must be positive")
    rows=[]
    for x in points:
        row=[]
        for y in points:
            d2=sum((float(a)-float(b))**2 for a,b in zip(x,y))
            row.append(math.exp(-d2/(2.0*sigma_sq)))
        rows.append(tuple(row))
    return tuple(rows)


def v03_implementation_registry() -> tuple[PrimitiveImplementation, ...]:
    return (
        PrimitiveImplementation("GFY.CYCLIC_GROUP_COMPOSITION.v1","eo.group_operands","geo.cayley_endpoint","group composition",1.0,cyclic_compose),
        PrimitiveImplementation("GFY.SO3_ROTATION.v1","eo.rotation_matrix_vector","geo.rotated_vector","SO(3) action",2.0,so3_apply),
        PrimitiveImplementation("GFY.EIGENPAIR_RESIDUAL.v1","eo.eigenpair_candidate","geo.invariant_direction_residual","eigenpair residual",2.0,eigenpair_residual),
        PrimitiveImplementation("GFY.GRAPH_LAPLACIAN_EQUIVALENCE.v1","geo.graph_adjacency","eo.graph_laplacian","construct Laplacian",3.0,graph_laplacian),
        PrimitiveImplementation("GFY.PROJECTIVE_HOMOGENEOUS_EQUIVALENCE.v1","eo.homogeneous_point","geo.projective_point","normalize projective representative",1.0,projective_normalize),
        PrimitiveImplementation("GFY.LP_STRONG_DUALITY_1D.v1","eo.primal_dual_optima","geo.duality_gap","strong-duality residual",1.0,strong_duality_gap),
        PrimitiveImplementation("GFY.ORTHOGONAL_PROJECTION.v1","eo.projection_matrix_vector","geo.nearest_point","orthogonal projection",2.0,orthogonal_project),
        PrimitiveImplementation("GFY.GAUSSIAN_KERNEL_EQUIVALENCE_PSD.v1","geo.point_cloud_sigma","eo.gaussian_gram","Gaussian Gram construction",4.0,gaussian_gram),
    )
