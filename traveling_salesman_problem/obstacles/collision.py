"""Detecção de colisão entre pontos, segmentos, árvores e lagos."""

import math
from typing import List, Tuple

import pygame

from traveling_salesman_problem.obstacles.models import LakeObstacle, Obstacle, TreeObstacle


def _tree_bounding_rectangle(
    center_x: int,
    center_y: int,
    radius: int,
) -> pygame.Rect:
    return pygame.Rect(center_x - radius, center_y - radius, radius * 2, radius * 2)


def _terrain_feature_bounding_rectangle(feature: Obstacle) -> pygame.Rect:
    if isinstance(feature, TreeObstacle):
        return _tree_bounding_rectangle(
            feature.center_x,
            feature.center_y,
            feature.radius,
        )
    return feature.rectangle.copy()


def terrain_features_overlap(
    first_feature: Obstacle,
    second_feature: Obstacle,
    padding: int = 20,
) -> bool:
    first_bounds = _terrain_feature_bounding_rectangle(first_feature).inflate(padding, padding)
    second_bounds = _terrain_feature_bounding_rectangle(second_feature).inflate(padding, padding)
    return first_bounds.colliderect(second_bounds)


obstacles_overlap = terrain_features_overlap


def point_inside_terrain_feature(
    point: Tuple[float, float],
    feature: Obstacle,
) -> bool:
    coordinate_x, coordinate_y = point

    if isinstance(feature, TreeObstacle):
        distance_to_center = math.hypot(
            coordinate_x - feature.center_x,
            coordinate_y - feature.center_y,
        )
        return distance_to_center <= feature.radius

    lake_rect = feature.rectangle
    normalized_x = (coordinate_x - lake_rect.centerx) / (lake_rect.width / 2)
    normalized_y = (coordinate_y - lake_rect.centery) / (lake_rect.height / 2)
    return (normalized_x * normalized_x + normalized_y * normalized_y) <= 1.0


point_inside_obstacle = point_inside_terrain_feature


def point_inside_any_terrain_feature(
    point: Tuple[float, float],
    terrain_features: List[Obstacle],
    only_enabled: bool = True,
) -> bool:
    for feature in terrain_features:
        if only_enabled and not feature.enabled:
            continue
        if point_inside_terrain_feature(point, feature):
            return True
    return False


point_inside_any_obstacle = point_inside_any_terrain_feature


def segment_intersects_circle(
    first_point: Tuple[float, float],
    second_point: Tuple[float, float],
    center_x: float,
    center_y: float,
    radius: float,
) -> bool:
    start_x, start_y = first_point
    end_x, end_y = second_point
    delta_x = end_x - start_x
    delta_y = end_y - start_y

    if delta_x == 0 and delta_y == 0:
        return math.hypot(start_x - center_x, start_y - center_y) <= radius

    projection_parameter = max(
        0.0,
        min(
            1.0,
            ((center_x - start_x) * delta_x + (center_y - start_y) * delta_y)
            / (delta_x * delta_x + delta_y * delta_y),
        ),
    )
    closest_x = start_x + projection_parameter * delta_x
    closest_y = start_y + projection_parameter * delta_y
    return math.hypot(closest_x - center_x, closest_y - center_y) <= radius


def segment_intersects_terrain_feature(
    first_point: Tuple[float, float],
    second_point: Tuple[float, float],
    feature: Obstacle,
) -> bool:
    if isinstance(feature, TreeObstacle):
        return segment_intersects_circle(
            first_point,
            second_point,
            feature.center_x,
            feature.center_y,
            feature.radius,
        )

    lake_rect = feature.rectangle
    sample_count = 12
    for sample_index in range(sample_count + 1):
        angle = 2 * math.pi * sample_index / sample_count
        edge_x = lake_rect.centerx + math.cos(angle) * lake_rect.width / 2
        edge_y = lake_rect.centery + math.sin(angle) * lake_rect.height / 2
        if segment_intersects_circle(first_point, second_point, edge_x, edge_y, 1.0):
            return True

    if point_inside_terrain_feature(first_point, feature):
        return True
    if point_inside_terrain_feature(second_point, feature):
        return True

    return bool(lake_rect.clipline(first_point, second_point))


segment_intersects_obstacle = segment_intersects_terrain_feature
