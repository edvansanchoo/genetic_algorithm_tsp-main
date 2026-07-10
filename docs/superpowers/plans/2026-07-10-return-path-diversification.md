# Return Path Diversification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Force depot return segments to use a different route than the outbound legs of the same trip, via hard edge blocking with soft ×20 fallback.

**Architecture:** Extend `find_path_weighted` with `forbidden_edges` (skip in Dijkstra). Decoder tracks `trip_edges` per trip; non-return legs keep vehicle-level soft ×1.75; `close_trip_returning_to_depot` tries hard block first, then weighted fallback. Return cost is real distance on hard path, weighted on fallback.

**Tech Stack:** Python, unittest, existing Pygame UI (decoder-only change).

## Global Constraints

- Branch: `feature/road-network-blocked-nodes`
- Spec: `docs/superpowers/specs/2026-07-10-return-path-diversification-design.md`
- `edge_reuse_penalty = 1.75` (unchanged for non-return segments)
- `return_fallback_penalty = 20.0` (new)
- Hard block scope: all edges used in **current trip** on return-to-depot only
- Never `fitness = ∞` solely because return reuses trip edges (fallback first)
- Do not change chromosome, assignment, or GA operators
- Map/animation draw stored `Trip.path_node_ids` only (no pathfinding in UI)

---

## File map

| File | Responsibility |
|------|----------------|
| Modify: `traveling_salesman_problem/problem/road_network.py` | `forbidden_edges` in `find_path_weighted` / `edge_cost` |
| Modify: `traveling_salesman_problem/problem/delivery_mesh.py` | Propagate `forbidden_edges` on segment path/distance |
| Modify: `traveling_salesman_problem/problem/vrp_decoder.py` | `trip_edges`; hard return + fallback in `close_trip` |
| Modify: `traveling_salesman_problem/config/application_settings.py` | `return_fallback_penalty: float = 20.0` |
| Modify: `traveling_salesman_problem/simulation/vehicle_genetic.py` | Pass `return_fallback_penalty` into decode |
| Modify: `traveling_salesman_problem/simulation/simulation_state.py` | Wire setting into genetic init/run |
| Test: `tests/test_return_path_diversification.py` | Hard + fallback + decoder integration |
| Update: `tests/test_vrp_decoder_edge_reuse.py` | Align expectations if needed |

---

### Task 1: `forbidden_edges` in pathfinding

**Files:**
- Modify: `traveling_salesman_problem/problem/road_network.py`
- Test: `tests/test_return_path_diversification.py` (pathfinding section)

**Interfaces:**
- Produces:
```python
def edge_cost(
    network: RoadNetwork,
    node_a: str,
    node_b: str,
    used_edges: Set[EdgeKey],
    reuse_penalty: float,
    forbidden_edges: Optional[Set[EdgeKey]] = None,
) -> float:
    # if canonical_edge in forbidden_edges → return float("inf")

def find_path_weighted(
    network: RoadNetwork,
    origin: str,
    destination: str,
    blocked: Optional[Set[str]] = None,
    used_edges: Optional[Set[EdgeKey]] = None,
    reuse_penalty: float = 1.0,
    forbidden_edges: Optional[Set[EdgeKey]] = None,
) -> List[str]:
```

- [ ] **Step 1: Write failing tests**

```python
# tests/test_return_path_diversification.py — class ForbiddenEdgePathfindingTests
def test_return_uses_alternate_when_outbound_edges_forbidden(self):
    network = RoadNetwork(
        nodes={"DEPOT": (0,0), "A": (10,0), "B": (10,10), "X": (20,0)},
        edges=[("DEPOT","A"),("A","X"),("DEPOT","B"),("B","X")],
        connection_radius=100.0,
    )
    outbound = {canonical_edge("DEPOT","A"), canonical_edge("A","X")}
    path = find_path_weighted(network, "X", "DEPOT", forbidden_edges=outbound)
    self.assertEqual(path, ["X", "B", "DEPOT"])

def test_forbidden_empty_matches_shortest(self):
    # same diamond, no forbidden → D,A,X from DEPOT to X
    ...
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
python -m unittest tests.test_return_path_diversification.ForbiddenEdgePathfindingTests -v
```

- [ ] **Step 3: Implement** `edge_cost` + `find_path_weighted` forbidden skip

```python
def edge_cost(..., forbidden_edges=None):
    forbidden_edges = forbidden_edges or set()
    key = canonical_edge(node_a, node_b)
    if key in forbidden_edges:
        return float("inf")
    ...
```

- [ ] **Step 4: Run tests — expect PASS**

- [ ] **Step 5: Commit**

```bash
git add traveling_salesman_problem/problem/road_network.py tests/test_return_path_diversification.py
git commit -m "feat(path): add forbidden_edges to weighted pathfinding"
```

---

### Task 2: Mesh segment API + fallback distance helper

**Files:**
- Modify: `traveling_salesman_problem/problem/delivery_mesh.py`
- Extend: `tests/test_return_path_diversification.py`

**Interfaces:**
```python
def delivery_segment_path(
    mesh, origin, destination,
    used_edges=None, reuse_penalty=1.0,
    forbidden_edges=None,
) -> List[str]

def delivery_segment_distance(
    mesh, origin, destination,
    used_edges=None, reuse_penalty=1.0,
    forbidden_edges=None,
) -> float
```

Add helper in decoder or mesh (decoder-local is fine):

```python
def return_segment_cost(
    mesh, origin, destination, trip_edges, fallback_penalty,
) -> Optional[Tuple[float, List[str]]]:
    # 1) path = segment(..., forbidden_edges=trip_edges, penalty=1.0)
    # 2) if empty: path = segment(..., used_edges=trip_edges, penalty=fallback_penalty)
    # 3) cost = path_distance if hard else path_weighted_distance
```

- [ ] **Step 1:** Mesh test — `delivery_segment_path` with `forbidden_edges` returns alternate
- [ ] **Step 2:** FAIL → implement wrappers → PASS
- [ ] **Step 3: Commit**

```bash
git commit -m "feat(mesh): propagate forbidden_edges on segments"
```

---

### Task 3: Decoder `trip_edges` + hard return

**Files:**
- Modify: `traveling_salesman_problem/problem/vrp_decoder.py`
- Modify: `traveling_salesman_problem/config/application_settings.py`
- Modify: `traveling_salesman_problem/simulation/vehicle_genetic.py`
- Modify: `traveling_salesman_problem/simulation/simulation_state.py`
- Extend: `tests/test_return_path_diversification.py`, `tests/test_vrp_decoder_edge_reuse.py`

**Interfaces:**
```python
def decode_vehicle_permutation(
    ...,
    reuse_penalty: float = 1.75,
    return_fallback_penalty: float = 20.0,
) -> DecodedVehiclePlan
```

**Decoder changes:**

```python
trip_edges: Set[EdgeKey] = set()  # reset when new trip starts (after close_trip)

def traverse_non_return(from_coord, to_coord):
    # existing logic + trip_edges.add(canonical_edge(...)) for each edge in path

def close_trip_returning_to_depot():
    # result = return_segment_cost(mesh, last_coordinate, depot, trip_edges, return_fallback_penalty)
    # on success: append path, update used_edges (vehicle), reset trip_edges on new trip
    # trip_edges cleared when starting new trip after close
```

Wire `return_fallback_penalty` from `ApplicationSettings` through `initialize_vehicle_genetic` / `run_vehicle_generation`.

- [ ] **Step 1: Failing decoder tests**

```python
def test_decoder_return_differs_from_outbound_on_diamond(self):
    # D→A→X outbound; return X→B→DEPOT
    self.assertEqual(trip.path_node_ids[1], ["X", "B", DEPOT_ID])

def test_decoder_single_edge_fallback_finite(self):
    # line mesh; fitness < inf; may reuse same edge
```

- [ ] **Step 2:** FAIL → implement → PASS

```bash
python -m unittest tests.test_return_path_diversification tests.test_vrp_decoder_edge_reuse tests.test_vrp_decoder -v
```

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(vrp): hard-block trip edges on depot return"
```

---

### Task 4: Regression + smoke

- [ ] **Step 1: Full suite**

```bash
python -m unittest tests.test_return_path_diversification tests.test_weighted_pathfinding tests.test_vrp_decoder_edge_reuse tests.test_vrp_decoder tests.test_vehicle_genetic tests.test_vrp_assignment tests.test_route_animation -v
```

- [ ] **Step 2: Smoke**

```bash
python -c "from traveling_salesman_problem.simulation.simulation_state import SimulationState; s=SimulationState(); s.initialize(); t=s.vehicle_states[0].best_plan.trips[0]; print(t.path_node_ids)"
```

- [ ] **Step 3: Manual** `python main.py` — filter V1; verify return line ≠ outbound when transit allows
- [ ] **Step 4: Commit** (if any test fixes)

```bash
git commit -m "test: regression for return path diversification"
```

---

## Spec coverage

| Spec item | Task |
|-----------|------|
| `forbidden_edges` hard block | 1 |
| Mesh propagation | 2 |
| `trip_edges` per trip | 3 |
| Hard return + ×20 fallback | 3 |
| Real cost on hard; weighted on fallback | 3 |
| `return_fallback_penalty = 20.0` | 3 |
| Non-return soft ×1.75 unchanged | 3 |
| UI unchanged | — |
| Tests hard / fallback / decoder | 1, 3, 4 |

## Self-review notes

- `trip_edges` must reset when a new trip opens after capacity split, not only at vehicle plan start.
- Return hard attempt uses `forbidden_edges=trip_edges` with `reuse_penalty=1.0` (no double penalty).
- `used_edges` (vehicle) still updated with return edges for subsequent trips.
- Existing `test_vrp_decoder_edge_reuse` should still pass (hard block is stricter than soft ×1.75).
