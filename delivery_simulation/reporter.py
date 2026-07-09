"""Formatação textual dos resultados."""

from delivery_simulation.models import DEPOT_ID, SimulationResult


def count_total_trips(result: SimulationResult) -> int:
    return sum(len(vehicle.trips) for vehicle in result.vehicles)


def _format_stop_chain(stops) -> str:
    parts = []
    for stop in stops:
        if stop.point_id == DEPOT_ID:
            parts.append("D")
        else:
            parts.append(f"{stop.point_id}({stop.items_delivered})")
    return " → ".join(parts)


def format_simulation_result(result: SimulationResult) -> list[str]:
    config = result.config
    lines = [
        "── Configuração ──",
        f"Veículos: {config.vehicle_count} | Pontos: {config.delivery_point_count} | Itens: {config.total_items}",
        "",
        "── Pontos ──",
    ]

    for point in result.delivery_points:
        x, y = point.coordinate
        lines.append(f"{point.id} ({x:.0f}, {y:.0f}): {point.total_items} itens")

    for vehicle in result.vehicles:
        vehicle_distance = sum(trip.distance for trip in vehicle.trips)
        assigned = ", ".join(vehicle.assigned_points) if vehicle.assigned_points else "—"
        lines.extend(
            [
                "",
                f"── Veículo {vehicle.id} ({len(vehicle.trips)} viagens, {vehicle_distance:.0f} px) ──",
                f"Entregas: {assigned}",
            ]
        )
        for trip_index, trip in enumerate(vehicle.trips, start=1):
            route_text = _format_stop_chain(trip.stops)
            lines.append(f"  Viagem {trip_index}: {route_text}  [{trip.distance:.0f} px]")

    lines.extend(["", f"── Total do sistema: {result.total_system_distance:.0f} px ──"])
    return lines
