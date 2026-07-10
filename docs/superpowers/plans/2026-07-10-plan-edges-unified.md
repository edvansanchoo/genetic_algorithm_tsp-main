# Unified Plan Edges Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace dual `trip_edges`/`used_edges` with one cumulative `plan_edges` set per vehicle decode, applying hard → ×20 → ×1.75 pathfinding on every segment including inter-trip legs.

**Architecture:** Single helper `_segment_with_plan_memory` escalates through forbidden then weighted tiers; decoder accumulates edges after each segment without resetting between trips. Settings rename penalties for clarity; no pathfinding API changes.

**Tech Stack:** Python, unittest.

## Global Constraints

- Branch: `feature/road-network-blocked-nodes`
- Spec: `docs/superpowers/specs/2026-07-10-plan-edges-unified-design.md`
- `plan_fallback_penalty = 20.0`, `plan_last_resort_penalty = 1.75`
- `plan_edges` never resets between trips of same vehicle decode
- `∞` only when all three tiers fail (real disconnect)
- Do not change chromosome, assignment, GA, or map rendering
- Deprecate decoder params `reuse_penalty` / `return_fallback_penalty` in favor of plan_* names

---

## File map

| File | Responsibility |
|------|----------------|
| Modify: `traveling_salesman_problem/problem/vrp_decoder.py` | `_segment_with_plan_memory`; remove `_return_segment`, `trip_edges`, `traverse_non_return` |
| Modify: `traveling_salesman_problem/config/application_settings.py` | Rename penalties |
| Modify: `traveling_salesman_problem/simulation/vehicle_genetic.py` | Wire renamed settings |
| Modify: `traveling_salesman_problem/simulation/simulation_state.py` | Wire renamed settings |
| Modify: `tests/test_return_path_diversification.py` | Update param names; add inter-trip test |
| Modify: `tests/test_vrp_decoder_edge_reuse.py` | Update param names if needed |

---

### Task 1: Unified segment helper + decoder refactor

**Files:**
- Modify: `traveling_salesman_problem/problem/vrp_decoder.py`
- Modify: `tests/test_return_path_diversification.py`

**Interfaces:**
- Produces:
```python
def _segment_with_plan_memory(
    mesh: DeliveryMesh,
    origin: Coordinate,
    destination: Coordinate,
    plan_edges: Set[EdgeKey],
    plan_fallback_penalty: float,
    plan_last_resort_penalty: float,
) -> Optional[Tuple[float, List[str]]]:
    # 1 forbidden=plan_edges → path_distance
    # 2 used=plan_edges, penalty=fallback → path_weighted_distance
    # 3 used=plan_edges, penalty=last_resort → path_weighted_distance
    # on success: plan_edges |= edges(path); return (cost, path)
    # on failure: None

def decode_vehicle_permutation(
    ...,
    plan_fallback_penalty: float = 20.0,
    plan_last_resort_penalty: float = 1.75,
) -> DecodedVehiclePlan:
```

- Removes: `_return_segment`, `used_edges`, `trip_edges`, `_record_path`, `traverse_non_return`
- `close_trip_returning_to_depot` calls same helper as delivery legs (no `trip_edges` reset)

- [ ] **Step 1: Add failing inter-trip test**

```python
# tests/test_return_path_diversification.py
class InterTripPlanEdgesTests(unittest.TestCase):
    def test_second_trip_avoids_first_trip_edges(self):
        # Diamond mesh DEPOT,A,B,X + token A(6) + token X(6), capacity=10 → 2 trips
        # Collect all edges from trip 0 paths; trip 1 paths must have empty intersection
        # when hard tier succeeds (use helper _edges_from_path on path_node_ids)
        ...
```

Keep existing return-diamond tests; update kwargs to `plan_fallback_penalty` / `plan_last_resort_penalty`.

- [ ] **Step 2: Run tests — expect FAIL**

```bash
python -m unittest tests.test_return_path_diversification -v
```

- [ ] **Step 3: Implement** `_segment_with_plan_memory` and simplify decoder loop

```python
def _segment_with_plan_memory(mesh, origin, destination, plan_edges, fallback, last_resort):
    path = delivery_segment_path(mesh, origin, destination, forbidden_edges=plan_edges)
    if path:
        cost = path_distance(mesh.network, path)
    else:
        path = delivery_segment_path(mesh, origin, destination, used_edges=plan_edges, reuse_penalty=fallback)
        if path:
            cost = path_weighted_distance(mesh.network, path, plan_edges, fallback)
        else:
            path = delivery_segment_path(mesh, origin, destination, used_edges=plan_edges, reuse_penalty=last_resort)
            if not path:
                return None
            cost = path_weighted_distance(mesh.network, path, plan_edges, last_resort)
    plan_edges.update(_edges_from_path(path))
    return cost, path
```

Both `traverse` to delivery and `close_trip` use this helper.

- [ ] **Step 4: Run tests — expect PASS**

- [ ] **Step 5: Commit**

```bash
git add traveling_salesman_problem/problem/vrp_decoder.py tests/test_return_path_diversification.py
git commit -m "refactor(vrp): unify plan_edges across all trip segments"
```

---

### Task 2: Settings rename + wiring

**Files:**
- Modify: `application_settings.py`
- Modify: `vehicle_genetic.py`
- Modify: `simulation_state.py`
- Modify: `tests/test_vrp_decoder_edge_reuse.py`

**Changes:**
```python
# application_settings.py — replace:
plan_fallback_penalty: float = 20.0
plan_last_resort_penalty: float = 1.75
# remove edge_reuse_penalty and return_fallback_penalty (or keep as deprecated aliases — prefer remove)
```

Update `decode_vehicle_permutation` call sites to use new names.

- [ ] **Step 1:** Grep for `reuse_penalty`, `return_fallback_penalty`, `edge_reuse_penalty` and update
- [ ] **Step 2:** Run full regression

```bash
python -m unittest tests.test_return_path_diversification tests.test_vrp_decoder_edge_reuse tests.test_vrp_decoder tests.test_vehicle_genetic tests.test_weighted_pathfinding -v
```

- [ ] **Step 3: Commit**

```bash
git commit -m "chore(settings): rename plan edge penalty settings"
```

---

### Task 3: Regression + smoke

- [ ] **Step 1:**

```bash
python -m unittest tests.test_return_path_diversification tests.test_vrp_decoder_edge_reuse tests.test_vrp_decoder tests.test_vehicle_genetic tests.test_vrp_assignment tests.test_route_animation -v
```

- [ ] **Step 2: Smoke**

```bash
python -c "from traveling_salesman_problem.simulation.simulation_state import SimulationState; s=SimulationState(); s.initialize(); print(s.settings.plan_fallback_penalty)"
```

- [ ] **Step 3: Manual** — capacity baixa para forçar 2 viagens; filtro Vn; viagem 2 não sobrepõe viagem 1
- [ ] **Step 4: Commit** if doc/checkbox updates needed

---

## Spec coverage

| Spec item | Task |
|-----------|------|
| Single `plan_edges` no reset between trips | 1 |
| 3-tier pathfinding all segments | 1 |
| Remove trip_edges/used_edges dual model | 1 |
| Settings rename | 2 |
| Inter-trip test | 1 |
| Regressão retorno diamante | 1, 3 |
| No GA/UI changes | — |

## Self-review notes

- Inter-trip test needs mesh where trip 2 has geometric alternative after trip 1 consumes short corridor; diamond + 2 heavy tokens + capacity=10 is sufficient.
- `close_trip` must NOT reset `plan_edges` (only trip state: stops, paths, load).
- Backward compat: grep entire repo for old setting names before claiming done.
