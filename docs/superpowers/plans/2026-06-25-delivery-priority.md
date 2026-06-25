# Delivery Priority TSP Extension — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the genetic-algorithm TSP simulator so routes balance total distance against delivery urgency via a configurable priority weight, with hospital preset, color-coded map nodes, and decomposed metrics.

**Architecture:** Add a parallel `city_priorities: List[int]` (1–10) aligned with `city_coordinates`. Extend `calculate_route_fitness` with `Σ(prioridade × posição)` rotated from `city_coordinates[0]`. Wire a priority-weight slider and hospital preset button into existing `SimulationState` / Pygame UI without changing GA encoding, crossover, mutation, or selection.

**Tech Stack:** Python 3.9+, Pygame, Matplotlib, NumPy (existing). Unit tests via stdlib `unittest` (no new dependencies).

## Global Constraints

- Package root: `traveling_salesman_problem/` (entry point `main.py`)
- Priority scale: integers **1–10** (10 = most urgent)
- Position reference: **`city_coordinates[0]` = position 1** (rotate route before counting)
- Fitness formula: `distância + terreno + peso × Σ(prioridade × posição)`
- Priority weight slider range: **0–100**, default **0**
- Hospital preset: `random.Random(42)`, 20% critical (8–10), 30% medium (5–7), rest low (1–4), min 1 critical
- Node visualization: color gradient only (green → yellow → red), **no size change**
- Do **not** refactor GA encoding, crossover, mutation, selection, or elitism
- UI validation: manual per spec; unit tests only for pure fitness/preset logic
- All user-facing strings in **Portuguese** (match existing UI)

---

## File Map

| File | Responsibility |
|------|----------------|
| `problem/priority_presets.py` | **Create** — hospital preset assignment |
| `problem/city_generator.py` | **Modify** — random priority generation + reshuffle hook |
| `genetic_algorithm/fitness.py` | **Modify** — priority penalty, composite fitness, decomposition, visit order |
| `config/application_settings.py` | **Modify** — `initial_priority_weight`, slider height reuse |
| `config/visual_theme.py` | **Modify** — `priority_to_color()` |
| `simulation/simulation_state.py` | **Modify** — state, widgets, events, generation loop |
| `simulation/pygame_application.py` | **Modify** — draw new controls, metrics, colors |
| `visualization/map_renderer.py` | **Modify** — per-city priority colors |
| `visualization/application_layout.py` | **Modify** — header metrics, delivery-order panel, legend, footer |
| `visualization/convergence_chart.py` | **Modify** — dynamic Y-axis label (caller passes label) |
| `tests/test_fitness_priority.py` | **Create** — unit tests for penalty/preset logic |

---

### Task 1: Priority presets and random generation

**Files:**
- Create: `traveling_salesman_problem/problem/priority_presets.py`
- Modify: `traveling_salesman_problem/problem/city_generator.py`
- Create: `tests/__init__.py` (empty)
- Create: `tests/test_fitness_priority.py` (preset tests only in this task)

**Interfaces:**
- Consumes: nothing
- Produces:
  - `generate_random_priorities(number_of_cities: int) -> List[int]`
  - `apply_hospital_priority_preset(number_of_cities: int) -> List[int]`

- [ ] **Step 1: Write the failing test**

Create `tests/test_fitness_priority.py`:

```python
import unittest

from traveling_salesman_problem.problem.priority_presets import apply_hospital_priority_preset
from traveling_salesman_problem.problem.city_generator import generate_random_priorities


class HospitalPresetTests(unittest.TestCase):
    def test_preset_is_reproducible_for_same_city_count(self):
        first = apply_hospital_priority_preset(15)
        second = apply_hospital_priority_preset(15)
        self.assertEqual(first, second)

    def test_preset_values_in_valid_range(self):
        priorities = apply_hospital_priority_preset(15)
        self.assertEqual(len(priorities), 15)
        self.assertTrue(all(1 <= value <= 10 for value in priorities))

    def test_preset_has_at_least_one_critical_delivery(self):
        priorities = apply_hospital_priority_preset(15)
        self.assertGreaterEqual(max(priorities), 8)

    def test_random_priorities_length_and_range(self):
        priorities = generate_random_priorities(15)
        self.assertEqual(len(priorities), 15)
        self.assertTrue(all(1 <= value <= 10 for value in priorities))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_fitness_priority.HospitalPresetTests -v`  
Expected: FAIL with `ModuleNotFoundError` or `ImportError`

- [ ] **Step 3: Write minimal implementation**

Create `traveling_salesman_problem/problem/priority_presets.py`:

```python
"""Presets de prioridade para cenários de demonstração."""

import random
from typing import List

HOSPITAL_PRESET_SEED = 42


def apply_hospital_priority_preset(number_of_cities: int) -> List[int]:
    """Distribui prioridades hospitalares de forma determinística."""
    random_generator = random.Random(HOSPITAL_PRESET_SEED)
    city_indices = list(range(number_of_cities))
    random_generator.shuffle(city_indices)

    critical_count = max(1, round(number_of_cities * 0.20))
    medium_count = round(number_of_cities * 0.30)

    priorities = [1] * number_of_cities
    for city_index in city_indices[:critical_count]:
        priorities[city_index] = random_generator.randint(8, 10)
    for city_index in city_indices[critical_count : critical_count + medium_count]:
        priorities[city_index] = random_generator.randint(5, 7)
    for city_index in city_indices[critical_count + medium_count :]:
        priorities[city_index] = random_generator.randint(1, 4)

    return priorities
```

Add to `traveling_salesman_problem/problem/city_generator.py`:

```python
def generate_random_priorities(number_of_cities: int) -> List[int]:
    """Sorteia prioridade 1–10 para cada cidade."""
    return [random.randint(1, 10) for _ in range(number_of_cities)]
```

Update `reshuffle_cities_and_population` signature and body to accept and regenerate priorities:

```python
def reshuffle_cities_and_population(
    city_coordinates: List[CityCoordinate],
    city_priorities: List[int],
    number_of_cities: int,
    population_size: int,
    population: List[List[CityCoordinate]],
    best_fitness_history: List[float],
    best_route_history: List[List[CityCoordinate]],
    window_width: int,
    window_height: int,
    plot_horizontal_offset: int,
    city_node_radius: int,
    obstacles: List[Obstacle],
) -> None:
    city_coordinates[:] = [
        generate_random_city_coordinate(
            window_width,
            window_height,
            plot_horizontal_offset,
            city_node_radius,
            obstacles,
        )
        for _ in range(number_of_cities)
    ]
    city_priorities[:] = generate_random_priorities(number_of_cities)
    population[:] = generate_random_population(city_coordinates, population_size)
    best_fitness_history.clear()
    best_route_history.clear()
```

Create empty `tests/__init__.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_fitness_priority.HospitalPresetTests -v`  
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add traveling_salesman_problem/problem/priority_presets.py \
        traveling_salesman_problem/problem/city_generator.py \
        tests/__init__.py tests/test_fitness_priority.py
git commit -m "feat: add delivery priority presets and random generation"
```

---

### Task 2: Fitness penalty and decomposition

**Files:**
- Modify: `traveling_salesman_problem/genetic_algorithm/fitness.py`
- Modify: `tests/test_fitness_priority.py` (append fitness tests)

**Interfaces:**
- Consumes: `CityCoordinate`, `Route` types from `fitness.py`
- Produces:
  - `calculate_route_distance(route: Route, obstacles=None, use_obstacle_penalties=True) -> float`
  - `calculate_priority_penalty(route: Route, city_coordinates: List[CityCoordinate], priorities: List[int]) -> float`
  - `calculate_route_fitness(route, obstacles=None, use_obstacle_penalties=True, city_coordinates=None, priorities=None, priority_weight=0.0) -> float`
  - `decompose_route_fitness(...) -> tuple[float, float, float]` — `(fitness_total, distance, weighted_priority_penalty)`
  - `build_delivery_visit_order(route, city_coordinates, priorities) -> List[tuple[int, int, int]]` — `(position, city_number, priority)`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_fitness_priority.py`:

```python
from traveling_salesman_problem.genetic_algorithm.fitness import (
    build_delivery_visit_order,
    calculate_priority_penalty,
    calculate_route_distance,
    calculate_route_fitness,
    decompose_route_fitness,
)


class PriorityPenaltyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.city_coordinates = [(0, 0), (10, 0), (10, 10), (0, 10)]
        self.priorities = [5, 10, 1, 3]

    def test_priority_penalty_rotates_from_reference_city(self):
        # Reference city is (0,0) with priority 5 at index 0.
        # Route visit order starting from reference: (0,0)->(10,0)->(10,10)->(0,10)
        route = [(0, 0), (10, 0), (10, 10), (0, 10)]
        # penalty = 5*1 + 10*2 + 1*3 + 3*4 = 5 + 20 + 3 + 12 = 40
        self.assertEqual(calculate_priority_penalty(route, self.city_coordinates, self.priorities), 40)

    def test_priority_penalty_ignores_rotation_start_in_route_list(self):
        # Same cycle but route list starts at (10,0); reference still city_coordinates[0]
        route = [(10, 0), (10, 10), (0, 10), (0, 0)]
        self.assertEqual(calculate_priority_penalty(route, self.city_coordinates, self.priorities), 40)

    def test_fitness_with_zero_weight_ignores_priority(self):
        route = [(10, 0), (10, 10), (0, 10), (0, 0)]
        without_priority = calculate_route_fitness(route)
        with_priority = calculate_route_fitness(
            route,
            city_coordinates=self.city_coordinates,
            priorities=self.priorities,
            priority_weight=0.0,
        )
        self.assertEqual(without_priority, with_priority)

    def test_fitness_adds_weighted_priority_penalty(self):
        route = [(0, 0), (10, 0), (10, 10), (0, 10)]
        distance = calculate_route_distance(route)
        fitness = calculate_route_fitness(
            route,
            city_coordinates=self.city_coordinates,
            priorities=self.priorities,
            priority_weight=2.0,
        )
        self.assertAlmostEqual(fitness, distance + 2.0 * 40)

    def test_decompose_route_fitness_returns_components(self):
        route = [(0, 0), (10, 0), (10, 10), (0, 10)]
        total, distance, weighted_priority = decompose_route_fitness(
            route,
            city_coordinates=self.city_coordinates,
            priorities=self.priorities,
            priority_weight=2.0,
        )
        self.assertAlmostEqual(distance, calculate_route_distance(route))
        self.assertAlmostEqual(weighted_priority, 80.0)
        self.assertAlmostEqual(total, distance + 80.0)

    def test_build_delivery_visit_order(self):
        route = [(10, 0), (10, 10), (0, 10), (0, 0)]
        visit_order = build_delivery_visit_order(route, self.city_coordinates, self.priorities)
        self.assertEqual(
            visit_order,
            [(1, 1, 5), (2, 2, 10), (3, 3, 1), (4, 4, 3)],
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_fitness_priority.PriorityPenaltyTests -v`  
Expected: FAIL with `ImportError` for new functions

- [ ] **Step 3: Write minimal implementation**

Replace/extend `traveling_salesman_problem/genetic_algorithm/fitness.py`:

```python
"""Cálculo de distância e avaliação de rotas."""

import math
from typing import Any, List, Optional, Tuple

from traveling_salesman_problem.obstacles.penalty import calculate_segment_obstacle_penalty

CityCoordinate = Tuple[float, float]
Route = List[CityCoordinate]


def calculate_euclidean_distance(
    first_point: CityCoordinate,
    second_point: CityCoordinate,
) -> float:
    delta_x = first_point[0] - second_point[0]
    delta_y = first_point[1] - second_point[1]
    return math.sqrt(delta_x ** 2 + delta_y ** 2)


def calculate_route_distance(
    route: Route,
    obstacles: Optional[List[Any]] = None,
    use_obstacle_penalties: bool = True,
) -> float:
    total_cost = 0.0
    number_of_cities = len(route)

    for city_index in range(number_of_cities):
        current_city = route[city_index]
        next_city = route[(city_index + 1) % number_of_cities]
        total_cost += calculate_euclidean_distance(current_city, next_city)

        if obstacles:
            total_cost += calculate_segment_obstacle_penalty(
                current_city,
                next_city,
                obstacles,
                use_obstacle_penalties,
            )

    return total_cost


def calculate_priority_penalty(
    route: Route,
    city_coordinates: List[CityCoordinate],
    priorities: List[int],
) -> float:
    if not route or not priorities:
        return 0.0

    coordinate_to_priority = dict(zip(city_coordinates, priorities))
    reference_city = city_coordinates[0]
    start_index = route.index(reference_city)
    number_of_cities = len(route)
    total_penalty = 0.0

    for offset in range(number_of_cities):
        position = offset + 1
        city = route[(start_index + offset) % number_of_cities]
        total_penalty += coordinate_to_priority[city] * position

    return total_penalty


def build_delivery_visit_order(
    route: Route,
    city_coordinates: List[CityCoordinate],
    priorities: List[int],
) -> List[Tuple[int, int, int]]:
    coordinate_to_priority = dict(zip(city_coordinates, priorities))
    coordinate_to_city_number = {
        coordinate: index + 1 for index, coordinate in enumerate(city_coordinates)
    }
    reference_city = city_coordinates[0]
    start_index = route.index(reference_city)
    number_of_cities = len(route)
    visit_order: List[Tuple[int, int, int]] = []

    for offset in range(number_of_cities):
        position = offset + 1
        city = route[(start_index + offset) % number_of_cities]
        visit_order.append(
            (position, coordinate_to_city_number[city], coordinate_to_priority[city])
        )

    return visit_order


def calculate_route_fitness(
    route: Route,
    obstacles: Optional[List[Any]] = None,
    use_obstacle_penalties: bool = True,
    city_coordinates: Optional[List[CityCoordinate]] = None,
    priorities: Optional[List[int]] = None,
    priority_weight: float = 0.0,
) -> float:
    distance = calculate_route_distance(route, obstacles, use_obstacle_penalties)

    if priority_weight <= 0 or not city_coordinates or not priorities:
        return distance

    priority_penalty = calculate_priority_penalty(route, city_coordinates, priorities)
    return distance + priority_weight * priority_penalty


def decompose_route_fitness(
    route: Route,
    obstacles: Optional[List[Any]] = None,
    use_obstacle_penalties: bool = True,
    city_coordinates: Optional[List[CityCoordinate]] = None,
    priorities: Optional[List[int]] = None,
    priority_weight: float = 0.0,
) -> Tuple[float, float, float]:
    distance = calculate_route_distance(route, obstacles, use_obstacle_penalties)
    weighted_priority_penalty = 0.0

    if priority_weight > 0 and city_coordinates and priorities:
        weighted_priority_penalty = priority_weight * calculate_priority_penalty(
            route,
            city_coordinates,
            priorities,
        )

    fitness_total = distance + weighted_priority_penalty
    return fitness_total, distance, weighted_priority_penalty
```

- [ ] **Step 4: Run all tests to verify they pass**

Run: `python -m unittest tests.test_fitness_priority -v`  
Expected: PASS (10 tests)

- [ ] **Step 5: Commit**

```bash
git add traveling_salesman_problem/genetic_algorithm/fitness.py tests/test_fitness_priority.py
git commit -m "feat: add priority penalty to route fitness evaluation"
```

---

### Task 3: Visual theme and map rendering

**Files:**
- Modify: `traveling_salesman_problem/config/visual_theme.py`
- Modify: `traveling_salesman_problem/visualization/map_renderer.py`

**Interfaces:**
- Consumes: nothing
- Produces:
  - `VisualTheme.priority_low`, `priority_mid`, `priority_high` color constants
  - `priority_to_color(priority: int) -> Tuple[int, int, int]`
  - `draw_cities(screen, city_coordinates, priorities, node_radius)` — priorities required

- [ ] **Step 1: Add color helper to visual_theme.py**

Append after the `VisualTheme` class:

```python
def priority_to_color(priority: int) -> tuple[int, int, int]:
    """Interpola verde (1) → amarelo (5) → vermelho (10)."""
    clamped_priority = max(1, min(10, priority))
    low_color = (76, 175, 80)
    mid_color = (255, 193, 7)
    high_color = (244, 67, 54)

    if clamped_priority <= 5:
        ratio = (clamped_priority - 1) / 4
        return _interpolate_color(low_color, mid_color, ratio)

    ratio = (clamped_priority - 5) / 5
    return _interpolate_color(mid_color, high_color, ratio)


def _interpolate_color(
    start_color: tuple[int, int, int],
    end_color: tuple[int, int, int],
    ratio: float,
) -> tuple[int, int, int]:
    return tuple(
        int(start + (end - start) * ratio)
        for start, end in zip(start_color, end_color)
    )
```

- [ ] **Step 2: Update map_renderer.py**

Replace `draw_cities`:

```python
def draw_cities(
    screen: pygame.Surface,
    city_coordinates: List[CityCoordinate],
    priorities: List[int],
    node_radius: int,
) -> None:
    for city, priority in zip(city_coordinates, priorities):
        fill_color = priority_to_color(priority)
        pygame.draw.circle(screen, VisualTheme.city_stroke, city, node_radius + 2)
        pygame.draw.circle(screen, fill_color, city, node_radius)
```

Add import: `from traveling_salesman_problem.config.visual_theme import VisualTheme, priority_to_color`

- [ ] **Step 3: Smoke-test import**

Run: `python -c "from traveling_salesman_problem.config.visual_theme import priority_to_color; assert priority_to_color(1)==(76,175,80); assert priority_to_color(10)==(244,67,54); print('ok')"`  
Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add traveling_salesman_problem/config/visual_theme.py \
        traveling_salesman_problem/visualization/map_renderer.py
git commit -m "feat: color map nodes by delivery priority"
```

---

### Task 4: Simulation state — data, widgets, generation loop

**Files:**
- Modify: `traveling_salesman_problem/config/application_settings.py`
- Modify: `traveling_salesman_problem/simulation/simulation_state.py`

**Interfaces:**
- Consumes: Task 1 (`generate_random_priorities`, `apply_hospital_priority_preset`, updated `reshuffle_cities_and_population`); Task 2 (`calculate_route_fitness`, `decompose_route_fitness`)
- Produces:
  - `SimulationState.city_priorities: List[int]`
  - `SimulationState.priority_weight_slider: MutationSlider`
  - `SimulationState.hospital_preset_button: ActionButton`
  - `SimulationState.priority_weight: float` (property reading slider)
  - `run_one_generation() -> tuple[int, float, Route, Route, float, float]` — adds `(distance, weighted_priority_penalty)`

- [ ] **Step 1: Add setting default**

In `application_settings.py`, add:

```python
initial_priority_weight: float = 0.0
```

- [ ] **Step 2: Extend SimulationState fields**

Add to dataclass:

```python
city_priorities: List[int] = field(default_factory=list)
priority_weight_slider: Optional[MutationSlider] = None
hospital_preset_button: Optional[ActionButton] = None
```

Add property:

```python
@property
def priority_weight(self) -> float:
    return self.priority_weight_slider.value
```

- [ ] **Step 3: Initialize priorities in `initialize()`**

After building `city_coordinates`, add:

```python
from traveling_salesman_problem.problem.city_generator import generate_random_priorities

self.city_priorities = generate_random_priorities(settings.number_of_cities)
```

- [ ] **Step 4: Update `_create_control_widgets` layout**

Insert priority slider below mutation slider. Shift subsequent Y positions:

```python
priority_weight_y = mutation_y + settings.mutation_slider_height + 12
self.section_quantity_y = priority_weight_y + settings.mutation_slider_height + 12
# terrain_count_y, section_actions_y, regenerate_y, section_terrain_y follow from section_quantity_y chain

self.priority_weight_slider = MutationSlider(
    position_x=VisualTheme.control_margin,
    position_y=priority_weight_y,
    width=controls_width,
    height=settings.mutation_slider_height,
    value=settings.initial_priority_weight,
    minimum_value=0.0,
    maximum_value=100.0,
    label="Peso da prioridade",
    value_suffix="",
)

# After regenerate_positions_button, add hospital button:
hospital_preset_y = regenerate_y + settings.regenerate_button_height + VisualTheme.control_gap
self.hospital_preset_button = ActionButton(
    position_x=VisualTheme.control_margin,
    position_y=hospital_preset_y,
    width=controls_width,
    height=settings.regenerate_button_height,
    label="Cenário hospitalar",
    subtitle="Prioridades críticas fixas",
)
self.section_terrain_y = hospital_preset_y + settings.regenerate_button_height + 12
```

- [ ] **Step 5: Wire events**

In `handle_control_events`:

```python
self.priority_weight_slider.handle_event(event)
self.hospital_preset_button.handle_event(event)

if event.type == pygame.KEYDOWN:
    if event.key == pygame.K_p:
        self.apply_hospital_preset()
```

Add method:

```python
def apply_hospital_preset(self) -> None:
    from traveling_salesman_problem.problem.priority_presets import apply_hospital_priority_preset
    self.city_priorities[:] = apply_hospital_priority_preset(len(self.city_coordinates))
```

In `update_terrain_counts_if_changed`, after hospital button press check:

```python
if self.hospital_preset_button.was_pressed:
    self.hospital_preset_button.was_pressed = False
    self.apply_hospital_preset()
    return
```

Update `shuffle_terrain_and_cities` call to pass `self.city_priorities`.

- [ ] **Step 6: Update `run_one_generation`**

```python
from traveling_salesman_problem.genetic_algorithm.fitness import (
    calculate_route_fitness,
    decompose_route_fitness,
)

priority_weight = self.priority_weight

population_fitness = [
    calculate_route_fitness(
        route,
        self.terrain_features,
        use_penalties,
        self.city_coordinates,
        self.city_priorities,
        priority_weight,
    )
    for route in self.population
]

# ... after best_route selected ...

best_fitness, best_distance, best_weighted_priority = decompose_route_fitness(
    best_route,
    self.terrain_features,
    use_penalties,
    self.city_coordinates,
    self.city_priorities,
    priority_weight,
)

return (
    generation_number,
    best_fitness,
    best_route,
    second_best_route,
    best_distance,
    best_weighted_priority,
)
```

- [ ] **Step 7: Verify import chain**

Run: `python -c "from traveling_salesman_problem.simulation.simulation_state import SimulationState; s=SimulationState(); s.initialize(); print(len(s.city_priorities))"`  
Expected: `15`

- [ ] **Step 8: Commit**

```bash
git add traveling_salesman_problem/config/application_settings.py \
        traveling_salesman_problem/simulation/simulation_state.py
git commit -m "feat: wire priority state, controls, and fitness into simulation"
```

---

### Task 5: UI layout — header metrics, delivery order, legend, footer

**Files:**
- Modify: `traveling_salesman_problem/visualization/application_layout.py`

**Interfaces:**
- Consumes: `build_delivery_visit_order` from `fitness.py`
- Produces:
  - `draw_map_header(..., best_distance, weighted_priority_penalty, priority_weight, mutation_percentage, obstacle_penalties_active)`
  - `draw_delivery_order_panel(screen, visit_order, position_y) -> int` — returns next Y
  - Updated `draw_map_legend` with priority swatches
  - Updated `draw_sidebar_footer` with **P** hint

- [ ] **Step 1: Extend draw_map_header signature and body**

Replace statistics block:

```python
def draw_map_header(
    screen: pygame.Surface,
    map_start_x: int,
    window_width: int,
    generation_number: int,
    best_fitness: float,
    best_distance: float,
    weighted_priority_penalty: float,
    priority_weight: float,
    mutation_percentage: float,
    obstacle_penalties_active: bool,
) -> None:
    # ... existing chrome ...

    if priority_weight <= 0:
        mode_label = "Só distância"
        mode_color = VisualTheme.text_muted
    elif priority_weight < 50:
        mode_label = "Equilibrado"
        mode_color = VisualTheme.text_primary
    else:
        mode_label = "Críticas primeiro"
        mode_color = VisualTheme.accent

    screen.blit(
        muted_font.render(mode_label, True, mode_color),
        (map_start_x + 16, 28),
    )

    statistics_parts = [
        f"Geração {generation_number}",
        f"Fitness {best_fitness:.1f}",
        f"Dist {best_distance:.1f}",
    ]
    if priority_weight > 0:
        statistics_parts.append(f"Prior {weighted_priority_penalty:.1f}")
    statistics_parts.append(f"Mut {mutation_percentage:.0f}%")
    statistics_text = "   ·   ".join(statistics_parts)
```

- [ ] **Step 2: Add draw_delivery_order_panel**

```python
def draw_delivery_order_panel(
    screen: pygame.Surface,
    visit_order: List[Tuple[int, int, int]],
    position_x: int,
    position_y: int,
    width: int,
    maximum_visible_rows: int = 8,
) -> int:
    header_font = get_user_interface_font(11, bold=True)
    row_font = get_monospace_font(10)
    screen.blit(
        header_font.render("ORDEM DE ENTREGAS", True, VisualTheme.text_muted),
        (position_x, position_y),
    )
    current_y = position_y + 18
    pygame.draw.line(
        screen,
        VisualTheme.divider,
        (position_x, current_y),
        (position_x + width, current_y),
        1,
    )
    current_y += 6

    for position, city_number, priority in visit_order[:maximum_visible_rows]:
        critical_marker = " ★" if priority >= 8 else ""
        line = f"{position:2d} · Cidade {city_number:2d} · prior. {priority}{critical_marker}"
        screen.blit(row_font.render(line, True, VisualTheme.text_primary), (position_x, current_y))
        current_y += 16

    if len(visit_order) > maximum_visible_rows:
        screen.blit(
            row_font.render(f"... +{len(visit_order) - maximum_visible_rows} entregas", True, VisualTheme.text_muted),
            (position_x, current_y),
        )
        current_y += 16

    return current_y + 4
```

Add imports: `from typing import List, Tuple` and `from traveling_salesman_problem.config.visual_theme import priority_to_color`.

- [ ] **Step 3: Extend draw_map_legend**

Add priority items using `priority_to_color`:

```python
legend_items = [
    (VisualTheme.route_best, "Melhor rota"),
    (VisualTheme.route_second_best, "Segunda melhor"),
    (priority_to_color(1), "Baixa prioridade (1)"),
    (priority_to_color(5), "Média prioridade (5)"),
    (priority_to_color(10), "Alta prioridade (10)"),
    (VisualTheme.tree_foliage, "Árvore"),
    (VisualTheme.lake_water, "Lago"),
]
```

Remove old generic "Cidades" entry. Increase `panel_width` to ~180 if needed.

- [ ] **Step 4: Update draw_sidebar_footer**

```python
hints = "Q · Sair    O · Penalidades de terreno    P · Cenário hospitalar    Esc · Fechar"
```

- [ ] **Step 5: Commit**

```bash
git add traveling_salesman_problem/visualization/application_layout.py
git commit -m "feat: add priority metrics header and delivery order panel"
```

---

### Task 6: Wire Pygame application loop

**Files:**
- Modify: `traveling_salesman_problem/simulation/pygame_application.py`

**Interfaces:**
- Consumes: all Task 4–5 outputs
- Produces: fully integrated running application

- [ ] **Step 1: Update generation unpacking**

```python
(
    generation_number,
    best_fitness,
    best_route,
    second_best_route,
    best_distance,
    best_weighted_priority,
) = simulation.run_one_generation()
```

- [ ] **Step 2: Draw priority slider and hospital button**

After mutation slider draw:

```python
simulation.priority_weight_slider.draw(screen)
```

After regenerate button draw:

```python
simulation.hospital_preset_button.draw(screen)
```

- [ ] **Step 3: Update draw_map_header call**

```python
draw_map_header(
    screen,
    settings.plot_horizontal_offset,
    settings.window_width,
    generation_number,
    best_fitness,
    best_distance,
    best_weighted_priority,
    simulation.priority_weight,
    simulation.mutation_slider.value * 100,
    simulation.terrain_control_panel.use_terrain_penalties,
)
```

- [ ] **Step 4: Update draw_cities call**

```python
draw_cities(
    screen,
    simulation.city_coordinates,
    simulation.city_priorities,
    settings.city_node_radius,
)
```

- [ ] **Step 5: Draw delivery order panel**

```python
from traveling_salesman_problem.genetic_algorithm.fitness import build_delivery_visit_order
from traveling_salesman_problem.visualization.application_layout import draw_delivery_order_panel

visit_order = build_delivery_visit_order(
    best_route,
    simulation.city_coordinates,
    simulation.city_priorities,
)
delivery_panel_y = settings.window_height - 200
draw_delivery_order_panel(
    screen,
    visit_order,
    VisualTheme.control_margin,
    delivery_panel_y,
    settings.plot_horizontal_offset - 2 * VisualTheme.control_margin,
)
```

- [ ] **Step 6: Dynamic convergence chart label**

```python
vertical_axis_label = (
    "Fitness (custo total)"
    if simulation.priority_weight > 0
    else "Distância (pixels)"
)
draw_convergence_chart(
    screen,
    list(range(len(simulation.best_fitness_history))),
    simulation.best_fitness_history,
    vertical_axis_label=vertical_axis_label,
)
```

- [ ] **Step 7: Update console print**

```python
print(
    f"Geração {generation_number}: "
    f"fitness={round(best_fitness, 2)}  "
    f"dist={round(best_distance, 2)}  "
    f"prior={round(best_weighted_priority, 2)}  "
    f"peso={round(simulation.priority_weight)}"
)
```

- [ ] **Step 8: Manual smoke test**

Run: `python main.py`  
Verify:
- App launches without errors
- Cities show green/yellow/red colors
- Priority slider visible and defaults to 0
- At weight 0, header shows "Só distância"

- [ ] **Step 9: Commit**

```bash
git add traveling_salesman_problem/simulation/pygame_application.py
git commit -m "feat: integrate delivery priority UI into pygame application"
```

---

### Task 7: Manual verification checklist (spec §8)

**Files:** none (verification only)

- [ ] **Step 1: Run unit tests**

Run: `python -m unittest tests.test_fitness_priority -v`  
Expected: all PASS

- [ ] **Step 2: Peso 0 — TSP original behavior**

Run app, keep weight at 0, confirm fitness ≈ distance in header.

- [ ] **Step 3: Peso 100 + preset hospitalar**

Press **P**, set weight to 100, wait ~50 generations. Confirm ★ deliveries (priority ≥ 8) appear in top positions in delivery-order panel.

- [ ] **Step 4: Slider ao vivo**

Mid-run, increase weight from 0 to 50. Confirm fitness values jump and convergence chart Y-label changes.

- [ ] **Step 5: Sortear posições**

Click "Sortear posições". Confirm new random priorities and cleared convergence history.

- [ ] **Step 6: Tecla P**

Press **P** without moving cities (compare city positions before/after).

- [ ] **Step 7: Métricas**

Confirm `fitness ≈ dist + prior` (± terrain if **O** active).

- [ ] **Step 8: Commit verification note (optional)**

No commit required unless fixes were needed during verification.

---

## Spec Coverage Self-Review

| Spec requirement | Task |
|------------------|------|
| Priority 1–10 per delivery | Task 1, 4 |
| Random + hospital preset | Task 1, 4 |
| Fitness `dist + terreno + peso × Σ(p×pos)` | Task 2, 4 |
| Weight slider 0–100 | Task 4, 6 |
| Position ref index 0 | Task 2 |
| Color gradient nodes | Task 3, 6 |
| Header metrics decomposed | Task 5, 6 |
| Delivery order panel with ★ | Task 5, 6 |
| Convergence Y-axis label | Task 6 |
| Console output | Task 6 |
| Keyboard P shortcut | Task 4 |
| GA encoding unchanged | Global constraint (no task modifies crossover/mutation/selection) |
| Manual verification §8 | Task 7 |

No placeholders. Types consistent across tasks.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-25-delivery-priority.md`. Two execution options:

**1. Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** — execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
