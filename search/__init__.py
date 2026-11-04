"""
Search Algorithms Module
========================
Provides uninformed and informed search algorithms for disaster rescue routing.

Person 1 implementations:
- Breadth-First Search (BFS)
- Depth-First Search (DFS)
- Iterative Deepening Depth-First Search (IDDFS)
- SearchResult: standardized result structure
"""

from .search_result import SearchResult
from .bfs import breadth_first_search
from .dfs import depth_first_search
from .iddfs import iterative_deepening_search

__all__ = [
    "SearchResult",
    "breadth_first_search",
    "depth_first_search",
    "iterative_deepening_search",
]
