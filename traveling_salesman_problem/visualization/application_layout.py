"""Estrutura visual da janela: sidebar, mapa e cabeçalhos."""

from typing import List, Tuple

import pygame

from traveling_salesman_problem.config.visual_theme import VisualTheme, priority_to_color
from traveling_salesman_problem.visualization.fonts import get_monospace_font, get_user_interface_font


def draw_application_chrome(
    screen: pygame.Surface,
    window_width: int,
    window_height: int,
) -> None:
    """Desenha fundo, sidebar e área do mapa."""
    screen.fill(VisualTheme.background_application)
    pygame.draw.rect(
        screen,
        VisualTheme.background_sidebar,
        pygame.Rect(0, 0, VisualTheme.sidebar_width, window_height),
    )
    pygame.draw.rect(
        screen,
        VisualTheme.background_map,
        pygame.Rect(
            VisualTheme.sidebar_width,
            VisualTheme.map_header_height,
            window_width - VisualTheme.sidebar_width,
            window_height - VisualTheme.map_header_height,
        ),
    )
    pygame.draw.line(
        screen,
        VisualTheme.divider,
        (VisualTheme.sidebar_width, 0),
        (VisualTheme.sidebar_width, window_height),
        2,
    )
    pygame.draw.line(
        screen,
        VisualTheme.divider,
        (VisualTheme.sidebar_width, VisualTheme.map_header_height),
        (window_width, VisualTheme.map_header_height),
        1,
    )


def draw_section_header(
    screen: pygame.Surface,
    position_x: int,
    position_y: int,
    width: int,
    title: str,
) -> int:
    """Desenha título de seção e retorna a posição vertical seguinte."""
    label_font = get_user_interface_font(12, bold=True)
    label_surface = label_font.render(title.upper(), True, VisualTheme.text_muted)
    screen.blit(label_surface, (position_x, position_y))
    line_y = position_y + 18
    pygame.draw.line(
        screen,
        VisualTheme.divider,
        (position_x, line_y),
        (position_x + width, line_y),
        1,
    )
    return line_y + 8


def draw_card(screen: pygame.Surface, rectangle: pygame.Rect) -> None:
    pygame.draw.rect(
        screen,
        VisualTheme.background_card,
        rectangle,
        border_radius=8,
    )
    pygame.draw.rect(
        screen,
        VisualTheme.border,
        rectangle,
        width=1,
        border_radius=8,
    )


def draw_summary_panel(
    screen: pygame.Surface,
    position_x: int,
    position_y: int,
    width: int,
    height: int,
    total_distance: float | None,
    total_trips: int | None,
) -> None:
    draw_card(screen, pygame.Rect(position_x, position_y, width, height))
    title_font = get_user_interface_font(13, bold=True)
    body_font = get_monospace_font(12)

    screen.blit(title_font.render("Resumo", True, VisualTheme.text_primary), (position_x + 12, position_y + 12))

    distance_text = f"{total_distance:.0f} px" if total_distance is not None else "---"
    trips_text = str(total_trips) if total_trips is not None else "---"

    screen.blit(
        body_font.render(f"Distância total: {distance_text}", True, VisualTheme.text_primary),
        (position_x + 12, position_y + 44),
    )
    screen.blit(
        body_font.render(f"Viagens: {trips_text}", True, VisualTheme.text_primary),
        (position_x + 12, position_y + 64),
    )


def draw_delivery_map_header(
    screen: pygame.Surface,
    map_start_x: int,
    window_width: int,
    total_distance: float | None,
    generation_number: int | None = None,
    active_vehicle_id: int | None = None,
    best_distance: float | None = None,
    second_best_distance: float | None = None,
) -> None:
    header_rectangle = pygame.Rect(
        map_start_x,
        0,
        window_width - map_start_x,
        VisualTheme.map_header_height,
    )
    pygame.draw.rect(screen, VisualTheme.background_map_header, header_rectangle)
    pygame.draw.line(
        screen,
        VisualTheme.divider,
        (map_start_x, VisualTheme.map_header_height - 1),
        (window_width, VisualTheme.map_header_height - 1),
        1,
    )

    title_font = get_user_interface_font(15, bold=True)
    muted_font = get_user_interface_font(11)
    statistics_font = get_monospace_font(11)

    screen.blit(
        title_font.render("Simulador de Entregas", True, VisualTheme.text_primary),
        (map_start_x + 16, 10),
    )

    if generation_number is not None and active_vehicle_id is not None:
        parts = [f"Gen {generation_number}", f"V{active_vehicle_id}"]
        display_best = best_distance if best_distance is not None else total_distance
        if display_best is not None:
            parts.append(f"melhor {display_best:.0f} px")
        if second_best_distance is not None and second_best_distance < float("inf"):
            parts.append(f"2ª {second_best_distance:.0f} px")
        subtitle = " · ".join(parts)
    else:
        subtitle = "Roteamento guloso · Configure e simule" if total_distance is None else "Roteamento guloso"
    screen.blit(
        muted_font.render(subtitle, True, VisualTheme.text_muted),
        (map_start_x + 16, 28),
    )

    if total_distance is not None:
        statistics_text = f"Total {total_distance:.0f} px"
        statistics_surface = statistics_font.render(statistics_text, True, VisualTheme.text_primary)
        statistics_rectangle = statistics_surface.get_rect(
            midright=(window_width - 16, VisualTheme.map_header_height // 2 + 2),
        )
        screen.blit(statistics_surface, statistics_rectangle)


def draw_results_panel(
    screen: pygame.Surface,
    result_lines: List[str],
    position_x: int,
    position_y: int,
    width: int,
    status_message: str | None = None,
) -> int:
    row_font = get_monospace_font(10)
    current_y = position_y

    if status_message:
        screen.blit(
            row_font.render(status_message, True, VisualTheme.accent),
            (position_x, current_y),
        )
        current_y += 16

    for line in result_lines:
        screen.blit(row_font.render(line, True, VisualTheme.text_primary), (position_x, current_y))
        current_y += 14

    return current_y + 4


def draw_trip_detail_panel(
    screen: pygame.Surface,
    simulation_result,
    active_vehicle_id: int,
    active_trip_index: int,
    view_mode: str,
    position_x: int,
    position_y: int,
    width: int,
) -> int:
    title_font = get_user_interface_font(11, bold=True)
    body_font = get_monospace_font(10)
    current_y = position_y

    vehicle = simulation_result.vehicles[active_vehicle_id - 1]
    if view_mode == "all":
        title = f"Veículo {active_vehicle_id} · todas as viagens ({len(vehicle.trips)})"
    else:
        trip_number = active_trip_index + 1 if vehicle.trips else 0
        title = f"Veículo {active_vehicle_id} · viagem {trip_number}"

    screen.blit(title_font.render(title, True, VisualTheme.text_primary), (position_x, current_y))
    current_y += 18

    if not vehicle.trips:
        screen.blit(body_font.render("Nenhuma viagem registrada.", True, VisualTheme.text_muted), (position_x, current_y))
        return current_y + 16

    trips = vehicle.trips if view_mode == "all" else [vehicle.trips[active_trip_index]]
    for trip_index, trip in enumerate(trips):
        if view_mode == "all":
            screen.blit(
                body_font.render(f"Viagem {trip_index + 1} · {trip.distance:.0f} px", True, VisualTheme.text_muted),
                (position_x, current_y),
            )
            current_y += 14

        stop_labels = []
        for stop in trip.stops:
            if stop.is_transit:
                stop_labels.append(stop.point_id)
            elif stop.items_delivered > 0:
                stop_labels.append(f"{stop.point_id}({stop.items_delivered})")
            else:
                stop_labels.append(stop.point_id)

        route_text = " → ".join(stop_labels)
        wrapped_lines = []
        while route_text:
            if body_font.size(route_text)[0] <= width:
                wrapped_lines.append(route_text)
                break
            split_at = max(route_text.rfind(" → ", 0, len(route_text) * width // body_font.size(route_text)[0]), 1)
            wrapped_lines.append(route_text[:split_at])
            route_text = route_text[split_at:].lstrip("→ ")

        for line in wrapped_lines:
            screen.blit(body_font.render(line, True, VisualTheme.text_primary), (position_x, current_y))
            current_y += 14

        if view_mode == "single":
            screen.blit(
                body_font.render(f"Distância: {trip.distance:.0f} px", True, VisualTheme.text_muted),
                (position_x, current_y),
            )
            current_y += 14

        if view_mode == "all" and trip_index < len(trips) - 1:
            current_y += 4

    return current_y + 4


def draw_map_header(
    screen: pygame.Surface,
    map_start_x: int,
    window_width: int,
    generation_number: int,
    best_fitness: float,
    best_distance: float,
    weighted_priority_penalty: float,
    priority_weight: float,
    mutation_percentage: float,
    obstacle_penalties_active: bool,
) -> None:
    header_rectangle = pygame.Rect(
        map_start_x,
        0,
        window_width - map_start_x,
        VisualTheme.map_header_height,
    )
    pygame.draw.rect(screen, VisualTheme.background_map_header, header_rectangle)
    pygame.draw.line(
        screen,
        VisualTheme.divider,
        (map_start_x, VisualTheme.map_header_height - 1),
        (window_width, VisualTheme.map_header_height - 1),
        1,
    )

    title_font = get_user_interface_font(15, bold=True)
    statistics_font = get_monospace_font(11)
    muted_font = get_user_interface_font(11)

    screen.blit(
        title_font.render("Mapa da rota", True, VisualTheme.text_primary),
        (map_start_x + 16, 10),
    )

    if priority_weight <= 0:
        mode_label = "Só distância"
        mode_color = VisualTheme.text_muted
    elif priority_weight < 50:
        mode_label = "Equilibrado"
        mode_color = VisualTheme.text_primary
    else:
        mode_label = "Críticas primeiro"
        mode_color = VisualTheme.accent

    if obstacle_penalties_active:
        mode_label = f"{mode_label} · Evita terreno"

    screen.blit(
        muted_font.render(mode_label, True, mode_color),
        (map_start_x + 16, 28),
    )

    statistics_parts = [
        f"Gen {generation_number}",
        f"Fit {best_fitness:.0f}",
        f"Dist {best_distance:.0f}",
    ]
    if priority_weight > 0:
        statistics_parts.append(f"Prior {weighted_priority_penalty:.0f}")
    statistics_parts.append(f"Mut {mutation_percentage:.0f}%")
    statistics_text = "  ·  ".join(statistics_parts)
    statistics_surface = statistics_font.render(statistics_text, True, VisualTheme.text_primary)
    max_statistics_width = window_width - map_start_x - 32
    if statistics_surface.get_width() > max_statistics_width:
        while statistics_surface.get_width() > max_statistics_width and len(statistics_text) > 0:
            statistics_text = statistics_text[:-1]
        statistics_surface = statistics_font.render(f"{statistics_text}…", True, VisualTheme.text_primary)
    statistics_rectangle = statistics_surface.get_rect(
        midright=(window_width - 16, VisualTheme.map_header_height // 2 + 2),
    )
    screen.blit(statistics_surface, statistics_rectangle)


def draw_delivery_order_panel(
    screen: pygame.Surface,
    visit_order: List[Tuple[int, int, int]],
    position_x: int,
    position_y: int,
    width: int,
    maximum_visible_rows: int | None = None,
    draw_title: bool = True,
) -> int:
    visible_rows = len(visit_order) if maximum_visible_rows is None else maximum_visible_rows
    row_font = get_monospace_font(10)
    current_y = position_y

    if draw_title:
        header_font = get_user_interface_font(11, bold=True)
        screen.blit(
            header_font.render("ORDEM DE ENTREGAS", True, VisualTheme.text_muted),
            (position_x, current_y),
        )
        current_y += 18
        pygame.draw.line(
            screen,
            VisualTheme.divider,
            (position_x, current_y),
            (position_x + width, current_y),
            1,
        )
        current_y += 6

    for position, city_number, priority in visit_order[:visible_rows]:
        critical_marker = " ★" if priority >= 8 else ""
        line = f"{position:2d} · Cidade {city_number:2d} · prior. {priority}{critical_marker}"
        screen.blit(row_font.render(line, True, VisualTheme.text_primary), (position_x, current_y))
        current_y += 16

    return current_y + 4


def draw_map_legend(
    screen: pygame.Surface,
    position_x: int,
    position_y: int,
) -> None:
    legend_items = [
        (VisualTheme.route_best, "Melhor rota"),
        (VisualTheme.route_second_best, "Segunda melhor"),
        (VisualTheme.route_best, "→ Direção da rota"),
        (VisualTheme.text_primary, "Posição na rota (1–N)"),
        (priority_to_color(1), "Baixa prioridade (1)"),
        (priority_to_color(5), "Média prioridade (5)"),
        (priority_to_color(10), "Alta prioridade (10)"),
        (VisualTheme.tree_foliage, "Árvore"),
        (VisualTheme.lake_water, "Lago"),
    ]
    padding = 10
    row_height = 18
    label_font = get_user_interface_font(11)
    panel_width = 180
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
        pygame.draw.circle(panel_surface, color, (padding + 6, item_y + 6), 5)
        panel_surface.blit(
            label_font.render(label, True, VisualTheme.text_muted),
            (padding + 18, item_y),
        )

    screen.blit(panel_surface, (position_x, position_y))


def draw_sidebar_footer(
    screen: pygame.Surface,
    position_y: int,
) -> None:
    hint_font = get_user_interface_font(10)
    first_line = "Q · Sair          Esc · Fechar          F · Tela cheia"
    second_line = "Sortear posições · Simular rotas"
    screen.blit(
        hint_font.render(first_line, True, VisualTheme.text_muted),
        (VisualTheme.control_margin, position_y),
    )
    screen.blit(
        hint_font.render(second_line, True, VisualTheme.text_muted),
        (VisualTheme.control_margin, position_y + 16),
    )
