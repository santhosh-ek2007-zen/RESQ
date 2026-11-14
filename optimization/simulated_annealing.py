"""
optimization/simulated_annealing.py — Simulated Annealing.

Accepts worse solutions with probability exp(-delta/T).
Tracks and returns the BEST-EVER order, not the final one.
Never accepts an infinite-cost (invalid) tour.
"""
from __future__ import annotations
import time
import math
import random
from optimization.common import (
    tour_cost, random_initial_order, neighbours, make_opt_result
)


def simulated_annealing(
    matrix: dict,
    base: str,
    locations: list[str],
    seed: int | None = 42,
    initial_temp: float = 100.0,
    cooling_rate: float = 0.995,
    min_temp: float = 0.01,
    max_iterations: int = 5000,
    **params,
) -> dict:
    """
    Simulated Annealing for TSP-style tour optimization.
    Returns a Section 3.3 result dict.
    """
    t0 = time.perf_counter()
    algorithm = "simulated_annealing"
    rng = random.Random(seed)

    if not locations:
        elapsed = (time.perf_counter() - t0) * 1000
        order = [base, base]
        return make_opt_result(algorithm, order, order, 0.0, 0.0, 0, seed, elapsed, "success")

    current = random_initial_order(base, locations, rng)
    current_cost = tour_cost(current, matrix)
    initial_order = current[:]
    initial_cost = current_cost

    best_order = current[:]
    best_cost = current_cost

    temp = initial_temp
    iterations = 0

    all_neighbours_cache = None

    for _ in range(max_iterations):
        if temp < min_temp:
            break
        iterations += 1

        # Pick a random neighbour
        nb_list = list(neighbours(current))
        if not nb_list:
            break
        nb = rng.choice(nb_list)
        nb_cost = tour_cost(nb, matrix)

        # Never accept infinite-cost (unreachable) tours
        if math.isinf(nb_cost):
            temp *= cooling_rate
            continue

        delta = nb_cost - current_cost
        if delta < 0:
            current = nb
            current_cost = nb_cost
        else:
            prob = math.exp(-delta / temp) if temp > 0 else 0.0
            if rng.random() < prob:
                current = nb
                current_cost = nb_cost

        if current_cost < best_cost:
            best_order = current[:]
            best_cost = current_cost

        temp *= cooling_rate

    elapsed = (time.perf_counter() - t0) * 1000

    if math.isinf(best_cost):
        return make_opt_result(
            algorithm, initial_order, None, initial_cost, None,
            iterations, seed, elapsed, "no_valid_tour",
            "No valid tour exists (unreachable location pair)."
        )

    return make_opt_result(
        algorithm, initial_order, best_order, initial_cost, best_cost,
        iterations, seed, elapsed, "success"
    )

