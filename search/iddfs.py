"""
search/iddfs.py — Iterative Deepening Depth-First Search.

Finds the route with the fewest edges (like BFS) but with memory proportional to depth.
Cycle prevention: PATH-BASED only (not global visited) to preserve completeness at each depth.
Counters accumulated ACROSS all depth iterations.

nodes_generated: each time a node is generated (pushed/recursed into).
nodes_explored:  each time a node is expanded (recursed into, not just returned as cutoff).
"""
from __future__ import annotations
import time
from search.common import make_result, no_route_result, validate_endpoints

_FOUND = object()
_CUTOFF = "cutoff"
_FAIL = "fail"


def _depth_limited_search(
    city,
    node: str,
    goal: str,
    path: list[str],
    limit: int,
    counters: dict,
) -> object:
    """
    Recursive depth-limited DFS.
    path contains nodes currently on the path (cycle prevention).
    Returns _FOUND (path is complete), _CUTOFF, or _FAIL.
    """
    counters["explored"] += 1

    if node == goal:
        return _FOUND

    if limit == 0:
        return _CUTOFF

    cutoff_occurred = False
    neighbours = sorted(city.neighbors(node), key=lambda x: x[0])
    for nbr, _w in neighbours:
        if nbr in path:  # path-based cycle prevention only
            continue
        path.append(nbr)
        counters["generated"] += 1
        result = _depth_limited_search(city, nbr, goal, path, limit - 1, counters)
        if result is _FOUND:
            return _FOUND
        if result is _CUTOFF:
            cutoff_occurred = True
        path.pop()

    return _CUTOFF if cutoff_occurred else _FAIL


def iddfs(city, start: str, goal: str) -> dict:
    """
    Iterative Deepening DFS from start to goal.
    Returns fewest-edge route (same as BFS) but uses O(d) memory.
    NOT cost-optimal. Counters accumulated across all depth iterations.
    """
    err = validate_endpoints(city, start, goal)
    if err:
        err["algorithm"] = "iddfs"
        return err

    t0 = time.perf_counter()

    if start == goal:
        elapsed = (time.perf_counter() - t0) * 1000
        return make_result("iddfs", [start], 0.0, 0, 1, elapsed, "success")

    n_nodes = len(list(city._g.nodes()))  # max useful depth
    counters = {"explored": 0, "generated": 1}  # start node generated

    for limit in range(n_nodes):
        path = [start]
        result = _depth_limited_search(city, start, goal, path, limit, counters)
        if result is _FOUND:
            cost = city.route_cost(path)
            elapsed = (time.perf_counter() - t0) * 1000
            return make_result(
                "iddfs", path, cost,
                counters["explored"], counters["generated"], elapsed, "success"
            )
        if result is _FAIL:
            break  # Graph fully exhausted, no route

    elapsed = (time.perf_counter() - t0) * 1000
    return no_route_result("iddfs", counters["explored"], counters["generated"], elapsed)

