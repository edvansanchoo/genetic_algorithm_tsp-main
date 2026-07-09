"""Algoritmo genético por veículo sobre permutações de DeliveryTask."""

import random
from dataclasses import dataclass, field
from typing import List, Optional

from delivery_simulation.models import DeliveryTask, RoadNetwork, Trip
from delivery_simulation.route_evaluator import TaskPermutation, evaluate_permutation
from traveling_salesman_problem.genetic_algorithm.population import sort_population_by_fitness
from traveling_salesman_problem.genetic_algorithm.selection import evolve_next_generation

TaskPopulation = List[TaskPermutation]


@dataclass
class VehicleGeneticState:
    vehicle_id: int
    tasks: List[DeliveryTask]
    population: TaskPopulation = field(default_factory=list)
    best_distance: float = field(default_factory=lambda: float("inf"))
    best_permutation: TaskPermutation = field(default_factory=list)
    best_trips: List[Trip] = field(default_factory=list)
    second_best_distance: float = field(default_factory=lambda: float("inf"))
    second_best_permutation: TaskPermutation = field(default_factory=list)
    second_best_trips: List[Trip] = field(default_factory=list)


def _generate_random_population(
    tasks: List[DeliveryTask],
    population_size: int,
    rng: random.Random,
) -> TaskPopulation:
    if not tasks:
        return [[] for _ in range(population_size)]
    return [rng.sample(tasks, len(tasks)) for _ in range(population_size)]


def _evaluate_population(
    tasks: List[DeliveryTask],
    population: TaskPopulation,
    road_network: RoadNetwork,
) -> tuple[list[float], TaskPermutation, float, List[Trip], TaskPermutation, float, List[Trip]]:
    fitness_values: list[float] = []
    ranked: list[tuple[float, TaskPermutation, List[Trip]]] = []

    for permutation in population:
        distance, trips, _report = evaluate_permutation(tasks, permutation, road_network)
        fitness_values.append(distance if distance != float("inf") else float("inf"))
        if distance != float("inf"):
            ranked.append((distance, list(permutation), trips))

    ranked.sort(key=lambda item: item[0])
    if not ranked:
        empty: TaskPermutation = []
        return fitness_values, empty, float("inf"), [], empty, float("inf"), []

    best_distance, best_permutation, best_trips = ranked[0]
    second_distance, second_permutation, second_trips = float("inf"), [], []
    for distance, permutation, trips in ranked[1:]:
        if permutation != best_permutation:
            second_distance, second_permutation, second_trips = distance, permutation, trips
            break

    return (
        fitness_values,
        best_permutation,
        best_distance,
        best_trips,
        second_permutation,
        second_distance,
        second_trips,
    )


def _apply_generation_best(
    state: VehicleGeneticState,
    best_permutation: TaskPermutation,
    best_distance: float,
    best_trips: List[Trip],
    second_permutation: TaskPermutation,
    second_distance: float,
    second_trips: List[Trip],
) -> None:
    if best_distance < state.best_distance:
        state.best_distance = best_distance
        state.best_permutation = best_permutation
        state.best_trips = best_trips

    if second_distance < float("inf"):
        state.second_best_distance = second_distance
        state.second_best_permutation = second_permutation
        state.second_best_trips = second_trips


def initialize_vehicle_genetic(
    vehicle_id: int,
    tasks: List[DeliveryTask],
    road_network: RoadNetwork,
    population_size: int = 100,
    rng: Optional[random.Random] = None,
) -> VehicleGeneticState:
    random_source = rng or random.Random()
    population = _generate_random_population(tasks, population_size, random_source)
    (
        _fitness_values,
        best_permutation,
        best_distance,
        best_trips,
        second_permutation,
        second_distance,
        second_trips,
    ) = _evaluate_population(tasks, population, road_network)

    if best_distance == float("inf") and population:
        best_permutation = list(population[0])
        best_distance, best_trips, _report = evaluate_permutation(
            tasks, best_permutation, road_network
        )

    state = VehicleGeneticState(
        vehicle_id=vehicle_id,
        tasks=list(tasks),
        population=population,
        best_distance=best_distance,
        best_permutation=best_permutation,
        best_trips=best_trips,
    )
    _apply_generation_best(
        state,
        best_permutation,
        best_distance,
        best_trips,
        second_permutation,
        second_distance,
        second_trips,
    )
    return state


def run_vehicle_generation(
    state: VehicleGeneticState,
    road_network: RoadNetwork,
    mutation_probability: float,
    population_size: int = 100,
) -> float:
    if not state.tasks:
        state.best_distance = 0.0
        return 0.0

    (
        fitness_values,
        best_permutation,
        best_distance,
        best_trips,
        second_permutation,
        second_distance,
        second_trips,
    ) = _evaluate_population(state.tasks, state.population, road_network)
    sorted_population, sorted_fitness = sort_population_by_fitness(state.population, fitness_values)

    finite_fitness = [value for value in sorted_fitness if value != float("inf")]
    if not finite_fitness:
        return state.best_distance

    _apply_generation_best(
        state,
        best_permutation,
        best_distance,
        best_trips,
        second_permutation,
        second_distance,
        second_trips,
    )

    state.population = evolve_next_generation(
        sorted_population,
        sorted_fitness,
        population_size,
        mutation_probability,
        mutation_type="adjacent",
        n_elite=3,
        use_2opt=False,
    )
    return state.best_distance
