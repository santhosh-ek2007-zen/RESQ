"""
experiments/benchmark.py — Standalone benchmark functions.

Used by services.py for the /api/benchmark endpoint.
Can also be run directly for scripted experiments.
"""
from __future__ import annotations
import math
import time
import pandas as pd

from models.city import CityGraph
from search.heuristics import HEURISTICS
from search.astar import astar, uniform_cost
from search.bfs import bfs
from search.dfs import dfs
from search.iddfs import iddfs
from search.best_first import greedy
from search.ida_star import ida_star
from optimization.cost_matrix import build_cost_matrix

SEARCH_FNS = {
    "bfs": bfs, "dfs": dfs, "iddfs": iddfs,
    "greedy": greedy, "astar": astar, "ida_star": ida_star,
}

DEFAULT_PAIRS = [("A", "K"), ("A", "J"), ("B", "I"), ("D", "G"), ("C", "K")]


def benchmark_search(
    city: CityGraph,
    pairs: list[tuple[str, str]] | None = None,
    algorithms: list[str] | None = None,
    heuristic: str = "euclidean",
    repeats: int = 5,
) -> pd.DataFrame:
    """
    Run all requested search algorithms on all pairs, repeats times.
    Asserts graph_version is unchanged throughout (identical conditions).
    Returns a DataFrame with one row per (pair, algorithm, repeat).
    """
    graph_version = city.version
    if pairs is None:
        pairs = DEFAULT_PAIRS
    if algorithms is None:
        algorithms = list(SEARCH_FNS.keys())

    h_fn = HEURISTICS.get(heuristic, HEURISTICS["euclidean"])
    rows = []

    for start, goal in pairs:
        if not city.has_node(start) or not city.has_node(goal):
            continue
        for alg in algorithms:
            fn = SEARCH_FNS[alg]
            for rep in range(repeats):
                if alg in ("astar", "ida_star", "greedy"):
                    res = fn(city, start, goal, heuristic=h_fn)
                else:
                    res = fn(city, start, goal)

                cost = res.get("total_cost")
                route = res.get("route") or []
                valid = False
                if res["status"] == "success" and route:
                    try:
                        city.route_cost(route)
                        valid = True
                    except Exception:
                        valid = False

                rows.append({
                    "pair": f"{start}→{goal}",
                    "start": start,
                    "destination": goal,
                    "algorithm": alg,
                    "repeat": rep + 1,
                    "status": res["status"],
                    "total_cost": cost,
                    "nodes_explored": res.get("nodes_explored", 0),
                    "nodes_generated": res.get("nodes_generated", 0),
                    "execution_time_ms": res.get("execution_time_ms", 0.0),
                    "route_valid": valid,
                    "graph_version": graph_version,
                    "heuristic": heuristic,
                    "repeats": repeats,
                })

    assert city.version == graph_version, "Graph mutated during benchmark!"
    return pd.DataFrame(rows)


def benchmark_optimisation(
    city: CityGraph,
    base: str,
    locations: list[str],
    algorithms: list[str],
    seeds=None,
    params: dict | None = None,
) -> pd.DataFrame:
    """
    Run all requested optimisation algorithms across all seeds.
    Same cost matrix used for all (built once per version).
    """
    from optimization.hill_climbing import hill_climbing
    from optimization.simulated_annealing import simulated_annealing
    from optimization.random_walk import random_walk
    from optimization.random_restart import random_restart

    OPT_FNS = {
        "hill_climbing": hill_climbing,
        "simulated_annealing": simulated_annealing,
        "random_walk": random_walk,
        "random_restart": random_restart,
    }

    if seeds is None:
        seeds = list(range(20))
    if params is None:
        params = {}

    graph_version = city.version
    all_nodes = [base] + list(locations)
    matrix = build_cost_matrix(city, all_nodes)

    rows = []
    for alg in algorithms:
        fn = OPT_FNS[alg]
        for seed in seeds:
            res = fn(matrix, base, list(locations), seed=seed, **params)
            rows.append({
                "algorithm": alg,
                "seed": seed,
                "initial_cost": res.get("initial_cost"),
                "best_cost": res.get("total_cost"),
                "iterations": res.get("iterations", 0),
                "execution_time_ms": res.get("execution_time_ms", 0.0),
                "status": res["status"],
                "graph_version": graph_version,
                "seeds": len(seeds),
            })

    assert city.version == graph_version, "Graph mutated during benchmark!"
    return pd.DataFrame(rows)

