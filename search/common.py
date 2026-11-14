"""
search/common.py — Shared utilities for all search algorithms.

Defines:
- make_result(): builds the standard Section 3.2 result dict.
- validate_endpoints(): checks start/goal exist in city.
- Counter definitions used consistently across all 6 algorithms:
    nodes_generated = every time a node is pushed/added to the frontier.
    nodes_explored  = every time a node is popped/expanded (non-stale).
"""
from __future__ import annotations
import time


def make_result(
    algorithm: str,
    route: list[str] | None,
    cost: float | None,
    explored: int,
    generated: int,
    elapsed_ms: float,
    status: str,
    message: str = "",
) -> dict:
    """Return the canonical Section 3.2 result dict."""
    return {
        "algorithm": algorithm,
        "route": route,
        "total_cost": cost,
        "nodes_explored": explored,
        "nodes_generated": generated,
        "execution_time_ms": round(elapsed_ms, 4),
        "status": status,
        "message": message,
    }


def no_route_result(algorithm: str, explored: int, generated: int, elapsed_ms: float) -> dict:
    return make_result(algorithm, None, None, explored, generated, elapsed_ms, "no_route")


def invalid_input_result(algorithm: str, message: str) -> dict:
    return make_result(algorithm, None, None, 0, 0, 0.0, "invalid_input", message)


def validate_endpoints(city, start: str, destination: str) -> dict | None:
    """
    Return an invalid_input result if either node is unknown.
    Return None if both are valid.
    """
    if not city.has_node(start):
        return invalid_input_result("?", f"Unknown start location '{start}'.")
    if not city.has_node(destination):
        return invalid_input_result("?", f"Unknown destination '{destination}'.")
    return None

