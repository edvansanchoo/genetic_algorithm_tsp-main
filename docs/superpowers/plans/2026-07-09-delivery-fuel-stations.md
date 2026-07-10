# Delivery Fuel Stations — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add limited fuel (max 150), network-near gas stations that refill to full, heuristic detours when a leg is unreachable on remaining fuel, and strong fitness penalty (`inf`) when a vehicle runs dry — without changing the GA chromosome.

**Architecture:** New `delivery_simulation/fuel/` package (models, placement, simulation). Stations become `F*` nodes in `RoadNetwork`. `evaluate_permutation` plans delivery destinations as today, then each leg may insert a one-time station detour via `travel_with_fuel`. Fitness remains graph distance or `inf`. UI adds a Postos slider, map markers, and a short fuel log.

**Tech Stack:** Python 3.9+, Pygame, stdlib `unittest`. Reuse `road_network.find_path` / `path_distance`, `IntegerSlider`, existing sidebar scroll.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-07-09-delivery-fuel-stations-design.md`
- `MAX_FUEL = 150`; consumption = graph `path_distance` (1:1)
- Station visit → tank = 150; each station at most once per vehicle
- Placement: ≤ 100 px from an anchor node (depot / delivery / transit); min separation 30 px; must connect in radius graph
- Dry tank → `is_feasible=False` → fitness `float("inf")`
- GA chromosome unchanged (`TaskPermutation`); no refuel genes
- Station IDs: `F1`, `F2`, … (`FUEL_STATION_ID_PREFIX = "F"`)
- Slider Postos: 0–6, default 3
- UI language: Portuguese
- Test runner: `python -m unittest discover tests -v`
- Do not implement the old TSP-only spec `2026-07-01-fuel-stations-design.md`

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `delivery_simulation/fuel/__init__.py` | Create | Package exports |
| `delivery_simulation/fuel/models.py` | Create | `GasStation`, `FuelLeg`, `FuelStopEvent`, `RouteFuelReport`, constants |
| `delivery_simulation/fuel/placement.py` | Create | `place_gas_stations` |
| `delivery_simulation/fuel/simulation.py` | Create | `travel_with_fuel` (one leg + optional detour) |
| `delivery_simulation/models.py` | Modify | Optional `Stop.is_fuel_station`; expose fuel on `SimulationResult` if needed |
| `delivery_simulation/route_evaluator.py` | Modify | Integrate fuel into legs; return fuel report |
| `delivery_simulation/vehicle_genetic.py` | Modify | Pass through new evaluator return shape if changed |
| `delivery_simulation/__init__.py` | Modify | Export fuel symbols |
| `tests/test_fuel_placement.py` | Create | Placement constraints |
| `tests/test_fuel_simulation.py` | Create | Consume, refill, detour, dry-out |
| `tests/test_route_evaluator.py` | Modify | Fuel-aware evaluation cases |
| `traveling_salesman_problem/config/application_settings.py` | Modify | Postos slider defaults |
| `traveling_salesman_problem/config/visual_theme.py` | Modify | Station color |
| `traveling_salesman_problem/simulation/simulation_state.py` | Modify | Generate stations, slider, fuel reports on best result |
| `traveling_salesman_problem/visualization/map_renderer.py` | Modify | Draw stations |
| `traveling_salesman_problem/visualization/application_layout.py` | Modify | Fuel log panel + header metrics |
| `traveling_salesman_problem/simulation/pygame_application.py` | Modify | Draw slider + stations + log |

---

### Task 1: Fuel models and constants

**Files:**
- Create: `delivery_simulation/fuel/__init__.py`
- Create: `delivery_simulation/fuel/models.py`
- Test: `tests/test_fuel_simulation.py` (model smoke only in this task)

**Interfaces:**
- Consumes: `Coordinate` from `delivery_simulation.models`
- Produces:
  - `MAX_FUEL: float = 150.0`
  - `MAX_STATION_DISTANCE_FROM_NETWORK: float = 100.0`
  - `FUEL_STATION_ID_PREFIX: str = "F"`
  - `MIN_STATION_SEPARATION: float = 30.0`
  - `@dataclass(frozen=True) class GasStation: id: str; coordinate: Coordinate`
  - `@dataclass class FuelLeg: leg_index: int; from_node_id: str; to_node_id: str; distance: float; fuel_before: float; fuel_consumed: float; fuel_after: float`
  - `@dataclass class FuelStopEvent: station_id: str; fuel_on_arrival: float; fuel_on_departure: float`
  - `@dataclass class RouteFuelReport: legs: List[FuelLeg]; stops: List[FuelStopEvent]; final_fuel: float; is_feasible: bool; expanded_node_ids: List[str]; total_distance: float`

- [ ] **Step 1: Write failing smoke test**

Create `tests/test_fuel_simulation.py`:

```python
import unittest

from delivery_simulation.fuel.models import MAX_FUEL, GasStation, RouteFuelReport


class FuelModelTests(unittest.TestCase):
    def test_max_fuel_is_150(self):
        self.assertEqual(MAX_FUEL, 150.0)

    def test_gas_station_frozen(self):
        station = GasStation("F1", (10.0, 20.0))
        self.assertEqual(station.id, "F1")
        with self.assertRaises(Exception):
            station.id = "F2"  # type: ignore[misc]
```

- [ ] **Step 2: Run test — expect FAIL (import error)**

Run: `python -m unittest tests.test_fuel_simulation.FuelModelTests -v`  
Expected: FAIL — `No module named 'delivery_simulation.fuel'`

- [ ] **Step 3: Implement models**

Create `delivery_simulation/fuel/models.py`:

```python
"""Tipos e constantes de combustível / postos."""

from dataclasses import dataclass, field
from typing import List, Tuple

Coordinate = Tuple[float, float]

MAX_FUEL = 150.0
MAX_STATION_DISTANCE_FROM_NETWORK = 100.0
FUEL_STATION_ID_PREFIX = "F"
MIN_STATION_SEPARATION = 30.0


@dataclass(frozen=True)
class GasStation:
    id: str
    coordinate: Coordinate


@dataclass
class FuelLeg:
    leg_index: int
    from_node_id: str
    to_node_id: str
    distance: float
    fuel_before: float
    fuel_consumed: float
    fuel_after: float


@dataclass
class FuelStopEvent:
    station_id: str
    fuel_on_arrival: float
    fuel_on_departure: float


@dataclass
class RouteFuelReport:
    legs: List[FuelLeg] = field(default_factory=list)
    stops: List[FuelStopEvent] = field(default_factory=list)
    final_fuel: float = MAX_FUEL
    is_feasible: bool = True
    expanded_node_ids: List[str] = field(default_factory=list)
    total_distance: float = 0.0
```

Create `delivery_simulation/fuel/__init__.py`:

```python
from delivery_simulation.fuel.models import (
    FUEL_STATION_ID_PREFIX,
    MAX_FUEL,
    MAX_STATION_DISTANCE_FROM_NETWORK,
    MIN_STATION_SEPARATION,
    FuelLeg,
    FuelStopEvent,
    GasStation,
    RouteFuelReport,
)

__all__ = [
    "FUEL_STATION_ID_PREFIX",
    "MAX_FUEL",
    "MAX_STATION_DISTANCE_FROM_NETWORK",
    "MIN_STATION_SEPARATION",
    "FuelLeg",
    "FuelStopEvent",
    "GasStation",
    "RouteFuelReport",
]
```

- [ ] **Step 4: Run test — expect PASS**

Run: `python -m unittest tests.test_fuel_simulation.FuelModelTests -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delivery_simulation/fuel/__init__.py delivery_simulation/fuel/models.py tests/test_fuel_simulation.py
git commit -m "feat: add fuel domain models and constants"
```

---

### Task 2: Place gas stations near the network

**Files:**
- Create: `delivery_simulation/fuel/placement.py`
- Create: `tests/test_fuel_placement.py`
- Modify: `delivery_simulation/fuel/__init__.py` (export `place_gas_stations`)

**Interfaces:**
- Consumes: `GasStation`, `MAX_STATION_DISTANCE_FROM_NETWORK`, `MIN_STATION_SEPARATION`, `FUEL_STATION_ID_PREFIX`, `euclidean`, `build_road_network`
- Produces:
  - `place_gas_stations(count: int, anchor_nodes: Dict[str, Coordinate], map_min_x: float, map_min_y: float, map_max_x: float, map_max_y: float, connection_radius: float, min_separation: float = MIN_STATION_SEPARATION, max_attempts: int = 100, rng: Optional[random.Random] = None) -> List[GasStation]`

- [ ] **Step 1: Write failing tests**

Create `tests/test_fuel_placement.py`:

```python
import math
import random
import unittest

from delivery_simulation.distance import euclidean
from delivery_simulation.fuel.models import MAX_STATION_DISTANCE_FROM_NETWORK, MIN_STATION_SEPARATION
from delivery_simulation.fuel.placement import place_gas_stations
from delivery_simulation.models import DEPOT_ID
from delivery_simulation.road_network import build_road_network


class FuelPlacementTests(unittest.TestCase):
    def test_stations_within_100px_of_an_anchor(self):
        anchors = {DEPOT_ID: (100.0, 100.0), "A": (200.0, 100.0), "T1": (150.0, 150.0)}
        stations = place_gas_stations(
            3, anchors, 0, 0, 400, 400, connection_radius=120.0, rng=random.Random(1)
        )
        self.assertEqual(len(stations), 3)
        for station in stations:
            nearest = min(euclidean(station.coordinate, coord) for coord in anchors.values())
            self.assertLessEqual(nearest, MAX_STATION_DISTANCE_FROM_NETWORK + 1e-6)

    def test_stations_do_not_overlap_anchors(self):
        anchors = {DEPOT_ID: (100.0, 100.0), "A": (250.0, 100.0)}
        stations = place_gas_stations(
            2, anchors, 0, 0, 400, 400, connection_radius=150.0, rng=random.Random(2)
        )
        for station in stations:
            for coord in anchors.values():
                self.assertGreaterEqual(
                    euclidean(station.coordinate, coord), MIN_STATION_SEPARATION - 1e-6
                )

    def test_stations_connect_in_radius_graph(self):
        anchors = {DEPOT_ID: (0.0, 0.0), "A": (80.0, 0.0), "T1": (40.0, 40.0)}
        radius = 100.0
        stations = place_gas_stations(
            2, anchors, -50, -50, 200, 200, connection_radius=radius, rng=random.Random(3)
        )
        nodes = dict(anchors)
        for station in stations:
            nodes[station.id] = station.coordinate
        network = build_road_network(nodes, radius)
        degree = {node_id: 0 for node_id in network.nodes}
        for a, b in network.edges:
            degree[a] += 1
            degree[b] += 1
        for station in stations:
            self.assertGreater(degree[station.id], 0)

    def test_zero_count_returns_empty(self):
        anchors = {DEPOT_ID: (0.0, 0.0)}
        self.assertEqual(
            place_gas_stations(0, anchors, 0, 0, 100, 100, connection_radius=50.0),
            [],
        )
```

- [ ] **Step 2: Run tests — expect FAIL**

Run: `python -m unittest tests.test_fuel_placement -v`  
Expected: FAIL — cannot import `place_gas_stations`

- [ ] **Step 3: Implement placement**

Create `delivery_simulation/fuel/placement.py`:

```python
"""Gera postos de combustível perto da rede existente."""

import math
import random
from typing import Dict, List, Optional, Set, Tuple

from delivery_simulation.distance import euclidean
from delivery_simulation.fuel.models import (
    FUEL_STATION_ID_PREFIX,
    MAX_STATION_DISTANCE_FROM_NETWORK,
    MIN_STATION_SEPARATION,
    GasStation,
)
from delivery_simulation.models import Coordinate
from delivery_simulation.road_network import build_road_network


def place_gas_stations(
    count: int,
    anchor_nodes: Dict[str, Coordinate],
    map_min_x: float,
    map_min_y: float,
    map_max_x: float,
    map_max_y: float,
    connection_radius: float,
    min_separation: float = MIN_STATION_SEPARATION,
    max_attempts: int = 100,
    rng: Optional[random.Random] = None,
) -> List[GasStation]:
    if count < 1:
        return []

    random_source = rng or random.Random()
    anchors = list(anchor_nodes.items())
    occupied: List[Coordinate] = list(anchor_nodes.values())
    stations: List[GasStation] = []

    for index in range(count):
        station_id = f"{FUEL_STATION_ID_PREFIX}{index + 1}"
        placed = False
        for _ in range(max_attempts):
            _, anchor_coord = random_source.choice(anchors)
            angle = random_source.uniform(0.0, 2.0 * math.pi)
            distance = random_source.uniform(min_separation, MAX_STATION_DISTANCE_FROM_NETWORK)
            candidate = (
                anchor_coord[0] + distance * math.cos(angle),
                anchor_coord[1] + distance * math.sin(angle),
            )
            if not (map_min_x <= candidate[0] <= map_max_x and map_min_y <= candidate[1] <= map_max_y):
                continue
            if any(euclidean(candidate, existing) < min_separation for existing in occupied):
                continue

            trial_nodes = dict(anchor_nodes)
            for existing in stations:
                trial_nodes[existing.id] = existing.coordinate
            trial_nodes[station_id] = candidate
            network = build_road_network(trial_nodes, connection_radius)
            degree = 0
            for node_a, node_b in network.edges:
                if node_a == station_id or node_b == station_id:
                    degree += 1
            if degree == 0:
                continue

            stations.append(GasStation(station_id, candidate))
            occupied.append(candidate)
            placed = True
            break

        if not placed:
            break

    return stations
```

Export `place_gas_stations` from `delivery_simulation/fuel/__init__.py`.

- [ ] **Step 4: Run tests — expect PASS**

Run: `python -m unittest tests.test_fuel_placement -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delivery_simulation/fuel/placement.py delivery_simulation/fuel/__init__.py tests/test_fuel_placement.py
git commit -m "feat: place gas stations near road network anchors"
```

---

### Task 3: `travel_with_fuel` — one leg with optional station detour

**Files:**
- Create: `delivery_simulation/fuel/simulation.py`
- Modify: `tests/test_fuel_simulation.py`
- Modify: `delivery_simulation/fuel/__init__.py`

**Interfaces:**
- Consumes: `find_path`, `path_distance`, `RoadNetwork`, `MAX_FUEL`, fuel models
- Produces:
  - `@dataclass class FuelTravelResult: paths: List[List[str]]; fuel_after: float; visited_stations: Set[str]; legs: List[FuelLeg]; stops: List[FuelStopEvent]; is_feasible: bool; distance: float`
  - `travel_with_fuel(network: RoadNetwork, origin: str, destination: str, fuel: float, station_ids: Set[str], visited_stations: Set[str], blocked: Set[str], leg_index_start: int = 0) -> FuelTravelResult`
  - Behavior: if `fuel >= dist(origin→destination)`, go direct; else pick unused station minimizing `dist(origin→F)+dist(F→destination)` with `fuel >= dist(origin→F)`; refill to `MAX_FUEL`; if none, `is_feasible=False`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_fuel_simulation.py`:

```python
from delivery_simulation.fuel.simulation import travel_with_fuel
from delivery_simulation.models import DEPOT_ID
from delivery_simulation.road_network import build_road_network


class TravelWithFuelTests(unittest.TestCase):
    def test_direct_leg_consumes_distance(self):
        nodes = {DEPOT_ID: (0.0, 0.0), "A": (40.0, 0.0)}
        network = build_road_network(nodes, radius=50.0)
        result = travel_with_fuel(
            network, DEPOT_ID, "A", fuel=150.0, station_ids=set(), visited_stations=set(), blocked=set()
        )
        self.assertTrue(result.is_feasible)
        self.assertAlmostEqual(result.distance, 40.0)
        self.assertAlmostEqual(result.fuel_after, 110.0)
        self.assertEqual(result.stops, [])

    def test_detours_to_station_when_fuel_insufficient(self):
        # DEPOT --50-- F1 --50-- A ; fuel 50 cannot do 100 direct, can reach F1
        nodes = {
            DEPOT_ID: (0.0, 0.0),
            "F1": (50.0, 0.0),
            "A": (100.0, 0.0),
        }
        network = build_road_network(nodes, radius=55.0)
        result = travel_with_fuel(
            network,
            DEPOT_ID,
            "A",
            fuel=50.0,
            station_ids={"F1"},
            visited_stations=set(),
            blocked=set(),
        )
        self.assertTrue(result.is_feasible)
        self.assertEqual(len(result.stops), 1)
        self.assertEqual(result.stops[0].station_id, "F1")
        self.assertAlmostEqual(result.stops[0].fuel_on_departure, 150.0)
        self.assertIn("F1", result.visited_stations)
        self.assertAlmostEqual(result.fuel_after, 100.0)  # 150 - 50 after refill

    def test_dry_out_when_no_viable_station(self):
        nodes = {DEPOT_ID: (0.0, 0.0), "A": (100.0, 0.0)}
        network = build_road_network(nodes, radius=150.0)
        result = travel_with_fuel(
            network, DEPOT_ID, "A", fuel=10.0, station_ids=set(), visited_stations=set(), blocked=set()
        )
        self.assertFalse(result.is_feasible)

    def test_does_not_revisit_station(self):
        nodes = {
            DEPOT_ID: (0.0, 0.0),
            "F1": (50.0, 0.0),
            "A": (100.0, 0.0),
        }
        network = build_road_network(nodes, radius=55.0)
        result = travel_with_fuel(
            network,
            DEPOT_ID,
            "A",
            fuel=50.0,
            station_ids={"F1"},
            visited_stations={"F1"},
            blocked=set(),
        )
        self.assertFalse(result.is_feasible)
```

- [ ] **Step 2: Run tests — expect FAIL**

Run: `python -m unittest tests.test_fuel_simulation.TravelWithFuelTests -v`  
Expected: FAIL — cannot import `travel_with_fuel`

- [ ] **Step 3: Implement simulation**

Create `delivery_simulation/fuel/simulation.py`:

```python
"""Simula consumo de combustível e desvios a postos em um trecho."""

from dataclasses import dataclass, field
from typing import List, Optional, Set

from delivery_simulation.fuel.models import MAX_FUEL, FuelLeg, FuelStopEvent
from delivery_simulation.models import RoadNetwork
from delivery_simulation.road_network import find_path, path_distance


@dataclass
class FuelTravelResult:
    paths: List[List[str]] = field(default_factory=list)
    fuel_after: float = 0.0
    visited_stations: Set[str] = field(default_factory=set)
    legs: List[FuelLeg] = field(default_factory=list)
    stops: List[FuelStopEvent] = field(default_factory=list)
    is_feasible: bool = True
    distance: float = 0.0


def _path_or_empty(
    network: RoadNetwork,
    origin: str,
    destination: str,
    blocked: Set[str],
) -> List[str]:
    return find_path(network, origin, destination, blocked)


def travel_with_fuel(
    network: RoadNetwork,
    origin: str,
    destination: str,
    fuel: float,
    station_ids: Set[str],
    visited_stations: Set[str],
    blocked: Set[str],
    leg_index_start: int = 0,
) -> FuelTravelResult:
    result = FuelTravelResult(fuel_after=fuel, visited_stations=set(visited_stations))
    direct = _path_or_empty(network, origin, destination, blocked)
    if not direct:
        result.is_feasible = False
        return result

    direct_distance = path_distance(network, direct)
    if fuel >= direct_distance:
        fuel_after = fuel - direct_distance
        result.paths = [direct]
        result.fuel_after = fuel_after
        result.distance = direct_distance
        result.legs = [
            FuelLeg(
                leg_index_start,
                origin,
                destination,
                direct_distance,
                fuel,
                direct_distance,
                fuel_after,
            )
        ]
        return result

    best: Optional[tuple[float, str, List[str], List[str]]] = None
    for station_id in station_ids:
        if station_id in visited_stations:
            continue
        path_to_station = _path_or_empty(network, origin, station_id, blocked)
        if not path_to_station:
            continue
        dist_to_station = path_distance(network, path_to_station)
        if fuel < dist_to_station:
            continue
        blocked_after = set(blocked) | {station_id}
        path_from_station = _path_or_empty(network, station_id, destination, blocked_after)
        if not path_from_station:
            continue
        dist_from_station = path_distance(network, path_from_station)
        total = dist_to_station + dist_from_station
        if best is None or total < best[0]:
            best = (total, station_id, path_to_station, path_from_station)

    if best is None:
        result.is_feasible = False
        return result

    _, station_id, path_to_station, path_from_station = best
    dist_to_station = path_distance(network, path_to_station)
    dist_from_station = path_distance(network, path_from_station)
    fuel_on_arrival = fuel - dist_to_station
    fuel_on_departure = MAX_FUEL
    fuel_after = fuel_on_departure - dist_from_station

    result.paths = [path_to_station, path_from_station]
    result.fuel_after = fuel_after
    result.visited_stations.add(station_id)
    result.distance = dist_to_station + dist_from_station
    result.stops = [
        FuelStopEvent(station_id, fuel_on_arrival, fuel_on_departure),
    ]
    result.legs = [
        FuelLeg(
            leg_index_start,
            origin,
            station_id,
            dist_to_station,
            fuel,
            dist_to_station,
            fuel_on_arrival,
        ),
        FuelLeg(
            leg_index_start + 1,
            station_id,
            destination,
            dist_from_station,
            fuel_on_departure,
            dist_from_station,
            fuel_after,
        ),
    ]
    return result
```

Export `travel_with_fuel` and `FuelTravelResult` from the fuel package.

- [ ] **Step 4: Run tests — expect PASS**

Run: `python -m unittest tests.test_fuel_simulation -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delivery_simulation/fuel/simulation.py delivery_simulation/fuel/__init__.py tests/test_fuel_simulation.py
git commit -m "feat: simulate fuel consumption and station detours per leg"
```

---

### Task 4: Integrate fuel into `evaluate_permutation`

**Files:**
- Modify: `delivery_simulation/models.py` (`Stop.is_fuel_station: bool = False`)
- Modify: `delivery_simulation/route_evaluator.py`
- Modify: `delivery_simulation/vehicle_genetic.py` (only if return type changes)
- Modify: `tests/test_route_evaluator.py`
- Modify: `delivery_simulation/__init__.py` if exporting new helpers

**Interfaces:**
- Consumes: `travel_with_fuel`, station id set from network nodes starting with `F`
- Produces:
  - `evaluate_permutation(...) -> tuple[float, List[Trip], RouteFuelReport]`
  - On dry-out: `(inf, [], report_with_is_feasible_False)`
  - Feasible distance includes station detours; trips include `Stop(station_id, 0, is_fuel_station=True)`
  - Update all callers: `vehicle_genetic._evaluate_population`, any tests unpacking 2-tuples

- [ ] **Step 1: Write failing integration tests**

Add to `tests/test_route_evaluator.py`:

```python
from delivery_simulation.fuel.models import MAX_FUEL


class RouteEvaluatorFuelTests(unittest.TestCase):
    def test_insufficient_fuel_without_station_is_infinity(self):
        nodes = {DEPOT_ID: (0.0, 0.0), "A": (200.0, 0.0)}
        network = build_road_network(nodes, radius=250.0)
        tasks = [DeliveryTask("A", 4)]
        distance, trips, report = evaluate_permutation(tasks, tasks, network)
        self.assertEqual(distance, float("inf"))
        self.assertFalse(report.is_feasible)

    def test_station_detour_makes_long_leg_feasible(self):
        nodes = {
            DEPOT_ID: (0.0, 0.0),
            "F1": (80.0, 0.0),
            "A": (160.0, 0.0),
        }
        network = build_road_network(nodes, radius=90.0)
        tasks = [DeliveryTask("A", 4)]
        distance, trips, report = evaluate_permutation(tasks, tasks, network)
        self.assertTrue(report.is_feasible)
        self.assertNotEqual(distance, float("inf"))
        stop_ids = [stop.point_id for stop in trips[0].stops]
        self.assertIn("F1", stop_ids)
        self.assertTrue(any(stop.is_fuel_station for stop in trips[0].stops))
        self.assertLess(report.final_fuel, MAX_FUEL)
```

Update existing tests in the same file to unpack three values:

```python
distance, trips, report = evaluate_permutation(...)
```

- [ ] **Step 2: Run tests — expect FAIL** (wrong unpack / no fuel logic)

Run: `python -m unittest tests.test_route_evaluator -v`  
Expected: FAIL

- [ ] **Step 3: Implement integration**

In `delivery_simulation/models.py`, extend `Stop`:

```python
@dataclass
class Stop:
    point_id: str
    items_delivered: int
    is_transit: bool = False
    is_fuel_station: bool = False
```

In `route_evaluator.py`:

1. Import `RouteFuelReport`, `travel_with_fuel`, `FUEL_STATION_ID_PREFIX`.
2. Helper `_station_ids(network) -> Set[str]` = `{id for id in network.nodes if id.startswith(FUEL_STATION_ID_PREFIX)}`.
3. Replace each `find_path` + `_append_path` for a destination with:
   - `travel = travel_with_fuel(network, current_node, destination, fuel, station_ids, visited_stations, blocked_for_pathfinding(...), leg_index)`
   - if not `travel.is_feasible`: return `inf, [], report`
   - for each path in `travel.paths`, `_append_path` (for station destination use `is_fuel_station=True` via new parameter or detect prefix)
   - update `fuel`, `visited_stations`, accumulate report legs/stops/distance
4. Start each vehicle evaluation with `fuel = MAX_FUEL`, empty `visited_stations`.
5. Return `(total_distance, completed_trips, report)`.

Update `_append_path` to accept fuel-station stops:

```python
elif node_id.startswith(FUEL_STATION_ID_PREFIX):
    if node_id not in _existing_stop_ids(active_trip):
        active_trip.stops.append(Stop(node_id, 0, is_fuel_station=True))
```

Update `vehicle_genetic._evaluate_population`:

```python
distance, trips, _report = evaluate_permutation(tasks, permutation, road_network)
```

Update any other callers the same way.

- [ ] **Step 4: Run full related tests**

Run: `python -m unittest tests.test_route_evaluator tests.test_vehicle_genetic tests.test_fuel_simulation -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delivery_simulation/models.py delivery_simulation/route_evaluator.py delivery_simulation/vehicle_genetic.py tests/test_route_evaluator.py delivery_simulation/__init__.py
git commit -m "feat: evaluate delivery routes with fuel constraints"
```

---

### Task 5: Wire stations into scenario generation (SimulationState)

**Files:**
- Modify: `traveling_salesman_problem/config/application_settings.py`
- Modify: `traveling_salesman_problem/simulation/simulation_state.py`
- Modify: `delivery_simulation/__init__.py` (export placement if useful)

**Interfaces:**
- Consumes: `place_gas_stations`, settings for postos slider
- Produces:
  - Settings: `initial_gas_station_count: int = 3`, `minimum_gas_stations: int = 0`, `maximum_gas_stations: int = 6`
  - State fields: `gas_stations: List[GasStation]`, `gas_station_count_slider: IntegerSlider`, `_last_gas_station_count`
  - `shuffle_positions` places stations after transit, merges `F*` into `nodes` before `build_connected_network`
  - Changing postos slider regenerates stations + network (same pattern as transit slider)
  - `clear_simulation_result` clears fuel UI state as needed

- [ ] **Step 1: Add settings**

In `application_settings.py`:

```python
initial_gas_station_count: int = 3
minimum_gas_stations: int = 0
maximum_gas_stations: int = 6
```

- [ ] **Step 2: Add slider and placement in `shuffle_positions`**

Pattern (mirror transit):

```python
from delivery_simulation.fuel.models import GasStation
from delivery_simulation.fuel.placement import place_gas_stations

# in initialize_controls:
self.gas_station_count_slider = IntegerSlider(
    ...,
    settings.initial_gas_station_count,
    settings.minimum_gas_stations,
    settings.maximum_gas_stations,
    label="Postos",
)

# in shuffle_positions, after transit nodes dict is built, before build_connected_network:
station_count = self.gas_station_count_slider.integer_value
anchors = {DEPOT_ID: depot}
for point in self.delivery_points:
    anchors[point.id] = point.coordinate
for node in transit:
    anchors[node.id] = node.coordinate
stations = place_gas_stations(
    station_count,
    anchors,
    settings.map_minimum_x,
    settings.map_minimum_y,
    settings.map_maximum_x,
    settings.map_maximum_y,
    connection_radius=radius,
)
self.gas_stations = stations
for station in stations:
    nodes[station.id] = station.coordinate
# connectivity check: still only require depot + delivery_ids (stations optional leaves)
```

Also handle slider change in `update_controls` like transit: if count changed and positions ready, call `shuffle_positions` (or a lighter regenerate that keeps depot/points and only rebuilds transit+stations — simplest: call `shuffle_positions`).

- [ ] **Step 3: Manual smoke (no automated UI test)**

Run: `python main.py`  
Expected: slider **Postos** visible; after **Sortear**, `F*` nodes appear in network when count > 0.

- [ ] **Step 4: Commit**

```bash
git add traveling_salesman_problem/config/application_settings.py traveling_salesman_problem/simulation/simulation_state.py delivery_simulation/__init__.py
git commit -m "feat: generate gas stations from Postos slider"
```

---

### Task 6: Map drawing, fuel log, and header metrics

**Files:**
- Modify: `traveling_salesman_problem/config/visual_theme.py`
- Modify: `traveling_salesman_problem/visualization/map_renderer.py`
- Modify: `traveling_salesman_problem/visualization/application_layout.py`
- Modify: `traveling_salesman_problem/simulation/pygame_application.py`
- Modify: `traveling_salesman_problem/simulation/simulation_state.py` (store latest `RouteFuelReport` per best vehicle if not already on trips)

**Interfaces:**
- Consumes: `gas_stations`, trip stops with `is_fuel_station`, optional `RouteFuelReport` on genetic best
- Produces:
  - `VisualTheme.gas_station_fill` (distinct color, e.g. `(217, 119, 6)`)
  - `draw_gas_stations(screen, gas_stations)`
  - `draw_fuel_log_panel(screen, report, ...)` showing legs + station events
  - Header line with `Comb {final:.0f}/150` or `Comb inválida`
  - Sidebar draws Postos slider under Configuração; map draws stations; results area shows fuel log for active vehicle best

- [ ] **Step 1: Theme + map draw**

```python
# visual_theme.py
gas_station_fill = (217, 119, 6)
gas_station_stroke = (255, 255, 255)

# map_renderer.py
def draw_gas_stations(screen, gas_stations) -> None:
    for station in gas_stations:
        center = (int(station.coordinate[0]), int(station.coordinate[1]))
        pygame.draw.circle(screen, VisualTheme.gas_station_fill, center, 8)
        pygame.draw.circle(screen, VisualTheme.gas_station_stroke, center, 8, 2)
```

Call from `pygame_application` after transit, before deliveries.

- [ ] **Step 2: Fuel log + header**

In `application_layout.py`, add `draw_fuel_log_panel` that renders lines like:

```text
LOG DE COMBUSTÍVEL
T01 · DEPOT → F1  dist 80  150→70
     posto F1: 70 → 150
T02 · F1 → A      dist 80  150→70
```

If `report is None` or empty: show `Sem dados de combustível.`  
If `not report.is_feasible`: show `Rota inviável (combustível).`

Extend `draw_delivery_map_header` (or caller) to include fuel summary from the active vehicle’s best report.

Persist reports: either recompute with `evaluate_permutation` when updating best genetic state, or store `RouteFuelReport` on `VehicleGeneticState` during `_evaluate_population`. Prefer storing on `VehicleGeneticState`:

```python
best_fuel_report: Optional[RouteFuelReport] = None
```

Update when best distance updates.

- [ ] **Step 3: Draw slider in sidebar**

In `_draw_scrollable_sidebar`, after transit/radius (or after mutation), draw `gas_station_count_slider`. Ensure `layout_controls` reserves vertical space for the new slider (same gap pattern as other integer sliders).

- [ ] **Step 4: Manual verification checklist**

1. Postos=0, long edges → many `inf` / inválida after Simular.
2. Postos=3 → some best routes include `F*` stops; log shows refill to 150.
3. Sortear / change Postos regenerates stations.
4. Existing GA chart and trip selector still work.

- [ ] **Step 5: Commit**

```bash
git add traveling_salesman_problem/config/visual_theme.py traveling_salesman_problem/visualization/map_renderer.py traveling_salesman_problem/visualization/application_layout.py traveling_salesman_problem/simulation/pygame_application.py traveling_salesman_problem/simulation/simulation_state.py delivery_simulation/vehicle_genetic.py
git commit -m "feat: visualize gas stations and fuel consumption log"
```

---

### Task 7: Regression sweep and export cleanup

**Files:**
- Modify: `delivery_simulation/__init__.py` (export fuel public API used by UI/tests)
- Touch tests only if failures appear

**Interfaces:**
- Produces: package exports for `GasStation`, `place_gas_stations`, `travel_with_fuel`, `MAX_FUEL`, `RouteFuelReport`

- [ ] **Step 1: Run full suite**

Run: `python -m unittest discover tests -v`  
Expected: all PASS

- [ ] **Step 2: Fix any broken unpack sites**

Search for `evaluate_permutation(` and ensure every call unpacks three values.

- [ ] **Step 3: Commit**

```bash
git add delivery_simulation/__init__.py tests
git commit -m "chore: export fuel API and fix evaluator call sites"
```

---

## Spec coverage checklist

| Spec requirement | Task |
|------------------|------|
| MAX_FUEL 150, consume 1:1 on graph | 1, 3, 4 |
| Separate `F*` stations, refill to full | 1, 3 |
| Placement ≤100 px, near network, connected | 2, 5 |
| Heuristic detour; not in GA chromosome | 3, 4 |
| Dry → invalid / `inf` | 3, 4 |
| One visit per station per vehicle | 3, 4 |
| Slider 0–6 default 3; regenerate on shuffle | 5 |
| Map + log + metrics | 6 |
| Out of scope (refuel genes, TSP-old spec) | not scheduled |

## Placeholder / consistency notes

- Evaluator return type is consistently `(float, List[Trip], RouteFuelReport)` from Task 4 onward.
- Station detection uses `FUEL_STATION_ID_PREFIX` (`"F"`), not a parallel registry, once nodes are in the network.
- `build_connected_network` connectivity guarantee remains for depot + deliveries only; stations must simply have degree ≥ 1 at placement time.
