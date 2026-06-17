"""Gráfico de convergência do algoritmo genético."""

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
    fitness_values: list,
    horizontal_axis_label: str = "Geração",
    vertical_axis_label: str = "Custo da rota",
) -> None:
    figure, axes = plt.subplots(figsize=(4.4, 4), dpi=100)
    axes.set_facecolor("#f8fafc")
    figure.patch.set_facecolor("#f1f4f9")
    axes.plot(generation_numbers, fitness_values, color="#2563eb", linewidth=2)
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
