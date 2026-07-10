"""Gráfico de convergência do algoritmo genético."""

from typing import Dict, List, Optional, Sequence, Tuple

import matplotlib
import matplotlib.pyplot as plt
import pygame
from matplotlib.backends.backend_agg import FigureCanvasAgg

from traveling_salesman_problem.config.visual_theme import VisualTheme
from traveling_salesman_problem.visualization.fonts import get_user_interface_font

matplotlib.use("Agg")


def draw_convergence_chart(
    screen: pygame.Surface,
    generation_numbers: list,
    fitness_values: list = None,
    horizontal_axis_label: str = "Geração",
    vertical_axis_label: str = "Custo da rota",
    series: Optional[Dict[int, Sequence[float]]] = None,
    series_colors: Optional[List[Tuple[int, int, int]]] = None,
) -> None:
    figure, axes = plt.subplots(figsize=(4.4, 4), dpi=100)
    axes.set_facecolor("#f8fafc")
    figure.patch.set_facecolor("#f1f4f9")

    if series:
        colors = series_colors or VisualTheme.vehicle_route_colors
        for index, (vehicle_id, values) in enumerate(sorted(series.items())):
            color = colors[index % len(colors)]
            hex_color = "#{:02x}{:02x}{:02x}".format(*color)
            xs = list(range(1, len(values) + 1))
            axes.plot(xs, values, color=hex_color, linewidth=2, label=f"V{vehicle_id + 1}")
        axes.legend(fontsize=7, loc="upper right")
    else:
        axes.plot(generation_numbers, fitness_values or [], color="#2563eb", linewidth=2)

    axes.set_ylabel(vertical_axis_label, fontsize=9, color="#475569")
    axes.set_xlabel(horizontal_axis_label, fontsize=9, color="#475569")
    axes.tick_params(labelsize=8, colors="#64748b")
    axes.grid(True, alpha=0.35, linestyle="--")
    for spine in axes.spines.values():
        spine.set_color("#cbd5e1")
    plt.tight_layout(pad=1.0)

    canvas = FigureCanvasAgg(figure)
    canvas.draw()
    raw_image_data = bytes(canvas.buffer_rgba())
    chart_surface = pygame.image.frombuffer(
        raw_image_data,
        canvas.get_width_height(),
        "RGBA",
    )
    screen.blit(chart_surface, (0, 0))
    plt.close(figure)

    plot_frame = pygame.Rect(8, 8, VisualTheme.sidebar_width - 16, VisualTheme.plot_height - 8)
    pygame.draw.rect(screen, VisualTheme.border, plot_frame, width=1, border_radius=4)
    caption = get_user_interface_font(11, bold=True).render(
        "Convergência",
        True,
        VisualTheme.text_muted,
    )
    screen.blit(caption, (plot_frame.x + 8, plot_frame.bottom - 22))
