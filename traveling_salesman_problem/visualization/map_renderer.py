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
    road_network,
) -> Tuple[int, int]:
    coordinate = road_network.nodes[stop_point_id]
    return (int(coordinate[0]), int(coordinate[1]))


def draw_road_network(screen: pygame.Surface, road_network) -> None:
    drawn = set()
    for node_a, node_b in road_network.edges:
        key = tuple(sorted((node_a, node_b)))
        if key in drawn:
            continue
        drawn.add(key)
        start = _coordinate_for_stop(node_a, road_network)
        end = _coordinate_for_stop(node_b, road_network)
        pygame.draw.line(screen, VisualTheme.graph_edge_color, start, end, 1)


def draw_transit_nodes(screen: pygame.Surface, transit_nodes) -> None:
    label_font = get_user_interface_font(9, bold=True)
    for node in transit_nodes:
        center = (int(node.coordinate[0]), int(node.coordinate[1]))
        pygame.draw.circle(screen, VisualTheme.transit_fill, center, 6)
        label = label_font.render(node.id, True, VisualTheme.text_primary)
        screen.blit(label, label.get_rect(center=(center[0], center[1] - 12)))


def _draw_styled_route(
    screen: pygame.Surface,
    coordinates: List[Tuple[int, int]],
    line_color: Tuple[int, int, int],
    style: str,
    line_width: int = 4,
    alpha: int = 255,
) -> None:
    if len(coordinates) < 2:
        return
    color = line_color
    if alpha < 255:
        color = tuple(int(channel * alpha / 255) for channel in line_color)

    if style == "solid":
        pygame.draw.lines(screen, color, False, coordinates, width=line_width)
        return

    dash = 10 if style == "dashed" else 4
    gap = 6 if style == "dashed" else 4
    for index in range(len(coordinates) - 1):
        start = coordinates[index]
        end = coordinates[index + 1]
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.hypot(dx, dy)
        if length == 0:
            continue
        steps = int(length / (dash + gap)) + 1
        for step in range(steps):
            t0 = step * (dash + gap) / length
            t1 = min((step * (dash + gap) + dash) / length, 1.0)
            if t0 >= 1.0:
                break
            p0 = (int(start[0] + dx * t0), int(start[1] + dy * t0))
            p1 = (int(start[0] + dx * t1), int(start[1] + dy * t1))
            pygame.draw.line(screen, color, p0, p1, line_width)


def _trips_to_coordinates(trips, road_network) -> List[List[Tuple[int, int]]]:
    return [
        [_coordinate_for_stop(stop.point_id, road_network) for stop in trip.stops]
        for trip in trips
    ]


def draw_vehicle_evolution_routes(
    screen: pygame.Surface,
    road_network,
    best_trips,
    second_best_trips,
    color: Tuple[int, int, int],
) -> None:
    if second_best_trips:
        for coordinates in _trips_to_coordinates(second_best_trips, road_network):
            muted = tuple(int(channel * 0.5) for channel in color)
            _draw_styled_route(screen, coordinates, muted, "dashed", line_width=2, alpha=128)
            draw_route_direction_arrows_for_coordinates(screen, coordinates, muted)

    for coordinates in _trips_to_coordinates(best_trips, road_network):
        _draw_styled_route(screen, coordinates, color, "solid", line_width=4)
        draw_route_direction_arrows_for_coordinates(screen, coordinates, color)


def draw_selected_routes(
    screen: pygame.Surface,
    simulation_result,
    active_vehicle_id: int,
    active_trip_index: int,
    view_mode: str,
    base_colors: Tuple[Tuple[int, int, int], ...],
    line_styles: Tuple[str, ...],
) -> None:
    vehicle = simulation_result.vehicles[active_vehicle_id - 1]
    color = base_colors[(active_vehicle_id - 1) % len(base_colors)]
    style = line_styles[(active_vehicle_id - 1) % len(line_styles)]

    if view_mode == "all":
        trip_count = len(vehicle.trips)
        for trip_index, trip in enumerate(vehicle.trips):
            alpha = 255 - trip_index * (180 // max(trip_count, 1))
            coordinates = [
                _coordinate_for_stop(stop.point_id, simulation_result.road_network)
                for stop in trip.stops
            ]
            _draw_styled_route(screen, coordinates, color, style, alpha=max(alpha, 80))
            draw_route_direction_arrows_for_coordinates(screen, coordinates, color)
        return

    if not vehicle.trips or active_trip_index >= len(vehicle.trips):
        return
    trip = vehicle.trips[active_trip_index]
    coordinates = [
        _coordinate_for_stop(stop.point_id, simulation_result.road_network)
        for stop in trip.stops
    ]
    _draw_styled_route(screen, coordinates, color, style)
    draw_route_direction_arrows_for_coordinates(screen, coordinates, color)


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
    line_styles: Tuple[str, ...],
    position_x: int,
    position_y: int,
) -> None:
    legend_items = [
        (base_colors[index], line_styles[index % len(line_styles)], f"Veículo {index + 1}")
        for index in range(vehicle_count)
    ]
    padding = 10
    row_height = 18
    label_font = get_user_interface_font(11)
    panel_width = 160
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

    for index, (color, style, label) in enumerate(legend_items):
        item_y = padding + index * row_height
        line_start = (padding, item_y + 8)
        line_end = (padding + 16, item_y + 8)
        if style == "solid":
            pygame.draw.line(panel_surface, color, line_start, line_end, width=3)
        else:
            dash = 4 if style == "dotted" else 6
            gap = 3 if style == "dotted" else 4
            x = line_start[0]
            while x < line_end[0]:
                segment_end = min(x + dash, line_end[0])
                pygame.draw.line(panel_surface, color, (x, line_start[1]), (segment_end, line_start[1]), width=3)
                x += dash + gap
        panel_surface.blit(
            label_font.render(label, True, VisualTheme.text_muted),
            (padding + 22, item_y),
        )

    screen.blit(panel_surface, (position_x, position_y))
