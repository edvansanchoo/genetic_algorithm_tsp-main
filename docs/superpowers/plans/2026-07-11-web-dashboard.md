# Web Dashboard VRP Hospitalar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a fully interactive Web dashboard (`python web.py`) that runs the existing VRP genetic algorithm via WebSocket, with complete functional parity to the Pygame desktop app, while leaving `python main.py` and all GA/VRP core logic unchanged.

**Architecture:** Introduce a `traveling_salesman_problem/web/` layer with headless control stubs, a `SimulationService` that owns `SimulationState` in headless mode, JSON serialization, and a FastAPI WebSocket server. Build a Vue 3 + Vite frontend with Canvas 2D map rendering that only displays server-provided state.

**Tech Stack:** Python 3.9+, FastAPI, uvicorn, websockets, Vue 3, Vite, Chart.js, Canvas 2D. Reuse existing `SimulationState`, `route_panel`, `route_animation`, `map_hit_test`, `VisualTheme`.

## Global Constraints

- **Do not create git commits** unless the user explicitly asks
- **Core intocável:** no changes to GA, VRP decoder, fitness, crossover, mutation, selection, population
- Desktop `python main.py` must work exactly as today after every task
- `web.py` must not import `pygame_application`
- Web toggles limited to `two_opt` and `show_mesh` (desktop parity)
- Runner-up, animation, arrows follow desktop rules (automatic on vehicle focus)
- Spec: `docs/superpowers/specs/2026-07-11-web-dashboard-design.md`
- v1 scope: phases F1–F4 only; F5 visual polish is out of scope

---

## File map

| File | Responsibility |
|------|----------------|
| Create: `traveling_salesman_problem/web/__init__.py` | Package marker |
| Create: `traveling_salesman_problem/web/headless_controls.py` | `HeadlessSlider`, `HeadlessToggle`, `HeadlessButton` |
| Create: `traveling_salesman_problem/web/log_buffer.py` | Ring buffer for generation/event logs |
| Create: `traveling_salesman_problem/web/state_serializer.py` | `SimulationState` + runtime → JSON dict |
| Create: `traveling_salesman_problem/web/command_handler.py` | WebSocket commands → `SimulationState` actions |
| Create: `traveling_salesman_problem/web/simulation_service.py` | Loop, pause, animation, broadcast |
| Create: `traveling_salesman_problem/web/server.py` | FastAPI app, static files, `/ws` |
| Create: `web.py` | Entry point: `uvicorn.run(...)` |
| Modify: `traveling_salesman_problem/simulation/simulation_state.py` | Add `initialize_headless()`, `_create_headless_controls()`, `restart_vehicle_genetic()`, `clear_all_blocked()` |
| Modify: `requirements.txt` | Add fastapi, uvicorn, websockets |
| Create: `frontend/` (Vue 3 + Vite project) | Dashboard UI |
| Create: `frontend/src/composables/useWebSocket.ts` | WS connection + state ref |
| Create: `frontend/src/canvas/mapRenderer.ts` | Canvas 2D drawing |
| Create: `frontend/src/components/*.vue` | Layout components |
| Test: `tests/test_headless_controls.py` | |
| Test: `tests/test_state_serializer.py` | |
| Test: `tests/test_command_handler.py` | |
| Test: `tests/test_simulation_service.py` | |
| Test: `tests/test_web_blocked_toggle.py` | |

---

### Task 1: Headless controls

**Files:**
- Create: `traveling_salesman_problem/web/__init__.py`
- Create: `traveling_salesman_problem/web/headless_controls.py`
- Test: `tests/test_headless_controls.py`

**Interfaces:**
- Produces:
```python
class HeadlessSlider:
    value: float
    minimum_value: float
    maximum_value: float
    label: str
    @property
    def integer_value(self) -> int: ...

class HeadlessToggle:
    is_active: bool
    label: str

class HeadlessButton:
    label: str
    subtitle: str = ""
    was_pressed: bool = False
```

- [ ] **Step 1: Write the failing test**

```python
# tests/test_headless_controls.py
from traveling_salesman_problem.web.headless_controls import (
    HeadlessSlider,
    HeadlessToggle,
    HeadlessButton,
)

def test_headless_slider_integer_value_rounds():
    slider = HeadlessSlider(value=2.6, minimum_value=1.0, maximum_value=5.0, label="Veículos")
    assert slider.integer_value == 3

def test_headless_slider_clamps_on_set():
    slider = HeadlessSlider(value=0.5, minimum_value=0.0, maximum_value=1.0, label="Mutação")
    slider.value = 1.5
    assert slider.value == 1.0

def test_headless_toggle_defaults_inactive():
    toggle = HeadlessToggle(label="2-opt", is_active=False)
    assert toggle.is_active is False
    toggle.is_active = True
    assert toggle.is_active is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_headless_controls.py -v`  
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# traveling_salesman_problem/web/headless_controls.py
from dataclasses import dataclass, field

@dataclass
class HeadlessSlider:
    minimum_value: float
    maximum_value: float
    label: str
    value: float = 0.0

    def __post_init__(self) -> None:
        self.value = self._clamp(self.value)

    def _clamp(self, raw: float) -> float:
        return max(self.minimum_value, min(self.maximum_value, float(raw)))

    @property
    def integer_value(self) -> int:
        return int(round(self.value))

    def set_value(self, raw: float) -> None:
        self.value = self._clamp(raw)

@dataclass
class HeadlessToggle:
    label: str
    is_active: bool = False

@dataclass
class HeadlessButton:
    label: str
    subtitle: str = ""
    was_pressed: bool = False
```

Note: use explicit property pattern or `__setattr__` override so assignment clamps correctly.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_headless_controls.py -v`  
Expected: PASS

- [ ] **Step 5: Verify desktop unaffected**

Run: `python -m pytest tests/ -v --ignore=tests/test_headless_controls.py -q`  
Expected: all existing tests PASS

---

### Task 2: `initialize_headless()` on SimulationState

**Files:**
- Modify: `traveling_salesman_problem/simulation/simulation_state.py`
- Test: `tests/test_headless_controls.py` (extend)

**Interfaces:**
- Consumes: Task 1 `HeadlessSlider`, `HeadlessToggle`, `HeadlessButton`
- Produces:
```python
# SimulationState
def initialize_headless(self) -> None: ...
def restart_vehicle_genetic(self) -> None: ...
def clear_all_blocked(self) -> None: ...
```

- [ ] **Step 1: Write the failing test**

```python
# tests/test_headless_controls.py (append)
from traveling_salesman_problem.config.application_settings import ApplicationSettings
from traveling_salesman_problem.simulation.simulation_state import SimulationState
from traveling_salesman_problem.web.headless_controls import HeadlessSlider

def test_initialize_headless_creates_controls_without_pygame_widgets():
    simulation = SimulationState(settings=ApplicationSettings())
    simulation.initialize_headless()
    assert simulation.mutation_slider is not None
    assert isinstance(simulation.mutation_slider, HeadlessSlider)
    assert simulation.depot is not None
    assert len(simulation.deliveries) > 0
    assert len(simulation.vehicle_states) > 0

def test_restart_vehicle_genetic_resets_generation_counter():
    simulation = SimulationState(settings=ApplicationSettings())
    simulation.initialize_headless()
    simulation.run_one_generation()
    second_gen, *_ = simulation.run_one_generation()
    assert second_gen == 2
    simulation.restart_vehicle_genetic()
    first_after_restart, *_ = simulation.run_one_generation()
    assert first_after_restart == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_headless_controls.py::test_initialize_headless_creates_controls_without_pygame_widgets -v`  
Expected: FAIL — `initialize_headless` not defined

- [ ] **Step 3: Implement `_create_headless_controls()` and `initialize_headless()`**

Add import at top of `simulation_state.py`:
```python
from traveling_salesman_problem.web.headless_controls import (
    HeadlessButton,
    HeadlessSlider,
    HeadlessToggle,
)
```

Add methods (mirror values from `_create_control_widgets` but without pygame rects):
```python
def initialize_headless(self) -> None:
    self.show_mesh = self.settings.initial_show_mesh
    self._create_headless_controls()
    self.shuffle_all()
    self._sync_capacity_to_maximum()

def _create_headless_controls(self) -> None:
    settings = self.settings
    saved_two_opt = self.two_opt_toggle.is_active if self.two_opt_toggle is not None else False
    saved_show_mesh = (
        self.mesh_toggle.is_active if self.mesh_toggle is not None else settings.initial_show_mesh
    )
    self.mutation_slider = HeadlessSlider(
        value=settings.initial_mutation_probability,
        minimum_value=0.0,
        maximum_value=1.0,
        label="Taxa de mutação",
    )
    self.priority_weight_slider = HeadlessSlider(
        value=settings.initial_priority_weight,
        minimum_value=0.0,
        maximum_value=100.0,
        label="Peso da prioridade",
    )
    self.two_opt_toggle = HeadlessToggle(label="Refinamento 2-opt", is_active=saved_two_opt)
    self.mesh_toggle = HeadlessToggle(label="Mostrar malha", is_active=saved_show_mesh)
    self.show_mesh = saved_show_mesh
    self.vehicle_count_slider = HeadlessSlider(
        value=float(settings.initial_vehicle_count),
        minimum_value=1.0,
        maximum_value=float(settings.maximum_vehicle_count),
        label="Veículos",
    )
    self.capacity_slider = HeadlessSlider(
        value=float(settings.initial_capacity),
        minimum_value=float(settings.minimum_capacity),
        maximum_value=float(settings.initial_capacity),
        label="Capacidade",
    )
    self.transit_count_slider = HeadlessSlider(
        value=float(settings.initial_transit_count),
        minimum_value=1.0,
        maximum_value=float(settings.maximum_mesh_nodes_per_type),
        label="Trânsito",
    )
    self.regenerate_positions_button = HeadlessButton(
        label="Sortear posições",
        subtitle="Depósito, entregas e malha",
    )
    self.hospital_preset_button = HeadlessButton(label="Cenário hospitalar")
    self.focus_filter_button = HeadlessButton(label=self.focus_filter_label())

def restart_vehicle_genetic(self) -> None:
    if self.mesh is None or self.depot is None:
        return
    settings = self.settings
    capacity = self.capacity_slider.integer_value
    priority_weight = self.priority_weight
    for vehicle_id, points in self.assignment.items():
        tokens = []
        for point in points:
            tokens.extend(split_into_tokens(point, capacity))
        self.vehicle_states[vehicle_id] = initialize_vehicle_genetic(
            vehicle_id=vehicle_id,
            tokens=tokens,
            population_size=settings.population_size,
            depot=self.depot,
            mesh=self.mesh,
            capacity=capacity,
            priority_weight=priority_weight,
            blocked_node_penalty=settings.blocked_node_penalty,
        )
    self.generation_counter = itertools.count(start=1)
    self.last_priority_weight = priority_weight

def clear_all_blocked(self) -> None:
    if self.mesh is None or self.depot is None:
        return
    if not self.mesh.blocked_ids:
        return
    transit_count = len(self.mesh.transit_ids)
    self.mesh = build_vrp_mesh(
        self.depot,
        self.deliveries,
        self.map_bounds(),
        transit_count=transit_count,
        rng_seed=_mesh_rng_seed(self.depot, self.deliveries, transit_count),
        maximum_transit=self.settings.maximum_mesh_nodes_per_type,
    )
    self._rescore_stored_plans_fitness()
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_headless_controls.py -v`  
Expected: PASS

- [ ] **Step 5: Verify desktop**

Run: `python -m pytest tests/ -v -q`  
Expected: all PASS

---

### Task 3: Log buffer

**Files:**
- Create: `traveling_salesman_problem/web/log_buffer.py`
- Test: `tests/test_log_buffer.py`

**Interfaces:**
- Produces:
```python
class LogBuffer:
    def append(self, log_type: str, message: str) -> None: ...
    def snapshot(self, limit: int = 200) -> list[dict]: ...
    def clear(self) -> None: ...
```

- [ ] **Step 1: Write failing test**

```python
def test_log_buffer_keeps_last_n_entries():
    buffer = LogBuffer(max_entries=3)
    for index in range(5):
        buffer.append("generation", f"msg {index}")
    entries = buffer.snapshot()
    assert len(entries) == 3
    assert entries[0]["message"] == "msg 2"
```

- [ ] **Step 2–4: Implement and verify**

- [ ] **Step 5: Run** `python -m pytest tests/test_log_buffer.py -v` → PASS

---

### Task 4: State serializer

**Files:**
- Create: `traveling_salesman_problem/web/state_serializer.py`
- Test: `tests/test_state_serializer.py`

**Interfaces:**
- Consumes: `SimulationState`, last `run_one_generation()` outputs, `TripAnimationState` cursor
- Produces:
```python
def serialize_state(
    simulation: SimulationState,
    *,
    generation_number: int,
    total_fitness: float,
    total_distance: float,
    total_priority: float,
    plans: dict,
    runner_up_plans: dict,
    histories: dict,
    running: bool,
    fps: float,
    animation: dict | None,
    logs: list[dict],
) -> dict: ...
```

- [ ] **Step 1: Write failing test**

```python
def test_serialize_state_has_required_keys():
    simulation = SimulationState(settings=ApplicationSettings())
    simulation.initialize_headless()
    gen, fitness, dist, prior, plans, runner_up, histories = simulation.run_one_generation()
    payload = serialize_state(
        simulation,
        generation_number=gen,
        total_fitness=fitness,
        total_distance=dist,
        total_priority=prior,
        plans=plans,
        runner_up_plans=runner_up,
        histories=histories,
        running=True,
        fps=30.0,
        animation=None,
        logs=[],
    )
    assert payload["type"] == "state_update"
    for key in ("generation", "metrics", "params", "toggles", "map", "plans", "routes_panel"):
        assert key in payload
```

- [ ] **Step 2: Run test** → FAIL

- [ ] **Step 3: Implement serializer**

Key helpers:
```python
def _rgb_to_hex(color: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*color)

def _serialize_map(simulation: SimulationState) -> dict: ...
def _serialize_plans(mesh, plans: dict, capacity: int) -> dict: ...
def _serialize_routes_panel(plans: dict, capacity: int, focus_vehicle_id) -> list: ...
```

Reuse:
- `build_route_panel_rows()` for `routes_panel`
- `VisualTheme.vehicle_route_colors`, `priority_to_color()`
- `expand_route_polyline()` for polylines per trip
- `simulation.map_bounds()` for bounds

- [ ] **Step 4: Run** `python -m pytest tests/test_state_serializer.py -v` → PASS

---

### Task 5: Command handler

**Files:**
- Create: `traveling_salesman_problem/web/command_handler.py`
- Test: `tests/test_command_handler.py`

**Interfaces:**
- Consumes: `SimulationState`, `LogBuffer`
- Produces:
```python
class CommandHandler:
    def __init__(self, simulation: SimulationState, logs: LogBuffer) -> None: ...
    def handle(self, command: dict) -> str | None: ...
    # Returns error message or None on success
```

- [ ] **Step 1: Write failing tests for each command**

```python
PARAM_KEYS = {
    "mutation": "mutation_slider",
    "priority_weight": "priority_weight_slider",
    "vehicle_count": "vehicle_count_slider",
    "capacity": "capacity_slider",
    "transit_count": "transit_count_slider",
}

def test_set_param_mutation():
    simulation = SimulationState(settings=ApplicationSettings())
    simulation.initialize_headless()
    handler = CommandHandler(simulation, LogBuffer())
    assert handler.handle({"type": "command", "action": "set_param", "key": "mutation", "value": 0.25}) is None
    assert simulation.mutation_slider.value == 0.25

def test_action_shuffle_positions():
    simulation = SimulationState(settings=ApplicationSettings())
    simulation.initialize_headless()
    old_depot = simulation.depot
    handler = CommandHandler(simulation, LogBuffer())
    handler.handle({"type": "command", "action": "action", "name": "shuffle_positions"})
    assert simulation.depot != old_depot

def test_set_focus_vehicle():
    simulation = SimulationState(settings=ApplicationSettings())
    simulation.initialize_headless()
    handler = CommandHandler(simulation, LogBuffer())
    handler.handle({"type": "command", "action": "set_focus", "vehicle_id": 0, "trip_index": None})
    assert simulation.focus_vehicle_id == 0

def test_toggle_blocked_at_map_coordinate():
    simulation = SimulationState(settings=ApplicationSettings())
    simulation.initialize_headless()
    depot = simulation.depot
    handler = CommandHandler(simulation, LogBuffer())
    handler.handle({"type": "command", "action": "toggle_blocked", "map_x": depot[0], "map_y": depot[1]})
    assert DEPOT_ID in simulation.mesh.blocked_ids
```

- [ ] **Step 2–3: Implement `CommandHandler.handle()`**

```python
def handle(self, command: dict) -> str | None:
    action = command.get("action")
    if action == "set_param":
        return self._set_param(command.get("key"), command.get("value"))
    if action == "set_toggle":
        return self._set_toggle(command.get("key"), command.get("active"))
    if action == "action":
        return self._run_action(command.get("name"))
    if action == "set_focus":
        return self._set_focus(command.get("vehicle_id"), command.get("trip_index"))
    if action == "toggle_blocked":
        return self._toggle_blocked(command.get("map_x"), command.get("map_y"))
    if action in ("pause", "resume"):
        return None  # handled by SimulationService
    return f"Ação desconhecida: {action}"
```

Action mapping:
| `name` | Method |
|--------|--------|
| `shuffle_positions` | `simulation.shuffle_all()` |
| `hospital_preset` | `simulation.apply_hospital_preset()` |
| `restart_algorithm` | `simulation.restart_vehicle_genetic()` |
| `clear_blocked` | `simulation.clear_all_blocked()` |

After param/toggle changes call `simulation.update_controls_if_changed()`.

- [ ] **Step 4: Run** `python -m pytest tests/test_command_handler.py -v` → PASS

---

### Task 6: SimulationService

**Files:**
- Create: `traveling_salesman_problem/web/simulation_service.py`
- Test: `tests/test_simulation_service.py`

**Interfaces:**
- Consumes: Tasks 3–5
- Produces:
```python
class SimulationService:
    paused: bool
    def __init__(self) -> None: ...
    def startup(self) -> None: ...
    async def run_loop(self, broadcast) -> None: ...
    def handle_command(self, command: dict) -> dict | None: ...
    def build_state_payload(self) -> dict: ...
```

- [ ] **Step 1: Write failing test**

```python
@pytest.mark.asyncio
async def test_simulation_service_runs_one_generation_while_not_paused():
    service = SimulationService()
    service.startup()
    service.paused = True
    payloads = []
    async def capture(payload):
        payloads.append(payload)
    await service.run_loop(capture, max_ticks=1)
    assert len(payloads) == 1
    assert payloads[0]["type"] == "state_update"
```

- [ ] **Step 2–3: Implement service**

Loop body (sync generation inside async):
```python
async def run_loop(self, broadcast, max_ticks: int | None = None) -> None:
    ticks = 0
    while max_ticks is None or ticks < max_ticks:
        if not self.paused:
            result = self.simulation.run_one_generation()
            self._store_generation_result(result)
            self.logs.append("generation", self._format_generation_log(result))
        self._advance_animation()
        await broadcast(self.build_state_payload())
        await asyncio.sleep(1 / self.settings.frames_per_second)
        ticks += 1
```

`handle_command` delegates to `CommandHandler`; handles `pause`/`resume` on `self.paused`.

- [ ] **Step 4: Run** `python -m pytest tests/test_simulation_service.py -v` → PASS

---

### Task 7: FastAPI server + entry point

**Files:**
- Create: `traveling_salesman_problem/web/server.py`
- Create: `web.py`
- Modify: `requirements.txt`

**Interfaces:**
- Produces: `app: FastAPI`, runnable via `python web.py`

- [ ] **Step 1: Add dependencies to `requirements.txt`**

```
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
websockets>=12.0
```

- [ ] **Step 2: Implement server**

```python
# traveling_salesman_problem/web/server.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

def create_app(service: SimulationService) -> FastAPI:
    app = FastAPI()
    clients: set[WebSocket] = set()

    @app.on_event("startup")
    async def startup():
        asyncio.create_task(service.run_loop(broadcast))

    async def broadcast(payload: dict):
        dead = []
        for ws in clients:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            clients.discard(ws)

    @app.websocket("/ws")
    async def ws_endpoint(websocket: WebSocket):
        await websocket.accept()
        clients.add(websocket)
        await websocket.send_json(service.build_state_payload())
        try:
            while True:
                msg = await websocket.receive_json()
                error = service.handle_command(msg)
                if error:
                    await websocket.send_json({"type": "error", "message": error})
        except WebSocketDisconnect:
            clients.discard(websocket)

    dist = Path("frontend/dist")
    if dist.exists():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")
        @app.get("/")
        async def index():
            return FileResponse(dist / "index.html")
    return app
```

```python
# web.py
import uvicorn
from traveling_salesman_problem.web.server import create_app
from traveling_salesman_problem.web.simulation_service import SimulationService

if __name__ == "__main__":
    service = SimulationService()
    service.startup()
    app = create_app(service)
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

- [ ] **Step 3: Smoke test backend only**

Run: `python web.py` (background)  
Test with Python client:
```python
import asyncio, websockets, json
async def main():
    async with websockets.connect("ws://127.0.0.1:8000/ws") as ws:
        msg = json.loads(await ws.recv())
        assert msg["type"] == "state_update"
asyncio.run(main())
```
Expected: receives `state_update` within 2 seconds

- [ ] **Step 4: Verify desktop** `python -m pytest tests/ -q` → PASS

---

### Task 8: Frontend scaffold (Vue 3 + Vite)

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/index.html`
- Create: `frontend/src/main.ts`
- Create: `frontend/src/App.vue`

- [ ] **Step 1: Scaffold project**

```bash
cd frontend
npm create vite@latest . -- --template vue-ts
npm install chart.js
```

- [ ] **Step 2: Configure Vite proxy for dev**

```typescript
// frontend/vite.config.ts
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      "/ws": { target: "ws://127.0.0.1:8000", ws: true },
    },
  },
  build: { outDir: "dist" },
});
```

- [ ] **Step 3: Minimal `App.vue` placeholder**

```vue
<template>
  <div class="app">
    <h1>VRP Hospitalar · Web</h1>
    <p v-if="connected">Geração: {{ state?.generation ?? "—" }}</p>
    <p v-else>Conectando...</p>
  </div>
</template>
```

- [ ] **Step 4: Build and verify**

```bash
cd frontend && npm run build
python web.py
```
Open `http://127.0.0.1:8000` — page loads

---

### Task 9: `useWebSocket` composable

**Files:**
- Create: `frontend/src/composables/useWebSocket.ts`
- Create: `frontend/src/types/simulation.ts`
- Modify: `frontend/src/App.vue`

**Interfaces:**
- Produces:
```typescript
export function useWebSocket(url = `ws://${location.host}/ws`) {
  const state: Ref<StateUpdate | null>
  const connected: Ref<boolean>
  const lastError: Ref<string | null>
  function sendCommand(command: Record<string, unknown>): void
  return { state, connected, lastError, sendCommand }
}
```

- [ ] **Step 1: Define TypeScript types matching serializer output**

- [ ] **Step 2: Implement composable with auto-reconnect**

- [ ] **Step 3: Wire into `App.vue`, confirm generation counter updates live**

---

### Task 10: Sidebar — params, toggles, actions, routes

**Files:**
- Create: `frontend/src/components/SidebarParams.vue`
- Create: `frontend/src/components/SidebarToggles.vue`
- Create: `frontend/src/components/SidebarActions.vue`
- Create: `frontend/src/components/SidebarRoutes.vue`
- Create: `frontend/src/components/SidebarInfo.vue`

- [ ] **Step 1: `SidebarParams` — 5 range inputs bound to `state.params`**

On `input` event:
```typescript
sendCommand({ type: "command", action: "set_param", key, value })
```

- [ ] **Step 2: `SidebarToggles` — checkboxes for `two_opt`, `show_mesh`**

- [ ] **Step 3: `SidebarActions` — buttons for shuffle, hospital, restart, clear_blocked**

- [ ] **Step 4: `SidebarRoutes` — render `state.routes_panel`; click sends `set_focus`**

- [ ] **Step 5: `SidebarInfo` — render `state.summary`**

- [ ] **Step 6: Manual test — each control changes backend state visible in next `state_update`**

---

### Task 11: MapCanvas — static layers

**Files:**
- Create: `frontend/src/canvas/mapRenderer.ts`
- Create: `frontend/src/canvas/mapTransform.ts`
- Create: `frontend/src/components/MapCanvas.vue`

**Interfaces:**
- Produces:
```typescript
export function worldToCanvas(x: number, y: number, transform: MapTransform): [number, number]
export function canvasToWorld(x: number, y: number, transform: MapTransform): [number, number]
export function drawMap(ctx: CanvasRenderingContext2D, state: StateUpdate, transform: MapTransform): void
```

- [ ] **Step 1: Implement `mapTransform` — fit `map.bounds` into canvas rect with padding**

- [ ] **Step 2: Draw layers 1–3, 6–8 (background, mesh, transit, deliveries, depot, blocked)**

Use colors from `state.map.theme`. Delivery color from priority gradient (port `priority_to_color` logic to JS or send hex per delivery from backend).

- [ ] **Step 3: Click handler — `canvasToWorld` → `toggle_blocked` command**

- [ ] **Step 4: Hover tooltip on deliveries showing id + priority**

---

### Task 12: MapCanvas — routes, runner-up, animation

**Files:**
- Modify: `frontend/src/canvas/mapRenderer.ts`
- Create: `frontend/src/components/MapToolbar.vue`

- [ ] **Step 1: Draw vehicle routes from `state.plans` polylines**

Solid line trip 1, dashed trips 2+. Colors from `state.map.theme.vehicle_colors`.

- [ ] **Step 2: Draw runner-up when `state.focus.vehicle_id` set and `state.runner_up` present**

- [ ] **Step 3: Draw direction arrows along polylines (sample every N pixels)**

- [ ] **Step 4: Draw animation cursor from `state.animation.position`**

- [ ] **Step 5: `MapToolbar` — vehicle filter dropdown sends `set_focus`; mesh toggle sends `set_toggle`**

---

### Task 13: Tabs, chart, logs, header, footer

**Files:**
- Create: `frontend/src/components/TabPanel.vue`
- Create: `frontend/src/components/ConvergenceChart.vue`
- Create: `frontend/src/components/LogConsole.vue`
- Create: `frontend/src/components/AppHeader.vue`
- Create: `frontend/src/components/StatusFooter.vue`
- Create: `frontend/src/components/StatsTable.vue`
- Create: `frontend/src/components/HistoryList.vue`

- [ ] **Step 1: `TabPanel` with tabs Resumo / Estatísticas / Histórico / Logs**

- [ ] **Step 2: `ConvergenceChart` — Chart.js line per vehicle from `state.histories`**

- [ ] **Step 3: `StatsTable` — per-vehicle fitness, distance from `state.plans`**

- [ ] **Step 4: `HistoryList` — accumulate generation metrics client-side from each `state_update`**

- [ ] **Step 5: `LogConsole` — render `state.logs` with type filter**

- [ ] **Step 6: `AppHeader` — metrics + pause/resume + restart buttons**

- [ ] **Step 7: `StatusFooter` — generation, population, penalties, fps**

---

### Task 14: App shell layout

**Files:**
- Modify: `frontend/src/App.vue`
- Create: `frontend/src/styles/layout.css`

- [ ] **Step 1: CSS grid layout per spec (sidebar | tabs | map)**

- [ ] **Step 2: Wire all components together**

- [ ] **Step 3: Build production bundle**

```bash
cd frontend && npm run build
python web.py
```

- [ ] **Step 4: Full manual walkthrough of parity checklist (spec §7)**

---

### Task 15: Integration tests + regression

**Files:**
- Create: `tests/test_web_blocked_toggle.py`
- Modify: `tests/test_command_handler.py` (edge cases)

- [ ] **Step 1: Blocked toggle parity test**

```python
def test_web_toggle_blocked_matches_simulation_state():
    simulation = SimulationState(settings=ApplicationSettings())
    simulation.initialize_headless()
    depot = simulation.depot
    simulation.toggle_blocked_at((int(depot[0]), int(depot[1])))
    assert DEPOT_ID in simulation.mesh.blocked_ids
```

- [ ] **Step 2: Run full test suite**

Run: `python -m pytest tests/ -v`  
Expected: ALL PASS

- [ ] **Step 3: Run desktop smoke test**

Run: `python main.py` — window opens, simulation runs (manual, 10 seconds)

---

## Spec coverage checklist

| Spec requirement | Task |
|------------------|------|
| `python web.py` independent process | Task 7 |
| Desktop unchanged | Every task step 5 |
| Headless controls | Task 1–2 |
| WebSocket `state_update` | Task 4, 6, 7 |
| All commands | Task 5 |
| Canvas map all layers | Task 11–12 |
| Sidebar sliders/toggles/actions | Task 10 |
| Route panel `D → … → D` | Task 4, 10 |
| Focus filter + trip | Task 5, 10, 12 |
| Convergence chart | Task 13 |
| Logs tab | Task 3, 13 |
| Pause/resume | Task 5, 6, 13 |
| 4 tabs | Task 13–14 |
| Footer metrics | Task 13 |
| F5 polish | Out of scope |

---

## Execution commands (reference)

```bash
# Backend tests
python -m pytest tests/test_headless_controls.py tests/test_state_serializer.py tests/test_command_handler.py tests/test_simulation_service.py tests/test_web_blocked_toggle.py -v

# Dev mode
python web.py
cd frontend && npm run dev

# Production local
cd frontend && npm run build
python web.py
```
