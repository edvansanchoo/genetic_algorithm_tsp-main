"""Estrutura visual da janela: sidebar, mapa e cabeçalhos."""

import pygame

from traveling_salesman_problem.config.visual_theme import VisualTheme
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
    statistics_font = get_monospace_font(13)
    muted_font = get_user_interface_font(11)

    screen.blit(
        title_font.render("Mapa da rota", True, VisualTheme.text_primary),
        (map_start_x + 16, 10),
    )

    penalty_label = "Evita árvores e lagos" if obstacle_penalties_active else "Só distância"
    penalty_color = VisualTheme.success if obstacle_penalties_active else VisualTheme.text_muted
    screen.blit(
        muted_font.render(penalty_label, True, penalty_color),
        (map_start_x + 16, 28),
    )

    statistics_text = "   ·   ".join([
        f"Geração {generation_number}",
        f"Custo {best_fitness:.1f}",
        f"Mutação {mutation_percentage:.0f}%",
    ])
    statistics_surface = statistics_font.render(statistics_text, True, VisualTheme.text_primary)
    statistics_rectangle = statistics_surface.get_rect(
        midright=(window_width - 16, VisualTheme.map_header_height // 2 + 2),
    )
    screen.blit(statistics_surface, statistics_rectangle)


def draw_map_legend(
    screen: pygame.Surface,
    position_x: int,
    position_y: int,
) -> None:
    legend_items = [
        (VisualTheme.route_best, "Melhor rota"),
        (VisualTheme.route_second_best, "Segunda melhor"),
        (VisualTheme.city_fill, "Cidades"),
        (VisualTheme.tree_foliage, "Árvore"),
        (VisualTheme.lake_water, "Lago"),
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
    hints = "Q · Sair          O · Penalidades de terreno          Esc · Fechar"
    screen.blit(
        hint_font.render(hints, True, VisualTheme.text_muted),
        (VisualTheme.control_margin, position_y),
    )
