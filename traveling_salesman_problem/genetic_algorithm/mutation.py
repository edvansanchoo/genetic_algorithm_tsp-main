"""Operador de mutação por troca de cidades adjacentes."""

import copy
import random
from typing import List, Tuple

CityCoordinate = Tuple[float, float]
Route = List[CityCoordinate]


def swap_adjacent_cities_mutation(
    route: Route,
    mutation_probability: float,
) -> Route:
    """
    Troca duas cidades vizinhas com probabilidade definida.

    A mutação só ocorre quando o sorteio aleatório é menor que
    a probabilidade informada e a rota possui ao menos duas cidades.
    """
    mutated_route = copy.deepcopy(route)

    if random.random() >= mutation_probability:
        return mutated_route

    if len(route) < 2:
        return route

    swap_index = random.randint(0, len(route) - 2)
    mutated_route[swap_index], mutated_route[swap_index + 1] = (
        route[swap_index + 1],
        route[swap_index],
    )

    return mutated_route

# essa mutação costuma ser mais ousada já que tende a explorar mais, dependendo do elitismo tende a ser mais instável
def swap_random_cities_mutation(
    route: Route,
    mutation_probability: float,
) -> Route:
    """Troca duas cidades quaisquer com probabilidade definida."""
    mutated_route = copy.deepcopy(route)

    if (random.random() >= mutation_probability):
        return mutated_route
    
    if len(route) < 2:
        return route
    
    first_index, second_index = sorted(random.sample(range(len(route)), 2))
    mutated_route[first_index], mutated_route[second_index] = (
        mutated_route[second_index],
        mutated_route[first_index],
    )

    return mutated_route

def apply_mutation(
    route: Route,
    mutation_probability: float,
    mutation_type: str = "adjacent",
) -> Route:
    """Aplica uma das mutações disponíveis."""
    if mutation_type == "random":
        return swap_random_cities_mutation(route, mutation_probability)
    return swap_adjacent_cities_mutation(route, mutation_probability)