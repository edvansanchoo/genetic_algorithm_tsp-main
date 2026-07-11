"""População genética por veículo (permutações de DeliveryToken)."""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from traveling_salesman_problem.problem.delivery_mesh import DeliveryMesh
from traveling_salesman_problem.problem.vrp_decoder import (
    DecodedVehiclePlan,
    decode_vehicle_permutation,
)
from traveling_salesman_problem.problem.vrp_models import Coordinate, DeliveryToken

TokenRoute = List[DeliveryToken]


def plan_has_drawable_trips(plan: Optional[DecodedVehiclePlan]) -> bool:
    if plan is None:
        return False
    return any(len(trip.stops) >= 2 for trip in plan.trips)


def _should_replace_best_plan(
    candidate_fitness: float,
    candidate_plan: DecodedVehiclePlan,
    current_fitness: float,
    current_plan: Optional[DecodedVehiclePlan],
) -> bool:
    candidate_drawable = plan_has_drawable_trips(candidate_plan)
    current_drawable = plan_has_drawable_trips(current_plan)
    if candidate_drawable and not current_drawable:
        return True
    if not candidate_drawable:
        return False
    return candidate_fitness < current_fitness


def select_runner_up_plan(
    evaluated: List[Tuple[float, TokenRoute, DecodedVehiclePlan]],
    best_permutation: TokenRoute,
    best_fitness: float,
) -> Optional[DecodedVehiclePlan]:
    for index in range(1, len(evaluated)):
        fitness, permutation, plan = evaluated[index]
        if not plan_has_drawable_trips(plan):
            continue
        if permutation != best_permutation or fitness > best_fitness:
            return plan
    return None


def _pick_best_evaluated(
    evaluated: List[Tuple[float, TokenRoute, DecodedVehiclePlan]],
) -> Tuple[float, TokenRoute, DecodedVehiclePlan]:
    for item in evaluated:
        if plan_has_drawable_trips(item[2]):
            return item
    return evaluated[0]


def _sample_drawable_permutation(
    tokens: List[DeliveryToken],
    depot: Coordinate,
    mesh: DeliveryMesh,
    capacity: int,
    priority_weight: float,
    max_attempts: int = 400,
) -> Optional[Tuple[TokenRoute, DecodedVehiclePlan]]:
    if not tokens:
        return None
    for _ in range(max_attempts):
        permutation = list(tokens)
        random.shuffle(permutation)
        plan = _evaluate(
            permutation,
            tokens,
            depot,
            mesh,
            capacity,
            priority_weight,
        )
        if plan_has_drawable_trips(plan):
            return permutation, plan
    return None


def order_crossover_tokens(
    first_parent: TokenRoute,
    second_parent: TokenRoute,
) -> TokenRoute:
    route_length = len(first_parent)
    if route_length == 0:
        return []
    if route_length == 1:
        return list(first_parent)

    start_index = random.randint(0, route_length - 1)
    end_index = random.randint(start_index + 1, route_length)

    child_route: TokenRoute = list(first_parent[start_index:end_index])
    used = {(token.point_id, token.quantity, index) for index, token in enumerate(child_route)}
    # Multiset-safe: consume tokens from second parent by (point_id, quantity)
    remaining_from_second: TokenRoute = []
    child_bag = list(child_route)
    for token in second_parent:
        matched = False
        for index, kept in enumerate(child_bag):
            if kept.point_id == token.point_id and kept.quantity == token.quantity:
                del child_bag[index]
                matched = True
                break
        if not matched:
            remaining_from_second.append(token)

    remaining_positions = [
        index
        for index in range(route_length)
        if index < start_index or index >= end_index
    ]
    result: TokenRoute = [None] * route_length  # type: ignore[list-item]
    for offset, token in enumerate(first_parent[start_index:end_index]):
        result[start_index + offset] = token
    for position, token in zip(remaining_positions, remaining_from_second):
        result[position] = token
    if any(item is None for item in result):
        return list(first_parent)
    return result


def mutate_tokens(
    route: TokenRoute,
    mutation_probability: float,
) -> TokenRoute:
    mutated = list(route)
    if random.random() >= mutation_probability or len(mutated) < 2:
        return mutated
    swap_index = random.randint(0, len(mutated) - 2)
    mutated[swap_index], mutated[swap_index + 1] = (
        mutated[swap_index + 1],
        mutated[swap_index],
    )
    return mutated


@dataclass
class VehicleGeneticState:
    vehicle_id: int
    tokens: List[DeliveryToken]
    population: List[TokenRoute]
    best_permutation: List[DeliveryToken] = field(default_factory=list)
    best_fitness: float = float("inf")
    best_plan: Optional[DecodedVehiclePlan] = None
    runner_up_plan: Optional[DecodedVehiclePlan] = None
    fitness_history: List[float] = field(default_factory=list)


def _evaluate(
    permutation: TokenRoute,
    tokens: List[DeliveryToken],
    depot: Coordinate,
    mesh: DeliveryMesh,
    capacity: int,
    priority_weight: float,
) -> DecodedVehiclePlan:
    return decode_vehicle_permutation(
        tokens,
        permutation,
        depot,
        mesh,
        capacity,
        priority_weight,
    )


def initialize_vehicle_genetic(
    vehicle_id: int,
    tokens: List[DeliveryToken],
    population_size: int,
    depot: Coordinate,
    mesh: DeliveryMesh,
    capacity: int,
    priority_weight: float,
) -> VehicleGeneticState:
    if not tokens:
        empty = VehicleGeneticState(
            vehicle_id=vehicle_id,
            tokens=[],
            population=[[] for _ in range(max(1, population_size))],
            best_permutation=[],
            best_fitness=0.0,
            best_plan=DecodedVehiclePlan([], 0.0, 0.0, 0.0),
        )
        empty.fitness_history.append(0.0)
        return empty

    population: List[TokenRoute] = []
    drawable_seed = _sample_drawable_permutation(
        tokens,
        depot,
        mesh,
        capacity,
        priority_weight,
    )
    if drawable_seed is not None:
        population.append(list(drawable_seed[0]))

    while len(population) < population_size:
        individual = list(tokens)
        random.shuffle(individual)
        population.append(individual)

    evaluated = []
    for individual in population:
        plan = _evaluate(
            individual,
            tokens,
            depot,
            mesh,
            capacity,
            priority_weight,
        )
        evaluated.append((plan.fitness, individual, plan))
    evaluated.sort(key=lambda item: item[0])

    best_fitness, best_permutation, best_plan = _pick_best_evaluated(evaluated)
    state = VehicleGeneticState(
        vehicle_id=vehicle_id,
        tokens=list(tokens),
        population=population,
        best_permutation=list(best_permutation),
        best_fitness=best_fitness,
        best_plan=best_plan,
        runner_up_plan=select_runner_up_plan(evaluated, best_permutation, best_fitness),
    )
    state.fitness_history.append(best_fitness)
    return state


def run_vehicle_generation(
    state: VehicleGeneticState,
    depot: Coordinate,
    mesh: DeliveryMesh,
    capacity: int,
    priority_weight: float,
    mutation_probability: float,
    use_2opt: bool = False,
    n_elite: int = 2,
) -> VehicleGeneticState:
    del use_2opt  # reserved; decoder-aware 2-opt deferred
    if not state.tokens:
        state.fitness_history.append(0.0)
        return state

    evaluated = []
    for individual in state.population:
        plan = _evaluate(
            individual,
            state.tokens,
            depot,
            mesh,
            capacity,
            priority_weight,
        )
        evaluated.append((plan.fitness, individual, plan))
    evaluated.sort(key=lambda item: item[0])

    best_fitness, best_permutation, best_plan = _pick_best_evaluated(evaluated)
    if _should_replace_best_plan(
        best_fitness,
        best_plan,
        state.best_fitness,
        state.best_plan,
    ):
        state.best_fitness = best_fitness
        state.best_permutation = list(best_permutation)
        state.best_plan = best_plan
    state.runner_up_plan = select_runner_up_plan(
        evaluated,
        state.best_permutation,
        state.best_fitness,
    )
    state.fitness_history.append(state.best_fitness)

    population_size = len(state.population)
    sorted_population = [individual for _, individual, _ in evaluated]
    fitness_values = [
        fitness if fitness != float("inf") else 1e18 for fitness, _, _ in evaluated
    ]

    new_population: List[TokenRoute] = [
        list(individual) for individual in sorted_population[: max(1, n_elite)]
    ]

    while len(new_population) < population_size:
        weights = [1.0 / value for value in fitness_values]
        first_parent, second_parent = random.choices(
            sorted_population,
            weights=weights,
            k=2,
        )
        child = order_crossover_tokens(first_parent, second_parent)
        child = mutate_tokens(child, mutation_probability)
        new_population.append(child)

    state.population = new_population
    return state
