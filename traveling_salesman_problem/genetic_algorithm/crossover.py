"""Operador de cruzamento Order Crossover para permutações."""

import random
from typing import List, Tuple

CityCoordinate = Tuple[float, float]
Route = List[CityCoordinate]


def order_crossover(first_parent: Route, second_parent: Route) -> Route:
    """
    Combina dois pais preservando ordem relativa (válido para TSP).

    Um segmento contíguo vem do primeiro pai; as demais posições
    são preenchidas na ordem em que aparecem no segundo pai.
    """
    route_length = len(first_parent)
    start_index = random.randint(0, route_length - 1)
    end_index = random.randint(start_index + 1, route_length)

    child_route = list(first_parent[start_index:end_index])
    remaining_positions = [
        index for index in range(route_length)
        if index < start_index or index >= end_index
    ]
    remaining_cities = [
        city for city in second_parent if city not in child_route
    ]

    for position, city in zip(remaining_positions, remaining_cities):
        child_route.insert(position, city)

    return child_route
