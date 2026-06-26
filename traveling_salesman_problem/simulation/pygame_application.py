"""Aplicação Pygame: loop principal da simulação."""

import sys

import pygame

from traveling_salesman_problem.config.application_settings import ApplicationSettings
from traveling_salesman_problem.config.visual_theme import VisualTheme
from traveling_salesman_problem.genetic_algorithm.fitness import build_delivery_visit_order
from traveling_salesman_problem.simulation.simulation_state import SimulationState
from traveling_salesman_problem.visualization.application_layout import (
    draw_application_chrome,
    draw_delivery_order_panel,
    draw_map_header,
    draw_map_legend,
    draw_section_header,
    draw_sidebar_footer,
)
from traveling_salesman_problem.visualization.convergence_chart import draw_convergence_chart
from traveling_salesman_problem.visualization.map_renderer import (
    draw_cities,
    draw_route_paths,
    draw_terrain_features,
)
from traveling_salesman_problem.visualization.sidebar_scroll import SidebarScrollView


def _draw_scrollable_sidebar(
    simulation: SimulationState,
    sidebar_scroll: SidebarScrollView,
    visit_order: list[tuple[int, int, int]],
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

    draw_section_header(
        content_surface,
        VisualTheme.control_margin,
        simulation.section_quantity_y,
        controls_width,
        "Terreno no mapa",
    )
    simulation.tree_count_slider.draw(content_surface)
    simulation.lake_count_slider.draw(content_surface)

    draw_section_header(
        content_surface,
        VisualTheme.control_margin,
        simulation.section_actions_y,
        controls_width,
        "Ações",
    )
    simulation.regenerate_positions_button.draw(content_surface)
    simulation.hospital_preset_button.draw(content_surface)

    draw_section_header(
        content_surface,
        VisualTheme.control_margin,
        simulation.section_terrain_y,
        controls_width,
        "Penalidades de terreno",
    )
    simulation.terrain_control_panel.draw(content_surface)

    delivery_section_y = simulation.delivery_order_section_y
    draw_section_header(
        content_surface,
        VisualTheme.control_margin,
        delivery_section_y,
        controls_width,
        "Ordem de entregas",
    )
    draw_delivery_order_panel(
        content_surface,
        visit_order,
        VisualTheme.control_margin,
        delivery_section_y + 26,
        controls_width,
        draw_title=False,
    )


def run_application(settings=None) -> None:
    if settings is None:
        settings = ApplicationSettings()

    pygame.init()
    screen = pygame.display.set_mode((settings.window_width, settings.window_height))
    pygame.display.set_caption("Problema do Caixeiro Viajante · Algoritmo Genético")
    clock = pygame.time.Clock()

    simulation = SimulationState(settings=settings)
    simulation.initialize()

    sidebar_scroll = SidebarScrollView(
        viewport_top=settings.scroll_viewport_top,
        viewport_height=settings.scroll_viewport_height,
        content_width=settings.plot_horizontal_offset - VisualTheme.scrollbar_width - 8,
    )

    is_running = True
    while is_running:
        for event in pygame.event.get():
            if sidebar_scroll.handle_event(event):
                continue

            if event.type == pygame.QUIT:
                is_running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    is_running = False
                else:
                    simulation.handle_control_events(event)
            elif event.type in (
                pygame.MOUSEBUTTONDOWN,
                pygame.MOUSEBUTTONUP,
                pygame.MOUSEMOTION,
            ):
                if sidebar_scroll.is_mouse_in_viewport(event.pos):
                    simulation.handle_control_events(sidebar_scroll.translate_event(event))

        simulation.update_terrain_counts_if_changed()

        (
            generation_number,
            best_fitness,
            best_route,
            second_best_route,
            best_distance,
            best_weighted_priority,
        ) = simulation.run_one_generation()

        visit_order = build_delivery_visit_order(
            best_route,
            simulation.city_coordinates,
            simulation.city_priorities,
        )
        sidebar_scroll.set_content_height(
            simulation.calculate_scrollable_content_height(len(visit_order))
        )

        vertical_axis_label = (
            "Fitness (custo total)"
            if simulation.priority_weight > 0
            else "Distância (pixels)"
        )

        draw_application_chrome(screen, settings.window_width, settings.window_height)

        draw_convergence_chart(
            screen,
            list(range(len(simulation.best_fitness_history))),
            simulation.best_fitness_history,
            vertical_axis_label=vertical_axis_label,
        )

        controls_width = settings.plot_horizontal_offset - 2 * VisualTheme.control_margin
        _draw_scrollable_sidebar(simulation, sidebar_scroll, visit_order, controls_width)
        sidebar_scroll.blit_to_screen(screen)
        draw_sidebar_footer(screen, settings.sidebar_footer_y)

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
            simulation.terrain_control_panel.use_terrain_penalties,
        )
        draw_map_legend(
            screen,
            settings.window_width - 190,
            VisualTheme.map_header_height + 12,
        )

        draw_terrain_features(screen, simulation.terrain_features)
        draw_cities(
            screen,
            simulation.city_coordinates,
            simulation.city_priorities,
            settings.city_node_radius,
        )
        draw_route_paths(
            screen,
            best_route,
            VisualTheme.route_best,
            line_width=3,
            draw_glow=True,
        )
        draw_route_paths(
            screen,
            second_best_route,
            VisualTheme.route_second_best,
            line_width=1,
        )

        print(
            f"Geração {generation_number}: "
            f"fitness={round(best_fitness, 2)}  "
            f"dist={round(best_distance, 2)}  "
            f"prior={round(best_weighted_priority, 2)}  "
            f"peso={round(simulation.priority_weight)}"
        )

        pygame.display.flip()
        clock.tick(settings.frames_per_second)

    pygame.quit()
    sys.exit()
