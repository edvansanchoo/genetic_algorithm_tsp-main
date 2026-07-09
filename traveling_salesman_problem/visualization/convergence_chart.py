"""Gráfico de convergência do algoritmo genético."""

import matplotlib
import matplotlib.pyplot as plt
import pygame
from matplotlib.backends.backend_agg import FigureCanvasAgg

from traveling_salesman_problem.config.visual_theme import VisualTheme
from traveling_salesman_problem.visualization.fonts import get_user_interface_font

matplotlib.use("Agg")


def _series_color(color) -> str:
    if isinstance(color, tuple):
        return f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
    return color


def draw_convergence_chart(
    screen: pygame.Surface,
    generation_numbers: list,
    fitness_values: list,
    horizontal_axis_label: str = "Geração",
    vertical_axis_label: str = "Custo da rota",
    series_colors: tuple | None = None,
    series_labels: list[str] | None = None,
    highlight_index: int | None = None,
) -> None:
    figure, axes = plt.subplots(figsize=(4.4, 4), dpi=100)
    axes.set_facecolor("#f8fafc")
    figure.patch.set_facecolor("#f1f4f9")

    if fitness_values and isinstance(fitness_values[0], list):
        series_list = fitness_values
        colors = series_colors or ("#2563eb",)
        for index, series in enumerate(series_list):
            label = (
                series_labels[index]
                if series_labels and index < len(series_labels)
                else f"V{index + 1}"
            )
            color = _series_color(colors[index % len(colors)])
            is_highlight = highlight_index is not None and index == highlight_index
            linewidth = 2.5 if is_highlight else 1.5
            alpha = 1.0 if is_highlight else 0.4
            axes.plot(
                generation_numbers[: len(series)],
                series,
                color=color,
                linewidth=linewidth,
                alpha=alpha,
                label=label,
            )
        if len(series_list) > 1:
            axes.legend(fontsize=8, loc="upper right")
    else:
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
