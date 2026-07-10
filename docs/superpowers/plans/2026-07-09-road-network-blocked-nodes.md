# Camada 1 — Malha nativa + bloqueios (Implementation Plan)

> **For agentic workers:** Execute task-by-task. **Do not commit** unless the user asks.

**Goal:** Replace trees/lakes with an in-package road mesh (transit + blocked) and pathfinding-based TSP distance.

**Architecture:** New `road_network.py` + `delivery_mesh.py` under `traveling_salesman_problem/problem/`. No `delivery_simulation`. GA chromosome unchanged.

**Tech Stack:** Python, Pygame, unittest.

## Global Constraints

- Branch `feature/road-network-blocked-nodes`
- **No git commits** unless user asks
- No VRP / capacity / fuel in this layer
- Blocked count ≥ 1; blocked nodes not in graph
- Keep priority fitness behavior

## Tasks

1. `road_network.py` + unit tests (radius graph, BFS, blocked skip, connectivity repair)
2. `delivery_mesh.py` + unit tests (build, detour, expand polyline, mutual reachability)
3. Wire `fitness.py` / `selection.py` (`mesh=` param; 2-opt uses mesh)
4. Settings + theme colors
5. `SimulationState` + `city_generator` — mesh lifecycle; remove terrain UX
6. Map/sidebar/`pygame_application` — draw mesh; remove trees/lakes/key O
7. Regression: `tests.test_fitness_priority` + new tests; manual `python main.py`

See design: `docs/superpowers/specs/2026-07-09-road-network-blocked-nodes-design.md`
