"""Aplicação Pygame: loop principal da simulação VRP."""

import sys

import pygame

from traveling_salesman_problem.config.application_settings import ApplicationSettings
from traveling_salesman_problem.config.visual_theme import VisualTheme
from traveling_salesman_problem.simulation.simulation_state import SimulationState
from traveling_salesman_problem.visualization.application_layout import (
    draw_application_chrome,
    draw_map_header,
    draw_map_legend,
    draw_route_text_panel,
    draw_section_header,
    draw_sidebar_footer,
)
from traveling_salesman_problem.visualization.convergence_chart import draw_convergence_chart
from traveling_salesman_problem.visualization.map_renderer import (
    draw_animation_cursor,
    draw_blocked_nodes,
    draw_delivery_points,
    draw_depot,
    draw_mesh_edges,
    draw_transit_nodes,
    draw_vehicle_plans,
)
from traveling_salesman_problem.visualization.route_animation import (
    build_animation_polyline,
    point_along_polyline,
)
from traveling_salesman_problem.visualization.route_panel import (
    filter_plans_by_focus,
    format_vehicle_section,
)
from traveling_salesman_problem.visualization.sidebar_scroll import SidebarScrollView

ANIMATION_SPEED = 0.12  # fração do percurso por segundo


def _route_panel_lines(simulation: SimulationState, plans: dict) -> list[str]:
    capacity = simulation.capacity_slider.integer_value
    visible = filter_plans_by_focus(plans, simulation.focus_vehicle_id)
    lines: list[str] = []
    for vehicle_id, plan in sorted(visible.items()):
        lines.extend(format_vehicle_section(vehicle_id, plan, capacity))
    return lines


def _draw_scrollable_sidebar(
    simulation: SimulationState,
    sidebar_scroll: SidebarScrollView,
    route_lines: list[str],
    controls_width: int,
) -> None:
    content_surface = sidebar_scroll.content_surface

    draw_section_header(
        content_surface,
        VisualTheme.control_margin,
        simulation.section_algorithm_y,
        controls_width,
        "Algoritmo",
    )
    simulation.mutation_slider.draw(content_surface)
    simulation.priority_weight_slider.draw(content_surface)
    simulation.two_opt_toggle.draw(content_surface)
    simulation.mesh_toggle.draw(content_surface)

    draw_section_header(
        content_surface,
        VisualTheme.control_margin,
        simulation.section_fleet_y,
        controls_width,
        "Frota",
    )
    simulation.vehicle_count_slider.draw(content_surface)
    simulation.capacity_slider.draw(content_surface)

    draw_section_header(
        content_surface,
        VisualTheme.control_margin,
        simulation.section_quantity_y,
        controls_width,
        "Malha no mapa",
    )
    simulation.transit_count_slider.draw(content_surface)
    simulation.blocked_count_slider.draw(content_surface)

    draw_section_header(
        content_surface,
        VisualTheme.control_margin,
        simulation.section_actions_y,
        controls_width,
        "Ações",
    )
    simulation.regenerate_positions_button.draw(content_surface)
    simulation.hospital_preset_button.draw(content_surface)
    simulation.focus_filter_button.draw(content_surface)

    delivery_section_y = simulation.delivery_order_section_y
    draw_section_header(
        content_surface,
        VisualTheme.control_margin,
        delivery_section_y,
        controls_width,
        "Rotas (D → … → D)",
    )
    draw_route_text_panel(
        content_surface,
        route_lines,
        VisualTheme.control_margin,
        delivery_section_y + 26,
        controls_width,
    )


def run_application(settings=None) -> None:
    if settings is None:
        settings = ApplicationSettings()

    pygame.init()
    screen = pygame.display.set_mode(
        (settings.window_width, settings.window_height),
        pygame.RESIZABLE,
    )
    pygame.display.set_caption("VRP hospitalar · Algoritmo Genético")
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
    animation_progress = 0.0
    last_focus_vehicle_id = simulation.focus_vehicle_id

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
                saved_mutation = simulation.mutation_slider.value
                saved_priority = simulation.priority_weight_slider.value
                saved_vehicles = simulation.vehicle_count_slider.integer_value
                saved_capacity = simulation.capacity_slider.integer_value
                saved_transit = simulation.transit_count_slider.integer_value
                saved_blocked = simulation.blocked_count_slider.integer_value
                saved_two_opt = simulation.two_opt_toggle.is_active
                saved_show_mesh = simulation.mesh_toggle.is_active
                saved_focus = simulation.focus_vehicle_id

                screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                settings = ApplicationSettings(window_width=event.w, window_height=event.h)
                simulation = SimulationState(settings=settings)
                simulation.initialize()
                simulation.mutation_slider.value = saved_mutation
                simulation.priority_weight_slider.value = saved_priority
                simulation.vehicle_count_slider.value = float(saved_vehicles)
                simulation.capacity_slider.value = float(saved_capacity)
                simulation.transit_count_slider.value = float(saved_transit)
                simulation.blocked_count_slider.value = float(max(1, saved_blocked))
                simulation.two_opt_toggle.is_active = saved_two_opt
                simulation.mesh_toggle.is_active = saved_show_mesh
                simulation.show_mesh = saved_show_mesh
                simulation.focus_vehicle_id = saved_focus
                simulation.focus_filter_button.label = simulation.focus_filter_label()
                simulation.rebuild_scenario()
                animation_progress = 0.0
                last_focus_vehicle_id = simulation.focus_vehicle_id

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

        previous_focus = simulation.focus_vehicle_id
        simulation.update_controls_if_changed()
        if simulation.focus_vehicle_id != previous_focus:
            animation_progress = 0.0
            last_focus_vehicle_id = simulation.focus_vehicle_id

        (
            generation_number,
            best_fitness,
            best_distance,
            best_weighted_priority,
            plans,
            histories,
        ) = simulation.run_one_generation()

        if simulation.focus_vehicle_id != last_focus_vehicle_id:
            animation_progress = 0.0
            last_focus_vehicle_id = simulation.focus_vehicle_id

        route_lines = _route_panel_lines(simulation, plans)
        sidebar_scroll.set_content_height(
            simulation.calculate_scrollable_content_height(max(1, len(route_lines)))
        )

        draw_application_chrome(screen, settings.window_width, settings.window_height)
        draw_map_header(
            screen,
            settings.plot_horizontal_offset,
            settings.window_width,
            generation_number,
            best_fitness,
            best_distance,
            best_weighted_priority,
            simulation.priority_weight,
            simulation.mutation_slider.value * 100,
        )
        draw_map_legend(
            screen,
            settings.window_width - 190,
            VisualTheme.map_header_height + 12,
        )
        draw_convergence_chart(
            screen,
            list(range(generation_number)),
            series=histories,
            series_colors=VisualTheme.vehicle_route_colors,
            vertical_axis_label="Fitness por veículo",
        )

        controls_width = settings.plot_horizontal_offset - 2 * VisualTheme.control_margin
        _draw_scrollable_sidebar(simulation, sidebar_scroll, route_lines, controls_width)
        sidebar_scroll.blit_to_screen(screen)
        draw_sidebar_footer(screen, settings.sidebar_footer_y)

        if simulation.show_mesh:
            draw_mesh_edges(screen, simulation.mesh)
            draw_transit_nodes(screen, simulation.mesh)

        draw_vehicle_plans(
            screen,
            simulation.mesh,
            plans,
            focus_vehicle_id=simulation.focus_vehicle_id,
            dim_others=True,
            draw_arrows=True,
        )
        draw_blocked_nodes(screen, simulation.mesh)
        draw_delivery_points(
            screen,
            simulation.deliveries,
            settings.city_node_radius,
        )
        draw_depot(screen, simulation.depot)

        focus_id = simulation.focus_vehicle_id
        if focus_id is not None and focus_id in plans and simulation.mesh is not None:
            polyline = build_animation_polyline(simulation.mesh, plans[focus_id])
            if len(polyline) >= 2:
                dt_seconds = clock.get_time() / 1000.0
                animation_progress = (animation_progress + ANIMATION_SPEED * dt_seconds) % 1.0
                cursor = point_along_polyline(polyline, animation_progress)
                color = VisualTheme.vehicle_route_colors[
                    focus_id % len(VisualTheme.vehicle_route_colors)
                ]
                draw_animation_cursor(screen, cursor, color)

        print(
            f"Geração {generation_number}: "
            f"fitness={round(best_fitness, 2)}  "
            f"dist={round(best_distance, 2)}  "
            f"prior={round(best_weighted_priority, 2)}  "
            f"veículos={simulation.vehicle_count_slider.integer_value}  "
            f"cap={simulation.capacity_slider.integer_value}"
        )

        pygame.display.flip()
        clock.tick(settings.frames_per_second)

    pygame.quit()
    sys.exit()
