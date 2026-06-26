"""Desenho de cidades, rotas, árvores e lagos no mapa."""

import math
from typing import List, Tuple

import pygame

from traveling_salesman_problem.config.visual_theme import VisualTheme, priority_to_color
from traveling_salesman_problem.genetic_algorithm.fitness import get_rotated_route
from traveling_salesman_problem.obstacles.models import LakeObstacle, Obstacle, TreeObstacle
from traveling_salesman_problem.visualization.terrain_drawings import draw_lake, draw_tree

CityCoordinate = Tuple[int, int]
Route = List[CityCoordinate]


def draw_terrain_features(screen: pygame.Surface, obstacles: List[Obstacle]) -> None:
    """Desenha árvores e lagos na ordem correta (lagos primeiro, árvores por cima)."""
    for obstacle in obstacles:
        if isinstance(obstacle, LakeObstacle):
            draw_lake(screen, obstacle)

    for obstacle in obstacles:
        if isinstance(obstacle, TreeObstacle):
            draw_tree(screen, obstacle)


def draw_cities(
    screen: pygame.Surface,
    city_coordinates: List[CityCoordinate],
    priorities: List[int],
    node_radius: int,
) -> None:
    for city, priority in zip(city_coordinates, priorities):
        fill_color = priority_to_color(priority)
        pygame.draw.circle(screen, VisualTheme.city_stroke, city, node_radius + 2)
        pygame.draw.circle(screen, fill_color, city, node_radius)


def draw_route_paths(
    screen: pygame.Surface,
    route: Route,
    line_color: Tuple[int, int, int],
    line_width: int = 1,
    draw_glow: bool = False,
) -> None:
    if draw_glow and len(route) > 1:
        pygame.draw.lines(
            screen,
            VisualTheme.route_best_glow,
            True,
            route,
            width=line_width + 4,
        )
    pygame.draw.lines(screen, line_color, True, route, width=line_width)


def draw_route_direction_arrows(
    screen: pygame.Surface,
    route: Route,
    city_coordinates: List[CityCoordinate],
    fill_color: Tuple[int, int, int] = (255, 255, 255),
    outline_color: Tuple[int, int, int] = VisualTheme.route_best,
    arrow_size: int = 8,
    min_segment_length: float = 20.0,
    segment_position_ratio: float = 0.65,
) -> None:
    """Desenha setas indicando a direção da rota rotacionada a partir do índice 0."""
    rotated_route = get_rotated_route(route, city_coordinates)
    if len(rotated_route) < 2:
        return

    number_of_cities = len(rotated_route)
    for index in range(number_of_cities):
        origin = rotated_route[index]
        destination = rotated_route[(index + 1) % number_of_cities]
        delta_x = destination[0] - origin[0]
        delta_y = destination[1] - origin[1]
        segment_length = math.hypot(delta_x, delta_y)
        if segment_length < min_segment_length:
            continue

        angle = math.atan2(delta_y, delta_x)
        arrow_center_x = origin[0] + delta_x * segment_position_ratio
        arrow_center_y = origin[1] + delta_y * segment_position_ratio

        tip = (
            arrow_center_x + math.cos(angle) * arrow_size * 0.5,
            arrow_center_y + math.sin(angle) * arrow_size * 0.5,
        )
        base_center_x = arrow_center_x - math.cos(angle) * arrow_size * 0.5
        base_center_y = arrow_center_y - math.sin(angle) * arrow_size * 0.5
        perpendicular_angle = angle + math.pi / 2
        half_base = arrow_size * 0.4
        base_left = (
            base_center_x + math.cos(perpendicular_angle) * half_base,
            base_center_y + math.sin(perpendicular_angle) * half_base,
        )
        base_right = (
            base_center_x - math.cos(perpendicular_angle) * half_base,
            base_center_y - math.sin(perpendicular_angle) * half_base,
        )

        triangle_points = [tip, base_left, base_right]
        pygame.draw.polygon(screen, fill_color, triangle_points)
        pygame.draw.polygon(screen, outline_color, triangle_points, 1)
