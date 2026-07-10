# Dynamic Capacity Max Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Set the capacity slider maximum to the sum of all delivery demands in the active scenario, with automatic clamp when the max shrinks.

**Architecture:** Add `total_delivery_demand()` in `vrp_assignment.py`; `SimulationState._sync_capacity_slider_bounds()` updates `capacity_slider.maximum_value` after each `rebuild_scenario()`. Remove fixed `maximum_capacity` from settings.

**Tech Stack:** Python 3, unittest.

## Global Constraints

- Branch: `feature/road-network-blocked-nodes`
- Spec: `docs/superpowers/specs/2026-07-10-dynamic-capacity-max-design.md`
- Max formula: `max(minimum_capacity, sum(demands))` with `minimum_capacity = 1`
- Clamp: if `slider.integer_value > maximum`, set `slider.value = maximum`
- Remove `maximum_capacity` from `ApplicationSettings`
- No decoder, GA, or assignment logic changes

---

## File map

| File | Responsibility |
|------|----------------|
| Modify: `traveling_salesman_problem/problem/vrp_assignment.py` | `total_delivery_demand` |
| Modify: `traveling_salesman_problem/simulation/simulation_state.py` | `_sync_capacity_slider_bounds`, wire in `rebuild_scenario` |
| Modify: `traveling_salesman_problem/config/application_settings.py` | Remove `maximum_capacity` |
| Create: `tests/test_capacity_bounds.py` | Unit tests for demand sum and sync helper |

---

### Task 1: `total_delivery_demand` helper

**Files:**
- Modify: `traveling_salesman_problem/problem/vrp_assignment.py`
- Create: `tests/test_capacity_bounds.py`

**Interfaces:**
- Produces:
```python
def total_delivery_demand(deliveries: Sequence[DeliveryPoint]) -> int:
    return sum(point.demand for point in deliveries)
```

- [ ] **Step 1: Write failing test**

```python
# tests/test_capacity_bounds.py
import unittest

from traveling_salesman_problem.problem.vrp_assignment import total_delivery_demand
from traveling_salesman_problem.problem.vrp_models import DeliveryPoint


class TotalDeliveryDemandTests(unittest.TestCase):
    def test_sums_all_demands(self) -> None:
        deliveries = [
            DeliveryPoint("A", (0.0, 0.0), priority=5, demand=6),
            DeliveryPoint("B", (10.0, 0.0), priority=3, demand=4),
            DeliveryPoint("C", (5.0, 5.0), priority=1, demand=10),
        ]
        self.assertEqual(total_delivery_demand(deliveries), 20)

    def test_empty_returns_zero(self) -> None:
        self.assertEqual(total_delivery_demand([]), 0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_capacity_bounds.TotalDeliveryDemandTests -v`

Expected: FAIL — `ImportError: cannot import name 'total_delivery_demand'`

- [ ] **Step 3: Implement**

```python
# traveling_salesman_problem/problem/vrp_assignment.py
from typing import Dict, List, Sequence, Tuple

def total_delivery_demand(deliveries: Sequence[DeliveryPoint]) -> int:
    return sum(point.demand for point in deliveries)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_capacity_bounds.TotalDeliveryDemandTests -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add traveling_salesman_problem/problem/vrp_assignment.py tests/test_capacity_bounds.py
git commit -m "feat(vrp): add total_delivery_demand helper"
```

---

### Task 2: Sync capacity slider in simulation

**Files:**
- Modify: `traveling_salesman_problem/simulation/simulation_state.py`
- Modify: `tests/test_capacity_bounds.py`

**Interfaces:**
- Consumes: `total_delivery_demand` from Task 1
- Produces: `SimulationState._sync_capacity_slider_bounds(self) -> None`

- [ ] **Step 1: Write failing sync tests**

```python
# tests/test_capacity_bounds.py
from unittest.mock import MagicMock

from traveling_salesman_problem.config.application_settings import ApplicationSettings
from traveling_salesman_problem.problem.vrp_models import DeliveryPoint
from traveling_salesman_problem.simulation.simulation_state import SimulationState


class CapacitySliderSyncTests(unittest.TestCase):
    def _state_with_deliveries(self, demands: list[int]) -> SimulationState:
        state = SimulationState(settings=ApplicationSettings())
        state.deliveries = [
            DeliveryPoint(f"P{i}", (float(i), 0.0), priority=5, demand=demand)
            for i, demand in enumerate(demands)
        ]
        state.capacity_slider = MagicMock()
        state.capacity_slider.integer_value = 10
        state.capacity_slider.value = 10.0
        state.capacity_slider.maximum_value = 30.0
        return state

    def test_sync_sets_max_to_total_demand(self) -> None:
        state = self._state_with_deliveries([6, 4, 10])
        state._sync_capacity_slider_bounds()
        self.assertEqual(state.capacity_slider.maximum_value, 20.0)

    def test_sync_clamps_when_above_new_max(self) -> None:
        state = self._state_with_deliveries([3, 2])
        state.capacity_slider.integer_value = 80
        state.capacity_slider.value = 80.0
        state._sync_capacity_slider_bounds()
        self.assertEqual(state.capacity_slider.maximum_value, 5.0)
        self.assertEqual(state.capacity_slider.value, 5.0)

    def test_sync_keeps_value_when_below_max(self) -> None:
        state = self._state_with_deliveries([20, 30])
        state.capacity_slider.integer_value = 10
        state.capacity_slider.value = 10.0
        state._sync_capacity_slider_bounds()
        self.assertEqual(state.capacity_slider.maximum_value, 50.0)
        self.assertEqual(state.capacity_slider.value, 10.0)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests.test_capacity_bounds.CapacitySliderSyncTests -v`

Expected: FAIL — `AttributeError: _sync_capacity_slider_bounds`

- [ ] **Step 3: Implement sync + wire rebuild**

```python
# simulation_state.py imports
from traveling_salesman_problem.problem.vrp_assignment import (
    assign_deliveries_greedy,
    split_into_tokens,
    total_delivery_demand,
)

def _sync_capacity_slider_bounds(self) -> None:
    if self.capacity_slider is None:
        return
    settings = self.settings
    total = total_delivery_demand(self.deliveries)
    maximum = max(settings.minimum_capacity, total)
    self.capacity_slider.maximum_value = float(maximum)
    if self.capacity_slider.integer_value > maximum:
        self.capacity_slider.value = float(maximum)
```

At end of `rebuild_scenario()`, before `_sync_focus_after_rebuild()`:
```python
        self._sync_capacity_slider_bounds()
```

Update widget creation — replace `maximum_value=settings.maximum_capacity` with:
```python
            maximum_value=settings.initial_capacity,
```

- [ ] **Step 4: Run tests**

Run: `python -m unittest tests.test_capacity_bounds -v`

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add traveling_salesman_problem/simulation/simulation_state.py tests/test_capacity_bounds.py
git commit -m "feat(ui): sync capacity slider max to total delivery demand"
```

---

### Task 3: Remove fixed maximum_capacity + regression

**Files:**
- Modify: `traveling_salesman_problem/config/application_settings.py`

- [ ] **Step 1: Remove setting**

Delete `maximum_capacity: int = 30` from `ApplicationSettings`.

- [ ] **Step 2: Grep for references**

Run: `rg "maximum_capacity" traveling_salesman_problem tests`

Expected: no matches (only docs)

- [ ] **Step 3: Full regression**

Run:
```bash
python -m unittest tests.test_capacity_bounds tests.test_vrp_decoder tests.test_vrp_assignment tests.test_vehicle_genetic -v
```

- [ ] **Step 4: Smoke init**

Run:
```bash
python -c "from traveling_salesman_problem.simulation.simulation_state import SimulationState; s=SimulationState(); s.initialize(); total=sum(p.demand for p in s.deliveries); print('demand', total, 'max', s.capacity_slider.maximum_value)"
```

Expected: `max` equals `demand` (or max(1, demand))

- [ ] **Step 5: Commit**

```bash
git add traveling_salesman_problem/config/application_settings.py
git commit -m "refactor(settings): remove fixed maximum_capacity cap"
```

---

## Spec coverage check

| Spec requirement | Task |
|------------------|------|
| Max = sum of demands | Task 1 + 2 |
| Clamp on shrink | Task 2 test + impl |
| Remove `maximum_capacity` | Task 3 |
| No decoder changes | — |

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-10-dynamic-capacity-max.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task
2. **Inline Execution** — implement in this session

Which approach?
