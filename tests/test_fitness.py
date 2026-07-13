"""Testes de cálculo de fitness e penalidade de prioridade."""

from traveling_salesman_problem.genetic_algorithm.fitness import (
    calculate_euclidean_distance,
    calculate_priority_penalty,
    calculate_route_distance,
    calculate_route_fitness,
    decompose_route_fitness,
)


def test_euclidean_distance():
    assert calculate_euclidean_distance((0, 0), (3, 4)) == 5.0


def test_route_distance_closed_loop():
    route = [(0, 0), (3, 0), (3, 4)]
    distance = calculate_route_distance(route)
    assert distance == 3.0 + 4.0 + 5.0


def test_priority_penalty_weights_early_positions():
    cities = [(0, 0), (10, 0), (20, 0)]
    priorities = [10, 1, 1]
    route = [(0, 0), (10, 0), (20, 0)]
    penalty = calculate_priority_penalty(route, cities, priorities)
    assert penalty == 10 * 1 + 1 * 2 + 1 * 3


def test_route_fitness_without_priority_weight():
    route = [(0, 0), (1, 0), (1, 1)]
    fitness = calculate_route_fitness(route, priority_weight=0.0)
    assert fitness == calculate_route_distance(route)


def test_decompose_route_fitness_splits_components():
    cities = [(0, 0), (5, 0)]
    priorities = [5, 1]
    route = [(0, 0), (5, 0)]
    total, distance, weighted = decompose_route_fitness(
        route,
        city_coordinates=cities,
        priorities=priorities,
        priority_weight=2.0,
    )
    assert distance == 10.0  # ciclo fechado: ida + volta ao depósito
    assert weighted == 2.0 * (5 * 1 + 1 * 2)
    assert total == distance + weighted