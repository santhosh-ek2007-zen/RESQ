"""
optimization/hill_climbing.py — Steepest-Ascent Hill Climbing.

Starts from a random tour order.
At each iteration, evaluates ALL neighbours and moves to the best strictly-better one.
Stops at a local optimum or max_iterations.
iterations = number of improvement rounds attempted.
"""
from __future__ import annotations
import time
import math
import random
from optimization.common import (
    tour_cost, random_initial_order, neighbours, make_opt_result
)


def hill_climbing(
    matrix: dict,
    base: str,
    locations: list[str],
    seed: int | None = 42,
    max_iterations: int = 1000,
    **params,
) -> dict:
    """
    Steepest-Ascent Hill Climbing for TSP-style tour optimization.
    Returns a Section 3.3 result dict.
    """
    t0 = time.perf_counter()
    algorithm = "hill_climbing"
    rng = random.Random(seed)

    if not locations:
        # Trivial: base only
        elapsed = (time.perf_counter() - t0) * 1000
        order = [base, base]
        return make_opt_result(algorithm, order, order, 0.0, 0.0, 0, seed, elapsed, "success")

    current = random_initial_order(base, locations, rng)
    current_cost = tour_cost(current, matrix)
    initial_order = current[:]
    initial_cost = current_cost

    iterations = 0
    for _ in range(max_iterations):
        iterations += 1
        best_neighbour = None
        best_cost = current_cost

        for nb in neighbours(current):
            nb_cost = tour_cost(nb, matrix)
            if nb_cost < best_cost:
                best_cost = nb_cost
                best_neighbour = nb

        if best_neighbour is None:
            break  # local optimum reached
        current = best_neighbour
        current_cost = best_cost

    elapsed = (time.perf_counter() - t0) * 1000

    if math.isinf(current_cost):
        return make_opt_result(
            algorithm, initial_order, None, initial_cost, None,
            iterations, seed, elapsed, "no_valid_tour",
            "No valid tour exists (unreachable location pair)."
        )

    return make_opt_result(
        algorithm, initial_order, current, initial_cost, current_cost,
        iterations, seed, elapsed, "success"
    )

