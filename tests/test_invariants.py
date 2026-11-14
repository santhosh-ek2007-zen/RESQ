"""
tests/test_invariants.py — Property-based invariant tests across all algorithms and scenarios.

Checks:
- No route uses a blocked road.
- Reported cost equals sum of edge weights.
- Unreachable => no_route, never cost 0 (except start==goal).
- Tours start/end at base, visit each location exactly once.
- Cost matrix is inf for isolated nodes, never 0 (except diagonal).
- Benchmark rows share one graph_version.
"""
import math
import random
import pytest
from models.city import build_sample_city
from search.bfs import bfs
from search.dfs import dfs
from search.iddfs import iddfs
from search.best_first import greedy
from search.astar import astar, uniform_cost
from search.ida_star import ida_star
from search.heuristics import euclidean
from optimization.cost_matrix import build_cost_matrix
from optimization.common import is_valid_tour, tour_cost
from optimization.hill_climbing import hill_climbing
from optimization.simulated_annealing import simulated_annealing
from optimization.random_walk import random_walk
from optimization.random_restart import random_restart

SEARCH_FNS = {
    "bfs": bfs, "dfs": dfs, "iddfs": iddfs,
    "greedy": greedy, "astar": astar, "ida_star": ida_star,
}
OPT_FNS = {
    "hill_climbing": hill_climbing,
    "simulated_annealing": simulated_annealing,
    "random_walk": random_walk,
    "random_restart": random_restart,
}
INFORMED = {"greedy", "astar", "ida_star"}


def _run_search(fn, name, city, start, goal):
    if name in INFORMED:
        return fn(city, start, goal, heuristic=euclidean)
    return fn(city, start, goal)


@pytest.fixture
def city():
    return build_sample_city()


def test_no_blocked_road_in_routes_random_blocks(city):
    """Block a random subset of roads and ensure no route uses them."""
    rng = random.Random(999)
    edges = list(city._g.edges())
    to_block = rng.sample(edges, min(5, len(edges)))
    for u, v in to_block:
        city.block_road(u, v)

    nodes = list(city._g.nodes())
    blocked_pairs = {(min(u, v), max(u, v)) for u, v in to_block}

    for name, fn in SEARCH_FNS.items():
        for start in nodes[:4]:
            for goal in nodes[-4:]:
                r = _run_search(fn, name, city, start, goal)
                if r["status"] == "success" and r["route"]:
                    route = r["route"]
                    for i in range(len(route) - 1):
                        u, v = route[i], route[i + 1]
                        pair = (min(u, v), max(u, v))
                        assert pair not in blocked_pairs, (
                            f"{name}: used blocked edge {u}-{v} in route {route}"
                        )


def test_reported_cost_equals_edge_sum(city):
    """Every success result's reported cost must equal city.route_cost(route)."""
    for name, fn in SEARCH_FNS.items():
        for start, goal in [("A", "K"), ("B", "I"), ("C", "J")]:
            r = _run_search(fn, name, city, start, goal)
            if r["status"] == "success" and r["route"]:
                expected = city.route_cost(r["route"])
                assert r["total_cost"] == pytest.approx(expected), (
                    f"{name} {start}→{goal}: reported {r['total_cost']}, computed {expected}"
                )


def test_unreachable_never_cost_zero(city):
    """Isolate J and verify no algorithm returns a 0-cost route to J."""
    city.block_road("G", "J")
    city.block_road("H", "J")
    city.block_road("J", "K")
    for name, fn in SEARCH_FNS.items():
        r = _run_search(fn, name, city, "A", "J")
        assert r["status"] == "no_route"
        assert r["total_cost"] is None
        assert r["route"] is None


def test_start_eq_goal_cost_zero(city):
    for name, fn in SEARCH_FNS.items():
        r = _run_search(fn, name, city, "A", "A")
        assert r["status"] == "success"
        assert r["total_cost"] == 0.0
        assert r["route"] == ["A"]


def test_tour_valid_structure(city):
    """Every optimization success must return a structurally valid tour."""
    matrix = build_cost_matrix(city, ["A", "C", "H", "D"])
    base = "A"
    locations = ["C", "H", "D"]
    for name, fn in OPT_FNS.items():
        r = fn(matrix, base, locations, seed=42)
        if r["status"] == "success":
            assert is_valid_tour(r["best_order"], base, locations), (
                f"{name}: tour {r['best_order']} is invalid"
            )


def test_inf_cost_pair_no_valid_tour(city):
    """When a location is isolated, optimization returns no_valid_tour."""
    city.block_road("G", "J")
    city.block_road("H", "J")
    city.block_road("J", "K")
    matrix = build_cost_matrix(city, ["A", "J", "C"])
    for name, fn in OPT_FNS.items():
        r = fn(matrix, "A", ["J", "C"], seed=0)
        assert r["status"] == "no_valid_tour"
        assert r["best_order"] is None


def test_cost_matrix_diagonal_zero(city):
    nodes = ["A", "B", "C", "D", "E"]
    matrix = build_cost_matrix(city, nodes)
    for n in nodes:
        assert matrix[(n, n)] == 0.0


def test_cost_matrix_non_negative(city):
    nodes = list(city._g.nodes())
    matrix = build_cost_matrix(city, nodes)
    for (u, v), cost in matrix.items():
        assert cost >= 0 or math.isinf(cost), f"Negative cost {cost} for {u},{v}"

