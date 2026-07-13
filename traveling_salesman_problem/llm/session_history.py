"""Histórico leve de snapshots da sessão de simulação."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Snapshot:
    timestamp: float
    generation: int
    fitness: float
    distance: float
    priority_served_pct: int
    blocked_nodes: int
    vehicle_count: int


@dataclass
class SessionHistory:
    max_entries: int = 500
    _snapshots: List[Snapshot] = field(default_factory=list)
    _best_fitness: Optional[float] = None
    _best_generation: int = 0

    def record_if_improved(
        self,
        generation: int,
        fitness: float,
        distance: float,
        priority_served_pct: int,
        blocked_nodes: int,
        vehicle_count: int,
    ) -> bool:
        if self._best_fitness is None or fitness < self._best_fitness:
            self._best_fitness = fitness
            self._best_generation = generation
            self._snapshots.append(
                Snapshot(
                    timestamp=time.time(),
                    generation=generation,
                    fitness=fitness,
                    distance=distance,
                    priority_served_pct=priority_served_pct,
                    blocked_nodes=blocked_nodes,
                    vehicle_count=vehicle_count,
                )
            )
            if len(self._snapshots) > self.max_entries:
                self._snapshots = self._snapshots[-self.max_entries :]
            return True
        return False

    def all_snapshots(self) -> List[Snapshot]:
        return list(self._snapshots)

    def latest(self) -> Optional[Snapshot]:
        return self._snapshots[-1] if self._snapshots else None

    def weekly_summary(self) -> dict:
        snaps = self._snapshots
        if not snaps:
            return {"snapshot_count": 0}
        fitness_values = [snapshot.fitness for snapshot in snaps]
        return {
            "snapshot_count": len(snaps),
            "best_fitness": min(fitness_values),
            "worst_fitness": max(fitness_values),
            "avg_distance": sum(snapshot.distance for snapshot in snaps) / len(snaps),
            "avg_priority_served_pct": sum(
                snapshot.priority_served_pct for snapshot in snaps
            )
            / len(snaps),
            "generations": [snapshot.generation for snapshot in snaps],
        }

    def daily_summary(self) -> dict:
        latest = self.latest()
        if latest is None:
            return {"snapshot_count": 0}
        recent = self._snapshots[-5:]
        return {
            "snapshot_count": len(self._snapshots),
            "current": {
                "generation": latest.generation,
                "fitness": latest.fitness,
                "distance": latest.distance,
                "priority_served_pct": latest.priority_served_pct,
            },
            "recent_improvements": [
                {
                    "generation": snapshot.generation,
                    "fitness": snapshot.fitness,
                    "distance": snapshot.distance,
                }
                for snapshot in recent
            ],
        }

    def trend(self, current_generation: int, current_fitness: float) -> dict:
        if self._best_fitness is None:
            return {"melhoria_fitness": 0.0, "geracoes_desde_melhoria": 0}
        first = self._snapshots[0].fitness if self._snapshots else current_fitness
        return {
            "melhoria_fitness": round(current_fitness - first, 2),
            "geracoes_desde_melhoria": max(0, current_generation - self._best_generation),
        }
