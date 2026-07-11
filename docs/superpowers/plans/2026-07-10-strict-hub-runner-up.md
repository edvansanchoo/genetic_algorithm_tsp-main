# Strict Hub + Runner-Up Route Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the delivery hub mesh so depot↔delivery has no direct edges (only via transit), and draw a dashed gray runner-up route for the focused vehicle’s best valid alternative plan.

**Architecture:** Generalize `build_delivery_hub_network` with `hub_set = {DEPOT} ∪ deliveries`; bump transit margin and outer retry loop in `build_vrp_mesh`; select `runner_up_plan` per generation in `vehicle_genetic`; wire through `simulation_state` and `map_renderer` only when `focus_vehicle_id` is set.

**Tech Stack:** Python 3.14, pygame-ce, unittest (`python -m unittest`).

## Global Constraints

- Branch: `feature/road-network-blocked-nodes`
- Spec: `docs/superpowers/specs/2026-07-10-strict-hub-runner-up-design.md`
- `hub_nodes = {DEPOT_ID} ∪ delivery_ids`; no edges between any two hub nodes
- Allowed edges: `DEPOT—T`, `Entrega—T`, `T—T`
- `no_through={DEPOT_ID}` on delivery→delivery segments (unchanged)
- Runner-up: best valid plan in current generation ≠ `best_plan`; only when vehicle focused
- Runner-up visual: `VisualTheme.route_second_best`, dashed, width=1, no arrows
- Transit margin: `ceil(tokens / veículos) + 10`
- `build_vrp_mesh`: re-sample transit; bump `transit_count += 2` up to `maximum_mesh_nodes_per_type`
- No decoder changes (`vrp_decoder.py` unchanged)

---

## File map

| File | Responsibility |
|------|----------------|
| Modify: `traveling_salesman_problem/problem/road_network.py` | Strict hub in `build_delivery_hub_network` |
| Modify: `traveling_salesman_problem/problem/delivery_mesh.py` | `effective_transit_count +10`; `build_vrp_mesh` outer bump loop |
| Modify: `traveling_salesman_problem/simulation/vehicle_genetic.py` | `runner_up_plan` selection |
| Modify: `traveling_salesman_problem/simulation/simulation_state.py` | Return `runner_up_plans` from `run_one_generation` |
| Modify: `traveling_salesman_problem/visualization/map_renderer.py` | `draw_runner_up_plan` |
| Modify: `traveling_salesman_problem/simulation/pygame_application.py` | Draw runner-up before best when focused |
| Modify: `traveling_salesman_problem/visualization/application_layout.py` | Legend entry |
| Modify: `tests/test_delivery_hub_mesh.py` | Strict topology + path tests |
| Modify: `tests/test_delivery_mesh.py` | Edge-count formula + transit margin |
| Modify: `tests/test_vehicle_genetic.py` | Runner-up selection tests |
| Create: `tests/test_runner_up_render.py` | Light render wiring test |

---

### Task 1: Strict hub network

**Files:**
- Modify: `traveling_salesman_problem/problem/road_network.py`
- Modify: `tests/test_delivery_hub_mesh.py`

**Interfaces:**
- Produces:
```python
def build_delivery_hub_network(
    nodes: Dict[str, Coordinate],
    delivery_ids: Sequence[str],
) -> RoadNetwork:
    # complete graph minus edges where BOTH endpoints in {DEPOT_ID, *delivery_ids}
```

- [ ] **Step 1: Update failing tests**

Replace/add in `tests/test_delivery_hub_mesh.py`:

```python
class DeliveryHubNetworkTests(unittest.TestCase):
    def test_no_hub_to_hub_edges(self) -> None:
        nodes = {
            DEPOT_ID: (0.0, 0.0),
            "A": (10.0, 0.0),
            "B": (0.0, 10.0),
            "T1": (5.0, 5.0),
        }
        network = build_delivery_hub_network(nodes, ["A", "B"])
        edge_set = {tuple(sorted(edge)) for edge in network.edges}
        self.assertNotIn(("A", "B"), edge_set)
        self.assertNotIn(tuple(sorted((DEPOT_ID, "A"))), edge_set)
        self.assertNotIn(tuple(sorted((DEPOT_ID, "B"))), edge_set)
        self.assertIn(tuple(sorted(("A", "T1"))), edge_set)
        self.assertIn(tuple(sorted((DEPOT_ID, "T1"))), edge_set)
        self.assertIn(tuple(sorted(("T1", "B"))), edge_set)

    def test_edge_count_formula_strict_hub(self) -> None:
        nodes = {
            DEPOT_ID: (0.0, 0.0),
            "A": (1.0, 0.0),
            "B": (2.0, 0.0),
            "T1": (3.0, 0.0),
        }
        network = build_delivery_hub_network(nodes, ["A", "B"])
        # 4 nodes, 6 pairs, hub pairs: DEPOT-A, DEPOT-B, A-B = 3 removed → 3 edges
        self.assertEqual(len(network.edges), 3)


class DeliveryHubPathTests(unittest.TestCase):
    def _hub_network(self):
        nodes = {
            DEPOT_ID: (0.0, 0.0),
            "A": (10.0, 0.0),
            "B": (20.0, 0.0),
            "T1": (10.0, 10.0),
        }
        return build_delivery_hub_network(nodes, ["A", "B"])

    def test_depot_to_delivery_uses_transit(self) -> None:
        network = self._hub_network()
        path = find_path(network, DEPOT_ID, "A")
        self.assertTrue(path)
        self.assertGreaterEqual(len(path), 3)
        self.assertIn("T1", path)
        self.assertEqual(path[0], DEPOT_ID)
        self.assertEqual(path[-1], "A")

    def test_delivery_to_depot_uses_transit(self) -> None:
        network = self._hub_network()
        path = find_path(network, "A", DEPOT_ID)
        self.assertTrue(path)
        self.assertIn("T1", path)

    def test_delivery_to_delivery_uses_transit_not_depot(self) -> None:
        network = self._hub_network()
        path = find_path_weighted(network, "A", "B", no_through={DEPOT_ID})
        self.assertTrue(path)
        self.assertIn("T1", path)
        self.assertNotIn(DEPOT_ID, path[1:-1])
```

Remove obsolete `test_depot_to_delivery_direct` and old edge-count test.

- [ ] **Step 2: Run tests — expect FAIL**

Run: `python -m unittest tests.test_delivery_hub_mesh -v`

Expected: FAIL — `DEPOT-A` still present or path direct

- [ ] **Step 3: Implement strict hub**

In `road_network.py`, update `build_delivery_hub_network`:

```python
def build_delivery_hub_network(
    nodes: Dict[str, Coordinate],
    delivery_ids: Sequence[str],
) -> RoadNetwork:
    hub_set = {DEPOT_ID, *delivery_ids}
    node_ids = list(nodes.keys())
    edges: List[Tuple[str, str]] = []
    for index, node_a in enumerate(node_ids):
        for node_b in node_ids[index + 1 :]:
            if node_a in hub_set and node_b in hub_set:
                continue
            edges.append((node_a, node_b))
    return RoadNetwork(
        nodes=dict(nodes),
        edges=edges,
        connection_radius=0.0,
    )
```

- [ ] **Step 4: Run tests — expect PASS**

Run: `python -m unittest tests.test_delivery_hub_mesh -v`

- [ ] **Step 5: Commit**

```bash
git add traveling_salesman_problem/problem/road_network.py tests/test_delivery_hub_mesh.py
git commit -m "feat(mesh): strict hub blocks depot-delivery direct edges"
```

---

### Task 2: Transit margin + mesh auto-bump

**Files:**
- Modify: `traveling_salesman_problem/problem/delivery_mesh.py`
- Modify: `tests/test_delivery_mesh.py`

**Interfaces:**
- Consumes: `build_delivery_hub_network` from Task 1
- Produces:
```python
def effective_transit_count(...) -> int:  # minimum uses + 10
def build_vrp_mesh(..., maximum_transit: Optional[int] = None) -> DeliveryMesh:
    # outer loop bumps transit_count by 2 until reachable or cap
```

- [ ] **Step 1: Write failing tests**

In `tests/test_delivery_mesh.py`:

```python
class EffectiveTransitCountTests(unittest.TestCase):
    def test_single_vehicle_margin_is_plus_ten(self):
        deliveries = [
            DeliveryPoint("A", (10.0, 0.0), priority=5, demand=10),
            DeliveryPoint("B", (20.0, 0.0), priority=7, demand=10),
        ]
        effective = effective_transit_count(
            deliveries, vehicle_count=1, capacity=10,
            requested_transit=5, maximum_transit=30,
        )
        # 2 tokens, ceil(2/1)+10 = 12
        self.assertEqual(effective, 12)


class StrictVrpMeshTests(unittest.TestCase):
    def test_build_vrp_mesh_reachable_with_strict_hub(self):
        depot = (400.0, 300.0)
        deliveries = [
            DeliveryPoint(f"P{i}", (100.0 + i * 40, 200.0), priority=5, demand=5)
            for i in range(12)
        ]
        mesh = build_vrp_mesh(
            depot, deliveries, map_bounds=(0, 0, 800, 600),
            transit_count=8, blocked_count=2, rng_seed=7,
            maximum_transit=20,
        )
        self.assertTrue(depot_reaches_all_deliveries(mesh))
        path = delivery_segment_path(mesh, depot, deliveries[0].coordinate)
        self.assertGreaterEqual(len(path), 3)
        self.assertTrue(set(mesh.transit_ids) & set(path))
```

Add imports: `depot_reaches_all_deliveries` from `delivery_mesh`.

Update `VrpMeshTests.test_build_vrp_mesh_includes_depot` edge-count assertion:

```python
hub_count = 1 + delivery_count  # DEPOT + deliveries
expected_edges = (
    node_count * (node_count - 1) // 2
    - hub_count * (hub_count - 1) // 2
)
```

Update path assertion: `len(path) >= 3` and transit in path.

- [ ] **Step 2: Run tests — expect FAIL**

Run: `python -m unittest tests.test_delivery_mesh.StrictVrpMeshTests tests.test_delivery_mesh.EffectiveTransitCountTests -v`

- [ ] **Step 3: Implement**

`effective_transit_count` — change `+ 6` to `+ 10`.

Refactor `build_vrp_mesh` with outer transit bump:

```python
def build_vrp_mesh(
    depot: Coordinate,
    deliveries: Sequence[DeliveryPoint],
    map_bounds: MapBounds,
    transit_count: int,
    blocked_count: int,
    rng: Optional[random.Random] = None,
    rng_seed: Optional[int] = None,
    max_rebuild_attempts: int = 40,
    maximum_transit: int = 20,
) -> DeliveryMesh:
    ...
    current_transit = transit_count
    while current_transit <= maximum_transit:
        for attempt in range(max_rebuild_attempts):
            # existing body using current_transit instead of transit_count
            ...
            if depot_reaches_all_deliveries(mesh):
                return mesh
        current_transit += 2
    raise RuntimeError("Could not build reachable VRP mesh")
```

Pass `maximum_transit=settings.maximum_mesh_nodes_per_type` from `rebuild_scenario` if adding parameter to call site (or hardcode 20 matching `ApplicationSettings`).

- [ ] **Step 4: Run tests — expect PASS**

Run: `python -m unittest tests.test_delivery_mesh -v`

- [ ] **Step 5: Commit**

```bash
git add traveling_salesman_problem/problem/delivery_mesh.py traveling_salesman_problem/simulation/simulation_state.py tests/test_delivery_mesh.py
git commit -m "feat(mesh): bump transit until strict hub mesh is reachable"
```

---

### Task 3: Runner-up plan in vehicle genetic

**Files:**
- Modify: `traveling_salesman_problem/simulation/vehicle_genetic.py`
- Modify: `tests/test_vehicle_genetic.py`

**Interfaces:**
- Consumes: `plan_has_drawable_trips`, `_should_replace_best_plan` (existing)
- Produces:
```python
@dataclass
class VehicleGeneticState:
    ...
    runner_up_plan: Optional[DecodedVehiclePlan] = None

def select_runner_up_plan(
    evaluated: List[Tuple[float, TokenRoute, DecodedVehiclePlan]],
    best_permutation: TokenRoute,
    best_fitness: float,
) -> Optional[DecodedVehiclePlan]

def run_vehicle_generation(...) -> VehicleGeneticState:
    # sets state.runner_up_plan each generation
```

- [ ] **Step 1: Write failing tests**

```python
from traveling_salesman_problem.simulation.vehicle_genetic import (
    select_runner_up_plan,
    plan_has_drawable_trips,
)

class RunnerUpSelectionTests(unittest.TestCase):
    def test_picks_first_valid_alternate(self):
        plan_a = DecodedVehiclePlan(trips=[Trip(...)], total_distance=10.0, priority_penalty=0.0, fitness=10.0)
        plan_b = DecodedVehiclePlan(trips=[Trip(...)], total_distance=20.0, priority_penalty=0.0, fitness=20.0)
        perm_a = [DeliveryToken("A", 1, 5)]
        perm_b = [DeliveryToken("B", 1, 5)]
        evaluated = [(10.0, perm_a, plan_a), (20.0, perm_b, plan_b)]
        runner = select_runner_up_plan(evaluated, perm_a, 10.0)
        self.assertIs(runner, plan_b)

    def test_returns_none_when_only_one_valid(self):
        valid = DecodedVehiclePlan(trips=[...], ...)
        invalid = DecodedVehiclePlan(trips=[], total_distance=float("inf"), priority_penalty=0.0, fitness=float("inf"))
        evaluated = [(10.0, [DeliveryToken("A", 1, 5)], valid), (float("inf"), [DeliveryToken("B", 1, 5)], invalid)]
        self.assertIsNone(select_runner_up_plan(evaluated, evaluated[0][1], 10.0))
```

Use real `Trip`/`TripStop` fixtures from existing tests or minimal stubs with `len(stops) >= 2`.

Add integration test in `VehicleGeneticTests`:

```python
def test_generation_sets_runner_up_when_alternate_exists(self):
    state = initialize_vehicle_genetic(...)
    for _ in range(5):
        state = run_vehicle_generation(state, ..., mutation_probability=0.5)
    if state.runner_up_plan:
        self.assertTrue(plan_has_drawable_trips(state.runner_up_plan))
        self.assertNotEqual(state.runner_up_plan.trips, state.best_plan.trips)
```

- [ ] **Step 2: Run tests — expect FAIL**

Run: `python -m unittest tests.test_vehicle_genetic.RunnerUpSelectionTests -v`

- [ ] **Step 3: Implement**

```python
def select_runner_up_plan(
    evaluated: List[Tuple[float, TokenRoute, DecodedVehiclePlan]],
    best_permutation: TokenRoute,
    best_fitness: float,
) -> Optional[DecodedVehiclePlan]:
    for index in range(1, len(evaluated)):
        fitness, permutation, plan = evaluated[index]
        if not plan_has_drawable_trips(plan):
            continue
        if permutation != best_permutation or fitness > best_fitness:
            return plan
    return None
```

In `run_vehicle_generation`, after sorting `evaluated`:

```python
state.runner_up_plan = select_runner_up_plan(
    evaluated, state.best_permutation, state.best_fitness
)
```

Initialize `runner_up_plan=None` in `initialize_vehicle_genetic`; set from first generation’s evaluated list using initial `best_permutation`.

- [ ] **Step 4: Run tests — expect PASS**

Run: `python -m unittest tests.test_vehicle_genetic -v`

- [ ] **Step 5: Commit**

```bash
git add traveling_salesman_problem/simulation/vehicle_genetic.py tests/test_vehicle_genetic.py
git commit -m "feat(ga): track runner-up valid plan per generation"
```

---

### Task 4: Wire simulation + render

**Files:**
- Modify: `traveling_salesman_problem/simulation/simulation_state.py`
- Modify: `traveling_salesman_problem/visualization/map_renderer.py`
- Modify: `traveling_salesman_problem/simulation/pygame_application.py`
- Modify: `traveling_salesman_problem/visualization/application_layout.py`
- Create: `tests/test_runner_up_render.py`

**Interfaces:**
- Consumes: `VehicleGeneticState.runner_up_plan`, `draw_runner_up_plan`
- Produces:
```python
def draw_runner_up_plan(
    screen: pygame.Surface,
    mesh: Optional[DeliveryMesh],
    plan: DecodedVehiclePlan,
    color: Tuple[int, int, int] = VisualTheme.route_second_best,
) -> None

# run_one_generation returns 8-tuple (add runner_up_plans dict)
```

- [ ] **Step 1: Write failing render test**

```python
# tests/test_runner_up_render.py
import unittest
from unittest.mock import MagicMock, patch
from traveling_salesman_problem.visualization.map_renderer import draw_runner_up_plan
from traveling_salesman_problem.problem.vrp_decoder import DecodedVehiclePlan

class DrawRunnerUpPlanTests(unittest.TestCase):
    @patch("traveling_salesman_problem.visualization.map_renderer._draw_dashed_polyline")
    def test_draws_dashed_for_each_trip(self, mock_dashed):
        screen = MagicMock()
        mesh = MagicMock()
        mesh.network.nodes = {"DEPOT": (0, 0), "A": (10, 0)}
        trip = MagicMock()
        trip.stops = [MagicMock(), MagicMock()]
        trip.path_node_ids = [["DEPOT", "A"]]
        plan = DecodedVehiclePlan(trips=[trip], total_distance=1.0, priority_penalty=0.0, fitness=1.0)
        draw_runner_up_plan(screen, mesh, plan)
        self.assertEqual(mock_dashed.call_count, 1)
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `python -m unittest tests.test_runner_up_render -v`

- [ ] **Step 3: Implement `draw_runner_up_plan`**

```python
def draw_runner_up_plan(
    screen: pygame.Surface,
    mesh: Optional[DeliveryMesh],
    plan: DecodedVehiclePlan,
    color: Tuple[int, int, int] = VisualTheme.route_second_best,
) -> None:
    if mesh is None:
        return
    for trip in plan.trips:
        if len(trip.stops) < 2:
            continue
        points = _trip_polyline_from_stored(mesh, trip)
        if len(points) < 2:
            continue
        _draw_dashed_polyline(screen, points, color, width=1)
```

**`simulation_state.run_one_generation`:** build `runner_up_plans` dict; extend return tuple.

**`pygame_application.py`:** unpack `runner_up_plans`; before `draw_vehicle_plans`:

```python
focus_id = simulation.focus_vehicle_id
if focus_id is not None and focus_id in runner_up_plans:
    draw_runner_up_plan(screen, simulation.mesh, runner_up_plans[focus_id])
```

**`application_layout.py`:** add legend item after `"Rota veículo"`:

```python
(VisualTheme.route_second_best, "2ª melhor (foco)"),
```

Export `draw_runner_up_plan` from `visualization/__init__.py` if needed.

- [ ] **Step 4: Run tests — expect PASS**

Run: `python -m unittest tests.test_runner_up_render -v`

- [ ] **Step 5: Full regression**

Run: `python -m unittest discover -s tests -q`

Expected: all tests OK (update any decoder test meshes that assumed DEPOT-A direct edge).

- [ ] **Step 6: Commit**

```bash
git add traveling_salesman_problem/simulation/simulation_state.py traveling_salesman_problem/simulation/pygame_application.py traveling_salesman_problem/visualization/map_renderer.py traveling_salesman_problem/visualization/application_layout.py tests/test_runner_up_render.py
git commit -m "feat(ui): dashed runner-up route when vehicle focused"
```

---

### Task 5: Fix test fixtures + manual verification

**Files:**
- Modify: any failing tests in `tests/test_vrp_decoder.py`, `tests/test_return_path_diversification.py`, `tests/test_vrp_decoder_edge_reuse.py` that assumed DEPOT-delivery direct hub edges

**Interfaces:**
- Consumes: strict hub from Task 1

- [ ] **Step 1: Run full suite, collect failures**

Run: `python -m unittest discover -s tests -v 2>&1 | findstr /i fail`

- [ ] **Step 2: Update manual test networks**

For each manual `RoadNetwork` used in decoder tests, ensure paths exist without DEPOT-delivery direct:
- Add transit node `T1` between DEPOT and deliveries
- Edges: `(DEPOT, "T1")`, `("T1", "A")`, etc.
- Keep delivery-delivery absent

Example diamond fix:

```python
nodes = {DEPOT_ID: (0,0), "A": (10,0), "B": (10,10), "X": (20,0), "T1": (5,5)}
edges = [
    (DEPOT_ID, "T1"), ("T1", "A"), ("T1", DEPOT_ID),
    ("A", "T1"), ("T1", "X"), (DEPOT_ID, "B"), ("B", "T1"), ("T1", "X"),
]
```

Adjust per test’s expected paths.

- [ ] **Step 3: Run full suite — expect PASS**

Run: `python -m unittest discover -s tests -q`

- [ ] **Step 4: Manual smoke test**

Run: `python main.py`

1. Filtro **Todos** → sem linha cinza
2. Filtro **V1** → melhor colorida + tracejado cinza (se GA tiver alternativa válida)
3. Malha on → sem aresta DEPOT↔entrega

- [ ] **Step 5: Commit**

```bash
git add tests/
git commit -m "test: update fixtures for strict hub topology"
```

---

## Spec coverage checklist

| Spec requirement | Task |
|------------------|------|
| No DEPOT↔entrega edges | Task 1 |
| Paths via transit | Task 1, 5 |
| `effective_transit +10` | Task 2 |
| `build_vrp_mesh` auto-bump | Task 2 |
| `runner_up_plan` selection | Task 3 |
| Focus-only render | Task 4 |
| Legend entry | Task 4 |
| Regression tests | Task 5 |

## Execution handoff

Plan saved to `docs/superpowers/plans/2026-07-10-strict-hub-runner-up.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks
2. **Inline Execution** — implement tasks in this session with checkpoints

Which approach do you want?
