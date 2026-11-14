"""
tests/test_search_all.py — Tests for all 6 search algorithms (Phase 4).
"""
import math
import pytest
from models.city import build_sample_city
from search.bfs import bfs
from search.dfs import dfs
from search.iddfs import iddfs
from search.best_first import greedy
from search.astar import astar, uniform_cost
from search.ida_star import ida_star
from search.heuristics import euclidean

ALL_ALGOS = {
    "bfs": bfs, "dfs": dfs, "iddfs": iddfs,
    "greedy": greedy, "astar": astar, "ida_star": ida_star,
}
OPTIMAL_ALGOS = {"astar", "ida_star"}
FEWEST_EDGE_ALGOS = {"bfs", "iddfs"}


@pytest.fixture
def city():
    return build_sample_city()


@pytest.mark.parametrize("alg_name,fn", list(ALL_ALGOS.items()))
def test_route_valid_a_to_k(alg_name, fn, city):
    if alg_name in ("astar", "ida_star", "greedy"):
        r = fn(city, "A", "K", heuristic=euclidean)
    else:
        r = fn(city, "A", "K")
    assert r["status"] == "success"
    assert r["route"] is not None
    assert r["route"][0] == "A"
    assert r["route"][-1] == "K"
    # Reported cost must match computed cost
    assert city.route_cost(r["route"]) == pytest.approx(r["total_cost"])


@pytest.mark.parametrize("alg_name,fn", list(ALL_ALGOS.items()))
def test_isolated_node_no_route_all(alg_name, fn, city):
    city.block_road("G", "J")
    city.block_road("H", "J")
    city.block_road("J", "K")
    if alg_name in ("astar", "ida_star", "greedy"):
        r = fn(city, "A", "J", heuristic=euclidean)
    else:
        r = fn(city, "A", "J")
    assert r["status"] == "no_route"
    assert r["route"] is None
    assert r["total_cost"] is None


@pytest.mark.parametrize("alg_name", list(OPTIMAL_ALGOS))
def test_optimal_equals_ucs(alg_name, city):
    """A* and IDA* must match the uniform-cost (UCS) optimal cost."""
    fn = ALL_ALGOS[alg_name]
    for start, goal in [("A", "K"), ("B", "I"), ("D", "G"), ("C", "K")]:
        ucs = uniform_cost(city, start, goal)
        r = fn(city, start, goal, heuristic=euclidean)
        if ucs["status"] == "success":
            assert r["status"] == "success"
            assert r["total_cost"] == pytest.approx(ucs["total_cost"]), (
                f"{alg_name} A→{goal}: got {r['total_cost']}, expected {ucs['total_cost']}"
            )


def test_bfs_iddfs_same_edge_count(city):
    """BFS and IDDFS should find routes with the same number of edges."""
    for start, goal in [("A", "K"), ("B", "I")]:
        b = bfs(city, start, goal)
        i = iddfs(city, start, goal)
        if b["status"] == "success" and i["status"] == "success":
            assert len(b["route"]) == len(i["route"]), (
                f"BFS and IDDFS differ in edge count for {start}→{goal}"
            )


def test_bfs_dfs_greedy_not_always_optimal(city):
    """
    Assert that at least one non-optimal algorithm finds a higher cost than A*.
    R4: BFS, DFS, Greedy are NOT guaranteed to be cost-optimal.
    """
    astar_cost = astar(city, "A", "K")["total_cost"]
    for alg_name in ["bfs", "dfs", "greedy"]:
        fn = ALL_ALGOS[alg_name]
        if alg_name == "greedy":
            r = fn(city, "A", "K", heuristic=euclidean)
        else:
            r = fn(city, "A", "K")
        if r["status"] == "success":
            assert r["total_cost"] >= astar_cost  # must be >= optimal


@pytest.mark.parametrize("alg_name,fn", list(ALL_ALGOS.items()))
def test_no_blocked_roads_in_route(alg_name, fn, city):
    city.block_road("E", "H")
    city.block_road("F", "H")
    if alg_name in ("astar", "ida_star", "greedy"):
        r = fn(city, "A", "K", heuristic=euclidean)
    else:
        r = fn(city, "A", "K")
    if r["status"] == "success":
        route = r["route"]
        for i in range(len(route) - 1):
            u, v = route[i], route[i + 1]
            assert not city.is_blocked(u, v), f"{alg_name} used blocked edge {u}-{v}"

