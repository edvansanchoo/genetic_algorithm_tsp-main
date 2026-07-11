# Manual Blocked Nodes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the "Bloqueados" slider with map-click toggle blocking on existing nodes, updating the mesh incrementally without moving points or redrawing stored routes.

**Architecture:** Remove random blocked-node generation from mesh builders; add `toggle_node_blocked` / `resolve_node_coordinate` in `delivery_mesh.py`; wire map hit-test and click handler in simulation; renderer resolves stored path coordinates from active or blocked nodes.

**Tech Stack:** Python 3, pygame, unittest.

## Global Constraints

- Branch: `feature/road-network-blocked-nodes`
- Spec: `docs/superpowers/specs/2026-07-11-manual-blocked-nodes-design.md`
- Block via click toggle on depot, delivery, or transit nodes
- No `rebuild_scenario` on block/unblock; GA and `best_plan` unchanged
- Stored routes use `trip.path_node_ids` — do not recalculate on toggle
- `blocked_ids` cleared on `rebuild_scenario` / `shuffle_all`
- Seed excludes `blocked_count`
- Slider "Bloqueados" removed from UI
- Draw order: deliveries → depot → blocked overlay last

---

## File map

| File | Responsibility |
|------|----------------|
| Modify: `traveling_salesman_problem/problem/delivery_mesh.py` | Toggle block, resolve coords, rebuild network; remove random blocked generation |
| Create: `traveling_salesman_problem/visualization/map_hit_test.py` | Pure hit-test for map nodes |
| Modify: `traveling_salesman_problem/simulation/simulation_state.py` | Remove slider; `toggle_blocked_at`; seed fix; clear blocks on rebuild |
| Modify: `traveling_salesman_problem/simulation/pygame_application.py` | Map click handler; draw order; remove slider draw |
| Modify: `traveling_salesman_problem/visualization/map_renderer.py` | Use `resolve_node_coordinate` in stored polyline |
| Modify: `traveling_salesman_problem/config/application_settings.py` | Remove `initial_blocked_count` |
| Modify: `tests/test_delivery_mesh.py` | Adapt blocked tests + toggle tests |
| Create: `tests/test_map_hit_test.py` | Hit-test unit tests |
| Modify: `tests/test_fitness_mesh_distance.py` | Remove `blocked_count` from mesh build |
| Modify: `tests/test_delivery_hub_mesh.py` | Remove `blocked_count` from mesh build |

---

### Task 1: Mesh toggle and coordinate resolution

**Files:**
- Modify: `traveling_salesman_problem/problem/delivery_mesh.py`
- Modify: `tests/test_delivery_mesh.py`

**Interfaces:**
- Produces:
```python
def resolve_node_coordinate(mesh: DeliveryMesh, node_id: str) -> Coordinate: ...

def rebuild_mesh_network(
    mesh: DeliveryMesh,
    delivery_ids: Sequence[str],
) -> DeliveryMesh: ...

def toggle_node_blocked(
    mesh: DeliveryMesh,
    node_id: str,
    delivery_ids: Sequence[str],
) -> DeliveryMesh: ...
```

- [ ] **Step 1: Write failing tests**

Add to `tests/test_delivery_mesh.py`:

```python
from traveling_salesman_problem.problem.delivery_mesh import (
    build_delivery_mesh,
    resolve_node_coordinate,
    toggle_node_blocked,
)
from traveling_salesman_problem.problem.vrp_models import DEPOT_ID


class ManualBlockedNodeTests(unittest.TestCase):
    def _sample_mesh(self):
        cities = [(0.0, 0.0), (100.0, 0.0)]
        return build_delivery_mesh(
            cities,
            map_bounds=(-20, -20, 120, 120),
            transit_count=4,
            rng_seed=1,
        )

    def test_toggle_block_removes_transit_from_network(self):
        mesh = self._sample_mesh()
        transit_id = mesh.transit_ids[0]
        original_coord = mesh.network.nodes[transit_id]

        updated = toggle_node_blocked(mesh, transit_id, mesh.delivery_ids)

        self.assertIn(transit_id, updated.blocked_ids)
        self.assertEqual(updated.blocked_coordinates[transit_id], original_coord)
        self.assertNotIn(transit_id, updated.network.nodes)

    def test_toggle_unblock_restores_transit_to_network(self):
        mesh = self._sample_mesh()
        transit_id = mesh.transit_ids[0]
        blocked = toggle_node_blocked(mesh, transit_id, mesh.delivery_ids)
        restored = toggle_node_blocked(blocked, transit_id, mesh.delivery_ids)

        self.assertNotIn(transit_id, restored.blocked_ids)
        self.assertIn(transit_id, restored.network.nodes)

    def test_resolve_coordinate_for_blocked_node(self):
        mesh = self._sample_mesh()
        transit_id = mesh.transit_ids[0]
        original_coord = mesh.network.nodes[transit_id]
        blocked = toggle_node_blocked(mesh, transit_id, mesh.delivery_ids)

        self.assertEqual(
            resolve_node_coordinate(blocked, transit_id),
            original_coord,
        )

    def test_blocked_transit_not_on_new_path(self):
        mesh = self._sample_mesh()
        cities = [(0.0, 0.0), (100.0, 0.0)]
        transit_id = mesh.transit_ids[0]
        blocked = toggle_node_blocked(mesh, transit_id, mesh.delivery_ids)
        path = delivery_segment_path(blocked, cities[0], cities[1])

        self.assertTrue(path)
        self.assertNotIn(transit_id, path)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_delivery_mesh.ManualBlockedNodeTests -v`

Expected: FAIL — `ImportError: cannot import name 'toggle_node_blocked'`

- [ ] **Step 3: Implement helpers in `delivery_mesh.py`**

Add after `delivery_mesh_from_parts`:

```python
def resolve_node_coordinate(mesh: DeliveryMesh, node_id: str) -> Coordinate:
    if node_id in mesh.network.nodes:
        return mesh.network.nodes[node_id]
    if node_id in mesh.blocked_coordinates:
        return mesh.blocked_coordinates[node_id]
    raise KeyError(f"Unknown node id: {node_id}")


def rebuild_mesh_network(
    mesh: DeliveryMesh,
    delivery_ids: Sequence[str],
) -> DeliveryMesh:
    active_nodes = dict(mesh.network.nodes)
    network = build_delivery_hub_network(active_nodes, delivery_ids)
    return DeliveryMesh(
        network=network,
        delivery_ids=list(mesh.delivery_ids),
        transit_ids=list(mesh.transit_ids),
        blocked_ids=set(mesh.blocked_ids),
        blocked_coordinates=dict(mesh.blocked_coordinates),
        coordinate_to_id={
            network.nodes[node_id]: node_id
            for node_id in network.nodes
            if node_id in delivery_ids or node_id == DEPOT_ID
        },
    )


def toggle_node_blocked(
    mesh: DeliveryMesh,
    node_id: str,
    delivery_ids: Sequence[str],
) -> DeliveryMesh:
    if node_id in mesh.blocked_ids:
        coordinate = mesh.blocked_coordinates[node_id]
        blocked_ids = set(mesh.blocked_ids)
        blocked_coordinates = dict(mesh.blocked_coordinates)
        blocked_ids.remove(node_id)
        del blocked_coordinates[node_id]
        active_nodes = dict(mesh.network.nodes)
        active_nodes[node_id] = coordinate
        interim = DeliveryMesh(
            network=RoadNetwork(
                nodes=active_nodes,
                edges=mesh.network.edges,
                connection_radius=mesh.network.connection_radius,
            ),
            delivery_ids=list(mesh.delivery_ids),
            transit_ids=list(mesh.transit_ids),
            blocked_ids=blocked_ids,
            blocked_coordinates=blocked_coordinates,
            coordinate_to_id=dict(mesh.coordinate_to_id),
        )
        return rebuild_mesh_network(interim, delivery_ids)

    if node_id not in mesh.network.nodes:
        raise KeyError(f"Cannot block unknown active node: {node_id}")

    coordinate = mesh.network.nodes[node_id]
    active_nodes = dict(mesh.network.nodes)
    del active_nodes[node_id]
    blocked_ids = set(mesh.blocked_ids)
    blocked_coordinates = dict(mesh.blocked_coordinates)
    blocked_ids.add(node_id)
    blocked_coordinates[node_id] = coordinate
    interim = DeliveryMesh(
        network=RoadNetwork(
            nodes=active_nodes,
            edges=[],
            connection_radius=mesh.network.connection_radius,
        ),
        delivery_ids=list(mesh.delivery_ids),
        transit_ids=list(mesh.transit_ids),
        blocked_ids=blocked_ids,
        blocked_coordinates=blocked_coordinates,
        coordinate_to_id=dict(mesh.coordinate_to_id),
    )
    return rebuild_mesh_network(interim, delivery_ids)
```

Add import at top of `delivery_mesh.py`:

```python
from traveling_salesman_problem.problem.vrp_models import DEPOT_ID, DeliveryPoint
```

(merge with existing `DeliveryPoint` import if present)

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_delivery_mesh.ManualBlockedNodeTests -v`

Expected: FAIL on `build_delivery_mesh` missing `blocked_count` — fixed in Task 2. If Task 2 done first, PASS.

- [ ] **Step 5: Commit**

```bash
git add traveling_salesman_problem/problem/delivery_mesh.py tests/test_delivery_mesh.py
git commit -m "feat(mesh): add toggle_node_blocked and resolve_node_coordinate"
```

---

### Task 2: Remove random blocked generation from mesh builders

**Files:**
- Modify: `traveling_salesman_problem/problem/delivery_mesh.py`
- Modify: `tests/test_delivery_mesh.py`
- Modify: `tests/test_fitness_mesh_distance.py`
- Modify: `tests/test_delivery_hub_mesh.py`

**Interfaces:**
- Consumes: `toggle_node_blocked` from Task 1
- Produces: `build_delivery_mesh(..., transit_count, rng_seed)` — no `blocked_count`
- Produces: `build_vrp_mesh(..., transit_count, rng_seed)` — no `blocked_count`

- [ ] **Step 1: Update `build_delivery_mesh` signature and body**

Remove parameter `blocked_count` and validation `blocked_count < 1`.

Change `generate_transit_nodes` call from `transit_count + blocked_count` to `transit_count`.

Remove blocked_nodes slice logic; initialize:

```python
blocked_ids: Set[str] = set()
blocked_coordinates: Dict[str, Coordinate] = {}
```

- [ ] **Step 2: Update `build_vrp_mesh` the same way**

Remove `blocked_count` parameter; generate only `current_transit` extras; empty blocked sets.

- [ ] **Step 3: Update all test call sites**

In `tests/test_delivery_mesh.py`, remove `blocked_count=...` from every `build_delivery_mesh` / `build_vrp_mesh` call.

Replace `test_blocked_node_never_on_path`:

```python
def test_blocked_node_never_on_path(self):
    cities = [(0.0, 0.0), (100.0, 0.0)]
    mesh = build_delivery_mesh(
        cities,
        map_bounds=(-20, -20, 120, 120),
        transit_count=4,
        rng_seed=1,
    )
    transit_id = mesh.transit_ids[0]
    mesh = toggle_node_blocked(mesh, transit_id, mesh.delivery_ids)
    path = delivery_segment_path(mesh, cities[0], cities[1])
    self.assertTrue(path)
    for blocked_id in mesh.blocked_ids:
        self.assertNotIn(blocked_id, path)
        self.assertNotIn(blocked_id, mesh.network.nodes)
```

Replace `test_blocked_not_in_network_nodes`:

```python
def test_blocked_not_in_network_nodes(self):
    cities = [(0.0, 0.0), (50.0, 50.0), (100.0, 0.0)]
    mesh = build_delivery_mesh(
        cities,
        map_bounds=(-20, -20, 120, 120),
        transit_count=6,
        rng_seed=3,
    )
    for transit_id in mesh.transit_ids[:2]:
        mesh = toggle_node_blocked(mesh, transit_id, mesh.delivery_ids)
    for blocked_id in mesh.blocked_ids:
        self.assertNotIn(blocked_id, mesh.network.nodes)
```

In `tests/test_fitness_mesh_distance.py` and `tests/test_delivery_hub_mesh.py`, remove `blocked_count=1` from builder calls.

- [ ] **Step 4: Run all mesh tests**

Run: `python -m unittest tests.test_delivery_mesh tests.test_fitness_mesh_distance tests.test_delivery_hub_mesh -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add traveling_salesman_problem/problem/delivery_mesh.py tests/test_delivery_mesh.py tests/test_fitness_mesh_distance.py tests/test_delivery_hub_mesh.py
git commit -m "refactor(mesh): remove random blocked node generation"
```

---

### Task 3: Seed without blocked_count

**Files:**
- Modify: `traveling_salesman_problem/simulation/simulation_state.py`

**Interfaces:**
- Produces:
```python
def _mesh_rng_seed(
    depot: Coordinate,
    deliveries: List[DeliveryPoint],
    transit_count: int,
) -> int: ...
```

- [ ] **Step 1: Update `_mesh_rng_seed`**

Remove `blocked_count` parameter and `parts.extend([transit_count, blocked_count])` → keep only `parts.append(transit_count)`.

- [ ] **Step 2: Update `rebuild_scenario` call site**

Change:

```python
rng_seed=_mesh_rng_seed(
    self.depot,
    self.deliveries,
    transit_count,
),
```

Remove all `blocked_count` variable usage in `rebuild_scenario` for mesh building (full removal in Task 5).

- [ ] **Step 3: Run tests**

Run: `python -m unittest discover tests -v`

Expected: PASS (no behavioral test yet; compile check)

- [ ] **Step 4: Commit**

```bash
git add traveling_salesman_problem/simulation/simulation_state.py
git commit -m "fix(mesh): remove blocked_count from rng seed"
```

---

### Task 4: Map hit-test

**Files:**
- Create: `traveling_salesman_problem/visualization/map_hit_test.py`
- Create: `tests/test_map_hit_test.py`

**Interfaces:**
- Produces:
```python
def hit_test_map_node(
    mesh: Optional[DeliveryMesh],
    depot: Optional[Coordinate],
    deliveries: Sequence[DeliveryPoint],
    screen_pos: Tuple[int, int],
    hit_radius: float,
) -> Optional[str]: ...
```

- [ ] **Step 1: Write failing tests**

```python
# tests/test_map_hit_test.py
import unittest

from traveling_salesman_problem.problem.delivery_mesh import (
    build_delivery_mesh,
    toggle_node_blocked,
)
from traveling_salesman_problem.problem.vrp_models import DEPOT_ID, DeliveryPoint
from traveling_salesman_problem.visualization.map_hit_test import hit_test_map_node


class MapHitTestTests(unittest.TestCase):
    def test_hits_blocked_node_for_unblock(self):
        cities = [(0.0, 0.0), (100.0, 0.0)]
        mesh = build_delivery_mesh(
            cities,
            map_bounds=(-20, -20, 120, 120),
            transit_count=3,
            rng_seed=2,
        )
        transit_id = mesh.transit_ids[0]
        mesh = toggle_node_blocked(mesh, transit_id, mesh.delivery_ids)
        coord = mesh.blocked_coordinates[transit_id]
        hit = hit_test_map_node(mesh, None, [], (int(coord[0]), int(coord[1])), 12.0)
        self.assertEqual(hit, transit_id)

    def test_hits_depot_before_transit(self):
        depot = (50.0, 50.0)
        deliveries = [DeliveryPoint("A", (200.0, 200.0), 5, 3)]
        mesh = build_delivery_mesh(
            [deliveries[0].coordinate],
            map_bounds=(-20, -20, 250, 250),
            transit_count=2,
            rng_seed=4,
        )
        hit = hit_test_map_node(mesh, depot, deliveries, (50, 50), 12.0)
        self.assertEqual(hit, DEPOT_ID)

    def test_returns_none_when_far(self):
        mesh = build_delivery_mesh(
            [(0.0, 0.0)],
            map_bounds=(-20, -20, 120, 120),
            transit_count=2,
            rng_seed=1,
        )
        self.assertIsNone(hit_test_map_node(mesh, None, [], (999, 999), 12.0))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_map_hit_test -v`

Expected: FAIL — module not found

- [ ] **Step 3: Implement `map_hit_test.py`**

```python
"""Hit-test de nós no mapa para bloqueio manual."""

from __future__ import annotations

import math
from typing import List, Optional, Sequence, Tuple

from traveling_salesman_problem.problem.delivery_mesh import DeliveryMesh
from traveling_salesman_problem.problem.road_network import Coordinate
from traveling_salesman_problem.problem.vrp_models import DEPOT_ID, DeliveryPoint

ScreenPos = Tuple[int, int]


def _distance(a: ScreenPos, b: Coordinate) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _nearest_within(
    screen_pos: ScreenPos,
    candidates: Sequence[Tuple[str, Coordinate]],
    hit_radius: float,
) -> Optional[str]:
    best_id: Optional[str] = None
    best_distance = hit_radius
    for node_id, coordinate in candidates:
        distance = _distance(screen_pos, coordinate)
        if distance <= best_distance:
            best_distance = distance
            best_id = node_id
    return best_id


def hit_test_map_node(
    mesh: Optional[DeliveryMesh],
    depot: Optional[Coordinate],
    deliveries: Sequence[DeliveryPoint],
    screen_pos: ScreenPos,
    hit_radius: float,
) -> Optional[str]:
    if mesh is None:
        return None

    blocked_candidates: List[Tuple[str, Coordinate]] = [
        (node_id, coordinate)
        for node_id, coordinate in mesh.blocked_coordinates.items()
    ]
    hit = _nearest_within(screen_pos, blocked_candidates, hit_radius)
    if hit is not None:
        return hit

    if depot is not None:
        hit = _nearest_within(screen_pos, [(DEPOT_ID, depot)], hit_radius)
        if hit is not None:
            return hit

    delivery_candidates = [
        (point.id, point.coordinate) for point in deliveries
    ]
    hit = _nearest_within(screen_pos, delivery_candidates, hit_radius)
    if hit is not None:
        return hit

    transit_candidates = [
        (node_id, mesh.network.nodes[node_id])
        for node_id in mesh.transit_ids
        if node_id in mesh.network.nodes
    ]
    return _nearest_within(screen_pos, transit_candidates, hit_radius)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_map_hit_test -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add traveling_salesman_problem/visualization/map_hit_test.py tests/test_map_hit_test.py
git commit -m "feat(ui): add map node hit-test for manual blocking"
```

---

### Task 5: Simulation state — remove slider, wire toggle

**Files:**
- Modify: `traveling_salesman_problem/simulation/simulation_state.py`

**Interfaces:**
- Consumes: `toggle_node_blocked`, `hit_test_map_node`
- Produces: `SimulationState.toggle_blocked_at(self, screen_pos: Tuple[int, int]) -> bool`

- [ ] **Step 1: Remove blocked slider fields and widget**

Delete:
- `blocked_count_slider: Optional[IntegerSlider]`
- `last_blocked_count: int`
- `blocked_count_slider` creation in `_create_control_widgets`
- `blocked_count_slider.handle_event` in `handle_control_events`
- `blocked_count_slider` from drag guard and `update_controls_if_changed`
- `blocked_count_slider.draw` references (Task 6)

Change transit slider to full width in `_create_control_widgets`:

```python
self.transit_count_slider = IntegerSlider(
    position_x=VisualTheme.control_margin,
    position_y=mesh_y,
    width=controls_width,  # was half_width
    height=settings.count_slider_height,
    value=settings.initial_transit_count,
    minimum_value=1,
    maximum_value=settings.maximum_mesh_nodes_per_type,
    label="Trânsito",
)
```

Remove entire `self.blocked_count_slider = IntegerSlider(...)` block.

- [ ] **Step 2: Update `rebuild_scenario`**

Remove `blocked_count` variable.

Call `build_vrp_mesh` without `blocked_count`.

After mesh build, ensure empty blocked state (builders already return empty).

Add helper to clear blocks explicitly after mesh assign:

```python
self.mesh.blocked_ids = set()
self.mesh.blocked_coordinates = {}
```

(if builders already empty, this is defensive)

- [ ] **Step 3: Add `toggle_blocked_at`**

```python
def toggle_blocked_at(self, screen_pos: tuple[int, int]) -> bool:
    if self.mesh is None or self.depot is None:
        return False
    settings = self.settings
    hit_radius = float(settings.city_node_radius + 6)
    node_id = hit_test_map_node(
        self.mesh,
        self.depot,
        self.deliveries,
        screen_pos,
        hit_radius,
    )
    if node_id is None:
        return False
    delivery_ids = [point.id for point in self.deliveries]
    if node_id == DEPOT_ID:
        delivery_ids_with_depot = [DEPOT_ID, *delivery_ids]
    else:
        delivery_ids_with_depot = delivery_ids
    self.mesh = toggle_node_blocked(
        self.mesh,
        node_id,
        delivery_ids_with_depot,
    )
    return True
```

Import at top:

```python
from traveling_salesman_problem.problem.delivery_mesh import (
    build_vrp_mesh,
    effective_transit_count,
    toggle_node_blocked,
)
from traveling_salesman_problem.visualization.map_hit_test import hit_test_map_node
```

For `toggle_node_blocked`, pass delivery ids that include depot when blocking depot — adjust `rebuild_mesh_network` call to use `[DEPOT_ID, *mesh.delivery_ids]` always:

```python
self.mesh = toggle_node_blocked(
    self.mesh,
    node_id,
    [DEPOT_ID, *self.mesh.delivery_ids],
)
```

- [ ] **Step 4: Verify compile**

Run: `python -c "from traveling_salesman_problem.simulation.simulation_state import SimulationState; print('ok')"`

Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add traveling_salesman_problem/simulation/simulation_state.py
git commit -m "feat(sim): manual block toggle, remove blocked slider"
```

---

### Task 6: Pygame application — map clicks and draw order

**Files:**
- Modify: `traveling_salesman_problem/simulation/pygame_application.py`
- Modify: `traveling_salesman_problem/config/application_settings.py`

**Interfaces:**
- Consumes: `SimulationState.toggle_blocked_at`

- [ ] **Step 1: Remove `initial_blocked_count` from settings**

In `application_settings.py`, delete line:

```python
initial_blocked_count: int = 2
```

- [ ] **Step 2: Remove slider draw**

In `_draw_sidebar_content`, delete:

```python
simulation.blocked_count_slider.draw(content_surface)
```

- [ ] **Step 3: Handle map clicks**

In event loop, before `simulation.handle_control_events`, add map click handler:

```python
elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
    if event.pos[0] >= settings.plot_horizontal_offset:
        if simulation.toggle_blocked_at(event.pos):
            continue
```

Place inside the `elif event.type in (MOUSEBUTTONDOWN, ...)` branch, only when not in sidebar scroll viewport.

- [ ] **Step 4: Remove resize blocked slider restore**

In `VIDEORESIZE` handler, delete `saved_blocked` and `simulation.blocked_count_slider.value = ...`.

- [ ] **Step 5: Fix draw order**

In main draw loop, move `draw_blocked_nodes` **after** `draw_delivery_points` and `draw_depot`:

```python
draw_transit_nodes(screen, simulation.mesh)
if simulation.show_mesh:
    draw_mesh_edges(screen, simulation.mesh)
# ... routes ...
draw_delivery_points(screen, simulation.deliveries, settings.city_node_radius)
draw_depot(screen, simulation.depot)
draw_blocked_nodes(screen, simulation.mesh)
```

- [ ] **Step 6: Manual smoke test**

Run: `python main.py`

Expected:
- No "Bloqueados" slider
- Click transit node → red X appears, node stays in place
- Routes on screen do not jump
- Click again → unblocks

- [ ] **Step 7: Commit**

```bash
git add traveling_salesman_problem/simulation/pygame_application.py traveling_salesman_problem/config/application_settings.py
git commit -m "feat(ui): map click blocking and updated draw order"
```

---

### Task 7: Renderer — stored paths through blocked nodes

**Files:**
- Modify: `traveling_salesman_problem/visualization/map_renderer.py`

**Interfaces:**
- Consumes: `resolve_node_coordinate` from Task 1

- [ ] **Step 1: Update `_trip_polyline_from_stored`**

Add import:

```python
from traveling_salesman_problem.problem.delivery_mesh import (
    DeliveryMesh,
    delivery_segment_path,
    resolve_node_coordinate,
)
```

Replace coordinate lookup in `path_node_ids` branch:

```python
def _trip_polyline_from_stored(
    mesh: DeliveryMesh,
    trip: Trip,
) -> List[CityCoordinate]:
    if not trip.path_node_ids:
        coordinates = [stop.coordinate for stop in trip.stops]
        return _trip_polyline(mesh, coordinates)
    points: List[CityCoordinate] = []
    for path in trip.path_node_ids:
        path_coords = [resolve_node_coordinate(mesh, node_id) for node_id in path]
        if points and path_coords:
            path_coords = path_coords[1:]
        points.extend(path_coords)
    return points
```

- [ ] **Step 2: Add regression test**

Add to `tests/test_delivery_mesh.py`:

```python
def test_stored_path_resolves_blocked_transit_coordinate(self):
    cities = [(0.0, 0.0), (100.0, 0.0)]
    mesh = build_delivery_mesh(
        cities,
        map_bounds=(-20, -20, 120, 120),
        transit_count=4,
        rng_seed=1,
    )
    path = delivery_segment_path(mesh, cities[0], cities[1])
    self.assertTrue(path)
    transit_in_path = next(node for node in path if node.startswith("T"))
    original = mesh.network.nodes[transit_in_path]
    blocked = toggle_node_blocked(mesh, transit_in_path, mesh.delivery_ids)
    resolved = resolve_node_coordinate(blocked, transit_in_path)
    self.assertEqual(resolved, original)
```

- [ ] **Step 3: Run tests**

Run: `python -m unittest tests.test_delivery_mesh.ManualBlockedNodeTests.test_stored_path_resolves_blocked_transit_coordinate -v`

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add traveling_salesman_problem/visualization/map_renderer.py tests/test_delivery_mesh.py
git commit -m "fix(render): resolve stored paths through blocked nodes"
```

---

### Task 8: Full regression

**Files:** (none — verification only)

- [ ] **Step 1: Run full test suite**

Run: `python -m unittest discover tests -v`

Expected: all PASS

- [ ] **Step 2: Manual acceptance checklist**

Run: `python main.py`

Verify:
1. Click block/unblock does not move any point
2. Existing route polylines unchanged immediately after toggle
3. After several generations, routes may use newly unblocked nodes
4. "Sortear posições" clears all blocks
5. Transit slider still rebuilds mesh (clears blocks)

- [ ] **Step 3: Commit if any fixups needed**

```bash
git add -A
git commit -m "test: manual blocked nodes regression fixes"
```

---

## Self-review

| Spec requirement | Task |
|------------------|------|
| Click toggle any node | Task 4, 5, 6 |
| Remove slider | Task 5, 6 |
| Incremental mesh update | Task 1, 5 |
| Stored routes unchanged | Task 7 |
| Seed without blocked_count | Task 3 |
| No random blocked generation | Task 2 |
| Clear blocks on rebuild | Task 5 |
| Draw order overlay last | Task 6 |
| Unit tests | Tasks 1, 4, 7, 8 |

No placeholders found. Type names consistent across tasks.
