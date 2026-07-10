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

- [ ] **Step 2: Run tests â€” expect FAIL**

Run: `python -m unittest tests.test_fuel_placement -v`  
Expected: FAIL â€” cannot import `place_gas_stations`

- [ ] **Step 3: Implement placement**

Create `delivery_simulation/fuel/placement.py`:

```python
"""Gera postos de combustÃ­vel perto da rede existente."""

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

- [ ] **Step 4: Run tests â€” expect PASS**

Run: `python -m unittest tests.test_fuel_placement -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delivery_simulation/fuel/placement.py delivery_simulation/fuel/__init__.py tests/test_fuel_placement.py
git commit -m "feat: place gas stations near road network anchors"
```

---

