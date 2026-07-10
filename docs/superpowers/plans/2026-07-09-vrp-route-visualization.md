# VRP Route Visualization Clarity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make depot departures/returns visually obvious via route panel text, arrows, larger depot, vehicle filter, distinct trip styles, focused-vehicle animation, and mesh toggle — without changing VRP algorithm logic.

**Architecture:** Pure presentation layer on top of existing `DecodedVehiclePlan` / `best_plan`. Add pure helpers for formatting and animation polylines (unit-tested); wire filter/mesh/animation state in `SimulationState`; enrich `map_renderer` and sidebar in `pygame_application`.

**Tech Stack:** Python, Pygame, unittest.

## Global Constraints

- Branch: `feature/road-network-blocked-nodes`
- **Do not create git commits** unless the user explicitly asks
- Do **not** modify `vrp_decoder`, assignment, or GA fitness logic
- Animation only when `focus_vehicle_id is not None`
- Spec: `docs/superpowers/specs/2026-07-09-vrp-route-visualization-design.md`

---

## File map

| File | Responsibility |
|------|----------------|
| Create: `traveling_salesman_problem/visualization/route_panel.py` | Format trip/vehicle panel lines; filter plans by focus |
| Create: `traveling_salesman_problem/visualization/route_animation.py` | Build animation polyline from plan; sample point at progress |
| Modify: `traveling_salesman_problem/visualization/map_renderer.py` | Bigger depot; dashed later trips; arrows; anim cursor; mesh flags |
| Modify: `traveling_salesman_problem/visualization/application_layout.py` | Draw structured route panel (or call `route_panel`) |
| Modify: `traveling_salesman_problem/config/visual_theme.py` | Depot size, arrow colors |
| Modify: `traveling_salesman_problem/simulation/simulation_state.py` | `focus_vehicle_id`, `show_mesh`, cycle-focus helper |
| Modify: `traveling_salesman_problem/simulation/pygame_application.py` | Controls + animation `t` + draw order |
| Test: `tests/test_route_panel.py` | |
| Test: `tests/test_route_animation.py` | |

---

### Task 1: Route panel formatter + plan filter

**Files:**
- Create: `traveling_salesman_problem/visualization/route_panel.py`
- Test: `tests/test_route_panel.py`

**Interfaces:**
```python
def format_trip_line(trip: Trip, trip_index: int, capacity: int) -> str
# "Viagem 1: D → A → C → D  (9/10)"
# Delivery stops use stop.node_id; depot stops render as "D"
# load = sum(stop.quantity for delivery stops)

def format_vehicle_section(vehicle_id: int, plan: DecodedVehiclePlan, capacity: int) -> List[str]
# ["Veículo 1", "  Viagem 1: ...", ...]

def filter_plans_by_focus(
    plans: Dict[int, DecodedVehiclePlan],
    focus_vehicle_id: Optional[int],
) -> Dict[int, DecodedVehiclePlan]
# None → all; else only that id if present
```

- [x] **Step 1: Write failing tests** covering D…D, load fraction, filter
- [x] **Step 2:** `python -m unittest tests.test_route_panel -v` → FAIL
- [x] **Step 3: Implement**
- [x] **Step 4:** PASS
- [x] **Step 5: Do not commit**

---

### Task 2: Animation polyline helpers

**Files:**
- Create: `traveling_salesman_problem/visualization/route_animation.py`
- Test: `tests/test_route_animation.py`

**Interfaces:**
```python
def build_animation_polyline(
    mesh: DeliveryMesh,
    plan: DecodedVehiclePlan,
) -> List[Coordinate]
# Concatenate mesh-expanded segments for each trip in order;
# first and last coordinates must equal depot (trip.stops[0] / [-1])

def point_along_polyline(
    points: List[Coordinate],
    progress: float,  # 0..1, wraps with progress % 1
) -> Coordinate
```

Use hand-built mesh + tiny `DecodedVehiclePlan` in tests (reuse patterns from `tests/test_vrp_decoder.py`).

- [x] TDD → implement → PASS → **Do not commit**

---

### Task 3: Map renderer — depot, trips, arrows, cursor, flags

**Files:**
- Modify: `map_renderer.py`
- Modify: `visual_theme.py` (`depot_marker_size: int = 18`, keep colors)

**Changes:**
1. `draw_depot(..., size=None)` — larger default; optional caption “Depósito” below marker.
2. `draw_vehicle_plans(..., focus_vehicle_id=None, dim_others=True)`:
   - If focus set: full opacity for focus; skip or draw others at ~25% alpha.
   - Trip 0: solid width 3; trip≥1: dashed (draw short segments) or alpha 0.55 width 2.
3. `draw_polyline_arrows(screen, points, color, emphasize_indices=None)` — arrows along polyline; emphasize last segment into depot.
4. `draw_animation_cursor(screen, point, color)` — filled circle with stroke.
5. `draw_mesh_edges` / `draw_transit_nodes` already exist — callers pass `show_mesh`.

Keep existing function names used by app; extend signatures with defaults so old tests don’t break.

- [x] Implement + smoke-import
- [x] **Do not commit**

---

### Task 4: SimulationState focus + mesh toggle

**Files:**
- Modify: `simulation_state.py`
- Modify: widgets usage in `_create_control_widgets`

**Add:**
```python
focus_vehicle_id: Optional[int] = None  # None = Todos
show_mesh: bool = True
mesh_toggle: Optional[ToggleButton] = None
# Vehicle focus: ActionButton "Filtro: Todos" that cycles None → 0 → 1 → … → None
# OR discrete buttons if space allows — prefer one cycling ActionButton for YAGNI
```

```python
def cycle_focus_vehicle(self) -> None:
    ids = sorted(self.vehicle_states.keys())
    if not ids:
        self.focus_vehicle_id = None
        return
    if self.focus_vehicle_id is None:
        self.focus_vehicle_id = ids[0]
    else:
        try:
            index = ids.index(self.focus_vehicle_id)
        except ValueError:
            self.focus_vehicle_id = ids[0]
            return
        if index + 1 >= len(ids):
            self.focus_vehicle_id = None
        else:
            self.focus_vehicle_id = ids[index + 1]
```

Update button label when cycling: `Filtro: Todos` / `Filtro: V1` / …

On `rebuild_scenario` / `shuffle_all`: if focus id no longer exists → `None`; animation reset handled in app.

Wire `mesh_toggle` → `show_mesh = mesh_toggle.is_active` each frame or on event.

- [x] Implement
- [x] **Do not commit**

---

### Task 5: Pygame loop — panel, controls, animation

**Files:**
- Modify: `pygame_application.py`
- Modify: `application_layout.py` if needed for drawing multi-line panel

**Replace** `_visit_order_rows` + old delivery order panel with `route_panel` output:

```python
lines = []
visible = filter_plans_by_focus(plans, simulation.focus_vehicle_id)
for vid, plan in sorted(visible.items()):
    lines.extend(format_vehicle_section(vid, plan, capacity))
# draw lines in sidebar (new draw_route_text_panel helper)
```

**Each frame:**
1. `simulation.update_controls_if_changed()` (include focus button + mesh toggle)
2. Run generation as today
3. If `focus_vehicle_id is not None` and plan exists:
   - `polyline = build_animation_polyline(mesh, plan)`
   - advance `animation_progress` by `speed * dt` (use `clock.get_time()` ms); wrap 0..1
   - reset progress when focus id changes (track `last_focus`)
4. Draw order:
   - chrome/header/chart/sidebar
   - if `show_mesh`: edges + transit
   - blocked + deliveries
   - `draw_vehicle_plans(..., focus=...)`
   - arrows for visible plans (or only focused)
   - depot on top
   - if animating: cursor at `point_along_polyline`

**Caption:** window title can stay; footer hint: `Filtro cicla veículos · Malha on/off`.

- [x] Manual checklist from spec §5–6
- [x] **Do not commit**

---

### Task 6: Regression

```bash
python -m unittest tests.test_route_panel tests.test_route_animation tests.test_vrp_decoder tests.test_vehicle_genetic tests.test_vrp_assignment -v
```

- [x] Fix any import/signature breakages
- [x] Confirm decoder tests still pass unchanged
- [x] **Do not commit**

---

## Spec coverage

| Spec item | Task |
|-----------|------|
| Panel D→…→D + load | 1, 5 |
| Arrows / return emphasis | 3, 5 |
| Larger depot | 3 |
| Vehicle filter | 4, 5 |
| Distinct trip styles | 3 |
| Focus-only animation | 2, 5 |
| Mesh toggle | 4, 5 |
| No algorithm changes / no commits | all |
