"""Estado mutável compartilhado durante a simulação de entregas."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import pygame

from delivery_simulation import (
    DeliveryPoint,
    RoadNetwork,
    SimulationConfig,
    SimulationResult,
    TransitNode,
    VALID_TOTAL_ITEMS,
    build_connected_network,
    distribute_items,
    extract_vehicle_assignments,
    format_simulation_result,
    generate_depot_and_points,
    generate_transit_nodes,
    initialize_vehicle_genetic,
    run_simulation,
    run_vehicle_generation,
)
from delivery_simulation.road_network import ensure_connectivity
from delivery_simulation.models import Coordinate, DEPOT_ID, Vehicle
from delivery_simulation.vehicle_genetic import VehicleGeneticState
from traveling_salesman_problem.config.application_settings import ApplicationSettings
from traveling_salesman_problem.config.visual_theme import VisualTheme
from traveling_salesman_problem.visualization.widgets import (
    ActionButton,
    DiscreteSlider,
    IntegerSlider,
    MutationSlider,
    TripSelector,
)

StatusMessage = Optional[str]


@dataclass
class SimulationState:
    settings: ApplicationSettings = field(default_factory=ApplicationSettings)

    depot: Optional[Coordinate] = None
    delivery_points: List[DeliveryPoint] = field(default_factory=list)
    road_network: Optional[RoadNetwork] = None
    transit_nodes: List[TransitNode] = field(default_factory=list)
    positions_ready: bool = False
    simulation_result: Optional[SimulationResult] = None
    best_simulation_result: Optional[SimulationResult] = None
    result_lines: List[str] = field(default_factory=list)
    status_message: StatusMessage = None

    is_evolution_running: bool = False
    vehicle_genetic_states: Dict[int, VehicleGeneticState] = field(default_factory=dict)
    vehicle_best_distance_history: Dict[int, List[float]] = field(default_factory=dict)
    generation_counter: int = 0

    vehicle_count_slider: Optional[IntegerSlider] = None
    delivery_point_count_slider: Optional[IntegerSlider] = None
    total_items_slider: Optional[DiscreteSlider] = None
    transit_count_slider: Optional[IntegerSlider] = None
    connection_radius_slider: Optional[IntegerSlider] = None
    mutation_slider: Optional[MutationSlider] = None
    shuffle_positions_button: Optional[ActionButton] = None
    simulate_button: Optional[ActionButton] = None
    trip_selector: Optional[TripSelector] = None

    section_config_y: int = 0
    section_actions_y: int = 0
    section_visualization_y: int = 0
    section_results_y: int = 0

    _last_vehicle_count: int = 0
    _last_delivery_point_count: int = 0
    _last_total_items: int = 0
    _last_transit_count: int = 0
    _last_connection_radius: int = 0

    def initialize(self) -> None:
        self._create_control_widgets()
        self._sync_slider_snapshots()

    def _create_control_widgets(self) -> None:
        settings = self.settings
        controls_width = settings.plot_horizontal_offset - 2 * VisualTheme.control_margin

        self.section_config_y = 0
        y = self.section_config_y + 26
        self.vehicle_count_slider = IntegerSlider(
            VisualTheme.control_margin, y, controls_width, settings.count_slider_height,
            settings.initial_vehicle_count, 1, 3, "Veículos",
        )
        y += settings.count_slider_height + 12
        self.delivery_point_count_slider = IntegerSlider(
            VisualTheme.control_margin, y, controls_width, settings.count_slider_height,
            settings.initial_delivery_point_count, 1, 3, "Pontos de entrega",
        )
        y += settings.count_slider_height + 12
        self.total_items_slider = DiscreteSlider(
            VisualTheme.control_margin, y, controls_width, settings.count_slider_height,
            settings.initial_total_items, VALID_TOTAL_ITEMS, "Total de itens",
        )
        y += settings.count_slider_height + 12
        self.transit_count_slider = IntegerSlider(
            VisualTheme.control_margin, y, controls_width, settings.count_slider_height,
            settings.initial_transit_node_count,
            settings.minimum_transit_nodes,
            settings.maximum_transit_nodes,
            "Nós de trânsito",
        )
        y += settings.count_slider_height + 12
        self.connection_radius_slider = IntegerSlider(
            VisualTheme.control_margin, y, controls_width, settings.count_slider_height,
            settings.initial_connection_radius,
            settings.minimum_connection_radius,
            settings.maximum_connection_radius,
            "Raio de conexão (px)",
        )
        y += settings.count_slider_height + 12
        self.mutation_slider = MutationSlider(
            VisualTheme.control_margin,
            y,
            controls_width,
            settings.mutation_slider_height,
            value=settings.initial_mutation_probability,
            minimum_value=0.0,
            maximum_value=1.0,
            label="Mutação",
            value_suffix="%",
        )
        y += settings.mutation_slider_height + 12
        self.section_actions_y = y
        shuffle_y = self.section_actions_y + 26
        simulate_y = shuffle_y + settings.action_button_height + VisualTheme.control_gap
        self.section_visualization_y = simulate_y + settings.action_button_height + 12
        self.section_results_y = self.section_visualization_y + 120

        self.shuffle_positions_button = ActionButton(
            VisualTheme.control_margin, shuffle_y, controls_width,
            settings.action_button_height, "Sortear posições",
            subtitle="Rede, trânsito e pedidos",
        )
        self.simulate_button = ActionButton(
            VisualTheme.control_margin, simulate_y, controls_width,
            settings.action_button_height, "Simular",
            subtitle="Guloso + AG contínuo (~3 gen/s)",
        )
        self.trip_selector = TripSelector(
            VisualTheme.control_margin,
            self.section_visualization_y + 26,
            controls_width,
        )

    def build_simulation_config(self) -> SimulationConfig:
        return SimulationConfig(
            vehicle_count=self.vehicle_count_slider.integer_value,
            delivery_point_count=self.delivery_point_count_slider.integer_value,
            total_items=self.total_items_slider.selected_value,
        )

    def can_simulate(self) -> bool:
        return (
            self.positions_ready
            and self.depot is not None
            and bool(self.delivery_points)
            and self.road_network is not None
        )

    def _reset_evolution(self) -> None:
        self.is_evolution_running = False
        self.vehicle_genetic_states = {}
        self.vehicle_best_distance_history = {}
        self.generation_counter = 0
        self.best_simulation_result = None
        if self.trip_selector is not None:
            self.trip_selector.set_enabled(False)

    def clear_simulation_result(self) -> None:
        self.simulation_result = None
        self.result_lines = []
        self._reset_evolution()

    def _rebuild_best_simulation_result(self) -> None:
        if self.simulation_result is None:
            return

        vehicles = []
        for vehicle in self.simulation_result.vehicles:
            genetic = self.vehicle_genetic_states.get(vehicle.id)
            if genetic is None or not genetic.best_trips:
                vehicles.append(vehicle)
                continue
            vehicles.append(
                Vehicle(
                    id=vehicle.id,
                    current_node_id=DEPOT_ID,
                    current_position=self.simulation_result.depot,
                    current_load=0,
                    trips=list(genetic.best_trips),
                    assigned_points=list(vehicle.assigned_points),
                )
            )

        total_distance = sum(trip.distance for vehicle in vehicles for trip in vehicle.trips)
        self.best_simulation_result = SimulationResult(
            config=self.simulation_result.config,
            depot=self.simulation_result.depot,
            delivery_points=self.simulation_result.delivery_points,
            vehicles=vehicles,
            total_system_distance=total_distance,
            road_network=self.simulation_result.road_network,
            transit_nodes=self.simulation_result.transit_nodes,
        )

    def start_evolution_from_greedy(self) -> None:
        if self.simulation_result is None or self.road_network is None:
            return

        assignments = extract_vehicle_assignments(self.simulation_result)
        self.vehicle_genetic_states = {}
        self.vehicle_best_distance_history = {}

        for vehicle_id, tasks in assignments.items():
            state = initialize_vehicle_genetic(
                vehicle_id,
                tasks,
                self.road_network,
                population_size=self.settings.population_size,
            )
            self.vehicle_genetic_states[vehicle_id] = state
            self.vehicle_best_distance_history[vehicle_id] = [state.best_distance]

        self.generation_counter = 1
        self._rebuild_best_simulation_result()
        self.is_evolution_running = True

        if self.trip_selector is not None and self.best_simulation_result is not None:
            self.trip_selector.set_enabled(True)
            trip_counts = {
                vehicle.id: len(vehicle.trips)
                for vehicle in self.best_simulation_result.vehicles
            }
            self.trip_selector.set_vehicle_trip_counts(
                self.simulation_result.config.vehicle_count,
                trip_counts,
            )
            self.trip_selector.active_vehicle_id = 1
            self.trip_selector.active_trip_index = 0
            self.trip_selector.view_mode = "single"

    def run_one_generation(self) -> None:
        if not self.is_evolution_running or self.road_network is None:
            return

        mutation_probability = self.mutation_slider.value
        for vehicle_id, state in self.vehicle_genetic_states.items():
            best_distance = run_vehicle_generation(
                state,
                self.road_network,
                mutation_probability,
                population_size=self.settings.population_size,
            )
            self.vehicle_best_distance_history.setdefault(vehicle_id, []).append(best_distance)

        self.generation_counter += 1
        self._rebuild_best_simulation_result()

        if self.trip_selector is not None and self.best_simulation_result is not None:
            trip_counts = {
                vehicle.id: len(vehicle.trips)
                for vehicle in self.best_simulation_result.vehicles
            }
            self.trip_selector.set_vehicle_trip_counts(
                self.simulation_result.config.vehicle_count,
                trip_counts,
            )

    def shuffle_positions(self) -> None:
        settings = self.settings
        point_count = self.delivery_point_count_slider.integer_value
        total_items = self.total_items_slider.selected_value
        transit_count = self.transit_count_slider.integer_value
        radius = float(self.connection_radius_slider.integer_value)

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

        delivery_ids = [point.id for point in self.delivery_points]
        warning = None

        for _ in range(50):
            transit = generate_transit_nodes(
                transit_count,
                settings.map_minimum_x,
                settings.map_minimum_y,
                settings.map_maximum_x,
                settings.map_maximum_y,
            )
            nodes = {DEPOT_ID: depot}
            for point in self.delivery_points:
                nodes[point.id] = point.coordinate
            for node in transit:
                nodes[node.id] = node.coordinate

            network, warning = build_connected_network(nodes, radius, DEPOT_ID, delivery_ids)
            if ensure_connectivity(network, DEPOT_ID, delivery_ids):
                self.transit_nodes = transit
                self.road_network = network
                break
            self.transit_nodes = transit
            self.road_network = network
        else:
            self.status_message = warning or "Rede gerada com arestas extras de fallback."

        self.positions_ready = True
        if warning is None:
            self.status_message = None
        elif self.status_message is None:
            self.status_message = warning
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
        try:
            self.simulation_result = run_simulation(
                config,
                self.depot,
                input_points,
                self.road_network,
                self.transit_nodes,
            )
        except RuntimeError as error:
            self.simulation_result = None
            self.result_lines = []
            self._reset_evolution()
            self.status_message = str(error)
            return

        self.result_lines = format_simulation_result(self.simulation_result)
        self.status_message = None
        self.start_evolution_from_greedy()

    def handle_control_events(self, event: pygame.event.Event) -> None:
        self.vehicle_count_slider.handle_event(event)
        self.delivery_point_count_slider.handle_event(event)
        self.total_items_slider.handle_event(event)
        self.transit_count_slider.handle_event(event)
        self.connection_radius_slider.handle_event(event)
        self.mutation_slider.handle_event(event)
        self.shuffle_positions_button.handle_event(event)
        if self.can_simulate():
            self.simulate_button.handle_event(event)
        if self.trip_selector.enabled:
            self.trip_selector.handle_event(event)

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

        if self._network_config_changed():
            self.clear_simulation_result()
            self.positions_ready = False
            self.depot = None
            self.delivery_points = []
            self.road_network = None
            self.transit_nodes = []
            self.status_message = "Configuração de rede alterada. Sorteie posições novamente."
            self._sync_slider_snapshots()
            return

        if self._delivery_config_changed():
            self.clear_simulation_result()
            if self.delivery_point_count_slider.integer_value != self._last_delivery_point_count:
                self.positions_ready = False
                self.depot = None
                self.delivery_points = []
                self.road_network = None
                self.transit_nodes = []
                self.status_message = "Quantidade de pontos alterada. Sorteie posições novamente."
            self._sync_slider_snapshots()

    def _network_config_changed(self) -> bool:
        return (
            self.transit_count_slider.integer_value != self._last_transit_count
            or self.connection_radius_slider.integer_value != self._last_connection_radius
        )

    def _delivery_config_changed(self) -> bool:
        return (
            self.vehicle_count_slider.integer_value != self._last_vehicle_count
            or self.delivery_point_count_slider.integer_value != self._last_delivery_point_count
            or self.total_items_slider.selected_value != self._last_total_items
        )

    def _sync_slider_snapshots(self) -> None:
        self._last_vehicle_count = self.vehicle_count_slider.integer_value
        self._last_delivery_point_count = self.delivery_point_count_slider.integer_value
        self._last_total_items = self.total_items_slider.selected_value
        self._last_transit_count = self.transit_count_slider.integer_value
        self._last_connection_radius = self.connection_radius_slider.integer_value

    def active_result(self) -> Optional[SimulationResult]:
        return self.best_simulation_result or self.simulation_result

    def active_vehicle_genetic_state(self) -> Optional[VehicleGeneticState]:
        if not self.trip_selector or not self.vehicle_genetic_states:
            return None
        return self.vehicle_genetic_states.get(self.trip_selector.active_vehicle_id)

    def calculate_scrollable_content_height(self) -> int:
        line_height = 14
        results_height = 26 + max(1, len(self.result_lines)) * line_height + 20
        status_height = 20 if self.status_message else 0
        if self.active_result() is not None:
            detail_height = 80
            return (
                self.section_visualization_y
                + 26
                + self.trip_selector.height
                + detail_height
                + results_height
                + status_height
            )
        return self.section_results_y + results_height + status_height

    def total_distance(self) -> Optional[float]:
        active = self.active_result()
        if active is None:
            return None
        return active.total_system_distance

    def total_trips(self) -> Optional[int]:
        active = self.active_result()
        if active is None:
            return None
        return sum(len(vehicle.trips) for vehicle in active.vehicles)
