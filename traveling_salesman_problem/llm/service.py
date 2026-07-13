"""Orquestração de geração e chat LLM."""

from __future__ import annotations

from typing import List, Optional

from traveling_salesman_problem.llm.context_builder import build_route_context, context_to_json
from traveling_salesman_problem.llm.ollama_client import OllamaClient
from traveling_salesman_problem.llm.prompts import GenerateType, build_messages


class LlmService:
    def __init__(self, simulation_service, ollama_client: OllamaClient) -> None:
        self._sim = simulation_service
        self._ollama = ollama_client

    def _build_context(self, vehicle_id: Optional[int] = None) -> str:
        context = build_route_context(
            simulation=self._sim.simulation,
            generation_number=self._sim.generation_number,
            total_fitness=self._sim.total_fitness,
            total_distance=self._sim.total_distance,
            total_priority=self._sim.total_priority,
            plans=self._sim.plans,
            session_history=self._sim.session_history,
            vehicle_id=vehicle_id,
        )
        return context_to_json(context)

    async def generate(
        self,
        generate_type: GenerateType,
        vehicle_id: Optional[int] = None,
    ) -> dict:
        context_json = self._build_context(vehicle_id=vehicle_id)
        messages = build_messages(generate_type, context_json)
        content = await self._ollama.chat(messages)
        return {"type": generate_type, "content": content}

    async def chat(self, message: str, history: Optional[List[dict]] = None) -> dict:
        context_json = self._build_context()
        messages = build_messages(
            "chat",
            context_json,
            user_message=message,
            history=history or [],
        )
        reply = await self._ollama.chat(messages)
        updated = list(history or [])
        updated.append({"role": "user", "content": message})
        updated.append({"role": "assistant", "content": reply})
        return {"reply": reply, "history": updated}

    async def health(self) -> dict:
        return await self._ollama.health_check()
