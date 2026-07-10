# Edge Reuse Diversification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prefer unused mesh edges within a vehicle plan via soft weighted pathfinding so outbound/return (and later trips) can diverge, and fitness reflects that cost.

**Architecture:** Add Dijkstra-style `find_path_weighted` with canonical undirected edges and a reuse multiplier. The VRP decoder keeps `used_edges` across all trips of one vehicle, stores each segment’s node path on `Trip`, and sums weighted costs into distance/fitness. Map/animation draw stored paths only (no re-shortest-path).

**Tech Stack:** Python, unittest, existing Pygame UI (no new deps).

## Global Constraints

- Branch: `feature/road-network-blocked-nodes`
- **Do not create git commits** unless the user explicitly asks
- Spec: `docs/superpowers/specs/2026-07-09-edge-reuse-diversification-design.md`
- Soft penalty only (never ∞ solely because an edge was reused)
- Memory scope: all trips of **one** vehicle plan; vehicles do not share `used_edges`
- Always on (no UI toggle); `edge_reuse_penalty = 1.75`
- Do not change chromosome, assignment, or GA operators

---

## File map

| File | Responsibility |
|------|----------------|
| Modify: `traveling_salesman_problem/problem/road_network.py` | Canonical edge, weighted path cost, `find_path_weighted` |
| Modify: `traveling_salesman_problem/problem/delivery_mesh.py` | Segment path/distance with optional `used_edges` / penalty |
| Modify: `traveling_salesman_problem/problem/vrp_models.py` | `Trip.path_node_ids: list[list[str]]` (one path per consecutive stop pair) |
| Modify: `traveling_salesman_problem/problem/vrp_decoder.py` | Maintain `used_edges`; weighted segments; fill `path_node_ids` |
| Modify: `traveling_salesman_problem/config/application_settings.py` | `edge_reuse_penalty: float = 1.75` |
| Modify: `traveling_salesman_problem/visualization/map_renderer.py` | Draw from `Trip.path_node_ids` |
| Modify: `traveling_salesman_problem/visualization/route_animation.py` | Build polyline from stored paths |
| Modify: `traveling_salesman_problem/simulation/vehicle_genetic.py` | Pass penalty from settings into decode if signature requires it |
| Test: `tests/test_weighted_pathfinding.py` | |
| Test: `tests/test_vrp_decoder_edge_reuse.py` | |
| Update: `tests/test_route_animation.py` | Use trips with `path_node_ids` |

---

### Task 1: Weighted pathfinding primitives

**Files:**
- Modify: `traveling_salesman_problem/problem/road_network.py`
- Test: `tests/test_weighted_pathfinding.py`

**Interfaces:**
- Produces:
```python
EdgeKey = Tuple[str, str]  # always (min_id, max_id) lexicographic

def canonical_edge(node_a: str, node_b: str) -> EdgeKey: ...

def edge_cost(
    network: RoadNetwork,
    node_a: str,
    node_b: str,
    used_edges: Set[EdgeKey],
    reuse_penalty: float,
) -> float:
    # euclidean * (reuse_penalty if canonical_edge in used_edges else 1.0)

def path_weighted_distance(
    network: RoadNetwork,
    path: List[str],
    used_edges: Set[EdgeKey],
    reuse_penalty: float,
) -> float: ...

def find_path_weighted(
    network: RoadNetwork,
    origin: str,
    destination: str,
    blocked: Optional[Set[str]] = None,
    used_edges: Optional[Set[EdgeKey]] = None,
    reuse_penalty: float = 1.0,
) -> List[str]:
    # Dijkstra on adjacency; skip blocked nodes; empty list if unreachable
```

- [ ] **Step 1: Write failing tests**

```python
# tests/test_weighted_pathfinding.py
import unittest
from traveling_salesman_problem.problem.road_network import (
    RoadNetwork,
    canonical_edge,
    find_path,
    find_path_weighted,
    path_weighted_distance,
)

class WeightedPathfindingTests(unittest.TestCase):
    def setUp(self):
        # Two routes D—A—X and D—B—X; short via A (len 20), long via B (len 30)
        self.network = RoadNetwork(
            nodes={
                "D": (0.0, 0.0),
                "A": (10.0, 0.0),
                "B": (0.0, 15.0),
                "X": (20.0, 0.0),
            },
            edges=[("D", "A"), ("A", "X"), ("D", "B"), ("B", "X")],
            connection_radius=100.0,
        )

    def test_canonical_edge_order(self):
        self.assertEqual(canonical_edge("B", "A"), ("A", "B"))

    def test_empty_used_matches_unweighted_preference(self):
        path = find_path_weighted(self.network, "D", "X", reuse_penalty=1.75)
        self.assertEqual(path, ["D", "A", "X"])

    def test_reuse_prefers_alternate_route(self):
        used = {canonical_edge("D", "A"), canonical_edge("A", "X")}
        path = find_path_weighted(
            self.network, "X", "D", used_edges=used, reuse_penalty=1.75
        )
        self.assertEqual(path, ["X", "B", "D"])

    def test_single_path_still_reachable_with_reuse(self):
        line = RoadNetwork(
            nodes={"D": (0.0, 0.0), "X": (10.0, 0.0)},
            edges=[("D", "X")],
            connection_radius=20.0,
        )
        used = {canonical_edge("D", "X")}
        path = find_path_weighted(line, "D", "X", used_edges=used, reuse_penalty=1.75)
        self.assertEqual(path, ["D", "X"])
        cost = path_weighted_distance(line, path, used, 1.75)
        self.assertAlmostEqual(cost, 10.0 * 1.75)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests — expect FAIL** (missing symbols)

```bash
python -m unittest tests.test_weighted_pathfinding -v
```

- [ ] **Step 3: Implement** in `road_network.py` (heapq Dijkstra; do not remove `find_path`)

```python
import heapq
from typing import Set, Tuple

EdgeKey = Tuple[str, str]

def canonical_edge(node_a: str, node_b: str) -> EdgeKey:
    return (node_a, node_b) if node_a <= node_b else (node_b, node_a)

def edge_cost(network, node_a, node_b, used_edges, reuse_penalty):
    base = euclidean(network.nodes[node_a], network.nodes[node_b])
    if canonical_edge(node_a, node_b) in used_edges:
        return base * reuse_penalty
    return base

def path_weighted_distance(network, path, used_edges, reuse_penalty):
    if len(path) < 2:
        return 0.0
    total = 0.0
    for i in range(len(path) - 1):
        total += edge_cost(network, path[i], path[i + 1], used_edges, reuse_penalty)
    return total

def find_path_weighted(
    network, origin, destination, blocked=None, used_edges=None, reuse_penalty=1.0
):
    blocked = blocked or set()
    used_edges = used_edges or set()
    # same guards as find_path for missing/blocked/equal
    adjacency = _adjacency(network)
    dist = {origin: 0.0}
    prev = {origin: None}
    heap = [(0.0, origin)]
    while heap:
        cost, node = heapq.heappop(heap)
        if cost > dist.get(node, float("inf")):
            continue
        if node == destination:
            break
        for neighbor in adjacency.get(node, []):
            if neighbor in blocked:
                continue
            new_cost = cost + edge_cost(
                network, node, neighbor, used_edges, reuse_penalty
            )
            if new_cost < dist.get(neighbor, float("inf")):
                dist[neighbor] = new_cost
                prev[neighbor] = node
                heapq.heappush(heap, (new_cost, neighbor))
    if destination not in prev and origin != destination:
        return []
    # reconstruct path from prev; if origin==destination return [origin]
    ...
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
python -m unittest tests.test_weighted_pathfinding -v
```

- [ ] **Step 5: Do not commit**

---

### Task 2: Mesh segment API with used_edges

**Files:**
- Modify: `traveling_salesman_problem/problem/delivery_mesh.py`
- Extend: `tests/test_weighted_pathfinding.py` (or small mesh cases in same file)

**Interfaces:**
- Consumes: `find_path_weighted`, `path_weighted_distance`, `canonical_edge`
- Produces:
```python
def delivery_segment_path(
    mesh: DeliveryMesh,
    origin: Coordinate,
    destination: Coordinate,
    used_edges: Optional[Set[EdgeKey]] = None,
    reuse_penalty: float = 1.0,
) -> List[str]:
    # find_path_weighted(..., blocked=set(mesh.blocked_ids), used_edges, reuse_penalty)

def delivery_segment_distance(
    mesh: DeliveryMesh,
    origin: Coordinate,
    destination: Coordinate,
    used_edges: Optional[Set[EdgeKey]] = None,
    reuse_penalty: float = 1.0,
) -> float:
    # path then path_weighted_distance; empty → inf
```

Keep `expand_route_polyline` on unweighted `find_path` / default args (legacy TSP) unless a caller breaks — VRP UI will stop using it for vehicle plans.

- [ ] **Step 1:** Add a mesh-level test that after marking short edges used, return path uses alternate (reuse Task 1 diamond graph via `delivery_mesh_from_parts`).
- [ ] **Step 2:** FAIL → implement wrappers → PASS
- [ ] **Step 3: Do not commit**

---

### Task 3: Trip paths + decoder edge memory

**Files:**
- Modify: `traveling_salesman_problem/problem/vrp_models.py`
- Modify: `traveling_salesman_problem/problem/vrp_decoder.py`
- Modify: `traveling_salesman_problem/config/application_settings.py` (`edge_reuse_penalty: float = 1.75`)
- Modify: `traveling_salesman_problem/simulation/vehicle_genetic.py` (pass `reuse_penalty` into `decode_vehicle_permutation`)
- Test: `tests/test_vrp_decoder_edge_reuse.py`

**Interfaces:**
```python
@dataclass
class Trip:
    stops: list[TripStop]
    distance: float
    path_node_ids: list[list[str]]  # len == len(stops)-1; each is node id path for that segment

def decode_vehicle_permutation(
    ...,
    reuse_penalty: float = 1.75,
) -> DecodedVehiclePlan:
```

**Decoder algorithm (replace each `delivery_segment_distance` call):**

```python
used_edges: Set[EdgeKey] = set()
# helper:
def traverse(from_coord, to_coord) -> tuple[float, list[str]] | None:
    path = delivery_segment_path(mesh, from_coord, to_coord, used_edges, reuse_penalty)
    if not path:
        return None
    cost = delivery_segment_distance(mesh, from_coord, to_coord, used_edges, reuse_penalty)
    for i in range(len(path) - 1):
        used_edges.add(canonical_edge(path[i], path[i + 1]))
    return cost, path

# when appending a stop / closing trip:
# accumulate cost into current_distance; append path to current_paths list
# Trip(..., path_node_ids=list(current_paths))
```

`used_edges` must **not** reset when starting a new trip after capacity split.

- [ ] **Step 1: Failing tests**

```python
# tests/test_vrp_decoder_edge_reuse.py
# Build diamond mesh: DEPOT, X, A, B as in Task 1 (ids DEPOT, X, A, B)
# Token only X demand 1; capacity 10; reuse_penalty 1.75
# plan = decode...
# trip = plan.trips[0]
# assert trip.path_node_ids[0] == [DEPOT, "A", "X"]   # outbound short
# assert trip.path_node_ids[1] == ["X", "B", DEPOT]   # return alternate
# Single-edge mesh D—X: still finite fitness with reuse_penalty 1.75
```

Also update any test that constructs `Trip(...)` to include `path_node_ids=[]` or real lists (`test_route_panel.py`, `test_route_animation.py`).

- [ ] **Step 2:** FAIL → implement model + decoder + wire penalty from settings in `vehicle_genetic` / `initialize_vehicle_genetic` / `run_vehicle_generation` → PASS

```bash
python -m unittest tests.test_vrp_decoder_edge_reuse tests.test_vrp_decoder -v
```

- [ ] **Step 3: Do not commit**

---

### Task 4: Visualization consumes stored paths

**Files:**
- Modify: `traveling_salesman_problem/visualization/map_renderer.py`
- Modify: `traveling_salesman_problem/visualization/route_animation.py`
- Update: `tests/test_route_animation.py`

**Interfaces:**
- Consumes: `Trip.path_node_ids`, `mesh.network.nodes`
- Produces: polylines without calling `delivery_segment_path` for VRP plans

```python
def coordinates_from_path_node_ids(mesh, path_node_ids: list[str]) -> list[Coordinate]:
    return [mesh.network.nodes[node_id] for node_id in path_node_ids]

def _trip_polyline_from_stored(mesh, trip: Trip) -> list[Coordinate]:
    points = []
    for path in trip.path_node_ids:
        coords = coordinates_from_path_node_ids(mesh, path)
        if points and coords:
            coords = coords[1:]
        points.extend(coords)
    return points

# draw_vehicle_plans: use _trip_polyline_from_stored(trip) instead of re-pathfinding
# build_animation_polyline: concatenate trip.path_node_ids the same way
```

If `path_node_ids` empty (legacy), fall back to old `_trip_polyline` for safety.

- [ ] **Step 1:** Update animation test to set `path_node_ids=[["DEPOT","A"],["A","DEPOT"]]` on the Trip
- [ ] **Step 2:** Implement renderer/animation changes
- [ ] **Step 3:**

```bash
python -m unittest tests.test_route_animation tests.test_route_panel -v
```

- [ ] **Step 4: Do not commit**

---

### Task 5: Regression + smoke

**Files:** none new (fix call sites if `Trip(` constructors fail)

- [ ] **Step 1: Run suite**

```bash
python -m unittest tests.test_weighted_pathfinding tests.test_vrp_decoder_edge_reuse tests.test_vrp_decoder tests.test_vehicle_genetic tests.test_vrp_assignment tests.test_route_panel tests.test_route_animation tests.test_delivery_mesh tests.test_fitness_mesh_distance -v
```

Expected: all PASS

- [ ] **Step 2: Smoke import**

```bash
python -c "from traveling_salesman_problem.simulation.simulation_state import SimulationState; s=SimulationState(); s.initialize(); print(s.settings.edge_reuse_penalty, s.vehicle_states[0].best_plan.trips[0].path_node_ids[:1])"
```

- [ ] **Step 3: Manual** `python main.py` — filter V1; with enough transit, outbound/return should often differ
- [ ] **Step 4: Do not commit**

---

## Spec coverage

| Spec item | Task |
|-----------|------|
| `find_path_weighted` / canonical edge / soft cost | 1 |
| Mesh segment API | 2 |
| Decoder `used_edges` across trips; fitness weighted | 3 |
| Paths stored on `Trip`; UI draws them | 3, 4 |
| `edge_reuse_penalty = 1.75` always on | 3 |
| Per-vehicle memory only | 3 |
| Tests: 2-path, 1-path, decoder ida≠volta, regression | 1, 3, 5 |
| No chromosome/assignment change; no commit | all |

## Self-review notes

- No placeholders; `Trip.path_node_ids` is required (not optional ambiguity).
- Visualization must not re-run independent weighted memory (would desync).
- `genetic_algorithm/fitness.py` (legacy TSP) may keep unweighted defaults — only VRP decode path must use penalty.
