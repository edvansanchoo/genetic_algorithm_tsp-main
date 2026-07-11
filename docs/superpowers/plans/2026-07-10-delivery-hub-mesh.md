# Delivery Hub Mesh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent direct delivery-to-delivery links; routes between deliveries must pass through transit nodes, not through the depot as an intermediate hop.

**Architecture:** `build_delivery_hub_network` omits delivery-delivery edges; `find_path`/`find_path_weighted` gain `no_through` to block depot as intermediate on delivery-to-delivery segments; mesh builders and reachability checks wire both; transit slider minimum becomes 1.

**Tech Stack:** Python 3, unittest.

## Global Constraints

- Branch: `feature/road-network-blocked-nodes`
- Spec: `docs/superpowers/specs/2026-07-10-delivery-hub-mesh-design.md`
- No delivery↔delivery edges in generated mesh
- Delivery→delivery paths must use transit; `no_through={DEPOT_ID}` on those segments
- Depot↔delivery direct edges and paths remain valid
- `transit_count >= 1` always
- Blocked nodes stay outside graph

---

## File map

| File | Responsibility |
|------|----------------|
| Modify: `traveling_salesman_problem/problem/road_network.py` | `build_delivery_hub_network`, `no_through` in pathfinding |
| Modify: `traveling_salesman_problem/problem/delivery_mesh.py` | Hub network build; segment/reachability `no_through` |
| Modify: `traveling_salesman_problem/simulation/simulation_state.py` | Transit min 1 |
| Create: `tests/test_delivery_hub_mesh.py` | Hub topology + path rules |
| Modify: `tests/test_delivery_mesh.py` | Update complete-graph edge count expectations |

---

### Task 1: Hub network builder

**Files:**
- Modify: `traveling_salesman_problem/problem/road_network.py`
- Create: `tests/test_delivery_hub_mesh.py`

**Interfaces:**
- Produces:
```python
def build_delivery_hub_network(
    nodes: Dict[str, Coordinate],
    delivery_ids: Sequence[str],
) -> RoadNetwork:
    # complete graph minus edges where both endpoints in delivery_ids
```

- [ ] **Step 1: Write failing tests**

```python
# tests/test_delivery_hub_mesh.py
import unittest
from traveling_salesman_problem.problem.road_network import build_delivery_hub_network
from traveling_salesman_problem.problem.vrp_models import DEPOT_ID


class DeliveryHubNetworkTests(unittest.TestCase):
    def test_no_delivery_to_delivery_edges(self) -> None:
        nodes = {
            DEPOT_ID: (0.0, 0.0),
            "A": (10.0, 0.0),
            "B": (0.0, 10.0),
            "T1": (5.0, 5.0),
        }
        network = build_delivery_hub_network(nodes, ["A", "B"])
        edge_set = {tuple(sorted(edge)) for edge in network.edges}
        self.assertNotIn(("A", "B"), edge_set)
        self.assertIn((DEPOT_ID, "A"), edge_set)
        self.assertIn(("A", "T1"), edge_set)
        self.assertIn(("T1", "B"), edge_set)

    def test_edge_count_formula(self) -> None:
        nodes = {DEPOT_ID: (0.0, 0.0), "A": (1.0, 0.0), "B": (2.0, 0.0), "T1": (3.0, 0.0)}
        network = build_delivery_hub_network(nodes, ["A", "B"])
        # 4 nodes, 6 complete pairs, minus 1 delivery-delivery = 5
        self.assertEqual(len(network.edges), 5)
```

- [ ] **Step 2: Run tests — expect FAIL**

Run: `python -m unittest tests.test_delivery_hub_mesh.DeliveryHubNetworkTests -v`

- [ ] **Step 3: Implement**

```python
def build_delivery_hub_network(
    nodes: Dict[str, Coordinate],
    delivery_ids: Sequence[str],
) -> RoadNetwork:
    delivery_set = set(delivery_ids)
    node_ids = list(nodes.keys())
    edges: List[Tuple[str, str]] = []
    for index, node_a in enumerate(node_ids):
        for node_b in node_ids[index + 1 :]:
            if node_a in delivery_set and node_b in delivery_set:
                continue
            edges.append((node_a, node_b))
    return RoadNetwork(
        nodes=dict(nodes),
        edges=edges,
        connection_radius=0.0,
    )
```

- [ ] **Step 4: Run tests — expect PASS**

- [ ] **Step 5: Commit**

```bash
git add traveling_salesman_problem/problem/road_network.py tests/test_delivery_hub_mesh.py
git commit -m "feat(mesh): add delivery hub network without delivery-delivery edges"
```

---

### Task 2: `no_through` pathfinding

**Files:**
- Modify: `traveling_salesman_problem/problem/road_network.py`
- Modify: `tests/test_delivery_hub_mesh.py`

**Interfaces:**
- Produces: `no_through: Optional[Set[str]] = None` on `find_path` and `find_path_weighted`
- Rule: neighbor in `no_through` is skippable only when `neighbor == destination`; otherwise skip as intermediate

- [ ] **Step 1: Write failing path tests**

```python
# tests/test_delivery_hub_mesh.py
from traveling_salesman_problem.problem.road_network import find_path, find_path_weighted

class DeliveryHubPathTests(unittest.TestCase):
    def _hub_network(self):
        nodes = {
            DEPOT_ID: (0.0, 0.0),
            "A": (10.0, 0.0),
            "B": (20.0, 0.0),
            "T1": (10.0, 10.0),
        }
        return build_delivery_hub_network(nodes, ["A", "B"])

    def test_depot_to_delivery_direct(self) -> None:
        network = self._hub_network()
        path = find_path(network, DEPOT_ID, "A")
        self.assertEqual(path, [DEPOT_ID, "A"])

    def test_delivery_to_delivery_uses_transit_not_depot(self) -> None:
        network = self._hub_network()
        path = find_path_weighted(
            network, "A", "B", no_through={DEPOT_ID}
        )
        self.assertTrue(path)
        self.assertIn("T1", path)
        self.assertNotIn(DEPOT_ID, path[1:-1])

    def test_delivery_to_delivery_empty_when_no_transit(self) -> None:
        nodes = {DEPOT_ID: (0.0, 0.0), "A": (10.0, 0.0), "B": (20.0, 0.0)}
        network = build_delivery_hub_network(nodes, ["A", "B"])
        path = find_path(network, "A", "B", no_through={DEPOT_ID})
        self.assertEqual(path, [])
```

- [ ] **Step 2: Run tests — expect FAIL**

- [ ] **Step 3: Add `no_through` to `find_path` and `find_path_weighted`**

In neighbor expansion loop, after blocked check:
```python
if no_through and neighbor in no_through and neighbor != destination:
    continue
```

- [ ] **Step 4: Run hub tests — expect PASS**

- [ ] **Step 5: Commit**

```bash
git add traveling_salesman_problem/problem/road_network.py tests/test_delivery_hub_mesh.py
git commit -m "feat(pathfinding): add no_through nodes for hub mesh routing"
```

---

### Task 3: Wire mesh + transit minimum + regression

**Files:**
- Modify: `traveling_salesman_problem/problem/delivery_mesh.py`
- Modify: `traveling_salesman_problem/simulation/simulation_state.py`
- Modify: `tests/test_delivery_mesh.py`
- Modify: `tests/test_delivery_hub_mesh.py`

**Interfaces:**
- Consumes: `build_delivery_hub_network`, `no_through` from Tasks 1–2

- [ ] **Step 1: Update delivery_mesh builders**

Replace `build_complete_network(nodes)` with:
```python
network = build_delivery_hub_network(nodes, delivery_ids)
# VRP: delivery_ids = [point.id for point in deliveries]
# TSP mesh: delivery_ids from D0..Dn
```

Add helper:
```python
def _no_through_for_segment(mesh, origin_id: str, destination_id: str) -> Optional[Set[str]]:
    if origin_id in mesh.delivery_ids and destination_id in mesh.delivery_ids:
        return {DEPOT_ID}
    return None
```

Use in `delivery_segment_path`, `deliveries_mutually_reachable`, `depot_reaches_all_deliveries` (latter only for delivery→delivery checks in mutually_reachable).

- [ ] **Step 2: Integration test via build_vrp_mesh**

```python
def test_vrp_mesh_delivery_paths_use_transit(self) -> None:
    # build_vrp_mesh with 2 deliveries, transit_count=2
    # delivery_segment_path between two delivery coords
    # assert transit in path, DEPOT not in middle
```

- [ ] **Step 3: Fix test_delivery_mesh complete-graph assertions**

Replace `n*(n-1)/2` edge expectations with hub formula:
`complete_pairs - delivery_delivery_pairs` where `delivery_delivery_pairs = n_deliveries * (n_deliveries - 1) / 2`

- [ ] **Step 4: Transit minimum**

In `simulation_state.py`:
```python
minimum_value=1,  # transit_count_slider
transit_count = max(1, self.transit_count_slider.integer_value)  # rebuild_scenario
```

- [ ] **Step 5: Regression**

```bash
python -m unittest tests.test_delivery_hub_mesh tests.test_delivery_mesh tests.test_return_path_diversification tests.test_vrp_decoder tests.test_vrp_decoder_edge_reuse -v
```

- [ ] **Step 6: Commit**

```bash
git add traveling_salesman_problem/problem/delivery_mesh.py traveling_salesman_problem/simulation/simulation_state.py tests/
git commit -m "feat(mesh): route deliveries through transit hubs only"
```

---

## Spec coverage check

| Requirement | Task |
|-------------|------|
| No delivery-delivery edges | Task 1 |
| Transit-only between deliveries | Task 2 + 3 |
| Depot direct to delivery OK | Task 2 tests |
| Transit min 1 | Task 3 |
| Reachability validation | Task 3 |

## Execution Handoff

Plan saved to `docs/superpowers/plans/2026-07-10-delivery-hub-mesh.md`.

**1. Subagent-Driven (recommended)** | **2. Inline Execution**

Which approach?
