"""Estrutura visual da janela: sidebar, mapa e cabeçalhos."""

from dataclasses import dataclass
from typing import List, Literal, Optional, Tuple

import pygame

from traveling_salesman_problem.config.visual_theme import VisualTheme, priority_to_color
from traveling_salesman_problem.visualization.fonts import get_monospace_font, get_user_interface_font

LegendIconKind = Literal[
    "square",
    "circle",
    "blocked",
    "line_solid",
    "line_dashed",
    "mesh_line",
    "priority_bar",
    "hint",
]


@dataclass(frozen=True)
class LegendItem:
    kind: LegendIconKind
    label: str
    color: Tuple[int, int, int] = (0, 0, 0)


def _blend_with_map(color: Tuple[int, int, int], alpha: float) -> Tuple[int, int, int]:
    background = VisualTheme.background_map
    return tuple(
        int(channel * alpha + background[index] * (1.0 - alpha))
        for index, channel in enumerate(color)
    )


def _build_legend_items(
    show_mesh: bool,
    vehicle_count: int,
    focus_vehicle_id: Optional[int],
    has_runner_up: bool,
    focus_trip_index: Optional[int] = None,
    trip_auto_cycle: bool = False,
) -> List[LegendItem]:
    items: List[LegendItem] = [
        LegendItem("square", "Depósito", VisualTheme.depot_fill),
        LegendItem("priority_bar", "Entrega (prior. 1 → 10)"),
        LegendItem("circle", "Nó de trânsito", VisualTheme.transit_fill),
        LegendItem("blocked", "Bloqueado (clique no mapa)", VisualTheme.blocked_fill),
    ]

    if show_mesh:
        items.append(LegendItem("mesh_line", "Aresta da malha", VisualTheme.mesh_edge))

    focused = focus_vehicle_id is not None
    palette = VisualTheme.vehicle_route_colors

    if vehicle_count <= 1 and not focused:
        route_color = palette[0]
        items.append(LegendItem("line_solid", "Rota — viagem 1", route_color))
        items.append(LegendItem("line_dashed", "Rota — viagens 2+", route_color))
    else:
        for vehicle_id in range(max(1, vehicle_count)):
            base_color = palette[vehicle_id % len(palette)]
            if focused and vehicle_id != focus_vehicle_id:
                continue
            items.append(
                LegendItem(
                    "line_solid",
                    f"V{vehicle_id + 1} rota",
                    base_color,
                )
            )
        if focused and vehicle_count > 1:
            items.append(
                LegendItem(
                    "line_solid",
                    "Outros veículos (foco)",
                    _blend_with_map(palette[0], 0.25),
                )
            )
            if has_runner_up:
                items.append(
                    LegendItem(
                        "line_dashed",
                        "2ª melhor — viagem ativa",
                        VisualTheme.route_second_best,
                    )
                )
            focus_color = palette[focus_vehicle_id % len(palette)]
            if focus_trip_index is not None:
                items.append(
                    LegendItem(
                        "line_solid",
                        f"Viagem {focus_trip_index + 1} (fixa)",
                        focus_color,
                    )
                )
            elif trip_auto_cycle:
                items.append(
                    LegendItem(
                        "line_solid",
                        "Viagem ativa (auto)",
                        focus_color,
                    )
                )
            items.append(LegendItem("circle", "Animação (foco)", focus_color))

    items.append(LegendItem("hint", "Clique viagem no painel · mapa: bloquear"))
    return items


def _draw_legend_icon(
    surface: pygame.Surface,
    item: LegendItem,
    center_x: int,
    center_y: int,
) -> None:
    if item.kind == "square":
        rect = pygame.Rect(0, 0, 9, 9)
        rect.center = (center_x, center_y)
        pygame.draw.rect(surface, VisualTheme.depot_stroke, rect.inflate(2, 2))
        pygame.draw.rect(surface, item.color, rect)
    elif item.kind == "circle":
        pygame.draw.circle(surface, VisualTheme.city_stroke, (center_x, center_y), 6)
        pygame.draw.circle(surface, item.color, (center_x, center_y), 5)
    elif item.kind == "blocked":
        pygame.draw.circle(surface, item.color, (center_x, center_y), 5)
        offset = 3
        pygame.draw.line(
            surface,
            VisualTheme.blocked_x,
            (center_x - offset, center_y - offset),
            (center_x + offset, center_y + offset),
            2,
        )
        pygame.draw.line(
            surface,
            VisualTheme.blocked_x,
            (center_x - offset, center_y + offset),
            (center_x + offset, center_y - offset),
            2,
        )
    elif item.kind in ("line_solid", "mesh_line"):
        pygame.draw.line(
            surface,
            item.color,
            (center_x - 7, center_y),
            (center_x + 7, center_y),
            2 if item.kind == "line_solid" else 1,
        )
    elif item.kind == "line_dashed":
        x_start = center_x - 7
        for segment in range(3):
            seg_x = x_start + segment * 5
            pygame.draw.line(
                surface,
                item.color,
                (seg_x, center_y),
                (min(seg_x + 3, center_x + 7), center_y),
                2,
            )
    elif item.kind == "priority_bar":
        sample_priorities = (1, 5, 10)
        for index, priority in enumerate(sample_priorities):
            pygame.draw.circle(
                surface,
                priority_to_color(priority),
                (center_x - 6 + index * 6, center_y),
                4,
            )
    elif item.kind == "hint":
        return


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
    obstacle_penalties_active: bool = False,
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

    mode_label = f"{mode_label} · VRP"

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


def draw_route_text_panel(
    screen: pygame.Surface,
    lines: List[str],
    position_x: int,
    position_y: int,
    width: int,
    *,
    row_vehicle_ids: Optional[List[Optional[int]]] = None,
    row_trip_indices: Optional[List[Optional[int]]] = None,
    row_is_header: Optional[List[bool]] = None,
    focus_vehicle_id: Optional[int] = None,
    focus_trip_index: Optional[int] = None,
    active_trip_index: Optional[int] = None,
) -> int:
    row_font = get_monospace_font(10)
    bold_font = get_monospace_font(10, bold=True)
    current_y = position_y
    for index, line in enumerate(lines):
        is_header = (
            row_is_header[index]
            if row_is_header is not None and index < len(row_is_header)
            else line.startswith("Veículo")
        )
        font = bold_font if is_header else row_font
        color = VisualTheme.text_primary if is_header else VisualTheme.text_muted
        vehicle_id = (
            row_vehicle_ids[index]
            if row_vehicle_ids is not None and index < len(row_vehicle_ids)
            else None
        )
        trip_index = (
            row_trip_indices[index]
            if row_trip_indices is not None and index < len(row_trip_indices)
            else None
        )
        if (
            not is_header
            and focus_vehicle_id is not None
            and vehicle_id == focus_vehicle_id
        ):
            highlighted = (
                focus_trip_index
                if focus_trip_index is not None
                else active_trip_index
            )
            if trip_index == highlighted:
                color = VisualTheme.text_primary
                font = bold_font
        display = line if len(line) <= 52 else f"{line[:49]}…"
        screen.blit(font.render(display, True, color), (position_x, current_y))
        current_y += 16
    return current_y + 4


def draw_map_legend(
    screen: pygame.Surface,
    position_x: int,
    position_y: int,
    show_mesh: bool = False,
    vehicle_count: int = 1,
    focus_vehicle_id: Optional[int] = None,
    has_runner_up: bool = False,
    focus_trip_index: Optional[int] = None,
    trip_auto_cycle: bool = False,
) -> None:
    legend_items = _build_legend_items(
        show_mesh=show_mesh,
        vehicle_count=vehicle_count,
        focus_vehicle_id=focus_vehicle_id,
        has_runner_up=has_runner_up,
        focus_trip_index=focus_trip_index,
        trip_auto_cycle=trip_auto_cycle,
    )
    padding = 10
    row_height = 18
    label_font = get_user_interface_font(11)
    hint_font = get_user_interface_font(9)
    panel_width = 210
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

    icon_center_x = padding + 8
    for index, item in enumerate(legend_items):
        item_y = padding + index * row_height
        if item.kind == "hint":
            panel_surface.blit(
                hint_font.render(item.label, True, VisualTheme.text_muted),
                (padding, item_y + 2),
            )
            continue
        _draw_legend_icon(panel_surface, item, icon_center_x, item_y + 9)
        panel_surface.blit(
            label_font.render(item.label, True, VisualTheme.text_muted),
            (padding + 20, item_y),
        )

    screen.blit(panel_surface, (position_x, position_y))


def draw_sidebar_footer(
    screen: pygame.Surface,
    position_y: int,
) -> None:
    hint_font = get_user_interface_font(10)
    first_line = "Q · Sair          Esc · Fechar"
    second_line = "Filtro cicla veículos · Malha on/off"
    screen.blit(
        hint_font.render(first_line, True, VisualTheme.text_muted),
        (VisualTheme.control_margin, position_y),
    )
    screen.blit(
        hint_font.render(second_line, True, VisualTheme.text_muted),
        (VisualTheme.control_margin, position_y + 16),
    )
