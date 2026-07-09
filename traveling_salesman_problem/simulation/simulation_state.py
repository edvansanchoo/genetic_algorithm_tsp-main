"""Estado mutável compartilhado durante a simulação de entregas."""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import pygame

from delivery_simulation import (
    DeliveryPoint,
    SimulationConfig,
    SimulationResult,
    VALID_TOTAL_ITEMS,
    distribute_items,
    format_simulation_result,
    generate_depot_and_points,
    run_simulation,
)
from delivery_simulation.models import Coordinate
from traveling_salesman_problem.config.application_settings import ApplicationSettings
from traveling_salesman_problem.config.visual_theme import VisualTheme
from traveling_salesman_problem.visualization.widgets import ActionButton, DiscreteSlider, IntegerSlider

StatusMessage = Optional[str]


@dataclass
class SimulationState:
    settings: ApplicationSettings = field(default_factory=ApplicationSettings)

    depot: Optional[Coordinate] = None
    delivery_points: List[DeliveryPoint] = field(default_factory=list)
    positions_ready: bool = False
    simulation_result: Optional[SimulationResult] = None
    result_lines: List[str] = field(default_factory=list)
    status_message: StatusMessage = None

    vehicle_count_slider: Optional[IntegerSlider] = None
    delivery_point_count_slider: Optional[IntegerSlider] = None
    total_items_slider: Optional[DiscreteSlider] = None
    shuffle_positions_button: Optional[ActionButton] = None
    simulate_button: Optional[ActionButton] = None

    section_config_y: int = 0
    section_actions_y: int = 0
    section_results_y: int = 0

    _last_vehicle_count: int = 0
    _last_delivery_point_count: int = 0
    _last_total_items: int = 0

    def initialize(self) -> None:
        self._create_control_widgets()
        self._last_vehicle_count = self.vehicle_count_slider.integer_value
        self._last_delivery_point_count = self.delivery_point_count_slider.integer_value
        self._last_total_items = self.total_items_slider.selected_value

    def _create_control_widgets(self) -> None:
        settings = self.settings
        controls_width = settings.plot_horizontal_offset - 2 * VisualTheme.control_margin

        self.section_config_y = 0
        config_content_y = self.section_config_y + 26
        vehicle_slider_y = config_content_y
        point_slider_y = vehicle_slider_y + settings.count_slider_height + 12
        items_slider_y = point_slider_y + settings.count_slider_height + 12
        self.section_actions_y = items_slider_y + settings.count_slider_height + 12
        shuffle_button_y = self.section_actions_y + 26
        simulate_button_y = shuffle_button_y + settings.action_button_height + VisualTheme.control_gap
        self.section_results_y = simulate_button_y + settings.action_button_height + 12

        self.vehicle_count_slider = IntegerSlider(
            position_x=VisualTheme.control_margin,
            position_y=vehicle_slider_y,
            width=controls_width,
            height=settings.count_slider_height,
            value=settings.initial_vehicle_count,
            minimum_value=1,
            maximum_value=3,
            label="Veículos",
        )
        self.delivery_point_count_slider = IntegerSlider(
            position_x=VisualTheme.control_margin,
            position_y=point_slider_y,
            width=controls_width,
            height=settings.count_slider_height,
            value=settings.initial_delivery_point_count,
            minimum_value=1,
            maximum_value=3,
            label="Pontos de entrega",
        )
        self.total_items_slider = DiscreteSlider(
            position_x=VisualTheme.control_margin,
            position_y=items_slider_y,
            width=controls_width,
            height=settings.count_slider_height,
            value=settings.initial_total_items,
            allowed_values=VALID_TOTAL_ITEMS,
            label="Total de itens",
        )
        self.shuffle_positions_button = ActionButton(
            position_x=VisualTheme.control_margin,
            position_y=shuffle_button_y,
            width=controls_width,
            height=settings.action_button_height,
            label="Sortear posições",
            subtitle="Distribuidora, pontos e pedidos",
        )
        self.simulate_button = ActionButton(
            position_x=VisualTheme.control_margin,
            position_y=simulate_button_y,
            width=controls_width,
            height=settings.action_button_height,
            label="Simular",
            subtitle="Calcular rotas gulosas",
        )

    def build_simulation_config(self) -> SimulationConfig:
        return SimulationConfig(
            vehicle_count=self.vehicle_count_slider.integer_value,
            delivery_point_count=self.delivery_point_count_slider.integer_value,
            total_items=self.total_items_slider.selected_value,
        )

    def can_simulate(self) -> bool:
        return self.positions_ready and self.depot is not None and bool(self.delivery_points)

    def clear_simulation_result(self) -> None:
        self.simulation_result = None
        self.result_lines = []

    def shuffle_positions(self) -> None:
        settings = self.settings
        point_count = self.delivery_point_count_slider.integer_value
        total_items = self.total_items_slider.selected_value

        depot, generated_points = generate_depot_and_points(
            point_count,
            settings.map_minimum_x,
            settings.map_minimum_y,
            settings.map_maximum_x,
            settings.map_maximum_y,
        )
        orders = distribute_items(total_items, point_count)

        self.depot = depot
        self.delivery_points = [
            DeliveryPoint(
                id=label,
                coordinate=coordinate,
                total_items=orders[label],
                remaining_items=orders[label],
            )
            for label, coordinate in generated_points
        ]
        self.positions_ready = True
        self.status_message = None
        self.clear_simulation_result()

    def run_delivery_simulation(self) -> None:
        if not self.can_simulate():
            self.status_message = "Sorteie posições antes de simular."
            return

        config = self.build_simulation_config()
        input_points = [
            DeliveryPoint(
                id=point.id,
                coordinate=point.coordinate,
                total_items=point.total_items,
                remaining_items=point.total_items,
            )
            for point in self.delivery_points
        ]
        self.simulation_result = run_simulation(config, self.depot, input_points)
        self.result_lines = format_simulation_result(self.simulation_result)
        self.status_message = None

    def handle_control_events(self, event: pygame.event.Event) -> None:
        self.vehicle_count_slider.handle_event(event)
        self.delivery_point_count_slider.handle_event(event)
        self.total_items_slider.handle_event(event)
        self.shuffle_positions_button.handle_event(event)
        if self.can_simulate():
            self.simulate_button.handle_event(event)

    def update_controls(self) -> None:
        if self.shuffle_positions_button.was_pressed:
            self.shuffle_positions_button.was_pressed = False
            self.shuffle_positions()
            self._sync_slider_snapshots()
            return

        if self.simulate_button.was_pressed:
            self.simulate_button.was_pressed = False
            if self.can_simulate():
                self.run_delivery_simulation()
            else:
                self.status_message = "Sorteie posições antes de simular."
            return

        current_vehicle_count = self.vehicle_count_slider.integer_value
        current_point_count = self.delivery_point_count_slider.integer_value
        current_total_items = self.total_items_slider.selected_value

        config_changed = (
            current_vehicle_count != self._last_vehicle_count
            or current_point_count != self._last_delivery_point_count
            or current_total_items != self._last_total_items
        )

        if config_changed:
            self.clear_simulation_result()
            if current_point_count != self._last_delivery_point_count:
                self.positions_ready = False
                self.depot = None
                self.delivery_points = []
                self.status_message = "Quantidade de pontos alterada. Sorteie posições novamente."
            self._sync_slider_snapshots()

    def _sync_slider_snapshots(self) -> None:
        self._last_vehicle_count = self.vehicle_count_slider.integer_value
        self._last_delivery_point_count = self.delivery_point_count_slider.integer_value
        self._last_total_items = self.total_items_slider.selected_value

    def calculate_scrollable_content_height(self) -> int:
        line_height = 14
        results_height = 26 + max(1, len(self.result_lines)) * line_height + 20
        status_height = 20 if self.status_message else 0
        return self.section_results_y + results_height + status_height

    def total_distance(self) -> Optional[float]:
        if self.simulation_result is None:
            return None
        return self.simulation_result.total_system_distance

    def total_trips(self) -> Optional[int]:
        if self.simulation_result is None:
            return None
        return sum(len(vehicle.trips) for vehicle in self.simulation_result.vehicles)
