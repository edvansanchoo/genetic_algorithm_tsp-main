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
) -> int:
    row_font = get_monospace_font(10)
    bold_font = get_monospace_font(10, bold=True)
    current_y = position_y
    for line in lines:
        is_header = line.startswith("Veículo")
        font = bold_font if is_header else row_font
        color = VisualTheme.text_primary if is_header else VisualTheme.text_muted
        display = line if len(line) <= 52 else f"{line[:49]}…"
        screen.blit(font.render(display, True, color), (position_x, current_y))
        current_y += 16
    return current_y + 4


def draw_map_legend(
    screen: pygame.Surface,
    position_x: int,
    position_y: int,
) -> None:
    legend_items = [
        (VisualTheme.depot_fill, "Depósito"),
        (VisualTheme.route_best, "Rota veículo"),
        (VisualTheme.route_second_best, "2ª melhor (foco)"),
        (VisualTheme.transit_fill, "Nó de trânsito"),
        (VisualTheme.blocked_fill, "Nó bloqueado"),
        (VisualTheme.mesh_edge, "Aresta da malha"),
        (priority_to_color(1), "Baixa prioridade (1)"),
        (priority_to_color(5), "Média prioridade (5)"),
        (priority_to_color(10), "Alta prioridade (10)"),
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
