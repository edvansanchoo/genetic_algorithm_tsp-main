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

- [ ] **Step 2: Run test â€” expect FAIL (import error)**

Run: `python -m unittest tests.test_fuel_simulation.FuelModelTests -v`  
Expected: FAIL â€” `No module named 'delivery_simulation.fuel'`

- [ ] **Step 3: Implement models**

Create `delivery_simulation/fuel/models.py`:

```python
"""Tipos e constantes de combustÃ­vel / postos."""

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

- [ ] **Step 4: Run test â€” expect PASS**

Run: `python -m unittest tests.test_fuel_simulation.FuelModelTests -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add delivery_simulation/fuel/__init__.py delivery_simulation/fuel/models.py tests/test_fuel_simulation.py
git commit -m "feat: add fuel domain models and constants"
```

---

