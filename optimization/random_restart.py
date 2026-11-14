"""
optimization/random_restart.py — Random-Restart Hill Climbing.

Runs hill climbing from multiple random starting points.
Keeps the best solution found across all restarts.
iterations = total across all restarts.
"""
from __future__ import annotations
import time
import math
import random
from optimization.common import (
    tour_cost, random_initial_order, neighbours, make_opt_result
)


def random_restart(
    matrix: dict,
    base: str,
    locations: list[str],
    seed: int | None = 42,
    restarts: int = 10,
    max_iterations: int = 1000,
    **params,
) -> dict:
    """
    Random-Restart Hill Climbing for TSP-style tour optimization.
    Returns a Section 3.3 result dict.
    """
    t0 = time.perf_counter()
    algorithm = "random_restart"
    rng = random.Random(seed)

    if not locations:
        elapsed = (time.perf_counter() - t0) * 1000
        order = [base, base]
        return make_opt_result(algorithm, order, order, 0.0, 0.0, 0, seed, elapsed, "success")

    # Initial order for display (from first restart)
    first_start = random_initial_order(base, locations, rng)
    initial_order = first_start[:]
    initial_cost = tour_cost(initial_order, matrix)

    best_order = None
    best_cost = math.inf
    total_iterations = 0

    # We already consumed one random sequence, track all restarts
    all_starts = [first_start]
    for _ in range(restarts - 1):
        all_starts.append(random_initial_order(base, locations, rng))

    for start_order in all_starts:
        current = start_order[:]
        current_cost = tour_cost(current, matrix)

        for _ in range(max_iterations):
            total_iterations += 1
            best_nb = None
            best_nb_cost = current_cost

            for nb in neighbours(current):
                nb_cost = tour_cost(nb, matrix)
                if nb_cost < best_nb_cost:
                    best_nb_cost = nb_cost
                    best_nb = nb

            if best_nb is None:
                break
            current = best_nb
            current_cost = best_nb_cost

        if current_cost < best_cost:
            best_cost = current_cost
            best_order = current[:]

    elapsed = (time.perf_counter() - t0) * 1000

    if math.isinf(best_cost) or best_order is None:
        return make_opt_result(
            algorithm, initial_order, None, initial_cost, None,
            total_iterations, seed, elapsed, "no_valid_tour",
            "No valid tour exists (unreachable location pair)."
        )

    return make_opt_result(
        algorithm, initial_order, best_order, initial_cost, best_cost,
        total_iterations, seed, elapsed, "success"
    )

