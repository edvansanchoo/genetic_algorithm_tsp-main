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


def calculate_route_distance(
    route: Route,
    obstacles: Optional[List[Any]] = None,
    use_obstacle_penalties: bool = True,
) -> float:
    """Soma distâncias do ciclo fechado e penalidades opcionais de terreno."""
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


def calculate_priority_penalty(
    route: Route,
    city_coordinates: List[CityCoordinate],
    priorities: List[int],
) -> float:
    """Retorna Σ(prioridade × posição). Posição 1 = city_coordinates[0]."""
    if not route or not priorities:
        return 0.0

    coordinate_to_priority = dict(zip(city_coordinates, priorities))
    reference_city = city_coordinates[0]
    start_index = route.index(reference_city)
    number_of_cities = len(route)
    total_penalty = 0.0

    for offset in range(number_of_cities):
        position = offset + 1
        city = route[(start_index + offset) % number_of_cities]
        total_penalty += coordinate_to_priority[city] * position

    return total_penalty


def get_rotated_route(
    route: Route,
    city_coordinates: List[CityCoordinate],
) -> Route:
    """Retorna a rota rotacionada para iniciar em city_coordinates[0]."""
    if not route:
        return []

    reference_city = city_coordinates[0]
    start_index = route.index(reference_city)
    number_of_cities = len(route)
    return [route[(start_index + offset) % number_of_cities] for offset in range(number_of_cities)]


def build_delivery_visit_order(
    route: Route,
    city_coordinates: List[CityCoordinate],
    priorities: List[int],
) -> List[Tuple[int, int, int]]:
    """Retorna (posição, número_da_cidade, prioridade) para cada parada."""
    coordinate_to_priority = dict(zip(city_coordinates, priorities))
    coordinate_to_city_number = {
        coordinate: index + 1 for index, coordinate in enumerate(city_coordinates)
    }
    rotated_route = get_rotated_route(route, city_coordinates)
    visit_order: List[Tuple[int, int, int]] = []

    for position, city in enumerate(rotated_route, start=1):
        visit_order.append(
            (position, coordinate_to_city_number[city], coordinate_to_priority[city])
        )

    return visit_order


def calculate_route_fitness(
    route: Route,
    obstacles: Optional[List[Any]] = None,
    use_obstacle_penalties: bool = True,
    city_coordinates: Optional[List[CityCoordinate]] = None,
    priorities: Optional[List[int]] = None,
    priority_weight: float = 0.0,
) -> float:
    """
    Avalia uma rota pelo custo total do ciclo fechado.

    O custo inclui distância, penalidades de terreno opcionais
    e penalidade ponderada por prioridade de entrega.
    """
    distance = calculate_route_distance(route, obstacles, use_obstacle_penalties)

    if priority_weight <= 0 or not city_coordinates or not priorities:
        return distance

    priority_penalty = calculate_priority_penalty(route, city_coordinates, priorities)
    return distance + priority_weight * priority_penalty


def decompose_route_fitness(
    route: Route,
    obstacles: Optional[List[Any]] = None,
    use_obstacle_penalties: bool = True,
    city_coordinates: Optional[List[CityCoordinate]] = None,
    priorities: Optional[List[int]] = None,
    priority_weight: float = 0.0,
) -> Tuple[float, float, float]:
    """Retorna (fitness_total, distância, penalidade_prioridade_ponderada)."""
    distance = calculate_route_distance(route, obstacles, use_obstacle_penalties)
    weighted_priority_penalty = 0.0

    if priority_weight > 0 and city_coordinates and priorities:
        weighted_priority_penalty = priority_weight * calculate_priority_penalty(
            route,
            city_coordinates,
            priorities,
        )

    fitness_total = distance + weighted_priority_penalty
    return fitness_total, distance, weighted_priority_penalty

def add_2opt(route):
    """Melhora um rota aplicando 2-opt."""
    improved_route = list(route)

    if len(improved_route) < 4:
        return improved_route
    
    improved = True
    while improved:
        improved = False
        current_distance = calculate_route_distance(improved_route)

        for first_index in range(len(improved_route) - 1):
            for second_index in range(first_index + 1, len(improved_route)):
                if second_index - first_index == 1:
                    continue

                candidate_route = list(improved_route)
                candidate_route[first_index + 1:second_index + 1] = reversed(
                    candidate_route[first_index + 1:second_index + 1]
                )

                candidate_distace = calculate_route_distance(candidate_route)

                if candidate_distace < current_distance:
                    improved_route = candidate_route
                    current_distance = candidate_route
                    current_distance = candidate_distace
                    improved = True
                    break
            if improved:
                break

    return improved_route