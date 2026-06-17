"""Posicionamento aleatório de cidades no mapa."""

import random
from typing import List, Tuple

from traveling_salesman_problem.genetic_algorithm.population import generate_random_population
from traveling_salesman_problem.obstacles.collision import point_inside_any_obstacle
from traveling_salesman_problem.obstacles.models import Obstacle

CityCoordinate = Tuple[int, int]


def generate_random_city_coordinate(
    window_width: int,
    window_height: int,
    plot_horizontal_offset: int,
    city_node_radius: int,
    obstacles: List[Obstacle],
) -> CityCoordinate:
    """Sorteia uma coordenada válida fora de obstáculos habilitados."""
    while True:
        coordinate_x = random.randint(
            city_node_radius + plot_horizontal_offset,
            window_width - city_node_radius,
        )
        coordinate_y = random.randint(
            city_node_radius,
            window_height - city_node_radius,
        )
        if not point_inside_any_obstacle(
            (coordinate_x, coordinate_y),
            obstacles,
            only_enabled=True,
        ):
            return (coordinate_x, coordinate_y)


def reshuffle_cities_and_population(
    city_coordinates: List[CityCoordinate],
    number_of_cities: int,
    population_size: int,
    population: List[List[CityCoordinate]],
    best_fitness_history: List[float],
    best_route_history: List[List[CityCoordinate]],
    window_width: int,
    window_height: int,
    plot_horizontal_offset: int,
    city_node_radius: int,
    obstacles: List[Obstacle],
) -> None:
    """Reposiciona cidades e reinicia população e histórico de convergência."""
    city_coordinates[:] = [
        generate_random_city_coordinate(
            window_width,
            window_height,
            plot_horizontal_offset,
            city_node_radius,
            obstacles,
        )
        for _ in range(number_of_cities)
    ]
    population[:] = generate_random_population(city_coordinates, population_size)
    best_fitness_history.clear()
    best_route_history.clear()
