"""Desenho de cidades, rotas, árvores e lagos no mapa."""

import math
from typing import List, Tuple

import pygame

from traveling_salesman_problem.config.visual_theme import VisualTheme, priority_to_color
from traveling_salesman_problem.genetic_algorithm.fitness import get_rotated_route
from traveling_salesman_problem.obstacles.models import LakeObstacle, Obstacle, TreeObstacle
from traveling_salesman_problem.visualization.fonts import get_monospace_font, get_user_interface_font
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


def draw_route_visit_positions(
    screen: pygame.Surface,
    route: Route,
    city_coordinates: List[CityCoordinate],
    node_radius: int,
) -> None:
    """Desenha a posição de visita abaixo de cada nó da melhor rota."""
    rotated_route = get_rotated_route(route, city_coordinates)
    if not rotated_route:
        return

    label_offset_y = node_radius + 6
    regular_font = get_monospace_font(10)
    bold_font = get_monospace_font(10, bold=True)

    for position, city in enumerate(rotated_route, start=1):
        label_font = bold_font if position == 1 else regular_font
        label_surface = label_font.render(str(position), True, VisualTheme.text_primary)
        label_rectangle = label_surface.get_rect(
            center=(city[0], city[1] + label_offset_y),
        )
        screen.blit(label_surface, label_rectangle)


def _coordinate_for_stop(
    stop_point_id: str,
    depot: Tuple[float, float],
    delivery_points,
) -> Tuple[int, int]:
    if stop_point_id == "DEPOT":
        return (int(depot[0]), int(depot[1]))
    point = next(item for item in delivery_points if item.id == stop_point_id)
    return (int(point.coordinate[0]), int(point.coordinate[1]))


def draw_depot(screen: pygame.Surface, depot: Tuple[float, float], half_size: int) -> None:
    x, y = int(depot[0]), int(depot[1])
    rectangle = pygame.Rect(x - half_size, y - half_size, half_size * 2, half_size * 2)
    pygame.draw.rect(screen, VisualTheme.depot_stroke, rectangle.inflate(4, 4))
    pygame.draw.rect(screen, VisualTheme.depot_fill, rectangle)
    label = get_user_interface_font(11, bold=True).render("D", True, VisualTheme.text_inverse)
    screen.blit(label, label.get_rect(center=rectangle.center))


def draw_delivery_points(
    screen: pygame.Surface,
    delivery_points,
    node_radius: int,
) -> None:
    label_font = get_user_interface_font(11, bold=True)
    count_font = get_monospace_font(10)

    for point in delivery_points:
        center = (int(point.coordinate[0]), int(point.coordinate[1]))
        pygame.draw.circle(screen, VisualTheme.city_stroke, center, node_radius + 2)
        pygame.draw.circle(screen, VisualTheme.city_fill, center, node_radius)

        label_surface = label_font.render(point.id, True, VisualTheme.text_primary)
        label_rect = label_surface.get_rect(center=(center[0], center[1] + node_radius + 10))
        screen.blit(label_surface, label_rect)

        count_surface = count_font.render(f"{point.total_items} itens", True, VisualTheme.text_muted)
        count_rect = count_surface.get_rect(center=(center[0], center[1] - node_radius - 10))
        screen.blit(count_surface, count_rect)


def _draw_open_route(
    screen: pygame.Surface,
    coordinates: List[Tuple[int, int]],
    line_color: Tuple[int, int, int],
    line_width: int = 2,
) -> None:
    if len(coordinates) < 2:
        return
    pygame.draw.lines(screen, line_color, False, coordinates, width=line_width)


def draw_vehicle_routes(
    screen: pygame.Surface,
    simulation_result,
    base_colors: Tuple[Tuple[int, int, int], ...],
) -> None:
    for vehicle_index, vehicle in enumerate(simulation_result.vehicles):
        color = base_colors[vehicle_index % len(base_colors)]
        for trip_index, trip in enumerate(vehicle.trips):
            coordinates = [
                _coordinate_for_stop(stop.point_id, simulation_result.depot, simulation_result.delivery_points)
                for stop in trip.stops
            ]
            route_color = color if trip_index % 2 == 0 else tuple(max(0, channel - 40) for channel in color)
            _draw_open_route(screen, coordinates, route_color, line_width=3)
            draw_route_direction_arrows_for_coordinates(screen, coordinates, route_color)


def draw_route_direction_arrows_for_coordinates(
    screen: pygame.Surface,
    coordinates: List[Tuple[int, int]],
    outline_color: Tuple[int, int, int],
    fill_color: Tuple[int, int, int] = (255, 255, 255),
    arrow_size: int = 8,
    min_segment_length: float = 20.0,
    segment_position_ratio: float = 0.65,
) -> None:
    if len(coordinates) < 2:
        return

    for index in range(len(coordinates) - 1):
        origin = coordinates[index]
        destination = coordinates[index + 1]
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


def draw_vehicle_legend(
    screen: pygame.Surface,
    vehicle_count: int,
    base_colors: Tuple[Tuple[int, int, int], ...],
    position_x: int,
    position_y: int,
) -> None:
    legend_items = [
        (base_colors[index], f"Veículo {index + 1}") for index in range(vehicle_count)
    ]
    padding = 10
    row_height = 18
    label_font = get_user_interface_font(11)
    panel_width = 140
    panel_height = padding * 2 + row_height * len(legend_items)
    panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    panel_surface.fill((255, 255, 255, 235))
    pygame.draw.rect(
        panel_surface,
        VisualTheme.border,
        panel_surface.get_rect(),
        width=1,
        border_radius=6,
    )

    for index, (color, label) in enumerate(legend_items):
        item_y = padding + index * row_height
        pygame.draw.line(
            panel_surface,
            color,
            (padding, item_y + 8),
            (padding + 16, item_y + 8),
            width=3,
        )
        panel_surface.blit(
            label_font.render(label, True, VisualTheme.text_muted),
            (padding + 22, item_y),
        )

    screen.blit(panel_surface, (position_x, position_y))
