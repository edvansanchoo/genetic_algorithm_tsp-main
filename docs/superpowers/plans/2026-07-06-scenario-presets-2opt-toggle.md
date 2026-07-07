# Scenario Presets & 2-opt Toggle — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a sidebar scenario selector (Aleatório + fixed presets for 5/10/12/15 cities) and a toggleable 2-opt refinement flag so users can compare algorithm measures on reproducible city layouts.

**Architecture:** Restructure `predefined_problems.py` into named `ScenarioPreset` entries. Add `ScenarioSelector` and `ToggleButton` widgets to the sidebar. Extend `SimulationState` with `apply_scenario()` (full reset on preset change) and pass `use_2opt` into `evolve_next_generation` (no reset on toggle). Wire drawing and event handling in `pygame_application.py`.

**Tech Stack:** Python 3.9+, Pygame, NumPy (existing). Unit tests via stdlib `unittest`.

## Global Constraints

- Package root: `traveling_salesman_problem/` (entry point `main.py`)
- Presets: **Aleatório**, **Pequeno (5)**, **Médio (10)**, **Grande (12)**, **Extra (15)**
- Preset change → **full reset** (cities, priorities, population, history, generation → 1)
- 2-opt toggle → applies **next generation only**; history and counter **unchanged**
- Default scenario: **`random`** (Aleatório); default 2-opt: **active**
- Priorities on preset change: new random draw (1–10), same as `initialize()`
- "Sortear posições" on fixed preset → switch to Aleatório + full reset + reshuffle
- Cenário hospitalar: **out of scope** — do not add hospital preset to scenario selector
- All user-facing strings in **Portuguese** (match existing UI)
- UI validation: manual per spec; unit tests for pure logic only

---

## File Map

| File | Responsibility |
|------|----------------|
| `genetic_algorithm/predefined_problems.py` | **Modify** — `ScenarioPreset` dataclass + `SCENARIO_PRESETS` |
| `genetic_algorithm/selection.py` | **Modify** — `use_2opt` parameter |
| `genetic_algorithm/__init__.py` | **Modify** — export new symbols |
| `visualization/widgets/scenario_selector.py` | **Create** — radio-style scenario buttons |
| `visualization/widgets/__init__.py` | **Modify** — export `ScenarioSelector`, `ToggleButton` |
| `simulation/simulation_state.py` | **Modify** — state, widgets, `apply_scenario`, wiring |
| `simulation/pygame_application.py` | **Modify** — draw new section, preserve state on resize |
| `tests/test_scenario_presets.py` | **Create** — unit tests for presets and 2-opt flag |

---

### Task 1: Scenario presets data model

**Files:**
- Modify: `traveling_salesman_problem/genetic_algorithm/predefined_problems.py`
- Modify: `traveling_salesman_problem/genetic_algorithm/__init__.py`
- Create: `tests/test_scenario_presets.py`

**Interfaces:**
- Consumes: nothing
- Produces:
  - `ScenarioPreset(label: str, city_count: int | None, coordinates: List[CityCoordinate] | None)`
  - `SCENARIO_PRESETS: Dict[str, ScenarioPreset]`
  - `get_scenario_coordinates(scenario_id: str) -> List[CityCoordinate] | None`
  - `get_scenario_city_count(scenario_id: str, default: int) -> int`
  - `predefined_city_problems` (backward-compat alias)

- [ ] **Step 1: Write the failing test**

Create `tests/test_scenario_presets.py`:

```python
import unittest

from traveling_salesman_problem.genetic_algorithm.predefined_problems import (
    SCENARIO_PRESETS,
    ScenarioPreset,
    get_scenario_city_count,
    get_scenario_coordinates,
    predefined_city_problems,
)


class ScenarioPresetTests(unittest.TestCase):
    def test_all_expected_presets_exist(self):
        expected_ids = {"random", "small_5", "medium_10", "large_12", "extra_15"}
        self.assertEqual(set(SCENARIO_PRESETS.keys()), expected_ids)

    def test_random_preset_has_no_fixed_coordinates(self):
        preset = SCENARIO_PRESETS["random"]
        self.assertIsNone(preset.city_count)
        self.assertIsNone(preset.coordinates)

    def test_small_5_has_five_fixed_coordinates(self):
        coordinates = get_scenario_coordinates("small_5")
        self.assertIsNotNone(coordinates)
        self.assertEqual(len(coordinates), 5)

    def test_get_scenario_city_count_uses_default_for_random(self):
        self.assertEqual(get_scenario_city_count("random", default=15), 15)

    def test_get_scenario_city_count_for_fixed_preset(self):
        self.assertEqual(get_scenario_city_count("medium_10", default=15), 10)

    def test_predefined_city_problems_backward_compat(self):
        self.assertEqual(len(predefined_city_problems[5]), 5)
        self.assertEqual(len(predefined_city_problems[15]), 15)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_scenario_presets.ScenarioPresetTests -v`  
Expected: FAIL with `ImportError` for `ScenarioPreset`, `get_scenario_coordinates`, etc.

- [ ] **Step 3: Write minimal implementation**

Replace `traveling_salesman_problem/genetic_algorithm/predefined_problems.py`:

```python
"""Instâncias fixas do problema para testes reproduzíveis."""

from dataclasses import dataclass
from typing import Dict, List, Tuple

CityCoordinate = Tuple[int, int]


@dataclass(frozen=True)
class ScenarioPreset:
    label: str
    city_count: int | None
    coordinates: List[CityCoordinate] | None


_FIXED_COORDINATES: Dict[int, List[CityCoordinate]] = {
    5: [(733, 251), (706, 87), (546, 97), (562, 49), (576, 253)],
    10: [
        (470, 169), (602, 202), (754, 239), (476, 233), (468, 301),
        (522, 29), (597, 171), (487, 325), (746, 232), (558, 136),
    ],
    12: [
        (728, 67), (560, 160), (602, 312), (712, 148), (535, 340),
        (720, 354), (568, 300), (629, 260), (539, 46), (634, 343),
        (491, 135), (768, 161),
    ],
    15: [
        (512, 317), (741, 72), (552, 50), (772, 346), (637, 12),
        (589, 131), (732, 165), (605, 15), (730, 38), (576, 216),
        (589, 381), (711, 387), (563, 228), (494, 22), (787, 288),
    ],
}

SCENARIO_PRESETS: Dict[str, ScenarioPreset] = {
    "random": ScenarioPreset(label="Aleatório", city_count=None, coordinates=None),
    "small_5": ScenarioPreset(label="Pequeno (5)", city_count=5, coordinates=_FIXED_COORDINATES[5]),
    "medium_10": ScenarioPreset(label="Médio (10)", city_count=10, coordinates=_FIXED_COORDINATES[10]),
    "large_12": ScenarioPreset(label="Grande (12)", city_count=12, coordinates=_FIXED_COORDINATES[12]),
    "extra_15": ScenarioPreset(label="Extra (15)", city_count=15, coordinates=_FIXED_COORDINATES[15]),
}

# Backward compatibility
predefined_city_problems: Dict[int, List[CityCoordinate]] = _FIXED_COORDINATES


def get_scenario_coordinates(scenario_id: str) -> List[CityCoordinate] | None:
    preset = SCENARIO_PRESETS[scenario_id]
    if preset.coordinates is None:
        return None
    return list(preset.coordinates)


def get_scenario_city_count(scenario_id: str, default: int) -> int:
    preset = SCENARIO_PRESETS[scenario_id]
    return preset.city_count if preset.city_count is not None else default
```

Update `traveling_salesman_problem/genetic_algorithm/__init__.py` exports:

```python
from traveling_salesman_problem.genetic_algorithm.predefined_problems import (
    SCENARIO_PRESETS,
    ScenarioPreset,
    get_scenario_city_count,
    get_scenario_coordinates,
    predefined_city_problems,
)

__all__ = [
    # ... existing ...
    "SCENARIO_PRESETS",
    "ScenarioPreset",
    "get_scenario_city_count",
    "get_scenario_coordinates",
    "predefined_city_problems",
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_scenario_presets.ScenarioPresetTests -v`  
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add traveling_salesman_problem/genetic_algorithm/predefined_problems.py traveling_salesman_problem/genetic_algorithm/__init__.py tests/test_scenario_presets.py
git commit -m "feat: add scenario preset data model"
```

---

### Task 2: Conditional 2-opt in selection

**Files:**
- Modify: `traveling_salesman_problem/genetic_algorithm/selection.py`
- Modify: `tests/test_scenario_presets.py`

**Interfaces:**
- Consumes: `add_2opt` from `fitness.py` (unchanged)
- Produces:
  - `evolve_next_generation(..., use_2opt: bool = True) -> List[Route]`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_scenario_presets.py`:

```python
from unittest.mock import patch

from traveling_salesman_problem.genetic_algorithm.selection import evolve_next_generation


class TwoOptToggleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cities = [(0, 0), (10, 0), (10, 10), (0, 10)]
        self.population = [
            list(self.cities),
            [(0, 0), (10, 10), (10, 0), (0, 10)],
        ]
        self.fitness_values = [100.0, 200.0]

    @patch("traveling_salesman_problem.genetic_algorithm.selection.add_2opt")
    def test_use_2opt_true_calls_add_2opt(self, mock_add_2opt):
        mock_add_2opt.side_effect = lambda route: route
        evolve_next_generation(
            self.population,
            self.fitness_values,
            population_size=2,
            mutation_probability=0.0,
            use_2opt=True,
        )
        self.assertGreater(mock_add_2opt.call_count, 0)

    @patch("traveling_salesman_problem.genetic_algorithm.selection.add_2opt")
    def test_use_2opt_false_skips_add_2opt(self, mock_add_2opt):
        evolve_next_generation(
            self.population,
            self.fitness_values,
            population_size=2,
            mutation_probability=0.0,
            use_2opt=False,
        )
        mock_add_2opt.assert_not_called()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_scenario_presets.TwoOptToggleTests -v`  
Expected: FAIL — `TypeError: evolve_next_generation() got an unexpected keyword argument 'use_2opt'`

- [ ] **Step 3: Write minimal implementation**

In `traveling_salesman_problem/genetic_algorithm/selection.py`, add parameter and guard:

```python
def evolve_next_generation(
    population: List[Route],
    fitness_values: List[float],
    population_size: int,
    mutation_probability: float,
    mutation_type: str = "adjacent",
    n_elite: int = 2,
    use_2opt: bool = True,
) -> List[Route]:
    # ... existing body ...
        child_route = apply_mutation(
            child_route,
            mutation_probability,
            mutation_type=mutation_type,
        )

        if use_2opt:
            child_route = add_2opt(child_route)

        new_population.append(child_route)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_scenario_presets -v`  
Expected: PASS (all tests)

- [ ] **Step 5: Commit**

```bash
git add traveling_salesman_problem/genetic_algorithm/selection.py tests/test_scenario_presets.py
git commit -m "feat: make 2-opt optional in evolve_next_generation"
```

---

### Task 3: ScenarioSelector widget

**Files:**
- Create: `traveling_salesman_problem/visualization/widgets/scenario_selector.py`
- Modify: `traveling_salesman_problem/visualization/widgets/__init__.py`

**Interfaces:**
- Consumes: `SCENARIO_PRESETS` from `predefined_problems.py`
- Produces:
  - `ScenarioSelector(position_x, position_y, width, active_scenario_id="random")`
  - Properties: `active_scenario_id: str`, `was_changed: bool`, `height: int`
  - Methods: `handle_event(event) -> None`, `draw(screen) -> None`, `set_active(scenario_id) -> None`

- [ ] **Step 1: Create widget**

Create `traveling_salesman_problem/visualization/widgets/scenario_selector.py`:

```python
"""Seletor de cenário com botões estilo rádio."""

import pygame

from traveling_salesman_problem.config.visual_theme import VisualTheme
from traveling_salesman_problem.genetic_algorithm.predefined_problems import SCENARIO_PRESETS
from traveling_salesman_problem.visualization.application_layout import draw_card
from traveling_salesman_problem.visualization.fonts import get_user_interface_font


class ScenarioSelector:
    OPTION_HEIGHT = 28
    OPTION_GAP = 4

    def __init__(
        self,
        position_x: int,
        position_y: int,
        width: int,
        active_scenario_id: str = "random",
    ) -> None:
        self.position_x = position_x
        self.position_y = position_y
        self.width = width
        self.active_scenario_id = active_scenario_id
        self.was_changed = False
        self._scenario_ids = list(SCENARIO_PRESETS.keys())

    @property
    def height(self) -> int:
        count = len(self._scenario_ids)
        return count * self.OPTION_HEIGHT + (count - 1) * self.OPTION_GAP

    def set_active(self, scenario_id: str) -> None:
        self.active_scenario_id = scenario_id

    def _option_rectangle(self, index: int) -> pygame.Rect:
        return pygame.Rect(
            self.position_x,
            self.position_y + index * (self.OPTION_HEIGHT + self.OPTION_GAP),
            self.width,
            self.OPTION_HEIGHT,
        )

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        for index, scenario_id in enumerate(self._scenario_ids):
            if self._option_rectangle(index).collidepoint(event.pos):
                if scenario_id != self.active_scenario_id:
                    self.active_scenario_id = scenario_id
                    self.was_changed = True
                return

    def draw(self, screen: pygame.Surface) -> None:
        label_font = get_user_interface_font(12)
        for index, scenario_id in enumerate(self._scenario_ids):
            option_rect = self._option_rectangle(index)
            is_active = scenario_id == self.active_scenario_id
            draw_card(screen, option_rect)
            if is_active:
                pygame.draw.rect(
                    screen,
                    VisualTheme.accent,
                    option_rect,
                    width=2,
                    border_radius=8,
                )
            preset = SCENARIO_PRESETS[scenario_id]
            text_color = VisualTheme.text_primary if is_active else VisualTheme.text_muted
            screen.blit(
                label_font.render(preset.label, True, text_color),
                (option_rect.x + 12, option_rect.centery - 7),
            )
```

Update `traveling_salesman_problem/visualization/widgets/__init__.py`:

```python
from traveling_salesman_problem.visualization.widgets.scenario_selector import ScenarioSelector
from traveling_salesman_problem.visualization.widgets.toggle_button import ToggleButton

__all__ = [
    # ... existing ...
    "ScenarioSelector",
    "ToggleButton",
]
```

- [ ] **Step 2: Smoke import**

Run: `python -c "from traveling_salesman_problem.visualization.widgets import ScenarioSelector, ToggleButton; print('ok')"`  
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add traveling_salesman_problem/visualization/widgets/scenario_selector.py traveling_salesman_problem/visualization/widgets/__init__.py
git commit -m "feat: add ScenarioSelector widget"
```

---

### Task 4: SimulationState — apply_scenario and 2-opt toggle

**Files:**
- Modify: `traveling_salesman_problem/simulation/simulation_state.py`

**Interfaces:**
- Consumes: `ScenarioSelector`, `ToggleButton`, `get_scenario_coordinates`, `get_scenario_city_count`, `generate_random_population`, `generate_random_city_coordinate`, `generate_random_priorities`
- Produces:
  - Fields: `active_scenario_id`, `scenario_selector`, `two_opt_toggle`, `section_scenario_y`, `effective_number_of_cities`
  - Methods: `apply_scenario(scenario_id: str) -> None`, `load_cities_for_scenario(scenario_id: str) -> List[CityCoordinate]`, `reset_simulation_history() -> None`
  - Updated: `_create_control_widgets()`, `handle_control_events()`, `update_terrain_counts_if_changed()`, `run_one_generation()`, `shuffle_terrain_and_cities()`

- [ ] **Step 1: Add imports and state fields**

At top of `simulation_state.py`, add:

```python
import itertools

from traveling_salesman_problem.genetic_algorithm.predefined_problems import (
    get_scenario_city_count,
    get_scenario_coordinates,
)
from traveling_salesman_problem.visualization.widgets import (
    ActionButton,
    IntegerSlider,
    MutationSlider,
    ScenarioSelector,
    TerrainControlPanel,
    ToggleButton,
)
```

Add fields to `SimulationState` dataclass:

```python
active_scenario_id: str = "random"
two_opt_toggle: Optional[ToggleButton] = None
scenario_selector: Optional[ScenarioSelector] = None
section_scenario_y: int = 0
effective_number_of_cities: int = 0
```

- [ ] **Step 2: Add helper methods**

Add to `SimulationState`:

```python
def reset_simulation_history(self) -> None:
    self.best_fitness_history.clear()
    self.best_route_history.clear()
    self.generation_counter = itertools.count(start=1)

@property
def effective_city_count(self) -> int:
    return get_scenario_city_count(
        self.active_scenario_id,
        default=self.settings.number_of_cities,
    )

def load_cities_for_scenario(self, scenario_id: str) -> List[CityCoordinate]:
    fixed_coordinates = get_scenario_coordinates(scenario_id)
    if fixed_coordinates is not None:
        return list(fixed_coordinates)
    settings = self.settings
    city_count = settings.number_of_cities
    return [
        generate_random_city_coordinate(
            settings.window_width,
            settings.window_height,
            settings.plot_horizontal_offset,
            settings.city_node_radius,
            self.terrain_features,
        )
        for _ in range(city_count)
    ]

def apply_scenario(self, scenario_id: str) -> None:
    settings = self.settings
    self.active_scenario_id = scenario_id
    self.scenario_selector.set_active(scenario_id)
    self.city_coordinates[:] = self.load_cities_for_scenario(scenario_id)
    self.effective_number_of_cities = len(self.city_coordinates)
    self.city_priorities[:] = generate_random_priorities(self.effective_number_of_cities)
    self.population[:] = generate_random_population(
        self.city_coordinates,
        settings.population_size,
    )
    self.reset_simulation_history()
```

- [ ] **Step 3: Update `_create_control_widgets` layout**

Insert 2-opt toggle after priority slider and scenario section before quantity section. Recalculate Y positions:

```python
def _create_control_widgets(self) -> None:
    settings = self.settings
    controls_width = settings.plot_horizontal_offset - 2 * VisualTheme.control_margin
    half_width = (controls_width - VisualTheme.control_gap) // 2

    self.section_algorithm_y = 0
    mutation_y = self.section_algorithm_y + 26
    priority_weight_y = mutation_y + settings.mutation_slider_height + 12
    two_opt_y = priority_weight_y + settings.mutation_slider_height + 12
    self.section_scenario_y = two_opt_y + 36 + 12
    scenario_selector_y = self.section_scenario_y + 26
    self.section_quantity_y = scenario_selector_y + self._scenario_selector_height() + 12
    # ... rest unchanged from terrain_count_y onward ...

    self.two_opt_toggle = ToggleButton(
        position_x=VisualTheme.control_margin,
        position_y=two_opt_y,
        width=controls_width,
        height=32,
        label="Refinamento 2-opt",
        is_active=True,
    )

    self.scenario_selector = ScenarioSelector(
        position_x=VisualTheme.control_margin,
        position_y=scenario_selector_y,
        width=controls_width,
        active_scenario_id=self.active_scenario_id,
    )
```

Add helper:

```python
def _scenario_selector_height(self) -> int:
    if self.scenario_selector is not None:
        return self.scenario_selector.height
    return ScenarioSelector(
        VisualTheme.control_margin, 0, 100, self.active_scenario_id
    ).height
```

Call `_scenario_selector_height()` only after creating a temporary selector OR hardcode: 5 options × 28 + 4 gaps × 4 = 156.

- [ ] **Step 4: Wire events and shuffle behavior**

In `handle_control_events`:

```python
self.two_opt_toggle.handle_event(event)
self.scenario_selector.handle_event(event)
```

In `update_terrain_counts_if_changed`, **before** hospital/regenerate checks:

```python
if self.scenario_selector.was_changed:
    self.scenario_selector.was_changed = False
    self.apply_scenario(self.scenario_selector.active_scenario_id)
    return
```

Update `shuffle_terrain_and_cities`:

```python
def shuffle_terrain_and_cities(self) -> None:
    if self.active_scenario_id != "random":
        self.apply_scenario("random")
    settings = self.settings
    reshuffle_terrain_feature_positions(...)
    self.terrain_control_panel.rebuild(self.terrain_features)
    reshuffle_cities_and_population(
        self.city_coordinates,
        self.city_priorities,
        self.effective_number_of_cities,  # was settings.number_of_cities
        settings.population_size,
        ...
    )
```

In `initialize()`, after creating cities:

```python
self.active_scenario_id = "random"
self.effective_number_of_cities = len(self.city_coordinates)
```

In `run_one_generation`, replace `settings.number_of_cities` usages where city count matters with `self.effective_number_of_cities`, and pass 2-opt flag:

```python
self.population = evolve_next_generation(
    self.population,
    population_fitness,
    settings.population_size,
    mutation_probability,
    mutation_type="adjacent",
    n_elite=3,
    use_2opt=self.two_opt_toggle.is_active,
)
```

- [ ] **Step 5: Manual smoke test**

Run: `python main.py`  
Expected: app starts; sidebar shows "Refinamento 2-opt" toggle and "CENÁRIO" section with 5 options; selecting "Pequeno (5)" shows 5 cities and resets generation to 1.

- [ ] **Step 6: Commit**

```bash
git add traveling_salesman_problem/simulation/simulation_state.py
git commit -m "feat: wire scenario presets and 2-opt toggle in simulation state"
```

---

### Task 5: Pygame UI drawing and resize preservation

**Files:**
- Modify: `traveling_salesman_problem/simulation/pygame_application.py`

**Interfaces:**
- Consumes: `simulation.two_opt_toggle`, `simulation.scenario_selector`, `simulation.section_scenario_y`
- Produces: updated sidebar rendering and resize handler preserving scenario + 2-opt state

- [ ] **Step 1: Draw new controls in `_draw_scrollable_sidebar`**

After priority slider block, add:

```python
simulation.two_opt_toggle.draw(content_surface)

draw_section_header(
    content_surface,
    VisualTheme.control_margin,
    simulation.section_scenario_y,
    controls_width,
    "Cenário",
)
simulation.scenario_selector.draw(content_surface)
```

Shift existing "Terreno no mapa" header to use `simulation.section_quantity_y` (already updated in Task 4).

- [ ] **Step 2: Preserve state on VIDEORESIZE**

In `pygame_application.py`, before recreating simulation on resize, capture:

```python
saved_scenario_id = simulation.active_scenario_id
saved_two_opt_active = simulation.two_opt_toggle.is_active
saved_mutation = simulation.mutation_slider.value
saved_priority_weight = simulation.priority_weight_slider.value
```

After `simulation.initialize()`, restore:

```python
simulation.two_opt_toggle.is_active = saved_two_opt_active
simulation.mutation_slider.value = saved_mutation
simulation.priority_weight_slider.value = saved_priority_weight
if saved_scenario_id != "random":
    simulation.apply_scenario(saved_scenario_id)
else:
    simulation.active_scenario_id = "random"
    simulation.scenario_selector.set_active("random")
```

- [ ] **Step 3: Manual verification checklist**

Run: `python main.py`

Verify:
1. Each preset loads correct city count; graph resets; generation starts at 1
2. Toggle 2-opt mid-run: graph continues, behavior changes next generation
3. "Sortear posições" on fixed preset → switches to Aleatório
4. Resize window → scenario and 2-opt state preserved

- [ ] **Step 4: Run unit tests**

Run: `python -m unittest discover tests -v`  
Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add traveling_salesman_problem/simulation/pygame_application.py
git commit -m "feat: draw scenario selector and preserve state on resize"
```

---

## Manual Test Checklist (post-implementation)

- [ ] Default launch: Aleatório selected, 2-opt active, 15 random cities
- [ ] Pequeno (5): exactly 5 cities at fixed positions, history cleared
- [ ] Toggle 2-opt off mid-run: generation counter does not reset
- [ ] Same preset, 2-opt on vs off: visibly different convergence speed
- [ ] Sortear posições on Extra (15): switches to Aleatório
- [ ] Window resize: scenario and 2-opt state preserved

---

## Spec Coverage (self-review)

| Spec requirement | Task |
|------------------|------|
| SCENARIO_PRESETS with 5 options | Task 1 |
| Backward-compat `predefined_city_problems` | Task 1 |
| `use_2opt` parameter | Task 2 |
| ScenarioSelector widget | Task 3 |
| ToggleButton in Algorithm section | Task 4 |
| `apply_scenario` full reset | Task 4 |
| 2-opt toggle no reset | Task 4 |
| Sortear posições → Aleatório on fixed preset | Task 4 |
| Sidebar drawing | Task 5 |
| Resize preservation | Task 5 |
| Hospital scenario out of scope | N/A (not implemented) |
| Map header stats (optional) | Deferred — not in tasks |
