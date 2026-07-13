"""Demonstração do cálculo de fitness com e sem penalidade de prioridade."""

from traveling_salesman_problem.genetic_algorithm.fitness import (
    build_delivery_visit_order,
    calculate_priority_penalty,
    decompose_route_fitness,
)


def main() -> None:
    cities = [(100, 100), (300, 100), (500, 100), (700, 100)]
    priorities = [10, 3, 5, 1]
    route = list(cities)

    print("=== Demonstração de Fitness ===\n")
    print(f"Cidades:     {cities}")
    print(f"Prioridades: {priorities}")
    print(f"Rota:        {route}\n")

    penalty = calculate_priority_penalty(route, cities, priorities)
    print(f"Penalidade de prioridade (bruta): {penalty:.1f}")
    print("  (entregas críticas no início da rota reduzem a penalidade)\n")

    for weight in (0.0, 1.0, 5.0):
        total, distance, weighted = decompose_route_fitness(
            route,
            city_coordinates=cities,
            priorities=priorities,
            priority_weight=weight,
        )
        print(f"Peso prioridade = {weight:4.1f} → fitness = {total:8.1f}  "
              f"(dist={distance:.1f}, prior_pond={weighted:.1f})")

    print("\nOrdem de visita:")
    for position, city_num, priority in build_delivery_visit_order(
        route, cities, priorities
    ):
        print(f"  Posição {position}: cidade {city_num}, prioridade {priority}")


if __name__ == "__main__":
    main()
