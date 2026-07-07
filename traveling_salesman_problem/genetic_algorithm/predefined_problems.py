"""Instâncias fixas do problema para testes reproduzíveis."""

import random
from dataclasses import dataclass
from typing import Dict, List, Tuple

from traveling_salesman_problem.config.application_settings import ApplicationSettings

CityCoordinate = Tuple[int, int]

MAP_LAYOUT_SETTINGS = ApplicationSettings()


@dataclass(frozen=True)
class ScenarioPreset:
    label: str
    city_count: int | None
    coordinates: List[CityCoordinate] | None


def _generate_fixed_layout(city_count: int, seed: int) -> List[CityCoordinate]:
    """Gera layout determinístico dentro da área do mapa."""
    random_generator = random.Random(seed)
    minimum_x = MAP_LAYOUT_SETTINGS.map_minimum_x
    minimum_y = MAP_LAYOUT_SETTINGS.map_minimum_y
    maximum_x = MAP_LAYOUT_SETTINGS.map_maximum_x
    maximum_y = MAP_LAYOUT_SETTINGS.map_maximum_y
    minimum_distance = 22

    coordinates: List[CityCoordinate] = []
    remaining_attempts = city_count * 200
    while len(coordinates) < city_count and remaining_attempts > 0:
        remaining_attempts -= 1
        candidate_x = random_generator.randint(minimum_x, maximum_x)
        candidate_y = random_generator.randint(minimum_y, maximum_y)
        if all(
            (candidate_x - existing_x) ** 2 + (candidate_y - existing_y) ** 2
            >= minimum_distance ** 2
            for existing_x, existing_y in coordinates
        ):
            coordinates.append((candidate_x, candidate_y))

    if len(coordinates) < city_count:
        columns = max(1, int(city_count ** 0.5))
        horizontal_span = maximum_x - minimum_x
        vertical_span = maximum_y - minimum_y
        for city_index in range(city_count):
            row = city_index // columns
            column = city_index % columns
            grid_x = minimum_x + (column + 1) * horizontal_span // (columns + 1)
            grid_y = minimum_y + (row + 1) * vertical_span // (city_count // columns + 2)
            coordinates.append((grid_x, grid_y))

    return coordinates


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

for city_count in (20, 25, 30, 40, 50):
    _FIXED_COORDINATES[city_count] = _generate_fixed_layout(city_count, city_count * 1000 + 42)

SCENARIO_PRESETS: Dict[str, ScenarioPreset] = {
    "random": ScenarioPreset(label="Aleatório", city_count=None, coordinates=None),
    "small_5": ScenarioPreset(label="Pequeno (5)", city_count=5, coordinates=_FIXED_COORDINATES[5]),
    "medium_10": ScenarioPreset(label="Médio (10)", city_count=10, coordinates=_FIXED_COORDINATES[10]),
    "large_12": ScenarioPreset(label="Grande (12)", city_count=12, coordinates=_FIXED_COORDINATES[12]),
    "extra_15": ScenarioPreset(label="Extra (15)", city_count=15, coordinates=_FIXED_COORDINATES[15]),
    "intense_20": ScenarioPreset(label="Intenso (20)", city_count=20, coordinates=_FIXED_COORDINATES[20]),
    "advanced_25": ScenarioPreset(label="Avançado (25)", city_count=25, coordinates=_FIXED_COORDINATES[25]),
    "complex_30": ScenarioPreset(label="Complexo (30)", city_count=30, coordinates=_FIXED_COORDINATES[30]),
    "massive_40": ScenarioPreset(label="Massivo (40)", city_count=40, coordinates=_FIXED_COORDINATES[40]),
    "maximum_50": ScenarioPreset(label="Máximo (50)", city_count=50, coordinates=_FIXED_COORDINATES[50]),
}

predefined_city_problems: Dict[int, List[CityCoordinate]] = _FIXED_COORDINATES


def get_scenario_coordinates(scenario_id: str) -> List[CityCoordinate] | None:
    preset = SCENARIO_PRESETS[scenario_id]
    if preset.coordinates is None:
        return None
    return list(preset.coordinates)


def get_scenario_city_count(scenario_id: str, default: int) -> int:
    preset = SCENARIO_PRESETS[scenario_id]
    return preset.city_count if preset.city_count is not None else default
