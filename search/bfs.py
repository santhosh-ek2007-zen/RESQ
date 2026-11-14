"""
search/bfs.py — Breadth-First Search.

Finds the route with the fewest edges (NOT minimum cost).
Cycle prevention: nodes added to `visited` when GENERATED (pushed), not when explored.

nodes_generated: incremented each time a node is added to the frontier.
nodes_explored:  incremented each time a node is dequeued and expanded.
"""
from __future__ import annotations
import time
import collections
from search.common import make_result, no_route_result, validate_endpoints


def bfs(city, start: str, goal: str) -> dict:
    """
    Breadth-First Search from start to goal.
    Returns a Section 3.2 result dict.
    NOT guaranteed to return the minimum-cost route.
    """
    err = validate_endpoints(city, start, goal)
    if err:
        err["algorithm"] = "bfs"
        return err

    t0 = time.perf_counter()

    # Trivial case
    if start == goal:
        elapsed = (time.perf_counter() - t0) * 1000
        return make_result("bfs", [start], 0.0, 0, 1, elapsed, "success")

    frontier: collections.deque = collections.deque()
    frontier.append(start)
    visited: set[str] = {start}  # mark visited when generated
    parent: dict[str, str | None] = {start: None}
    nodes_generated = 1
    nodes_explored = 0

    while frontier:
        node = frontier.popleft()
        nodes_explored += 1

        if node == goal:
            # Reconstruct path
            route = []
            cur = node
            while cur is not None:
                route.append(cur)
                cur = parent[cur]
            route.reverse()
            cost = city.route_cost(route)
            elapsed = (time.perf_counter() - t0) * 1000
            return make_result("bfs", route, cost, nodes_explored, nodes_generated, elapsed, "success")

        for nbr, _w in city.neighbors(node):
            if nbr not in visited:
                visited.add(nbr)
                parent[nbr] = node
                frontier.append(nbr)
                nodes_generated += 1

    elapsed = (time.perf_counter() - t0) * 1000
    return no_route_result("bfs", nodes_explored, nodes_generated, elapsed)

