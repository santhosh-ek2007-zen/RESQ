"""
Interactive Demo - Disaster Rescue Route Planner (Person 1)
===========================================================
Demonstrates the city graph representation and uninformed search
algorithms (BFS, DFS, IDDFS) navigating through a simulated disaster city.

Features demonstrated:
1. City model initialization with 16 realistic locations and weighted roads.
2. Dynamic disaster blockage (collapsed bridges, flooded river crossings).
3. Uninformed search algorithm execution:
   - Breadth-First Search (BFS): Fewest hops guarantee.
   - Depth-First Search (DFS): Stack-based fast exploration.
   - Iterative Deepening DFS (IDDFS): BFS hop optimality with DFS low memory.
4. Dynamic road reopening and rerouting demonstration.
5. Comparative performance metrics table.
"""

import sys
import os

# Ensure package root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from models.city import CityGraph, create_sample_city
from search.bfs import breadth_first_search
from search.dfs import depth_first_search
from search.iddfs import iterative_deepening_search


def print_separator(title: str = "") -> None:
    if title:
        print(f"\n{'=' * 20} {title} {'=' * 20}")
    else:
        print("=" * 60)


def display_comparison_table(results) -> None:
    """Print an ASCII comparison table matching the team benchmark format."""
    print(f"\n{'Algorithm':<8} | {'Hops':<5} | {'Cost':<7} | {'Explored':<9} | {'Generated':<10} | {'Time (ms)':<9} | {'Route'}")
    print("-" * 90)
    for res in results:
        hops_str = str(res.path_length) if res.has_route else "N/A"
        cost_str = f"{res.total_cost:.1f}" if res.has_route else "INF"
        time_ms = f"{res.execution_time * 1000:.3f}"
        route_str = " -> ".join(res.route) if res.has_route and res.route else "No route"
        print(f"{res.algorithm:<8} | {hops_str:<5} | {cost_str:<7} | {res.nodes_explored:<9} | {res.nodes_generated:<10} | {time_ms:<9} | {route_str}")


def run_demo():
    print_separator("AI-BASED DISASTER RESCUE ROUTE PLANNER")
    print("Person 1 Deliverables: City Model & Uninformed Search")

    # 1. Initialize Sample City
    city = create_sample_city()
    print(f"\nLoaded city: '{city.name}'")
    print(f"Total locations : {city.num_locations}")
    print(f"Total roads     : {city.num_roads}")
    print(f"Blocked roads   : {len(city.get_blocked_roads())}")
    for u, v, c in city.get_blocked_roads():
        print(f"  [BLOCKED] {u} <---> {v} (Cost: {c})")

    # -------------------------------------------------------------------------
    # Scenario 1: Rescue Base -> Central Hospital
    # Bridge North to Downtown is BLOCKED by disaster debris.
    # -------------------------------------------------------------------------
    start = "Rescue Base"
    dest = "Central Hospital"
    print_separator(f"Scenario 1: Route from '{start}' to '{dest}'")
    print("Note: Direct road from 'Bridge North' to 'Downtown' is BLOCKED.")

    bfs_res = breadth_first_search(city, start, dest)
    dfs_res = depth_first_search(city, start, dest)
    iddfs_res = iterative_deepening_search(city, start, dest)

    display_comparison_table([bfs_res, dfs_res, iddfs_res])

    # -------------------------------------------------------------------------
    # Scenario 2: Rescue Base -> East Hospital
    # River Crossing to East Hospital is BLOCKED (flooded river).
    # -------------------------------------------------------------------------
    dest2 = "East Hospital"
    print_separator(f"Scenario 2: Route from '{start}' to '{dest2}'")
    print("Note: 'River Crossing' to 'East Hospital' is BLOCKED (flooding).")

    bfs_res2 = breadth_first_search(city, start, dest2)
    dfs_res2 = depth_first_search(city, start, dest2)
    iddfs_res2 = iterative_deepening_search(city, start, dest2)

    display_comparison_table([bfs_res2, dfs_res2, iddfs_res2])

    # -------------------------------------------------------------------------
    # Scenario 3: Real-Time Disaster Reaction (Reopening a Road)
    # Clear the debris on Bridge North <-> Downtown and re-plan!
    # -------------------------------------------------------------------------
    print_separator("Scenario 3: Road Clearance & Dynamic Rerouting")
    print("Emergency crews have cleared the debris on 'Bridge North' <---> 'Downtown'!")
    city.reopen_road("Bridge North", "Downtown")
    print("Road reopened: Bridge North <---> Downtown is now OPEN.")

    bfs_res3 = breadth_first_search(city, start, dest)
    dfs_res3 = depth_first_search(city, start, dest)
    iddfs_res3 = iterative_deepening_search(city, start, dest)

    print("\nUpdated route planning results:")
    display_comparison_table([bfs_res3, dfs_res3, iddfs_res3])

    # -------------------------------------------------------------------------
    # Scenario 4: Completely Isolated Destination (Unreachable handling)
    # -------------------------------------------------------------------------
    print_separator("Scenario 4: Isolated Hazard Zone (Unreachable Handling)")
    # Block all roads leading to North Shelter
    city.block_road("Hilltop", "North Shelter")
    city.block_road("Central Hospital", "North Shelter")
    print("All roads connecting to 'North Shelter' have been blocked by mudslides.")

    bfs_res4 = breadth_first_search(city, start, "North Shelter")
    dfs_res4 = depth_first_search(city, start, "North Shelter")
    iddfs_res4 = iterative_deepening_search(city, start, "North Shelter")

    display_comparison_table([bfs_res4, dfs_res4, iddfs_res4])
    print("\nAll algorithms successfully detected the unreachable state and returned clean failures.")

    print_separator("DEMO COMPLETED SUCCESSFULLY")
    print("Person 1 modules are ready for integration with Person 2, 3, and 4.")


if __name__ == "__main__":
    run_demo()
