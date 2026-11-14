"""
tests/test_optimisation.py — Tests for cost matrix and optimization algorithms.
"""
import math
import pytest
from models.city import build_sample_city
from optimization.cost_matrix import build_cost_matrix, matrix_to_json
from optimization.common import tour_cost, is_valid_tour, brute_force_best
from optimization.hill_climbing import hill_climbing
from optimization.simulated_annealing import simulated_annealing
from optimization.random_walk import random_walk
from optimization.random_restart import random_restart
from search.astar import uniform_cost

ALL_OPT = {
    "hill_climbing": hill_climbing,
    "simulated_annealing": simulated_annealing,
    "random_walk": random_walk,
    "random_restart": random_restart,
}


@pytest.fixture
def city():
    return build_sample_city()


@pytest.fixture
def matrix(city):
    return build_cost_matrix(city, ["A", "C", "H", "D"])


def test_matrix_symmetric(matrix):
    nodes = ["A", "C", "H", "D"]
    for u in nodes:
        for v in nodes:
            assert matrix[(u, v)] == matrix[(v, u)], f"Matrix not symmetric for {u},{v}"


def test_matrix_diagonal_zero(matrix):
    for n in ["A", "C", "H", "D"]:
        assert matrix[(n, n)] == 0.0


def test_matrix_matches_ucs(city, matrix):
    """Matrix entries must match uniform-cost search costs."""
    for u, v in [("A", "C"), ("A", "H"), ("C", "D"), ("H", "D")]:
        ucs = uniform_cost(city, u, v)
        expected = ucs["total_cost"] if ucs["status"] == "success" else math.inf
        assert matrix[(u, v)] == pytest.approx(expected)


def test_matrix_isolated_node_is_inf(city):
    """Isolated J should have inf cost to other nodes."""
    city.block_road("G", "J")
    city.block_road("H", "J")
    city.block_road("J", "K")
    matrix = build_cost_matrix(city, ["A", "J", "C"])
    assert math.isinf(matrix[("A", "J")])
    assert math.isinf(matrix[("J", "C")])


def test_matrix_to_json_converts_inf(city):
    city.block_road("G", "J")
    city.block_road("H", "J")
    city.block_road("J", "K")
    matrix = build_cost_matrix(city, ["A", "J"])
    j = matrix_to_json(matrix)
    assert j["A"]["J"] is None
    assert j["J"]["A"] is None
    assert j["A"]["A"] == 0.0


@pytest.mark.parametrize("alg_name,fn", list(ALL_OPT.items()))
def test_valid_tour_returned(alg_name, fn, matrix):
    base = "A"
    locations = ["C", "H", "D"]
    r = fn(matrix, base, locations, seed=42)
    if r["status"] == "success":
        assert is_valid_tour(r["best_order"], base, locations)
        assert tour_cost(r["best_order"], matrix) == pytest.approx(r["total_cost"])


@pytest.mark.parametrize("alg_name,fn", list(ALL_OPT.items()))
def test_same_seed_same_result(alg_name, fn, matrix):
    base = "A"
    locations = ["C", "H", "D"]
    r1 = fn(matrix, base, locations, seed=7)
    r2 = fn(matrix, base, locations, seed=7)
    assert r1["total_cost"] == r2["total_cost"]
    assert r1["best_order"] == r2["best_order"]


@pytest.mark.parametrize("alg_name,fn", list(ALL_OPT.items()))
def test_unreachable_location_no_valid_tour(alg_name, fn, city):
    """When a location is unreachable, algorithms return no_valid_tour."""
    city.block_road("G", "J")
    city.block_road("H", "J")
    city.block_road("J", "K")
    matrix = build_cost_matrix(city, ["A", "J", "C"])
    r = fn(matrix, "A", ["J", "C"], seed=0)
    assert r["status"] == "no_valid_tour"
    assert r["best_order"] is None


def test_matrix_rebuilds_after_block(city):
    """Cost matrix must reflect blocked roads (version-based invalidation)."""
    nodes = ["A", "E", "H"]
    m1 = build_cost_matrix(city, nodes)
    cost_before = m1[("A", "H")]

    city.block_road("E", "H")
    city.block_road("F", "H")
    m2 = build_cost_matrix(city, nodes)
    cost_after = m2[("A", "H")]

    assert cost_after > cost_before or math.isinf(cost_after)


def test_brute_force_comparison_sa_rr(city):
    """
    On a small instance SA and random_restart should reach near-optimal
    cost in most seeds (statistical over 20 seeds).
    """
    nodes = ["A", "C", "H", "D"]
    matrix = build_cost_matrix(city, nodes)
    base = "A"
    locations = ["C", "H", "D"]
    _, opt_cost = brute_force_best(base, locations, matrix)

    tolerance = 1.10  # within 10% of optimal
    for alg_name, fn in [("simulated_annealing", simulated_annealing),
                          ("random_restart", random_restart)]:
        successes = 0
        for seed in range(20):
            r = fn(matrix, base, locations, seed=seed)
            if r["status"] == "success" and r["total_cost"] is not None:
                if r["total_cost"] <= opt_cost * tolerance:
                    successes += 1
        assert successes >= 12, (
            f"{alg_name} reached near-optimal in only {successes}/20 seeds"
        )

