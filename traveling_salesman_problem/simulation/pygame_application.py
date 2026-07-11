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
    draw_runner_up_plan,
)
from traveling_salesman_problem.visualization.route_animation import (
    TripAnimationState,
    advance_trip_animation,
)
from traveling_salesman_problem.visualization.route_panel import (
    build_route_panel_rows,
    filter_plans_by_focus,
    hit_test_route_panel,
)
from traveling_salesman_problem.visualization.sidebar_scroll import SidebarScrollView

ANIMATION_SPEED = 0.12


def _route_panel_data(simulation: SimulationState, plans: dict) -> tuple[list[str], list]:
    capacity = simulation.capacity_slider.integer_value
    visible = filter_plans_by_focus(plans, simulation.focus_vehicle_id)
    rows = build_route_panel_rows(visible, capacity)
    return [row.text for row in rows], rows


def _draw_scrollable_sidebar(
    simulation: SimulationState,
    sidebar_scroll: SidebarScrollView,
    route_lines: list[str],
    route_rows: list,
    active_trip_index: int | None,
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
        row_vehicle_ids=[row.vehicle_id for row in route_rows],
        row_trip_indices=[row.trip_index for row in route_rows],
        row_is_header=[row.is_vehicle_header for row in route_rows],
        focus_vehicle_id=simulation.focus_vehicle_id,
        focus_trip_index=simulation.focus_trip_index,
        active_trip_index=active_trip_index,
    )


def _reset_trip_animation(
    trip_animation: TripAnimationState,
    simulation: SimulationState,
) -> None:
    start_trip = simulation.focus_trip_index or 0
    trip_animation.reset(start_trip)


def _try_handle_route_panel_click(
    simulation: SimulationState,
    event: pygame.event.Event,
    route_rows: list,
    controls_width: int,
    trip_animation: TripAnimationState,
) -> bool:
    if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
        return False
    panel_y = simulation.delivery_order_section_y + 26
    hit = hit_test_route_panel(
        route_rows,
        event.pos[0],
        event.pos[1],
        VisualTheme.control_margin,
        panel_y,
        controls_width,
    )
    if hit is None:
        return False
    kind, vehicle_id, trip_index = hit
    simulation.handle_route_panel_selection(vehicle_id, kind, trip_index)
    _reset_trip_animation(trip_animation, simulation)
    return True


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
    trip_animation = TripAnimationState()
    last_focus_vehicle_id = simulation.focus_vehicle_id
    last_focus_trip_index = simulation.focus_trip_index
    active_trip_index: int | None = None
    route_rows: list = []

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
                saved_two_opt = simulation.two_opt_toggle.is_active
                saved_show_mesh = simulation.mesh_toggle.is_active
                saved_focus = simulation.focus_vehicle_id
                saved_focus_trip = simulation.focus_trip_index

                screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                settings = ApplicationSettings(window_width=event.w, window_height=event.h)
                simulation = SimulationState(settings=settings)
                simulation.initialize()
                simulation.mutation_slider.value = saved_mutation
                simulation.priority_weight_slider.value = saved_priority
                simulation.vehicle_count_slider.value = float(saved_vehicles)
                simulation.capacity_slider.value = float(saved_capacity)
                simulation.transit_count_slider.value = float(saved_transit)
                simulation.two_opt_toggle.is_active = saved_two_opt
                simulation.mesh_toggle.is_active = saved_show_mesh
                simulation.show_mesh = saved_show_mesh
                simulation.focus_vehicle_id = saved_focus
                simulation.focus_trip_index = saved_focus_trip
                simulation.focus_filter_button.label = simulation.focus_filter_label()
                simulation.rebuild_scenario()
                _reset_trip_animation(trip_animation, simulation)
                last_focus_vehicle_id = simulation.focus_vehicle_id
                last_focus_trip_index = simulation.focus_trip_index

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
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                controls_width = settings.plot_horizontal_offset - 2 * VisualTheme.control_margin
                if sidebar_scroll.is_mouse_in_viewport(event.pos):
                    translated = sidebar_scroll.translate_event(event)
                    if _try_handle_route_panel_click(
                        simulation,
                        translated,
                        route_rows,
                        controls_width,
                        trip_animation,
                    ):
                        last_focus_vehicle_id = simulation.focus_vehicle_id
                        last_focus_trip_index = simulation.focus_trip_index
                    else:
                        simulation.handle_control_events(translated)
                elif event.pos[0] >= settings.plot_horizontal_offset:
                    simulation.toggle_blocked_at(event.pos)
            elif event.type in (
                pygame.MOUSEBUTTONUP,
                pygame.MOUSEMOTION,
            ):
                if sidebar_scroll.is_mouse_in_viewport(event.pos):
                    simulation.handle_control_events(sidebar_scroll.translate_event(event))

        previous_focus = simulation.focus_vehicle_id
        previous_trip = simulation.focus_trip_index
        simulation.update_controls_if_changed()
        if (
            simulation.focus_vehicle_id != previous_focus
            or simulation.focus_trip_index != previous_trip
        ):
            _reset_trip_animation(trip_animation, simulation)
            last_focus_vehicle_id = simulation.focus_vehicle_id
            last_focus_trip_index = simulation.focus_trip_index

        (
            generation_number,
            best_fitness,
            best_distance,
            best_weighted_priority,
            plans,
            runner_up_plans,
            histories,
        ) = simulation.run_one_generation()

        if (
            simulation.focus_vehicle_id != last_focus_vehicle_id
            or simulation.focus_trip_index != last_focus_trip_index
        ):
            _reset_trip_animation(trip_animation, simulation)
            last_focus_vehicle_id = simulation.focus_vehicle_id
            last_focus_trip_index = simulation.focus_trip_index

        route_lines, route_rows = _route_panel_data(simulation, plans)
        sidebar_scroll.set_content_height(
            simulation.calculate_scrollable_content_height(max(1, len(route_lines)))
        )

        focus_id = simulation.focus_vehicle_id
        locked_trip = simulation.focus_trip_index
        trip_auto_cycle = focus_id is not None and locked_trip is None
        animation_cursor = None

        if focus_id is not None and focus_id in plans and simulation.mesh is not None:
            dt_seconds = clock.get_time() / 1000.0
            animation_cursor, active_trip_index = advance_trip_animation(
                trip_animation,
                simulation.mesh,
                plans[focus_id],
                dt_seconds,
                locked_trip_index=locked_trip,
                speed=ANIMATION_SPEED,
            )
        else:
            active_trip_index = None

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
            settings.window_width - 220,
            VisualTheme.map_header_height + 12,
            show_mesh=simulation.show_mesh,
            vehicle_count=simulation.vehicle_count_slider.integer_value,
            focus_vehicle_id=focus_id,
            has_runner_up=(focus_id is not None and focus_id in runner_up_plans),
            focus_trip_index=locked_trip,
            trip_auto_cycle=trip_auto_cycle,
        )
        draw_convergence_chart(
            screen,
            list(range(generation_number)),
            series=histories,
            series_colors=VisualTheme.vehicle_route_colors,
            vertical_axis_label="Fitness por veículo",
        )

        controls_width = settings.plot_horizontal_offset - 2 * VisualTheme.control_margin
        _draw_scrollable_sidebar(
            simulation,
            sidebar_scroll,
            route_lines,
            route_rows,
            active_trip_index,
            controls_width,
        )
        sidebar_scroll.blit_to_screen(screen)
        draw_sidebar_footer(screen, settings.sidebar_footer_y)

        draw_transit_nodes(screen, simulation.mesh)
        if simulation.show_mesh:
            draw_mesh_edges(screen, simulation.mesh)

        display_trip_index = locked_trip if locked_trip is not None else active_trip_index
        if focus_id is not None and focus_id in runner_up_plans:
            draw_runner_up_plan(
                screen,
                simulation.mesh,
                runner_up_plans[focus_id],
                trip_index=display_trip_index,
            )

        draw_vehicle_plans(
            screen,
            simulation.mesh,
            plans,
            focus_vehicle_id=focus_id,
            focus_trip_index=locked_trip,
            active_trip_index=active_trip_index,
            dim_others=True,
            draw_arrows=True,
        )
        draw_delivery_points(
            screen,
            simulation.deliveries,
            settings.city_node_radius,
        )
        draw_depot(screen, simulation.depot)
        draw_blocked_nodes(screen, simulation.mesh)

        if animation_cursor is not None and focus_id is not None:
            color = VisualTheme.vehicle_route_colors[
                focus_id % len(VisualTheme.vehicle_route_colors)
            ]
            draw_animation_cursor(screen, animation_cursor, color)

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
