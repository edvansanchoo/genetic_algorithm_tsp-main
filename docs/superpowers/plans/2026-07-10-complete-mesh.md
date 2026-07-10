# Complete Mesh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace radius-limited mesh edges with a complete graph among depot, deliveries, and transit nodes; blocked nodes stay outside the graph; remove `connection_radius` from simulation settings.

**Architecture:** Add `build_complete_graph` / `build_complete_network` in `road_network.py`; mesh builders assemble `nodes` (no blocked ids) then call complete network builder instead of `build_connected_network`. Settings and simulation stop passing radius. Manual `RoadNetwork` in tests unchanged.

**Tech Stack:** Python 3, unittest, pygame (smoke only).

## Global Constraints

- Branch: `feature/road-network-blocked-nodes`
- Spec: `docs/superpowers/specs/2026-07-10-complete-mesh-design.md`
- Blocked nodes (`B*`) never in `network.nodes`
- `build_radius_graph` and `build_connected_network` remain for radius unit tests
- `RoadNetwork.connection_radius` kept on dataclass; generated meshes use `0.0`
- No changes to `vrp_decoder.py`, `vehicle_genetic.py`, `map_renderer.py`
- Edge cost and pathfinding logic unchanged (euclidean Dijkstra/BFS)

---

## File map

| File | Responsibility |
|------|----------------|
| Modify: `traveling_salesman_problem/problem/road_network.py` | `build_complete_graph`, `build_complete_network` |
| Modify: `traveling_salesman_problem/problem/delivery_mesh.py` | Use complete network; drop `connection_radius` param |
| Modify: `traveling_salesman_problem/config/application_settings.py` | Remove `connection_radius` |
| Modify: `traveling_salesman_problem/simulation/simulation_state.py` | Stop passing radius to `build_vrp_mesh` |
| Modify: `tests/test_delivery_mesh.py` | New complete-graph tests; update `build_*_mesh` calls |

---

### Task 1: Complete graph builders

**Files:**
- Modify: `traveling_salesman_problem/problem/road_network.py` (after `build_radius_graph`)
- Modify: `tests/test_delivery_mesh.py` (`RoadNetworkTests` class)

**Interfaces:**
- Produces:
```python
def build_complete_graph(nodes: Dict[str, Coordinate]) -> List[Tuple[str, str]]:
    """One undirected edge per unordered pair of node ids."""

def build_complete_network(nodes: Dict[str, Coordinate]) -> RoadNetwork:
    """RoadNetwork with all pairs connected; connection_radius=0.0."""
```

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_delivery_mesh.py — add to RoadNetworkTests

    def test_build_complete_graph_connects_all_pairs(self):
        from traveling_salesman_problem.problem.road_network import build_complete_graph

        nodes = {
            "D0": (0.0, 0.0),
            "D1": (5.0, 0.0),
            "T1": (2.0, 3.0),
            "T2": (8.0, 1.0),
        }
        edges = build_complete_graph(nodes)
        self.assertEqual(len(edges), 6)  # 4 * 3 / 2
        edge_set = {tuple(sorted(pair)) for pair in edges}
        self.assertIn(("D0", "D1"), edge_set)
        self.assertIn(("D0", "T2"), edge_set)
        self.assertIn(("T1", "T2"), edge_set)

    def test_build_complete_network_has_zero_radius(self):
        from traveling_salesman_problem.problem.road_network import build_complete_network

        nodes = {"A": (0.0, 0.0), "B": (100.0, 0.0)}
        network = build_complete_network(nodes)
        self.assertEqual(len(network.edges), 1)
        self.assertEqual(network.connection_radius, 0.0)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_delivery_mesh.RoadNetworkTests.test_build_complete_graph_connects_all_pairs tests.test_delivery_mesh.RoadNetworkTests.test_build_complete_network_has_zero_radius -v`

Expected: FAIL with `ImportError` or `cannot import name 'build_complete_graph'`

- [ ] **Step 3: Implement builders**

```python
# traveling_salesman_problem/problem/road_network.py — after build_radius_graph

def build_complete_graph(nodes: Dict[str, Coordinate]) -> List[Tuple[str, str]]:
    node_ids = list(nodes.keys())
    edges: List[Tuple[str, str]] = []
    for index, node_a in enumerate(node_ids):
        for node_b in node_ids[index + 1 :]:
            edges.append((node_a, node_b))
    return edges


def build_complete_network(nodes: Dict[str, Coordinate]) -> RoadNetwork:
    return RoadNetwork(
        nodes=dict(nodes),
        edges=build_complete_graph(nodes),
        connection_radius=0.0,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_delivery_mesh.RoadNetworkTests -v`

Expected: all PASS (including existing radius tests)

- [ ] **Step 5: Commit**

```bash
git add traveling_salesman_problem/problem/road_network.py tests/test_delivery_mesh.py
git commit -m "feat(mesh): add complete graph network builders"
```

---

### Task 2: Wire mesh builders to complete graph

**Files:**
- Modify: `traveling_salesman_problem/problem/delivery_mesh.py`
- Modify: `tests/test_delivery_mesh.py` (`DeliveryMeshTests`, `VrpMeshTests`)

**Interfaces:**
- Consumes: `build_complete_network` from Task 1
- Produces: `build_delivery_mesh` and `build_vrp_mesh` without `connection_radius` parameter

- [ ] **Step 1: Write failing mesh integration tests**

```python
# tests/test_delivery_mesh.py — add to DeliveryMeshTests

    def test_generated_mesh_is_complete_graph(self):
        cities = [(0.0, 0.0), (100.0, 0.0), (50.0, 80.0)]
        mesh = build_delivery_mesh(
            cities,
            map_bounds=(-20, -20, 120, 120),
            transit_count=4,
            blocked_count=1,
            rng_seed=1,
        )
        node_count = len(mesh.network.nodes)
        expected_edges = node_count * (node_count - 1) // 2
        self.assertEqual(len(mesh.network.edges), expected_edges)
        for transit_id in mesh.transit_ids:
            degree = sum(
                1
                for a, b in mesh.network.edges
                if transit_id in (a, b)
            )
            self.assertGreaterEqual(degree, 1)

    def test_blocked_not_in_network_nodes(self):
        cities = [(0.0, 0.0), (100.0, 0.0)]
        mesh = build_delivery_mesh(
            cities,
            map_bounds=(-20, -20, 120, 120),
            transit_count=2,
            blocked_count=2,
            rng_seed=3,
        )
        for blocked_id in mesh.blocked_ids:
            self.assertNotIn(blocked_id, mesh.network.nodes)
```

```python
# tests/test_delivery_mesh.py — update VrpMeshTests.test_build_vrp_mesh_includes_depot

        mesh = build_vrp_mesh(
            depot,
            deliveries,
            map_bounds=(-10, -10, 60, 60),
            transit_count=3,
            blocked_count=1,
            rng_seed=11,
        )
        node_count = len(mesh.network.nodes)
        self.assertEqual(
            len(mesh.network.edges),
            node_count * (node_count - 1) // 2,
        )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_delivery_mesh.DeliveryMeshTests.test_generated_mesh_is_complete_graph tests.test_delivery_mesh.VrpMeshTests -v`

Expected: FAIL — `TypeError` (unexpected `connection_radius`) or edge count mismatch

- [ ] **Step 3: Update delivery_mesh.py**

```python
# traveling_salesman_problem/problem/delivery_mesh.py

# Replace import:
from traveling_salesman_problem.problem.road_network import (
    ...
    build_complete_network,
)
# Remove: build_connected_network (if no longer used in this file)

# build_delivery_mesh — remove connection_radius param and usage:
def build_delivery_mesh(
    city_coordinates: Sequence[Coordinate],
    map_bounds: MapBounds,
    transit_count: int,
    blocked_count: int,
    rng: Optional[random.Random] = None,
    rng_seed: Optional[int] = None,
    max_rebuild_attempts: int = 40,
) -> DeliveryMesh:
    ...
        network = build_complete_network(nodes)
        mesh = DeliveryMesh(...)
        if deliveries_mutually_reachable(mesh):
            return mesh

# build_vrp_mesh — same pattern:
def build_vrp_mesh(
    depot: Coordinate,
    deliveries: Sequence[DeliveryPoint],
    map_bounds: MapBounds,
    transit_count: int,
    blocked_count: int,
    rng: Optional[random.Random] = None,
    rng_seed: Optional[int] = None,
    max_rebuild_attempts: int = 40,
) -> DeliveryMesh:
    ...
        network = build_complete_network(nodes)
        mesh = DeliveryMesh(...)
        if depot_reaches_all_deliveries(mesh):
            return mesh
```

- [ ] **Step 4: Update existing test calls — remove `connection_radius=`**

In `tests/test_delivery_mesh.py`, remove `connection_radius=...` from every `build_delivery_mesh` and `build_vrp_mesh` call (4 call sites in current file).

- [ ] **Step 5: Run delivery mesh tests**

Run: `python -m unittest tests.test_delivery_mesh -v`

Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add traveling_salesman_problem/problem/delivery_mesh.py tests/test_delivery_mesh.py
git commit -m "feat(mesh): build VRP and delivery meshes as complete graphs"
```

---

### Task 3: Remove connection_radius from settings + regression

**Files:**
- Modify: `traveling_salesman_problem/config/application_settings.py`
- Modify: `traveling_salesman_problem/simulation/simulation_state.py`

**Interfaces:**
- Consumes: `build_vrp_mesh` without `connection_radius` from Task 2

- [ ] **Step 1: Remove setting**

```python
# traveling_salesman_problem/config/application_settings.py
# Delete line:
#     connection_radius: float = 140.0
```

- [ ] **Step 2: Update simulation_state.py**

```python
# traveling_salesman_problem/simulation/simulation_state.py — rebuild_scenario
        self.mesh = build_vrp_mesh(
            self.depot,
            self.deliveries,
            self.map_bounds(),
            transit_count=transit_count,
            blocked_count=blocked_count,
            # remove: connection_radius=settings.connection_radius,
        )
```

- [ ] **Step 3: Grep for stray references**

Run: `rg "connection_radius" traveling_salesman_problem tests`

Expected: only `road_network.py` (dataclass + radius builders), manual `RoadNetwork(...)` in tests, and docs — **not** in `application_settings.py`, `delivery_mesh.py` builders, or `simulation_state.py`.

- [ ] **Step 4: Full regression**

Run:
```bash
python -m unittest tests.test_delivery_mesh tests.test_return_path_diversification tests.test_vrp_decoder tests.test_vrp_decoder_edge_reuse tests.test_vehicle_genetic tests.test_weighted_pathfinding tests.test_vrp_assignment tests.test_route_animation tests.test_fitness_mesh_distance -v
```

Expected: all PASS

- [ ] **Step 5: Smoke init**

Run:
```bash
python -c "from traveling_salesman_problem.simulation.simulation_state import SimulationState; s=SimulationState(); s.initialize(); print('nodes', len(s.mesh.network.nodes), 'edges', len(s.mesh.network.edges))"
```

Expected: prints finite nodes/edges; edges == n*(n-1)/2

- [ ] **Step 6: Commit**

```bash
git add traveling_salesman_problem/config/application_settings.py traveling_salesman_problem/simulation/simulation_state.py
git commit -m "refactor(mesh): drop connection_radius from simulation settings"
```

---

## Spec coverage check

| Spec requirement | Task |
|------------------|------|
| Complete graph topology | Task 1 + 2 |
| Blocked outside `network.nodes` | Task 2 tests |
| Remove `connection_radius` from settings/simulation | Task 3 |
| Keep `build_radius_graph` for unit tests | Task 1 (unchanged) |
| `RoadNetwork.connection_radius=0.0` on generated mesh | Task 1 |
| Regression suite | Task 3 step 4 |

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-10-complete-mesh.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks
2. **Inline Execution** — implement tasks in this session with checkpoints

Which approach?
