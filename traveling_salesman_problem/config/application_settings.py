"""Parâmetros da janela, do mapa e do simulador de entregas."""

from dataclasses import dataclass

from traveling_salesman_problem.config.visual_theme import VisualTheme


@dataclass(frozen=True)
class ApplicationSettings:
    window_width: int = 1120
    window_height: int = 940
    frames_per_second: int = 30

    initial_vehicle_count: int = 1
    initial_delivery_point_count: int = 2
    initial_total_items: int = 6
    initial_transit_node_count: int = 8
    initial_connection_radius: int = 150
    minimum_transit_nodes: int = 3
    maximum_transit_nodes: int = 15
    minimum_connection_radius: int = 80
    maximum_connection_radius: int = 250
    initial_gas_station_count: int = 3
    minimum_gas_stations: int = 0
    maximum_gas_stations: int = 6

    map_margin: int = 20
    delivery_point_radius: int = 9
    depot_half_size: int = 7

    count_slider_height: int = 48
    action_button_height: int = 36
    summary_panel_height: int = 0

    population_size: int = 100
    initial_mutation_probability: float = 0.01
    mutation_slider_height: int = 58
    generations_per_second: float = 3.0

    @property
    def plot_horizontal_offset(self) -> int:
        return VisualTheme.sidebar_width

    @property
    def controls_top_position(self) -> int:
        return VisualTheme.plot_height + VisualTheme.control_gap

    @property
    def scroll_viewport_top(self) -> int:
        return self.controls_top_position

    @property
    def scroll_viewport_height(self) -> int:
        return (
            self.window_height
            - self.scroll_viewport_top
            - VisualTheme.sidebar_footer_height
            - VisualTheme.control_gap
        )

    @property
    def sidebar_footer_y(self) -> int:
        return self.window_height - VisualTheme.sidebar_footer_height

    @property
    def map_minimum_x(self) -> int:
        return self.plot_horizontal_offset + self.map_margin

    @property
    def map_minimum_y(self) -> int:
        return VisualTheme.map_header_height + self.map_margin

    @property
    def map_maximum_x(self) -> int:
        return self.window_width - self.map_margin

    @property
    def map_maximum_y(self) -> int:
        return self.window_height - self.map_margin
