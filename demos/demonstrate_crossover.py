"""Demonstração isolada do operador de cruzamento Order Crossover."""

from traveling_salesman_problem.genetic_algorithm.crossover import order_crossover


def main() -> None:
    first_parent = [
        (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6),
    ]
    second_parent = [
        (6, 6), (5, 5), (4, 4), (3, 3), (2, 2), (1, 1),
    ]

    child_route = order_crossover(first_parent, second_parent)

    print("Primeiro pai:", first_parent)
    print("Segundo pai:", second_parent)
    print("Filho gerado:", child_route)


if __name__ == "__main__":
    main()
