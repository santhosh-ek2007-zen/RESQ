"""
search/best_first.py — Greedy Best-First Search.

Expands the node with the lowest heuristic value h(n).
NOT cost-optimal. Uses a priority queue ordered by h only.

nodes_generated: incremented each time a node is pushed to the frontier.
nodes_explored:  incremented each time a node is popped/expanded.
"""
from __future__ import annotations
import time
import heapq
from search.common import make_result, no_route_result, validate_endpoints
from search.heuristics import euclidean


def greedy(city, start: str, goal: str, heuristic=euclidean) -> dict:
    """
    Greedy Best-First Search from start to goal.
    Returns a Section 3.2 result dict.
    NOT guaranteed to return the minimum-cost route.
    """
    err = validate_endpoints(city, start, goal)
    if err:
        err["algorithm"] = "greedy"
        return err

    t0 = time.perf_counter()

    if start == goal:
        elapsed = (time.perf_counter() - t0) * 1000
        return make_result("greedy", [start], 0.0, 0, 1, elapsed, "success")

    # (h_value, tie_counter, node)
    counter = 0
    h_start = heuristic(city, start, goal)
    frontier: list = [(h_start, counter, start)]
    visited: set[str] = {start}
    parent: dict[str, str | None] = {start: None}
    nodes_generated = 1
    nodes_explored = 0

    while frontier:
        h, _, node = heapq.heappop(frontier)
        nodes_explored += 1

        if node == goal:
            route = []
            cur = node
            while cur is not None:
                route.append(cur)
                cur = parent[cur]
            route.reverse()
            cost = city.route_cost(route)
            elapsed = (time.perf_counter() - t0) * 1000
            return make_result("greedy", route, cost, nodes_explored, nodes_generated, elapsed, "success")

        for nbr, _w in city.neighbors(node):
            if nbr not in visited:
                visited.add(nbr)
                parent[nbr] = node
                counter += 1
                h_nbr = heuristic(city, nbr, goal)
                heapq.heappush(frontier, (h_nbr, counter, nbr))
                nodes_generated += 1

    elapsed = (time.perf_counter() - t0) * 1000
    return no_route_result("greedy", nodes_explored, nodes_generated, elapsed)

