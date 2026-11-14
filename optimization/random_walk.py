"""
optimization/random_walk.py — Random Walk (baseline).

Generates max_iterations random valid tours and tracks the best one.
Serves as a baseline for comparing other optimization algorithms.
"""
from __future__ import annotations
import time
import math
import random
from optimization.common import (
    tour_cost, random_initial_order, make_opt_result
)


def random_walk(
    matrix: dict,
    base: str,
    locations: list[str],
    seed: int | None = 42,
    max_iterations: int = 1000,
    **params,
) -> dict:
    """
    Random Walk optimizer: tries max_iterations random tours, keeps the best.
    Returns a Section 3.3 result dict.
    """
    t0 = time.perf_counter()
    algorithm = "random_walk"
    rng = random.Random(seed)

    if not locations:
        elapsed = (time.perf_counter() - t0) * 1000
        order = [base, base]
        return make_opt_result(algorithm, order, order, 0.0, 0.0, 0, seed, elapsed, "success")

    # Generate initial order for display
    initial_order = random_initial_order(base, locations, rng)
    initial_cost = tour_cost(initial_order, matrix)

    best_order = initial_order[:]
    best_cost = initial_cost

    for i in range(max_iterations - 1):
        candidate = random_initial_order(base, locations, rng)
        cost = tour_cost(candidate, matrix)
        if cost < best_cost:
            best_cost = cost
            best_order = candidate[:]

    elapsed = (time.perf_counter() - t0) * 1000

    if math.isinf(best_cost):
        return make_opt_result(
            algorithm, initial_order, None, initial_cost, None,
            max_iterations, seed, elapsed, "no_valid_tour",
            "No valid tour exists (unreachable location pair)."
        )

    return make_opt_result(
        algorithm, initial_order, best_order, initial_cost, best_cost,
        max_iterations, seed, elapsed, "success"
    )

