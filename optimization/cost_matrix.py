"""
optimization/cost_matrix.py — Build pairwise cost matrix using Uniform-Cost Search.

Rule R5: matrix built with A* (zero heuristic) = UCS, never BFS or Greedy.
Rule R6: matrix rebuilt whenever city.version changes.
Unreachable pairs → math.inf in Python, null in JSON.
"""
from __future__ import annotations
import math
from search.astar import uniform_cost


def build_cost_matrix(city, nodes: list[str]) -> dict:
    """
    Build a symmetric pairwise cost matrix for the given node list.
    Returns dict[(u, v)] = cost (float or math.inf).
    Diagonal = 0.
    """
    matrix: dict = {}
    node_list = list(nodes)

    for i, u in enumerate(node_list):
        matrix[(u, u)] = 0.0
        for v in node_list[i + 1:]:
            result = uniform_cost(city, u, v)
            if result["status"] == "success" and result["total_cost"] is not None:
                cost = float(result["total_cost"])
            else:
                cost = math.inf
            matrix[(u, v)] = cost
            matrix[(v, u)] = cost  # symmetric

    return matrix


class CostMatrixCache:
    """
    Cache the cost matrix keyed by (city.version, frozenset(nodes)).
    Invalidates automatically when city.version changes.
    """

    def __init__(self) -> None:
        self._cache: dict = {}

    def get(self, city, nodes: list[str]) -> dict:
        """Return cached matrix or build and cache a new one."""
        key = (city.version, frozenset(nodes))
        if key not in self._cache:
            self._cache[key] = build_cost_matrix(city, nodes)
            # Keep only the most recent version to avoid stale data bloat
            self._cache = {k: v for k, v in self._cache.items() if k[0] == city.version}
            self._cache[key] = build_cost_matrix(city, nodes)
        return self._cache[key]


def matrix_to_json(matrix: dict) -> dict:
    """
    Convert a cost matrix dict to a JSON-safe nested dict.
    math.inf → null.
    """
    # Collect all unique nodes
    nodes: set[str] = set()
    for u, v in matrix:
        nodes.add(u)
        nodes.add(v)
    node_list = sorted(nodes)

    result = {}
    for u in node_list:
        result[u] = {}
        for v in node_list:
            cost = matrix.get((u, v), math.inf)
            result[u][v] = None if cost == math.inf else cost
    return result

