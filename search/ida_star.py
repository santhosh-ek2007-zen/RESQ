"""
search/ida_star.py — IDA* Search (Iterative Deepening A*).

Uses iterative deepening on f = g + h.
Guarantees minimum-cost route with admissible heuristic.
Counters accumulated across ALL iterations.
Cycle prevention: path-based (nodes currently on the path).

nodes_generated: each time a node is pushed onto the recursive call stack.
nodes_explored:  each time a node is expanded (not returned as cutoff).
"""
from __future__ import annotations
import time
import math
from search.common import make_result, no_route_result, validate_endpoints
from search.heuristics import euclidean

_FOUND = object()


def _search(
    city,
    path: list[str],
    g: float,
    threshold: float,
    goal: str,
    heuristic,
    counters: dict,
    path_set: set,
    max_iter: int,
) -> tuple[object, float]:
    """
    Recursive IDA* helper.
    Returns (_FOUND, cost) or (_CUTOFF, min_f_exceeded) or (_FAIL, inf).
    """
    node = path[-1]
    f = g + heuristic(city, node, goal)

    if f > threshold + 1e-9:
        return _FOUND if node == goal else object(), f  # return cutoff value

    # Return cutoff marker with f value
    if f > threshold + 1e-9:
        return object(), f

    if node == goal:
        counters["explored"] += 1
        return _FOUND, g

    counters["explored"] += 1
    minimum = math.inf

    neighbours = sorted(city.neighbors(node), key=lambda x: x[0])
    for nbr, w in neighbours:
        if nbr in path_set:
            continue
        path.append(nbr)
        path_set.add(nbr)
        counters["generated"] += 1
        counters["iter"] += 1
        if counters["iter"] > max_iter:
            path.pop()
            path_set.discard(nbr)
            return object(), math.inf

        result, val = _search(city, path, g + w, threshold, goal, heuristic, counters, path_set, max_iter)
        if result is _FOUND:
            return _FOUND, val
        if val < minimum:
            minimum = val
        path.pop()
        path_set.discard(nbr)

    return object(), minimum


def ida_star(city, start: str, goal: str, heuristic=euclidean) -> dict:
    """
    IDA* Search from start to goal.
    Returns a Section 3.2 result dict.
    Guarantees minimum-cost route with admissible heuristic.
    """
    err = validate_endpoints(city, start, goal)
    if err:
        err["algorithm"] = "ida_star"
        return err

    t0 = time.perf_counter()

    if start == goal:
        elapsed = (time.perf_counter() - t0) * 1000
        return make_result("ida_star", [start], 0.0, 0, 1, elapsed, "success")

    threshold = heuristic(city, start, goal)
    counters = {"explored": 0, "generated": 1, "iter": 0}
    n_nodes = len(list(city._g.nodes()))
    max_iter = n_nodes * n_nodes * 100  # safety cap

    while threshold < math.inf:
        path = [start]
        path_set = {start}
        result, val = _search(city, path, 0.0, threshold, goal, heuristic, counters, path_set, max_iter)
        if result is _FOUND:
            cost = city.route_cost(path)
            elapsed = (time.perf_counter() - t0) * 1000
            return make_result(
                "ida_star", path, cost,
                counters["explored"], counters["generated"], elapsed, "success"
            )
        if val == math.inf:
            break
        threshold = val

    elapsed = (time.perf_counter() - t0) * 1000
    return no_route_result("ida_star", counters["explored"], counters["generated"], elapsed)

