"""Criação e ordenação da população de rotas."""

import random
from typing import List, Tuple

CityCoordinate = Tuple[float, float]
Route = List[CityCoordinate]


def generate_random_population(
    city_coordinates: List[CityCoordinate],
    population_size: int,
) -> List[Route]:
    """Gera rotas aleatórias como permutações válidas das cidades."""
    return [
        random.sample(city_coordinates, len(city_coordinates))
        for _ in range(population_size)
    ]


def sort_population_by_fitness(
    population: List[Route],
    fitness_values: List[float],
) -> Tuple[List[Route], List[float]]:
    """Ordena rotas da melhor (menor distância) para a pior."""
    paired = list(zip(population, fitness_values))
    paired.sort(key=lambda pair: pair[1])
    sorted_population, sorted_fitness = zip(*paired)
    return list(sorted_population), list(sorted_fitness)
