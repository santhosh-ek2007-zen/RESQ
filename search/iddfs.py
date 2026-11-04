"""
Iterative Deepening Depth-First Search (IDDFS) for Disaster Rescue Route Planning
===============================================================================
Role: Person 1 (City Model & Uninformed Search)

Specifications:
- Depth-limited DFS (DLS) repeated with increasing depth limits (0, 1, 2, ...).
- Clear stopping conditions:
  1. Goal reached: reconstruct route and return immediately.
  2. Unreachable: all branches exhausted before hitting cutoff (cutoff_occurred is False),
     meaning the entire connected component has been explored.
  3. Maximum depth limit reached without finding destination.
- Cycle avoidance along the active search path.
- Accurately tracks accumulated nodes explored and nodes generated across iterations.
- Guarantee: Finds the path with the fewest edges (hops), matching BFS completeness.
- Returns standardized SearchResult:
    (route, total_cost, nodes_explored, nodes_generated, execution_time)
"""

import time
from typing import List, Optional, Tuple, Set
from models.city import CityGraph
from .search_result import SearchResult


def _depth_limited_dfs(
    city: CityGraph,
    current: str,
    destination: str,
    depth_limit: int,
    path: List[str],
    path_set: Set[str],
    min_depth: dict,
    stats: dict
) -> Tuple[Optional[List[str]], bool]:
    """
    Recursive Depth-Limited Search (DLS) helper with cycle prevention
    and state pruning for graph search.
    
    :param city: The shared CityGraph instance
    :param current: Current location being explored
    :param destination: Goal location
    :param depth_limit: Remaining depth allowed (0 means limit reached)
    :param path: Current path from start to current
    :param path_set: Fast membership set of nodes currently in path (cycle avoidance)
    :param min_depth: Maps node name to shallowest depth it was reached in this iteration
    :param stats: Mutable dictionary tracking 'nodes_explored' and 'nodes_generated'
    :return: (found_route_or_None, cutoff_occurred_boolean)
    """
    stats["nodes_explored"] += 1

    if current == destination:
        return list(path), False

    if depth_limit <= 0:
        # Reached depth boundary; cutoff occurred
        return None, True

    cutoff_occurred = False

    for neighbor, edge_cost in city.get_open_neighbors(current):
        # Cycle prevention along the current search branch
        if neighbor not in path_set:
            next_depth = len(path)
            # Graph search pruning: if neighbor already reached at an equal or shallower depth
            if neighbor in min_depth and min_depth[neighbor] <= next_depth:
                continue

            min_depth[neighbor] = next_depth
            stats["nodes_generated"] += 1

            path.append(neighbor)
            path_set.add(neighbor)

            result_route, sub_cutoff = _depth_limited_dfs(
                city=city,
                current=neighbor,
                destination=destination,
                depth_limit=depth_limit - 1,
                path=path,
                path_set=path_set,
                min_depth=min_depth,
                stats=stats
            )

            path.pop()
            path_set.remove(neighbor)

            if result_route is not None:
                return result_route, False
            if sub_cutoff:
                cutoff_occurred = True

    return None, cutoff_occurred


def iterative_deepening_search(
    city: CityGraph,
    start: str,
    destination: str,
    max_depth: Optional[int] = None
) -> SearchResult:
    """
    Find a route using Iterative Deepening Depth-First Search (IDDFS).
    
    :param city: The shared CityGraph instance
    :param start: Starting location name
    :param destination: Goal destination location name
    :param max_depth: Maximum depth limit (defaults to city.num_locations)
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
            algorithm="IDDFS",
            start=start,
            destination=destination,
            success=True,
            metadata={"hops": 0, "optimality": "Fewest edges", "depth_reached": 0}
        )

    # Set practical default max_depth if not provided
    if max_depth is None:
        # In a graph of N nodes, any simple cycle-free path has at most N - 1 edges
        max_depth = max(city.num_locations, 10)

    stats = {
        "nodes_explored": 0,
        "nodes_generated": 1  # Root node generated
    }

    found_route: Optional[List[str]] = None
    depth_reached = 0

    # Iterative deepening from depth 0 up to max_depth
    for depth in range(0, max_depth + 1):
        depth_reached = depth
        path = [start]
        path_set = {start}

        min_depth = {start: 0}
        found_route, cutoff = _depth_limited_dfs(
            city=city,
            current=start,
            destination=destination,
            depth_limit=depth,
            path=path,
            path_set=path_set,
            min_depth=min_depth,
            stats=stats
        )

        # Stopping Condition 1: Destination found
        if found_route is not None:
            break

        # Stopping Condition 2: No cutoff occurred, meaning the entire reachable
        # component was explored without being constrained by depth limit.
        if not cutoff:
            # Destination is definitively unreachable in this connected component
            break

    t_end = time.perf_counter()
    execution_time = t_end - t_start

    # Stopping Condition 3 or unreachable:
    if found_route is None:
        return SearchResult(
            route=None,
            total_cost=float("inf"),
            nodes_explored=stats["nodes_explored"],
            nodes_generated=stats["nodes_generated"],
            execution_time=execution_time,
            algorithm="IDDFS",
            start=start,
            destination=destination,
            success=False,
            metadata={
                "hops": -1,
                "optimality": "Fewest edges",
                "depth_reached": depth_reached
            }
        )

    total_cost = city.compute_route_cost(found_route)

    return SearchResult(
        route=found_route,
        total_cost=total_cost,
        nodes_explored=stats["nodes_explored"],
        nodes_generated=stats["nodes_generated"],
        execution_time=execution_time,
        algorithm="IDDFS",
        start=start,
        destination=destination,
        success=True,
        metadata={
            "hops": len(found_route) - 1,
            "optimality": "Fewest edges",
            "depth_reached": depth_reached
        }
    )
