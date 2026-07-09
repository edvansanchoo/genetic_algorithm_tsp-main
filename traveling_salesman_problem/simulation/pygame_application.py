"""Aplicação Pygame: loop principal da simulação de entregas."""

import sys

import pygame

from traveling_salesman_problem.config.application_settings import ApplicationSettings
from traveling_salesman_problem.config.visual_theme import VisualTheme
from traveling_salesman_problem.simulation.evolution_throttle import compute_generations_for_frame
from traveling_salesman_problem.simulation.simulation_state import SimulationState
from traveling_salesman_problem.visualization.application_layout import (
    draw_application_chrome,
    draw_delivery_map_header,
    draw_results_panel,
    draw_section_header,
    draw_sidebar_footer,
    draw_trip_detail_panel,
)
from traveling_salesman_problem.visualization.convergence_chart import draw_convergence_chart
from traveling_salesman_problem.visualization.map_renderer import (
    draw_delivery_points,
    draw_depot,
    draw_road_network,
    draw_selected_routes,
    draw_transit_nodes,
    draw_vehicle_evolution_routes,
    draw_vehicle_legend,
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
    simulation.transit_count_slider.draw(content_surface)
    simulation.connection_radius_slider.draw(content_surface)
    simulation.mutation_slider.draw(content_surface)

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

    results_y = simulation.section_results_y
    active_result = simulation.active_result()
    if active_result is not None:
        draw_section_header(
            content_surface,
            VisualTheme.control_margin,
            simulation.section_visualization_y,
            controls_width,
            "Visualização",
        )
        simulation.trip_selector.draw(content_surface)
        detail_y = simulation.section_visualization_y + 26 + simulation.trip_selector.height + 8
        detail_bottom = draw_trip_detail_panel(
            content_surface,
            active_result,
            simulation.trip_selector.active_vehicle_id,
            simulation.trip_selector.active_trip_index,
            simulation.trip_selector.view_mode,
            VisualTheme.control_margin,
            detail_y,
            controls_width,
        )
        results_y = detail_bottom + 12

    draw_section_header(
        content_surface,
        VisualTheme.control_margin,
        results_y,
        controls_width,
        "Resultado",
    )
    draw_results_panel(
        content_surface,
        simulation.result_lines,
        VisualTheme.control_margin,
        results_y + 26,
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
    pygame.display.set_caption("Simulador de Entregas · AG Multi-Veículo")
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
    accumulated_evolution_time = 0.0

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
                saved_transit_count = simulation.transit_count_slider.integer_value
                saved_connection_radius = simulation.connection_radius_slider.integer_value
                saved_mutation = simulation.mutation_slider.value

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
                simulation.transit_count_slider.value = float(saved_transit_count)
                simulation.connection_radius_slider.value = float(saved_connection_radius)
                simulation.mutation_slider.value = saved_mutation

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

        delta_seconds = clock.get_time() / 1000.0
        if simulation.is_evolution_running:
            gen_count, accumulated_evolution_time = compute_generations_for_frame(
                delta_seconds,
                settings.generations_per_second,
                accumulated_evolution_time,
            )
            for _ in range(gen_count):
                simulation.run_one_generation()
        else:
            accumulated_evolution_time = 0.0

        sidebar_scroll.set_content_height(simulation.calculate_scrollable_content_height())

        draw_application_chrome(screen, settings.window_width, settings.window_height)

        if simulation.vehicle_best_distance_history:
            vehicle_ids = sorted(simulation.vehicle_best_distance_history)
            series = [simulation.vehicle_best_distance_history[vehicle_id] for vehicle_id in vehicle_ids]
            labels = [f"V{vehicle_id}" for vehicle_id in vehicle_ids]
            max_len = max(len(values) for values in series)
            highlight_index = None
            if simulation.trip_selector is not None:
                highlight_index = simulation.trip_selector.active_vehicle_id - 1
            draw_convergence_chart(
                screen,
                list(range(max_len)),
                series,
                vertical_axis_label="Distância (px)",
                series_colors=VisualTheme.vehicle_route_colors,
                series_labels=labels,
                highlight_index=highlight_index,
            )

        controls_width = settings.plot_horizontal_offset - 2 * VisualTheme.control_margin
        _draw_scrollable_sidebar(simulation, sidebar_scroll, controls_width)
        sidebar_scroll.blit_to_screen(screen)
        draw_sidebar_footer(screen, settings.sidebar_footer_y)

        genetic = simulation.active_vehicle_genetic_state()
        draw_delivery_map_header(
            screen,
            settings.plot_horizontal_offset,
            settings.window_width,
            simulation.total_distance(),
            generation_number=simulation.generation_counter if simulation.is_evolution_running else None,
            active_vehicle_id=(
                simulation.trip_selector.active_vehicle_id
                if simulation.is_evolution_running and simulation.trip_selector is not None
                else None
            ),
            best_distance=genetic.best_distance if genetic is not None else None,
            second_best_distance=genetic.second_best_distance if genetic is not None else None,
        )

        if simulation.road_network is not None:
            draw_road_network(screen, simulation.road_network)
        if simulation.transit_nodes:
            draw_transit_nodes(screen, simulation.transit_nodes)
        if simulation.depot is not None:
            draw_depot(screen, simulation.depot, settings.depot_half_size)
        if simulation.delivery_points:
            draw_delivery_points(screen, simulation.delivery_points, settings.delivery_point_radius)

        active_result = simulation.active_result()
        genetic = simulation.active_vehicle_genetic_state()
        if (
            simulation.is_evolution_running
            and genetic is not None
            and simulation.road_network is not None
            and genetic.best_trips
        ):
            color = VisualTheme.vehicle_route_colors[
                (simulation.trip_selector.active_vehicle_id - 1) % len(VisualTheme.vehicle_route_colors)
            ]
            draw_vehicle_evolution_routes(
                screen,
                simulation.road_network,
                genetic.best_trips,
                genetic.second_best_trips,
                color,
            )
        elif active_result is not None:
            draw_selected_routes(
                screen,
                active_result,
                simulation.trip_selector.active_vehicle_id,
                simulation.trip_selector.active_trip_index,
                simulation.trip_selector.view_mode,
                VisualTheme.vehicle_route_colors,
                VisualTheme.vehicle_line_styles,
            )
        if active_result is not None:
            draw_vehicle_legend(
                screen,
                simulation.vehicle_count_slider.integer_value,
                VisualTheme.vehicle_route_colors,
                VisualTheme.vehicle_line_styles,
                settings.window_width - 180,
                settings.window_height - 120,
            )

        pygame.display.flip()
        clock.tick(settings.frames_per_second)

    pygame.quit()
    sys.exit()
