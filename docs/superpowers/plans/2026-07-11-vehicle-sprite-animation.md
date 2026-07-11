# Vehicle Sprite Animation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the focused-vehicle route circle cursor with a tinted, rotating truck PNG sprite (16×16) that follows the existing animation polyline.

**Architecture:** Keep `build_animation_polyline` / `point_along_polyline` unchanged; add `heading_along_polyline` for segment angle; new `vehicle_sprite.py` loads/tints/rotates the PNG; `draw_animation_vehicle` in `map_renderer` blits the sprite or falls back to `draw_animation_cursor`. Wire in `pygame_application` only when `focus_vehicle_id` is set.

**Tech Stack:** Python 3, pygame-ce, unittest (`python -m unittest`)

## Global Constraints

- Asset path: `traveling_salesman_problem/assets/truck.png`
- PNG: flat silhouette, transparent background, truck pointing **right** (0° = east)
- Source resolution ~32×32; display size **16×16** px
- Tint: full vehicle route color (`VisualTheme.vehicle_route_colors`)
- Rotation: free rotation along current polyline segment direction
- Trigger: `focus_vehicle_id is not None` and drawable plan (unchanged)
- Speed: `ANIMATION_SPEED = 0.12` (unchanged)
- Fallback: missing/corrupt PNG → `draw_animation_cursor` (no crash)
- Out of scope: animation in “Todos” mode, runner-up animation, per-vehicle distinct shapes

**Spec:** `docs/superpowers/specs/2026-07-11-vehicle-sprite-animation-design.md`

---

## File Map

| File | Responsibility |
|------|----------------|
| `traveling_salesman_problem/assets/truck.png` | Base sprite (Cursor-generated, white silhouette) |
| `traveling_salesman_problem/visualization/vehicle_sprite.py` | Load, tint, scale, rotate |
| `traveling_salesman_problem/visualization/route_animation.py` | `heading_along_polyline` |
| `traveling_salesman_problem/visualization/map_renderer.py` | `draw_animation_vehicle` |
| `traveling_salesman_problem/simulation/pygame_application.py` | Animation loop wiring |
| `traveling_salesman_problem/config/visual_theme.py` | `vehicle_sprite_size = 16` |
| `traveling_salesman_problem/visualization/application_layout.py` | Legend label |
| `tests/test_route_animation.py` | Heading tests |
| `tests/test_vehicle_sprite.py` | Sprite load/tint/render tests |

---

### Task 1: `heading_along_polyline`

**Files:**
- Modify: `traveling_salesman_problem/visualization/route_animation.py`
- Test: `tests/test_route_animation.py`

**Interfaces:**
- Consumes: `Coordinate` from `road_network`, existing `point_along_polyline` segment logic
- Produces: `heading_along_polyline(points: List[Coordinate], progress: float) -> float` (degrees; 0 = east, clockwise screen coords)

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_route_animation.py`:

```python
from traveling_salesman_problem.visualization.route_animation import (
    build_animation_polyline,
    heading_along_polyline,
    point_along_polyline,
)


class HeadingAlongPolylineTests(unittest.TestCase):
    def test_horizontal_segment_points_east(self):
        points = [(0.0, 0.0), (10.0, 0.0)]
        self.assertAlmostEqual(heading_along_polyline(points, 0.25), 0.0, places=1)

    def test_vertical_segment_points_south(self):
        points = [(0.0, 0.0), (0.0, 10.0)]
        self.assertAlmostEqual(heading_along_polyline(points, 0.25), 90.0, places=1)

    def test_single_point_returns_zero(self):
        self.assertEqual(heading_along_polyline([(5.0, 5.0)], 0.5), 0.0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_route_animation.HeadingAlongPolylineTests -v`

Expected: FAIL with `ImportError` or `cannot import name 'heading_along_polyline'`

- [ ] **Step 3: Implement `heading_along_polyline`**

Add to `traveling_salesman_problem/visualization/route_animation.py`:

```python
def _segment_index_and_ratio(
    points: List[Coordinate],
    progress: float,
) -> tuple[int, float]:
    if len(points) < 2:
        return 0, 0.0

    progress = progress % 1.0
    if progress < 0:
        progress += 1.0

    lengths = []
    total = 0.0
    for index in range(len(points) - 1):
        segment = math.hypot(
            points[index + 1][0] - points[index][0],
            points[index + 1][1] - points[index][1],
        )
        lengths.append(segment)
        total += segment

    if total <= 1e-9:
        return 0, 0.0

    target = progress * total
    accumulated = 0.0
    for index, segment in enumerate(lengths):
        if accumulated + segment >= target:
            if segment <= 1e-9:
                return index, 0.0
            return index, (target - accumulated) / segment
        accumulated += segment
    return len(lengths) - 1, 1.0


def heading_along_polyline(
    points: List[Coordinate],
    progress: float,
) -> float:
    if len(points) < 2:
        return 0.0

    index, _ratio = _segment_index_and_ratio(points, progress)
    x0, y0 = points[index]
    x1, y1 = points[min(index + 1, len(points) - 1)]
    dx = x1 - x0
    dy = y1 - y0
    if abs(dx) <= 1e-9 and abs(dy) <= 1e-9:
        return 0.0
    return math.degrees(math.atan2(dy, dx))
```

Refactor `point_along_polyline` to call `_segment_index_and_ratio` (DRY) — keep existing behavior identical.

- [ ] **Step 4: Run tests**

Run: `python -m unittest tests.test_route_animation -v`

Expected: PASS (all tests in file)

- [ ] **Step 5: Commit**

```bash
git add traveling_salesman_problem/visualization/route_animation.py tests/test_route_animation.py
git commit -m "feat(animation): add heading along polyline"
```

---

### Task 2: Truck asset + `vehicle_sprite.py`

**Files:**
- Create: `traveling_salesman_problem/assets/truck.png`
- Create: `traveling_salesman_problem/visualization/vehicle_sprite.py`
- Test: `tests/test_vehicle_sprite.py`

**Interfaces:**
- Produces:
  - `VEHICLE_SPRITE_PATH: Path`
  - `load_vehicle_sprite_base() -> Optional[pygame.Surface]`
  - `tint_surface(surface: pygame.Surface, color: Tuple[int,int,int]) -> pygame.Surface`
  - `render_vehicle_sprite(color: Tuple[int,int,int], angle_deg: float, size: int = 16) -> Optional[pygame.Surface]`
  - `preload_vehicle_sprite() -> bool` (optional eager load; returns True if base loaded)

- [ ] **Step 1: Generate and add `truck.png`**

Use Cursor image generation (or equivalent) with prompt:

> Flat minimal delivery truck icon, side view facing right, white silhouette on fully transparent background, no text, no shadow, 32x32 pixels, simple geometric style suitable for color tinting in a logistics map UI.

Save to `traveling_salesman_problem/assets/truck.png`.

- [ ] **Step 2: Write failing sprite tests**

Create `tests/test_vehicle_sprite.py`:

```python
"""Testes do sprite de caminhão na animação."""

import unittest

import pygame

from traveling_salesman_problem.config.visual_theme import VisualTheme
from traveling_salesman_problem.visualization.vehicle_sprite import (
    VEHICLE_SPRITE_PATH,
    load_vehicle_sprite_base,
    render_vehicle_sprite,
    tint_surface,
)


class VehicleSpriteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    def test_asset_path_exists(self):
        self.assertTrue(VEHICLE_SPRITE_PATH.is_file())

    def test_load_base_returns_surface_with_alpha(self):
        base = load_vehicle_sprite_base()
        self.assertIsNotNone(base)
        assert base is not None
        self.assertGreater(base.get_width(), 0)
        self.assertTrue(base.get_flags() & pygame.SRCALPHA)

    def test_tint_changes_visible_pixels(self):
        base = load_vehicle_sprite_base()
        self.assertIsNotNone(base)
        assert base is not None
        tinted = tint_surface(base, VisualTheme.vehicle_route_colors[0])
        self.assertNotEqual(base.get_at((base.get_width() // 2, base.get_height() // 2)), tinted.get_at((base.get_width() // 2, base.get_height() // 2)))

    def test_render_vehicle_sprite_scaled(self):
        rendered = render_vehicle_sprite(VisualTheme.vehicle_route_colors[1], 45.0, size=16)
        self.assertIsNotNone(rendered)
        assert rendered is not None
        self.assertGreaterEqual(rendered.get_width(), 1)
        self.assertGreaterEqual(rendered.get_height(), 1)
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python -m unittest tests.test_vehicle_sprite -v`

Expected: FAIL — module or asset missing

- [ ] **Step 4: Implement `vehicle_sprite.py`**

Create `traveling_salesman_problem/visualization/vehicle_sprite.py`:

```python
"""Sprite de caminhão para animação de rota (PNG gerado para o projeto)."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import pygame

Color = Tuple[int, int, int]

VEHICLE_SPRITE_PATH = (
    Path(__file__).resolve().parent.parent / "assets" / "truck.png"
)

_base_surface: Optional[pygame.Surface] = None
_load_failed = False


def load_vehicle_sprite_base() -> Optional[pygame.Surface]:
    global _base_surface, _load_failed
    if _load_failed:
        return None
    if _base_surface is not None:
        return _base_surface
    if not VEHICLE_SPRITE_PATH.is_file():
        _load_failed = True
        return None
    try:
        loaded = pygame.image.load(str(VEHICLE_SPRITE_PATH)).convert_alpha()
    except pygame.error:
        _load_failed = True
        return None
    _base_surface = loaded
    return _base_surface


def preload_vehicle_sprite() -> bool:
    return load_vehicle_sprite_base() is not None


def tint_surface(surface: pygame.Surface, color: Color) -> pygame.Surface:
    tinted = surface.copy()
    tinted.fill((*color, 255), special_flags=pygame.BLEND_RGBA_MULT)
    return tinted


def render_vehicle_sprite(
    color: Color,
    angle_deg: float,
    size: int = 16,
) -> Optional[pygame.Surface]:
    base = load_vehicle_sprite_base()
    if base is None:
        return None
    tinted = tint_surface(base, color)
    if base.get_width() != size or base.get_height() != size:
        tinted = pygame.transform.smoothscale(tinted, (size, size))
    return pygame.transform.rotate(tinted, -angle_deg)
```

Note: negate `angle_deg` because pygame rotates counter-clockwise while `atan2` heading uses screen coordinates.

- [ ] **Step 5: Run tests**

Run: `python -m unittest tests.test_vehicle_sprite -v`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add traveling_salesman_problem/assets/truck.png traveling_salesman_problem/visualization/vehicle_sprite.py tests/test_vehicle_sprite.py
git commit -m "feat(ui): add truck sprite asset and renderer"
```

---

### Task 3: `draw_animation_vehicle` + pygame wiring

**Files:**
- Modify: `traveling_salesman_problem/visualization/map_renderer.py`
- Modify: `traveling_salesman_problem/simulation/pygame_application.py`
- Modify: `traveling_salesman_problem/config/visual_theme.py`
- Test: `tests/test_vehicle_sprite.py` (add draw smoke test optional) or manual only

**Interfaces:**
- Consumes: `render_vehicle_sprite(color, angle_deg, size)` from Task 2; `heading_along_polyline` from Task 1
- Produces: `draw_animation_vehicle(screen, point, angle_deg, color, sprite_size=16) -> None`

- [ ] **Step 1: Add `vehicle_sprite_size` to theme**

In `traveling_salesman_problem/config/visual_theme.py` after `depot_marker_size`:

```python
vehicle_sprite_size: int = 16
```

- [ ] **Step 2: Add `draw_animation_vehicle` to map_renderer**

Add import:

```python
from traveling_salesman_problem.visualization.vehicle_sprite import render_vehicle_sprite
```

Add function after `draw_animation_cursor`:

```python
def draw_animation_vehicle(
    screen: pygame.Surface,
    point: CityCoordinate,
    angle_deg: float,
    color: Tuple[int, int, int],
    sprite_size: int = VisualTheme.vehicle_sprite_size,
) -> None:
    sprite = render_vehicle_sprite(color, angle_deg, size=sprite_size)
    if sprite is None:
        draw_animation_cursor(screen, point, color, radius=max(6, sprite_size // 2))
        return
    rect = sprite.get_rect(center=(int(point[0]), int(point[1])))
    screen.blit(sprite, rect)
```

- [ ] **Step 3: Wire `pygame_application.py`**

Add imports:

```python
from traveling_salesman_problem.visualization.map_renderer import (
    draw_animation_cursor,
    draw_animation_vehicle,
    ...
)
from traveling_salesman_problem.visualization.route_animation import (
    build_animation_polyline,
    heading_along_polyline,
    point_along_polyline,
)
from traveling_salesman_problem.visualization.vehicle_sprite import preload_vehicle_sprite
```

After `pygame.init()` / before main loop, call:

```python
preload_vehicle_sprite()
```

Replace animation block (~lines 296–304):

```python
if focus_id is not None and focus_id in plans and simulation.mesh is not None:
    polyline = build_animation_polyline(simulation.mesh, plans[focus_id])
    if len(polyline) >= 2:
        dt_seconds = clock.get_time() / 1000.0
        animation_progress = (animation_progress + ANIMATION_SPEED * dt_seconds) % 1.0
        position = point_along_polyline(polyline, animation_progress)
        heading = heading_along_polyline(polyline, animation_progress)
        color = VisualTheme.vehicle_route_colors[
            focus_id % len(VisualTheme.vehicle_route_colors)
        ]
        draw_animation_vehicle(screen, position, heading, color)
```

Remove unused `draw_animation_cursor` import if no longer referenced directly in this file (still used via fallback inside `draw_animation_vehicle`).

- [ ] **Step 4: Run regression**

Run: `python -m unittest discover -s tests -q`

Expected: PASS (all tests)

- [ ] **Step 5: Commit**

```bash
git add traveling_salesman_problem/config/visual_theme.py traveling_salesman_problem/visualization/map_renderer.py traveling_salesman_problem/simulation/pygame_application.py
git commit -m "feat(ui): draw truck sprite on focused route"
```

---

### Task 4: Legend + exports

**Files:**
- Modify: `traveling_salesman_problem/visualization/application_layout.py`
- Modify: `traveling_salesman_problem/visualization/__init__.py` (if exports needed)

**Interfaces:**
- Consumes: `VisualTheme.vehicle_route_colors[0]` for legend swatch color

- [ ] **Step 1: Update legend**

In `draw_map_legend`, insert after `"Rota veículo"`:

```python
(VisualTheme.vehicle_route_colors[0], "Veículo em rota (foco)"),
```

- [ ] **Step 2: Export new symbols (optional)**

In `visualization/__init__.py`, add if project re-exports renderer helpers:

```python
from traveling_salesman_problem.visualization.map_renderer import draw_animation_vehicle
```

- [ ] **Step 3: Run tests**

Run: `python -m unittest discover -s tests -q`

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add traveling_salesman_problem/visualization/application_layout.py traveling_salesman_problem/visualization/__init__.py
git commit -m "feat(ui): add focused vehicle legend entry"
```

---

### Task 5: Regression + manual smoke

**Files:** none new

- [ ] **Step 1: Full test suite**

Run: `python -m unittest discover -s tests -q`

Expected: `OK` (88+ tests)

- [ ] **Step 2: Manual smoke**

Run: `python main.py`

Checklist:
1. Cycle focus to `V1` → colored truck (~16px) moves along route and rotates on turns
2. Cycle to `V2` → truck color changes to second palette color
3. Cycle to `Todos` → no truck/cursor animation
4. Temporarily rename `truck.png` → app still runs with circle fallback (revert after check)

- [ ] **Step 3: Commit plan doc (if not committed)**

```bash
git add docs/superpowers/plans/2026-07-11-vehicle-sprite-animation.md
git commit -m "docs: vehicle sprite animation plan"
```

---

## Spec Coverage Check

| Spec requirement | Task |
|------------------|------|
| PNG asset in repo | Task 2 |
| 16×16 display, tint full color | Task 2, 3 |
| Rotate with segment | Task 1, 3 |
| Focus-only trigger | Task 3 |
| ANIMATION_SPEED unchanged | Task 3 (no change) |
| Fallback to circle | Task 3 |
| `heading_along_polyline` tests | Task 1 |
| Sprite tests | Task 2 |
| Legend update | Task 4 |
| Acceptance smoke | Task 5 |

## Type Consistency Check

- `heading_along_polyline(...) -> float` used by `pygame_application` and passed to `draw_animation_vehicle(..., angle_deg, ...)`
- `render_vehicle_sprite(color, angle_deg, size)` used by `draw_animation_vehicle`
- `VisualTheme.vehicle_sprite_size` default `16` used as `sprite_size` default
