"""
optimization/common.py — Shared helpers for all optimization algorithms.

Contracts:
- tour: list starting and ending at base, visiting each location exactly once.
- random.Random(seed) instances used exclusively — never global random.
- make_opt_result builds the Section 3.3 result dict.
"""
from __future__ import annotations
import math
import random
import itertools
from typing import Generator


def tour_cost(order: list[str], matrix: dict) -> float:
    """
    Sum of costs for consecutive pairs in a tour.
    Returns math.inf if any pair is unreachable (math.inf in matrix).
    """
    total = 0.0
    for i in range(len(order) - 1):
        c = matrix.get((order[i], order[i + 1]), math.inf)
        if c == math.inf:
            return math.inf
        total += c
    return total


def is_valid_tour(order: list[str], base: str, locations: list[str]) -> bool:
    """
    Check that:
    - order starts and ends at base
    - each location appears exactly once in the interior
    - no extra nodes
    """
    if len(order) < 2:
        return False
    if order[0] != base or order[-1] != base:
        return False
    interior = order[1:-1]
    return sorted(interior) == sorted(locations)


def random_initial_order(base: str, locations: list[str], rng: random.Random) -> list[str]:
    """Return [base] + shuffled(locations) + [base]."""
    locs = list(locations)
    rng.shuffle(locs)
    return [base] + locs + [base]


def neighbours(order: list[str]) -> Generator[list[str], None, None]:
    """
    Generate neighbouring tour orders by swapping two interior positions.
    Interior = order[1:-1] (excludes the base endpoints).
    Also yields 2-opt reversals of interior segments.
    """
    n = len(order)
    # Swap pairs
    for i in range(1, n - 2):
        for j in range(i + 1, n - 1):
            neighbour = order[:]
            neighbour[i], neighbour[j] = neighbour[j], neighbour[i]
            yield neighbour

    # 2-opt reversals of interior segments (length ≥ 2)
    for i in range(1, n - 2):
        for j in range(i + 2, n - 1):
            neighbour = order[:]
            neighbour[i:j + 1] = neighbour[i:j + 1][::-1]
            yield neighbour


def brute_force_best(base: str, locations: list[str], matrix: dict) -> tuple[list[str], float]:
    """
    Find the optimal tour by brute force (for small instances in tests).
    Returns (best_order, best_cost).
    """
    best_order = None
    best_cost = math.inf
    for perm in itertools.permutations(locations):
        order = [base] + list(perm) + [base]
        cost = tour_cost(order, matrix)
        if cost < best_cost:
            best_cost = cost
            best_order = order
    return best_order, best_cost


def make_opt_result(
    algorithm: str,
    initial_order: list[str] | None,
    best_order: list[str] | None,
    initial_cost: float | None,
    best_cost: float | None,
    iterations: int,
    seed: int | None,
    elapsed_ms: float,
    status: str,
    message: str = "",
) -> dict:
    """Build the Section 3.3 optimization result dict."""

    def _fmt_cost(c):
        if c is None or (isinstance(c, float) and math.isinf(c)):
            return None
        return c

    return {
        "algorithm": algorithm,
        "initial_order": initial_order,
        "best_order": best_order,
        "initial_cost": _fmt_cost(initial_cost),
        "total_cost": _fmt_cost(best_cost),
        "iterations": iterations,
        "seed": seed,
        "execution_time_ms": round(elapsed_ms, 4),
        "status": status,
        "message": message,
    }

