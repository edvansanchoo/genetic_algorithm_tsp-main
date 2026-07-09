"""Aplicação Pygame: loop principal da simulação de entregas."""

import sys

import pygame

from traveling_salesman_problem.config.application_settings import ApplicationSettings
from traveling_salesman_problem.config.visual_theme import VisualTheme
from traveling_salesman_problem.simulation.simulation_state import SimulationState
from traveling_salesman_problem.visualization.application_layout import (
    draw_application_chrome,
    draw_delivery_map_header,
    draw_results_panel,
    draw_section_header,
    draw_sidebar_footer,
    draw_summary_panel,
)
from traveling_salesman_problem.visualization.map_renderer import (
    draw_delivery_points,
    draw_depot,
    draw_vehicle_legend,
    draw_vehicle_routes,
)
from traveling_salesman_problem.visualization.sidebar_scroll import SidebarScrollView


def _draw_scrollable_sidebar(
    simulation: SimulationState,
    sidebar_scroll: SidebarScrollView,
    controls_width: int,
) -> None:
    content_surface = sidebar_scroll.content_surface

    draw_section_header(
        content_surface,
        VisualTheme.control_margin,
        simulation.section_config_y,
        controls_width,
        "Configuração",
    )
    simulation.vehicle_count_slider.draw(content_surface)
    simulation.delivery_point_count_slider.draw(content_surface)
    simulation.total_items_slider.draw(content_surface)

    draw_section_header(
        content_surface,
        VisualTheme.control_margin,
        simulation.section_actions_y,
        controls_width,
        "Ações",
    )
    simulation.shuffle_positions_button.draw(content_surface)
    if simulation.can_simulate():
        simulation.simulate_button.draw(content_surface)
    else:
        muted_button = simulation.simulate_button
        pygame.draw.rect(
            content_surface,
            VisualTheme.neutral,
            muted_button.rectangle,
            border_radius=8,
        )
        from traveling_salesman_problem.visualization.fonts import get_user_interface_font

        label_surface = get_user_interface_font(13, bold=True).render(
            muted_button.label,
            True,
            VisualTheme.text_inverse,
        )
        content_surface.blit(label_surface, label_surface.get_rect(center=muted_button.rectangle.center))

    draw_section_header(
        content_surface,
        VisualTheme.control_margin,
        simulation.section_results_y,
        controls_width,
        "Resultado",
    )
    draw_results_panel(
        content_surface,
        simulation.result_lines,
        VisualTheme.control_margin,
        simulation.section_results_y + 26,
        controls_width,
        status_message=simulation.status_message,
    )


def run_application(settings=None) -> None:
    if settings is None:
        settings = ApplicationSettings()

    pygame.init()
    screen = pygame.display.set_mode(
        (settings.window_width, settings.window_height),
        pygame.RESIZABLE,
    )
    pygame.display.set_caption("Simulador de Entregas · Roteamento Guloso")
    clock = pygame.time.Clock()

    simulation = SimulationState(settings=settings)
    simulation.initialize()

    sidebar_scroll = SidebarScrollView(
        viewport_top=settings.scroll_viewport_top,
        viewport_height=settings.scroll_viewport_height,
        content_width=settings.plot_horizontal_offset - VisualTheme.scrollbar_width - 8,
    )

    is_running = True
    fullscreen = False

    while is_running:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEWHEEL:
                if sidebar_scroll.handle_event(event):
                    continue
            elif sidebar_scroll.handle_event(event):
                continue

            if event.type == pygame.QUIT:
                is_running = False
            elif event.type == pygame.VIDEORESIZE:
                saved_vehicle_count = simulation.vehicle_count_slider.integer_value
                saved_point_count = simulation.delivery_point_count_slider.integer_value
                saved_total_items = simulation.total_items_slider.selected_value

                screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                settings = ApplicationSettings(
                    window_width=event.w,
                    window_height=event.h,
                )
                simulation = SimulationState(settings=settings)
                simulation.initialize()
                simulation.vehicle_count_slider.value = float(saved_vehicle_count)
                simulation.delivery_point_count_slider.value = float(saved_point_count)
                simulation.total_items_slider.value = float(saved_total_items)
                simulation.total_items_slider.snap_to_nearest()

                sidebar_scroll = SidebarScrollView(
                    viewport_top=settings.scroll_viewport_top,
                    viewport_height=settings.scroll_viewport_height,
                    content_width=settings.plot_horizontal_offset - VisualTheme.scrollbar_width - 8,
                )
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    is_running = False
                elif event.key == pygame.K_f:
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode(
                            (settings.window_width, settings.window_height),
                            pygame.RESIZABLE,
                        )
                else:
                    simulation.handle_control_events(event)
            elif event.type in (
                pygame.MOUSEBUTTONDOWN,
                pygame.MOUSEBUTTONUP,
                pygame.MOUSEMOTION,
            ):
                if sidebar_scroll.is_mouse_in_viewport(event.pos):
                    simulation.handle_control_events(sidebar_scroll.translate_event(event))

        simulation.update_controls()
        sidebar_scroll.set_content_height(simulation.calculate_scrollable_content_height())

        draw_application_chrome(screen, settings.window_width, settings.window_height)

        draw_summary_panel(
            screen,
            VisualTheme.control_margin,
            0,
            settings.plot_horizontal_offset - 2 * VisualTheme.control_margin,
            settings.summary_panel_height,
            simulation.total_distance(),
            simulation.total_trips(),
        )

        controls_width = settings.plot_horizontal_offset - 2 * VisualTheme.control_margin
        _draw_scrollable_sidebar(simulation, sidebar_scroll, controls_width)
        sidebar_scroll.blit_to_screen(screen)
        draw_sidebar_footer(screen, settings.sidebar_footer_y)

        draw_delivery_map_header(
            screen,
            settings.plot_horizontal_offset,
            settings.window_width,
            simulation.total_distance(),
        )

        if simulation.depot is not None:
            draw_depot(screen, simulation.depot, settings.depot_half_size)
        if simulation.delivery_points:
            draw_delivery_points(screen, simulation.delivery_points, settings.delivery_point_radius)
        if simulation.simulation_result is not None:
            draw_vehicle_routes(
                screen,
                simulation.simulation_result,
                VisualTheme.vehicle_route_colors,
            )
            draw_vehicle_legend(
                screen,
                simulation.vehicle_count_slider.integer_value,
                VisualTheme.vehicle_route_colors,
                settings.window_width - 160,
                settings.window_height - 120,
            )

        pygame.display.flip()
        clock.tick(settings.frames_per_second)

    pygame.quit()
    sys.exit()
