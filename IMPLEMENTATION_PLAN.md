# AI-Based Disaster Rescue Route Planner: Implementation Plan (for Antigravity)

> **Audience:** an AI coding agent (Google Antigravity) plus the human team supervising it.
> **Source:** "Revised Team Guide: Local Web Application Edition".
> **Goal:** a local Flask web app (`http://127.0.0.1:5000`) that visualises a simulated city graph, runs search and route-improvement algorithms written in Python, compares them, and exports CSV. All results are read in the browser, never from the terminal.

---

## 0. How to use this document with Antigravity

1. Open the project folder as the Antigravity workspace.
2. Save this file as `docs/IMPLEMENTATION_PLAN.md` and put the **Standing Rules** (Section 1) into your workspace rules file (e.g. `.agent/rules/project.md`, or `AGENTS.md` if your version reads it), so every agent session sees them.
3. Execute **one phase at a time** (Sections 5 to 11). Each phase has: goal, files, detailed steps, acceptance checks, and a ready-to-paste **Agent Prompt**.
4. Do not start the next phase until the current phase's **Exit Check** passes. Ask the agent to produce a short verification report (commands run, test output, and for UI phases a browser check) before moving on.
5. Commit after every phase (`git commit -m "phase N: ..."`).

---

## 1. Standing rules (never violate)

| # | Rule |
|---|------|
| R1 | **Algorithms stay in Python.** Never reimplement search or optimisation in JavaScript. The browser only sends JSON and renders results. |
| R2 | **Flask routes are thin.** A route validates input, calls `services.py`, returns JSON. No algorithm logic in `routes.py`. |
| R3 | **Frontend depends only on the agreed result schema** (Section 3), never on algorithm internals. |
| R4 | **Never assume BFS, DFS, IDDFS or Greedy return the minimum weighted cost.** Only A\* (admissible heuristic), IDA\* (admissible heuristic) and uniform-cost search guarantee it. |
| R5 | **The cost matrix must be built with A\* using a zero heuristic** (equivalent to uniform-cost search). Never BFS or Greedy. Unreachable pairs are `math.inf` in Python and `null` in JSON, **never 0**. |
| R6 | **Recompute the cost matrix whenever a road is blocked, reopened or re-weighted.** |
| R7 | **No route may use a blocked road.** Every adjacent pair in a route must be an open edge. Reported cost = sum of edge weights. |
| R8 | **Unreachable means `status: "no_route"`, `route: null`, `total_cost: null`.** Never a fake zero-cost path. |
| R9 | **Stochastic algorithms accept a `seed`** and benchmarks repeat across multiple seeds. One good run is not evidence. |
| R10 | **Scope limits:** local only. No auth, cloud deployment, live traffic, real maps (no Leaflet), user accounts or databases. |
| R11 | **Never fail silently.** Frontend shows loading, validation errors, no-route messages and success states. |
| R12 | Make small commits; change shared interfaces (Section 3) only deliberately and update this document when you do. |

---

## 2. Tech stack and project structure

| Layer | Technology | Purpose |
|---|---|---|
| Backend | Python 3.10+ and Flask | Serve page, expose JSON API |
| Algorithms and data | NetworkX, Pandas | Graph model, benchmarking, CSV |
| Frontend | HTML, CSS, vanilla JavaScript | Controls and dashboard |
| Graph view | Cytoscape.js | Interactive city graph and route highlight |
| Charts | Chart.js | Runtime, nodes explored, cost comparisons |
| Tests | pytest | Unit and API tests |

```
rescue_route_planner/
├── app/
│   ├── __init__.py            # create_app() factory, registers blueprint
│   ├── routes.py              # page + API endpoints (thin)
│   ├── services.py            # orchestration: validation-aware calls into algorithms
│   ├── validation.py          # request payload validation helpers
│   ├── templates/
│   │   └── index.html         # single dashboard page
│   └── static/
│       ├── css/style.css
│       ├── js/
│       │   ├── app.js         # UI events, API calls, state
│       │   ├── graph.js       # Cytoscape rendering + highlight
│       │   └── charts.js      # Chart.js rendering
│       └── vendor/            # optional: pinned cytoscape.min.js, chart.umd.min.js
├── models/
│   └── city.py                # CityGraph class + sample city
├── search/
│   ├── common.py              # SearchResult builder, helpers, timing
│   ├── bfs.py
│   ├── dfs.py
│   ├── iddfs.py
│   ├── heuristics.py
│   ├── best_first.py          # Greedy Best-First
│   ├── astar.py
│   └── ida_star.py
├── optimization/
│   ├── cost_matrix.py
│   ├── common.py              # tour validation, tour cost, neighbours
│   ├── hill_climbing.py
│   ├── simulated_annealing.py
│   ├── random_walk.py
│   └── random_restart.py
├── experiments/
│   ├── benchmark.py
│   └── results/               # generated CSVs (gitignored except .gitkeep)
├── tests/
├── main.py                    # starts Flask
├── requirements.txt
├── README.md
└── .gitignore
```

> Folder name `search/` can shadow nothing in the stdlib, but if you hit import clashes rename packages to `rr_search/` and `rr_optimization/`. Do this consistently, in one commit.

---

## 3. Shared contracts (agree before any coding)

### 3.1 Graph representation

* Implemented as `networkx.Graph` (undirected) wrapped by `CityGraph`.
* **Node IDs** are short strings (`"A"`, `"B"`, ...). Node attributes: `label` (str), `x`, `y` (floats, used **only** for layout and the Euclidean heuristic).
* **Edge attributes:** `weight` (positive int or float; travel cost), `blocked` (bool, default `False`).
* **Open view:** algorithms must only traverse edges where `blocked is False`. `CityGraph.neighbors(node)` returns `(neighbor, weight)` pairs for **open** edges only, so no algorithm can accidentally cross a blocked road.
* `CityGraph.version` is an integer incremented on every mutation (block, reopen, reweight, reset). It is used to invalidate cached cost matrices.

### 3.2 Search result (JSON-compatible)

```json
{
  "algorithm": "astar",
  "route": ["A", "C", "E", "H"],
  "total_cost": 13,
  "nodes_explored": 7,
  "nodes_generated": 12,
  "execution_time_ms": 0.42,
  "status": "success",
  "message": ""
}
```

* `status` ∈ `success | no_route | invalid_input`.
* When `status != "success"`: `route = null`, `total_cost = null`.
* **Counters:** `nodes_generated` = every time a node is pushed/added to the frontier. `nodes_explored` = every time a node is popped/expanded. Use these definitions consistently in all six algorithms.
* **Timing:** `time.perf_counter()` around the algorithm call, converted to milliseconds.

### 3.3 Optimisation result

```json
{
  "algorithm": "simulated_annealing",
  "initial_order": ["A", "C", "H", "D", "A"],
  "best_order": ["A", "D", "C", "H", "A"],
  "initial_cost": 31,
  "total_cost": 27,
  "iterations": 1000,
  "seed": 42,
  "execution_time_ms": 3.1,
  "status": "success",
  "message": ""
}
```

* `best_order` starts and ends at the rescue base and visits each selected location exactly once.
* `status` ∈ `success | no_valid_tour | invalid_input`. `no_valid_tour` when any required pair is unreachable (matrix contains `inf` on every possible tour).

### 3.4 Error envelope (all endpoints)

HTTP 400 for malformed input, 404 for unknown road/node where appropriate, 500 for unexpected errors:

```json
{ "status": "invalid_input", "message": "Unknown location 'Z'." }
```

Search and optimisation endpoints return **HTTP 200** with `status: "no_route"` / `"no_valid_tour"` (these are valid outcomes, not server errors).

### 3.5 API endpoints

| Method + path | Request body | Response |
|---|---|---|
| `GET /` | none | Dashboard HTML |
| `GET /api/city` | none | `{nodes:[{id,label,x,y}], edges:[{id,source,target,weight,blocked}], version}` |
| `POST /api/roads/block` | `{source, target}` | Updated city JSON (same as `/api/city`) |
| `POST /api/roads/reopen` | `{source, target}` | Updated city JSON |
| `POST /api/roads/reset` | none | City JSON after restoring all roads to open |
| `POST /api/search` | `{algorithm, start, destination, heuristic?}` | Search result |
| `POST /api/optimise` | `{algorithm, base, locations:[...], seed?, params?}` | Optimisation result |
| `POST /api/benchmark` | `{mode:"search"|"optimise", pairs?, base?, locations?, algorithms:[...], repeats?, seeds?}` | `{rows:[...], meta:{...}}` |
| `GET /api/results.csv` | none | Latest benchmark as CSV download (`404` JSON if none yet) |

Edge `id` convention: `"A-B"` with the two endpoints **sorted alphabetically**, so `block("B","A")` and `block("A","B")` refer to the same edge.

Algorithm name keys: search = `bfs, dfs, iddfs, greedy, astar, ida_star`; optimisation = `hill_climbing, simulated_annealing, random_walk, random_restart`.

---

## 4. Sample city (use exactly this to start)

Create `models/city.py::build_sample_city()` with these 11 nodes (x, y on a 0 to 100 grid):

| ID | Label | x | y |
|---|---|---|---|
| A | Rescue Base | 10 | 50 |
| B | Hospital | 30 | 20 |
| C | School | 30 | 50 |
| D | Market | 30 | 80 |
| E | Bridge | 50 | 35 |
| F | Station | 50 | 65 |
| G | Park | 70 | 15 |
| H | Mall | 70 | 50 |
| I | Stadium | 70 | 85 |
| J | Airport | 90 | 30 |
| K | Port | 90 | 70 |

Edges (`source-target: weight`):
`A-B:6, A-C:4, A-D:6, B-C:5, B-E:4, C-D:4, C-E:5, C-F:5, D-F:5, E-F:4, E-G:5, E-H:4, F-H:4, F-I:5, G-H:5, G-J:5, H-J:5, H-K:5, I-K:5, J-K:6`

Design notes:
* The graph has cycles (needed to test cycle prevention) and several competing routes (needed to show BFS/DFS/Greedy being suboptimal versus A\*).
* Removing `E-H` and `F-H` should force a long detour; removing `H-J`, `H-K`, `I-K`, `J-K` together isolates nothing but removing `G-J`, `H-J`, `J-K` isolates `J` (good unreachable test). Use these in tests.

---

## 5. Phase 1: Skeleton and mock dashboard (Milestone 1)

**Goal:** browser opens locally and shows a sample graph and a sample result from **mock JSON**, so frontend work can proceed in parallel with algorithms.

**Files:** `main.py`, `app/__init__.py`, `app/routes.py`, `app/templates/index.html`, `app/static/css/style.css`, `app/static/js/{app.js,graph.js}`, `requirements.txt`, `.gitignore`, `README.md` (stub).

**Steps**

1. Create the virtual environment and `requirements.txt`:
   ```
   flask>=3.0
   networkx>=3.2
   pandas>=2.1
   pytest>=8.0
   ```
2. `app/__init__.py`: `create_app()` factory that creates `Flask(__name__)`, registers the blueprint from `routes.py`, and returns the app.
3. `main.py`: imports `create_app`, runs `app.run(host="127.0.0.1", port=5000, debug=True)`.
4. `routes.py`: `GET /` renders `index.html`; temporarily `GET /api/city` returns a hard-coded mock JSON in the Section 3.5 format (hard-code 4 to 5 nodes).
5. `index.html`: layout with five regions (see Section 12 for the full UI spec): header, **left sidebar** (controls), **centre** (graph panel `<div id="cy">`), **right** (result panel), **bottom** (comparison/charts). Load Cytoscape.js and Chart.js from pinned CDN URLs (note the version in a comment) or from `static/vendor/` for offline use. Pick **one** approach and document it in the README.
6. `graph.js`: `renderGraph(cityJson)` builds Cytoscape elements: node `data:{id,label}` with `position:{x,y}` and a `preset` layout; edge `data:{id,source,target,weight,label:weight}`. Blocked edges get class `blocked` (dashed red, low opacity). Style edge labels from `data(label)`.
7. `app.js`: on `DOMContentLoaded` call `fetch('/api/city')` then `renderGraph`. Wrap in try/catch and show an error banner on failure.

**Exit check**
* `python main.py` starts without errors.
* Opening `http://127.0.0.1:5000` shows the labelled graph with weights.
* Browser console has no errors.

**Agent Prompt (paste):**
> Implement Phase 1 of `docs/IMPLEMENTATION_PLAN.md`. Create the project skeleton, Flask app factory, `main.py`, and a static dashboard that fetches `/api/city` (mock data for now) and renders it with Cytoscape.js. Do not write any algorithms yet. When done, run the server, open the page in the browser, take a screenshot, and report that the graph renders with edge weights and that the console shows no errors.

---

## 6. Phase 2: Shared city model (Milestone 2)

**Goal:** a real `CityGraph` serving `/api/city`, with block/reopen/reset.

**File:** `models/city.py`, `app/services.py`, `app/routes.py`, `tests/test_city.py`.

**Steps**

1. Implement `CityGraph`:
   * `__init__(self)`: holds `nx.Graph`, `version = 0`, and remembers the **original** edge list for `reset()`.
   * `add_location(id, label, x, y)`, `add_road(u, v, weight)` (validate `weight > 0`, nodes exist, no self-loop).
   * `has_node(n)`, `has_road(u, v)`, `is_blocked(u, v)`.
   * `neighbors(n)`: yields `(nbr, weight)` for open edges only.
   * `edge_weight(u, v)`: weight of an open edge, else raises `KeyError`/returns `None` (choose one and document it).
   * `block_road(u, v)`, `reopen_road(u, v)`: raise `ValueError("Road does not exist")` if missing; blocking an already blocked road is idempotent but still returns cleanly. Bump `version` only when state actually changes.
   * `reset()`: all edges open, version bump.
   * `to_dict()`: the exact JSON shape in 3.5 (edge ids sorted: `"A-B"`).
   * `route_cost(route)`: validates every consecutive pair is an **open** edge and returns the sum. Raises `ValueError` otherwise. **Every algorithm's reported cost must be cross-checked against this in tests.**
2. `build_sample_city()` constructs the Section 4 city.
3. `services.py`: holds a module-level singleton `city = build_sample_city()` (single-user local app; no database). Provide `get_city_dict()`, `block_road(u, v)`, `reopen_road(u, v)`, `reset_city()`.
4. `routes.py`: implement `GET /api/city`, `POST /api/roads/block`, `POST /api/roads/reopen`, `POST /api/roads/reset`. Use `validation.py` helpers to check JSON presence and string fields. Return the error envelope on failure.
5. Frontend: add "Block road" / "Reopen road" dropdown pair (source/target) populated from the city JSON, plus a "Reset scenario" button. Optionally allow clicking an edge in Cytoscape to preselect it. After each call, re-render the graph from the returned JSON.

**Tests (`tests/test_city.py`)**
* Sample city has 11 nodes and 20 edges.
* Blocking `E-H` marks it blocked in `to_dict()` and removes it from `neighbors("E")`.
* `block("H","E")` equals `block("E","H")`.
* Blocking a nonexistent road raises; API returns 400 or 404 with the envelope.
* `route_cost(["A","C","E"]) == 9`; raises when a blocked edge is in the route.
* `version` increments on change, not on a no-op.

**Exit check:** `pytest tests/test_city.py` passes; in the browser, blocking a road turns it dashed/red and reopening restores it.

**Agent Prompt:**
> Implement Phase 2 of the plan: `CityGraph`, the sample city from Section 4, `services.py`, and the block/reopen/reset/city endpoints with validation. Add the road-control UI. Write the listed tests and run them. Then verify in the browser that blocking and reopening `E-H` visibly changes the graph.

---

## 7. Phase 3: First end-to-end route (Milestone 3: BFS and A\*)

**Goal:** a user picks start, destination, algorithm, presses Run, and sees a highlighted route and metrics.

**Files:** `search/common.py`, `search/bfs.py`, `search/heuristics.py`, `search/astar.py`, `services.py`, `routes.py`, `validation.py`, `tests/test_search_basic.py`, frontend files.

**Steps**

1. `search/common.py`
   * `make_result(algorithm, route, cost, explored, generated, elapsed_ms, status, message="")` returns the Section 3.2 dict.
   * `timed(fn)` decorator or helper that measures with `perf_counter`.
   * `validate_endpoints(city, start, destination)` returns an `invalid_input` result when a node is unknown (do not raise inside algorithms; return results).
   * Trivial case: `start == destination` returns `success`, `route=[start]`, `total_cost=0` (this is the only legitimate zero-cost route).
2. `search/bfs.py`: `bfs(city, start, goal) -> dict`.
   * Queue (`collections.deque`), `visited` set added **when generated** (prevents duplicates), `parent` dict for path reconstruction.
   * Use `city.neighbors(n)`; compute `total_cost = city.route_cost(route)` at the end.
   * Finds the fewest-edge route, **not** the cheapest. Document in the docstring.
3. `search/heuristics.py`
   * `zero(city, n, goal) -> 0`.
   * `euclidean(city, n, goal)`: `scale * dist((x,y)_n, (x,y)_goal)` where `scale = min(weight / euclid_dist(u,v))` over **all** edges of the original graph (compute once per city, cache on the `CityGraph` or in a helper). This makes the heuristic admissible and consistent regardless of coordinates.
   * `HEURISTICS = {"zero": zero, "euclidean": euclidean}`.
   * Heuristic choice is a request parameter (`heuristic`, default `"euclidean"`).
4. `search/astar.py`: `astar(city, start, goal, heuristic=euclidean)`.
   * Priority queue `heapq` of `(f, tie_counter, node)`; `g_score` dict; `parent` dict.
   * **Update rule:** when a cheaper path to a neighbour is found (`tentative_g < g_score.get(nbr, inf)`), update `g_score`, `parent`, and push again. Keep a closed/`best_g` check when popping (skip stale entries: `if g > g_score[node]: continue`).
   * Count `nodes_generated` on every push and `nodes_explored` on every non-stale pop/expansion.
   * Return `no_route` when the queue empties.
   * Also expose `uniform_cost(city, start, goal)` = `astar(..., heuristic=zero)` (used for the cost matrix).
5. `services.run_search(payload)`:
   * Validate required fields, algorithm name ∈ registry, nodes exist.
   * Look up the function in `SEARCH_ALGORITHMS = {"bfs": bfs, "astar": astar, ...}` and call with the shared `city`.
   * Return the result dict.
6. `routes.py`: `POST /api/search` → `services.run_search`.
7. Frontend
   * Controls: **Start** and **Destination** dropdowns (labels shown, IDs as values), **Algorithm** dropdown, **Heuristic** dropdown (only enabled for informed algorithms), **Run** button.
   * `runSearch()` disables the button, shows a spinner, `fetch('/api/search', {method:'POST', headers:{'Content-Type':'application/json'}, body})`, handles HTTP errors and `status` values.
   * `highlightRoute(route)` in `graph.js`: remove old highlight classes, add `route-node` to route nodes and `route-edge` to edges between consecutive nodes (look up edge ids with the sorted-pair convention). Strong colour and thicker width.
   * **Route result panel:** route sequence (`A → C → E → H`), total cost, algorithm name, status badge, execution time (ms), nodes explored, nodes generated. For `no_route`, show a clear message and clear any highlight.

**Tests (`tests/test_search_basic.py`)**
* BFS A→K returns a valid route; A\* A→K has cost ≤ BFS cost (and equals the uniform-cost optimum).
* Route cost equals `city.route_cost(route)`.
* With `E-H`, `F-H` blocked, no returned route contains them.
* Isolate `J` (block `G-J`, `H-J`, `J-K`): any search A→J returns `no_route`, `route is None`, `total_cost is None`.
* `start == destination` returns cost 0 and `[start]`.
* Unknown node returns `invalid_input`.
* API test with Flask test client for `POST /api/search` success and invalid algorithm (400).

**Exit check:** In the browser: choose A → K, run A\*, route highlights, metric cards fill. This is the "smallest vertical slice" from the guide.

**Agent Prompt:**
> Implement Phase 3: BFS, heuristics (zero and a scaled, admissible Euclidean), A\*, the search service and `POST /api/search`, and the frontend controls, route highlight and result panel. Follow the counter definitions in Section 3.2 and rule R7/R8. Write and run the listed tests, then use the browser to run A\* from A to K and screenshot the highlighted route.

---

## 8. Phase 4: Complete search suite (Milestone 4)

**Goal:** all six algorithms runnable from the UI with consistent behaviour.

**Files:** `search/dfs.py`, `search/iddfs.py`, `search/best_first.py`, `search/ida_star.py`, registry update, tests.

**Steps and algorithm details**

1. **DFS (`dfs.py`)**: iterative with an explicit stack of `(node, path)` or parent map. Cycle prevention via a `visited` set. Neighbour order must be **deterministic** (sort neighbour IDs) so results are reproducible. Not cost-optimal; document it. Count generated on push, explored on pop.
2. **IDDFS (`iddfs.py`)**: for `limit` in `0..N-1` (N = number of nodes), run depth-limited DFS (recursive or iterative) that prevents cycles **along the current path only** (not globally; otherwise completeness is lost at a given depth). Return the first route found (fewest edges, like BFS). Accumulate counters **across all iterations**. Return `no_route` if the limit reaches `N-1` without success.
3. **Greedy Best-First (`best_first.py`)**: priority queue ordered by `h(n)` only, `visited` set, parent map. Not optimal; document it. Takes the same `heuristic` parameter.
4. **IDA\* (`ida_star.py`)**: iterative deepening on `f = g + h`.
   * `threshold = h(start)`.
   * Recursive `search(node, g, threshold, path)`: compute `f = g + h`; if `f > threshold` return `f`; if goal return FOUND; else track the **minimum** `f` that exceeded the threshold across all children (next threshold); skip nodes already on the current path (cycle prevention).
   * Repeat with `threshold = next_threshold` until found or `next_threshold == inf` (→ `no_route`).
   * Accumulate counters across iterations. Include a safety cap on iterations to avoid infinite loops with float weights.
5. Register in `SEARCH_ALGORITHMS`: `bfs, dfs, iddfs, greedy, astar, ida_star`.
6. Frontend: algorithm dropdown lists all six with human labels; show a small note beside the dropdown stating whether the algorithm guarantees minimum cost (e.g. "Optimal", "Not guaranteed", "Fewest edges").
7. **Algorithm comparison table** (bottom panel): "Compare selected algorithms" button runs `POST /api/search` once per checked algorithm on the **same** start/destination/graph version (sequentially, via `Promise.all` is fine) and fills a table: algorithm, status, route, cost, time, explored, generated, valid (✓/✗). Highlight the lowest cost row. Clicking a row highlights that route on the graph.

**Tests (`tests/test_search_all.py`)**
* Parametrised over all six algorithms and several (start, goal) pairs, including after blocking roads: route valid (`city.route_cost` doesn't raise), cost matches reported cost, no blocked roads.
* A\* and IDA\* costs equal the uniform-cost cost for every pair (optimality check, admissible heuristic).
* BFS/IDDFS route length (edges) is minimal and equal to each other.
* Isolated node returns `no_route` for all six.
* Show (as a test or script) at least one scenario where BFS/DFS/Greedy cost > A\* cost to prove R4 (assert `>=`, and print a note when `>`).

**Exit check:** all six algorithms run from the UI; comparison table fills with consistent validity checks.

**Agent Prompt:**
> Implement Phase 4: DFS, IDDFS, Greedy Best-First and IDA\* exactly as specified in Section 8 (counter definitions, cycle prevention, accumulated counters for iterative methods). Register all six, add the guarantee notes and the comparison table to the UI, and write `tests/test_search_all.py`. Run the full test suite and verify the comparison table in the browser on A→K, with and without a blocked road.

---

## 9. Phase 5: Cost matrix and optimisation (Milestone 5)

**Goal:** choose a rescue base and affected locations; get a valid base-to-base visiting order from four algorithms.

**Files:** `optimization/cost_matrix.py`, `optimization/common.py`, the four algorithm files, `services.py`, `routes.py`, tests, frontend panel.

### 9.1 Cost matrix (`cost_matrix.py`)

* `build_cost_matrix(city, nodes) -> dict[(u, v)] = cost`, computed with `uniform_cost` (A\* with the zero heuristic) for each unordered pair in `nodes` (the base plus the selected locations). Store symmetric entries. Diagonal = 0 (the only allowed zero). Unreachable pair = `math.inf`.
* `CostMatrixCache`: keyed by `(city.version, frozenset(nodes))`. Return the cached matrix only if the version is unchanged; otherwise rebuild. This satisfies R6.
* Expose `matrix_to_json(matrix)` converting `inf → null`.

### 9.2 Shared helpers (`optimization/common.py`)

* `tour_cost(order, matrix)`: sum of consecutive pair costs; returns `inf` if any pair is `inf`.
* `is_valid_tour(order, base, locations)`: starts and ends at base, each location exactly once, no other nodes.
* `random_initial_order(base, locations, rng)`: `[base] + shuffled(locations) + [base]`.
* `neighbours(order)`: generate neighbouring orders by **swapping two interior positions** (optionally add 2-opt reversal of an interior segment). Never move the base endpoints.
* `make_opt_result(...)` builds the Section 3.3 dict; `status = "no_valid_tour"` if `best_cost` is `inf`.
* Use `random.Random(seed)` instances, **never** global `random`, for reproducibility.
* Edge case: 0 or 1 selected location → trivial tour; 2+ for meaningful optimisation. Validate `locations` has no duplicates, does not include the base, and all are known nodes.

### 9.3 Algorithms

All share the signature `fn(matrix, base, locations, seed=None, **params) -> dict`.

1. **Hill Climbing** (`hill_climbing.py`): start from a random order; at each iteration evaluate all neighbours; move to the best strictly-better neighbour (steepest ascent) or first-improvement (pick one and document it); stop at a local optimum or `max_iterations` (default 1000). `iterations` counts moves/evaluation rounds (define and keep consistent).
2. **Simulated Annealing** (`simulated_annealing.py`): params `initial_temp` (default 100), `cooling_rate` (0.995), `min_temp` (0.01), `max_iterations` (5000). Each iteration pick a **random** neighbour; if `delta < 0` accept; else accept with probability `exp(-delta / T)`. Guard for `inf` (never accept an invalid tour; reject when `new_cost` is `inf`). Track and return the **best-ever** order, not the final one.
3. **Random Walk** (`random_walk.py`): `max_iterations` (default 1000) random valid orders; track best. This is the baseline.
4. **Random-Restart Hill Climbing** (`random_restart.py`): `restarts` (default 10); each restart uses a different random initial order from the same RNG stream; keep the best; `iterations` = total across restarts.

If the initial order has infinite cost (unreachable pair), algorithms should still try to find a finite tour; if none found, return `no_valid_tour` with `best_order = null`.

### 9.4 Service and endpoint

* `services.run_optimise(payload)`: validate `algorithm`, `base`, `locations` (1 to 8 recommended cap for UI sanity), `seed` (int or null, default 42), `params` (whitelisted keys only). Get or build the matrix (cached by version), run the algorithm, return the result plus `matrix` (`inf→null`) so the UI can show it. Reject `base` in `locations`.
* `POST /api/optimise` → `services.run_optimise`.

### 9.5 Frontend

* **Optimisation panel**: Base dropdown, multi-select checkboxes for affected locations (disable the base), algorithm dropdown, seed input (default 42), Run button.
* Results: **initial order** and **best order** shown separately (`A → C → H → D → A`), initial cost, final cost, improvement %, iterations, time, status. Show `no_valid_tour` with a clear message.
* Graph: highlight the best tour as the **concatenated shortest paths** between consecutive stops. Get these by calling `POST /api/search` with `astar` for each leg (or have the optimise endpoint return `legs` with routes). Use a distinct colour from the search route and number the stops (node badges 1, 2, 3...).
* Show the pairwise cost matrix in a small collapsible table (`—` for unreachable).

**Tests (`tests/test_optimisation.py`)**
* Matrix symmetric; diagonal 0; matches A\*/uniform cost for sample pairs; isolated node's entries are `inf` (and `null` in JSON), never 0.
* Matrix rebuilds after a road is blocked (assert `version` change causes a different matrix where expected).
* Every returned tour satisfies `is_valid_tour`; cost equals `tour_cost` on the matrix.
* Same seed gives identical output; different seeds can differ.
* Unreachable selected location returns `no_valid_tour`.
* On a small instance (≤ 6 locations) brute-force the optimum and assert SA and random-restart HC reach within a tolerance in most seeds (statistical test over ≥ 20 seeds, not a single run).

**Exit check:** In the browser, pick base A and locations C, H, D; run each algorithm; a valid base-to-base order appears and is drawn on the graph.

**Agent Prompt:**
> Implement Phase 5: the cost matrix with version-based cache invalidation (A\* with zero heuristic, `inf` for unreachable), the shared tour helpers, the four route-improvement algorithms with seeded RNGs, `POST /api/optimise`, and the optimisation panel with tour drawing. Follow Section 9 exactly and write the listed tests, including the multi-seed brute-force comparison. Verify in the browser using base A and locations C, H, D, and again after blocking a road.

---

## 10. Phase 6: Benchmarks, charts, CSV (Milestone 6)

**Goal:** controlled comparisons with charts and CSV export.

**Files:** `experiments/benchmark.py`, `services.py`, `routes.py`, `app/static/js/charts.js`, tests.

**Steps**

1. `benchmark_search(city, pairs, algorithms, heuristic="euclidean", repeats=5) -> pandas.DataFrame`
   * Freeze `graph_version = city.version` at the start; assert it is unchanged at the end (identical conditions).
   * For each `(start, goal)` pair and each algorithm, run `repeats` times; record `execution_time_ms` per run. Row columns: `pair, start, destination, algorithm, repeat, status, total_cost, nodes_explored, nodes_generated, execution_time_ms, route_valid, graph_version, heuristic`.
   * Default pairs: if none supplied, choose up to 5 fixed pairs deterministically (e.g. `A→K, A→J, B→I, D→G, C→K`), skipping unreachable ones only if the user asks; otherwise include them (they show `no_route`).
   * Provide an aggregated view (mean/min/max time, mean cost, mean nodes) via `df.groupby`.
2. `benchmark_optimisation(city, base, locations, algorithms, seeds=range(20), params=None)`
   * Same matrix for all algorithms (build once). Each algorithm runs once **per seed**. Columns: `algorithm, seed, initial_cost, best_cost, iterations, execution_time_ms, status, graph_version`.
   * Aggregate: mean, std, min, max best cost per algorithm, plus success rate. This is where "one good run is not evidence" is respected; the UI must show the number of seeds.
3. `services.run_benchmark(payload)`: validates `mode`, algorithms, repeats (1 to 20), seeds (1 to 50); stores the latest DataFrame in a module variable `LATEST_RESULTS` (with metadata: mode, timestamp, repeats/seeds, graph_version); returns `{rows, summary, meta}` JSON (`NaN/inf → null`).
4. `GET /api/results.csv`: `df.to_csv(index=False)` with headers `Content-Type: text/csv` and `Content-Disposition: attachment; filename=benchmark_results.csv`. If none exists, return 404 with the envelope. Also write a copy to `experiments/results/`. Include meta comment columns or a sibling row-set so seeds/repeats are disclosed (simplest: add `repeats` / `seeds` columns).
5. `charts.js`
   * Search: grouped bar charts (x = algorithm) for **mean runtime (ms)**, **mean nodes explored**, **mean route cost**. Axis titles with units. Use "no route" annotation (omit bars) rather than zero bars.
   * Optimisation: bar (mean ± std as a second dataset or error annotation) and/or a box-like min/mean/max for best cost per algorithm; show seeds count in the chart title.
   * Always destroy the previous chart instance before creating a new one (`chart.destroy()`).
6. UI: "Benchmark" tab/section with mode toggle, algorithm checkboxes, repeats/seeds inputs, Run Benchmark, loading state, charts, summary table and a **Download CSV** button (plain link to `/api/results.csv`, disabled until a benchmark has run).

**Tests**
* Benchmark rows count = pairs × algorithms × repeats.
* All algorithms in a benchmark share the same `graph_version`.
* `/api/results.csv` returns 404 before any run, valid CSV after, parseable by `pandas.read_csv`.
* Determinism: rerunning optimisation benchmark with the same seeds gives identical costs (times differ).

**Exit check:** run a benchmark from the UI, see three charts update, download a CSV that opens correctly.

**Agent Prompt:**
> Implement Phase 6: `experiments/benchmark.py` for search and optimisation, `POST /api/benchmark`, `GET /api/results.csv`, `charts.js`, and the Benchmark UI section. Enforce identical graph version and disclose repeats/seeds in outputs. Add the listed tests, run everything, then verify in the browser by running a search benchmark and an optimisation benchmark and downloading the CSV.

---

## 11. Phase 7: Hardening, tests, README, demo (Milestone 7)

**Steps**

1. **Input validation sweep:** missing JSON body, wrong types, empty strings, unknown nodes, unknown algorithm names, duplicate locations, base inside locations, huge `repeats`, non-integer `seed`. Each must return the error envelope with an HTTP 4xx and a human-readable message; none may produce a stack trace.
2. **Global error handlers:** `@app.errorhandler(Exception)` returns `{"status":"error","message":"Unexpected server error"}` (log the traceback to the terminal for developers).
3. **Frontend resilience:** every `fetch` wrapped in try/catch; non-2xx responses display `message`; network failure shows "Cannot reach the server"; buttons re-enable in `finally`.
4. **Stale-data checks:** after any block/reopen/reset, clear route highlights, results panels and comparison tables (they refer to an old graph version) or mark them "stale". Disable the CSV download until a new benchmark is run, or label it with its graph version.
5. **Quality checklist as automated tests** (`tests/test_invariants.py`), run across *all* algorithms and many random scenarios (random blocked-road subsets with a fixed seed):
   * No route uses a blocked road.
   * Adjacent route nodes are open edges.
   * Reported cost equals the sum of edge weights.
   * Unreachable ⇒ `no_route`, never cost 0 (except start == goal).
   * Tours start/end at base, visit each location exactly once.
   * Impossible transitions (`inf`) never produce a "valid" tour.
   * Cost matrix is regenerated when the version changes.
   * Benchmark rows share one graph version.
6. **Manual MVP walkthrough** (Section 13) performed and recorded with screenshots in `docs/demo/`.
7. **README.md** must contain: project summary; prerequisites (Python version); setup (venv creation for Windows PowerShell and macOS/Linux); `pip install -r requirements.txt`; how to run (`python main.py`); URL; how to run tests (`pytest`); how to use the dashboard (short); project structure; algorithm guarantees table; offline-demo note (vendor files) or CDN note; known limitations.
8. **Clean-clone test:** in a fresh directory, clone, create a new venv, install, run, open the site, run the MVP walkthrough.

**Agent Prompt:**
> Implement Phase 7: complete the validation sweep, global error handlers, frontend resilience and stale-state handling, write `tests/test_invariants.py` covering the checklist in Section 11, write the README, then perform a clean-environment install and run the full MVP walkthrough in the browser, saving screenshots to `docs/demo/`. Report any failure honestly with the exact command output.

---

## 12. Frontend specification (reference for all UI phases)

**Layout (laptop first; mobile optional):**

```
┌──────────────────────── Header: title + status banner ─────────────────────────┐
│ Sidebar (controls)      │ Graph panel (Cytoscape)       │ Result panel         │
│  Search controls        │  legend: open / blocked /     │  Route sequence      │
│  Road controls          │  route / tour                 │  Metric cards        │
│  Optimisation controls  │                               │  Optimisation result │
├─────────────────────────┴───────────────────────────────┴──────────────────────┤
│ Algorithm comparison table │ Benchmark controls │ Charts │ Download CSV        │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Graph style:**
* Nodes: circle with label; base node visually distinct (e.g. different fill) when selected as base.
* Open roads: solid grey, labelled with weight. Blocked roads: dashed red, reduced opacity, label retained. Route: thick accent colour. Tour: a second accent colour with stop numbers.
* Fixed `preset` layout from `x, y` so the picture is stable across updates.

**State handling (`app.js`):** one `state` object: `{city, lastSearch, lastOptimise, lastBenchmark}`. All render functions read from it. After any city mutation, replace `state.city`, re-render, clear stale outputs.

**Accessibility/clarity:** colour is never the only signal (blocked roads are also dashed); buttons have text labels; error and success messages appear in a visible banner region with `role="status"`.

**Do not** add Leaflet, map tiles, frameworks, or a build step in v1.

---

## 13. Minimum viable demo (acceptance script)

Execute in the browser, in order:

1. Start Flask (`python main.py`) and open `http://127.0.0.1:5000`.
2. The sample city appears with road weights.
3. Choose start A, destination K, algorithm A\*; click Run; the path highlights and metrics fill.
4. Block one road on the displayed route; rerun the same query; the route changes, or a clear no-route message appears.
5. Run at least two search algorithms (e.g. BFS and A\*) on the same scenario and compare metrics in the table.
6. Choose base A and affected locations (e.g. C, H, D); run one optimisation algorithm; the visiting order (and drawn tour) appears.
7. Run a benchmark and download the CSV.

All seven steps must work without reading any terminal output.

---

## 14. Definition of done

* Fresh clone → install documented dependencies → `python main.py` → dashboard at `http://127.0.0.1:5000`.
* Scenarios can be configured (block/reopen/reset roads, select locations).
* All six search algorithms and four optimisation algorithms run from the UI.
* Routes and metrics are inspected visually; algorithms compared; results exported as CSV.
* `pytest` passes, including the invariant tests.
* No algorithm result needs to be read from the command line.

---

## 15. Appendix: team mapping (optional, for parallel work)

| Member | Owns | Phases |
|---|---|---|
| Person 1 | `models/city.py`, `search/{bfs,dfs,iddfs}.py`, city tests | 2, 3 (BFS), 4 (DFS, IDDFS) |
| Person 2 | `search/{heuristics,best_first,astar,ida_star}.py`, heuristic experiments | 3 (A\*), 4 (Greedy, IDA\*) |
| Person 3 | `optimization/*` | 5 |
| Person 4 | Flask app, services, frontend, benchmark integration, CSV, README | 1, 2 (API/UI), 3 to 7 (integration) |

When using Antigravity with several agents in parallel, give each agent **only its own files**, and have them all code against Section 3 contracts. Person 4's agent can build against mock JSON (Phase 1) while the others implement algorithms.

## 16. Appendix: common pitfalls checklist

* Pushing to the frontier without updating `g_score` on a cheaper path (breaks A\* optimality).
* Marking nodes visited at *pop* time in BFS (works but inflates `nodes_generated`); stay consistent with Section 3.2.
* Global visited set in IDDFS (breaks completeness); use path-based cycle prevention.
* Float comparison in IDA\* thresholds (use a small epsilon or integer weights).
* Using Python's global `random` (breaks reproducibility); use `random.Random(seed)`.
* Serialising `math.inf` or `NaN` to JSON (invalid JSON); convert to `null`.
* Edge id mismatches (`"B-A"` vs `"A-B"`); always sort endpoints.
* Forgetting to destroy Chart.js instances before redrawing.
* Leaving route highlights on screen after the graph changed.
