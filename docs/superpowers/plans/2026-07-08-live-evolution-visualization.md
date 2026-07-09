# Live Evolution Visualization — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show continuous AG evolution like TSP main — best + second-best routes for selected vehicle on map, throttled generations (~3/s), and highlighted convergence chart line per vehicle.

**Architecture:** Extend `VehicleGeneticState` with second-best solution from sorted population; add time-based generation throttle in Pygame loop; draw dual routes on map for active vehicle only; extend convergence chart with highlight opacity/linewidth for selected vehicle.

**Tech Stack:** Python 3.9+, Pygame, matplotlib (Agg), stdlib `unittest`. Reuse existing `vehicle_genetic`, `map_renderer`, `convergence_chart`.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-07-08-live-evolution-visualization-design.md`
- Map: **best + 2nd best** of **selected vehicle** only (all trips each)
- Throttle: **`generations_per_second = 3.0`** (clamp 2.0–5.0 in settings)
- Chart: all vehicle lines; **highlight** selected vehicle (`highlight_index` 0-based)
- Flow: **Sortear** + **Simular** unchanged
- Test runner: `python -m unittest discover tests -v`
- UI language: Portuguese
- Pygame manual smoke: out of scope for automated tests

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `delivery_simulation/vehicle_genetic.py` | Modify | Track `second_best_*` |
| `tests/test_vehicle_genetic.py` | Modify | Tests for 2nd best |
| `traveling_salesman_problem/config/application_settings.py` | Modify | `generations_per_second` |
| `traveling_salesman_problem/simulation/simulation_state.py` | Modify | Expose active vehicle best/2nd; generation counter |
| `traveling_salesman_problem/visualization/map_renderer.py` | Modify | `draw_vehicle_evolution_routes()` |
| `traveling_salesman_problem/visualization/convergence_chart.py` | Modify | `highlight_index` styling |
| `tests/test_convergence_chart.py` | Modify | Highlight smoke test |
| `tests/test_evolution_throttle.py` | Create | Throttle unit test |
| `traveling_salesman_problem/visualization/application_layout.py` | Modify | Map header gen + distances |
| `traveling_salesman_problem/simulation/pygame_application.py` | Modify | Throttle loop + new drawing |

---

### Task 1: Second-best tracking in vehicle genetic

**Files:**
- Modify: `delivery_simulation/vehicle_genetic.py`
- Modify: `tests/test_vehicle_genetic.py`

**Interfaces:**
- Consumes: `evaluate_permutation`, `sort_population_by_fitness`
- Produces:
  - `VehicleGeneticState.second_best_distance: float`
  - `VehicleGeneticState.second_best_permutation: TaskPermutation`
  - `VehicleGeneticState.second_best_trips: list[Trip]`
  - `_evaluate_population` returns `(fitness, best_perm, best_dist, best_trips, second_perm, second_dist, second_trips)`

- [ ] **Step 1: Write failing test**

Append to `tests/test_vehicle_genetic.py`:

```python
    def test_tracks_second_best_distinct_from_best(self):
        network = build_road_network(
            {DEPOT_ID: (0.0, 0.0), "A": (3.0, 0.0), "B": (0.0, 4.0), "C": (4.0, 4.0)},
            radius=100.0,
        )
        tasks = [
            DeliveryTask("A", 2),
            DeliveryTask("B", 2),
            DeliveryTask("C", 2),
        ]
        state = initialize_vehicle_genetic(1, tasks, network, population_size=30, rng=random.Random(7))

        self.assertLess(state.best_distance, float("inf"))
        self.assertLess(state.second_best_distance, float("inf"))
        self.assertGreaterEqual(state.second_best_distance, state.best_distance)
        self.assertNotEqual(state.best_permutation, state.second_best_permutation)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_vehicle_genetic.VehicleGeneticTests.test_tracks_second_best_distinct_from_best -v`  
Expected: FAIL — `VehicleGeneticState` has no `second_best_distance`

- [ ] **Step 3: Implement second-best**

In `vehicle_genetic.py`, extend dataclass:

```python
@dataclass
class VehicleGeneticState:
    vehicle_id: int
    tasks: List[DeliveryTask]
    population: TaskPopulation = field(default_factory=list)
    best_distance: float = field(default_factory=lambda: float("inf"))
    best_permutation: TaskPermutation = field(default_factory=list)
    best_trips: List[Trip] = field(default_factory=list)
    second_best_distance: float = field(default_factory=lambda: float("inf"))
    second_best_permutation: TaskPermutation = field(default_factory=list)
    second_best_trips: List[Trip] = field(default_factory=list)
```

Replace `_evaluate_population` to track top-2 finite distances:

```python
def _evaluate_population(
    tasks: List[DeliveryTask],
    population: TaskPopulation,
    road_network: RoadNetwork,
) -> tuple[list[float], TaskPermutation, float, List[Trip], TaskPermutation, float, List[Trip]]:
    fitness_values: list[float] = []
    ranked: list[tuple[float, TaskPermutation, List[Trip]]] = []

    for permutation in population:
        distance, trips = evaluate_permutation(tasks, permutation, road_network)
        fitness_values.append(distance if distance != float("inf") else float("inf"))
        if distance != float("inf"):
            ranked.append((distance, list(permutation), trips))

    ranked.sort(key=lambda item: item[0])
    if not ranked:
        empty: TaskPermutation = []
        return fitness_values, empty, float("inf"), [], empty, float("inf"), []

    best_perm, best_dist, best_trips = ranked[0][1], ranked[0][0], ranked[0][2]
    if len(ranked) > 1:
        second_dist, second_perm, second_trips = ranked[1][0], ranked[1][1], ranked[1][2]
    else:
        second_dist, second_perm, second_trips = float("inf"), [], []

    return fitness_values, best_perm, best_dist, best_trips, second_perm, second_dist, second_trips
```

Update `initialize_vehicle_genetic` and `run_vehicle_generation` to unpack and assign `second_best_*`. In `run_vehicle_generation`, update `second_best_*` when `second_dist < state.second_best_distance` OR each generation refresh from current population top-2:

```python
    (
        fitness_values,
        best_permutation,
        best_distance,
        best_trips,
        second_permutation,
        second_best_distance,
        second_best_trips,
    ) = _evaluate_population(state.tasks, state.population, road_network)

    if best_distance < state.best_distance:
        state.best_distance = best_distance
        state.best_permutation = best_permutation
        state.best_trips = best_trips

    if second_best_distance < float("inf"):
        state.second_best_distance = second_best_distance
        state.second_best_permutation = second_permutation
        state.second_best_trips = second_best_trips
```

Also set second_best in `initialize_vehicle_genetic` return.

- [ ] **Step 4: Run tests**

Run: `python -m unittest tests.test_vehicle_genetic -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delivery_simulation/vehicle_genetic.py tests/test_vehicle_genetic.py
git commit -m "feat: track second-best route per vehicle in GA"
```

---

### Task 2: Generation throttle

**Files:**
- Modify: `traveling_salesman_problem/config/application_settings.py`
- Modify: `traveling_salesman_problem/simulation/pygame_application.py`
- Create: `tests/test_evolution_throttle.py`

**Interfaces:**
- Consumes: `ApplicationSettings.generations_per_second`
- Produces:
  - `compute_generations_for_frame(delta_seconds: float, gps: float, accumulated: float) -> tuple[int, float]`

- [ ] **Step 1: Write failing test**

Create `tests/test_evolution_throttle.py`:

```python
import unittest

from traveling_salesman_problem.simulation.evolution_throttle import compute_generations_for_frame


class EvolutionThrottleTests(unittest.TestCase):
    def test_three_per_second_over_one_second(self):
        count, remaining = compute_generations_for_frame(1.0, 3.0, 0.0)
        self.assertEqual(count, 3)
        self.assertAlmostEqual(remaining, 0.0)

    def test_accumulates_partial_frames(self):
        count, remaining = compute_generations_for_frame(0.1, 3.0, 0.0)
        self.assertEqual(count, 0)
        self.assertAlmostEqual(remaining, 0.1)

        count, remaining = compute_generations_for_frame(0.1, 3.0, remaining)
        self.assertEqual(count, 0)
        self.assertAlmostEqual(remaining, 0.2)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_evolution_throttle -v`  
Expected: FAIL — module not found

- [ ] **Step 3: Implement throttle helper**

Create `traveling_salesman_problem/simulation/evolution_throttle.py`:

```python
def compute_generations_for_frame(
    delta_seconds: float,
    generations_per_second: float,
    accumulated_seconds: float,
) -> tuple[int, float]:
    clamped_gps = max(2.0, min(5.0, generations_per_second))
    accumulated_seconds += max(0.0, delta_seconds)
    interval = 1.0 / clamped_gps
    count = 0
    while accumulated_seconds >= interval:
        count += 1
        accumulated_seconds -= interval
    return count, accumulated_seconds
```

Add to `application_settings.py`:

```python
generations_per_second: float = 3.0
```

In `pygame_application.py`:

```python
from traveling_salesman_problem.simulation.evolution_throttle import compute_generations_for_frame

accumulated_evolution_time = 0.0
# in loop, replace single run_one_generation:
delta = clock.get_time() / 1000.0
if simulation.is_evolution_running:
    gen_count, accumulated_evolution_time = compute_generations_for_frame(
        delta,
        settings.generations_per_second,
        accumulated_evolution_time,
    )
    for _ in range(gen_count):
        simulation.run_one_generation()
else:
    clock.get_time()  # still consume tick when not evolving
```

Reset `accumulated_evolution_time = 0.0` when simulation resets (on Sortear via new SimulationState is automatic).

- [ ] **Step 4: Run tests**

Run: `python -m unittest tests.test_evolution_throttle -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add traveling_salesman_problem/simulation/evolution_throttle.py traveling_salesman_problem/config/application_settings.py traveling_salesman_problem/simulation/pygame_application.py tests/test_evolution_throttle.py
git commit -m "feat: throttle AG generations to ~3 per second"
```

---

### Task 3: Map — best + second-best routes

**Files:**
- Modify: `traveling_salesman_problem/visualization/map_renderer.py`
- Modify: `traveling_salesman_problem/simulation/simulation_state.py`

**Interfaces:**
- Consumes: `VehicleGeneticState.best_trips`, `second_best_trips`, `RoadNetwork`
- Produces:
  - `draw_vehicle_evolution_routes(screen, road_network, best_trips, second_best_trips, color, line_styles) -> None`
  - `SimulationState.active_vehicle_genetic_state() -> VehicleGeneticState | None`

- [ ] **Step 1: Add accessor in simulation_state**

```python
def active_vehicle_genetic_state(self) -> VehicleGeneticState | None:
    if not self.trip_selector or not self.vehicle_genetic_states:
        return None
    return self.vehicle_genetic_states.get(self.trip_selector.active_vehicle_id)
```

- [ ] **Step 2: Implement map drawing**

In `map_renderer.py`:

```python
def _trips_to_coordinates(trips, road_network) -> list[list[tuple[int, int]]]:
    return [
        [_coordinate_for_stop(stop.point_id, road_network) for stop in trip.stops]
        for trip in trips
    ]


def draw_vehicle_evolution_routes(
    screen: pygame.Surface,
    road_network,
    best_trips,
    second_best_trips,
    color: tuple[int, int, int],
) -> None:
    if second_best_trips:
        for coordinates in _trips_to_coordinates(second_best_trips, road_network):
            muted = tuple(int(channel * 0.5) for channel in color)
            _draw_styled_route(screen, coordinates, muted, "dashed", line_width=2, alpha=128)
            draw_route_direction_arrows_for_coordinates(screen, coordinates, muted)

    for coordinates in _trips_to_coordinates(best_trips, road_network):
        _draw_styled_route(screen, coordinates, color, "solid", line_width=4)
        draw_route_direction_arrows_for_coordinates(screen, coordinates, color)
```

- [ ] **Step 3: Wire pygame_application**

Replace `draw_selected_routes` block when `simulation.is_evolution_running`:

```python
genetic = simulation.active_vehicle_genetic_state()
if genetic is not None and simulation.road_network is not None:
    color = VisualTheme.vehicle_route_colors[(simulation.trip_selector.active_vehicle_id - 1) % 3]
    draw_vehicle_evolution_routes(
        screen,
        simulation.road_network,
        genetic.best_trips,
        genetic.second_best_trips,
        color,
    )
elif active_result is not None:
    draw_selected_routes(...)  # fallback when not evolving
```

- [ ] **Step 4: Manual smoke**

Run: `python main.py` — after Simular, selected vehicle shows thick + dashed routes updating.

- [ ] **Step 5: Commit**

```bash
git add traveling_salesman_problem/visualization/map_renderer.py traveling_salesman_problem/simulation/simulation_state.py traveling_salesman_problem/simulation/pygame_application.py
git commit -m "feat: draw best and second-best routes for selected vehicle"
```

---

### Task 4: Chart highlight + map header

**Files:**
- Modify: `traveling_salesman_problem/visualization/convergence_chart.py`
- Modify: `traveling_salesman_problem/visualization/application_layout.py`
- Modify: `tests/test_convergence_chart.py`
- Modify: `traveling_salesman_problem/simulation/pygame_application.py`

**Interfaces:**
- Produces:
  - `draw_convergence_chart(..., highlight_index: int | None = None)`
  - `draw_delivery_map_header(..., generation_number, second_best_distance)`

- [ ] **Step 1: Extend chart test**

```python
    def test_highlight_index_does_not_raise(self):
        screen = pygame.Surface((450, 400))
        draw_convergence_chart(
            screen,
            [0, 1, 2],
            [[100.0, 90.0, 80.0], [120.0, 110.0, 100.0]],
            series_colors=VisualTheme.vehicle_route_colors,
            series_labels=["V1", "V2"],
            highlight_index=0,
        )
```

- [ ] **Step 2: Implement highlight in chart**

In multi-series loop:

```python
is_highlight = highlight_index is not None and index == highlight_index
linewidth = 2.5 if is_highlight else 1.5
alpha = 1.0 if is_highlight else 0.4
color_rgba = (*matplotlib.colors.to_rgb(color), alpha)  # or apply alpha to line via alpha param
axes.plot(..., linewidth=linewidth, alpha=alpha)
```

- [ ] **Step 3: Update map header**

Extend `draw_delivery_map_header` signature:

```python
def draw_delivery_map_header(
    screen,
    map_start_x,
    window_width,
    total_distance,
    generation_number: int | None = None,
    active_vehicle_id: int | None = None,
    second_best_distance: float | None = None,
) -> None:
```

Subtitle when evolving:

```python
if generation_number is not None and active_vehicle_id is not None:
    parts = [f"Gen {generation_number}", f"V{active_vehicle_id}"]
    if total_distance is not None:
        parts.append(f"melhor {total_distance:.0f} px")
    if second_best_distance is not None and second_best_distance < float("inf"):
        parts.append(f"2ª {second_best_distance:.0f} px")
    subtitle = " · ".join(parts)
```

Call from `pygame_application.py` with `simulation.generation_counter`, active vehicle id, and `genetic.second_best_distance`.

- [ ] **Step 4: Pass highlight_index to chart**

```python
highlight_index = simulation.trip_selector.active_vehicle_id - 1 if simulation.trip_selector else None
draw_convergence_chart(..., highlight_index=highlight_index)
```

- [ ] **Step 5: Run tests**

Run: `python -m unittest discover tests -v`  
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add traveling_salesman_problem/visualization/convergence_chart.py traveling_salesman_problem/visualization/application_layout.py traveling_salesman_problem/simulation/pygame_application.py tests/test_convergence_chart.py
git commit -m "feat: highlight active vehicle on chart and show gen in header"
```

---

### Task 5: UI polish

**Files:**
- Modify: `traveling_salesman_problem/simulation/simulation_state.py`

- [ ] **Step 1: Update Simular button subtitle**

```python
self.simulate_button = ActionButton(
    ...,
    subtitle="Guloso + AG contínuo (~3 gen/s)",
)
```

- [ ] **Step 2: Full test suite + manual smoke**

Run: `python -m unittest discover tests -v`  
Run: `python main.py` — verify chart lines move ~3/s, map shows 2 routes, header updates.

- [ ] **Step 3: Commit**

```bash
git add traveling_salesman_problem/simulation/simulation_state.py
git commit -m "chore: clarify continuous AG subtitle on Simular button"
```

---

## Spec Coverage Checklist

| Spec requirement | Task |
|------------------|------|
| second_best_* in AG | Task 1 |
| Throttle 3 gen/s | Task 2 |
| Map best + 2nd best selected vehicle | Task 3 |
| Chart highlight selected vehicle | Task 4 |
| Header Gen + distances | Task 4 |
| Sortear + Simular flow | unchanged |
| Tests | Tasks 1, 2, 4 |

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-08-live-evolution-visualization.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — execute tasks in this session with checkpoints

Which approach?
