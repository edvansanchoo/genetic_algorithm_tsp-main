"""Demonstração de gerações headless (sem interface gráfica)."""

from traveling_salesman_problem.simulation.simulation_state import SimulationState


def main() -> None:
    generations = 10
    print("=== Simulação Headless — Algoritmo Genético VRP ===\n")

    state = SimulationState()
    state.initialize_headless()
    print(f"Veículos: {state.vehicle_count_slider.integer_value}")
    print(f"Entregas: {len(state.deliveries)}")
    print(f"Capacidade: {state.capacity_slider.integer_value}\n")
    print(f"{'Geração':>8}  {'Fitness':>12}  {'Distância':>12}  {'Prioridade':>12}")
    print("-" * 50)

    for _ in range(generations):
        gen, fitness, distance, priority, *_ = state.run_one_generation()
        print(f"{gen:8d}  {fitness:12.2f}  {distance:12.2f}  {priority:12.2f}")

    print(f"\n{generations} gerações concluídas (modo headless, sem Pygame).")


if __name__ == "__main__":
    main()
