"""
Depth-First Search (DFS) for Disaster Rescue Route Planning
==========================================================
Role: Person 1 (City Model & Uninformed Search)

Specifications:
- Stack-based exploration (LIFO) or recursive search with cycle prevention.
- Route reconstruction via parent tracking or path history.
- Exclusively traverses open, unblocked roads.
- Cycle prevention via visited set.
- Graceful handling of unreachable destinations (route=None, total_cost=inf).
- Note: DFS does NOT guarantee the shortest path nor the lowest-cost route.
- Returns standardized SearchResult:
    (route, total_cost, nodes_explored, nodes_generated, execution_time)
"""

import time
from typing import List, Optional, Dict
from models.city import CityGraph
from .search_result import SearchResult


def depth_first_search(city: CityGraph, start: str, destination: str) -> SearchResult:
    """
    Find a route from start to destination using Depth-First Search (DFS).
    
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
            algorithm="DFS",
            start=start,
            destination=destination,
            success=True,
            metadata={"hops": 0, "optimality": "Not guaranteed"}
        )

    # Stack stores nodes to explore (LIFO)
    # Using parent mapping for clean route reconstruction and cycle prevention
    stack: List[str] = [start]
    visited: set[str] = set()
    parent: Dict[str, Optional[str]] = {start: None}

    nodes_explored = 0
    nodes_generated = 1  # Start node counted as generated
    goal_found = False

    while stack:
        current = stack.pop()
        
        if current in visited:
            continue
            
        visited.add(current)
        nodes_explored += 1

        if current == destination:
            goal_found = True
            break

        # Explore open neighbors; reverse order so natural ordering is probed first
        open_neighbors = city.get_open_neighbors(current)
        for neighbor, edge_cost in reversed(open_neighbors):
            if neighbor not in visited:
                # Update parent if neighbor was not yet discovered
                if neighbor not in parent:
                    parent[neighbor] = current
                nodes_generated += 1
                stack.append(neighbor)

    t_end = time.perf_counter()
    execution_time = t_end - t_start

    # Destination unreachable
    if not goal_found:
        return SearchResult(
            route=None,
            total_cost=float("inf"),
            nodes_explored=nodes_explored,
            nodes_generated=nodes_generated,
            execution_time=execution_time,
            algorithm="DFS",
            start=start,
            destination=destination,
            success=False,
            metadata={"hops": -1, "optimality": "Not guaranteed"}
        )

    # Reconstruct route from destination to start
    route: List[str] = []
    curr: Optional[str] = destination
    while curr is not None:
        route.append(curr)
        curr = parent.get(curr)
    route.reverse()

    total_cost = city.compute_route_cost(route)

    return SearchResult(
        route=route,
        total_cost=total_cost,
        nodes_explored=nodes_explored,
        nodes_generated=nodes_generated,
        execution_time=execution_time,
        algorithm="DFS",
        start=start,
        destination=destination,
        success=True,
        metadata={"hops": len(route) - 1, "optimality": "Not guaranteed"}
    )
