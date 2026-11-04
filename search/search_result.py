"""
Search Result - Shared Output Format for Search Algorithms
==========================================================
Role: Person 1 (City Model & Uninformed Search)

As agreed in the team specification (Section 4):
All search algorithms must return:
- route: list of location names from start to destination, or None / "no route"
- total_cost: sum of road travel weights along the route (inf if unreachable)
- nodes_explored: total number of nodes popped/expanded from frontier
- nodes_generated: total number of candidate nodes created/discovered
- execution_time: wall-clock runtime in seconds

This unified format ensures Person 2 (Informed Search) and Person 4 (Benchmarking
and Visualization) can seamlessly consume and compare results across BFS, DFS,
IDDFS, Greedy Best-First, A*, and IDA*.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


@dataclass
class SearchResult:
    """
    Standardized return object for all graph search algorithms.
    """
    route: Optional[List[str]]
    total_cost: float
    nodes_explored: int
    nodes_generated: int
    execution_time: float
    algorithm: str = ""
    start: str = ""
    destination: str = ""
    success: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def has_route(self) -> bool:
        """True if a valid route was found."""
        return self.success and self.route is not None and len(self.route) > 0

    @property
    def path_length(self) -> int:
        """Number of edges traversed (0 if no route or single node)."""
        if not self.has_route or self.route is None or len(self.route) <= 1:
            return 0
        return len(self.route) - 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for tabular reporting (e.g., Pandas DataFrame)."""
        return {
            "algorithm": self.algorithm,
            "start": self.start,
            "destination": self.destination,
            "success": self.success,
            "route": " -> ".join(self.route) if self.has_route and self.route else "no route",
            "total_cost": self.total_cost if self.has_route else float("inf"),
            "path_length": self.path_length,
            "nodes_explored": self.nodes_explored,
            "nodes_generated": self.nodes_generated,
            "execution_time_sec": self.execution_time,
        }

    def __getitem__(self, item: str) -> Any:
        """Allow subscript access for backward compatibility (e.g. result['route'])."""
        data = self.to_dict()
        if item in data:
            return data[item]
        return getattr(self, item)

    def summary(self) -> str:
        """Human-readable multi-line summary of the search result."""
        status = "SUCCESS" if self.has_route else "FAILED (No Route Found)"
        route_str = " -> ".join(self.route) if self.has_route and self.route else "None"
        cost_str = f"{self.total_cost:.2f}" if self.has_route else "Infinity"
        return (
            f"[{self.algorithm}] {self.start} -> {self.destination}: {status}\n"
            f"  Route: {route_str}\n"
            f"  Total Cost: {cost_str}\n"
            f"  Steps (edges): {self.path_length}\n"
            f"  Nodes Explored: {self.nodes_explored}\n"
            f"  Nodes Generated: {self.nodes_generated}\n"
            f"  Execution Time: {self.execution_time * 1000:.3f} ms"
        )
