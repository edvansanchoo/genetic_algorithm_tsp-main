"""Penalidades aplicadas quando uma rota cruza árvores ou lagos."""

from typing import List, Tuple

from traveling_salesman_problem.obstacles.collision import segment_intersects_terrain_feature
from traveling_salesman_problem.obstacles.models import Obstacle


def calculate_segment_terrain_penalty(
    first_point: Tuple[float, float],
    second_point: Tuple[float, float],
    terrain_features: List[Obstacle],
    use_terrain_penalties: bool = True,
) -> float:
    if not use_terrain_penalties:
        return 0.0

    total_penalty = 0.0
    for feature in terrain_features:
        if not feature.enabled:
            continue
        if segment_intersects_terrain_feature(first_point, second_point, feature):
            total_penalty += feature.penalty

    return total_penalty


calculate_segment_obstacle_penalty = calculate_segment_terrain_penalty
