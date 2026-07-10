"""Desenho de entregas, malha, bloqueios e rotas no mapa."""

import math
from typing import Dict, List, Optional, Sequence, Tuple

import pygame

from traveling_salesman_problem.config.visual_theme import VisualTheme, priority_to_color
from traveling_salesman_problem.genetic_algorithm.fitness import get_rotated_route
from traveling_salesman_problem.problem.delivery_mesh import (
    DeliveryMesh,
    delivery_segment_path,
    expand_route_polyline,
)
from traveling_salesman_problem.problem.vrp_decoder import DecodedVehiclePlan
from traveling_salesman_problem.problem.vrp_models import DeliveryPoint, Trip
from traveling_salesman_problem.visualization.fonts import get_monospace_font

CityCoordinate = Tuple[float, float]
Route = List[CityCoordinate]


def draw_mesh_edges(screen: pygame.Surface, mesh: Optional[DeliveryMesh]) -> None:
    if mesh is None:
        return
    for node_a, node_b in mesh.network.edges:
        start = mesh.network.nodes[node_a]
        end = mesh.network.nodes[node_b]
        pygame.draw.line(screen, VisualTheme.mesh_edge, start, end, 1)


def draw_transit_nodes(
    screen: pygame.Surface,
    mesh: Optional[DeliveryMesh],
    radius: int = 5,
) -> None:
    if mesh is None:
        return
    for node_id in mesh.transit_ids:
        center = mesh.network.nodes[node_id]
        point = (int(center[0]), int(center[1]))
        pygame.draw.circle(screen, VisualTheme.transit_stroke, point, radius + 1)
        pygame.draw.circle(screen, VisualTheme.transit_fill, point, radius)


def draw_blocked_nodes(
    screen: pygame.Surface,
    mesh: Optional[DeliveryMesh],
    radius: int = 7,
) -> None:
    if mesh is None:
        return
    for coordinate in mesh.blocked_coordinates.values():
        center = (int(coordinate[0]), int(coordinate[1]))
        pygame.draw.circle(screen, VisualTheme.blocked_fill, center, radius)
        offset = radius - 2
        pygame.draw.line(
            screen,
            VisualTheme.blocked_x,
            (center[0] - offset, center[1] - offset),
            (center[0] + offset, center[1] + offset),
            2,
        )
        pygame.draw.line(
            screen,
            VisualTheme.blocked_x,
            (center[0] - offset, center[1] + offset),
            (center[0] + offset, center[1] - offset),
            2,
        )


def draw_depot(
    screen: pygame.Surface,
    depot: Optional[CityCoordinate],
    size: Optional[int] = None,
    show_caption: bool = True,
) -> None:
    if depot is None:
        return
    marker_size = VisualTheme.depot_marker_size if size is None else size
    center = (int(depot[0]), int(depot[1]))
    rect = pygame.Rect(0, 0, marker_size, marker_size)
    rect.center = center
    pygame.draw.rect(screen, VisualTheme.depot_stroke, rect.inflate(4, 4))
    pygame.draw.rect(screen, VisualTheme.depot_fill, rect)
    font = get_monospace_font(11, bold=True)
    label = font.render("D", True, VisualTheme.text_inverse)
    screen.blit(label, label.get_rect(center=center))
    if show_caption:
        caption = get_monospace_font(9).render("Depósito", True, VisualTheme.text_primary)
        screen.blit(
            caption,
            caption.get_rect(midtop=(center[0], center[1] + marker_size // 2 + 4)),
        )


def _blend_with_map(color: Tuple[int, int, int], alpha: float) -> Tuple[int, int, int]:
    background = VisualTheme.background_map
    return tuple(
        int(channel * alpha + background[index] * (1.0 - alpha))
        for index, channel in enumerate(color)
    )


def _draw_dashed_polyline(
    screen: pygame.Surface,
    points: List[CityCoordinate],
    color: Tuple[int, int, int],
    width: int = 2,
    dash_length: float = 8.0,
    gap_length: float = 6.0,
) -> None:
    if len(points) < 2:
        return
    draw_dash = True
    remaining = dash_length
    for index in range(len(points) - 1):
        start_x, start_y = points[index]
        end_x, end_y = points[index + 1]
        segment_dx = end_x - start_x
        segment_dy = end_y - start_y
        segment_length = math.hypot(segment_dx, segment_dy)
        if segment_length <= 1e-9:
            continue
        unit_x = segment_dx / segment_length
        unit_y = segment_dy / segment_length
        cursor = 0.0
        while cursor < segment_length:
            step = min(remaining, segment_length - cursor)
            next_cursor = cursor + step
            if draw_dash:
                pygame.draw.line(
                    screen,
                    color,
                    (start_x + unit_x * cursor, start_y + unit_y * cursor),
                    (start_x + unit_x * next_cursor, start_y + unit_y * next_cursor),
                    width,
                )
            cursor = next_cursor
            remaining -= step
            if remaining <= 1e-9:
                draw_dash = not draw_dash
                remaining = dash_length if draw_dash else gap_length


def _trip_polyline(
    mesh: DeliveryMesh,
    trip_coordinates: List[CityCoordinate],
) -> List[CityCoordinate]:
    points: List[CityCoordinate] = []
    for index in range(len(trip_coordinates) - 1):
        path = delivery_segment_path(
            mesh,
            trip_coordinates[index],
            trip_coordinates[index + 1],
        )
        if not path:
            continue
        path_coords = [mesh.network.nodes[node_id] for node_id in path]
        if points:
            path_coords = path_coords[1:]
        points.extend(path_coords)
    return points


def _trip_polyline_from_stored(
    mesh: DeliveryMesh,
    trip: Trip,
) -> List[CityCoordinate]:
    if not trip.path_node_ids:
        coordinates = [stop.coordinate for stop in trip.stops]
        return _trip_polyline(mesh, coordinates)
    points: List[CityCoordinate] = []
    for path in trip.path_node_ids:
        path_coords = [mesh.network.nodes[node_id] for node_id in path]
        if points and path_coords:
            path_coords = path_coords[1:]
        points.extend(path_coords)
    return points


def draw_polyline_arrows(
    screen: pygame.Surface,
    points: List[CityCoordinate],
    color: Tuple[int, int, int],
    emphasize_indices: Optional[Sequence[int]] = None,
    arrow_size: int = 7,
    min_segment_length: float = 24.0,
) -> None:
    if len(points) < 2:
        return
    emphasize = set(emphasize_indices or ())
    for index in range(len(points) - 1):
        origin = points[index]
        destination = points[index + 1]
        delta_x = destination[0] - origin[0]
        delta_y = destination[1] - origin[1]
        segment_length = math.hypot(delta_x, delta_y)
        if segment_length < min_segment_length:
            continue
        angle = math.atan2(delta_y, delta_x)
        size = arrow_size * (1.45 if index in emphasize else 1.0)
        ratio = 0.72 if index in emphasize else 0.55
        center_x = origin[0] + delta_x * ratio
        center_y = origin[1] + delta_y * ratio
        tip = (
            center_x + math.cos(angle) * size * 0.5,
            center_y + math.sin(angle) * size * 0.5,
        )
        base_center_x = center_x - math.cos(angle) * size * 0.5
        base_center_y = center_y - math.sin(angle) * size * 0.5
        perpendicular = angle + math.pi / 2
        half_base = size * 0.4
        base_left = (
            base_center_x + math.cos(perpendicular) * half_base,
            base_center_y + math.sin(perpendicular) * half_base,
        )
        base_right = (
            base_center_x - math.cos(perpendicular) * half_base,
            base_center_y - math.sin(perpendicular) * half_base,
        )
        triangle = [tip, base_left, base_right]
        fill = VisualTheme.route_arrow_fill if index in emphasize else color
        outline = color if index in emphasize else VisualTheme.route_arrow_outline
        pygame.draw.polygon(screen, fill, triangle)
        pygame.draw.polygon(screen, outline, triangle, 1)


def draw_animation_cursor(
    screen: pygame.Surface,
    point: CityCoordinate,
    color: Tuple[int, int, int],
    radius: int = 8,
) -> None:
    center = (int(point[0]), int(point[1]))
    pygame.draw.circle(screen, VisualTheme.route_arrow_outline, center, radius + 2)
    pygame.draw.circle(screen, color, center, radius)
    pygame.draw.circle(screen, VisualTheme.route_arrow_fill, center, max(2, radius // 3))


def draw_delivery_points(
    screen: pygame.Surface,
    deliveries: List[DeliveryPoint],
    node_radius: int,
) -> None:
    for point in deliveries:
        fill_color = priority_to_color(point.priority)
        center = (int(point.coordinate[0]), int(point.coordinate[1]))
        pygame.draw.circle(screen, VisualTheme.city_stroke, center, node_radius + 2)
        pygame.draw.circle(screen, fill_color, center, node_radius)


def draw_cities(
    screen: pygame.Surface,
    city_coordinates: List[CityCoordinate],
    priorities: List[int],
    node_radius: int,
) -> None:
    for city, priority in zip(city_coordinates, priorities):
        fill_color = priority_to_color(priority)
        point = (int(city[0]), int(city[1]))
        pygame.draw.circle(screen, VisualTheme.city_stroke, point, node_radius + 2)
        pygame.draw.circle(screen, fill_color, point, node_radius)


def draw_vehicle_plans(
    screen: pygame.Surface,
    mesh: Optional[DeliveryMesh],
    plans_by_vehicle: Dict[int, DecodedVehiclePlan],
    colors: Optional[List[Tuple[int, int, int]]] = None,
    focus_vehicle_id: Optional[int] = None,
    dim_others: bool = True,
    draw_arrows: bool = True,
) -> None:
    if mesh is None:
        return
    palette = colors or VisualTheme.vehicle_route_colors
    for vehicle_id, plan in plans_by_vehicle.items():
        is_focused = focus_vehicle_id is None or vehicle_id == focus_vehicle_id
        if focus_vehicle_id is not None and not is_focused and not dim_others:
            continue
        base_color = palette[vehicle_id % len(palette)]
        color = base_color if is_focused else _blend_with_map(base_color, 0.25)
        for trip_index, trip in enumerate(plan.trips):
            if len(trip.stops) < 2:
                continue
            points = _trip_polyline_from_stored(mesh, trip)
            if len(points) < 2:
                continue
            if trip_index == 0:
                pygame.draw.lines(screen, color, False, points, width=3)
            else:
                faded = color if is_focused else _blend_with_map(base_color, 0.18)
                if is_focused:
                    faded = _blend_with_map(base_color, 0.55)
                _draw_dashed_polyline(screen, points, faded, width=2)
            if draw_arrows and is_focused:
                emphasize = {len(points) - 2} if len(points) >= 2 else set()
                draw_polyline_arrows(screen, points, color, emphasize_indices=emphasize)


def draw_route_paths(
    screen: pygame.Surface,
    route: Route,
    line_color: Tuple[int, int, int],
    line_width: int = 1,
    draw_glow: bool = False,
    mesh: Optional[DeliveryMesh] = None,
) -> None:
    points: Sequence[CityCoordinate] = route
    closed = True
    if mesh is not None:
        expanded = expand_route_polyline(mesh, route)
        if len(expanded) >= 2:
            points = expanded
            closed = False

    if len(points) < 2:
        return

    if draw_glow:
        pygame.draw.lines(
            screen,
            VisualTheme.route_best_glow,
            closed,
            points,
            width=line_width + 4,
        )
    pygame.draw.lines(screen, line_color, closed, points, width=line_width)


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
