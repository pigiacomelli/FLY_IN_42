*This project has been created as part of the 42 curriculum by pgiacome.*

# Fly-in

## Description

Fly-in is an object-oriented drone routing and discrete-turn simulation system.
It parses a map of zones and bidirectional connections, computes several
candidate routes, assigns drones to those routes, and schedules simultaneous
movements while respecting all movement and capacity rules.

The implementation handles:

- zone occupancy limits (`max_drones`);
- connection throughput limits (`max_link_capacity`);
- inaccessible `blocked` zones;
- two-turn movements into `restricted` zones;
- preference for `priority` zones when path costs are tied;
- unlimited occupancy at the start and end hubs;
- simultaneous movement and same-turn capacity release;
- strategic waiting when a safe movement is not available;
- mandatory next-turn arrival after entering a restricted-zone connection.

The objective is to deliver every drone from the start hub to the end hub in as
few simulation turns as possible. Each output line represents one turn and uses
the required `D<ID>-<zone>` or `D<ID>-<connection>` format.

## Architecture

```text
map file
   |
   v
Parser ---> ParsedMap ---> MapValidator
                           |
                           v
                     Graph + drones
                           |
                           v
                 KShortestPathfinder
                           |
                           v
                     RoutePlanner
                           |
                           v
                      Scheduler
                           |
                           v
MovementValidator <--- Simulation ---> SimulationState
                           |
                           v
                   TerminalRenderer
```

### Main responsibilities

| Component | Responsibility |
|---|---|
| `Parser` | Parse map syntax and metadata with line-specific errors. |
| `MapValidator` | Validate semantic invariants such as start-to-end reachability. |
| `Graph` | Store zones using adjacency lists and expose connections and neighbors. |
| `Pathfinder` | Find a minimum-turn path with priority-zone tie-breaking. |
| `KShortestPathfinder` | Generate alternative loopless candidate paths. |
| `RoutePlanner` | Assign drones to routes using projected congestion pressure. |
| `Scheduler` | Build a safe simultaneous movement set for each turn. |
| `MovementValidator` | Validate zone, connection, transit, and capacity constraints. |
| `Simulation` | Atomically apply a validated turn and advance active transits. |
| `SimulationRunner` | Coordinate turns until all drones are delivered. |
| `TerminalRenderer` | Print the required output with optional ANSI zone colors. |

## Algorithm explanation

### Graph representation

The graph uses an adjacency list:

```text
zone name -> list of incident Connection objects
```

For `V` zones and `E` connections, storage is `O(V + E)`. Neighbor traversal is
`O(deg(v))`, which is more appropriate for sparse maps than an adjacency matrix
requiring `O(V^2)` memory.

### Weighted shortest path

`Pathfinder` uses Dijkstra's algorithm because movement costs are non-negative:
entering a normal or priority zone costs one turn, while entering a restricted
zone costs two turns. Priority-zone count is used only as a secondary ordering
criterion when total turn cost is equal.

With a binary heap:

```text
Time:  O((V + E) log V)
Space: O(V + E)
```

### Multiple candidate paths

`KShortestPathfinder` follows Yen's loopless K-shortest-path strategy. It keeps
root prefixes, creates spur-path alternatives, and uses the weighted shortest
pathfinder for each spur computation. Candidate paths are immutable and
identified by their ordered zone sequence.

The number of alternatives is configurable with `--paths`, since generating
more paths trades additional planning time and memory for more routing options.

### Congestion-aware route assignment

For each drone, `RoutePlanner` scores every candidate path using:

1. weighted path duration;
2. maximum projected queue delay on a path resource;
3. total projected congestion pressure;
4. number of priority zones and hop count as deterministic tie-breakers.

Tracked resources include both connections and intermediate zones. This avoids
treating paths with shared bottlenecks as fully independent.

For `D` drones, `K` candidate paths, and average path length `L`, assignment is
approximately:

```text
O(D * K * L)
```

### Turn scheduler

The scheduler is deterministic and greedy, with validation-backed admission:

1. identify drones currently available at zones;
2. prioritize drones that are further downstream / closer to finishing;
3. create the next forward movement on each assigned route;
4. tentatively add that movement to the current turn;
5. reserve capacity needed by mandatory restricted-zone arrivals;
6. accept the movement only when `MovementValidator` validates the complete
   simultaneous movement set.

Downstream-first ordering lets a drone leave a capacity-one zone in the same
turn that another drone enters it. Every accepted batch is checked by the same
validator used by the simulation engine, so scheduler and simulation rules stay
consistent.

### Restricted-zone movement

Entering a restricted zone takes two turns. On the first turn, the drone enters
the connection and the output reports that connection. On the following turn,
the drone must arrive at the restricted destination; it cannot wait longer on
the connection.

The scheduler conservatively reserves capacity for these mandatory arrivals so
that a drone is never launched into a transit that cannot legally complete.

### Atomic simulation turns

`Simulation.apply_turn()` validates the entire movement batch before modifying
any state. If one proposed movement is invalid, no partial turn is applied.

The simulation snapshots drones already in transit before new movements start.
Only those previous transits are advanced during the current turn, preventing a
new two-turn movement from incorrectly finishing immediately.

## Instructions

### Requirements

- Python 3.10 or later;
- `uv` (recommended) or another compatible Python package manager;
- no graph library is used.

### Install

```bash
make install
```

### Run

```bash
make run ARGS="maps/easy/01_linear_path.txt"
```

Equivalent direct command:

```bash
uv run python -m fly_in maps/easy/01_linear_path.txt
```

Useful options:

```text
--paths N       maximum number of candidate paths (default: 16)
--max-turns N   defensive simulation turn limit
--no-color      disable ANSI terminal colors
--stats         print aggregate metrics to stderr
```

Example:

```bash
uv run python -m fly_in \
    maps/hard/03_ultimate_challenge.txt \
    --no-color \
    --stats
```

### Debug

```bash
make debug ARGS="maps/easy/01_linear_path.txt --no-color"
```

### Tests and lint

```bash
make test
make lint
make check
```

`make lint` executes `flake8` and `mypy` with the flags required by the subject.
`make check` runs both linting and the complete automated test suite.

### Benchmarks

```bash
make benchmark
```

Reference-map results with the default 16 candidate paths:

| Map | Result | Reference target |
|---|---:|---:|
| Linear path | 4 | <= 6 |
| Simple fork | 4 | <= 8 |
| Basic capacity | 4 | <= 6 |
| Dead end trap | 8 | <= 12 |
| Circular loop | 15 | <= 15 |
| Priority puzzle | 7 | <= 12 |
| Maze nightmare | 13 | <= 30 |
| Capacity hell | 16 | <= 35 |
| Ultimate challenge | 26 | <= 45 |
| The Impossible Dream | 43 | < 45 reference record |

These results are deterministic for the bundled official maps and current
implementation. Evaluation maps may have different topologies and congestion
patterns.

## Example input and expected output

### Example input

```text
nb_drones: 2
start_hub: start 0 0 [color=green]
hub: waypoint1 1 0 [color=blue]
hub: waypoint2 2 0 [color=blue]
end_hub: goal 3 0 [color=red]

connection: start-waypoint1
connection: waypoint1-waypoint2
connection: waypoint2-goal
```

### Expected output

```text
D1-waypoint1
D1-waypoint2 D2-waypoint1
D1-goal D2-waypoint2
D2-goal
```

Each line represents one simulation turn. Drones that remain stationary during
a turn are omitted from the output.

## Output format

A one-turn movement prints the destination zone:

```text
D1-waypoint1 D2-corridorA
```

The first turn of a movement into a restricted zone prints the connection:

```text
D1-loop_b-exit_point
```

The mandatory arrival on the following turn prints the destination:

```text
D1-exit_point
```

Drones that wait are omitted. Drones that reach the end zone are delivered and
are no longer scheduled.

## Visual representation

The project uses a terminal-based visual representation. `TerminalRenderer`
preserves the required movement-line format while applying ANSI colors when a
destination zone contains `color=<value>` metadata.

This makes movements easier to distinguish during the simulation without
changing the mandatory output structure.

For example, a movement into a zone declared with `color=red` is displayed in
red in a compatible terminal. Unknown single-word color values remain valid and
are mapped to a fallback ANSI color.

Use `--no-color` when plain-text output is preferred, such as during automated
testing or output redirection.

## Error handling

Parser failures include the source line and a clear cause. Application-level
errors are converted into concise terminal messages instead of uncaught Python
tracebacks.

Handled invalid inputs include:

- duplicate zones or connections;
- malformed metadata;
- invalid capacities;
- unknown connection endpoints;
- missing start or end hubs;
- invalid zone types;
- unreachable end zones;
- missing routes;
- simulation deadlocks;
- turn-limit exhaustion.

## Project structure

```text
fly_in/
├── application.py
├── cli.py
├── domain/
├── output/
├── parsing/
├── pathfinding/
├── scheduling/
├── simulation/
├── validator/
└── visualization/
    ├── renderer.py
    └── terminal_renderer.py
maps/
scripts/
tests/
Makefile
README.md
pyproject.toml
```

## Limitations and possible improvements

- Route assignment is heuristic rather than globally optimal.
- The scheduler does not solve a full time-expanded minimum-cost flow problem.
- Candidate quality depends on the number of paths requested with `--paths`.
- A more advanced optimizer could simulate competing complete assignments,
  perform local search, or use a time-expanded residual network.

These choices keep the implementation explainable, deterministic, testable,
and fast while still meeting the supplied performance targets.

## Resources

- Edsger W. Dijkstra, *A Note on Two Problems in Connexion with Graphs*.
- Jin Y. Yen, *Finding the K Shortest Loopless Paths in a Network*.
- Python documentation for `heapq`, `enum`, `argparse`, `pathlib`, and typing.
- PEP 8 and PEP 257 for style and documentation.
- 42 Fly-in subject, version 1.5.

### Use of AI

AI was used as a support tool during the development process for:

- discussing ideas and comparing possible architectural and algorithmic
  approaches;
- proposing test cases and edge cases used to validate the implementation;
- reviewing and improving project documentation.

The final implementation was developed and tested incrementally. All submitted
code, architectural decisions, algorithms, and trade-offs are understood and
can be explained during peer evaluation.
