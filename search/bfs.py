"""
Breadth-First Search (BFS) for Disaster Rescue Route Planning
============================================================
Role: Person 1 (City Model & Uninformed Search)

Specifications:
- Queue-based exploration (FIFO using collections.deque).
- Visited set to prevent revisiting nodes and cycles.
- Parent-based route reconstruction.
- Exclusively uses open roads (ignores blocked roads).
- Handles unreachable cases gracefully (returns route=None, total_cost=inf).
- Guarantee: Finds the path with the fewest edges (hops), NOT necessarily
  the cheapest travel cost.
- Returns standardized SearchResult:
    (route, total_cost, nodes_explored, nodes_generated, execution_time)
"""

import time
from collections import deque
from typing import List, Optional, Dict
from models.city import CityGraph
from .search_result import SearchResult


def breadth_first_search(city: CityGraph, start: str, destination: str) -> SearchResult:
    """
    Find a route from start to destination using Breadth-First Search (BFS).
    
    :param city: The shared CityGraph instance
    :param start: Starting location name
    :param destination: Goal destination location name
    :return: SearchResult with route, cost, node statistics, and execution time
    """
    t_start = time.perf_counter()

    # Input validation
    if not city.has_location(start):
        raise ValueError(f"Start location '{start}' does not exist in the city graph.")
    if not city.has_location(destination):
        raise ValueError(f"Destination '{destination}' does not exist in the city graph.")

    # Edge case: already at destination
    if start == destination:
        t_end = time.perf_counter()
        return SearchResult(
            route=[start],
            total_cost=0.0,
            nodes_explored=1,
            nodes_generated=1,
            execution_time=t_end - t_start,
            algorithm="BFS",
            start=start,
            destination=destination,
            success=True,
            metadata={"hops": 0, "optimality": "Fewest edges"}
        )

    # Queue stores the frontier nodes (FIFO)
    queue: deque[str] = deque([start])
    visited: set[str] = {start}
    parent: Dict[str, Optional[str]] = {start: None}

    nodes_explored = 0
    nodes_generated = 1  # Count root node as generated
    goal_found = False

    while queue:
        current = queue.popleft()
        nodes_explored += 1

        if current == destination:
            goal_found = True
            break

        # Explore only open roads
        for neighbor, edge_cost in city.get_open_neighbors(current):
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = current
                nodes_generated += 1
                queue.append(neighbor)

                # Early check optimization: if neighbor is destination, we can break or continue.
                # In standard BFS graph search, either expand on pop or check on generation.
                # Expanding on pop ensures uniform frontier metrics consistent across textbooks.

    t_end = time.perf_counter()
    execution_time = t_end - t_start

    # Unreachable destination handling
    if not goal_found:
        return SearchResult(
            route=None,
            total_cost=float("inf"),
            nodes_explored=nodes_explored,
            nodes_generated=nodes_generated,
            execution_time=execution_time,
            algorithm="BFS",
            start=start,
            destination=destination,
            success=False,
            metadata={"hops": -1, "optimality": "Fewest edges"}
        )

    # Route reconstruction using parent pointers
    route: List[str] = []
    curr: Optional[str] = destination
    while curr is not None:
        route.append(curr)
        curr = parent.get(curr)
    route.reverse()

    # Calculate actual path cost from edge weights
    total_cost = city.compute_route_cost(route)

    return SearchResult(
        route=route,
        total_cost=total_cost,
        nodes_explored=nodes_explored,
        nodes_generated=nodes_generated,
        execution_time=execution_time,
        algorithm="BFS",
        start=start,
        destination=destination,
        success=True,
        metadata={"hops": len(route) - 1, "optimality": "Fewest edges"}
    )
