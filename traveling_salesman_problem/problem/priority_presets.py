"""Presets de prioridade para cenários de demonstração."""

import random
from typing import List

HOSPITAL_PRESET_SEED = 42


def apply_hospital_priority_preset(number_of_cities: int) -> List[int]:
    """Distribui prioridades hospitalares de forma determinística."""
    random_generator = random.Random(HOSPITAL_PRESET_SEED)
    city_indices = list(range(number_of_cities))
    random_generator.shuffle(city_indices)

    critical_count = max(1, round(number_of_cities * 0.20))
    medium_count = round(number_of_cities * 0.30)

    priorities = [1] * number_of_cities
    for city_index in city_indices[:critical_count]:
        priorities[city_index] = random_generator.randint(8, 10)
    for city_index in city_indices[critical_count : critical_count + medium_count]:
        priorities[city_index] = random_generator.randint(5, 7)
    for city_index in city_indices[critical_count + medium_count :]:
        priorities[city_index] = random_generator.randint(1, 4)

    return priorities
