# Delivery Genetic Optimization — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add continuous per-vehicle genetic algorithm optimization after greedy assignment, with multi-line convergence chart (one line per vehicle) and graph-based route evaluation, matching the TSP main-branch UX.

**Architecture:** Greedy simulation runs once on **Simular** to fix vehicle assignments (`DeliveryTask` tokens). Each vehicle then evolves an independent population of task permutations using reused GA operators from `genetic_algorithm/`. Fitness is total graph distance via a new `route_evaluator`. Pygame loop calls `run_one_generation()` every frame while evolution is active.

**Tech Stack:** Python 3.9+, Pygame, matplotlib (Agg backend for chart), numpy, stdlib `unittest`. Reuse `genetic_algorithm/population.py`, `selection.py`, `mutation.py`, `crossover.py`.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-07-08-delivery-genetic-optimization-design.md`
- Vehicles: **1–3**; delivery points: **1–3**; item totals: **2, 4, 6, 8, 10, 12, 14** only
- Capacity: **10 items/trip**; partial delivery via multiple `DeliveryTask` tokens
- Distance/fitness: **graph pathfinding** (BFS, transit nodes, depot trip rules from `routing.py`)
- Population size: **100** (fixed); mutation slider: **0.0–1.0**, default **0.01**, label **Mutação (%)**
- Elitism: **3**; mutation type: **adjacent**; **no 2-opt**
- UI language: **Portuguese**
- Loop: continuous after **Simular**; **Sortear** resets evolution + chart history
- Chart: **N lines** (1 per vehicle), colors from `VisualTheme.vehicle_route_colors`
- Test runner: `python -m unittest discover tests -v`
- Pygame manual smoke test: out of scope for automated tests

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `delivery_simulation/models.py` | Modify | Add `DeliveryTask` |
| `delivery_simulation/assignment.py` | Modify | Add `extract_vehicle_assignments`, keep `run_simulation` |
| `delivery_simulation/route_evaluator.py` | Create | Simulate permutation on graph → distance + trips |
| `delivery_simulation/vehicle_genetic.py` | Create | Per-vehicle GA state + `run_one_generation` |
| `delivery_simulation/__init__.py` | Modify | Export new symbols |
| `tests/test_assignment_extraction.py` | Create | Assignment extraction tests |
| `tests/test_route_evaluator.py` | Create | Evaluator + capacity + graph tests |
| `tests/test_vehicle_genetic.py` | Create | GA initialization + improvement tests |
| `traveling_salesman_problem/visualization/convergence_chart.py` | Modify | Multi-series chart |
| `tests/test_convergence_chart.py` | Create | Smoke test for N series |
| `traveling_salesman_problem/config/application_settings.py` | Modify | Restore plot layout + GA params |
| `traveling_salesman_problem/simulation/simulation_state.py` | Modify | Evolution loop, histories, mutation slider |
| `traveling_salesman_problem/simulation/pygame_application.py` | Modify | Chart at top, continuous generation loop |
| `traveling_salesman_problem/visualization/application_layout.py` | Modify | Remove tall summary panel usage |

---

### Task 1: `DeliveryTask` model

**Files:**
- Modify: `delivery_simulation/models.py`
- Test: `tests/test_assignment_extraction.py` (partial — model smoke test)

**Interfaces:**
- Consumes: nothing
- Produces:
  - `@dataclass(frozen=True) class DeliveryTask: point_id: str; items: int`

- [ ] **Step 1: Add model**

In `delivery_simulation/models.py`, after imports:

```python
@dataclass(frozen=True)
class DeliveryTask:
    point_id: str
    items: int
```

- [ ] **Step 2: Smoke test**

Add to `tests/test_assignment_extraction.py`:

```python
import unittest

from delivery_simulation.models import DeliveryTask


class DeliveryTaskTests(unittest.TestCase):
    def test_task_is_hashable_and_equal(self):
        first = DeliveryTask("A", 10)
        second = DeliveryTask("A", 10)
        self.assertEqual(first, second)
        self.assertEqual(len({first, second}), 1)
```

- [ ] **Step 3: Run test**

Run: `python -m unittest tests.test_assignment_extraction.DeliveryTaskTests -v`  
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add delivery_simulation/models.py tests/test_assignment_extraction.py
git commit -m "feat: add DeliveryTask model for GA permutations"
```

---

### Task 2: Greedy assignment extraction

**Files:**
- Modify: `delivery_simulation/assignment.py`
- Modify: `delivery_simulation/__init__.py`
- Test: `tests/test_assignment_extraction.py`

**Interfaces:**
- Consumes: `SimulationResult`, `DeliveryTask`, `DEPOT_ID`, `Stop`
- Produces:
  - `extract_vehicle_assignments(result: SimulationResult) -> dict[int, list[DeliveryTask]]`

- [ ] **Step 1: Write failing test**

Append to `tests/test_assignment_extraction.py`:

```python
from delivery_simulation.assignment import extract_vehicle_assignments
from delivery_simulation.models import (
    DEPOT_ID,
    DeliveryPoint,
    DeliveryTask,
    RoadNetwork,
    SimulationConfig,
    SimulationResult,
    Stop,
    Trip,
    Vehicle,
)


class ExtractVehicleAssignmentsTests(unittest.TestCase):
    def test_extracts_delivery_stops_per_vehicle(self):
        network = RoadNetwork(nodes={DEPOT_ID: (0.0, 0.0), "A": (1.0, 0.0)}, edges=[], connection_radius=100.0)
        result = SimulationResult(
            config=SimulationConfig(2, 1, 14),
            depot=(0.0, 0.0),
            delivery_points=[DeliveryPoint("A", (1.0, 0.0), 14, 0)],
            vehicles=[
                Vehicle(
                    id=1,
                    current_node_id=DEPOT_ID,
                    current_position=(0.0, 0.0),
                    current_load=0,
                    trips=[
                        Trip(
                            stops=[
                                Stop(DEPOT_ID, 0),
                                Stop("A", 10),
                                Stop(DEPOT_ID, 0),
                            ],
                            distance=20.0,
                        )
                    ],
                ),
                Vehicle(
                    id=2,
                    current_node_id=DEPOT_ID,
                    current_position=(0.0, 0.0),
                    current_load=0,
                    trips=[
                        Trip(
                            stops=[
                                Stop(DEPOT_ID, 0),
                                Stop("A", 4),
                                Stop(DEPOT_ID, 0),
                            ],
                            distance=10.0,
                        )
                    ],
                ),
            ],
            total_system_distance=30.0,
            road_network=network,
            transit_nodes=[],
        )

        assignments = extract_vehicle_assignments(result)

        self.assertEqual(assignments[1], [DeliveryTask("A", 10)])
        self.assertEqual(assignments[2], [DeliveryTask("A", 4)])

    def test_ignores_transit_and_empty_stops(self):
        network = RoadNetwork(nodes={DEPOT_ID: (0.0, 0.0), "A": (1.0, 0.0), "T1": (0.5, 0.0)}, edges=[], connection_radius=100.0)
        result = SimulationResult(
            config=SimulationConfig(1, 1, 4),
            depot=(0.0, 0.0),
            delivery_points=[DeliveryPoint("A", (1.0, 0.0), 4, 0)],
            vehicles=[
                Vehicle(
                    id=1,
                    current_node_id=DEPOT_ID,
                    current_position=(0.0, 0.0),
                    current_load=0,
                    trips=[
                        Trip(
                            stops=[
                                Stop(DEPOT_ID, 0),
                                Stop("T1", 0, is_transit=True),
                                Stop("A", 4),
                                Stop("T1", 0, is_transit=True),
                                Stop(DEPOT_ID, 0),
                            ],
                            distance=30.0,
                        )
                    ],
                ),
            ],
            total_system_distance=30.0,
            road_network=network,
            transit_nodes=[],
        )

        self.assertEqual(extract_vehicle_assignments(result)[1], [DeliveryTask("A", 4)])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_assignment_extraction.ExtractVehicleAssignmentsTests -v`  
Expected: FAIL — `ImportError: cannot import name 'extract_vehicle_assignments'`

- [ ] **Step 3: Implement extraction**

In `delivery_simulation/assignment.py`:

```python
from delivery_simulation.models import DeliveryTask, DEPOT_ID, SimulationResult


def extract_vehicle_assignments(result: SimulationResult) -> dict[int, list[DeliveryTask]]:
    assignments: dict[int, list[DeliveryTask]] = {}

    for vehicle in result.vehicles:
        tasks: list[DeliveryTask] = []
        for trip in vehicle.trips:
            for stop in trip.stops:
                if stop.is_transit:
                    continue
                if stop.point_id == DEPOT_ID:
                    continue
                if stop.items_delivered <= 0:
                    continue
                tasks.append(DeliveryTask(stop.point_id, stop.items_delivered))
        assignments[vehicle.id] = tasks

    return assignments
```

Export in `delivery_simulation/__init__.py`:

```python
from delivery_simulation.assignment import extract_vehicle_assignments, run_simulation
# add to __all__
"extract_vehicle_assignments",
"DeliveryTask",
```

Import `DeliveryTask` in `__init__.py` from models.

- [ ] **Step 4: Run tests**

Run: `python -m unittest tests.test_assignment_extraction -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delivery_simulation/assignment.py delivery_simulation/__init__.py tests/test_assignment_extraction.py
git commit -m "feat: extract fixed vehicle assignments from greedy result"
```

---

### Task 3: Route evaluator (graph + capacity)

**Files:**
- Create: `delivery_simulation/route_evaluator.py`
- Test: `tests/test_route_evaluator.py`

**Interfaces:**
- Consumes: `DeliveryTask`, `RoadNetwork`, `find_path`, `path_distance`, `DEPOT_ID`, `MAX_CAPACITY`, `Trip`, `Stop`
- Produces:
  - `TaskPermutation = list[DeliveryTask]`
  - `evaluate_permutation(tasks: list[DeliveryTask], permutation: TaskPermutation, road_network: RoadNetwork) -> tuple[float, list[Trip]]`
  - Returns `(total_distance, trips)`; `total_distance == float("inf")` if any leg unreachable

- [ ] **Step 1: Write failing tests**

Create `tests/test_route_evaluator.py`:

```python
import unittest

from delivery_simulation.models import DEPOT_ID, DeliveryTask, RoadNetwork
from delivery_simulation.road_network import build_road_network
from delivery_simulation.route_evaluator import evaluate_permutation


class RouteEvaluatorTests(unittest.TestCase):
    def test_single_task_uses_graph_not_euclidean_skip(self):
        nodes = {
            DEPOT_ID: (0.0, 0.0),
            "T1": (5.0, 0.0),
            "A": (10.0, 0.0),
        }
        network = build_road_network(nodes, radius=6.0)
        tasks = [DeliveryTask("A", 4)]
        distance, trips = evaluate_permutation(tasks, tasks, network)

        stop_ids = [stop.point_id for stop in trips[0].stops]
        self.assertIn("T1", stop_ids)
        self.assertAlmostEqual(distance, 20.0)

    def test_capacity_splits_into_two_trips(self):
        nodes = {DEPOT_ID: (0.0, 0.0), "A": (10.0, 0.0)}
        network = build_road_network(nodes, radius=100.0)
        tasks = [DeliveryTask("A", 10), DeliveryTask("A", 4)]
        permutation = list(tasks)
        distance, trips = evaluate_permutation(tasks, permutation, network)

        self.assertEqual(len(trips), 2)
        self.assertEqual(trips[0].stops[0].point_id, DEPOT_ID)
        self.assertEqual(trips[0].stops[-1].point_id, DEPOT_ID)
        self.assertEqual(trips[1].stops[-1].point_id, DEPOT_ID)
        self.assertGreater(distance, 0.0)

    def test_unreachable_leg_returns_infinity(self):
        nodes = {DEPOT_ID: (0.0, 0.0), "A": (100.0, 0.0)}
        network = build_road_network(nodes, radius=1.0)
        tasks = [DeliveryTask("A", 4)]
        distance, trips = evaluate_permutation(tasks, tasks, network)
        self.assertEqual(distance, float("inf"))
        self.assertEqual(trips, [])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_route_evaluator -v`  
Expected: FAIL — `ModuleNotFoundError: route_evaluator`

- [ ] **Step 3: Implement evaluator**

Create `delivery_simulation/route_evaluator.py`. Reuse pathfinding rules from `routing.py` by importing helpers or duplicating minimal `_blocked_for_pathfinding`, `_is_transit_node`, `_traverse_path` logic inline (prefer import from `routing.py` if made public; otherwise copy the three small helpers into `route_evaluator.py` to avoid large refactor):

```python
"""Avalia permutação de entregas na rede de ruas."""

from dataclasses import dataclass, field
from typing import List, Optional, Set

from delivery_simulation.models import DEPOT_ID, MAX_CAPACITY, DeliveryTask, RoadNetwork, Stop, Trip
from delivery_simulation.road_network import find_path, path_distance

TaskPermutation = List[DeliveryTask]


@dataclass
class _ActiveTrip:
    stops: List[Stop] = field(default_factory=list)
    distance: float = 0.0
    visited_nodes: Set[str] = field(default_factory=set)


def _is_transit_node(node_id: str) -> bool:
    return node_id.startswith("T")


def _blocked_for_pathfinding(blocked: Set[str], destination: str) -> Set[str]:
    if destination != DEPOT_ID:
        return set(blocked)
    return {node_id for node_id in blocked if not _is_transit_node(node_id) and node_id != DEPOT_ID}


def _existing_stop_ids(active_trip: _ActiveTrip) -> Set[str]:
    return {stop.point_id for stop in active_trip.stops}


def _append_path(
    active_trip: _ActiveTrip,
    network: RoadNetwork,
    path: List[str],
    delivery_node: Optional[str],
    delivery_amount: int,
    record_transit_stops: bool,
) -> bool:
    for index in range(1, len(path)):
        previous_id = path[index - 1]
        node_id = path[index]
        active_trip.distance += path_distance(network, [previous_id, node_id])

        is_delivery = node_id == delivery_node and delivery_amount > 0
        if node_id == DEPOT_ID:
            active_trip.stops.append(Stop(DEPOT_ID, 0, is_transit=False))
        elif is_delivery:
            active_trip.stops.append(Stop(node_id, delivery_amount, is_transit=False))
        elif _is_transit_node(node_id) and record_transit_stops:
            if node_id not in _existing_stop_ids(active_trip):
                active_trip.stops.append(Stop(node_id, 0, is_transit=True))

        if node_id != DEPOT_ID or index == len(path) - 1:
            active_trip.visited_nodes.add(node_id)

    if path and path[0] == DEPOT_ID and len(path) > 1:
        active_trip.visited_nodes.add(DEPOT_ID)
    return True


def evaluate_permutation(
    tasks: List[DeliveryTask],
    permutation: TaskPermutation,
    road_network: RoadNetwork,
) -> tuple[float, List[Trip]]:
    if not tasks:
        return 0.0, []

    if len(permutation) != len(tasks):
        return float("inf"), []

    current_node = DEPOT_ID
    load = 0
    completed_trips: List[Trip] = []
    active_trip = _ActiveTrip(stops=[Stop(DEPOT_ID, 0)])

    for task in permutation:
        if load + task.items > MAX_CAPACITY:
            blocked = active_trip.visited_nodes
            path = find_path(road_network, current_node, DEPOT_ID, _blocked_for_pathfinding(blocked, DEPOT_ID))
            if not path:
                return float("inf"), []
            _append_path(active_trip, road_network, path, None, 0, record_transit_stops=False)
            completed_trips.append(Trip(stops=list(active_trip.stops), distance=active_trip.distance))
            active_trip = _ActiveTrip(stops=[Stop(DEPOT_ID, 0)])
            current_node = DEPOT_ID
            load = 0

        blocked = active_trip.visited_nodes
        path = find_path(road_network, current_node, task.point_id, _blocked_for_pathfinding(blocked, task.point_id))
        if not path:
            return float("inf"), []
        _append_path(active_trip, road_network, path, task.point_id, task.items, record_transit_stops=True)
        current_node = task.point_id
        load += task.items

    blocked = active_trip.visited_nodes
    path = find_path(road_network, current_node, DEPOT_ID, _blocked_for_pathfinding(blocked, DEPOT_ID))
    if not path:
        return float("inf"), []
    _append_path(active_trip, road_network, path, None, 0, record_transit_stops=False)
    completed_trips.append(Trip(stops=list(active_trip.stops), distance=active_trip.distance))

    total_distance = sum(trip.distance for trip in completed_trips)
    return total_distance, completed_trips
```

Export `evaluate_permutation` from `delivery_simulation/__init__.py`.

- [ ] **Step 4: Run tests**

Run: `python -m unittest tests.test_route_evaluator -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delivery_simulation/route_evaluator.py delivery_simulation/__init__.py tests/test_route_evaluator.py
git commit -m "feat: evaluate delivery permutations on road network"
```

---

### Task 4: Per-vehicle genetic algorithm

**Files:**
- Create: `delivery_simulation/vehicle_genetic.py`
- Test: `tests/test_vehicle_genetic.py`

**Interfaces:**
- Consumes: `DeliveryTask`, `evaluate_permutation`, `RoadNetwork`, `Trip`, `sort_population_by_fitness`, `evolve_next_generation`
- Produces:
  - `@dataclass VehicleGeneticState` with fields: `vehicle_id`, `tasks`, `population`, `best_distance`, `best_permutation`, `best_trips`
  - `initialize_vehicle_genetic(vehicle_id: int, tasks: list[DeliveryTask], road_network: RoadNetwork, population_size: int = 100, rng=None) -> VehicleGeneticState`
  - `run_vehicle_generation(state: VehicleGeneticState, road_network: RoadNetwork, mutation_probability: float, population_size: int = 100) -> float` → returns new best distance

- [ ] **Step 1: Write failing tests**

Create `tests/test_vehicle_genetic.py`:

```python
import random
import unittest

from delivery_simulation.models import DEPOT_ID, DeliveryTask
from delivery_simulation.road_network import build_road_network
from delivery_simulation.vehicle_genetic import initialize_vehicle_genetic, run_vehicle_generation


class VehicleGeneticTests(unittest.TestCase):
    def test_initialize_creates_population_of_permutations(self):
        network = build_road_network({DEPOT_ID: (0.0, 0.0), "A": (3.0, 0.0), "B": (0.0, 4.0)}, radius=100.0)
        tasks = [DeliveryTask("A", 4), DeliveryTask("B", 4)]
        state = initialize_vehicle_genetic(1, tasks, network, population_size=20, rng=random.Random(0))

        self.assertEqual(len(state.population), 20)
        self.assertEqual(len(state.population[0]), 2)
        self.assertLess(state.best_distance, float("inf"))

    def test_generation_does_not_worsen_best(self):
        network = build_road_network({DEPOT_ID: (0.0, 0.0), "A": (3.0, 0.0), "B": (0.0, 4.0)}, radius=100.0)
        tasks = [DeliveryTask("A", 4), DeliveryTask("B", 4)]
        state = initialize_vehicle_genetic(1, tasks, network, population_size=30, rng=random.Random(1))
        initial_best = state.best_distance

        for _ in range(5):
            run_vehicle_generation(state, network, mutation_probability=0.2, population_size=30)

        self.assertLessEqual(state.best_distance, initial_best)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_vehicle_genetic -v`  
Expected: FAIL — module not found

- [ ] **Step 3: Implement vehicle genetic**

Create `delivery_simulation/vehicle_genetic.py`:

```python
"""Algoritmo genético por veículo sobre permutações de DeliveryTask."""

import random
from dataclasses import dataclass, field
from typing import List, Optional

from delivery_simulation.models import DeliveryTask, RoadNetwork, Trip
from delivery_simulation.route_evaluator import TaskPermutation, evaluate_permutation
from traveling_salesman_problem.genetic_algorithm.population import sort_population_by_fitness
from traveling_salesman_problem.genetic_algorithm.selection import evolve_next_generation

TaskPopulation = List[TaskPermutation]


@dataclass
class VehicleGeneticState:
    vehicle_id: int
    tasks: List[DeliveryTask]
    population: TaskPopulation = field(default_factory=list)
    best_distance: float = field(default_factory=lambda: float("inf"))
    best_permutation: TaskPermutation = field(default_factory=list)
    best_trips: List[Trip] = field(default_factory=list)


def _generate_random_population(tasks: List[DeliveryTask], population_size: int, rng: random.Random) -> TaskPopulation:
    if not tasks:
        return [[] for _ in range(population_size)]
    return [rng.sample(tasks, len(tasks)) for _ in range(population_size)]


def _evaluate_population(
    tasks: List[DeliveryTask],
    population: TaskPopulation,
    road_network: RoadNetwork,
) -> tuple[list[float], TaskPermutation, float, List[Trip]]:
    fitness_values: list[float] = []
    best_distance = float("inf")
    best_permutation: TaskPermutation = []
    best_trips: List[Trip] = []

    for permutation in population:
        distance, trips = evaluate_permutation(tasks, permutation, road_network)
        fitness = distance if distance > 0 else 0.0
        if distance == float("inf"):
            fitness = float("inf")
        fitness_values.append(fitness)
        if distance < best_distance:
            best_distance = distance
            best_permutation = list(permutation)
            best_trips = trips

    return fitness_values, best_permutation, best_distance, best_trips


def initialize_vehicle_genetic(
    vehicle_id: int,
    tasks: List[DeliveryTask],
    road_network: RoadNetwork,
    population_size: int = 100,
    rng: Optional[random.Random] = None,
) -> VehicleGeneticState:
    random_source = rng or random.Random()
    population = _generate_random_population(tasks, population_size, random_source)
    _, best_permutation, best_distance, best_trips = _evaluate_population(tasks, population, road_network)

    if best_distance == float("inf") and population:
        best_permutation = list(population[0])
        best_distance, best_trips = evaluate_permutation(tasks, best_permutation, road_network)

    return VehicleGeneticState(
        vehicle_id=vehicle_id,
        tasks=list(tasks),
        population=population,
        best_distance=best_distance,
        best_permutation=best_permutation,
        best_trips=best_trips,
    )


def run_vehicle_generation(
    state: VehicleGeneticState,
    road_network: RoadNetwork,
    mutation_probability: float,
    population_size: int = 100,
) -> float:
    if not state.tasks:
        state.best_distance = 0.0
        return 0.0

    fitness_values, best_permutation, best_distance, best_trips = _evaluate_population(
        state.tasks,
        state.population,
        road_network,
    )
    sorted_population, sorted_fitness = sort_population_by_fitness(state.population, fitness_values)

    finite_fitness = [value for value in sorted_fitness if value != float("inf")]
    if not finite_fitness:
        return state.best_distance

    if best_distance < state.best_distance:
        state.best_distance = best_distance
        state.best_permutation = best_permutation
        state.best_trips = best_trips

    state.population = evolve_next_generation(
        sorted_population,
        sorted_fitness,
        population_size,
        mutation_probability,
        mutation_type="adjacent",
        n_elite=3,
        use_2opt=False,
    )
    return state.best_distance
```

Export from `delivery_simulation/__init__.py`.

- [ ] **Step 4: Run tests**

Run: `python -m unittest tests.test_vehicle_genetic -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delivery_simulation/vehicle_genetic.py delivery_simulation/__init__.py tests/test_vehicle_genetic.py
git commit -m "feat: add per-vehicle genetic optimizer for delivery order"
```

---

### Task 5: Multi-series convergence chart

**Files:**
- Modify: `traveling_salesman_problem/visualization/convergence_chart.py`
- Create: `tests/test_convergence_chart.py`

**Interfaces:**
- Consumes: `VisualTheme.vehicle_route_colors`
- Produces:
  - Updated `draw_convergence_chart(screen, generation_numbers, fitness_values, ...)` — **backward compatible**: if `fitness_values` is `list[float]`, draw single line; if `list[list[float]]`, draw multi-series
  - New optional params: `series_colors: tuple | None = None`, `series_labels: list[str] | None = None`

- [ ] **Step 1: Write smoke test**

Create `tests/test_convergence_chart.py`:

```python
import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from traveling_salesman_problem.config.visual_theme import VisualTheme
from traveling_salesman_problem.visualization.convergence_chart import draw_convergence_chart


class ConvergenceChartTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_multi_series_does_not_raise(self):
        screen = pygame.Surface((450, 400))
        draw_convergence_chart(
            screen,
            [0, 1, 2],
            [[100.0, 90.0, 80.0], [120.0, 110.0, 100.0]],
            series_colors=VisualTheme.vehicle_route_colors,
            series_labels=["V1", "V2"],
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_convergence_chart -v`  
Expected: FAIL — unexpected keyword `series_colors`

- [ ] **Step 3: Extend chart**

Update `draw_convergence_chart` signature and body:

```python
def draw_convergence_chart(
    screen: pygame.Surface,
    generation_numbers: list,
    fitness_values: list,
    horizontal_axis_label: str = "Geração",
    vertical_axis_label: str = "Custo da rota",
    series_colors: tuple | None = None,
    series_labels: list[str] | None = None,
) -> None:
    figure, axes = plt.subplots(figsize=(4.4, 4), dpi=100)
    axes.set_facecolor("#f8fafc")
    figure.patch.set_facecolor("#f1f4f9")

    if fitness_values and isinstance(fitness_values[0], list):
        series_list = fitness_values
        colors = series_colors or ("#2563eb",)
        for index, series in enumerate(series_list):
            label = series_labels[index] if series_labels and index < len(series_labels) else f"S{index + 1}"
            color = colors[index % len(colors)]
            hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}" if isinstance(color, tuple) else color
            axes.plot(generation_numbers[: len(series)], series, color=hex_color, linewidth=2, label=label)
        if len(series_list) > 1:
            axes.legend(fontsize=8, loc="upper right")
    else:
        axes.plot(generation_numbers, fitness_values, color="#2563eb", linewidth=2)

    axes.set_ylabel(vertical_axis_label, fontsize=9, color="#475569")
    axes.set_xlabel(horizontal_axis_label, fontsize=9, color="#475569")
    # ... rest unchanged (tick_params, grid, blit, caption "Convergência")
```

- [ ] **Step 4: Run test**

Run: `python -m unittest tests.test_convergence_chart -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add traveling_salesman_problem/visualization/convergence_chart.py tests/test_convergence_chart.py
git commit -m "feat: support multi-vehicle lines in convergence chart"
```

---

### Task 6: Application settings + layout restore

**Files:**
- Modify: `traveling_salesman_problem/config/application_settings.py`
- Modify: `traveling_salesman_problem/visualization/application_layout.py` (only if summary panel blocks chart)

**Interfaces:**
- Produces in `ApplicationSettings`:
  - `population_size: int = 100`
  - `initial_mutation_probability: float = 0.01`
  - `mutation_slider_height: int = 58`
  - Remove or reduce `summary_panel_height` — chart uses `VisualTheme.plot_height` (400px) at y=0

- [ ] **Step 1: Update settings**

In `application_settings.py`:

```python
population_size: int = 100
initial_mutation_probability: float = 0.01
mutation_slider_height: int = 58
summary_panel_height: int = 0  # chart replaces summary at top
```

Ensure `controls_top_position` still returns `VisualTheme.plot_height + VisualTheme.control_gap`.

- [ ] **Step 2: Verify imports still work**

Run: `python -c "from traveling_salesman_problem.config.application_settings import ApplicationSettings; print(ApplicationSettings())"`  
Expected: prints dataclass without error

- [ ] **Step 3: Commit**

```bash
git add traveling_salesman_problem/config/application_settings.py
git commit -m "feat: restore GA settings for delivery evolution chart layout"
```

---

### Task 7: SimulationState — evolution loop

**Files:**
- Modify: `traveling_salesman_problem/simulation/simulation_state.py`

**Interfaces:**
- Consumes: `extract_vehicle_assignments`, `initialize_vehicle_genetic`, `run_vehicle_generation`, `run_simulation`, `MutationSlider`, `Vehicle`, `Trip`, `SimulationResult`
- Produces:
  - `is_evolution_running: bool`
  - `vehicle_genetic_states: dict[int, VehicleGeneticState]`
  - `vehicle_best_distance_history: dict[int, list[float]]`
  - `generation_counter: int`
  - `best_simulation_result: SimulationResult | None`
  - `run_one_generation() -> None`
  - `start_evolution_from_greedy() -> None` (called by Simular)
  - `_reset_evolution() -> None` (called by Sortear)

- [ ] **Step 1: Add imports and fields**

Add to `SimulationState` dataclass:

```python
from delivery_simulation import extract_vehicle_assignments, run_simulation
from delivery_simulation.vehicle_genetic import VehicleGeneticState, initialize_vehicle_genetic, run_vehicle_generation
from traveling_salesman_problem.visualization.widgets import MutationSlider

is_evolution_running: bool = False
vehicle_genetic_states: dict[int, VehicleGeneticState] = field(default_factory=dict)
vehicle_best_distance_history: dict[int, list[float]] = field(default_factory=dict)
generation_counter: int = 0
best_simulation_result: Optional[SimulationResult] = None
mutation_slider: Optional[MutationSlider] = None
```

- [ ] **Step 2: Add mutation slider in `_create_control_widgets`**

After connection radius slider:

```python
y += settings.count_slider_height + 12
self.mutation_slider = MutationSlider(
    VisualTheme.control_margin,
    y,
    controls_width,
    settings.mutation_slider_height,
    value=settings.initial_mutation_probability,
    minimum_value=0.0,
    maximum_value=1.0,
    label="Mutação",
    value_suffix="%",
)
y += settings.mutation_slider_height + 12
self.section_actions_y = y
```

Shift subsequent section Y positions accordingly.

- [ ] **Step 3: Implement evolution methods**

```python
def _reset_evolution(self) -> None:
    self.is_evolution_running = False
    self.vehicle_genetic_states = {}
    self.vehicle_best_distance_history = {}
    self.generation_counter = 0
    self.best_simulation_result = None
    if self.trip_selector is not None:
        self.trip_selector.set_enabled(False)

def _rebuild_best_simulation_result(self) -> None:
    if self.simulation_result is None:
        return
    vehicles = []
    for vehicle in self.simulation_result.vehicles:
        genetic = self.vehicle_genetic_states.get(vehicle.id)
        if genetic is None:
            vehicles.append(vehicle)
            continue
        vehicles.append(
            Vehicle(
                id=vehicle.id,
                current_node_id=vehicle.current_node_id,
                current_position=vehicle.current_position,
                current_load=0,
                trips=list(genetic.best_trips),
                assigned_points=list(vehicle.assigned_points),
            )
        )
    total_distance = sum(trip.distance for v in vehicles for trip in v.trips)
    self.best_simulation_result = SimulationResult(
        config=self.simulation_result.config,
        depot=self.simulation_result.depot,
        delivery_points=self.simulation_result.delivery_points,
        vehicles=vehicles,
        total_system_distance=total_distance,
        road_network=self.simulation_result.road_network,
        transit_nodes=self.simulation_result.transit_nodes,
    )

def start_evolution_from_greedy(self) -> None:
    if self.simulation_result is None or self.road_network is None:
        return
    assignments = extract_vehicle_assignments(self.simulation_result)
    self.vehicle_genetic_states = {}
    self.vehicle_best_distance_history = {}
    for vehicle_id, tasks in assignments.items():
        state = initialize_vehicle_genetic(
            vehicle_id,
            tasks,
            self.road_network,
            population_size=self.settings.population_size,
        )
        self.vehicle_genetic_states[vehicle_id] = state
        self.vehicle_best_distance_history[vehicle_id] = [state.best_distance]
    self.generation_counter = 1
    self._rebuild_best_simulation_result()
    self.is_evolution_running = True
    if self.trip_selector is not None:
        self.trip_selector.set_enabled(True)
        trip_counts = {v.id: len(v.trips) for v in self.best_simulation_result.vehicles}
        self.trip_selector.set_vehicle_trip_counts(len(trip_counts), trip_counts)

def run_one_generation(self) -> None:
    if not self.is_evolution_running or self.road_network is None:
        return
    mutation_probability = self.mutation_slider.value
    for vehicle_id, state in self.vehicle_genetic_states.items():
        best_distance = run_vehicle_generation(
            state,
            self.road_network,
            mutation_probability,
            population_size=self.settings.population_size,
        )
        history = self.vehicle_best_distance_history.setdefault(vehicle_id, [])
        history.append(best_distance)
    self.generation_counter += 1
    self._rebuild_best_simulation_result()
```

- [ ] **Step 4: Wire Sortear and Simular**

In `shuffle_positions()` → call `self._reset_evolution()` at end (replace `clear_simulation_result` evolution parts).

Replace `run_delivery_simulation()` body tail:

```python
self.simulation_result = run_simulation(...)
self.result_lines = format_simulation_result(self.simulation_result)
self.status_message = None
self.start_evolution_from_greedy()
```

In `handle_control_events` → add `self.mutation_slider.handle_event(event)`.

In `clear_simulation_result` → also call `_reset_evolution()` or merge logic.

- [ ] **Step 5: Manual smoke (no automated test)**

Run: `python -c "from traveling_salesman_problem.simulation.simulation_state import SimulationState; s=SimulationState(); s.initialize(); print('ok')"`  
Expected: `ok`

- [ ] **Step 6: Commit**

```bash
git add traveling_salesman_problem/simulation/simulation_state.py
git commit -m "feat: add continuous per-vehicle GA evolution to simulation state"
```

---

### Task 8: Pygame loop + chart integration

**Files:**
- Modify: `traveling_salesman_problem/simulation/pygame_application.py`

**Interfaces:**
- Consumes: `draw_convergence_chart`, `simulation.run_one_generation()`, `simulation.best_simulation_result`, `simulation.vehicle_best_distance_history`, `simulation.is_evolution_running`

- [ ] **Step 1: Restore chart at top of sidebar**

Remove `draw_summary_panel` call (or pass zero height). Before sidebar scroll, blit chart:

```python
if simulation.vehicle_best_distance_history:
    series = [
        simulation.vehicle_best_distance_history[vehicle_id]
        for vehicle_id in sorted(simulation.vehicle_best_distance_history)
    ]
    labels = [f"V{vehicle_id}" for vehicle_id in sorted(simulation.vehicle_best_distance_history)]
    max_len = max(len(values) for values in series)
    generation_numbers = list(range(max_len))
    draw_convergence_chart(
        screen,
        generation_numbers,
        series,
        vertical_axis_label="Distância (px)",
        series_colors=VisualTheme.vehicle_route_colors,
        series_labels=labels,
    )
```

- [ ] **Step 2: Continuous generation in main loop**

After `simulation.update_controls()`:

```python
if simulation.is_evolution_running:
    simulation.run_one_generation()
```

- [ ] **Step 3: Map uses `best_simulation_result`**

Replace `simulation.simulation_result` with:

```python
active_result = simulation.best_simulation_result or simulation.simulation_result
```

Use `active_result` for routes, trip detail panel, trip selector counts.

- [ ] **Step 4: Draw mutation slider in sidebar**

In `_draw_scrollable_sidebar`, after connection radius slider:

```python
simulation.mutation_slider.draw(content_surface)
```

- [ ] **Step 5: Manual smoke test**

Run: `python main.py`  
Expected:
1. Sortear posições → map shows network
2. Simular → chart appears with N lines updating each frame
3. Map routes update as generations improve
4. Sortear again → chart resets

- [ ] **Step 6: Run full test suite**

Run: `python -m unittest discover tests -v`  
Expected: all PASS

- [ ] **Step 7: Commit**

```bash
git add traveling_salesman_problem/simulation/pygame_application.py
git commit -m "feat: wire continuous GA evolution and multi-line convergence chart"
```

---

## Spec Coverage Checklist

| Spec requirement | Task |
|------------------|------|
| DeliveryTask model | Task 1 |
| Greedy assignment extraction | Task 2 |
| Graph route evaluator + capacity | Task 3 |
| Per-vehicle GA (pop 100, elite 3, adjacent mutation) | Task 4 |
| Multi-line convergence chart | Task 5 |
| Mutation slider + settings | Task 6, 7 |
| Continuous loop after Simular | Task 7, 8 |
| Sortear resets evolution | Task 7 |
| Map shows best per-vehicle routes | Task 7, 8 |
| Tests | Tasks 1–5, 8 |

## Out of Scope (confirmed)

- Global multi-vehicle GA, 2-opt toggle, pause button, population slider, pygame automated tests

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-08-delivery-genetic-optimization.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks, fast iteration  
2. **Inline Execution** — execute tasks in this session with checkpoints

Which approach?
