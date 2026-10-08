# SPDX-License-Identifier: MIT
# MAPEOGEO Preproduction Fabric P0
# Python Reference Model: CSR Graph Subsystem & BFS Neighborhood Exploration

from collections import deque
from dataclasses import dataclass
from typing import List, Tuple, Set, Optional

@dataclass
class GraphNode:
    edge_base: int
    edge_count: int
    node_type: int
    flags: int
    version: int

@dataclass
class GraphEdge:
    target_node: int
    relation_type: int
    flags: int

class CSRGraphReference:
    """Golden reference for CSR graph representation and deterministic traversal."""

    def __init__(self, max_nodes=256, max_edges=1024):
        self.max_nodes = max_nodes
        self.max_edges = max_edges
        self.nodes: List[GraphNode] = []
        self.edges: List[GraphEdge] = []

    def load_graph(self, nodes: List[GraphNode], edges: List[GraphEdge]):
        self.nodes = list(nodes)
        self.edges = list(edges)

    def node_lookup(self, node_id: int) -> Tuple[Optional[GraphNode], bool]:
        """Returns (node, error_bounds)."""
        if node_id >= len(self.nodes) or node_id >= self.max_nodes:
            return None, True
        return self.nodes[node_id], False

    def edge_fetch(self, edge_idx: int) -> Tuple[Optional[GraphEdge], bool]:
        """Returns (edge, error_bounds)."""
        if edge_idx >= len(self.edges) or edge_idx >= self.max_edges:
            return None, True
        return self.edges[edge_idx], False

    def follow(self, node_id: int) -> Tuple[Optional[GraphNode], Optional[GraphEdge], bool, bool]:
        """Follows first edge of node_id. Returns (target_node, edge, error_bounds, error_malformed)."""
        node, err_bounds = self.node_lookup(node_id)
        if err_bounds or node is None:
            return None, None, True, False
        if node.edge_count == 0:
            return None, None, False, False
        if node.edge_base >= len(self.edges) or node.edge_base >= self.max_edges:
            return None, None, False, True
        edge = self.edges[node.edge_base]
        if edge.target_node >= len(self.nodes) or edge.target_node >= self.max_nodes:
            return None, edge, False, True
        target = self.nodes[edge.target_node]
        return target, edge, False, False

    def relation_match(self, node_id: int, relation_type: int) -> Tuple[int, List[GraphEdge], bool]:
        """Finds matching relations from node_id. relation_type=0 matches all."""
        node, err_bounds = self.node_lookup(node_id)
        if err_bounds or node is None:
            return 0, [], True
        matched_edges = []
        for i in range(node.edge_base, min(node.edge_base + node.edge_count, len(self.edges))):
            e = self.edges[i]
            if relation_type == 0 or e.relation_type == relation_type:
                matched_edges.append(e)
        return len(matched_edges), matched_edges, False

    def neighborhood(self, start_node: int, radius: int, relation_filter: int = 0) -> Tuple[List[Tuple[int, int]], bool, bool]:
        """
        Deterministic multi-hop BFS neighborhood expansion up to radius (1, 2, or 3).
        Returns:
            neighbors: ordered list of (node_id, distance)
            error_bounds: bool
            error_malformed: bool
        """
        if start_node >= len(self.nodes) or start_node >= self.max_nodes:
            return [], True, False

        visited: Set[int] = {start_node}
        queue = deque([(start_node, 0)])
        result: List[Tuple[int, int]] = []
        err_malformed = False

        while queue:
            curr_node, curr_dist = queue.popleft()
            if curr_dist >= radius:
                continue

            node_rec = self.nodes[curr_node]
            for e_idx in range(node_rec.edge_base, node_rec.edge_base + node_rec.edge_count):
                if e_idx >= len(self.edges) or e_idx >= self.max_edges:
                    err_malformed = True
                    continue
                edge = self.edges[e_idx]
                target = edge.target_node

                if target >= len(self.nodes) or target >= self.max_nodes:
                    err_malformed = True
                    continue

                if relation_filter != 0 and edge.relation_type != relation_filter:
                    continue

                if target not in visited:
                    visited.add(target)
                    result.append((target, curr_dist + 1))
                    if curr_dist + 1 < radius:
                        queue.append((target, curr_dist + 1))

        return result, False, err_malformed
