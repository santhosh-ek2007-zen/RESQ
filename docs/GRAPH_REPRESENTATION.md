# City Graph Representation Documentation
**AI-Based Disaster Rescue Route Planner**  
**Role:** Person 1 (City Model & Uninformed Search)

---

## 1. Overview and Design Principles

The city is represented as an undirected weighted graph \( G = (V, E) \) using **NetworkX**:
- **Vertices (\(V\))**: Critical urban locations including the rescue operational base, hospitals, emergency shelters, supply depots, and transit junctions.
- **Edges (\(E\))**: Road segments connecting adjacent locations, each with a travel cost (weight) and a disaster blockage flag (`blocked`).
- **Encapsulation**: The `CityGraph` class in `models/city.py` completely encapsulates graph storage and manipulation, keeping search algorithms decoupled from graph internals.

---

## 2. Graph Data Structures & Attributes

### 2.1 Location (Node) Attributes
Each node in NetworkX has the following attributes:
| Attribute | Type | Description | Intended Role Usage |
|-----------|------|-------------|---------------------|
| `name` | `str` | Unique location identifier (e.g., `'Rescue Base'`, `'Central Hospital'`) | All team members |
| `pos` | `Tuple[float, float]` | 2D cartesian coordinates `(x, y)` | **Person 2** (distance heuristics), **Person 4** (graph plotting) |
| `label` | `str` | Human-readable label for plots | **Person 4** (visualization) |
| `loc_type` | `str` | Category: `'base'`, `'hospital'`, `'shelter'`, `'depot'`, `'junction'` | **Person 3** (TSP targets), **Person 4** (node coloring) |

### 2.2 Road (Edge) Attributes
Each edge in NetworkX has the following attributes:
| Attribute | Type | Description | Intended Role Usage |
|-----------|------|-------------|---------------------|
| `weight` | `float` | Strictly positive travel cost (travel time / distance) | All search & optimization algorithms |
| `blocked` | `bool` | `True` if impassable due to disaster; `False` if open | **Person 1, 2, 4** |

---

## 3. Public API Reference (`models/city.py`)

### 3.1 Location Operations
```python
city = CityGraph("City Name")

# Add location with coordinates and category
city.add_location(name="Central Hospital", pos=(4.0, 8.0), label="Central Hospital", loc_type="hospital")

# Check existence
city.has_location("Central Hospital")  # Returns True

# Get coordinates
pos = city.get_location_pos("Central Hospital")  # Returns (4.0, 8.0)

# List all locations
locations = city.get_locations()
```

### 3.2 Road Operations & Dynamic Disaster Management
```python
# Add road (undirected, default open)
city.add_road(u="Rescue Base", v="Bridge North", cost=4.0, blocked=False)

# Block road dynamically (e.g. collapsed bridge)
city.block_road("Bridge North", "Downtown")
city.is_road_blocked("Bridge North", "Downtown")  # Returns True

# Reopen road dynamically (e.g. debris cleared)
city.reopen_road("Bridge North", "Downtown")
city.is_road_blocked("Bridge North", "Downtown")  # Returns False

# Query cost
cost = city.get_road_cost("Rescue Base", "Bridge North")  # 4.0
```

### 3.3 Search Algorithm Interface: Exposing Only Open Roads
Search algorithms must **never traverse blocked roads**. Use `get_open_neighbors`:
```python
# Returns list of (neighbor_name, edge_cost) where blocked == False
for neighbor, cost in city.get_open_neighbors(current_node):
    # Expand open neighbor
    ...
```

To get a filtered NetworkX graph with only open edges:
```python
open_nx_graph = city.get_open_graph()
```

To get the full NetworkX graph (for visualization of both open and blocked roads):
```python
full_nx_graph = city.get_full_graph()
```

### 3.4 Route Validation & Cost Calculation
All algorithms must calculate costs consistently:
```python
route = ["Rescue Base", "Bridge North", "Hilltop", "Central Hospital"]
cost = city.compute_route_cost(route)  # Sums edge weights; returns inf if any road is blocked
is_valid = city.is_valid_route(route, start="Rescue Base", destination="Central Hospital")
```

---

## 4. Standard Result Format (`SearchResult`)

All search algorithms (BFS, DFS, IDDFS, Greedy, A*, IDA*) return a unified `SearchResult` instance:

```python
from search import SearchResult

result = SearchResult(
    route=["Rescue Base", "Bridge North", "Hilltop", "Central Hospital"],
    total_cost=11.6,
    nodes_explored=4,
    nodes_generated=7,
    execution_time=0.00042,
    algorithm="BFS",
    start="Rescue Base",
    destination="Central Hospital",
    success=True
)

# Access fields as attributes or dictionary keys:
print(result.route)             # ['Rescue Base', ...]
print(result.total_cost)        # 11.6
print(result.nodes_explored)    # 4
print(result.nodes_generated)   # 7
print(result.execution_time)    # in seconds
print(result["route"])          # Backward-compatible dict access

# Export to Pandas:
import pandas as pd
df = pd.DataFrame([result.to_dict()])
```

When a destination is unreachable:
```python
result.route = None
result.total_cost = float("inf")
result.success = False
```

---

## 5. Integration Guides for Teammates

### For Person 2 (Heuristics & Informed Search)
1. **Coordinates for Heuristics**:
   Call `city.get_location_pos(node)` to get `(x, y)` coordinates.
   - Euclidean distance: `math.hypot(x2 - x1, y2 - y1)`
   - Manhattan distance: `abs(x2 - x1) + abs(y2 - y1)`
   - Zero heuristic: `h(n) = 0.0` (Uniform-Cost Search)
2. **Neighbor Expansion**:
   Use `city.get_open_neighbors(current)` in Greedy Best-First, A*, and IDA*.
3. **Return Format**:
   Return a `SearchResult` with `algorithm="A*"`, `"Greedy"`, or `"IDA*"`.

### For Person 3 (Cost Matrix & Route Improvement)
1. **Generating Pairwise Cost Matrix**:
   Compute all-pairs shortest paths on the open roads using Person 2's A* with `h(n) = 0` (or Dijkstra via NetworkX).
2. **Unreachable Handling**:
   Mark disconnected pairs explicitly with `float('inf')` as required by Section 4.
3. **Dynamic Recalculation**:
   When roads change state, re-run the cost matrix on `city`.

### For Person 4 (Visualization & Benchmarking)
1. **NetworkX Plotting**:
   ```python
   pos = {n: city.get_location_pos(n) for n in city.get_locations()}
   open_roads = [(u, v) for u, v, _ in city.get_open_roads()]
   blocked_roads = [(u, v) for u, v, _ in city.get_blocked_roads()]
   
   # Draw nodes, open edges in green/gray, blocked edges in dashed red!
   ```
2. **Tabular Results**:
   Convert search outputs directly via `result.to_dict()` into a Pandas DataFrame for CSV export and comparison charts.

---

## 6. Built-In 16-Location Benchmark City

Initialized via `create_sample_city()`:
- **16 Locations**:
  `Rescue Base (HQ)`, `Bridge North`, `Bridge South`, `Downtown`, `Central Hospital`, `North Shelter`, `South Shelter`, `West Shelter`, `East Hospital`, `Depot Alpha`, `Depot Beta`, `Old Town`, `River Crossing`, `Harbor`, `Industrial Zone`, `Hilltop`.
- **Initial Disaster Damage**:
  - `Bridge North <-> Downtown`: **BLOCKED** (bridge collapsed).
  - `River Crossing <-> East Hospital`: **BLOCKED** (flooding).
- **Alternate Routes**: Available through northern perimeter or southern harbor transit corridors.
