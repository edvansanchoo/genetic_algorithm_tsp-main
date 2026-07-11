"""Tratamento de comandos WebSocket para a simulação."""

from __future__ import annotations

from typing import Optional

from traveling_salesman_problem.simulation.simulation_state import SimulationState
from traveling_salesman_problem.web.headless_controls import HeadlessSlider
from traveling_salesman_problem.web.log_buffer import LogBuffer

PARAM_KEYS = {
    "mutation": "mutation_slider",
    "priority_weight": "priority_weight_slider",
    "vehicle_count": "vehicle_count_slider",
    "capacity": "capacity_slider",
    "transit_count": "transit_count_slider",
}

TOGGLE_KEYS = {
    "two_opt": "two_opt_toggle",
    "show_mesh": "mesh_toggle",
}


class CommandHandler:
    def __init__(self, simulation: SimulationState, logs: LogBuffer) -> None:
        self.simulation = simulation
        self.logs = logs

    def handle(self, command: dict) -> Optional[str]:
        action = command.get("action")
        if action == "set_param":
            return self._set_param(command.get("key"), command.get("value"))
        if action == "set_toggle":
            return self._set_toggle(command.get("key"), command.get("active"))
        if action == "action":
            return self._run_action(command.get("name"))
        if action == "set_focus":
            return self._set_focus(command.get("vehicle_id"), command.get("trip_index"))
        if action == "toggle_blocked":
            return self._toggle_blocked(command.get("map_x"), command.get("map_y"))
        if action in ("pause", "resume"):
            return None
        return f"Ação desconhecida: {action}"

    def _set_param(self, key: object, value: object) -> Optional[str]:
        if key not in PARAM_KEYS or value is None:
            return f"Parâmetro inválido: {key}"
        slider_name = PARAM_KEYS[key]
        slider = getattr(self.simulation, slider_name)
        if not isinstance(slider, HeadlessSlider):
            return f"Controle inválido para parâmetro: {key}"
        slider.value = float(value)
        self.simulation.update_controls_if_changed()
        self.logs.append("param", f"{key}={slider.value}")
        return None

    def _set_toggle(self, key: object, active: object) -> Optional[str]:
        if key not in TOGGLE_KEYS or active is None:
            return f"Toggle inválido: {key}"
        toggle = getattr(self.simulation, TOGGLE_KEYS[key])
        toggle.is_active = bool(active)
        if key == "show_mesh":
            self.simulation.show_mesh = bool(active)
        self.simulation.update_controls_if_changed()
        self.logs.append("toggle", f"{key}={bool(active)}")
        return None

    def _run_action(self, name: object) -> Optional[str]:
        if name == "shuffle_positions":
            self.simulation.shuffle_all()
            self.logs.append("action", "Sortear posições")
            return None
        if name == "hospital_preset":
            self.simulation.apply_hospital_preset()
            self.logs.append("action", "Cenário hospitalar")
            return None
        if name == "restart_algorithm":
            self.simulation.restart_vehicle_genetic()
            self.logs.append("action", "Reiniciar algoritmo")
            return None
        if name == "clear_blocked":
            self.simulation.clear_all_blocked()
            self.logs.append("action", "Limpar bloqueios")
            return None
        return f"Ação desconhecida: {name}"

    def _set_focus(self, vehicle_id: object, trip_index: object) -> Optional[str]:
        if vehicle_id is None:
            self.simulation.focus_vehicle_id = None
            self.simulation.focus_trip_index = None
        else:
            vehicle_id_int = int(vehicle_id)
            if vehicle_id_int not in self.simulation.vehicle_states:
                return f"Veículo inválido: {vehicle_id_int}"
            if trip_index is None:
                self.simulation.handle_route_panel_selection(vehicle_id_int, "header", None)
            else:
                self.simulation.handle_route_panel_selection(
                    vehicle_id_int,
                    "trip",
                    int(trip_index),
                )
        if self.simulation.focus_filter_button is not None:
            self.simulation.focus_filter_button.label = self.simulation.focus_filter_label()
        return None

    def _toggle_blocked(self, map_x: object, map_y: object) -> Optional[str]:
        if map_x is None or map_y is None:
            return "Coordenadas inválidas para bloqueio"
        changed = self.simulation.toggle_blocked_at((int(float(map_x)), int(float(map_y))))
        if changed:
            self.logs.append("blocked", f"toggle ({map_x}, {map_y})")
        return None
