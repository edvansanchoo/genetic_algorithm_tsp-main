"""Estado mutável compartilhado durante a simulação."""

import itertools
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import pygame

from traveling_salesman_problem.config.application_settings import ApplicationSettings
from traveling_salesman_problem.config.visual_theme import VisualTheme
from traveling_salesman_problem.genetic_algorithm.fitness import (
    calculate_route_fitness,
    decompose_route_fitness,
)
from traveling_salesman_problem.genetic_algorithm.population import (
    generate_random_population,
    sort_population_by_fitness,
)
from traveling_salesman_problem.genetic_algorithm.predefined_problems import (
    get_scenario_coordinates,
)
from traveling_salesman_problem.genetic_algorithm.selection import evolve_next_generation
from traveling_salesman_problem.obstacles.models import Obstacle
from traveling_salesman_problem.obstacles.placement import (
    generate_terrain_features_by_type,
    reshuffle_terrain_feature_positions,
    sync_terrain_feature_counts,
)
from traveling_salesman_problem.problem.city_generator import (
    generate_random_city_coordinate,
    generate_random_priorities,
    reshuffle_cities_and_population,
)
from traveling_salesman_problem.problem.priority_presets import apply_hospital_priority_preset
from traveling_salesman_problem.visualization.widgets import (
    ActionButton,
    IntegerSlider,
    MutationSlider,
    ScenarioSelector,
    TerrainControlPanel,
    ToggleButton,
)

CityCoordinate = Tuple[int, int]
Route = List[CityCoordinate]


@dataclass
class SimulationState:
    settings: ApplicationSettings = field(default_factory=ApplicationSettings)

    city_coordinates: List[CityCoordinate] = field(default_factory=list)
    city_priorities: List[int] = field(default_factory=list)
    population: List[Route] = field(default_factory=list)
    terrain_features: List[Obstacle] = field(default_factory=list)

    best_fitness_history: List[float] = field(default_factory=list)
    best_route_history: List[Route] = field(default_factory=list)

    generation_counter: itertools.count = field(default_factory=lambda: itertools.count(start=1))

    mutation_slider: Optional[MutationSlider] = None
    priority_weight_slider: Optional[MutationSlider] = None
    tree_count_slider: Optional[IntegerSlider] = None
    lake_count_slider: Optional[IntegerSlider] = None
    regenerate_positions_button: Optional[ActionButton] = None
    hospital_preset_button: Optional[ActionButton] = None
    terrain_control_panel: Optional[TerrainControlPanel] = None
    two_opt_toggle: Optional[ToggleButton] = None
    scenario_selector: Optional[ScenarioSelector] = None

    active_scenario_id: str = "random"
    effective_number_of_cities: int = 0

    last_tree_count: int = 0
    last_lake_count: int = 0

    section_algorithm_y: int = 0
    section_scenario_y: int = 0
    section_quantity_y: int = 0
    section_actions_y: int = 0
    section_terrain_y: int = 0

    @property
    def obstacles(self) -> List[Obstacle]:
        return self.terrain_features

    @property
    def priority_weight(self) -> float:
        return self.priority_weight_slider.value

    @property
    def delivery_order_section_y(self) -> int:
        terrain_panel_y = self.section_terrain_y + 26
        return terrain_panel_y + self.terrain_control_panel.height + 12

    def calculate_scrollable_content_height(self, delivery_row_count: int) -> int:
        delivery_panel_y = self.delivery_order_section_y + 26
        delivery_panel_height = 18 + 6 + delivery_row_count * 16 + 20
        return delivery_panel_y + delivery_panel_height

    def reset_simulation_history(self) -> None:
        self.best_fitness_history.clear()
        self.best_route_history.clear()
        self.generation_counter = itertools.count(start=1)

    def load_cities_for_scenario(self, scenario_id: str) -> List[CityCoordinate]:
        fixed_coordinates = get_scenario_coordinates(scenario_id)
        if fixed_coordinates is not None:
            return list(fixed_coordinates)
        settings = self.settings
        city_count = settings.number_of_cities
        return [
            generate_random_city_coordinate(
                settings.window_width,
                settings.window_height,
                settings.plot_horizontal_offset,
                settings.city_node_radius,
                self.terrain_features,
            )
            for _ in range(city_count)
        ]

    def apply_scenario(self, scenario_id: str) -> None:
        settings = self.settings
        self.active_scenario_id = scenario_id
        if self.scenario_selector is not None:
            self.scenario_selector.set_active(scenario_id)
        self.city_coordinates[:] = self.load_cities_for_scenario(scenario_id)
        self.effective_number_of_cities = len(self.city_coordinates)
        self.city_priorities[:] = generate_random_priorities(self.effective_number_of_cities)
        self.population[:] = generate_random_population(
            self.city_coordinates,
            settings.population_size,
        )
        self.reset_simulation_history()

    def initialize(self) -> None:
        settings = self.settings

        self.terrain_features = generate_terrain_features_by_type(
            settings.initial_tree_count,
            settings.initial_lake_count,
            settings.map_minimum_x,
            settings.map_minimum_y,
            settings.map_maximum_x,
            settings.map_maximum_y,
            enabled=False,
        )

        self.city_coordinates = [
            generate_random_city_coordinate(
                settings.window_width,
                settings.window_height,
                settings.plot_horizontal_offset,
                settings.city_node_radius,
                self.terrain_features,
            )
            for _ in range(settings.number_of_cities)
        ]

        self.city_priorities = generate_random_priorities(settings.number_of_cities)

        self.population = generate_random_population(
            self.city_coordinates,
            settings.population_size,
        )

        self.effective_number_of_cities = len(self.city_coordinates)

        self._create_control_widgets()
        self.last_tree_count = settings.initial_tree_count
        self.last_lake_count = settings.initial_lake_count

    def _create_control_widgets(self) -> None:
        settings = self.settings
        controls_width = settings.plot_horizontal_offset - 2 * VisualTheme.control_margin
        half_width = (controls_width - VisualTheme.control_gap) // 2
        saved_two_opt_active = (
            self.two_opt_toggle.is_active if self.two_opt_toggle is not None else False
        )

        self.section_algorithm_y = 0
        mutation_y = self.section_algorithm_y + 26
        priority_weight_y = mutation_y + settings.mutation_slider_height + 12
        two_opt_y = priority_weight_y + settings.mutation_slider_height + 12
        self.section_scenario_y = two_opt_y + 32 + 12
        scenario_selector_y = self.section_scenario_y + 26

        self.two_opt_toggle = ToggleButton(
            position_x=VisualTheme.control_margin,
            position_y=two_opt_y,
            width=controls_width,
            height=32,
            label="Refinamento 2-opt",
            is_active=saved_two_opt_active,
        )

        self.scenario_selector = ScenarioSelector(
            position_x=VisualTheme.control_margin,
            position_y=scenario_selector_y,
            width=controls_width,
            viewport_height=settings.scenario_selector_viewport_height,
            active_scenario_id=self.active_scenario_id,
        )

        self.section_quantity_y = scenario_selector_y + settings.scenario_selector_viewport_height + 12
        terrain_count_y = self.section_quantity_y + 26
        self.section_actions_y = terrain_count_y + settings.count_slider_height + 12
        regenerate_y = self.section_actions_y + 26
        hospital_preset_y = regenerate_y + settings.regenerate_button_height + VisualTheme.control_gap
        self.section_terrain_y = hospital_preset_y + settings.regenerate_button_height + 12
        terrain_panel_y = self.section_terrain_y + 26

        self.mutation_slider = MutationSlider(
            position_x=VisualTheme.control_margin,
            position_y=mutation_y,
            width=controls_width,
            height=settings.mutation_slider_height,
            value=settings.initial_mutation_probability,
            label="Taxa de mutação",
            value_suffix="%",
        )

        self.priority_weight_slider = MutationSlider(
            position_x=VisualTheme.control_margin,
            position_y=priority_weight_y,
            width=controls_width,
            height=settings.mutation_slider_height,
            value=settings.initial_priority_weight,
            minimum_value=0.0,
            maximum_value=100.0,
            label="Peso da prioridade",
            value_suffix="",
        )

        self.tree_count_slider = IntegerSlider(
            position_x=VisualTheme.control_margin,
            position_y=terrain_count_y,
            width=half_width,
            height=settings.count_slider_height,
            value=settings.initial_tree_count,
            minimum_value=0,
            maximum_value=settings.maximum_terrain_features_per_type,
            label="Árvores",
        )

        self.lake_count_slider = IntegerSlider(
            position_x=VisualTheme.control_margin + half_width + VisualTheme.control_gap,
            position_y=terrain_count_y,
            width=half_width,
            height=settings.count_slider_height,
            value=settings.initial_lake_count,
            minimum_value=0,
            maximum_value=settings.maximum_terrain_features_per_type,
            label="Lagos",
        )

        self.regenerate_positions_button = ActionButton(
            position_x=VisualTheme.control_margin,
            position_y=regenerate_y,
            width=controls_width,
            height=settings.regenerate_button_height,
            label="Sortear posições",
            subtitle="Árvores, lagos e cidades",
        )

        self.hospital_preset_button = ActionButton(
            position_x=VisualTheme.control_margin,
            position_y=hospital_preset_y,
            width=controls_width,
            height=settings.regenerate_button_height,
            label="Cenário hospitalar",
            subtitle="Prioridades críticas fixas",
        )

        self.terrain_control_panel = TerrainControlPanel(
            position_x=VisualTheme.control_margin,
            position_y=terrain_panel_y,
            width=controls_width,
            terrain_features=self.terrain_features,
        )

    def synchronize_terrain_from_sliders(self) -> None:
        settings = self.settings
        sync_terrain_feature_counts(
            self.terrain_features,
            self.tree_count_slider.integer_value,
            self.lake_count_slider.integer_value,
            settings.map_minimum_x,
            settings.map_minimum_y,
            settings.map_maximum_x,
            settings.map_maximum_y,
        )
        self.terrain_control_panel.tree_penalty_slider.apply_penalty_to_terrain()
        self.terrain_control_panel.lake_penalty_slider.apply_penalty_to_terrain()
        self.terrain_control_panel.rebuild(self.terrain_features)

    def apply_hospital_preset(self) -> None:
        self.city_priorities[:] = apply_hospital_priority_preset(len(self.city_coordinates))

    def shuffle_terrain_and_cities(self) -> None:
        if self.active_scenario_id != "random":
            self.apply_scenario("random")
        settings = self.settings
        reshuffle_terrain_feature_positions(
            self.terrain_features,
            settings.map_minimum_x,
            settings.map_minimum_y,
            settings.map_maximum_x,
            settings.map_maximum_y,
        )
        self.terrain_control_panel.rebuild(self.terrain_features)
        reshuffle_cities_and_population(
            self.city_coordinates,
            self.city_priorities,
            self.effective_number_of_cities,
            settings.population_size,
            self.population,
            self.best_fitness_history,
            self.best_route_history,
            settings.window_width,
            settings.window_height,
            settings.plot_horizontal_offset,
            settings.city_node_radius,
            self.terrain_features,
        )

    def handle_control_events(self, event: pygame.event.Event) -> None:
        self.mutation_slider.handle_event(event)
        self.priority_weight_slider.handle_event(event)
        self.two_opt_toggle.handle_event(event)
        self.scenario_selector.handle_event(event)
        self.tree_count_slider.handle_event(event)
        self.lake_count_slider.handle_event(event)
        self.regenerate_positions_button.handle_event(event)
        self.hospital_preset_button.handle_event(event)
        self.terrain_control_panel.handle_event(event)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_o:
                toggle = self.terrain_control_panel.global_penalty_toggle
                toggle.is_active = not toggle.is_active
            elif event.key == pygame.K_p:
                self.apply_hospital_preset()

    def update_terrain_counts_if_changed(self) -> None:
        if self.scenario_selector.was_changed:
            self.scenario_selector.was_changed = False
            self.apply_scenario(self.scenario_selector.active_scenario_id)
            return

        if self.hospital_preset_button.was_pressed:
            self.hospital_preset_button.was_pressed = False
            self.apply_hospital_preset()
            return

        if self.regenerate_positions_button.was_pressed:
            self.regenerate_positions_button.was_pressed = False
            self.shuffle_terrain_and_cities()
            self.last_tree_count = self.tree_count_slider.integer_value
            self.last_lake_count = self.lake_count_slider.integer_value
            return

        if self.tree_count_slider.is_dragging or self.lake_count_slider.is_dragging:
            return

        current_trees = self.tree_count_slider.integer_value
        current_lakes = self.lake_count_slider.integer_value
        if current_trees != self.last_tree_count or current_lakes != self.last_lake_count:
            self.synchronize_terrain_from_sliders()
            self.last_tree_count = current_trees
            self.last_lake_count = current_lakes

    def run_one_generation(self) -> tuple[int, float, Route, Route, float, float]:
        settings = self.settings
        use_penalties = self.terrain_control_panel.use_terrain_penalties
        mutation_probability = self.mutation_slider.value
        priority_weight = self.priority_weight

        population_fitness = [
            calculate_route_fitness(
                route,
                self.terrain_features,
                use_penalties,
                self.city_coordinates,
                self.city_priorities,
                priority_weight,
            )
            for route in self.population
        ]

        self.population, population_fitness = sort_population_by_fitness(
            self.population,
            population_fitness,
        )

        best_route = self.population[0]
        best_fitness, best_distance, best_weighted_priority = decompose_route_fitness(
            best_route,
            self.terrain_features,
            use_penalties,
            self.city_coordinates,
            self.city_priorities,
            priority_weight,
        )
        second_best_route = self.population[1]

        self.best_fitness_history.append(best_fitness)
        self.best_route_history.append(best_route)

        self.population = evolve_next_generation(
            self.population,
            population_fitness,
            settings.population_size,
            mutation_probability,
            mutation_type="adjacent",
            n_elite=3,
            use_2opt=self.two_opt_toggle.is_active,
        )

        generation_number = next(self.generation_counter)
        return (
            generation_number,
            best_fitness,
            best_route,
            second_best_route,
            best_distance,
            best_weighted_priority,
        )
