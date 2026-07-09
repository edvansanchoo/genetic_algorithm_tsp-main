# Greedy Delivery Simulation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Pygame GA-TSP main flow with a greedy multi-vehicle delivery simulator (1–3 vehicles, 1–3 points, even item totals 2–14, capacity 10/trip) while preserving layout, widgets, and scroll sidebar.

**Architecture:** Pure domain logic in new top-level package `delivery_simulation/` (models, generators, routing, reporter). `traveling_salesman_problem/simulation/` becomes a thin Pygame orchestrator. GA code stays in repo but is removed from the main UI path.

**Tech Stack:** Python 3.9+, Pygame (UI), stdlib `unittest` + `pytest` (tests). No new dependencies.

## Global Constraints

- Entry point: `main.py` → `run_application()` (unchanged path)
- Vehicles: **1–3**; delivery points: **1–3**; item totals: **2, 4, 6, 8, 10, 12, 14** only
- Capacity: **10 items/trip**; partial delivery at same point allowed
- Distance: **Euclidean only**; no terrain/obstacles/penalties
- Depot: **randomized with points** on "Sortear posições"
- Buttons: **Sortear posições** (coords + orders) · **Simular** (routes only, requires prior shuffle)
- UI language: **Portuguese** (match existing widgets)
- Remove from UI: GA, convergence chart, obstacles, priority, hospital preset, 2-opt, scenario selector
- Preserve in repo untouched: `genetic_algorithm/*`, `demos/*`, `obstacles/*`
- Pygame integration tests: **out of scope** (manual validation)
- Spec reference: `docs/superpowers/specs/2026-07-08-greedy-delivery-simulation-design.md`

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `delivery_simulation/__init__.py` | Create | Package exports |
| `delivery_simulation/models.py` | Create | Domain dataclasses + constants |
| `delivery_simulation/distance.py` | Create | Euclidean distance |
| `delivery_simulation/order_generator.py` | Create | Random item distribution |
| `delivery_simulation/point_generator.py` | Create | Random depot + point coords |
| `delivery_simulation/routing.py` | Create | Greedy global algorithm |
| `delivery_simulation/assignment.py` | Create | Facade `run_simulation()` |
| `delivery_simulation/reporter.py` | Create | Text lines for sidebar |
| `tests/test_distance.py` | Create | Distance unit tests |
| `tests/test_order_generator.py` | Create | Order generator tests |
| `tests/test_point_generator.py` | Create | Point generator tests |
| `tests/test_routing.py` | Create | Routing + capacity tests |
| `tests/test_routing_multi_vehicle.py` | Create | Multi-vehicle tests |
| `traveling_salesman_problem/config/application_settings.py` | Modify | Delivery defaults, remove GA params |
| `traveling_salesman_problem/config/visual_theme.py` | Modify | Vehicle route colors |
| `traveling_salesman_problem/visualization/widgets/discrete_slider.py` | Create | Even-step item slider |
| `traveling_salesman_problem/visualization/widgets/__init__.py` | Modify | Export `DiscreteSlider` |
| `traveling_salesman_problem/simulation/simulation_state.py` | Modify | Replace GA state with delivery state |
| `traveling_salesman_problem/visualization/map_renderer.py` | Modify | Depot, points, vehicle routes |
| `traveling_salesman_problem/visualization/application_layout.py` | Modify | Summary + results panels |
| `traveling_salesman_problem/simulation/pygame_application.py` | Modify | Static loop, no GA/convergence |

---

### Task 1: Domain models and distance

**Files:**
- Create: `delivery_simulation/__init__.py`
- Create: `delivery_simulation/models.py`
- Create: `delivery_simulation/distance.py`
- Create: `tests/test_distance.py`

**Interfaces:**
- Consumes: nothing
- Produces:
  - `Coordinate = Tuple[float, float]`
  - `MAX_CAPACITY = 10`
  - `VALID_TOTAL_ITEMS = (2, 4, 6, 8, 10, 12, 14)`
  - `DEPOT_ID = "DEPOT"`
  - Dataclasses: `DeliveryPoint`, `Stop`, `Trip`, `Vehicle`, `SimulationConfig`, `SimulationResult`
  - `euclidean(a: Coordinate, b: Coordinate) -> float`

- [ ] **Step 1: Write the failing test**

Create `tests/test_distance.py`:

```python
import math
import unittest

from delivery_simulation.distance import euclidean


class EuclideanDistanceTests(unittest.TestCase):
    def test_horizontal_segment(self):
        self.assertAlmostEqual(euclidean((0, 0), (3, 0)), 3.0)

    def test_diagonal_3_4_5(self):
        self.assertAlmostEqual(euclidean((0, 0), (3, 4)), 5.0)

    def test_same_point_is_zero(self):
        self.assertAlmostEqual(euclidean((100, 200), (100, 200)), 0.0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_distance.py -v`  
Expected: FAIL — `ModuleNotFoundError: delivery_simulation`

- [ ] **Step 3: Write minimal implementation**

Create `delivery_simulation/__init__.py`:

```python
"""Simulador guloso de distribuição de entregas."""
```

Create `delivery_simulation/models.py`:

```python
"""Modelos de domínio do simulador de entregas."""

from dataclasses import dataclass, field
from typing import List, Tuple

Coordinate = Tuple[float, float]

MAX_CAPACITY = 10
VALID_TOTAL_ITEMS = (2, 4, 6, 8, 10, 12, 14)
DEPOT_ID = "DEPOT"
POINT_IDS = ("A", "B", "C")


@dataclass
class DeliveryPoint:
    id: str
    coordinate: Coordinate
    total_items: int
    remaining_items: int


@dataclass
class Stop:
    point_id: str
    items_delivered: int


@dataclass
class Trip:
    stops: List[Stop]
    distance: float


@dataclass
class Vehicle:
    id: int
    current_position: Coordinate
    current_load: int
    trips: List[Trip] = field(default_factory=list)
    assigned_points: List[str] = field(default_factory=list)


@dataclass
class SimulationConfig:
    vehicle_count: int
    delivery_point_count: int
    total_items: int


@dataclass
class SimulationResult:
    config: SimulationConfig
    depot: Coordinate
    delivery_points: List[DeliveryPoint]
    vehicles: List[Vehicle]
    total_system_distance: float
```

Create `delivery_simulation/distance.py`:

```python
"""Cálculo de distância euclidiana."""

import math

from delivery_simulation.models import Coordinate


def euclidean(point_a: Coordinate, point_b: Coordinate) -> float:
    delta_x = point_b[0] - point_a[0]
    delta_y = point_b[1] - point_a[1]
    return math.hypot(delta_x, delta_y)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_distance.py -v`  
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add delivery_simulation/ tests/test_distance.py
git commit -m "feat: add delivery simulation domain models and distance"
```

---

### Task 2: Order generator

**Files:**
- Create: `delivery_simulation/order_generator.py`
- Create: `tests/test_order_generator.py`

**Interfaces:**
- Consumes: `POINT_IDS`, `VALID_TOTAL_ITEMS` from `models.py`
- Produces: `distribute_items(total_items: int, point_count: int, rng: random.Random | None = None) -> dict[str, int]`

- [ ] **Step 1: Write the failing test**

Create `tests/test_order_generator.py`:

```python
import random
import unittest

from delivery_simulation.models import VALID_TOTAL_ITEMS
from delivery_simulation.order_generator import distribute_items


class OrderGeneratorTests(unittest.TestCase):
    def test_sum_equals_total_for_all_valid_totals(self):
        for total in VALID_TOTAL_ITEMS:
            for point_count in (1, 2, 3):
                with self.subTest(total=total, point_count=point_count):
                    orders = distribute_items(total, point_count, rng=random.Random(42))
                    self.assertEqual(len(orders), point_count)
                    self.assertEqual(sum(orders.values()), total)
                    self.assertTrue(all(value >= 0 for value in orders.values()))

    def test_zero_items_allowed_on_some_points(self):
        orders = distribute_items(2, 3, rng=random.Random(0))
        self.assertEqual(sum(orders.values()), 2)

    def test_reproducible_with_seed(self):
        first = distribute_items(14, 3, rng=random.Random(99))
        second = distribute_items(14, 3, rng=random.Random(99))
        self.assertEqual(first, second)

    def test_single_point_gets_all_items(self):
        orders = distribute_items(8, 1, rng=random.Random(1))
        self.assertEqual(orders, {"A": 8})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_order_generator.py -v`  
Expected: FAIL — `ModuleNotFoundError: order_generator`

- [ ] **Step 3: Write minimal implementation**

Create `delivery_simulation/order_generator.py`:

```python
"""Distribuição aleatória de itens entre pontos de entrega."""

import random
from typing import Dict, Optional

from delivery_simulation.models import POINT_IDS


def distribute_items(
    total_items: int,
    point_count: int,
    rng: Optional[random.Random] = None,
) -> Dict[str, int]:
    if point_count < 1 or point_count > len(POINT_IDS):
        raise ValueError(f"point_count deve estar entre 1 e {len(POINT_IDS)}")

    random_source = rng or random.Random()
    point_ids = POINT_IDS[:point_count]
    orders = {point_id: 0 for point_id in point_ids}

    for _ in range(total_items):
        chosen_id = random_source.choice(point_ids)
        orders[chosen_id] += 1

    return orders
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_order_generator.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delivery_simulation/order_generator.py tests/test_order_generator.py
git commit -m "feat: add random order distribution for delivery points"
```

---

### Task 3: Point generator

**Files:**
- Create: `delivery_simulation/point_generator.py`
- Create: `tests/test_point_generator.py`

**Interfaces:**
- Consumes: `POINT_IDS` from `models.py`
- Produces:
  ```python
  def generate_depot_and_points(
      point_count: int,
      map_min_x: float,
      map_min_y: float,
      map_max_x: float,
      map_max_y: float,
      min_separation: float = 30.0,
      max_attempts: int = 100,
      rng: random.Random | None = None,
  ) -> tuple[Coordinate, list[tuple[str, Coordinate]]]
  ```

- [ ] **Step 1: Write the failing test**

Create `tests/test_point_generator.py`:

```python
import math
import random
import unittest

from delivery_simulation.point_generator import generate_depot_and_points


class PointGeneratorTests(unittest.TestCase):
    def test_returns_depot_and_requested_point_count(self):
        depot, points = generate_depot_and_points(
            point_count=3,
            map_min_x=100,
            map_min_y=100,
            map_max_x=500,
            map_max_y=400,
            rng=random.Random(7),
        )
        self.assertEqual(len(points), 3)
        self.assertEqual([point_id for point_id, _ in points], ["A", "B", "C"])
        self.assertEqual(len(depot), 2)

    def test_coordinates_inside_map_bounds(self):
        depot, points = generate_depot_and_points(
            point_count=2,
            map_min_x=100,
            map_min_y=100,
            map_max_x=500,
            map_max_y=400,
            rng=random.Random(3),
        )
        all_coords = [depot] + [coord for _, coord in points]
        for x, y in all_coords:
            self.assertGreaterEqual(x, 100)
            self.assertLessEqual(x, 500)
            self.assertGreaterEqual(y, 100)
            self.assertLessEqual(y, 400)

    def test_minimum_separation_between_all_points(self):
        depot, points = generate_depot_and_points(
            point_count=3,
            map_min_x=0,
            map_min_y=0,
            map_max_x=1000,
            map_max_y=1000,
            min_separation=30.0,
            rng=random.Random(11),
        )
        coords = [depot] + [coord for _, coord in points]
        for index_a, coord_a in enumerate(coords):
            for coord_b in coords[index_a + 1:]:
                distance = math.hypot(coord_b[0] - coord_a[0], coord_b[1] - coord_a[1])
                self.assertGreaterEqual(distance, 30.0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_point_generator.py -v`  
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

Create `delivery_simulation/point_generator.py`:

```python
"""Geração aleatória de coordenadas da distribuidora e pontos de entrega."""

import random
from typing import List, Optional, Tuple

from delivery_simulation.models import Coordinate, POINT_IDS


def _random_coordinate(
    map_min_x: float,
    map_min_y: float,
    map_max_x: float,
    map_max_y: float,
    rng: random.Random,
) -> Coordinate:
    x = rng.uniform(map_min_x, map_max_x)
    y = rng.uniform(map_min_y, map_max_y)
    return (x, y)


def _is_far_enough(candidate: Coordinate, existing: List[Coordinate], min_separation: float) -> bool:
    for existing_coordinate in existing:
        delta_x = candidate[0] - existing_coordinate[0]
        delta_y = candidate[1] - existing_coordinate[1]
        if (delta_x * delta_x + delta_y * delta_y) ** 0.5 < min_separation:
            return False
    return True


def generate_depot_and_points(
    point_count: int,
    map_min_x: float,
    map_min_y: float,
    map_max_x: float,
    map_max_y: float,
    min_separation: float = 30.0,
    max_attempts: int = 100,
    rng: Optional[random.Random] = None,
) -> Tuple[Coordinate, List[Tuple[str, Coordinate]]]:
    if point_count < 1 or point_count > len(POINT_IDS):
        raise ValueError(f"point_count deve estar entre 1 e {len(POINT_IDS)}")

    random_source = rng or random.Random()
    placed: List[Coordinate] = []
    labels = POINT_IDS[:point_count]

    for _ in range(max_attempts):
        depot = _random_coordinate(map_min_x, map_min_y, map_max_x, map_max_y, random_source)
        placed = [depot]
        point_coordinates: List[Tuple[str, Coordinate]] = []
        success = True

        for label in labels:
            point_found = False
            for _attempt in range(max_attempts):
                candidate = _random_coordinate(
                    map_min_x, map_min_y, map_max_x, map_max_y, random_source
                )
                if _is_far_enough(candidate, placed, min_separation):
                    placed.append(candidate)
                    point_coordinates.append((label, candidate))
                    point_found = True
                    break
            if not point_found:
                success = False
                break

        if success:
            return depot, point_coordinates

    raise RuntimeError("Não foi possível posicionar distribuidora e pontos sem sobreposição")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_point_generator.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delivery_simulation/point_generator.py tests/test_point_generator.py
git commit -m "feat: add depot and delivery point coordinate generator"
```

---

### Task 4: Greedy routing engine

**Files:**
- Create: `delivery_simulation/routing.py`
- Create: `tests/test_routing.py`
- Create: `tests/test_routing_multi_vehicle.py`

**Interfaces:**
- Consumes: `euclidean`, all models, `DEPOT_ID`, `MAX_CAPACITY`
- Produces: `run_greedy_simulation(config: SimulationConfig, depot: Coordinate, delivery_points: List[DeliveryPoint]) -> SimulationResult`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_routing.py`:

```python
import unittest

from delivery_simulation.models import DeliveryPoint, SimulationConfig
from delivery_simulation.routing import run_greedy_simulation


class GreedyRoutingTests(unittest.TestCase):
    def _make_points(self, spec: dict[str, tuple[tuple[float, float], int]]) -> list[DeliveryPoint]:
        return [
            DeliveryPoint(
                id=point_id,
                coordinate=coordinate,
                total_items=item_count,
                remaining_items=item_count,
            )
            for point_id, (coordinate, item_count) in spec.items()
        ]

    def test_single_vehicle_abc_example_produces_two_trips(self):
        depot = (0.0, 0.0)
        points = self._make_points(
            {
                "A": ((1.0, 0.0), 6),
                "B": ((10.0, 0.0), 8),
                "C": ((2.0, 1.0), 2),
            }
        )
        config = SimulationConfig(vehicle_count=1, delivery_point_count=3, total_items=16)

        result = run_greedy_simulation(config, depot, points)
        vehicle = result.vehicles[0]

        self.assertEqual(len(vehicle.trips), 2)
        first_route = [stop.point_id for stop in vehicle.trips[0].stops]
        second_route = [stop.point_id for stop in vehicle.trips[1].stops]
        self.assertEqual(first_route, ["DEPOT", "A", "C", "DEPOT"])
        self.assertEqual(second_route, ["DEPOT", "B", "DEPOT"])
        self.assertTrue(all(point.remaining_items == 0 for point in result.delivery_points))

    def test_partial_delivery_when_point_exceeds_capacity(self):
        depot = (0.0, 0.0)
        points = self._make_points({"A": ((5.0, 0.0), 14)})
        config = SimulationConfig(vehicle_count=1, delivery_point_count=1, total_items=14)

        result = run_greedy_simulation(config, depot, points)
        vehicle = result.vehicles[0]

        self.assertEqual(len(vehicle.trips), 2)
        delivered = [
            (stop.point_id, stop.items_delivered)
            for trip in vehicle.trips
            for stop in trip.stops
            if stop.point_id != "DEPOT"
        ]
        self.assertEqual(delivered, [("A", 10), ("A", 4)])

    def test_all_trips_start_and_end_at_depot(self):
        depot = (0.0, 0.0)
        points = self._make_points({"A": ((3.0, 0.0), 4), "B": ((0.0, 4.0), 4)})
        config = SimulationConfig(vehicle_count=1, delivery_point_count=2, total_items=8)

        result = run_greedy_simulation(config, depot, points)

        for vehicle in result.vehicles:
            for trip in vehicle.trips:
                self.assertEqual(trip.stops[0].point_id, "DEPOT")
                self.assertEqual(trip.stops[-1].point_id, "DEPOT")
                self.assertGreater(trip.distance, 0.0)
```

Create `tests/test_routing_multi_vehicle.py`:

```python
import unittest

from delivery_simulation.models import DeliveryPoint, SimulationConfig
from delivery_simulation.routing import run_greedy_simulation


class MultiVehicleRoutingTests(unittest.TestCase):
    def test_two_vehicles_share_pending_deliveries(self):
        depot = (0.0, 0.0)
        points = [
            DeliveryPoint("A", (1.0, 0.0), 4, 4),
            DeliveryPoint("B", (100.0, 0.0), 4, 4),
        ]
        config = SimulationConfig(vehicle_count=2, delivery_point_count=2, total_items=8)

        result = run_greedy_simulation(config, depot, points)

        self.assertEqual(len(result.vehicles), 2)
        self.assertTrue(all(point.remaining_items == 0 for point in result.delivery_points))
        assigned_union = set(result.vehicles[0].assigned_points + result.vehicles[1].assigned_points)
        self.assertEqual(assigned_union, {"A", "B"})

    def test_never_exceeds_capacity_per_trip(self):
        depot = (0.0, 0.0)
        points = [
            DeliveryPoint("A", (1.0, 0.0), 6, 6),
            DeliveryPoint("B", (2.0, 0.0), 6, 6),
        ]
        config = SimulationConfig(vehicle_count=2, delivery_point_count=2, total_items=12)

        result = run_greedy_simulation(config, depot, points)

        for vehicle in result.vehicles:
            for trip in vehicle.trips:
                load = 0
                for stop in trip.stops:
                    if stop.point_id != "DEPOT":
                        load += stop.items_delivered
                self.assertLessEqual(load, 10)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_routing.py tests/test_routing_multi_vehicle.py -v`  
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

Create `delivery_simulation/routing.py`:

```python
"""Algoritmo guloso global com capacidade por viagem."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from delivery_simulation.distance import euclidean
from delivery_simulation.models import (
    DEPOT_ID,
    MAX_CAPACITY,
    Coordinate,
    DeliveryPoint,
    SimulationConfig,
    SimulationResult,
    Stop,
    Trip,
    Vehicle,
)


@dataclass
class _ActiveTrip:
    stops: List[Stop] = field(default_factory=list)
    distance: float = 0.0


@dataclass(order=True)
class _Candidate:
    distance: float
    vehicle_id: int
    point_id: str
    delivery_amount: int = field(compare=False)


def _clone_points(delivery_points: List[DeliveryPoint]) -> List[DeliveryPoint]:
    return [
        DeliveryPoint(
            id=point.id,
            coordinate=point.coordinate,
            total_items=point.total_items,
            remaining_items=point.total_items,
        )
        for point in delivery_points
    ]


def _pending_points(points: List[DeliveryPoint]) -> List[DeliveryPoint]:
    return [point for point in points if point.remaining_items > 0]


def _append_depot_return(active_trip: _ActiveTrip, vehicle: Vehicle, depot: Coordinate) -> None:
    if vehicle.current_position == depot:
        active_trip.stops.append(Stop(DEPOT_ID, 0))
        return
    segment_distance = euclidean(vehicle.current_position, depot)
    active_trip.distance += segment_distance
    active_trip.stops.append(Stop(DEPOT_ID, 0))
    vehicle.current_position = depot


def _finalize_trip(vehicle: Vehicle, active_trip: Optional[_ActiveTrip]) -> None:
    if active_trip is None or not active_trip.stops:
        return
    vehicle.trips.append(Trip(stops=list(active_trip.stops), distance=active_trip.distance))


def run_greedy_simulation(
    config: SimulationConfig,
    depot: Coordinate,
    delivery_points: List[DeliveryPoint],
) -> SimulationResult:
    points = _clone_points(delivery_points)
    vehicles = [
        Vehicle(id=index + 1, current_position=depot, current_load=0)
        for index in range(config.vehicle_count)
    ]
    active_trips: Dict[int, Optional[_ActiveTrip]] = {vehicle.id: None for vehicle in vehicles}

    while _pending_points(points):
        candidates: List[_Candidate] = []

        for vehicle in vehicles:
            remaining_capacity = MAX_CAPACITY - vehicle.current_load
            pending = _pending_points(points)

            can_deliver = any(
                min(remaining_capacity, point.remaining_items) > 0 for point in pending
            )

            if remaining_capacity == 0 or not can_deliver:
                if vehicle.current_position != depot or vehicle.current_load > 0:
                    candidates.append(
                        _Candidate(
                            euclidean(vehicle.current_position, depot),
                            vehicle.id,
                            DEPOT_ID,
                            0,
                        )
                    )
                continue

            for point in pending:
                delivery_amount = min(remaining_capacity, point.remaining_items)
                if delivery_amount <= 0:
                    continue
                candidates.append(
                    _Candidate(
                        euclidean(vehicle.current_position, point.coordinate),
                        vehicle.id,
                        point.id,
                        delivery_amount,
                    )
                )

        if not candidates:
            raise RuntimeError("Nenhum candidato disponível com entregas pendentes")

        chosen = min(candidates)
        vehicle = vehicles[chosen.vehicle_id - 1]

        if chosen.point_id == DEPOT_ID:
            active_trip = active_trips[vehicle.id]
            if active_trip is not None:
                _append_depot_return(active_trip, vehicle, depot)
                _finalize_trip(vehicle, active_trip)
            active_trips[vehicle.id] = None
            vehicle.current_load = 0
            continue

        point = next(item for item in points if item.id == chosen.point_id)
        active_trip = active_trips[vehicle.id]
        if active_trip is None:
            active_trip = _ActiveTrip(stops=[Stop(DEPOT_ID, 0)], distance=0.0)
            active_trips[vehicle.id] = active_trip

        segment_distance = euclidean(vehicle.current_position, point.coordinate)
        active_trip.distance += segment_distance
        active_trip.stops.append(Stop(point.id, chosen.delivery_amount))

        vehicle.current_position = point.coordinate
        vehicle.current_load += chosen.delivery_amount
        point.remaining_items -= chosen.delivery_amount

        if point.id not in vehicle.assigned_points:
            vehicle.assigned_points.append(point.id)

    for vehicle in vehicles:
        active_trip = active_trips[vehicle.id]
        if active_trip is not None:
            _append_depot_return(active_trip, vehicle, depot)
            _finalize_trip(vehicle, active_trip)
            active_trips[vehicle.id] = None
        vehicle.current_load = 0

    total_system_distance = sum(
        trip.distance for vehicle in vehicles for trip in vehicle.trips
    )

    final_points = [
        DeliveryPoint(
            id=point.id,
            coordinate=point.coordinate,
            total_items=point.total_items,
            remaining_items=0,
        )
        for point in points
    ]

    return SimulationResult(
        config=config,
        depot=depot,
        delivery_points=final_points,
        vehicles=vehicles,
        total_system_distance=total_system_distance,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_routing.py tests/test_routing_multi_vehicle.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delivery_simulation/routing.py tests/test_routing.py tests/test_routing_multi_vehicle.py
git commit -m "feat: add greedy multi-vehicle routing with trip capacity"
```

---

### Task 5: Assignment facade and reporter

**Files:**
- Create: `delivery_simulation/assignment.py`
- Create: `delivery_simulation/reporter.py`

**Interfaces:**
- Consumes: `run_greedy_simulation`, all models
- Produces:
  - `run_simulation(config, depot, delivery_points) -> SimulationResult`
  - `format_simulation_result(result: SimulationResult) -> list[str]`
  - `count_total_trips(result: SimulationResult) -> int`

- [ ] **Step 1: Write minimal implementation** (pure formatting — no separate test file required beyond routing tests)

Create `delivery_simulation/assignment.py`:

```python
"""Facade de simulação."""

from typing import List

from delivery_simulation.models import Coordinate, DeliveryPoint, SimulationConfig, SimulationResult
from delivery_simulation.routing import run_greedy_simulation


def run_simulation(
    config: SimulationConfig,
    depot: Coordinate,
    delivery_points: List[DeliveryPoint],
) -> SimulationResult:
    return run_greedy_simulation(config, depot, delivery_points)
```

Create `delivery_simulation/reporter.py`:

```python
"""Formatação textual dos resultados."""

from delivery_simulation.models import DEPOT_ID, SimulationResult


def count_total_trips(result: SimulationResult) -> int:
    return sum(len(vehicle.trips) for vehicle in result.vehicles)


def _format_stop_chain(stops) -> str:
    parts = []
    for stop in stops:
        if stop.point_id == DEPOT_ID:
            parts.append("D")
        else:
            parts.append(f"{stop.point_id}({stop.items_delivered})")
    return " → ".join(parts)


def format_simulation_result(result: SimulationResult) -> list[str]:
    config = result.config
    lines = [
        "── Configuração ──",
        f"Veículos: {config.vehicle_count} | Pontos: {config.delivery_point_count} | Itens: {config.total_items}",
        "",
        "── Pontos ──",
    ]

    for point in result.delivery_points:
        x, y = point.coordinate
        lines.append(f"{point.id} ({x:.0f}, {y:.0f}): {point.total_items} itens")

    for vehicle in result.vehicles:
        vehicle_distance = sum(trip.distance for trip in vehicle.trips)
        assigned = ", ".join(vehicle.assigned_points) if vehicle.assigned_points else "—"
        lines.extend(
            [
                "",
                f"── Veículo {vehicle.id} ({len(vehicle.trips)} viagens, {vehicle_distance:.0f} px) ──",
                f"Entregas: {assigned}",
            ]
        )
        for trip_index, trip in enumerate(vehicle.trips, start=1):
            route_text = _format_stop_chain(trip.stops)
            lines.append(f"  Viagem {trip_index}: {route_text}  [{trip.distance:.0f} px]")

    lines.extend(["", f"── Total do sistema: {result.total_system_distance:.0f} px ──"])
    return lines
```

Update `delivery_simulation/__init__.py` exports:

```python
from delivery_simulation.assignment import run_simulation
from delivery_simulation.models import (
    DeliveryPoint,
    SimulationConfig,
    SimulationResult,
    VALID_TOTAL_ITEMS,
)
from delivery_simulation.order_generator import distribute_items
from delivery_simulation.point_generator import generate_depot_and_points
from delivery_simulation.reporter import count_total_trips, format_simulation_result

__all__ = [
    "DeliveryPoint",
    "SimulationConfig",
    "SimulationResult",
    "VALID_TOTAL_ITEMS",
    "count_total_trips",
    "distribute_items",
    "format_simulation_result",
    "generate_depot_and_points",
    "run_simulation",
]
```

- [ ] **Step 2: Smoke test reporter in Python REPL**

Run:
```bash
python -c "from delivery_simulation.reporter import format_simulation_result; print('ok')"
```
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add delivery_simulation/
git commit -m "feat: add simulation facade and result reporter"
```

---

### Task 6: DiscreteSlider widget

**Files:**
- Create: `traveling_salesman_problem/visualization/widgets/discrete_slider.py`
- Modify: `traveling_salesman_problem/visualization/widgets/__init__.py`

**Interfaces:**
- Consumes: `MutationSlider` base behavior
- Produces:
  ```python
  class DiscreteSlider(MutationSlider):
      allowed_values: tuple[int, ...]
      def snap_to_nearest(self) -> None
      @property
      def selected_value(self) -> int
  ```

- [ ] **Step 1: Create widget**

Create `traveling_salesman_problem/visualization/widgets/discrete_slider.py`:

```python
"""Slider com valores discretos pré-definidos."""

from typing import Tuple

from traveling_salesman_problem.visualization.widgets.mutation_slider import MutationSlider


class DiscreteSlider(MutationSlider):
    def __init__(
        self,
        position_x: int,
        position_y: int,
        width: int,
        height: int,
        value: int,
        allowed_values: Tuple[int, ...],
        label: str,
    ) -> None:
        if not allowed_values:
            raise ValueError("allowed_values não pode ser vazio")
        self.allowed_values = allowed_values
        minimum = float(min(allowed_values))
        maximum = float(max(allowed_values))
        super().__init__(
            position_x,
            position_y,
            width,
            height,
            float(value),
            minimum,
            maximum,
            label,
            "",
        )
        self.snap_to_nearest()

    def snap_to_nearest(self) -> None:
        nearest = min(self.allowed_values, key=lambda item: abs(item - self.value))
        self.value = float(nearest)

    @property
    def selected_value(self) -> int:
        return int(self.value)

    def handle_event(self, event) -> None:
        super().handle_event(event)
        if event.type == getattr(__import__("pygame"), "MOUSEBUTTONUP", None):
            self.snap_to_nearest()
```

Update `traveling_salesman_problem/visualization/widgets/__init__.py` — add import and export `DiscreteSlider`.

- [ ] **Step 2: Commit**

```bash
git add traveling_salesman_problem/visualization/widgets/
git commit -m "feat: add discrete slider widget for even item totals"
```

---

### Task 7: ApplicationSettings cleanup

**Files:**
- Modify: `traveling_salesman_problem/config/application_settings.py`

**Interfaces:**
- Produces new defaults:
  - `initial_vehicle_count = 1`
  - `initial_delivery_point_count = 2`
  - `initial_total_items = 6`
- Removes: `number_of_cities`, `population_size`, `initial_mutation_probability`, `initial_priority_weight`, `initial_tree_count`, `initial_lake_count`, `maximum_terrain_features_per_type`, `scenario_selector_viewport_height`

- [ ] **Step 1: Replace GA settings with delivery settings**

Replace dataclass fields in `application_settings.py`:

```python
@dataclass(frozen=True)
class ApplicationSettings:
    window_width: int = 1120
    window_height: int = 940
    frames_per_second: int = 30

    initial_vehicle_count: int = 1
    initial_delivery_point_count: int = 2
    initial_total_items: int = 6

    map_margin: int = 20
    delivery_point_radius: int = 9
    depot_half_size: int = 7

    count_slider_height: int = 48
    action_button_height: int = 36
    summary_panel_height: int = 400
```

Keep existing computed properties (`plot_horizontal_offset`, `map_minimum_x`, etc.) unchanged.

- [ ] **Step 2: Commit**

```bash
git add traveling_salesman_problem/config/application_settings.py
git commit -m "refactor: replace GA settings with delivery simulation defaults"
```

---

### Task 8: SimulationState rewrite

**Files:**
- Modify: `traveling_salesman_problem/simulation/simulation_state.py`

**Interfaces:**
- Consumes: all `delivery_simulation` exports, `IntegerSlider`, `DiscreteSlider`, `ActionButton`, `VALID_TOTAL_ITEMS`
- Produces state fields and methods:
  ```python
  depot: Coordinate | None
  delivery_points: list[DeliveryPoint]
  positions_ready: bool
  simulation_result: SimulationResult | None
  result_lines: list[str]

  def shuffle_positions(self) -> None
  def run_delivery_simulation(self) -> None
  def clear_simulation_result(self) -> None
  def build_simulation_config(self) -> SimulationConfig
  def can_simulate(self) -> bool
  ```

- [ ] **Step 1: Rewrite simulation_state.py**

Key implementation points:

1. Remove all GA, obstacle, priority, scenario imports and fields.
2. Add delivery fields (`depot`, `delivery_points`, `simulation_result`, `result_lines`, `positions_ready`).
3. `_create_control_widgets()` layout:
   - `section_summary_y = 0` (reserved — drawn by layout, not widgets)
   - `section_config_y = 0`
   - Sliders: `vehicle_count_slider` (1–3), `delivery_point_count_slider` (1–3), `total_items_slider` (`DiscreteSlider` with `VALID_TOTAL_ITEMS`)
   - `section_actions_y`
   - Buttons: `shuffle_positions_button` ("Sortear posições"), `simulate_button` ("Simular")
   - `section_results_y`
4. `initialize()` → `_create_control_widgets()` only; `positions_ready = False`.
5. `shuffle_positions()`:
   ```python
   depot, generated = generate_depot_and_points(
       self.delivery_point_count_slider.integer_value,
       settings.map_minimum_x, settings.map_minimum_y,
       settings.map_maximum_x, settings.map_maximum_y,
   )
   orders = distribute_items(self.total_items_slider.selected_value, len(generated))
   self.depot = depot
   self.delivery_points = [
       DeliveryPoint(id=label, coordinate=coord, total_items=orders[label], remaining_items=orders[label])
       for label, coord in generated
   ]
   self.positions_ready = True
   self.clear_simulation_result()
   ```
6. `run_delivery_simulation()`:
   ```python
   if not self.can_simulate():
       return
   config = self.build_simulation_config()
   self.simulation_result = run_simulation(config, self.depot, self.delivery_points)
   self.result_lines = format_simulation_result(self.simulation_result)
   ```
7. `handle_control_events()` — wire sliders + buttons; on slider change call `clear_simulation_result()`; if delivery point count changed also set `positions_ready = False`.
8. `update_controls()` (rename from `update_terrain_counts_if_changed`):
   - shuffle button → `shuffle_positions()`
   - simulate button → `run_delivery_simulation()`
9. `calculate_scrollable_content_height()` based on `len(result_lines)`.

- [ ] **Step 2: Commit**

```bash
git add traveling_salesman_problem/simulation/simulation_state.py
git commit -m "refactor: replace GA simulation state with delivery simulation state"
```

---

### Task 9: Visual theme and map renderer

**Files:**
- Modify: `traveling_salesman_problem/config/visual_theme.py`
- Modify: `traveling_salesman_problem/visualization/map_renderer.py`

**Interfaces:**
- Produces:
  - `VisualTheme.vehicle_route_colors: tuple[tuple[int,int,int], ...]`
  - `draw_depot(screen, depot, half_size) -> None`
  - `draw_delivery_points(screen, points, radius) -> None`
  - `draw_vehicle_routes(screen, result, colors) -> None`
  - `draw_vehicle_legend(screen, vehicle_count, colors, map_bounds) -> None`

- [ ] **Step 1: Add vehicle colors to VisualTheme**

```python
vehicle_route_colors = (
    route_best,           # (37, 99, 235)
    (234, 88, 12),        # laranja
    success,              # (22, 163, 74)
)
depot_fill = (30, 64, 175)
depot_stroke = (255, 255, 255)
```

- [ ] **Step 2: Replace map_renderer drawing functions**

Remove imports/usages of `draw_terrain_features`, `draw_cities`, priority colors, obstacle types.

Add:

```python
def draw_depot(screen, depot: Coordinate, half_size: int) -> None:
    x, y = depot
    rect = pygame.Rect(int(x - half_size), int(y - half_size), half_size * 2, half_size * 2)
    pygame.draw.rect(screen, VisualTheme.depot_stroke, rect.inflate(4, 4))
    pygame.draw.rect(screen, VisualTheme.depot_fill, rect)
    label = get_user_interface_font(11, bold=True).render("D", True, VisualTheme.text_inverse)
    screen.blit(label, label.get_rect(center=rect.center))


def draw_delivery_points(screen, delivery_points, radius) -> None:
    for point in delivery_points:
        center = (int(point.coordinate[0]), int(point.coordinate[1]))
        pygame.draw.circle(screen, VisualTheme.city_stroke, center, radius + 2)
        pygame.draw.circle(screen, VisualTheme.city_fill, center, radius)
        # label + item count (see spec)


def draw_vehicle_routes(screen, simulation_result, base_colors) -> None:
    for vehicle_index, vehicle in enumerate(simulation_result.vehicles):
        color = base_colors[vehicle_index % len(base_colors)]
        for trip_index, trip in enumerate(vehicle.trips):
            coordinates = [_coordinate_for_stop(stop, simulation_result) for stop in trip.stops]
            alpha_color = color if trip_index % 2 == 0 else tuple(max(0, c - 40) for c in color)
            _draw_open_route(screen, coordinates, alpha_color)
            draw_route_direction_arrows(screen, coordinates, alpha_color)
```

Implement helper `_coordinate_for_stop` mapping `DEPOT` → `result.depot`, else lookup point coordinate.

- [ ] **Step 3: Commit**

```bash
git add traveling_salesman_problem/config/visual_theme.py traveling_salesman_problem/visualization/map_renderer.py
git commit -m "feat: add depot, delivery point, and multi-vehicle route rendering"
```

---

### Task 10: Application layout — summary and results panels

**Files:**
- Modify: `traveling_salesman_problem/visualization/application_layout.py`

**Interfaces:**
- Produces:
  - `draw_summary_panel(screen, total_distance, total_trips, has_result) -> None`
  - `draw_results_panel(screen, result_lines, x, y, width) -> int` (returns next Y)

- [ ] **Step 1: Remove GA-specific functions**

Remove or stop using: `draw_map_header` GA metrics params, `draw_delivery_order_panel`, priority legend helpers tied to GA.

- [ ] **Step 2: Add summary panel** (replaces convergence chart area at top of sidebar)

```python
def draw_summary_panel(
    screen: pygame.Surface,
    position_x: int,
    position_y: int,
    width: int,
    height: int,
    total_distance: float | None,
    total_trips: int | None,
) -> None:
    draw_card(screen, pygame.Rect(position_x, position_y, width, height))
    title_font = get_user_interface_font(13, bold=True)
    body_font = get_monospace_font(12)

    screen.blit(title_font.render("Resumo", True, VisualTheme.text_primary), (position_x + 12, position_y + 12))

    distance_text = f"{total_distance:.0f} px" if total_distance is not None else "---"
    trips_text = str(total_trips) if total_trips is not None else "---"

    screen.blit(body_font.render(f"Distância total: {distance_text}", True, VisualTheme.text_primary), (position_x + 12, position_y + 44))
    screen.blit(body_font.render(f"Viagens: {trips_text}", True, VisualTheme.text_primary), (position_x + 12, position_y + 64))
```

- [ ] **Step 3: Add results panel**

Render each line from `result_lines` in monospace at 14px line height; return final Y for scroll height calculation.

- [ ] **Step 4: Add simplified map header**

```python
def draw_delivery_map_header(
    screen: pygame.Surface,
    map_start_x: int,
    window_width: int,
    total_distance: float | None,
) -> None:
    # Title: "Simulador de Entregas · Roteamento Guloso"
    # Subtitle: distância total or "Configure e simule"
```

- [ ] **Step 5: Commit**

```bash
git add traveling_salesman_problem/visualization/application_layout.py
git commit -m "feat: add delivery summary and results panels to sidebar layout"
```

---

### Task 11: Pygame application loop rewrite

**Files:**
- Modify: `traveling_salesman_problem/simulation/pygame_application.py`

**Interfaces:**
- Consumes: updated `SimulationState`, new layout + map renderer functions

- [ ] **Step 1: Rewrite `_draw_scrollable_sidebar`**

Draw sections:
1. Summary panel (fixed, outside scroll OR at top of scroll — use fixed summary at `controls_top_position - summary_panel_height` or integrate at scroll top per spec)
2. CONFIGURAÇÃO — 3 sliders
3. AÇÕES — 2 buttons
4. RESULTADO — `draw_results_panel` with `simulation.result_lines`

- [ ] **Step 2: Rewrite main loop**

Remove:
- `draw_convergence_chart`
- `run_one_generation()`
- `build_delivery_visit_order`
- terrain drawing
- second-best route drawing

Add:
```python
simulation.update_controls()

draw_application_chrome(...)
draw_delivery_map_header(
    screen,
    settings.plot_horizontal_offset,
    settings.window_width,
    simulation.simulation_result.total_system_distance if simulation.simulation_result else None,
)

if simulation.depot is not None:
    draw_depot(screen, simulation.depot, settings.depot_half_size)
if simulation.delivery_points:
    draw_delivery_points(screen, simulation.delivery_points, settings.delivery_point_radius)
if simulation.simulation_result is not None:
    draw_vehicle_routes(screen, simulation.simulation_result, VisualTheme.vehicle_route_colors)
    draw_vehicle_legend(...)
```

Update window caption: `"Simulador de Entregas · Roteamento Guloso"`.

Disable **Simular** button visually when `not simulation.can_simulate()` (extend `ActionButton` draw or skip click handling).

- [ ] **Step 3: Manual smoke test**

Run: `python main.py`

Checklist:
1. Window opens without traceback
2. Sliders adjust vehicle/point/item counts
3. **Sortear posições** shows depot + labeled points with item counts
4. **Simular** draws colored routes and fills sidebar results
5. Changing slider clears routes until re-simulate
6. Q/Esc closes

- [ ] **Step 4: Run all unit tests**

Run: `python -m pytest tests/ -v`  
Expected: all delivery tests PASS; pre-existing GA tests (`test_fitness_priority`, `test_scenario_presets`) still PASS unchanged

- [ ] **Step 5: Commit**

```bash
git add traveling_salesman_problem/simulation/pygame_application.py
git commit -m "feat: replace GA pygame loop with greedy delivery simulator UI"
```

---

## Spec Coverage Checklist

| Spec requirement | Task |
|------------------|------|
| Modular packages (generators, routing, distance, reporter) | Tasks 1–5 |
| 1–3 vehicles, 1–3 points, even items 2–14 | Tasks 6–8 |
| Greedy global algorithm + partial delivery | Task 4 |
| Sortear vs Simular button flow | Task 8 |
| Depot randomized with points | Tasks 3, 8 |
| Pygame UI replacement (no GA/obstacles) | Tasks 8–11 |
| Map: depot, points, routes, legend | Task 9 |
| Sidebar: summary, config, actions, results | Tasks 10–11 |
| Unit tests | Tasks 1–4 |
| GA preserved in repo | No task modifies `genetic_algorithm/` |

## Self-Review Notes

- All tasks include exact file paths and concrete code — no TBD placeholders.
- `run_greedy_simulation` signature consistent across Tasks 4–5–8.
- `DiscreteSlider.selected_value` used consistently for item totals.
- `DEPOT_ID = "DEPOT"` used in routing; reporter displays as `"D"`.
- Pre-existing tests kept green by not modifying GA modules.

---

**Plan complete and saved to `docs/superpowers/plans/2026-07-08-greedy-delivery-simulation.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
