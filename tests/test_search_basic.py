"""
tests/test_search_basic.py — Tests for BFS and A* (Phase 3).
"""
import math
import pytest
from models.city import build_sample_city
from search.bfs import bfs
from search.astar import astar, uniform_cost
from search.heuristics import euclidean


@pytest.fixture
def city():
    return build_sample_city()


def test_bfs_finds_route_a_to_k(city):
    r = bfs(city, "A", "K")
    assert r["status"] == "success"
    assert r["route"] is not None
    assert r["route"][0] == "A"
    assert r["route"][-1] == "K"


def test_astar_cost_le_bfs_cost(city):
    bfs_r = bfs(city, "A", "K")
    ast_r = astar(city, "A", "K")
    assert ast_r["status"] == "success"
    assert bfs_r["status"] == "success"
    assert ast_r["total_cost"] <= bfs_r["total_cost"]


def test_route_cost_matches_reported(city):
    for start, goal in [("A", "K"), ("A", "J"), ("B", "I")]:
        r = astar(city, start, goal)
        if r["status"] == "success":
            assert city.route_cost(r["route"]) == pytest.approx(r["total_cost"])


def test_blocked_road_not_in_route(city):
    city.block_road("E", "H")
    city.block_road("F", "H")
    for fn in [bfs, astar]:
        r = fn(city, "A", "K")
        if r["status"] == "success" and r["route"]:
            route = r["route"]
            pairs = set()
            for i in range(len(route) - 1):
                u, v = route[i], route[i + 1]
                pairs.add((min(u, v), max(u, v)))
            assert ("E", "H") not in pairs
            assert ("F", "H") not in pairs


def test_isolated_node_no_route(city):
    """Block G-J, H-J, J-K to isolate J."""
    city.block_road("G", "J")
    city.block_road("H", "J")
    city.block_road("J", "K")
    for fn in [bfs, astar]:
        r = fn(city, "A", "J")
        assert r["status"] == "no_route"
        assert r["route"] is None
        assert r["total_cost"] is None


def test_start_equals_destination(city):
    for fn in [bfs, astar]:
        r = fn(city, "A", "A")
        assert r["status"] == "success"
        assert r["route"] == ["A"]
        assert r["total_cost"] == 0.0


def test_unknown_node_returns_invalid(city):
    r = bfs(city, "A", "Z")
    assert r["status"] == "invalid_input"
    r2 = astar(city, "Z", "K")
    assert r2["status"] == "invalid_input"


def test_astar_optimal_equals_uniform_cost(city):
    """A* with euclidean heuristic must equal uniform_cost on the same graph."""
    for start, goal in [("A", "K"), ("B", "I"), ("D", "G")]:
        ast_r = astar(city, start, goal, heuristic=euclidean)
        ucs_r = uniform_cost(city, start, goal)
        if ast_r["status"] == "success":
            assert ast_r["total_cost"] == pytest.approx(ucs_r["total_cost"])

