"""
app/services.py — Orchestration layer between Flask routes and algorithms.

Holds the shared city singleton.
Provides run_search, run_optimise, run_benchmark.
Flask routes are thin: they validate HTTP, call services, return JSON.
"""
from __future__ import annotations
import math
import time
import pandas as pd
import io

from models.city import build_sample_city
from search.bfs import bfs
from search.dfs import dfs
from search.iddfs import iddfs
from search.best_first import greedy
from search.astar import astar, uniform_cost
from search.ida_star import ida_star
from search.heuristics import HEURISTICS
from optimization.cost_matrix import CostMatrixCache, matrix_to_json
from optimization.hill_climbing import hill_climbing
from optimization.simulated_annealing import simulated_annealing
from optimization.random_walk import random_walk
from optimization.random_restart import random_restart

# ------------------------------------------------------------------ #
# Shared singletons
# ------------------------------------------------------------------ #

city = build_sample_city()
_matrix_cache = CostMatrixCache()

# Latest benchmark result for CSV export
LATEST_RESULTS: dict | None = None

# ------------------------------------------------------------------ #
# Algorithm registries
# ------------------------------------------------------------------ #

SEARCH_ALGORITHMS: dict = {
    "bfs":      bfs,
    "dfs":      dfs,
    "iddfs":    iddfs,
    "greedy":   greedy,
    "astar":    astar,
    "ida_star": ida_star,
}

OPT_ALGORITHMS: dict = {
    "hill_climbing":       hill_climbing,
    "simulated_annealing": simulated_annealing,
    "random_walk":         random_walk,
    "random_restart":      random_restart,
}

# Human-readable labels and guarantee notes
SEARCH_LABELS: dict = {
    "bfs":      {"label": "Breadth-First Search (BFS)",      "guarantee": "Fewest edges"},
    "dfs":      {"label": "Depth-First Search (DFS)",         "guarantee": "Not guaranteed"},
    "iddfs":    {"label": "Iterative Deepening DFS (IDDFS)",  "guarantee": "Fewest edges"},
    "greedy":   {"label": "Greedy Best-First Search",         "guarantee": "Not guaranteed"},
    "astar":    {"label": "A* Search",                        "guarantee": "Optimal cost"},
    "ida_star": {"label": "IDA* Search",                      "guarantee": "Optimal cost"},
}

OPT_LABELS: dict = {
    "hill_climbing":       "Hill Climbing",
    "simulated_annealing": "Simulated Annealing",
    "random_walk":         "Random Walk (Baseline)",
    "random_restart":      "Random-Restart Hill Climbing",
}

# ------------------------------------------------------------------ #
# City operations
# ------------------------------------------------------------------ #

def get_city_dict() -> dict:
    return city.to_dict()


def block_road(u: str, v: str) -> dict:
    city.block_road(u, v)
    return city.to_dict()


def reopen_road(u: str, v: str) -> dict:
    city.reopen_road(u, v)
    return city.to_dict()


def reset_city() -> dict:
    city.reset()
    return city.to_dict()

# ------------------------------------------------------------------ #
# Search
# ------------------------------------------------------------------ #

def run_search(payload: dict) -> tuple[dict, int]:
    """
    Validate payload, run the requested search algorithm, return (result, http_status).
    """
    algorithm = payload.get("algorithm", "")
    start = payload.get("start", "")
    destination = payload.get("destination", "")
    heuristic_name = payload.get("heuristic", "euclidean")

    if not algorithm:
        return {"status": "invalid_input", "message": "Field 'algorithm' is required."}, 400
    if algorithm not in SEARCH_ALGORITHMS:
        valid = ", ".join(SEARCH_ALGORITHMS.keys())
        return {"status": "invalid_input", "message": f"Unknown algorithm '{algorithm}'. Valid: {valid}."}, 400
    if not start:
        return {"status": "invalid_input", "message": "Field 'start' is required."}, 400
    if not destination:
        return {"status": "invalid_input", "message": "Field 'destination' is required."}, 400
    if not city.has_node(start):
        return {"status": "invalid_input", "message": f"Unknown location '{start}'."}, 400
    if not city.has_node(destination):
        return {"status": "invalid_input", "message": f"Unknown location '{destination}'."}, 400

    heuristic = HEURISTICS.get(heuristic_name, HEURISTICS["euclidean"])
    fn = SEARCH_ALGORITHMS[algorithm]

    # Informed algorithms take heuristic; uninformed ones don't
    if algorithm in ("astar", "ida_star", "greedy"):
        result = fn(city, start, destination, heuristic=heuristic)
    else:
        result = fn(city, start, destination)

    result["algorithm"] = algorithm
    return result, 200

# ------------------------------------------------------------------ #
# Optimization
# ------------------------------------------------------------------ #

def run_optimise(payload: dict) -> tuple[dict, int]:
    """
    Validate payload, run the requested optimization algorithm, return (result, http_status).
    """
    algorithm = payload.get("algorithm", "")
    base = payload.get("base", "")
    locations = payload.get("locations", [])
    seed = payload.get("seed", 42)
    params = payload.get("params", {})

    if not algorithm:
        return {"status": "invalid_input", "message": "Field 'algorithm' is required."}, 400
    if algorithm not in OPT_ALGORITHMS:
        valid = ", ".join(OPT_ALGORITHMS.keys())
        return {"status": "invalid_input", "message": f"Unknown algorithm '{algorithm}'. Valid: {valid}."}, 400
    if not base:
        return {"status": "invalid_input", "message": "Field 'base' is required."}, 400
    if not city.has_node(base):
        return {"status": "invalid_input", "message": f"Unknown base location '{base}'."}, 400
    if not isinstance(locations, list) or len(locations) < 1:
        return {"status": "invalid_input", "message": "Field 'locations' must be a non-empty list."}, 400

    # Validate all location nodes
    for loc in locations:
        if not city.has_node(loc):
            return {"status": "invalid_input", "message": f"Unknown location '{loc}'."}, 400

    # Base must not be in locations
    if base in locations:
        return {"status": "invalid_input", "message": "Base must not appear in the locations list."}, 400

    # No duplicates
    if len(set(locations)) != len(locations):
        return {"status": "invalid_input", "message": "Locations list must not contain duplicates."}, 400

    # Cap locations at 8 for UI sanity
    if len(locations) > 8:
        return {"status": "invalid_input", "message": "Maximum 8 affected locations allowed."}, 400

    # Validate seed
    if seed is not None and not isinstance(seed, int):
        try:
            seed = int(seed)
        except (TypeError, ValueError):
            return {"status": "invalid_input", "message": "Field 'seed' must be an integer or null."}, 400

    # Whitelist allowed params
    allowed_params = {
        "max_iterations", "initial_temp", "cooling_rate", "min_temp", "restarts"
    }
    if params:
        invalid_keys = set(params.keys()) - allowed_params
        if invalid_keys:
            return {"status": "invalid_input", "message": f"Unknown params: {', '.join(invalid_keys)}."}, 400

    # Build cost matrix (cached)
    all_nodes = [base] + list(locations)
    matrix = _matrix_cache.get(city, all_nodes)

    # Run the algorithm
    fn = OPT_ALGORITHMS[algorithm]
    result = fn(matrix, base, list(locations), seed=seed, **params)

    # Also return the matrix for the UI
    result["matrix"] = matrix_to_json(matrix)
    return result, 200

# ------------------------------------------------------------------ #
# Benchmark
# ------------------------------------------------------------------ #

_DEFAULT_SEARCH_PAIRS = [
    ("A", "K"), ("A", "J"), ("B", "I"), ("D", "G"), ("C", "K")
]


def run_benchmark(payload: dict) -> tuple[dict, int]:
    """
    Run search or optimization benchmarks.
    Returns (result_dict, http_status).
    """
    global LATEST_RESULTS

    mode = payload.get("mode", "search")
    if mode not in ("search", "optimise"):
        return {"status": "invalid_input", "message": "Field 'mode' must be 'search' or 'optimise'."}, 400

    algorithms = payload.get("algorithms", [])
    if not algorithms:
        algorithms = list(SEARCH_ALGORITHMS.keys()) if mode == "search" else list(OPT_ALGORITHMS.keys())

    # Validate algorithms
    registry = SEARCH_ALGORITHMS if mode == "search" else OPT_ALGORITHMS
    for alg in algorithms:
        if alg not in registry:
            return {"status": "invalid_input", "message": f"Unknown algorithm '{alg}'."}, 400

    graph_version = city.version
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")

    if mode == "search":
        pairs = payload.get("pairs", None)
        if pairs is None:
            pairs = _DEFAULT_SEARCH_PAIRS
        else:
            # Validate pairs
            for p in pairs:
                if not isinstance(p, (list, tuple)) or len(p) != 2:
                    return {"status": "invalid_input", "message": "Each pair must be [start, destination]."}, 400

        repeats = int(payload.get("repeats", 5))
        repeats = max(1, min(20, repeats))
        heuristic_name = payload.get("heuristic", "euclidean")
        heuristic = HEURISTICS.get(heuristic_name, HEURISTICS["euclidean"])

        rows = []
        for start, goal in pairs:
            if not city.has_node(start) or not city.has_node(goal):
                continue
            for alg in algorithms:
                fn = SEARCH_ALGORITHMS[alg]
                for rep in range(repeats):
                    if alg in ("astar", "ida_star", "greedy"):
                        res = fn(city, start, goal, heuristic=heuristic)
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
                        "execution_time_ms": res.get("execution_time_ms", 0),
                        "route_valid": valid,
                        "graph_version": graph_version,
                        "heuristic": heuristic_name,
                        "repeats": repeats,
                    })

        df = pd.DataFrame(rows)

        # Aggregate: mean/min/max time, mean cost, mean nodes
        if not df.empty:
            agg = df.groupby(["pair", "algorithm"]).agg(
                mean_time=("execution_time_ms", "mean"),
                min_time=("execution_time_ms", "min"),
                max_time=("execution_time_ms", "max"),
                mean_cost=("total_cost", "mean"),
                mean_explored=("nodes_explored", "mean"),
                mean_generated=("nodes_generated", "mean"),
            ).reset_index()
            summary = agg.to_dict(orient="records")
        else:
            summary = []

        LATEST_RESULTS = {
            "mode": mode,
            "timestamp": timestamp,
            "graph_version": graph_version,
            "repeats": repeats,
            "df": df,
        }

        rows_json = _safe_to_records(df)
        return {
            "status": "success",
            "rows": rows_json,
            "summary": _sanitize(summary),
            "meta": {"mode": mode, "graph_version": graph_version, "repeats": repeats, "timestamp": timestamp},
        }, 200

    else:  # optimise
        base = payload.get("base", "A")
        locations = payload.get("locations", [])
        seeds_raw = payload.get("seeds", list(range(20)))
        seeds = [int(s) for s in seeds_raw[:50]]

        if not city.has_node(base):
            return {"status": "invalid_input", "message": f"Unknown base '{base}'."}, 400
        for loc in locations:
            if not city.has_node(loc):
                return {"status": "invalid_input", "message": f"Unknown location '{loc}'."}, 400
        if base in locations:
            return {"status": "invalid_input", "message": "Base must not be in locations."}, 400

        all_nodes = [base] + list(locations)
        matrix = _matrix_cache.get(city, all_nodes)

        rows = []
        for alg in algorithms:
            fn = OPT_ALGORITHMS[alg]
            for seed in seeds:
                res = fn(matrix, base, list(locations), seed=seed)
                rows.append({
                    "algorithm": alg,
                    "seed": seed,
                    "initial_cost": res.get("initial_cost"),
                    "best_cost": res.get("total_cost"),
                    "iterations": res.get("iterations", 0),
                    "execution_time_ms": res.get("execution_time_ms", 0),
                    "status": res["status"],
                    "graph_version": graph_version,
                    "seeds": len(seeds),
                })

        df = pd.DataFrame(rows)

        if not df.empty:
            agg = df.groupby("algorithm").agg(
                mean_best_cost=("best_cost", "mean"),
                std_best_cost=("best_cost", "std"),
                min_best_cost=("best_cost", "min"),
                max_best_cost=("best_cost", "max"),
                success_rate=("status", lambda x: (x == "success").mean()),
            ).reset_index()
            summary = agg.to_dict(orient="records")
        else:
            summary = []

        LATEST_RESULTS = {
            "mode": mode,
            "timestamp": timestamp,
            "graph_version": graph_version,
            "seeds": seeds,
            "df": df,
        }

        rows_json = _safe_to_records(df)
        return {
            "status": "success",
            "rows": rows_json,
            "summary": _sanitize(summary),
            "meta": {"mode": mode, "graph_version": graph_version, "seeds": seeds, "timestamp": timestamp},
        }, 200


def get_results_csv() -> tuple[str | None, str | None]:
    """Return (csv_string, error_message). error_message is None on success."""
    if LATEST_RESULTS is None:
        return None, "No benchmark results available. Run a benchmark first."
    df: pd.DataFrame = LATEST_RESULTS["df"]
    return df.to_csv(index=False), None


# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #

def _sanitize(obj):
    """Replace NaN/inf with None for JSON serialization."""
    import json
    import math

    def _fix(v):
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return None
        return v

    if isinstance(obj, list):
        return [{k: _fix(v) for k, v in row.items()} for row in obj]
    return obj


def _safe_to_records(df: pd.DataFrame) -> list[dict]:
    """Convert DataFrame to records with NaN/inf → None."""
    import math
    records = df.to_dict(orient="records")
    result = []
    for row in records:
        clean = {}
        for k, v in row.items():
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                clean[k] = None
            else:
                clean[k] = v
        result.append(clean)
    return result

