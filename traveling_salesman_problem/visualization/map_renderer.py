"""Desenho de cidades, rotas, árvores e lagos no mapa."""

from typing import List, Tuple

import pygame

from traveling_salesman_problem.config.visual_theme import VisualTheme, priority_to_color
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
