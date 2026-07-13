"""Orquestração da simulação no modo Web."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Dict, List, Optional

from traveling_salesman_problem.config.application_settings import ApplicationSettings
from traveling_salesman_problem.simulation.simulation_state import SimulationState
from traveling_salesman_problem.visualization.route_animation import (
    TripAnimationState,
    advance_trip_animation,
)
from traveling_salesman_problem.llm.session_history import SessionHistory
from traveling_salesman_problem.web.command_handler import CommandHandler
from traveling_salesman_problem.web.log_buffer import LogBuffer
from traveling_salesman_problem.web.state_serializer import _priority_served_pct, serialize_state

BroadcastFn = Callable[[dict], Awaitable[None]]


@dataclass
class SimulationService:
    settings: ApplicationSettings = field(default_factory=ApplicationSettings)
    paused: bool = False
    simulation: SimulationState = field(default_factory=SimulationState)
    logs: LogBuffer = field(default_factory=LogBuffer)
    animation_state: TripAnimationState = field(default_factory=TripAnimationState)
    command_handler: CommandHandler | None = None
    session_history: SessionHistory = field(default_factory=SessionHistory)

    generation_number: int = 0
    total_fitness: float = 0.0
    total_distance: float = 0.0
    total_priority: float = 0.0
    plans: Dict = field(default_factory=dict)
    runner_up_plans: Dict = field(default_factory=dict)
    histories: Dict = field(default_factory=dict)
    animation_payload: Optional[dict] = None
    active_trip_index: Optional[int] = None

    _last_frame_time: float = field(default_factory=time.perf_counter)
    _fps: float = 0.0

    def startup(self) -> None:
        self.simulation = SimulationState(settings=self.settings)
        self.simulation.initialize_headless()
        self.command_handler = CommandHandler(self.simulation, self.logs)
        self.logs.append("event", "Simulação Web iniciada")

    def handle_command(self, command: dict) -> Optional[str]:
        action = command.get("action")
        if action == "pause":
            self.paused = True
            self.logs.append("event", "Simulação pausada")
            return None
        if action == "resume":
            self.paused = False
            self.logs.append("event", "Simulação retomada")
            return None
        if self.command_handler is None:
            return "Serviço não inicializado"
        return self.command_handler.handle(command)

    def build_state_payload(self) -> dict:
        return serialize_state(
            self.simulation,
            generation_number=self.generation_number,
            total_fitness=self.total_fitness,
            total_distance=self.total_distance,
            total_priority=self.total_priority,
            plans=self.plans,
            runner_up_plans=self.runner_up_plans,
            histories=self.histories,
            running=not self.paused,
            fps=self._fps,
            animation=self.animation_payload,
            logs=self.logs.snapshot(),
        )

    def _store_generation_result(self, result: tuple) -> None:
        (
            self.generation_number,
            self.total_fitness,
            self.total_distance,
            self.total_priority,
            self.plans,
            self.runner_up_plans,
            self.histories,
        ) = result

    def _format_generation_log(self, result: tuple) -> str:
        generation_number, fitness, distance, priority, *_ = result
        return (
            f"Geração {generation_number}: fitness={round(fitness, 2)} "
            f"dist={round(distance, 2)} prior={round(priority, 2)}"
        )

    def _advance_animation(self, dt_seconds: float) -> None:
        self.animation_payload = None
        self.active_trip_index = None
        focus_id = self.simulation.focus_vehicle_id
        if focus_id is None or focus_id not in self.plans or self.simulation.mesh is None:
            return
        cursor, active_trip_index = advance_trip_animation(
            self.animation_state,
            self.simulation.mesh,
            self.plans[focus_id],
            dt_seconds,
            locked_trip_index=self.simulation.focus_trip_index,
            speed=0.12,
        )
        self.active_trip_index = active_trip_index
        if cursor is not None:
            self.animation_payload = {
                "vehicle_id": focus_id,
                "position": [float(cursor[0]), float(cursor[1])],
                "trip_index": active_trip_index,
            }

    async def run_loop(
        self,
        broadcast: BroadcastFn,
        *,
        max_ticks: int | None = None,
    ) -> None:
        ticks = 0
        while max_ticks is None or ticks < max_ticks:
            now = time.perf_counter()
            dt_seconds = now - self._last_frame_time
            self._last_frame_time = now
            if dt_seconds > 0:
                self._fps = 1.0 / dt_seconds

            if not self.paused:
                result = self.simulation.run_one_generation()
                self._store_generation_result(result)
                generation_number, fitness, distance, priority, plans, *_ = result
                priority_pct = _priority_served_pct(self.simulation, plans)
                blocked = (
                    len(self.simulation.mesh.blocked_ids)
                    if self.simulation.mesh
                    else 0
                )
                vehicle_count = self.simulation.vehicle_count_slider.integer_value
                self.session_history.record_if_improved(
                    generation_number,
                    fitness,
                    distance,
                    priority_pct,
                    blocked,
                    vehicle_count,
                )
                self.logs.append("generation", self._format_generation_log(result))

            self._advance_animation(dt_seconds)
            await broadcast(self.build_state_payload())
            await asyncio.sleep(1 / self.settings.frames_per_second)
            ticks += 1
