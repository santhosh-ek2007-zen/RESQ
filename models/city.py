"""
City Model - Shared Graph Representation for Disaster Rescue Route Planner
===========================================================================
Role: Person 1 (City Model & Uninformed Search)

This module defines the shared city model built on top of NetworkX.
Locations are graph nodes (with coordinates and metadata), and roads are
edges with travel costs (weights) and blocked states.

Design Requirements:
- Independent of any search algorithm.
- Supports blocking and reopening roads dynamically.
- Exposes only currently open roads to search and route-planning algorithms.
- Provides road cost calculation and route validation.
- Includes a sample 16-location disaster network for testing and benchmarking.
"""

from typing import Dict, List, Optional, Set, Tuple, Any
import networkx as nx


class CityGraph:
    """
    Represents the simulated disaster-affected city as a weighted graph.
    
    Nodes represent locations (rescue base, hospitals, shelters, depots, junctions).
    Edges represent road segments with travel costs and a boolean 'blocked' state.
    """

    def __init__(self, name: str = "Disaster City") -> None:
        self.name = name
        # Underlying undirected NetworkX graph
        self._graph = nx.Graph()

    # -------------------------------------------------------------------------
    # Location (Node) Operations
    # -------------------------------------------------------------------------

    def add_location(
        self,
        name: str,
        pos: Optional[Tuple[float, float]] = None,
        label: Optional[str] = None,
        loc_type: str = "junction",
        **metadata: Any
    ) -> None:
        """
        Add a location (node) to the city graph.
        
        :param name: Unique identifier for the location (e.g., 'Hospital', 'Base')
        :param pos: (x, y) 2D coordinates for heuristic estimation and visualization
        :param label: Human-readable display label
        :param loc_type: Category (e.g., 'base', 'hospital', 'shelter', 'depot', 'hazard')
        :param metadata: Any additional key-value properties
        """
        self._graph.add_node(
            name,
            pos=pos if pos is not None else (0.0, 0.0),
            label=label or name,
            loc_type=loc_type,
            **metadata
        )

    def has_location(self, name: str) -> bool:
        """Check whether a location exists in the city graph."""
        return self._graph.has_node(name)

    def get_locations(self) -> List[str]:
        """Return a list of all location identifiers."""
        return list(self._graph.nodes)

    def get_location_pos(self, name: str) -> Tuple[float, float]:
        """
        Get the (x, y) coordinates of a location.
        Raises KeyError if the location does not exist.
        """
        if not self.has_location(name):
            raise KeyError(f"Location '{name}' does not exist in the city graph.")
        return self._graph.nodes[name].get("pos", (0.0, 0.0))

    def get_location_data(self, name: str) -> Dict[str, Any]:
        """Get the attributes dictionary for a location."""
        if not self.has_location(name):
            raise KeyError(f"Location '{name}' does not exist in the city graph.")
        return dict(self._graph.nodes[name])

    @property
    def num_locations(self) -> int:
        """Total number of locations."""
        return self._graph.number_of_nodes()

    # -------------------------------------------------------------------------
    # Road (Edge) Operations
    # -------------------------------------------------------------------------

    def add_road(
        self,
        u: str,
        v: str,
        cost: float,
        blocked: bool = False,
        **metadata: Any
    ) -> None:
        """
        Add an undirected road (edge) between two locations.
        
        :param u: First location name
        :param v: Second location name
        :param cost: Positive travel cost / weight (e.g., time, distance)
        :param blocked: True if road is blocked/impassable after disaster
        """
        if not self.has_location(u):
            raise KeyError(f"Cannot add road: start location '{u}' does not exist.")
        if not self.has_location(v):
            raise KeyError(f"Cannot add road: end location '{v}' does not exist.")
        if cost <= 0:
            raise ValueError(f"Road cost must be strictly positive, got {cost}.")

        self._graph.add_edge(
            u,
            v,
            weight=float(cost),
            blocked=bool(blocked),
            **metadata
        )

    def has_road(self, u: str, v: str) -> bool:
        """Check if an edge exists between u and v (regardless of blocked state)."""
        return self._graph.has_edge(u, v)

    def block_road(self, u: str, v: str) -> None:
        """
        Mark a road as blocked (e.g., collapsed bridge, flood, debris).
        Raises KeyError if the road does not exist.
        """
        if not self.has_road(u, v):
            raise KeyError(f"Road between '{u}' and '{v}' does not exist.")
        self._graph[u][v]["blocked"] = True

    def reopen_road(self, u: str, v: str) -> None:
        """
        Reopen a blocked road (e.g., debris cleared, temporary pontoon erected).
        Raises KeyError if the road does not exist.
        """
        if not self.has_road(u, v):
            raise KeyError(f"Road between '{u}' and '{v}' does not exist.")
        self._graph[u][v]["blocked"] = False

    def is_road_blocked(self, u: str, v: str) -> bool:
        """
        Check if a road is blocked.
        Raises KeyError if the road does not exist.
        """
        if not self.has_road(u, v):
            raise KeyError(f"Road between '{u}' and '{v}' does not exist.")
        return bool(self._graph[u][v].get("blocked", False))

    def get_road_cost(self, u: str, v: str) -> float:
        """
        Get travel cost of a road.
        Raises KeyError if the road does not exist.
        """
        if not self.has_road(u, v):
            raise KeyError(f"Road between '{u}' and '{v}' does not exist.")
        return float(self._graph[u][v]["weight"])

    def set_road_cost(self, u: str, v: str, cost: float) -> None:
        """Update the travel cost of an existing road."""
        if not self.has_road(u, v):
            raise KeyError(f"Road between '{u}' and '{v}' does not exist.")
        if cost <= 0:
            raise ValueError(f"Road cost must be positive, got {cost}.")
        self._graph[u][v]["weight"] = float(cost)

    @property
    def num_roads(self) -> int:
        """Total number of roads (both open and blocked)."""
        return self._graph.number_of_edges()

    # -------------------------------------------------------------------------
    # Search Interface: Exposing Only Open Roads
    # -------------------------------------------------------------------------

    def get_open_neighbors(self, location: str) -> List[Tuple[str, float]]:
        """
        Return open, unblocked neighbors for the given location, along with travel costs.
        Search algorithms use this method to ensure blocked roads are never traversed.
        
        :param location: The current location name
        :return: List of tuples (neighbor_name, edge_cost)
        """
        if not self.has_location(location):
            raise KeyError(f"Location '{location}' does not exist.")

        open_neighbors: List[Tuple[str, float]] = []
        for neighbor, edge_data in self._graph[location].items():
            if not edge_data.get("blocked", False):
                open_neighbors.append((neighbor, float(edge_data["weight"])))
        return open_neighbors

    def get_open_roads(self) -> List[Tuple[str, str, float]]:
        """Return all currently open roads as (u, v, cost)."""
        open_edges: List[Tuple[str, str, float]] = []
        for u, v, data in self._graph.edges(data=True):
            if not data.get("blocked", False):
                open_edges.append((u, v, float(data["weight"])))
        return open_edges

    def get_blocked_roads(self) -> List[Tuple[str, str, float]]:
        """Return all currently blocked roads as (u, v, cost)."""
        blocked_edges: List[Tuple[str, str, float]] = []
        for u, v, data in self._graph.edges(data=True):
            if data.get("blocked", False):
                blocked_edges.append((u, v, float(data["weight"])))
        return blocked_edges

    def get_open_graph(self) -> nx.Graph:
        """
        Return a new NetworkX graph containing all locations and only open roads.
        Helpful for visualization and algorithms that accept a filtered NetworkX object.
        """
        open_g = nx.Graph()
        for node, data in self._graph.nodes(data=True):
            open_g.add_node(node, **data)
        for u, v, data in self._graph.edges(data=True):
            if not data.get("blocked", False):
                open_g.add_edge(u, v, **data)
        return open_g

    def get_full_graph(self) -> nx.Graph:
        """
        Return the raw underlying NetworkX graph containing all nodes and edges
        (including blocked status).
        """
        return self._graph

    # -------------------------------------------------------------------------
    # Route Cost Calculation & Validation
    # -------------------------------------------------------------------------

    def compute_route_cost(self, route: Optional[List[str]]) -> float:
        """
        Compute total cost of a sequential route.
        Validates that:
        1. All nodes exist.
        2. Consecutive nodes have an existing edge.
        3. None of the edges traversed are blocked.
        
        Returns:
            - 0.0 if route has length 0 or 1 (and node exists).
            - float('inf') if route is None, empty, or traverses a blocked / non-existent road.
            - Total sum of weights for a valid unblocked route.
        """
        if route is None or len(route) == 0:
            return float("inf")

        # Single location route
        if len(route) == 1:
            return 0.0 if self.has_location(route[0]) else float("inf")

        total = 0.0
        for i in range(len(route) - 1):
            u, v = route[i], route[i + 1]
            if not self.has_road(u, v):
                return float("inf")
            if self.is_road_blocked(u, v):
                return float("inf")
            total += self.get_road_cost(u, v)

        return total

    def is_valid_route(self, route: Optional[List[str]], start: str, destination: str) -> bool:
        """
        Verify that a route is valid:
        - Starts at start
        - Ends at destination
        - Only uses open roads
        - Has finite cost
        """
        if not route or len(route) == 0:
            return False
        if route[0] != start or route[-1] != destination:
            return False
        cost = self.compute_route_cost(route)
        return cost < float("inf")


# -----------------------------------------------------------------------------
# Factory: Sample 16-Location Disaster Rescue City
# -----------------------------------------------------------------------------

def create_sample_city() -> CityGraph:
    """
    Creates a benchmark disaster scenario city with 16 interconnected locations.
    
    Locations include:
      - 'Rescue Base' (operational HQ)
      - Hospitals: 'Central Hospital', 'East Hospital'
      - Shelters: 'North Shelter', 'South Shelter', 'West Shelter'
      - Depots: 'Depot Alpha', 'Depot Beta'
      - Key junctions & bridges: 'Bridge North', 'Bridge South', 'River Crossing',
        'Downtown', 'Old Town', 'Harbor', 'Airport Road', 'Industrial Zone', 'Hilltop'
        
    Initial Disaster Damage:
      - 'Bridge North' - 'Downtown' is BLOCKED (bridge collapsed).
      - 'River Crossing' - 'East Hospital' is BLOCKED (river flooded road).
    """
    city = CityGraph(name="Metropolis Disaster Zone")

    # Add 16 locations with (x, y) coordinates for distance heuristics & plotting
    locations = [
        ("Rescue Base", (0.0, 0.0), "Rescue Base (HQ)", "base"),
        ("Bridge North", (0.0, 4.0), "North Bridge", "junction"),
        ("Bridge South", (2.0, -3.0), "South Bridge", "junction"),
        ("Downtown", (4.0, 3.0), "Downtown Core", "junction"),
        ("Central Hospital", (4.0, 8.0), "Central Hospital", "hospital"),
        ("North Shelter", (-2.0, 9.0), "North Emergency Shelter", "shelter"),
        ("South Shelter", (4.0, -6.0), "South Evacuation Shelter", "shelter"),
        ("West Shelter", (-6.0, 1.0), "West Community Shelter", "shelter"),
        ("East Hospital", (10.0, 2.0), "East District Hospital", "hospital"),
        ("Depot Alpha", (-3.0, -3.0), "Supply Depot Alpha", "depot"),
        ("Depot Beta", (8.0, 6.0), "Medical Depot Beta", "depot"),
        ("Old Town", (-4.0, 4.0), "Historic Old Town", "junction"),
        ("River Crossing", (6.0, 0.0), "River Crossing Pt", "junction"),
        ("Harbor", (8.0, -4.0), "Maritime Harbor", "junction"),
        ("Industrial Zone", (-3.0, -6.0), "Industrial District", "junction"),
        ("Hilltop", (-1.0, 6.0), "Hilltop Observation", "junction"),
    ]

    for name, pos, label, loc_type in locations:
        city.add_location(name=name, pos=pos, label=label, loc_type=loc_type)

    # Roads with distance/travel costs
    # Format: (u, v, cost, initially_blocked)
    roads = [
        # From Base
        ("Rescue Base", "Bridge North", 4.0, False),
        ("Rescue Base", "Bridge South", 3.6, False),
        ("Rescue Base", "Depot Alpha", 4.2, False),
        ("Rescue Base", "West Shelter", 6.1, False),
        
        # Northern & Central connections
        ("Bridge North", "Downtown", 4.1, True),      # Initially BLOCKED (disaster debris)
        ("Bridge North", "Hilltop", 2.2, False),
        ("Bridge North", "Old Town", 4.0, False),
        ("Hilltop", "North Shelter", 3.2, False),
        ("Hilltop", "Central Hospital", 5.4, False),
        ("Downtown", "Central Hospital", 5.0, False),
        ("Downtown", "Depot Beta", 5.0, False),
        ("Downtown", "River Crossing", 3.6, False),
        ("Central Hospital", "North Shelter", 6.1, False),
        ("Central Hospital", "Depot Beta", 4.5, False),
        
        # Western connections
        ("Old Town", "West Shelter", 3.6, False),
        ("Old Town", "Hilltop", 3.6, False),
        ("West Shelter", "Depot Alpha", 5.0, False),
        
        # Southern & Eastern connections
        ("Depot Alpha", "Industrial Zone", 3.0, False),
        ("Industrial Zone", "Bridge South", 5.8, False),
        ("Bridge South", "South Shelter", 3.6, False),
        ("Bridge South", "River Crossing", 5.0, False),
        ("South Shelter", "Harbor", 4.5, False),
        ("River Crossing", "Harbor", 4.5, False),
        ("River Crossing", "East Hospital", 4.5, True), # Initially BLOCKED (river flooding)
        ("River Crossing", "Depot Beta", 6.3, False),
        ("Depot Beta", "East Hospital", 4.5, False),
        ("Harbor", "East Hospital", 6.3, False),
    ]

    for u, v, cost, blocked in roads:
        city.add_road(u, v, cost, blocked=blocked)

    return city
