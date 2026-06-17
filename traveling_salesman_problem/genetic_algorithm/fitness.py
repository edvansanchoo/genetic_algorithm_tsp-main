"""Cálculo de distância e avaliação de rotas."""

import math
from typing import Any, List, Optional, Tuple

from traveling_salesman_problem.obstacles.penalty import calculate_segment_obstacle_penalty

CityCoordinate = Tuple[float, float]
Route = List[CityCoordinate]


def calculate_euclidean_distance(
    first_point: CityCoordinate,
    second_point: CityCoordinate,
) -> float:
    """Distância euclidiana entre dois pontos do plano."""
    delta_x = first_point[0] - second_point[0]
    delta_y = first_point[1] - second_point[1]
    return math.sqrt(delta_x ** 2 + delta_y ** 2)


def calculate_route_fitness(
    route: Route,
    obstacles: Optional[List[Any]] = None,
    use_obstacle_penalties: bool = True,
) -> float:
    """
    Avalia uma rota pelo custo total do ciclo fechado.

    O custo inclui a soma das distâncias entre cidades consecutivas
    e, opcionalmente, penalidades por cruzar árvores ou lagos habilitados.
    """
    total_cost = 0.0
    number_of_cities = len(route)

    for city_index in range(number_of_cities):
        current_city = route[city_index]
        next_city = route[(city_index + 1) % number_of_cities]
        total_cost += calculate_euclidean_distance(current_city, next_city)

        if obstacles:
            total_cost += calculate_segment_obstacle_penalty(
                current_city,
                next_city,
                obstacles,
                use_obstacle_penalties,
            )

    return total_cost
