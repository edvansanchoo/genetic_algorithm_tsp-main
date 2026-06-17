"""Desenho procedural de árvores e lagos no mapa."""

import pygame

from traveling_salesman_problem.config.visual_theme import VisualTheme
from traveling_salesman_problem.obstacles.models import LakeObstacle, TreeObstacle

FOLIAGE_COLOR_VARIANTS = [
    [(34, 139, 34), (46, 125, 50), (22, 101, 52)],
    [(56, 142, 60), (76, 175, 80), (27, 94, 32)],
    [(45, 106, 79), (62, 142, 95), (30, 86, 49)],
]

LAKE_WATER_COLOR_VARIANTS = [
    [(56, 189, 248), (14, 165, 233), (2, 132, 199)],
    [(52, 211, 153), (16, 185, 129), (5, 150, 105)],
    [(96, 165, 250), (59, 130, 246), (37, 99, 235)],
]


def _draw_tree_foliage(
    surface: pygame.Surface,
    center_x: int,
    center_y: int,
    radius: int,
    variant_index: int,
) -> None:
    colors = FOLIAGE_COLOR_VARIANTS[variant_index % len(FOLIAGE_COLOR_VARIANTS)]
    crown_center_y = center_y - radius // 4
    crown_radius = int(radius * 0.85)

    pygame.draw.circle(surface, colors[2], (center_x, crown_center_y), crown_radius)
    pygame.draw.circle(
        surface,
        colors[0],
        (center_x - crown_radius // 3, crown_center_y - crown_radius // 5),
        int(crown_radius * 0.75),
    )
    pygame.draw.circle(
        surface,
        colors[1],
        (center_x + crown_radius // 3, crown_center_y - crown_radius // 6),
        int(crown_radius * 0.7),
    )
    pygame.draw.circle(
        surface,
        colors[0],
        (center_x, crown_center_y - crown_radius // 3),
        int(crown_radius * 0.55),
    )


def draw_tree(screen: pygame.Surface, tree: TreeObstacle) -> None:
    center_x = tree.center_x
    center_y = tree.center_y
    radius = tree.radius

    if not tree.enabled:
        pygame.draw.circle(
            screen,
            VisualTheme.terrain_disabled,
            (center_x, center_y),
            radius,
            width=2,
        )
        trunk_width = max(4, radius // 4)
        trunk_height = max(8, radius // 2)
        trunk_rect = pygame.Rect(
            center_x - trunk_width // 2,
            center_y + radius // 6,
            trunk_width,
            trunk_height,
        )
        pygame.draw.rect(screen, VisualTheme.terrain_disabled, trunk_rect, width=1, border_radius=2)
        return

    shadow_surface = pygame.Surface((radius * 2, radius), pygame.SRCALPHA)
    pygame.draw.ellipse(
        shadow_surface,
        (0, 0, 0, 45),
        (0, radius // 3, radius * 2, radius // 2),
    )
    screen.blit(shadow_surface, (center_x - radius, center_y + radius // 3))

    trunk_width = max(6, radius // 3)
    trunk_height = max(10, radius // 2)
    trunk_rect = pygame.Rect(
        center_x - trunk_width // 2,
        center_y + radius // 8,
        trunk_width,
        trunk_height,
    )
    pygame.draw.rect(screen, VisualTheme.tree_trunk, trunk_rect, border_radius=3)
    pygame.draw.rect(screen, VisualTheme.tree_trunk_dark, trunk_rect, width=1, border_radius=3)

    _draw_tree_foliage(screen, center_x, center_y, radius, tree.variant_index)


def draw_lake(screen: pygame.Surface, lake: LakeObstacle) -> None:
    lake_rect = lake.rectangle
    center_x = lake_rect.centerx
    center_y = lake_rect.centery
    ellipse_rect = lake_rect.inflate(-8, -8)

    if not lake.enabled:
        pygame.draw.ellipse(screen, VisualTheme.terrain_disabled, ellipse_rect, width=2)
        return

    shore_rect = lake_rect.inflate(6, 6)
    pygame.draw.ellipse(screen, VisualTheme.lake_shore, shore_rect)
    pygame.draw.ellipse(screen, VisualTheme.lake_shore_dark, shore_rect, width=2)

    colors = LAKE_WATER_COLOR_VARIANTS[lake.variant_index % len(LAKE_WATER_COLOR_VARIANTS)]
    pygame.draw.ellipse(screen, colors[0], ellipse_rect)
    inner_rect = ellipse_rect.inflate(-ellipse_rect.width // 4, -ellipse_rect.height // 4)
    pygame.draw.ellipse(screen, colors[1], inner_rect)
    deep_rect = inner_rect.inflate(-inner_rect.width // 3, -inner_rect.height // 3)
    pygame.draw.ellipse(screen, colors[2], deep_rect)

    ripple_color = (255, 255, 255, 80)
    for ripple_index in range(3):
        ripple_surface = pygame.Surface((ellipse_rect.width, ellipse_rect.height // 3), pygame.SRCALPHA)
        ripple_y = ellipse_rect.height // 4 + ripple_index * (ellipse_rect.height // 5)
        pygame.draw.arc(
            ripple_surface,
            ripple_color,
            (8, ripple_y, ellipse_rect.width - 16, ellipse_rect.height // 4),
            0.2,
            2.9,
            1,
        )
        screen.blit(ripple_surface, (ellipse_rect.x, ellipse_rect.y))

    highlight_rect = pygame.Rect(
        center_x - ellipse_rect.width // 5,
        center_y - ellipse_rect.height // 3,
        ellipse_rect.width // 4,
        ellipse_rect.height // 6,
    )
    highlight_surface = pygame.Surface(highlight_rect.size, pygame.SRCALPHA)
    pygame.draw.ellipse(highlight_surface, (255, 255, 255, 90), highlight_surface.get_rect())
    screen.blit(highlight_surface, highlight_rect.topleft)
