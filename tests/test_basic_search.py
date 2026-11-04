"""
Unit Tests for City Model & Uninformed Search
=============================================
Role: Person 1 Deliverables Verification

Test Coverage:
1. City Model & Graph Representation:
   - Node and edge addition, weights, coordinates, metadata.
   - Dynamic road blocking and reopening.
   - Exposing only open roads to algorithms.
   - Route cost computation and validation.
   - Edge cases: invalid locations, negative weights.

2. Uninformed Search Algorithms (BFS, DFS, IDDFS):
   - Blocked roads are NEVER traversed.
   - Routes connect start to destination with continuous valid open roads.
   - Reported route costs strictly match the sum of edge weights.
   - Unreachable destinations handled gracefully (route=None, cost=inf, success=False).
   - Start == destination edge case (route=[start], cost=0.0).
   - BFS guarantees fewest edges (hops).
   - IDDFS guarantees fewest edges (hops), matching BFS edge count.
   - Reopening a blocked road allows search to find the reopened path.
   - Execution on the 16-node benchmark disaster network.
"""

import math
import pytest
from models.city import CityGraph, create_sample_city
from search.bfs import breadth_first_search
from search.dfs import depth_first_search
from search.iddfs import iterative_deepening_search
from search.search_result import SearchResult


# =============================================================================
# City Model Fixtures & Tests
# =============================================================================

@pytest.fixture
def simple_city() -> CityGraph:
    """
    Creates a simple 5-node city for granular assertions:
    A --- (2.0) --- B --- (3.0) --- C
    |                               |
  (10.0)                          (1.0)
    |                               |
    D ------------- (2.0) --------- E
    """
    city = CityGraph("Small City")
    city.add_location("A", pos=(0, 0))
    city.add_location("B", pos=(2, 0))
    city.add_location("C", pos=(5, 0))
    city.add_location("D", pos=(0, -3))
    city.add_location("E", pos=(5, -3))

    city.add_road("A", "B", cost=2.0)
    city.add_road("B", "C", cost=3.0)
    city.add_road("C", "E", cost=1.0)
    city.add_road("A", "D", cost=10.0)
    city.add_road("D", "E", cost=2.0)
    return city


def test_city_creation_and_properties(simple_city: CityGraph):
    """Test node/edge additions and basic graph queries."""
    assert simple_city.num_locations == 5
    assert simple_city.num_roads == 5
    assert simple_city.has_location("A")
    assert not simple_city.has_location("Z")
    assert simple_city.has_road("A", "B")
    assert simple_city.has_road("B", "A")  # Undirected
    assert simple_city.get_road_cost("A", "B") == 2.0
    assert simple_city.get_location_pos("A") == (0, 0)


def test_invalid_locations_and_negative_costs():
    """Verify invalid locations and invalid costs raise errors."""
    city = CityGraph("Error City")
    city.add_location("A")
    with pytest.raises(KeyError):
        city.add_road("A", "NonExistent", cost=5.0)

    city.add_location("B")
    with pytest.raises(ValueError):
        city.add_road("A", "B", cost=-3.0)

    with pytest.raises(ValueError):
        city.add_road("A", "B", cost=0.0)


def test_blocking_and_reopening_roads(simple_city: CityGraph):
    """Test road blocking, unblocking, and neighbor exposure."""
    # Initially all open
    neighbors_a = dict(simple_city.get_open_neighbors("A"))
    assert "B" in neighbors_a and "D" in neighbors_a
    assert not simple_city.is_road_blocked("A", "B")

    # Block road (A, B)
    simple_city.block_road("A", "B")
    assert simple_city.is_road_blocked("A", "B")
    assert simple_city.is_road_blocked("B", "A")

    # Now open neighbors of A should ONLY contain D
    open_neighbors_a = [n for n, _ in simple_city.get_open_neighbors("A")]
    assert "B" not in open_neighbors_a
    assert "D" in open_neighbors_a

    # Reopen road (A, B)
    simple_city.reopen_road("A", "B")
    assert not simple_city.is_road_blocked("A", "B")
    open_neighbors_reopened = [n for n, _ in simple_city.get_open_neighbors("A")]
    assert "B" in open_neighbors_reopened


def test_compute_route_cost(simple_city: CityGraph):
    """Test route cost computation and validation."""
    valid_route = ["A", "B", "C", "E"]
    expected_cost = 2.0 + 3.0 + 1.0  # 6.0
    assert simple_city.compute_route_cost(valid_route) == expected_cost
    assert simple_city.is_valid_route(valid_route, "A", "E")

    # Route traversing blocked road must report infinity
    simple_city.block_road("B", "C")
    assert simple_city.compute_route_cost(valid_route) == float("inf")
    assert not simple_city.is_valid_route(valid_route, "A", "E")

    # Route with non-existent edge
    assert simple_city.compute_route_cost(["A", "C"]) == float("inf")

    # Route with invalid end-points
    assert not simple_city.is_valid_route(valid_route, "A", "C")  # Ends at E, not C


# =============================================================================
# Search Algorithms Tests (BFS, DFS, IDDFS)
# =============================================================================

@pytest.mark.parametrize("search_func,algo_name", [
    (breadth_first_search, "BFS"),
    (depth_first_search, "DFS"),
    (iterative_deepening_search, "IDDFS"),
])
def test_all_search_valid_route(simple_city: CityGraph, search_func, algo_name):
    """Verify all 3 algorithms find a valid connecting route from start to dest."""
    result: SearchResult = search_func(simple_city, "A", "E")
    assert result.success is True
    assert result.has_route is True
    assert result.route is not None
    assert result.route[0] == "A"
    assert result.route[-1] == "E"
    assert simple_city.is_valid_route(result.route, "A", "E")
    # Cost reported must strictly match the graph road weights
    assert result.total_cost == simple_city.compute_route_cost(result.route)
    assert result.nodes_explored > 0
    assert result.nodes_generated > 0
    assert result.execution_time >= 0.0


@pytest.mark.parametrize("search_func", [
    breadth_first_search,
    depth_first_search,
    iterative_deepening_search,
])
def test_blocked_roads_never_used(simple_city: CityGraph, search_func):
    """Verify blocked roads are never traversed by any search algorithm."""
    # Normal route from A to E is A -> B -> C -> E (3 edges)
    # If we block B -> C, algorithms must route via A -> D -> E
    simple_city.block_road("B", "C")
    result: SearchResult = search_func(simple_city, "A", "E")

    assert result.success is True
    assert result.route is not None
    # Ensure (B, C) is not anywhere in the route
    route_edges = list(zip(result.route[:-1], result.route[1:]))
    assert ("B", "C") not in route_edges and ("C", "B") not in route_edges
    assert simple_city.is_valid_route(result.route, "A", "E")
    # Expected detour: A -> D -> E (cost 10 + 2 = 12)
    assert result.route == ["A", "D", "E"]
    assert result.total_cost == 12.0


@pytest.mark.parametrize("search_func", [
    breadth_first_search,
    depth_first_search,
    iterative_deepening_search,
])
def test_unreachable_destination(simple_city: CityGraph, search_func):
    """Verify unreachable destinations return failure result cleanly."""
    # Completely isolate location E by blocking C-E and D-E
    simple_city.block_road("C", "E")
    simple_city.block_road("D", "E")

    result: SearchResult = search_func(simple_city, "A", "E")
    assert result.success is False
    assert result.has_route is False
    assert result.route is None
    assert result.total_cost == float("inf")


@pytest.mark.parametrize("search_func", [
    breadth_first_search,
    depth_first_search,
    iterative_deepening_search,
])
def test_start_equals_destination(simple_city: CityGraph, search_func):
    """Verify handling when start == destination."""
    result: SearchResult = search_func(simple_city, "A", "A")
    assert result.success is True
    assert result.route == ["A"]
    assert result.total_cost == 0.0
    assert result.path_length == 0


def test_bfs_finds_fewest_edges():
    """
    BFS must find the path with fewest edges (hops), even if another path
    has lower cumulative cost.
    
    Graph:
    Start -> N1 -> Dest : 2 hops, weight = 100 + 100 = 200
    Start -> L1 -> L2 -> L3 -> Dest : 4 hops, weight = 1 + 1 + 1 + 1 = 4
    BFS should choose the 2-hop route.
    """
    city = CityGraph("Fewest Edges Test")
    for loc in ["Start", "N1", "Dest", "L1", "L2", "L3"]:
        city.add_location(loc)

    # 2 hops, high cost
    city.add_road("Start", "N1", 100.0)
    city.add_road("N1", "Dest", 100.0)

    # 4 hops, low cost
    city.add_road("Start", "L1", 1.0)
    city.add_road("L1", "L2", 1.0)
    city.add_road("L2", "L3", 1.0)
    city.add_road("L3", "Dest", 1.0)

    bfs_res = breadth_first_search(city, "Start", "Dest")
    assert bfs_res.route == ["Start", "N1", "Dest"]
    assert bfs_res.path_length == 2
    assert bfs_res.total_cost == 200.0

    # IDDFS also guarantees fewest hops!
    iddfs_res = iterative_deepening_search(city, "Start", "Dest")
    assert iddfs_res.route == ["Start", "N1", "Dest"]
    assert iddfs_res.path_length == 2


def test_reopen_road_restores_path():
    """Verify that reopening a road immediately makes it available for search."""
    city = CityGraph("Reopen Test")
    city.add_location("Start")
    city.add_location("Dest")
    city.add_road("Start", "Dest", cost=5.0, blocked=True)

    # Blocked -> unreachable
    res1 = breadth_first_search(city, "Start", "Dest")
    assert not res1.has_route

    # Reopen -> reachable in 1 hop
    city.reopen_road("Start", "Dest")
    res2 = breadth_first_search(city, "Start", "Dest")
    assert res2.has_route
    assert res2.route == ["Start", "Dest"]
    assert res2.total_cost == 5.0


def test_sample_16_location_city_disaster_scenario():
    """Verify search algorithms work across the full 16-node disaster network."""
    city = create_sample_city()
    assert city.num_locations == 16

    # Test route from Rescue Base to Central Hospital
    # Note that Bridge North -> Downtown is initially BLOCKED!
    bfs_res = breadth_first_search(city, "Rescue Base", "Central Hospital")
    assert bfs_res.has_route
    assert city.is_valid_route(bfs_res.route, "Rescue Base", "Central Hospital")

    # Confirm Bridge North -> Downtown was NOT used
    edges = list(zip(bfs_res.route[:-1], bfs_res.route[1:]))
    assert ("Bridge North", "Downtown") not in edges
    assert ("Downtown", "Bridge North") not in edges

    # Verify IDDFS on sample city finds matching hop count
    iddfs_res = iterative_deepening_search(city, "Rescue Base", "Central Hospital")
    assert iddfs_res.has_route
    assert iddfs_res.path_length == bfs_res.path_length

    # Verify DFS finds a valid path
    dfs_res = depth_first_search(city, "Rescue Base", "Central Hospital")
    assert dfs_res.has_route
    assert city.is_valid_route(dfs_res.route, "Rescue Base", "Central Hospital")


def test_result_to_dict_and_subscript():
    """Verify SearchResult supports dictionary conversion and key access for Person 4."""
    city = create_sample_city()
    res = breadth_first_search(city, "Rescue Base", "Hilltop")
    d = res.to_dict()
    assert d["algorithm"] == "BFS"
    assert d["start"] == "Rescue Base"
    assert d["destination"] == "Hilltop"
    assert d["success"] is True
    assert "route" in d
    assert res["route"] == d["route"]
    assert res["total_cost"] == d["total_cost"]
