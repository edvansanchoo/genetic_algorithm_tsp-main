"""Demonstração isolada do operador de mutação."""

from traveling_salesman_problem.genetic_algorithm.mutation import swap_adjacent_cities_mutation


def main() -> None:
    original_route = [(99, 100), (2, 50), (1, 71)]
    mutation_probability = 1.0

    mutated_route = swap_adjacent_cities_mutation(original_route, mutation_probability)

    print("Rota original:", original_route)
    print("Rota mutada:", mutated_route)


if __name__ == "__main__":
    main()
