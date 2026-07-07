"""Parâmetros da janela, do mapa e do algoritmo genético."""

from dataclasses import dataclass

from traveling_salesman_problem.config.visual_theme import VisualTheme


@dataclass(frozen=True)
class ApplicationSettings:
    window_width: int = 1120
    window_height: int = 940
    frames_per_second: int = 30

    number_of_cities: int = 15
    population_size: int = 100
    initial_mutation_probability: float = 0.01
    initial_priority_weight: float = 0.0

    initial_tree_count: int = 3
    initial_lake_count: int = 2
    maximum_terrain_features_per_type: int = 8

    map_margin: int = 20
    city_node_radius: int = 9

    mutation_slider_height: int = 58
    count_slider_height: int = 48
    regenerate_button_height: int = 36
    scenario_selector_viewport_height: int = 140

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
