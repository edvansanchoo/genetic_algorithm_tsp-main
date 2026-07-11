"""Estado mutável da simulação VRP (Camada 2)."""

from __future__ import annotations

import itertools
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import pygame

from traveling_salesman_problem.config.application_settings import ApplicationSettings
from traveling_salesman_problem.config.visual_theme import VisualTheme
from traveling_salesman_problem.problem.city_generator import (
    generate_random_city_coordinate,
    generate_random_priorities,
)
from traveling_salesman_problem.problem.delivery_mesh import DeliveryMesh, build_vrp_mesh
from traveling_salesman_problem.problem.priority_presets import apply_hospital_priority_preset
from traveling_salesman_problem.problem.vrp_assignment import (
    assign_deliveries_greedy,
    split_into_tokens,
    total_delivery_demand,
)
from traveling_salesman_problem.problem.vrp_models import Coordinate, DeliveryPoint
from traveling_salesman_problem.simulation.vehicle_genetic import (
    VehicleGeneticState,
    initialize_vehicle_genetic,
    run_vehicle_generation,
)
from traveling_salesman_problem.visualization.widgets import (
    ActionButton,
    IntegerSlider,
    MutationSlider,
    ToggleButton,
)

POINT_IDS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


@dataclass
class SimulationState:
    settings: ApplicationSettings = field(default_factory=ApplicationSettings)

    depot: Optional[Coordinate] = None
    deliveries: List[DeliveryPoint] = field(default_factory=list)
    mesh: Optional[DeliveryMesh] = None
    assignment: Dict[int, List[DeliveryPoint]] = field(default_factory=dict)
    vehicle_states: Dict[int, VehicleGeneticState] = field(default_factory=dict)

    generation_counter: itertools.count = field(
        default_factory=lambda: itertools.count(start=1)
    )

    mutation_slider: Optional[MutationSlider] = None
    priority_weight_slider: Optional[MutationSlider] = None
    vehicle_count_slider: Optional[IntegerSlider] = None
    capacity_slider: Optional[IntegerSlider] = None
    transit_count_slider: Optional[IntegerSlider] = None
    blocked_count_slider: Optional[IntegerSlider] = None
    regenerate_positions_button: Optional[ActionButton] = None
    hospital_preset_button: Optional[ActionButton] = None
    focus_filter_button: Optional[ActionButton] = None
    two_opt_toggle: Optional[ToggleButton] = None
    mesh_toggle: Optional[ToggleButton] = None

    focus_vehicle_id: Optional[int] = None
    show_mesh: bool = True

    last_vehicle_count: int = 0
    last_capacity: int = 0
    last_transit_count: int = 0
    last_blocked_count: int = 0

    section_algorithm_y: int = 0
    section_fleet_y: int = 0
    section_quantity_y: int = 0
    section_actions_y: int = 0

    @property
    def priority_weight(self) -> float:
        return self.priority_weight_slider.value

    @property
    def delivery_order_section_y(self) -> int:
        return (
            self.section_actions_y
            + 26
            + self.settings.regenerate_button_height * 3
            + VisualTheme.control_gap * 2
            + 32
            + 12
            + 12
        )

    def calculate_scrollable_content_height(self, route_line_count: int) -> int:
        route_panel_y = self.delivery_order_section_y + 26
        route_panel_height = 8 + max(1, route_line_count) * 16 + 20
        return route_panel_y + route_panel_height

    def focus_filter_label(self) -> str:
        if self.focus_vehicle_id is None:
            return "Filtro: Todos"
        return f"Filtro: V{self.focus_vehicle_id + 1}"

    def cycle_focus_vehicle(self) -> None:
        ids = sorted(self.vehicle_states.keys())
        if not ids:
            self.focus_vehicle_id = None
        elif self.focus_vehicle_id is None:
            self.focus_vehicle_id = ids[0]
        else:
            try:
                index = ids.index(self.focus_vehicle_id)
            except ValueError:
                self.focus_vehicle_id = ids[0]
            else:
                if index + 1 >= len(ids):
                    self.focus_vehicle_id = None
                else:
                    self.focus_vehicle_id = ids[index + 1]
        if self.focus_filter_button is not None:
            self.focus_filter_button.label = self.focus_filter_label()

    def _sync_focus_after_rebuild(self) -> None:
        if (
            self.focus_vehicle_id is not None
            and self.focus_vehicle_id not in self.vehicle_states
        ):
            self.focus_vehicle_id = None
        if self.focus_filter_button is not None:
            self.focus_filter_button.label = self.focus_filter_label()
        if self.mesh_toggle is not None:
            self.show_mesh = self.mesh_toggle.is_active


    def map_bounds(self) -> tuple[float, float, float, float]:
        settings = self.settings
        return (
            float(settings.map_minimum_x),
            float(settings.map_minimum_y),
            float(settings.map_maximum_x),
            float(settings.map_maximum_y),
        )

    def _random_map_point(self) -> Coordinate:
        settings = self.settings
        point = generate_random_city_coordinate(
            settings.window_width,
            settings.window_height,
            settings.plot_horizontal_offset,
            settings.city_node_radius,
            [],
        )
        return (float(point[0]), float(point[1]))

    def _generate_deliveries(self) -> List[DeliveryPoint]:
        settings = self.settings
        count = settings.number_of_deliveries
        priorities = generate_random_priorities(count)
        deliveries: List[DeliveryPoint] = []
        for index in range(count):
            point_id = POINT_IDS[index] if index < len(POINT_IDS) else f"P{index}"
            deliveries.append(
                DeliveryPoint(
                    id=point_id,
                    coordinate=self._random_map_point(),
                    priority=priorities[index],
                    demand=random.randint(settings.min_demand, settings.max_demand),
                )
            )
        return deliveries

    def rebuild_scenario(self) -> None:
        settings = self.settings
        vehicle_count = (
            self.vehicle_count_slider.integer_value
            if self.vehicle_count_slider is not None
            else settings.initial_vehicle_count
        )
        capacity = (
            self.capacity_slider.integer_value
            if self.capacity_slider is not None
            else settings.initial_capacity
        )
        transit_count = max(
            1,
            self.transit_count_slider.integer_value
            if self.transit_count_slider is not None
            else settings.initial_transit_count,
        )
        blocked_count = max(
            1,
            self.blocked_count_slider.integer_value
            if self.blocked_count_slider is not None
            else settings.initial_blocked_count,
        )

        if self.depot is None or not self.deliveries:
            self.depot = self._random_map_point()
            self.deliveries = self._generate_deliveries()

        self.mesh = build_vrp_mesh(
            self.depot,
            self.deliveries,
            self.map_bounds(),
            transit_count=transit_count,
            blocked_count=blocked_count,
        )
        self.assignment = assign_deliveries_greedy(
            self.deliveries,
            vehicle_count=vehicle_count,
            depot=self.depot,
        )
        self.vehicle_states = {}
        for vehicle_id, points in self.assignment.items():
            tokens = []
            for point in points:
                tokens.extend(split_into_tokens(point, capacity))
            self.vehicle_states[vehicle_id] = initialize_vehicle_genetic(
                vehicle_id=vehicle_id,
                tokens=tokens,
                population_size=settings.population_size,
                depot=self.depot,
                mesh=self.mesh,
                capacity=capacity,
                priority_weight=self.priority_weight if self.priority_weight_slider else 0.0,
                plan_fallback_penalty=settings.plan_fallback_penalty,
                plan_last_resort_penalty=settings.plan_last_resort_penalty,
            )

        self.generation_counter = itertools.count(start=1)
        self.last_vehicle_count = vehicle_count
        self.last_capacity = capacity
        self.last_transit_count = transit_count
        self.last_blocked_count = blocked_count
        self._sync_capacity_slider_bounds()
        self._sync_focus_after_rebuild()

    def _sync_capacity_slider_bounds(self) -> None:
        if self.capacity_slider is None:
            return
        settings = self.settings
        total = total_delivery_demand(self.deliveries)
        maximum = max(settings.minimum_capacity, total)
        self.capacity_slider.maximum_value = float(maximum)
        if self.capacity_slider.integer_value > maximum:
            self.capacity_slider.value = float(maximum)

    def shuffle_all(self) -> None:
        self.depot = None
        self.deliveries = []
        self.rebuild_scenario()

    def apply_hospital_preset(self) -> None:
        if not self.deliveries:
            return
        priorities = apply_hospital_priority_preset(len(self.deliveries))
        self.deliveries = [
            DeliveryPoint(
                id=point.id,
                coordinate=point.coordinate,
                priority=priorities[index],
                demand=point.demand,
            )
            for index, point in enumerate(self.deliveries)
        ]
        self.rebuild_scenario()

    def initialize(self) -> None:
        self._create_control_widgets()
        self.shuffle_all()

    def _create_control_widgets(self) -> None:
        settings = self.settings
        controls_width = settings.plot_horizontal_offset - 2 * VisualTheme.control_margin
        half_width = (controls_width - VisualTheme.control_gap) // 2
        saved_two_opt = (
            self.two_opt_toggle.is_active if self.two_opt_toggle is not None else False
        )
        saved_show_mesh = (
            self.mesh_toggle.is_active if self.mesh_toggle is not None else self.show_mesh
        )

        self.section_algorithm_y = 0
        mutation_y = self.section_algorithm_y + 26
        priority_y = mutation_y + settings.mutation_slider_height + 12
        two_opt_y = priority_y + settings.mutation_slider_height + 12
        mesh_toggle_y = two_opt_y + 32 + 12

        self.section_fleet_y = mesh_toggle_y + 32 + 12
        fleet_y = self.section_fleet_y + 26

        self.section_quantity_y = fleet_y + settings.count_slider_height + 12
        mesh_y = self.section_quantity_y + 26

        self.section_actions_y = mesh_y + settings.count_slider_height + 12
        regenerate_y = self.section_actions_y + 26
        hospital_y = regenerate_y + settings.regenerate_button_height + VisualTheme.control_gap
        focus_y = hospital_y + settings.regenerate_button_height + VisualTheme.control_gap

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
            position_y=priority_y,
            width=controls_width,
            height=settings.mutation_slider_height,
            value=settings.initial_priority_weight,
            minimum_value=0.0,
            maximum_value=100.0,
            label="Peso da prioridade",
            value_suffix="",
        )
        self.two_opt_toggle = ToggleButton(
            position_x=VisualTheme.control_margin,
            position_y=two_opt_y,
            width=controls_width,
            height=32,
            label="Refinamento 2-opt",
            is_active=saved_two_opt,
        )
        self.mesh_toggle = ToggleButton(
            position_x=VisualTheme.control_margin,
            position_y=mesh_toggle_y,
            width=controls_width,
            height=32,
            label="Mostrar malha",
            is_active=saved_show_mesh,
        )
        self.show_mesh = saved_show_mesh
        self.vehicle_count_slider = IntegerSlider(
            position_x=VisualTheme.control_margin,
            position_y=fleet_y,
            width=half_width,
            height=settings.count_slider_height,
            value=settings.initial_vehicle_count,
            minimum_value=1,
            maximum_value=settings.maximum_vehicle_count,
            label="Veículos",
        )
        self.capacity_slider = IntegerSlider(
            position_x=VisualTheme.control_margin + half_width + VisualTheme.control_gap,
            position_y=fleet_y,
            width=half_width,
            height=settings.count_slider_height,
            value=settings.initial_capacity,
            minimum_value=settings.minimum_capacity,
            maximum_value=settings.initial_capacity,
            label="Capacidade",
        )
        self.transit_count_slider = IntegerSlider(
            position_x=VisualTheme.control_margin,
            position_y=mesh_y,
            width=half_width,
            height=settings.count_slider_height,
            value=settings.initial_transit_count,
            minimum_value=1,
            maximum_value=settings.maximum_mesh_nodes_per_type,
            label="Trânsito",
        )
        self.blocked_count_slider = IntegerSlider(
            position_x=VisualTheme.control_margin + half_width + VisualTheme.control_gap,
            position_y=mesh_y,
            width=half_width,
            height=settings.count_slider_height,
            value=max(1, settings.initial_blocked_count),
            minimum_value=1,
            maximum_value=settings.maximum_mesh_nodes_per_type,
            label="Bloqueados",
        )
        self.regenerate_positions_button = ActionButton(
            position_x=VisualTheme.control_margin,
            position_y=regenerate_y,
            width=controls_width,
            height=settings.regenerate_button_height,
            label="Sortear posições",
            subtitle="Depósito, entregas e malha",
        )
        self.hospital_preset_button = ActionButton(
            position_x=VisualTheme.control_margin,
            position_y=hospital_y,
            width=controls_width,
            height=settings.regenerate_button_height,
            label="Cenário hospitalar",
            subtitle="Prioridades críticas fixas",
        )
        self.focus_filter_button = ActionButton(
            position_x=VisualTheme.control_margin,
            position_y=focus_y,
            width=controls_width,
            height=settings.regenerate_button_height,
            label=self.focus_filter_label(),
            subtitle="Cicla Todos → V1 → V2 → …",
        )

    def handle_control_events(self, event: pygame.event.Event) -> None:
        self.mutation_slider.handle_event(event)
        self.priority_weight_slider.handle_event(event)
        self.two_opt_toggle.handle_event(event)
        self.mesh_toggle.handle_event(event)
        self.vehicle_count_slider.handle_event(event)
        self.capacity_slider.handle_event(event)
        self.transit_count_slider.handle_event(event)
        self.blocked_count_slider.handle_event(event)
        self.regenerate_positions_button.handle_event(event)
        self.hospital_preset_button.handle_event(event)
        self.focus_filter_button.handle_event(event)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
            self.apply_hospital_preset()

    def update_controls_if_changed(self) -> None:
        if self.mesh_toggle is not None:
            self.show_mesh = self.mesh_toggle.is_active
        if self.focus_filter_button.was_pressed:
            self.focus_filter_button.was_pressed = False
            self.cycle_focus_vehicle()
            return
        if self.hospital_preset_button.was_pressed:
            self.hospital_preset_button.was_pressed = False
            self.apply_hospital_preset()
            return
        if self.regenerate_positions_button.was_pressed:
            self.regenerate_positions_button.was_pressed = False
            self.shuffle_all()
            return
        if any(
            slider.is_dragging
            for slider in (
                self.vehicle_count_slider,
                self.capacity_slider,
                self.transit_count_slider,
                self.blocked_count_slider,
            )
        ):
            return

        vehicle_count = self.vehicle_count_slider.integer_value
        capacity = self.capacity_slider.integer_value
        transit_count = self.transit_count_slider.integer_value
        blocked_count = self.blocked_count_slider.integer_value
        if (
            vehicle_count != self.last_vehicle_count
            or capacity != self.last_capacity
            or transit_count != self.last_transit_count
            or blocked_count != self.last_blocked_count
        ):
            self.rebuild_scenario()

    def run_one_generation(self) -> tuple:
        capacity = self.capacity_slider.integer_value
        mutation_probability = self.mutation_slider.value
        priority_weight = self.priority_weight

        for vehicle_id, state in list(self.vehicle_states.items()):
            self.vehicle_states[vehicle_id] = run_vehicle_generation(
                state,
                depot=self.depot,
                mesh=self.mesh,
                capacity=capacity,
                priority_weight=priority_weight,
                mutation_probability=mutation_probability,
                use_2opt=self.two_opt_toggle.is_active,
                plan_fallback_penalty=self.settings.plan_fallback_penalty,
                plan_last_resort_penalty=self.settings.plan_last_resort_penalty,
            )

        generation_number = next(self.generation_counter)
        total_fitness = 0.0
        total_distance = 0.0
        total_priority = 0.0
        plans = {}
        histories = {}
        for vehicle_id, state in self.vehicle_states.items():
            total_fitness += state.best_fitness if state.best_fitness != float("inf") else 0.0
            if state.best_plan is not None:
                total_distance += state.best_plan.total_distance if state.best_plan.total_distance != float("inf") else 0.0
                total_priority += state.best_plan.priority_penalty * priority_weight
                plans[vehicle_id] = state.best_plan
            histories[vehicle_id] = list(state.fitness_history)

        return (
            generation_number,
            total_fitness,
            total_distance,
            total_priority,
            plans,
            histories,
        )
