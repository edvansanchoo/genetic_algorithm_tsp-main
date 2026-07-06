"""Seleção de pais e evolução de uma nova geração."""

import random
from typing import List, Tuple

import numpy as np

from traveling_salesman_problem.genetic_algorithm.crossover import order_crossover
from traveling_salesman_problem.genetic_algorithm.mutation import apply_mutation
from traveling_salesman_problem.genetic_algorithm.fitness import add_2opt

CityCoordinate = Tuple[float, float]
Route = List[CityCoordinate]


def select_two_parents_by_fitness_weight(
    population: List[Route],
    fitness_values: List[float],
) -> Tuple[Route, Route]:
    """
    Seleciona dois pais com probabilidade inversamente proporcional ao custo.

    Rotas mais curtas recebem peso maior e têm mais chance de reproduzir.
    """
    selection_weights = 1 / np.array(fitness_values)
    first_parent, second_parent = random.choices(
        population,
        weights=selection_weights,
        k=2,
    )
    return first_parent, second_parent


def evolve_next_generation(
    population: List[Route],
    fitness_values: List[float],
    population_size: int,
    mutation_probability: float,
    mutation_type: str = "adjacent", # seleciona o tipo de mutação adjacent/random,
    n_elite: int = 2, # elitismo para guardar "os melhores" para a próxima geração
) -> List[Route]:
    """
    Produz a próxima geração com elitismo, cruzamento e mutação.

    O melhor indivíduo da geração atual é copiado sem alteração;
    os demais são gerados por seleção, crossover e mutação.
    """
    new_population = [population[0]]

    while len(new_population) < population_size:
        first_parent, second_parent = select_two_parents_by_fitness_weight(
            population,
            fitness_values,
        )
        child_route = order_crossover(first_parent, second_parent)
        child_route = apply_mutation(
            child_route,
            mutation_probability,
            mutation_type=mutation_type,
        )

        # 2-opt costuma reduzir drasticamente, achando boas rotas mais cedo
        # em contrapartida 2-opt custa mais no processamento por geração
        # child_route = add_2opt(child_route)

        new_population.append(child_route)

    return new_population
