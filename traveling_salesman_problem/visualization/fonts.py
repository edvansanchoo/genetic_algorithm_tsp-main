"""Cache de fontes Pygame para a interface."""

import pygame

from traveling_salesman_problem.config.visual_theme import VisualTheme

_font_cache: dict[tuple[str, int, bool], pygame.font.Font] = {}


def get_user_interface_font(size: int, bold: bool = False) -> pygame.font.Font:
    cache_key = (VisualTheme.font_user_interface, size, bold)
    if cache_key not in _font_cache:
        _font_cache[cache_key] = pygame.font.SysFont(
            VisualTheme.font_user_interface,
            size,
            bold=bold,
        )
    return _font_cache[cache_key]


def get_monospace_font(size: int, bold: bool = False) -> pygame.font.Font:
    cache_key = (VisualTheme.font_monospace, size, bold)
    if cache_key not in _font_cache:
        _font_cache[cache_key] = pygame.font.SysFont(
            VisualTheme.font_monospace,
            size,
            bold=bold,
        )
    return _font_cache[cache_key]
