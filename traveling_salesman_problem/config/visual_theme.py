"""Cores, tipografia e medidas compartilhadas pela interface Pygame."""


class VisualTheme:
    sidebar_width: int = 450
    plot_height: int = 400
    map_header_height: int = 44
    control_margin: int = 14
    control_gap: int = 10
    section_gap: int = 16
    row_height: int = 32
    sidebar_footer_height: int = 36
    scrollbar_width: int = 6

    background_application = (248, 249, 252)
    background_sidebar = (241, 244, 249)
    background_card = (255, 255, 255)
    background_map = (232, 245, 224)
    background_map_header = (255, 255, 255)

    border = (214, 220, 229)
    border_strong = (180, 188, 200)
    divider = (220, 226, 235)

    text_primary = (28, 32, 40)
    text_muted = (96, 105, 120)
    text_inverse = (255, 255, 255)

    accent = (37, 99, 235)
    accent_hover = (29, 78, 216)
    accent_soft = (219, 234, 254)
    accent_track = (191, 219, 254)

    success = (22, 163, 74)
    success_background = (220, 252, 231)
    success_border = (134, 239, 172)

    neutral = (148, 156, 169)
    neutral_background = (241, 245, 249)
    neutral_border = (203, 213, 225)

    city_fill = (220, 38, 38)
    city_stroke = (255, 255, 255)
    route_best = (37, 99, 235)
    route_best_glow = (191, 219, 254)
    route_second_best = (148, 163, 184)

    obstacle_fill = (254, 202, 202, 140)
    obstacle_border = (239, 68, 68)
    obstacle_disabled = (226, 232, 240)

    mesh_edge = (203, 213, 225)
    transit_fill = (148, 163, 184)
    transit_stroke = (100, 116, 139)
    blocked_fill = (239, 68, 68)
    blocked_x = (127, 29, 29)

    depot_fill = (15, 23, 42)
    depot_stroke = (255, 255, 255)
    depot_marker_size: int = 18
    route_arrow_fill = (255, 255, 255)
    route_arrow_outline = (15, 23, 42)
    vehicle_route_colors = [
        (37, 99, 235),
        (220, 38, 38),
        (5, 150, 105),
        (217, 119, 6),
        (124, 58, 237),
    ]

    tree_trunk = (101, 67, 33)
    tree_trunk_dark = (78, 52, 26)
    tree_foliage = (34, 139, 34)
    lake_shore = (210, 180, 140)
    lake_shore_dark = (160, 130, 95)
    lake_water = (14, 165, 233)
    terrain_disabled = (180, 190, 180)

    font_user_interface = "Segoe UI"
    font_monospace = "Consolas"


def priority_to_color(priority: int) -> tuple[int, int, int]:
    """Interpola verde (1) → amarelo (5) → vermelho (10)."""
    clamped_priority = max(1, min(10, priority))
    low_color = (76, 175, 80)
    mid_color = (255, 193, 7)
    high_color = (244, 67, 54)

    if clamped_priority <= 5:
        ratio = (clamped_priority - 1) / 4
        return _interpolate_color(low_color, mid_color, ratio)

    ratio = (clamped_priority - 5) / 5
    return _interpolate_color(mid_color, high_color, ratio)


def _interpolate_color(
    start_color: tuple[int, int, int],
    end_color: tuple[int, int, int],
    ratio: float,
) -> tuple[int, int, int]:
    return tuple(
        int(start + (end - start) * ratio)
        for start, end in zip(start_color, end_color)
    )
