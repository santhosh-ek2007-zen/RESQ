"""
search/astar.py — A* Search and Uniform-Cost Search.

A* uses f = g + h where h is an admissible, consistent heuristic.
Guarantees minimum-cost route when heuristic is admissible.

uniform_cost = A* with zero heuristic (Dijkstra / UCS).
Used for the cost matrix in optimization/cost_matrix.py.

nodes_generated: every push to the priority queue.
nodes_explored:  every non-stale pop/expansion.
"""
from __future__ import annotations
import time
import heapq
import math
from search.common import make_result, no_route_result, validate_endpoints
from search.heuristics import euclidean, zero


def astar(city, start: str, goal: str, heuristic=euclidean) -> dict:
    """
    A* Search from start to goal.
    Returns a Section 3.2 result dict.
    Guarantees minimum-cost route when heuristic is admissible.
    """
    err = validate_endpoints(city, start, goal)
    if err:
        err["algorithm"] = "astar"
        return err

    t0 = time.perf_counter()

    if start == goal:
        elapsed = (time.perf_counter() - t0) * 1000
        return make_result("astar", [start], 0.0, 0, 1, elapsed, "success")

    # (f, tie_counter, node)
    tie_counter = 0
    g_score: dict[str, float] = {start: 0.0}
    h_start = heuristic(city, start, goal)
    frontier: list = [(h_start, tie_counter, start)]
    parent: dict[str, str | None] = {start: None}
    nodes_generated = 1
    nodes_explored = 0

    while frontier:
        f, _, node = heapq.heappop(frontier)
        g = g_score.get(node, math.inf)

        # Stale entry check: if g stored is better than what we popped, skip
        if f > g + heuristic(city, node, goal) + 1e-9:
            continue

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
            return make_result("astar", route, cost, nodes_explored, nodes_generated, elapsed, "success")

        for nbr, w in city.neighbors(node):
            tentative_g = g + w
            if tentative_g < g_score.get(nbr, math.inf):
                g_score[nbr] = tentative_g
                parent[nbr] = node
                tie_counter += 1
                f_nbr = tentative_g + heuristic(city, nbr, goal)
                heapq.heappush(frontier, (f_nbr, tie_counter, nbr))
                nodes_generated += 1

    elapsed = (time.perf_counter() - t0) * 1000
    return no_route_result("astar", nodes_explored, nodes_generated, elapsed)


def uniform_cost(city, start: str, goal: str) -> dict:
    """
    Uniform-Cost Search (A* with zero heuristic).
    Guarantees minimum-cost route. Used for cost matrix construction.
    """
    result = astar(city, start, goal, heuristic=zero)
    result["algorithm"] = "astar"  # keep algorithm label consistent
    return result

