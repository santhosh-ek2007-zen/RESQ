"""
models/city.py — CityGraph class and sample city builder.

Rules:
- neighbors(n) yields only open edges (blocked=False).
- version increments on every real state change (block/reopen/reset).
- route_cost validates every consecutive pair is an open edge.
- Edge IDs are always sorted: "A-B" not "B-A".
"""
from __future__ import annotations
import math
import networkx as nx
from typing import Generator


def _edge_id(u: str, v: str) -> str:
    """Return canonical edge id with alphabetically sorted endpoints."""
    return f"{min(u,v)}-{max(u,v)}"


class CityGraph:
    def __init__(self) -> None:
        self._g: nx.Graph = nx.Graph()
        self.version: int = 0
        # Store original edges for reset: list of (u, v, weight)
        self._original_edges: list[tuple[str, str, float]] = []

    # ------------------------------------------------------------------ #
    # Build helpers
    # ------------------------------------------------------------------ #

    def add_location(self, node_id: str, label: str, x: float, y: float) -> None:
        """Add a node with display metadata."""
        self._g.add_node(node_id, label=label, x=x, y=y)

    def add_road(self, u: str, v: str, weight: float) -> None:
        """Add an undirected road. Validates weight > 0, nodes exist, no self-loop."""
        if u not in self._g:
            raise ValueError(f"Unknown node '{u}'.")
        if v not in self._g:
            raise ValueError(f"Unknown node '{v}'.")
        if u == v:
            raise ValueError("Self-loops are not allowed.")
        if weight <= 0:
            raise ValueError("Road weight must be positive.")
        self._g.add_edge(u, v, weight=weight, blocked=False)
        self._original_edges.append((u, v, weight))

    # ------------------------------------------------------------------ #
    # Query helpers
    # ------------------------------------------------------------------ #

    def has_node(self, n: str) -> bool:
        return n in self._g

    def has_road(self, u: str, v: str) -> bool:
        return self._g.has_edge(u, v)

    def is_blocked(self, u: str, v: str) -> bool:
        if not self._g.has_edge(u, v):
            return False
        return self._g[u][v].get("blocked", False)

    def neighbors(self, n: str) -> Generator[tuple[str, float], None, None]:
        """Yield (neighbor, weight) for open (non-blocked) edges only."""
        for nbr in self._g.neighbors(n):
            edge = self._g[n][nbr]
            if not edge.get("blocked", False):
                yield nbr, edge["weight"]

    def edge_weight(self, u: str, v: str) -> float | None:
        """Return weight of an open edge, or None if missing/blocked."""
        if not self._g.has_edge(u, v):
            return None
        edge = self._g[u][v]
        if edge.get("blocked", False):
            return None
        return edge["weight"]

    def get_node_attrs(self, n: str) -> dict:
        return dict(self._g.nodes[n])

    # ------------------------------------------------------------------ #
    # Mutation helpers
    # ------------------------------------------------------------------ #

    def block_road(self, u: str, v: str) -> None:
        """Block a road. Idempotent if already blocked. Raises ValueError if missing."""
        if not self._g.has_edge(u, v):
            raise ValueError(f"Road '{_edge_id(u,v)}' does not exist.")
        if not self._g[u][v].get("blocked", False):
            self._g[u][v]["blocked"] = True
            self.version += 1

    def reopen_road(self, u: str, v: str) -> None:
        """Reopen a blocked road. Idempotent if already open. Raises ValueError if missing."""
        if not self._g.has_edge(u, v):
            raise ValueError(f"Road '{_edge_id(u,v)}' does not exist.")
        if self._g[u][v].get("blocked", False):
            self._g[u][v]["blocked"] = False
            self.version += 1

    def reset(self) -> None:
        """Restore all roads to open state."""
        changed = False
        for u, v in self._g.edges():
            if self._g[u][v].get("blocked", False):
                self._g[u][v]["blocked"] = False
                changed = True
        if changed:
            self.version += 1

    # ------------------------------------------------------------------ #
    # Serialization
    # ------------------------------------------------------------------ #

    def to_dict(self) -> dict:
        """Return JSON-compatible dict for /api/city."""
        nodes = []
        for nid, attrs in self._g.nodes(data=True):
            nodes.append({
                "id": nid,
                "label": attrs.get("label", nid),
                "x": attrs.get("x", 0),
                "y": attrs.get("y", 0),
            })

        edges = []
        for u, v, attrs in self._g.edges(data=True):
            eid = _edge_id(u, v)
            edges.append({
                "id": eid,
                "source": min(u, v),
                "target": max(u, v),
                "weight": attrs["weight"],
                "blocked": attrs.get("blocked", False),
            })

        return {"nodes": nodes, "edges": edges, "version": self.version}

    # ------------------------------------------------------------------ #
    # Route cost validator
    # ------------------------------------------------------------------ #

    def route_cost(self, route: list[str]) -> float:
        """
        Return total cost of a route.
        Raises ValueError if any consecutive pair is not an open edge.
        A single-node route costs 0.
        """
        if len(route) == 1:
            return 0.0
        total = 0.0
        for i in range(len(route) - 1):
            u, v = route[i], route[i + 1]
            w = self.edge_weight(u, v)
            if w is None:
                raise ValueError(
                    f"Edge '{_edge_id(u,v)}' is missing or blocked in the route."
                )
            total += w
        return total

    # ------------------------------------------------------------------ #
    # Heuristic support
    # ------------------------------------------------------------------ #

    @property
    def min_weight_per_distance(self) -> float:
        """
        Scale factor for the admissible Euclidean heuristic.
        min over all edges of (weight / euclidean_distance).
        Computed once and cached. Returns 1.0 if no edges have distinct endpoints.
        """
        if hasattr(self, "_scale"):
            return self._scale  # type: ignore[attr-defined]
        scale = math.inf
        for u, v, attrs in self._g.edges(data=True):
            na = self._g.nodes[u]
            nb = self._g.nodes[v]
            dx = na["x"] - nb["x"]
            dy = na["y"] - nb["y"]
            d = math.sqrt(dx * dx + dy * dy)
            if d > 0:
                s = attrs["weight"] / d
                if s < scale:
                    scale = s
        self._scale: float = scale if scale < math.inf else 1.0  # type: ignore[attr-defined]
        return self._scale

    def node_position(self, n: str) -> tuple[float, float]:
        """Return (x, y) of a node."""
        attrs = self._g.nodes[n]
        return attrs["x"], attrs["y"]


# ------------------------------------------------------------------ #
# Sample city factory
# ------------------------------------------------------------------ #

def build_sample_city() -> CityGraph:
    """
    Build the 11-node sample city from the implementation plan (Section 4).
    Returns a fully constructed CityGraph.
    """
    city = CityGraph()

    # Nodes: (id, label, x, y)
    nodes = [
        ("A", "Rescue Base", 10, 50),
        ("B", "Hospital",   30, 20),
        ("C", "School",     30, 50),
        ("D", "Market",     30, 80),
        ("E", "Bridge",     50, 35),
        ("F", "Station",    50, 65),
        ("G", "Park",       70, 15),
        ("H", "Mall",       70, 50),
        ("I", "Stadium",    70, 85),
        ("J", "Airport",    90, 30),
        ("K", "Port",       90, 70),
    ]
    for nid, label, x, y in nodes:
        city.add_location(nid, label, x, y)

    # Edges: (source, target, weight)
    edges = [
        ("A", "B", 6),
        ("A", "C", 4),
        ("A", "D", 6),
        ("B", "C", 5),
        ("B", "E", 4),
        ("C", "D", 4),
        ("C", "E", 5),
        ("C", "F", 5),
        ("D", "F", 5),
        ("E", "F", 4),
        ("E", "G", 5),
        ("E", "H", 4),
        ("F", "H", 4),
        ("F", "I", 5),
        ("G", "H", 5),
        ("G", "J", 5),
        ("H", "J", 5),
        ("H", "K", 5),
        ("I", "K", 5),
        ("J", "K", 6),
    ]
    for u, v, w in edges:
        city.add_road(u, v, w)

    return city

