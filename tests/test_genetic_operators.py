"""Testes dos operadores genéticos (crossover e mutação)."""

from unittest.mock import patch

from traveling_salesman_problem.genetic_algorithm.crossover import order_crossover
from traveling_salesman_problem.genetic_algorithm.mutation import (
    apply_mutation,
    swap_adjacent_cities_mutation,
)


def test_order_crossover_preserves_permutation():
    first_parent = [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6)]
    second_parent = [(6, 6), (5, 5), (4, 4), (3, 3), (2, 2), (1, 1)]

    with patch(
        "traveling_salesman_problem.genetic_algorithm.crossover.random.randint",
        side_effect=[1, 4],
    ):
        child = order_crossover(first_parent, second_parent)

    assert len(child) == len(first_parent)
    assert sorted(child) == sorted(first_parent)
    assert child[1:4] == first_parent[1:4]


def test_adjacent_mutation_skipped_when_random_above_probability():
    route = [(1, 1), (2, 2), (3, 3)]
    with patch("random.random", return_value=0.99):
        result = swap_adjacent_cities_mutation(route, mutation_probability=0.5)
    assert result == route


def test_adjacent_mutation_swaps_neighbors():
    route = [(1, 1), (2, 2), (3, 3), (4, 4)]
    with patch("random.random", return_value=0.0):
        with patch("random.randint", return_value=1):
            result = swap_adjacent_cities_mutation(route, mutation_probability=0.5)
    assert result[1] == (3, 3)
    assert result[2] == (2, 2)


def test_apply_mutation_random_type():
    route = [(10, 10), (20, 20), (30, 30)]
    with patch("random.random", return_value=0.0):
        with patch("random.sample", return_value=[0, 2]):
            result = apply_mutation(route, 0.5, mutation_type="random")
    assert result[0] == (30, 30)
    assert result[2] == (10, 10)
