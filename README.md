# RESQ --- AI-Powered Disaster Rescue Route Planner


**Intelligent Route Finding. Optimised Rescue Operations. Smarter
Decisions.**

A Python-based Artificial Intelligence project that explores search and
optimisation algorithms to identify efficient rescue routes in simulated
disaster scenarios.




------------------------------------------------------------------------

## Overview

In disaster situations, road accessibility can change rapidly. Roads may
become blocked, travel costs may increase, and rescue teams may need to
visit multiple affected locations before returning to their rescue base.

**RESQ** is an AI-based Disaster Rescue Route Planner designed to
simulate these challenges using graph-based modelling, heuristic search,
and optimisation algorithms.

The system represents a city as a weighted graph, where locations are
vertices, roads are edges, and travel costs represent the cost of moving
between locations. Roads can be blocked or reopened to simulate changing
disaster conditions.

RESQ addresses two fundamental problems:

1.  **Intelligent Route Finding:** Finding routes between a rescue base
    and a destination while avoiding blocked roads.
2.  **Rescue Route Optimisation:** Finding a low-cost visiting order for
    multiple affected locations while returning to the rescue base.

The project implements and compares ten AI algorithms to understand
their effectiveness, computational efficiency, and solution quality.

## Problem Statement

During disaster response operations, identifying accessible and
cost-efficient routes is an important computational challenge.

Traditional route selection can become inefficient when road conditions
change or when rescue teams must visit multiple affected locations.

The challenge is to develop a system that can:

-   Represent a city as a dynamic weighted graph.
-   Identify routes while avoiding blocked roads.
-   Apply uninformed and informed search strategies.
-   Estimate remaining travel costs using heuristic functions.
-   Optimise the order in which multiple affected locations are visited.
-   Evaluate algorithms using execution time, exploration metrics, and
    solution costs.

RESQ approaches these challenges through classical Artificial
Intelligence search and optimisation techniques.

## Objectives

-   Develop a graph-based representation of a simulated city.
-   Implement uninformed and informed search algorithms.
-   Design and evaluate suitable heuristic functions.
-   Find minimum-cost routes between selected locations.
-   Optimise rescue visiting orders using local search techniques.
-   Compare the performance of different AI algorithms.
-   Visualise routes, blocked roads, and optimisation results.
-   Generate experimental results and export them for analysis.

## Core Features

  -----------------------------------------------------------------------
  Feature                             Description
  ----------------------------------- -----------------------------------
  City Modelling                      Represent locations and weighted
                                      roads using NetworkX

  Road Management                     Block and reopen roads to simulate
                                      disaster conditions

  Route Finding                       Execute six search algorithms

  Heuristic Evaluation                Compare zero and distance-based
                                      heuristics

  Route Optimisation                  Optimise visiting orders for
                                      multiple affected locations

  Visualisation                       Display city networks and computed
                                      routes

  Performance Analysis                Compare execution time, nodes
                                      explored, and route costs

  Data Export                         Export experimental results using
                                      Pandas
  -----------------------------------------------------------------------

## AI Algorithms Implemented

### 1. Route Finding Algorithms

RESQ uses six search algorithms to find routes between a starting
location and a destination.

  -----------------------------------------------------------------------
  Algorithm               Category                Search Strategy
  ----------------------- ----------------------- -----------------------
  Breadth-First Search    Uninformed              Explores nodes level by
  (BFS)                                           level

  Depth-First Search      Uninformed              Explores one path
  (DFS)                                           deeply before
                                                  backtracking

  Iterative Deepening DFS Uninformed              Repeated depth-limited
  (IDDFS)                                         exploration

  Greedy Best-First       Informed                Prioritises estimated
  Search                                          remaining cost

  A\* Search              Informed                Combines actual and
                                                  estimated costs

  Iterative Deepening A\* Informed                Uses depth-first
  (IDA\*)                                         exploration with
                                                  increasing cost
                                                  thresholds
  -----------------------------------------------------------------------

**Heuristic Search**

The informed search algorithms use heuristic functions to estimate the
remaining cost to the destination.

A\* uses:

\[ f(n)=g(n)+h(n) \]

Where:

-   (g(n)): Actual cost from the starting location.
-   (h(n)): Estimated cost from the current location to the destination.
-   (f(n)): Estimated total path cost.

The project evaluates zero and suitable distance-based heuristics to
understand their impact on search performance.

### 2. Route Optimisation Algorithms

Finding individual routes is not sufficient when rescue teams need to
visit multiple affected locations.

RESQ models this as a route optimisation problem.

Given:

-   A rescue base.
-   A collection of affected locations.
-   A pairwise minimum-travel-cost matrix.

The objective is to find an efficient visiting order that starts and
ends at the rescue base while visiting every selected location exactly
once.

The following optimisation algorithms are used:

  -----------------------------------------------------------------------
  Algorithm                           Strategy
  ----------------------------------- -----------------------------------
  Hill Climbing                       Iteratively improves the current
                                      visiting order

  Simulated Annealing                 Accepts certain worse solutions to
                                      escape local optima

  Random Walk                         Explores randomly generated
                                      visiting orders

  Random-Restart Hill Climbing        Repeats hill climbing from
                                      different starting solutions
  -----------------------------------------------------------------------

The cost matrix is generated using A\* with a zero heuristic, ensuring
that the optimisation algorithms operate on minimum weighted travel
costs rather than unweighted path lengths.

## System Architecture

RESQ follows a modular architecture that separates city modelling, route
finding, optimisation, visualisation, and experimentation.

``` mermaid
flowchart TD
    A["City Model<br/>Weighted Graph"] --> B["Road Management<br/>Open / Blocked Roads"]
    B --> C["Route Finding"]
    C --> D["BFS, DFS, IDDFS"]
    C --> E["Greedy, A*, IDA*"]
    D --> F["Route Results"]
    E --> F
    F --> G["Pairwise Cost Matrix"]
    G --> H["Route Optimisation"]
    H --> I["Hill Climbing"]
    H --> J["Simulated Annealing"]
    H --> K["Random Walk"]
    H --> L["Random-Restart HC"]
    I --> M["Optimised Visiting Order"]
    J --> M
    K --> M
    L --> M
    M --> N["Visualisation and Benchmarking"]
    N --> O["Charts and CSV Results"]
```

### Architectural Components

**1. City Model**

Maintains the shared weighted graph containing locations, roads, travel
costs, and blocked-road information.

**2. Route Finding Engine**

Executes the six search algorithms and returns route information and
performance metrics.

**3. Cost Matrix Generator**

Computes minimum weighted travel costs between relevant locations and
identifies unreachable pairs.

**4. Route Optimisation Engine**

Applies four optimisation algorithms to determine efficient visiting
orders.

**5. Visualisation and Benchmarking Engine**

Displays the city network, highlights routes, compares algorithm
performance, and exports experimental results.

## Technology Stack

  Technology   Purpose
  ------------ ---------------------------------------------
  Python       Core implementation
  NetworkX     Graph representation and manipulation
  Matplotlib   City and route visualisation
  Pandas       Experimental data processing and CSV export

## Project Structure

``` text
RESQ/
│
├── models/
│   └── city.py
│
├── search/
│   ├── bfs.py
│   ├── dfs.py
│   ├── iddfs.py
│   ├── heuristics.py
│   ├── best_first.py
│   ├── astar.py
│   └── ida_star.py
│
├── optimization/
│   ├── cost_matrix.py
│   ├── hill_climbing.py
│   ├── simulated_annealing.py
│   ├── random_walk.py
│   └── random_restart.py
│
├── visualization/
│   ├── city_view.py
│   └── results_view.py
│
├── experiments/
│   └── benchmark.py
├── results/
│
├── main.py
├── requirements.txt
└── README.md
```

## Installation and Execution

### Prerequisites

-   Python 3.x
-   pip package manager
-   Git

### 1. Clone the repository

``` bash
git clone https://github.com/santhosh-ek2007-zen/RESQ.git
```

### 2. Navigate to the project directory

``` bash
cd RESQ
```

### 3. Create a virtual environment

``` bash
python -m venv venv
```

Activate it:

**Windows**

``` bash
venv\Scripts\activate
```

**Linux / macOS**

``` bash
source venv/bin/activate
```

### 4. Install dependencies

``` bash
pip install -r requirements.txt
```

### 5. Run the application

``` bash
python main.py
```

*Note: The execution instructions assume the project entry point and
requirements file are configured as shown above.*

## Performance Evaluation

RESQ evaluates algorithms under identical experimental conditions to
ensure meaningful comparisons.

### Route Finding Metrics

  Metric            Purpose
  ----------------- ------------------------------------------------
  Execution Time    Measures computational time
  Nodes Explored    Measures the number of expanded locations
  Nodes Generated   Measures the number of generated search states
  Route Cost        Measures the total travel cost
  Route Validity    Verifies that the route follows open roads

### Route Optimisation Metrics

  Metric                 Purpose
  ---------------------- --------------------------------------------
  Final Route Cost       Measures the quality of the visiting order
  Execution Time         Measures computational efficiency
  Iterations             Measures optimisation effort
  Best Solution          Records the best visiting order
  Run-to-Run Variation   Evaluates consistency across repeated runs

Randomised optimisation experiments use multiple random seeds to avoid
drawing conclusions from a single favourable execution.

### Experimental Visualisations

The benchmarking module is designed to generate comparisons such as:

-   Execution time across search algorithms.
-   Nodes explored by each search algorithm.
-   Route costs across different search strategies.
-   Final visiting costs across optimisation algorithms.
-   Optimisation cost progression across iterations.

Experimental results are exported as CSV files for further analysis.

## Testing and Validation

The project includes testing across individual modules and the
integrated system.

Important validation scenarios include:

-   Routes must never use blocked roads.
-   Returned routes must connect the specified starting and destination
    locations.
-   Reported travel costs must match the graph's edge weights.
-   Unreachable destinations must be handled correctly.
-   Heuristic search algorithms must update better-known path costs
    correctly.
-   Every selected affected location must be visited exactly once.
-   Optimised routes must start and finish at the rescue base.
-   Unreachable transitions must never be accepted as valid movements.

## Limitations

-   The city is simulated using a graph rather than a real geographical
    map.
-   The system does not use live traffic or disaster information.
-   Travel costs are represented using predefined edge weights.
-   The optimisation problem assumes every selected affected location
    must be visited exactly once.
-   The project focuses on classical AI search and optimisation rather
    than production-grade emergency dispatch.

## Future Enhancements

Potential extensions include:

-   Integration with real geographical maps.
-   Dynamic road closures and changing travel costs.
-   Real-time traffic information.
-   Priority-based rescue location selection.
-   Multiple rescue vehicles and distributed route planning.
-   Integration with live disaster information.
-   More advanced optimisation techniques and comparative studies.

## Team Contributions

RESQ is developed collaboratively by a four-member team.

  Team Member   Responsibility
  ------------- ---------------------------------------------
  Diwakar DG     City Modelling and Uninformed Search
  Santhosh EK      Heuristics and Informed Search
  Rubesh BB      Route Optimisation and Cost Matrix
  Uvan Rishee and Santhosh EK     Visualisation, Benchmarking and Integration

Each module follows a shared interface to support independent
development, testing, and integration.

## Academic Context

This project explores concepts from Artificial Intelligence,
particularly:

-   Uninformed Search Strategies
-   Informed Search Strategies
-   Heuristic Functions
-   A\* and Iterative Deepening A\*
-   Local Search and Optimisation
-   Graph Theory
-   Algorithm Performance Evaluation

The objective is not only to find a solution, but also to understand how
different AI algorithms behave under identical problem conditions.

------------------------------------------------------------------------

**RESQ**

*Finding better routes when every decision matters.*

Built with Python \| Artificial Intelligence \| Graph Search \|
Optimisation
