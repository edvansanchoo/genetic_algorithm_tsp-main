"""Demonstração do preset hospitalar de prioridades."""

from traveling_salesman_problem.problem.priority_presets import apply_hospital_priority_preset


def priority_label(value: int) -> str:
    if value >= 8:
        return "CRÍTICA"
    if value >= 5:
        return "MÉDIA"
    return "BAIXA"


def main() -> None:
    count = 15
    priorities = apply_hospital_priority_preset(count)

    print("=== Preset Hospitalar de Prioridades ===\n")
    print(f"Entregas: {count}  |  Seed fixa: 42 (resultado determinístico)\n")

    buckets = {"CRÍTICA": 0, "MÉDIA": 0, "BAIXA": 0}
    for index, value in enumerate(priorities, start=1):
        label = priority_label(value)
        buckets[label] += 1
        print(f"  Entrega {index:2d}: prioridade {value:2d}  [{label}]")

    print("\nDistribuição:")
    for label, total in buckets.items():
        pct = total / count * 100
        print(f"  {label:8s}: {total:2d} ({pct:.0f}%)")


if __name__ == "__main__":
    main()
