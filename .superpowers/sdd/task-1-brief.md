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
