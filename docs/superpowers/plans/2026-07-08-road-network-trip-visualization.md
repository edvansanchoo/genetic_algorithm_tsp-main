# Road Network & Trip Visualization — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the greedy delivery simulator so vehicles move only on a radius-based road graph (with mandatory transit nodes), and add an interactive vehicle/trip selector for focused map visualization.

**Architecture:** New `road_network.py` module (graph build + BFS pathfinding). `routing.py` uses graph distance and expands full paths into `Trip.stops`. UI adds transit/radius sliders and `TripSelector` widget for filtered route rendering.

**Tech Stack:** Python 3.9+, Pygame, stdlib `unittest`. Builds on branch `feat/greedy-delivery-simulation`.

## Global Constraints

- Graph edges: connect node pairs where euclidean distance ≤ **connection radius** (slider 80–250 px, default 150)
- Transit nodes: **3–15** (default 8), randomly placed on shuffle
- Pathfinding: **BFS** simple path; no repeated nodes per trip; DEPOT only at trip start/end
- Delivery algorithm: **greedy global** unchanged in logic; distance metric = graph path length
- All user-facing strings in **Portuguese**
- Spec: `docs/superpowers/specs/2026-07-08-road-network-trip-visualization-design.md`
- Pygame integration: manual validation only

---

## File Map

| File | Action |
|------|--------|
| `delivery_simulation/models.py` | Modify — TransitNode, RoadNetwork, Stop.is_transit, SimulationResult fields |
| `delivery_simulation/road_network.py` | Create — graph + BFS + connectivity |
| `delivery_simulation/routing.py` | Modify — graph-aware movement |
| `delivery_simulation/assignment.py` | Modify — pass RoadNetwork |
| `delivery_simulation/reporter.py` | Modify — transit in output |
| `delivery_simulation/__init__.py` | Modify — exports |
| `tests/test_road_network.py` | Create |
| `tests/test_routing_graph.py` | Create |
| `tests/test_connectivity.py` | Create |
| `traveling_salesman_problem/config/application_settings.py` | Modify — slider defaults |
| `traveling_salesman_problem/simulation/simulation_state.py` | Modify — network state, sliders, trip selector |
| `traveling_salesman_problem/visualization/widgets/trip_selector.py` | Create |
| `traveling_salesman_problem/visualization/map_renderer.py` | Modify — graph, transit, styled routes |
| `traveling_salesman_problem/visualization/application_layout.py` | Modify — trip detail panel |
| `traveling_salesman_problem/simulation/pygame_application.py` | Modify — wiring |

---

### Task 1: Extend domain models

**Files:**
- Modify: `delivery_simulation/models.py`
- Modify: `tests/test_routing.py` (fix Stop construction if needed)

**Interfaces:**
- Produces: `TransitNode`, `RoadNetwork`, `Stop.is_transit`, `SimulationResult.road_network`, `SimulationResult.transit_nodes`

- [ ] **Step 1: Add new dataclasses and extend Stop**

```python
@dataclass
class TransitNode:
    id: str
    coordinate: Coordinate

@dataclass
class RoadNetwork:
    nodes: dict[str, Coordinate]
    edges: list[tuple[str, str]]
    connection_radius: float

@dataclass
class Stop:
    point_id: str
    items_delivered: int
    is_transit: bool = False
```

Add to `SimulationResult`:
```python
road_network: RoadNetwork
transit_nodes: List[TransitNode]
```

- [ ] **Step 2: Run existing tests — expect failures where SimulationResult construction changed**

Run: `python -m unittest discover tests -v`

- [ ] **Step 3: Commit**

```bash
git add delivery_simulation/models.py
git commit -m "feat: add road network and transit node models"
```

---

### Task 2: Road network module

**Files:**
- Create: `delivery_simulation/road_network.py`
- Create: `tests/test_road_network.py`

**Interfaces:**
- Produces:
  - `generate_transit_nodes(count, map_min_x, map_min_y, map_max_x, map_max_y, min_separation=30.0, rng=None) -> list[TransitNode]`
  - `build_radius_graph(nodes: dict[str, Coordinate], radius: float) -> list[tuple[str, str]]`
  - `build_road_network(nodes, radius) -> RoadNetwork`
  - `find_path(network, origin, dest, blocked: set[str]) -> list[str]`
  - `path_distance(network, path) -> float`
  - `is_reachable(network, origin, dest, blocked=frozenset()) -> bool`
  - `ensure_connectivity(network, depot_id, required_ids) -> bool`
  - `connect_nearest_neighbor(network, node_id) -> RoadNetwork` (fallback)

- [ ] **Step 1: Write failing tests**

```python
# test_road_network.py key cases:
# - build_radius_graph connects only pairs within radius
# - find_path D->A through transit T1 when direct edge missing
# - find_path respects blocked nodes (cannot revisit T1)
# - find_path allows DEPOT as dest even if DEPOT in blocked (unless origin==DEPOT)
# - path_distance sums segment lengths
```

- [ ] **Step 2: Implement road_network.py**

BFS adjacency from edges (bidirectional). `find_path`:
- Queue: `(node_id, path_list)`
- Skip neighbors in `blocked` except when `neighbor == dest == DEPOT`
- Return first path reaching dest with minimum edges; tie-break by `path_distance`

`generate_transit_nodes`: ids `T1`, `T2`, …; same min-separation logic as point_generator.

- [ ] **Step 3: Run tests**

Run: `python -m unittest tests.test_road_network -v`  
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add delivery_simulation/road_network.py tests/test_road_network.py
git commit -m "feat: add radius graph builder and BFS pathfinding"
```

---

### Task 3: Connectivity validation and shuffle integration

**Files:**
- Create: `tests/test_connectivity.py`
- Modify: `traveling_salesman_problem/simulation/simulation_state.py` (partial — shuffle only)

**Interfaces:**
- Consumes: `generate_depot_and_points`, `generate_transit_nodes`, `build_road_network`, `ensure_connectivity`
- Produces: `SimulationState.road_network`, `SimulationState.transit_nodes`

- [ ] **Step 1: Write failing connectivity test**

```python
def test_shuffle_retries_until_connected():
    # With enough transit nodes and radius, shuffle_positions sets road_network
    # where depot reaches all delivery ids
```

- [ ] **Step 2: Update shuffle_positions in simulation_state.py**

After generating depot + delivery points:
1. Loop up to 50 times: generate transit nodes, build network
2. If `ensure_connectivity(network, DEPOT_ID, delivery_ids)`: break
3. Else retry
4. If still failing: apply `connect_nearest_neighbor` for each unreachable delivery; set `status_message` warning

Store `self.road_network`, `self.transit_nodes`.

- [ ] **Step 3: Run tests**

Run: `python -m unittest tests.test_connectivity -v`

- [ ] **Step 4: Commit**

```bash
git add tests/test_connectivity.py traveling_salesman_problem/simulation/simulation_state.py
git commit -m "feat: generate connected road network on shuffle"
```

---

### Task 4: Graph-integrated routing

**Files:**
- Modify: `delivery_simulation/routing.py`
- Modify: `delivery_simulation/assignment.py`
- Create: `tests/test_routing_graph.py`
- Modify: `tests/test_routing.py` (update for RoadNetwork param)

**Interfaces:**
- Consumes: `RoadNetwork`, `find_path`, `path_distance`
- Produces: `run_greedy_simulation(config, depot, delivery_points, road_network, transit_nodes) -> SimulationResult`

- [ ] **Step 1: Write failing tests**

```python
def test_movement_expands_transit_stops():
    # Graph: DEPOT-T1-A, vehicle goes DEPOT->A, stops include T1 with is_transit=True

def test_trip_has_no_repeated_nodes():
    # All stop point_ids (except DEPOT at start/end only) unique within trip

def test_greedy_uses_graph_distance_not_euclidean():
    # Layout where euclidean DEPOT->A < DEPOT->T1->A but graph requires T1
```

- [ ] **Step 2: Refactor routing.py**

Key changes:
- Track `vehicle.current_node_id: str` (not just coordinate)
- `visited_in_trip: set[str]` per active trip
- `_move_vehicle_along_path(vehicle, active_trip, path, delivery_amount_at_dest)`:
  - For each node in path[1:]: append Stop; add to visited; update position
- Candidate distance: `path_distance(find_path(...))` — empty path → skip candidate
- Depot return: expand full graph path to DEPOT
- Include `road_network` and `transit_nodes` in `SimulationResult`

Helper `_is_transit(node_id) -> bool`: starts with `T`

- [ ] **Step 3: Update assignment.py**

```python
def run_simulation(config, depot, delivery_points, road_network, transit_nodes):
    return run_greedy_simulation(config, depot, delivery_points, road_network, transit_nodes)
```

- [ ] **Step 4: Run all routing tests**

Run: `python -m unittest tests.test_routing tests.test_routing_multi_vehicle tests.test_routing_graph -v`

- [ ] **Step 5: Commit**

```bash
git add delivery_simulation/routing.py delivery_simulation/assignment.py tests/
git commit -m "feat: integrate graph pathfinding into greedy routing"
```

---

### Task 5: Reporter transit formatting

**Files:**
- Modify: `delivery_simulation/reporter.py`

- [ ] **Step 1: Update _format_stop_chain**

```python
if stop.is_transit or (stop.point_id.startswith("T") and stop.items_delivered == 0):
    parts.append(stop.point_id)  # T3 without parens
elif stop.point_id == DEPOT_ID:
    parts.append("D")
else:
    parts.append(f"{stop.point_id}({stop.items_delivered})")
```

Add transit summary line per trip in vehicle section.

- [ ] **Step 2: Commit**

```bash
git add delivery_simulation/reporter.py
git commit -m "feat: show transit nodes in simulation report"
```

---

### Task 6: Config sliders (transit count + radius)

**Files:**
- Modify: `traveling_salesman_problem/config/application_settings.py`
- Modify: `traveling_salesman_problem/simulation/simulation_state.py`

- [ ] **Step 1: Add settings**

```python
initial_transit_node_count: int = 8
initial_connection_radius: int = 150
minimum_connection_radius: int = 80
maximum_connection_radius: int = 250
minimum_transit_nodes: int = 3
maximum_transit_nodes: int = 15
```

- [ ] **Step 2: Add sliders in _create_control_widgets**

- `transit_count_slider`: IntegerSlider 3–15
- `connection_radius_slider`: IntegerSlider 80–250

Changing either clears simulation result and sets `positions_ready = False`.

- [ ] **Step 3: Wire run_delivery_simulation to pass road_network**

- [ ] **Step 4: Commit**

```bash
git add traveling_salesman_problem/config/application_settings.py traveling_salesman_problem/simulation/simulation_state.py
git commit -m "feat: add transit count and connection radius sliders"
```

---

### Task 7: Map rendering — graph, transit, styled routes

**Files:**
- Modify: `traveling_salesman_problem/visualization/map_renderer.py`
- Modify: `traveling_salesman_problem/config/visual_theme.py`

- [ ] **Step 1: Add visual constants**

```python
graph_edge_color = (120, 130, 140)
transit_fill = (150, 150, 150)
vehicle_line_styles = ("solid", "dashed", "dotted")  # per vehicle index
```

- [ ] **Step 2: Add draw functions**

- `draw_road_network(screen, network)` — edges 1px gray
- `draw_transit_nodes(screen, transit_nodes)` — small gray circles + labels
- `_draw_styled_route(screen, coordinates, color, style, width, alpha=255)` — solid/dashed/dotted
- Update `_coordinate_for_stop` to resolve transit node coords from `road_network.nodes`

- [ ] **Step 3: Add filtered route drawing**

```python
def draw_selected_routes(
    screen, simulation_result, vehicle_id, trip_index, view_mode, base_colors, line_styles
):
    # view_mode "single": only vehicles[v].trips[t]
    # view_mode "all": all trips for vehicle v with decreasing alpha
```

- [ ] **Step 4: Commit**

```bash
git add traveling_salesman_problem/visualization/map_renderer.py traveling_salesman_problem/config/visual_theme.py
git commit -m "feat: render road graph, transit nodes, and styled routes"
```

---

### Task 8: TripSelector widget

**Files:**
- Create: `traveling_salesman_problem/visualization/widgets/trip_selector.py`
- Modify: `traveling_salesman_problem/visualization/widgets/__init__.py`

**Interfaces:**
- Produces:
  ```python
  class TripSelector:
      active_vehicle_id: int
      active_trip_index: int  # 0-based; -1 = all trips
      view_mode: str          # "single" | "all"
      def set_vehicle_trip_counts(counts: dict[int, int]) -> None
      def handle_event(event) -> None
      def draw(screen) -> None
  ```

- [ ] **Step 1: Implement widget**

- Row of vehicle toggle buttons (1..vehicle_count from state)
- Row of trip buttons (1..N) + "Todos"
- Mode toggles: "Uma viagem" / "Todas"
- Disabled/greyed when no simulation_result
- `was_changed: bool` flag for state sync

- [ ] **Step 2: Integrate in simulation_state.py**

Fields: `trip_selector`, reset on simulate to vehicle 1 trip 1.

- [ ] **Step 3: Commit**

```bash
git add traveling_salesman_problem/visualization/widgets/
git commit -m "feat: add interactive trip selector widget"
```

---

### Task 9: UI layout and pygame wiring

**Files:**
- Modify: `traveling_salesman_problem/visualization/application_layout.py`
- Modify: `traveling_salesman_problem/simulation/pygame_application.py`

- [ ] **Step 1: Add draw_trip_detail_panel**

Shows active vehicle/trip chain, distance, load, transit list (from simulation_result).

- [ ] **Step 2: Update pygame_application.py**

Draw order on map:
1. Road network edges
2. Transit nodes
3. Depot + delivery points
4. Selected route(s) via `draw_selected_routes`

Sidebar scroll sections:
- Config (existing + new sliders)
- Ações
- Visualização (TripSelector — only if simulation_result)
- Resultado

- [ ] **Step 3: Manual smoke test**

Run: `python main.py`

Checklist:
1. Sortear → gray edges + transit nodes visible
2. Simular → routes follow graph (through transit nodes)
3. Trip selector filters map to one trip
4. "Todas" shows all trips for vehicle with different opacity
5. Sidebar shows transit in route chain

- [ ] **Step 4: Run full test suite**

Run: `python -m unittest discover tests -v`  
Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add traveling_salesman_problem/visualization/application_layout.py traveling_salesman_problem/simulation/pygame_application.py
git commit -m "feat: wire trip selector and graph visualization in pygame UI"
```

---

## Spec Coverage Checklist

| Spec requirement | Task |
|------------------|------|
| Radius graph | Task 2 |
| Transit nodes on shuffle | Task 3 |
| BFS mandatory transit | Task 4 |
| No repeat per trip | Task 4 |
| Sliders transit + radius | Task 6 |
| Graph edges on map | Task 7 |
| Trip selector interactive | Task 8 |
| Vehicle line styles | Task 7 |
| Reporter transit | Task 5 |
| Connectivity fallback | Task 3 |

## Self-Review Notes

- All tasks have concrete file paths and test commands.
- `find_path` DEPOT blocking rules documented in Task 2 implementation.
- Existing greedy tests updated in Task 4 for new `run_greedy_simulation` signature.

---

**Plan saved to `docs/superpowers/plans/2026-07-08-road-network-trip-visualization.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — fresh subagent per task, review between tasks

**2. Inline Execution** — implement in this session on `feat/greedy-delivery-simulation`

**Which approach?**
