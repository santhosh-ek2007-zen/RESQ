"""
search/dfs.py — Depth-First Search (iterative).

Finds A route — not guaranteed to be cost-optimal or fewest-edges.
Cycle prevention: global `visited` set.
Deterministic: neighbours sorted alphabetically before pushing.

nodes_generated: incremented each time a node is pushed onto the stack.
nodes_explored:  incremented each time a node is popped.
"""
from __future__ import annotations
import time
from search.common import make_result, no_route_result, validate_endpoints


def dfs(city, start: str, goal: str) -> dict:
    """
    Iterative Depth-First Search from start to goal.
    Returns a Section 3.2 result dict.
    NOT guaranteed to return the minimum-cost or fewest-edge route.
    """
    err = validate_endpoints(city, start, goal)
    if err:
        err["algorithm"] = "dfs"
        return err

    t0 = time.perf_counter()

    if start == goal:
        elapsed = (time.perf_counter() - t0) * 1000
        return make_result("dfs", [start], 0.0, 0, 1, elapsed, "success")

    # Stack contains (node, path_so_far)
    stack: list[tuple[str, list[str]]] = [(start, [start])]
    visited: set[str] = {start}
    nodes_generated = 1
    nodes_explored = 0

    while stack:
        node, path = stack.pop()
        nodes_explored += 1

        if node == goal:
            cost = city.route_cost(path)
            elapsed = (time.perf_counter() - t0) * 1000
            return make_result("dfs", path, cost, nodes_explored, nodes_generated, elapsed, "success")

        # Sort neighbours for determinism, reverse so alphabetically-first is explored first
        neighbours = sorted(city.neighbors(node), key=lambda x: x[0], reverse=True)
        for nbr, _w in neighbours:
            if nbr not in visited:
                visited.add(nbr)
                stack.append((nbr, path + [nbr]))
                nodes_generated += 1

    elapsed = (time.perf_counter() - t0) * 1000
    return no_route_result("dfs", nodes_explored, nodes_generated, elapsed)

