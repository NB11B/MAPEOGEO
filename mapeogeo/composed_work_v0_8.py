"""Runtime composition qualification for independently registered primitives v0.8."""
from __future__ import annotations
import math
from typing import Sequence

from .work_router import RouteEdge, WorkRouter
from .v03_implementation_registry import graph_laplacian, gaussian_gram


def symmetric_eigenvalues_2x2(matrix: Sequence[Sequence[float]]) -> tuple[float,float]:
    a=float(matrix[0][0]); b=float(matrix[0][1]); d=float(matrix[1][1])
    tr=a+d
    disc=math.sqrt((a-d)*(a-d)+4*b*b)
    return tuple(sorted(((tr-disc)/2.0,(tr+disc)/2.0)))


def algebraic_connectivity_2node(laplacian) -> float:
    vals=symmetric_eigenvalues_2x2(laplacian)
    return vals[1]


def spectral_radius_2x2(matrix) -> float:
    return max(abs(v) for v in symmetric_eigenvalues_2x2(matrix))


def composition_router() -> WorkRouter:
    return WorkRouter((
        RouteEdge("auto.graph-laplacian","geo.graph_adjacency","eo.graph_laplacian",3.0,True,"v0.3 contract-bound Laplacian"),
        RouteEdge("prim.laplacian.lambda2","eo.graph_laplacian","work.algebraic_connectivity",3.0,True,"second eigenvalue"),
        RouteEdge("auto.gaussian-gram","geo.point_cloud_sigma","eo.gaussian_gram",4.0,True,"v0.3 contract-bound Gaussian Gram"),
        RouteEdge("prim.gram.spectral-radius","eo.gaussian_gram","work.kernel_spectral_radius",3.0,True,"max abs eigenvalue"),
    ))


def execute_graph_connectivity(adjacency) -> float:
    return algebraic_connectivity_2node(graph_laplacian(adjacency))


def execute_kernel_spectral_radius(points, sigma_sq: float) -> float:
    return spectral_radius_2x2(gaussian_gram(points,sigma_sq))
