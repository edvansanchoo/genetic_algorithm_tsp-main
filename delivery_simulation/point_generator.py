"""Geração aleatória de coordenadas da distribuidora e pontos de entrega."""

import random
from typing import List, Optional, Tuple

from delivery_simulation.models import Coordinate, POINT_IDS


def _random_coordinate(
    map_min_x: float,
    map_min_y: float,
    map_max_x: float,
    map_max_y: float,
    rng: random.Random,
) -> Coordinate:
    x = rng.uniform(map_min_x, map_max_x)
    y = rng.uniform(map_min_y, map_max_y)
    return (x, y)


def _is_far_enough(candidate: Coordinate, existing: List[Coordinate], min_separation: float) -> bool:
    for existing_coordinate in existing:
        delta_x = candidate[0] - existing_coordinate[0]
        delta_y = candidate[1] - existing_coordinate[1]
        if (delta_x * delta_x + delta_y * delta_y) ** 0.5 < min_separation:
            return False
    return True


def generate_depot_and_points(
    point_count: int,
    map_min_x: float,
    map_min_y: float,
    map_max_x: float,
    map_max_y: float,
    min_separation: float = 30.0,
    max_attempts: int = 100,
    rng: Optional[random.Random] = None,
) -> Tuple[Coordinate, List[Tuple[str, Coordinate]]]:
    if point_count < 1 or point_count > len(POINT_IDS):
        raise ValueError(f"point_count deve estar entre 1 e {len(POINT_IDS)}")

    random_source = rng or random.Random()
    labels = POINT_IDS[:point_count]

    for _ in range(max_attempts):
        depot = _random_coordinate(map_min_x, map_min_y, map_max_x, map_max_y, random_source)
        placed: List[Coordinate] = [depot]
        point_coordinates: List[Tuple[str, Coordinate]] = []
        success = True

        for label in labels:
            point_found = False
            for _attempt in range(max_attempts):
                candidate = _random_coordinate(
                    map_min_x, map_min_y, map_max_x, map_max_y, random_source
                )
                if _is_far_enough(candidate, placed, min_separation):
                    placed.append(candidate)
                    point_coordinates.append((label, candidate))
                    point_found = True
                    break
            if not point_found:
                success = False
                break

        if success:
            return depot, point_coordinates

    raise RuntimeError("Não foi possível posicionar distribuidora e pontos sem sobreposição")
