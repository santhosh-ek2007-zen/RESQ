"""
search/heuristics.py — Heuristic functions for informed search.

euclidean: admissible and consistent scaled Euclidean distance.
  scale = min(weight / euclid_dist(u,v)) over all graph edges.
  This ensures h(n) never overestimates true cost.

zero: uniform-cost heuristic (effectively Dijkstra / UCS).
"""
from __future__ import annotations
import math


def zero(city, n: str, goal: str) -> float:
    """Zero heuristic — makes A* equivalent to uniform-cost search."""
    return 0.0


def euclidean(city, n: str, goal: str) -> float:
    """
    Scaled Euclidean distance heuristic.
    Admissible: h(n) <= true cost to goal.
    Consistent: h(n) <= cost(n, m) + h(m) for all neighbors m.
    """
    scale = city.min_weight_per_distance
    xn, yn = city.node_position(n)
    xg, yg = city.node_position(goal)
    dist = math.sqrt((xn - xg) ** 2 + (yn - yg) ** 2)
    return scale * dist


HEURISTICS: dict = {
    "zero": zero,
    "euclidean": euclidean,
}

