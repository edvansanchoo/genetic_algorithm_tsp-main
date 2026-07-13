# LLM Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrar Ollama local (`gemma4:e2b`) ao dashboard Web para gerar instruções de motoristas, relatórios diários/semanais, sugestões de melhoria e chat em linguagem natural sobre rotas VRP.

**Architecture:** Novo pacote `traveling_salesman_problem/llm/` com cliente Ollama, construtor de contexto compacto, templates de prompt e histórico de sessão em memória. Endpoints REST `/api/llm/*` no FastAPI (separados do WebSocket). Nova aba "Assistente" no Vue com chat, botões de geração e exportação MD/PDF.

**Tech Stack:** Python 3.9+, FastAPI, httpx, markdown; Vue 3, TypeScript, marked; Ollama local. Spec: `docs/superpowers/specs/2026-07-13-llm-integration-design.md`.

## Global Constraints

- **Do not create git commits** unless the user explicitly asks
- **Core intocável:** sem mudanças em GA, crossover, mutation, fitness, VRP decoder
- Desktop `python main.py` deve continuar funcionando
- LLM **somente no backend** — frontend nunca chama Ollama diretamente
- Idioma dos prompts e respostas: **português**
- `OLLAMA_MODEL` default: `gemma4:e2b`
- `OLLAMA_BASE_URL` default: `http://127.0.0.1:11434`
- `OLLAMA_TIMEOUT` default: `120`
- `LLM_MAX_CONTEXT_TOKENS` default: `2000`
- Testes CI **não** dependem de Ollama instalado (mock httpx)
- CSS puro + tokens existentes — sem Tailwind

---

## File map

| File | Responsibility |
|------|----------------|
| Create: `traveling_salesman_problem/llm/__init__.py` | Exporta API pública do pacote |
| Create: `traveling_salesman_problem/llm/config.py` | Lê env vars `OLLAMA_*`, `LLM_*` |
| Create: `traveling_salesman_problem/llm/session_history.py` | Snapshots em memória |
| Create: `traveling_salesman_problem/llm/context_builder.py` | JSON compacto para prompts |
| Create: `traveling_salesman_problem/llm/prompts.py` | Templates system/user |
| Create: `traveling_salesman_problem/llm/ollama_client.py` | Cliente async httpx |
| Create: `traveling_salesman_problem/llm/service.py` | Orquestração generate/chat/export |
| Create: `traveling_salesman_problem/llm/export.py` | MD download + PDF opcional |
| Create: `traveling_salesman_problem/web/llm_routes.py` | Router FastAPI `/api/llm/*` |
| Create: `tests/test_session_history.py` | Testes SessionHistory |
| Create: `tests/test_context_builder.py` | Testes context builder |
| Create: `tests/test_prompts.py` | Testes templates |
| Create: `tests/test_ollama_client.py` | Testes client (mock) |
| Create: `tests/test_llm_service.py` | Testes orquestração (mock) |
| Create: `tests/test_llm_routes.py` | Testes endpoints (mock) |
| Create: `.env.example` | Documenta variáveis |
| Create: `requirements-llm.txt` | weasyprint opcional |
| Create: `frontend/src/composables/useLlmApi.ts` | REST client |
| Create: `frontend/src/components/LlmAssistantPanel.vue` | Container da aba |
| Create: `frontend/src/components/LlmActionBar.vue` | Botões + dropdown veículo |
| Create: `frontend/src/components/LlmOutputViewer.vue` | Render Markdown |
| Create: `frontend/src/components/LlmChatBox.vue` | Chat NL |
| Modify: `requirements.txt` | httpx, markdown |
| Modify: `frontend/package.json` | marked |
| Modify: `traveling_salesman_problem/web/simulation_service.py` | SessionHistory no loop |
| Modify: `traveling_salesman_problem/web/server.py` | CORS + router LLM |
| Modify: `frontend/src/components/TabPanel.vue` | Nova aba Assistente |
| Modify: `README.md` | Seção Ollama + Assistente |

---

### Task 1: Dependências e configuração

**Files:**
- Modify: `requirements.txt`
- Create: `requirements-llm.txt`
- Create: `.env.example`
- Create: `traveling_salesman_problem/llm/__init__.py`
- Create: `traveling_salesman_problem/llm/config.py`
- Test: (config testado indiretamente em Task 2+)

**Interfaces:**
- Produces: `LlmConfig` dataclass com `base_url`, `model`, `timeout`, `max_context_tokens`
- Produces: `load_llm_config() -> LlmConfig`

- [ ] **Step 1: Adicionar dependências Python**

Em `requirements.txt`, adicionar ao final:

```
httpx>=0.27.0
markdown>=3.5.0
```

Criar `requirements-llm.txt`:

```
weasyprint>=62.0
```

- [ ] **Step 2: Criar `.env.example`**

```env
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=gemma4:e2b
OLLAMA_TIMEOUT=120
LLM_MAX_CONTEXT_TOKENS=2000
```

- [ ] **Step 3: Implementar `config.py`**

```python
# traveling_salesman_problem/llm/config.py
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class LlmConfig:
    base_url: str
    model: str
    timeout: float
    max_context_tokens: int


def load_llm_config() -> LlmConfig:
    return LlmConfig(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/"),
        model=os.getenv("OLLAMA_MODEL", "gemma4:e2b"),
        timeout=float(os.getenv("OLLAMA_TIMEOUT", "120")),
        max_context_tokens=int(os.getenv("LLM_MAX_CONTEXT_TOKENS", "2000")),
    )
```

- [ ] **Step 4: Criar `__init__.py`**

```python
# traveling_salesman_problem/llm/__init__.py
from traveling_salesman_problem.llm.config import LlmConfig, load_llm_config

__all__ = ["LlmConfig", "load_llm_config"]
```

- [ ] **Step 5: Verificar import**

Run: `python -c "from traveling_salesman_problem.llm.config import load_llm_config; print(load_llm_config())"`
Expected: `LlmConfig(base_url='http://127.0.0.1:11434', model='gemma4:e2b', ...)`

---

### Task 2: SessionHistory

**Files:**
- Create: `traveling_salesman_problem/llm/session_history.py`
- Test: `tests/test_session_history.py`

**Interfaces:**
- Produces: `Snapshot` dataclass
- Produces: `SessionHistory.record_if_improved(...)`, `latest()`, `all_snapshots()`, `weekly_summary()`, `daily_summary()`, `trend()`

- [ ] **Step 1: Escrever teste que falha**

```python
# tests/test_session_history.py
import unittest

from traveling_salesman_problem.llm.session_history import SessionHistory


class SessionHistoryTests(unittest.TestCase):
    def test_records_only_on_fitness_improvement(self):
        history = SessionHistory(max_entries=10)
        self.assertFalse(history.record_if_improved(
            generation=1, fitness=100.0, distance=50.0,
            priority_served_pct=80, blocked_nodes=0, vehicle_count=2,
        ))
        self.assertEqual(len(history.all_snapshots()), 1)

        self.assertFalse(history.record_if_improved(
            generation=2, fitness=100.0, distance=49.0,
            priority_served_pct=80, blocked_nodes=0, vehicle_count=2,
        ))
        self.assertEqual(len(history.all_snapshots()), 1)

        self.assertTrue(history.record_if_improved(
            generation=3, fitness=90.0, distance=48.0,
            priority_served_pct=85, blocked_nodes=1, vehicle_count=2,
        ))
        self.assertEqual(len(history.all_snapshots()), 2)

    def test_weekly_summary_aggregates(self):
        history = SessionHistory(max_entries=10)
        history.record_if_improved(1, 100.0, 50.0, 80, 0, 2)
        history.record_if_improved(2, 90.0, 45.0, 85, 1, 2)
        summary = history.weekly_summary()
        self.assertEqual(summary["snapshot_count"], 2)
        self.assertEqual(summary["best_fitness"], 90.0)
        self.assertEqual(summary["worst_fitness"], 100.0)

    def test_trend_after_plateau(self):
        history = SessionHistory(max_entries=10)
        history.record_if_improved(1, 100.0, 50.0, 80, 0, 2)
        history.record_if_improved(5, 90.0, 45.0, 85, 0, 2)
        trend = history.trend(current_generation=10, current_fitness=90.0)
        self.assertEqual(trend["geracoes_desde_melhoria"], 5)
        self.assertAlmostEqual(trend["melhoria_fitness"], -10.0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Rodar teste — deve falhar**

Run: `python -m pytest tests/test_session_history.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implementar `session_history.py`**

```python
# traveling_salesman_problem/llm/session_history.py
from __future__ import annotations

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
        *,
        timestamp: float,
    ) -> bool:
        import time
        ts = timestamp if timestamp else time.time()
        if self._best_fitness is None or fitness < self._best_fitness:
            self._best_fitness = fitness
            self._best_generation = generation
            self._snapshots.append(Snapshot(
                timestamp=ts,
                generation=generation,
                fitness=fitness,
                distance=distance,
                priority_served_pct=priority_served_pct,
                blocked_nodes=blocked_nodes,
                vehicle_count=vehicle_count,
            ))
            if len(self._snapshots) > self.max_entries:
                self._snapshots = self._snapshots[-self.max_entries :]
            return self._snapshots[-1].generation == generation
        return False

    def all_snapshots(self) -> List[Snapshot]:
        return list(self._snapshots)

    def latest(self) -> Optional[Snapshot]:
        return self._snapshots[-1] if self._snapshots else None

    def weekly_summary(self) -> dict:
        snaps = self._snapshots
        if not snaps:
            return {"snapshot_count": 0}
        fitness_values = [s.fitness for s in snaps]
        return {
            "snapshot_count": len(snaps),
            "best_fitness": min(fitness_values),
            "worst_fitness": max(fitness_values),
            "avg_distance": sum(s.distance for s in snaps) / len(snaps),
            "avg_priority_served_pct": sum(s.priority_served_pct for s in snaps) / len(snaps),
            "generations": [s.generation for s in snaps],
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
                {"generation": s.generation, "fitness": s.fitness, "distance": s.distance}
                for s in recent
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
```

> **Nota implementador:** ajustar assinatura de `record_if_improved` para usar `time.time()` internamente (remover kw-only `timestamp` dos call sites) — o teste acima usa chamadas sem timestamp; implementação final:

```python
def record_if_improved(self, generation, fitness, distance, priority_served_pct, blocked_nodes, vehicle_count) -> bool:
    import time
    ...
    ts = time.time()
```

- [ ] **Step 4: Rodar testes — devem passar**

Run: `python -m pytest tests/test_session_history.py -v`
Expected: 3 passed

---

### Task 3: RouteContextBuilder

**Files:**
- Create: `traveling_salesman_problem/llm/context_builder.py`
- Test: `tests/test_context_builder.py`

**Interfaces:**
- Consumes: `SimulationState`, `Dict[int, DecodedVehiclePlan]`, métricas do `SimulationService`, `SessionHistory`
- Produces: `build_route_context(...) -> dict`

- [ ] **Step 1: Escrever teste que falha**

```python
# tests/test_context_builder.py
import unittest

from traveling_salesman_problem.config.application_settings import ApplicationSettings
from traveling_salesman_problem.llm.context_builder import build_route_context
from traveling_salesman_problem.llm.session_history import SessionHistory
from traveling_salesman_problem.simulation.simulation_state import SimulationState


class ContextBuilderTests(unittest.TestCase):
    def setUp(self):
        self.simulation = SimulationState(settings=ApplicationSettings())
        self.simulation.initialize_headless()
        for _ in range(3):
            self.simulation.run_one_generation()
        self.history = SessionHistory()

    def test_builds_required_keys(self):
        result = self.simulation.run_one_generation()
        gen, fitness, distance, priority, plans, *_ = result
        self.history.record_if_improved(
            gen, fitness, distance, 80,
            len(self.simulation.mesh.blocked_ids) if self.simulation.mesh else 0,
            self.simulation.vehicle_count_slider.integer_value,
        )
        ctx = build_route_context(
            simulation=self.simulation,
            generation_number=gen,
            total_fitness=fitness,
            total_distance=distance,
            total_priority=priority,
            plans=plans,
            session_history=self.history,
        )
        self.assertEqual(ctx["cenario"], "hospitalar")
        self.assertIn("metricas", ctx)
        self.assertIn("entregas", ctx)
        self.assertIn("veiculos", ctx)
        self.assertIn("tendencia", ctx)
        self.assertTrue(len(ctx["entregas"]) > 0)
        self.assertTrue(len(ctx["veiculos"]) > 0)

    def test_filters_vehicle_when_requested(self):
        result = self.simulation.run_one_generation()
        _, fitness, distance, priority, plans, *_ = result
        vehicle_id = next(iter(plans.keys()))
        ctx = build_route_context(
            simulation=self.simulation,
            generation_number=1,
            total_fitness=fitness,
            total_distance=distance,
            total_priority=priority,
            plans=plans,
            session_history=SessionHistory(),
            vehicle_id=vehicle_id,
        )
        self.assertEqual(len(ctx["veiculos"]), 1)
        self.assertEqual(ctx["veiculos"][0]["id"], vehicle_id)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Rodar teste — deve falhar**

Run: `python -m pytest tests/test_context_builder.py -v`
Expected: FAIL

- [ ] **Step 3: Implementar `context_builder.py`**

```python
# traveling_salesman_problem/llm/context_builder.py
from __future__ import annotations

import json
from typing import Dict, Optional

from traveling_salesman_problem.llm.session_history import SessionHistory
from traveling_salesman_problem.problem.vrp_decoder import DecodedVehiclePlan
from traveling_salesman_problem.problem.vrp_models import DEPOT_ID
from traveling_salesman_problem.simulation.simulation_state import SimulationState
from traveling_salesman_problem.web.state_serializer import _priority_served_pct


def _serialize_vehicle(vehicle_id: int, plan: DecodedVehiclePlan, capacity: int) -> dict:
    trips = []
    total_load = 0
    for trip in plan.trips:
        stops = ["D" if s.node_id == DEPOT_ID else s.node_id for s in trip.stops]
        load = sum(s.quantity for s in trip.stops if s.node_id != DEPOT_ID)
        total_load += load
        trips.append({"paradas": stops, "carga": load})
    return {
        "id": vehicle_id,
        "distancia": round(plan.total_distance, 2),
        "carga": total_load,
        "capacidade": capacity,
        "viagens": trips,
    }


def build_route_context(
    *,
    simulation: SimulationState,
    generation_number: int,
    total_fitness: float,
    total_distance: float,
    total_priority: float,
    plans: Dict[int, DecodedVehiclePlan],
    session_history: SessionHistory,
    vehicle_id: Optional[int] = None,
) -> dict:
    capacity = simulation.capacity_slider.integer_value
    priority_pct = _priority_served_pct(simulation, plans)
    blocked = len(simulation.mesh.blocked_ids) if simulation.mesh else 0

    deliveries = [
        {
            "id": p.id,
            "prioridade": p.priority,
            "demanda": p.demand,
            "coords": [round(p.coordinate[0], 1), round(p.coordinate[1], 1)],
        }
        for p in simulation.deliveries
    ]

    vehicle_items = sorted(plans.items(), key=lambda item: item[0])
    if vehicle_id is not None:
        vehicle_items = [(vid, pl) for vid, pl in vehicle_items if vid == vehicle_id]

    depot = None
    if simulation.depot is not None:
        depot = [round(simulation.depot[0], 1), round(simulation.depot[1], 1)]

    return {
        "cenario": "hospitalar",
        "geracao": generation_number,
        "metricas": {
            "fitness": round(total_fitness, 2),
            "distancia": round(total_distance, 2),
            "penalidade_prioridade": round(total_priority, 2),
            "prioridade_pct": priority_pct,
        },
        "deposito": depot,
        "entregas": deliveries,
        "veiculos": [_serialize_vehicle(vid, pl, capacity) for vid, pl in vehicle_items],
        "bloqueios": blocked,
        "tendencia": session_history.trend(generation_number, total_fitness),
        "historico_sessao": session_history.daily_summary(),
        "historico_semanal": session_history.weekly_summary(),
    }


def context_to_json(context: dict) -> str:
    return json.dumps(context, ensure_ascii=False, indent=2)
```

- [ ] **Step 4: Rodar testes — devem passar**

Run: `python -m pytest tests/test_context_builder.py -v`
Expected: 2 passed

---

### Task 4: Prompt templates

**Files:**
- Create: `traveling_salesman_problem/llm/prompts.py`
- Test: `tests/test_prompts.py`

**Interfaces:**
- Produces: `GenerateType = Literal["instructions", "daily_report", "weekly_report", "improvements"]`
- Produces: `build_messages(generate_type, context_json, user_message=None, history=None) -> list[dict]`

- [ ] **Step 1: Escrever teste que falha**

```python
# tests/test_prompts.py
import unittest

from traveling_salesman_problem.llm.prompts import build_messages


class PromptsTests(unittest.TestCase):
    def test_instructions_includes_context_and_portuguese(self):
        messages = build_messages("instructions", '{"geracao": 1}')
        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("motorista", messages[0]["content"].lower())
        self.assertIn("CONTEXTO:", messages[1]["content"])
        self.assertIn('{"geracao": 1}', messages[1]["content"])

    def test_chat_includes_user_message(self):
        messages = build_messages(
            "chat",
            "{}",
            user_message="Qual veículo tem mais carga?",
            history=[{"role": "user", "content": "Olá"}],
        )
        roles = [m["role"] for m in messages]
        self.assertIn("user", roles)
        self.assertTrue(any("Qual veículo" in m.get("content", "") for m in messages))

    def test_all_generate_types_have_system_prompt(self):
        for kind in ("instructions", "daily_report", "weekly_report", "improvements"):
            messages = build_messages(kind, "{}")
            self.assertGreater(len(messages[0]["content"]), 50)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Rodar teste — deve falhar**

Run: `python -m pytest tests/test_prompts.py -v`
Expected: FAIL

- [ ] **Step 3: Implementar `prompts.py`**

```python
# traveling_salesman_problem/llm/prompts.py
from __future__ import annotations

from typing import List, Literal, Optional

GenerateType = Literal["instructions", "daily_report", "weekly_report", "improvements"]

_SYSTEM_BASE = (
    "Você é um assistente de logística hospitalar. "
    "Use APENAS os dados do bloco CONTEXTO. "
    "Se a informação não estiver no contexto, diga que não sabe. "
    "Responda em português brasileiro em Markdown estruturado."
)

_PROMPTS: dict[str, str] = {
    "instructions": _SYSTEM_BASE + " Gere instruções passo a passo para motoristas e equipes de entrega, por veículo e por viagem.",
    "daily_report": _SYSTEM_BASE + " Gere um relatório operacional diário com métricas, destaques positivos e alertas.",
    "weekly_report": _SYSTEM_BASE + " Consolide o histórico da sessão em um relatório semanal de eficiência de rotas e uso de recursos.",
    "improvements": _SYSTEM_BASE + " Analise padrões nos dados e sugira melhorias concretas no processo de entregas.",
    "chat": _SYSTEM_BASE + " Responda perguntas sobre rotas, entregas e veículos de forma concisa.",
}


def build_messages(
    kind: str,
    context_json: str,
    *,
    user_message: Optional[str] = None,
    history: Optional[List[dict]] = None,
) -> List[dict]:
    system = _PROMPTS.get(kind, _PROMPTS["chat"])
    messages: List[dict] = [{"role": "system", "content": system}]
    if history:
        messages.extend(history)
    if kind == "chat" and user_message:
        messages.append({
            "role": "user",
            "content": f"CONTEXTO:\n{context_json}\n\nPERGUNTA:\n{user_message}",
        })
    else:
        messages.append({
            "role": "user",
            "content": f"CONTEXTO:\n{context_json}\n\nGere a resposta solicitada.",
        })
    return messages
```

- [ ] **Step 4: Rodar testes — devem passar**

Run: `python -m pytest tests/test_prompts.py -v`
Expected: 3 passed

---

### Task 5: OllamaClient

**Files:**
- Create: `traveling_salesman_problem/llm/ollama_client.py`
- Test: `tests/test_ollama_client.py`

**Interfaces:**
- Consumes: `LlmConfig`
- Produces: `OllamaClient.chat(messages) -> str`, `OllamaClient.health_check() -> dict`
- Produces: `OllamaError`, `OllamaOfflineError`, `OllamaTimeoutError`

- [ ] **Step 1: Escrever teste com mock**

```python
# tests/test_ollama_client.py
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from traveling_salesman_problem.llm.config import LlmConfig
from traveling_salesman_problem.llm.ollama_client import OllamaClient, OllamaOfflineError


class OllamaClientTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.config = LlmConfig(
            base_url="http://127.0.0.1:11434",
            model="gemma4:e2b",
            timeout=30.0,
            max_context_tokens=2000,
        )

    async def test_chat_returns_assistant_content(self):
        client = OllamaClient(self.config)
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "# Instruções\nPasso 1"}}
        mock_response.raise_for_status = MagicMock()

        with patch.object(client._client, "post", new_callable=AsyncMock, return_value=mock_response):
            result = await client.chat([{"role": "user", "content": "teste"}])
        self.assertIn("Instruções", result)

    async def test_health_check_detects_missing_model(self):
        client = OllamaClient(self.config)
        mock_response = MagicMock()
        mock_response.json.return_value = {"models": [{"name": "other:tag"}]}
        mock_response.raise_for_status = MagicMock()

        with patch.object(client._client, "get", new_callable=AsyncMock, return_value=mock_response):
            result = await client.health_check()
        self.assertFalse(result["ok"])
        self.assertIn("gemma4:e2b", result["message"])

    async def test_offline_raises(self):
        client = OllamaClient(self.config)
        with patch.object(client._client, "get", new_callable=AsyncMock, side_effect=ConnectionError()):
            with self.assertRaises(OllamaOfflineError):
                await client.health_check()


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Rodar teste — deve falhar**

Run: `python -m pytest tests/test_ollama_client.py -v`
Expected: FAIL

- [ ] **Step 3: Implementar `ollama_client.py`**

```python
# traveling_salesman_problem/llm/ollama_client.py
from __future__ import annotations

from typing import List

import httpx

from traveling_salesman_problem.llm.config import LlmConfig


class OllamaError(Exception):
    pass


class OllamaOfflineError(OllamaError):
    pass


class OllamaTimeoutError(OllamaError):
    pass


class OllamaClient:
    def __init__(self, config: LlmConfig) -> None:
        self.config = config
        self._client = httpx.AsyncClient(base_url=config.base_url, timeout=config.timeout)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def health_check(self) -> dict:
        try:
            response = await self._client.get("/api/tags")
            response.raise_for_status()
        except (httpx.ConnectError, httpx.NetworkError) as exc:
            raise OllamaOfflineError("Ollama não está rodando. Execute: ollama serve") from exc
        except httpx.TimeoutException as exc:
            raise OllamaTimeoutError("Timeout ao conectar ao Ollama") from exc

        models = response.json().get("models", [])
        names = {m.get("name", "") for m in models}
        model_ok = any(self.config.model in name for name in names)
        if not model_ok:
            return {
                "ok": False,
                "model": self.config.model,
                "message": f"Modelo '{self.config.model}' não encontrado. Execute: ollama pull {self.config.model}",
            }
        return {"ok": True, "model": self.config.model, "message": "ok"}

    async def chat(self, messages: List[dict]) -> str:
        try:
            response = await self._client.post(
                "/api/chat",
                json={"model": self.config.model, "messages": messages, "stream": False},
            )
            response.raise_for_status()
        except (httpx.ConnectError, httpx.NetworkError) as exc:
            raise OllamaOfflineError("Ollama não está rodando. Execute: ollama serve") from exc
        except httpx.TimeoutException as exc:
            raise OllamaTimeoutError("Tempo esgotado aguardando resposta do modelo") from exc

        payload = response.json()
        return payload.get("message", {}).get("content", "").strip()
```

- [ ] **Step 4: Rodar testes — devem passar**

Run: `python -m pytest tests/test_ollama_client.py -v`
Expected: 3 passed

---

### Task 6: LlmService (orquestração)

**Files:**
- Create: `traveling_salesman_problem/llm/service.py`
- Test: `tests/test_llm_service.py`

**Interfaces:**
- Consumes: `SimulationService`, `OllamaClient`, `SessionHistory`
- Produces: `LlmService.generate(type, vehicle_id=None) -> dict`, `LlmService.chat(message, history) -> dict`

- [ ] **Step 1: Escrever teste com mock**

```python
# tests/test_llm_service.py
import unittest
from unittest.mock import AsyncMock, MagicMock

from traveling_salesman_problem.llm.service import LlmService


class LlmServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_generate_instructions(self):
        simulation_service = MagicMock()
        simulation_service.generation_number = 5
        simulation_service.total_fitness = 100.0
        simulation_service.total_distance = 50.0
        simulation_service.total_priority = 10.0
        simulation_service.plans = {}
        simulation_service.simulation = MagicMock()
        simulation_service.session_history = MagicMock()
        simulation_service.session_history.trend.return_value = {"melhoria_fitness": -5, "geracoes_desde_melhoria": 2}
        simulation_service.session_history.daily_summary.return_value = {}
        simulation_service.session_history.weekly_summary.return_value = {}

        ollama = AsyncMock()
        ollama.chat.return_value = "# Instruções"

        service = LlmService(simulation_service, ollama)
        with unittest.mock.patch(
            "traveling_salesman_problem.llm.service.build_route_context",
            return_value={"geracao": 5},
        ):
            result = await service.generate("instructions")
        self.assertEqual(result["type"], "instructions")
        self.assertIn("Instruções", result["content"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Implementar `service.py`**

```python
# traveling_salesman_problem/llm/service.py
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

    async def generate(self, generate_type: GenerateType, vehicle_id: Optional[int] = None) -> dict:
        context_json = self._build_context(vehicle_id=vehicle_id)
        messages = build_messages(generate_type, context_json)
        content = await self._ollama.chat(messages)
        return {"type": generate_type, "content": content}

    async def chat(self, message: str, history: Optional[List[dict]] = None) -> dict:
        context_json = self._build_context()
        messages = build_messages("chat", context_json, user_message=message, history=history or [])
        reply = await self._ollama.chat(messages)
        updated = list(history or [])
        updated.append({"role": "user", "content": message})
        updated.append({"role": "assistant", "content": reply})
        return {"reply": reply, "history": updated}

    async def health(self) -> dict:
        return await self._ollama.health_check()
```

- [ ] **Step 3: Rodar testes — devem passar**

Run: `python -m pytest tests/test_llm_service.py -v`
Expected: 1 passed

---

### Task 7: Integrar SessionHistory no SimulationService

**Files:**
- Modify: `traveling_salesman_problem/web/simulation_service.py`

**Interfaces:**
- Produces: `SimulationService.session_history: SessionHistory`
- Modifies: `run_loop` registra snapshot quando fitness melhora

- [ ] **Step 1: Adicionar SessionHistory ao dataclass**

No topo de `simulation_service.py`, importar:

```python
from traveling_salesman_problem.llm.session_history import SessionHistory
from traveling_salesman_problem.web.state_serializer import _priority_served_pct
```

Adicionar campo ao `@dataclass`:

```python
session_history: SessionHistory = field(default_factory=SessionHistory)
_best_fitness_recorded: Optional[float] = None
```

- [ ] **Step 2: Registrar snapshot após `_store_generation_result`**

Em `run_loop`, após `self._store_generation_result(result)`:

```python
gen, fitness, distance, priority, plans, *_ = result
priority_pct = _priority_served_pct(self.simulation, plans)
blocked = len(self.simulation.mesh.blocked_ids) if self.simulation.mesh else 0
vehicle_count = self.simulation.vehicle_count_slider.integer_value
self.session_history.record_if_improved(
    gen, fitness, distance, priority_pct, blocked, vehicle_count,
)
```

- [ ] **Step 3: Verificar simulação ainda roda**

Run: `python -c "from traveling_salesman_problem.web.simulation_service import SimulationService; s=SimulationService(); s.startup(); print('ok')"`
Expected: `ok`

---

### Task 8: Export MD/PDF

**Files:**
- Create: `traveling_salesman_problem/llm/export.py`

**Interfaces:**
- Produces: `export_markdown(content) -> tuple[bytes, str, str]` (bytes, media_type, filename)
- Produces: `export_pdf(content) -> tuple[bytes, str, str]` ou raises `PdfUnavailableError`

- [ ] **Step 1: Implementar export**

```python
# traveling_salesman_problem/llm/export.py
from __future__ import annotations

import markdown


class PdfUnavailableError(Exception):
    pass


def export_markdown(content: str, filename: str = "relatorio-vrp.md") -> tuple[bytes, str, str]:
    return content.encode("utf-8"), "text/markdown; charset=utf-8", filename


def export_pdf(content: str, filename: str = "relatorio-vrp.pdf") -> tuple[bytes, str, str]:
    try:
        from weasyprint import HTML
    except ImportError as exc:
        raise PdfUnavailableError("WeasyPrint não instalado. Use requirements-llm.txt ou exporte MD.") from exc

    html = markdown.markdown(content, extensions=["tables", "fenced_code"])
    wrapped = f"<!DOCTYPE html><html><head><meta charset='utf-8'></head><body>{html}</body></html>"
    pdf_bytes = HTML(string=wrapped).write_pdf()
    return pdf_bytes, "application/pdf", filename
```

---

### Task 9: REST routes + CORS

**Files:**
- Create: `traveling_salesman_problem/web/llm_routes.py`
- Modify: `traveling_salesman_problem/web/server.py`
- Test: `tests/test_llm_routes.py`

**Interfaces:**
- Produces: `create_llm_router(llm_service: LlmService) -> APIRouter`

- [ ] **Step 1: Escrever teste de rotas**

```python
# tests/test_llm_routes.py
import unittest
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from traveling_salesman_problem.web.llm_routes import create_llm_router


class LlmRoutesTests(unittest.TestCase):
    def setUp(self):
        self.llm_service = MagicMock()
        self.llm_service.health = AsyncMock(return_value={"ok": True, "model": "gemma4:e2b"})
        self.llm_service.generate = AsyncMock(return_value={"type": "instructions", "content": "# OK"})
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(create_llm_router(lambda: self.llm_service))
        self.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/api/llm/health")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])

    def test_generate_endpoint(self):
        response = self.client.post("/api/llm/generate", json={"type": "instructions"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("content", response.json())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Implementar `llm_routes.py`**

```python
# traveling_salesman_problem/web/llm_routes.py
from __future__ import annotations

from typing import Callable, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from traveling_salesman_problem.llm.export import PdfUnavailableError, export_markdown, export_pdf
from traveling_salesman_problem.llm.ollama_client import OllamaOfflineError, OllamaTimeoutError
from traveling_salesman_problem.llm.prompts import GenerateType


class GenerateRequest(BaseModel):
    type: GenerateType
    vehicle_id: Optional[int] = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    history: List[dict] = Field(default_factory=list)


class ExportRequest(BaseModel):
    content: str = Field(min_length=1)
    format: Literal["md", "pdf"] = "md"
    filename: Optional[str] = None


def create_llm_router(get_service: Callable):
    router = APIRouter(prefix="/api/llm", tags=["llm"])

    @router.get("/health")
    async def health(service=Depends(get_service)):
        try:
            return await service.health()
        except OllamaOfflineError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except OllamaTimeoutError as exc:
            raise HTTPException(status_code=504, detail=str(exc)) from exc

    @router.post("/generate")
    async def generate(body: GenerateRequest, service=Depends(get_service)):
        try:
            return await service.generate(body.type, vehicle_id=body.vehicle_id)
        except OllamaOfflineError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except OllamaTimeoutError as exc:
            raise HTTPException(status_code=504, detail=str(exc)) from exc

    @router.post("/chat")
    async def chat(body: ChatRequest, service=Depends(get_service)):
        try:
            return await service.chat(body.message, history=body.history)
        except OllamaOfflineError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except OllamaTimeoutError as exc:
            raise HTTPException(status_code=504, detail=str(exc)) from exc

    @router.post("/export")
    async def export_report(body: ExportRequest):
        name = body.filename or "relatorio-vrp"
        try:
            if body.format == "md":
                data, media_type, filename = export_markdown(body.content, f"{name}.md")
            else:
                data, media_type, filename = export_pdf(body.content, f"{name}.pdf")
        except PdfUnavailableError as exc:
            raise HTTPException(status_code=501, detail=str(exc)) from exc
        return Response(
            content=data,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    return router
```

- [ ] **Step 3: Registrar no `server.py`**

Adicionar imports e CORS:

```python
from fastapi.middleware.cors import CORSMiddleware
from traveling_salesman_problem.llm.config import load_llm_config
from traveling_salesman_problem.llm.ollama_client import OllamaClient
from traveling_salesman_problem.llm.service import LlmService
from traveling_salesman_problem.web.llm_routes import create_llm_router
```

Dentro de `create_app`, após `app = FastAPI(...)`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

llm_config = load_llm_config()
ollama_client = OllamaClient(llm_config)
llm_service = LlmService(service, ollama_client)

@app.on_event("shutdown")
async def shutdown_llm() -> None:
    await ollama_client.aclose()

app.include_router(create_llm_router(lambda: llm_service))
```

- [ ] **Step 4: Rodar testes de rotas**

Run: `python -m pytest tests/test_llm_routes.py -v`
Expected: 2 passed

- [ ] **Step 5: Rodar suite completa**

Run: `python -m pytest tests/ -v --ignore=tests/test_route_animation.py`
Expected: all pass (ajustar ignores se necessário)

---

### Task 10: Frontend — useLlmApi composable

**Files:**
- Create: `frontend/src/composables/useLlmApi.ts`
- Modify: `frontend/package.json`

**Interfaces:**
- Produces: `useLlmApi()` com `health`, `generate`, `chat`, `exportReport`, refs reativos

- [ ] **Step 1: Adicionar `marked`**

Run: `cd frontend && npm install marked`

- [ ] **Step 2: Implementar composable**

```typescript
// frontend/src/composables/useLlmApi.ts
import { ref } from "vue";

const API_BASE = import.meta.env.DEV ? "http://127.0.0.1:8000" : "";

export type GenerateType =
  | "instructions"
  | "daily_report"
  | "weekly_report"
  | "improvements";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export function useLlmApi() {
  const loading = ref(false);
  const error = ref<string | null>(null);
  const lastOutput = ref<string>("");
  const chatHistory = ref<ChatMessage[]>([]);
  const ollamaStatus = ref<{ ok: boolean; model?: string; message?: string } | null>(null);

  async function health() {
    try {
      const res = await fetch(`${API_BASE}/api/llm/health`);
      const data = await res.json();
      ollamaStatus.value = data;
      return data;
    } catch {
      ollamaStatus.value = { ok: false, message: "Backend indisponível" };
      return ollamaStatus.value;
    }
  }

  async function generate(type: GenerateType, vehicleId?: number | null) {
    loading.value = true;
    error.value = null;
    try {
      const res = await fetch(`${API_BASE}/api/llm/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type, vehicle_id: vehicleId ?? null }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? `Erro ${res.status}`);
      }
      const data = await res.json();
      lastOutput.value = data.content ?? "";
      return data;
    } catch (exc) {
      error.value = exc instanceof Error ? exc.message : "Erro desconhecido";
      throw exc;
    } finally {
      loading.value = false;
    }
  }

  async function chat(message: string) {
    loading.value = true;
    error.value = null;
    try {
      const res = await fetch(`${API_BASE}/api/llm/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, history: chatHistory.value }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? `Erro ${res.status}`);
      }
      const data = await res.json();
      chatHistory.value = data.history ?? chatHistory.value;
      return data;
    } catch (exc) {
      error.value = exc instanceof Error ? exc.message : "Erro desconhecido";
      throw exc;
    } finally {
      loading.value = false;
    }
  }

  async function exportReport(content: string, format: "md" | "pdf") {
    const res = await fetch(`${API_BASE}/api/llm/export`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content, format }),
    });
    if (!res.ok) {
      if (res.status === 501 && format === "pdf") {
        window.print();
        return;
      }
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail ?? `Erro ${res.status}`);
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = format === "md" ? "relatorio-vrp.md" : "relatorio-vrp.pdf";
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return {
    loading,
    error,
    lastOutput,
    chatHistory,
    ollamaStatus,
    health,
    generate,
    chat,
    exportReport,
  };
}
```

---

### Task 11: Frontend — componentes LLM

**Files:**
- Create: `frontend/src/components/LlmOutputViewer.vue`
- Create: `frontend/src/components/LlmActionBar.vue`
- Create: `frontend/src/components/LlmChatBox.vue`
- Create: `frontend/src/components/LlmAssistantPanel.vue`

- [ ] **Step 1: `LlmOutputViewer.vue`**

```vue
<script setup lang="ts">
import { computed } from "vue";
import { marked } from "marked";

const props = defineProps<{ content: string }>();
const html = computed(() => marked.parse(props.content || "_Sem conteúdo ainda._"));
</script>

<template>
  <div class="llm-output" v-html="html" />
</template>

<style scoped>
.llm-output {
  background: var(--bg-muted);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 12px;
  font-size: 13px;
  line-height: 1.5;
  max-height: 240px;
  overflow-y: auto;
  color: var(--text-primary);
}
.llm-output :deep(h1), .llm-output :deep(h2), .llm-output :deep(h3) {
  margin: 0.5em 0 0.25em;
  font-size: 1em;
}
.llm-output :deep(ul), .llm-output :deep(ol) {
  padding-left: 1.25em;
}
@media print {
  .llm-output { max-height: none; overflow: visible; border: none; }
}
</style>
```

- [ ] **Step 2: `LlmActionBar.vue`**

Props: `loading`, `disabled`, `vehicleIds: number[]`
Emits: `generate(type, vehicleId?)`

Botões: Instruções (com `<select>` de veículo), Rel. Diário, Rel. Semanal, Sugestões.
Usar `UiButton` existente.

- [ ] **Step 3: `LlmChatBox.vue`**

Props: `loading`, `history: ChatMessage[]`
Emits: `send(message: string)`

Input text + botão Enviar; lista de mensagens user/assistant acima.

- [ ] **Step 4: `LlmAssistantPanel.vue`**

```vue
<script setup lang="ts">
import { computed, onMounted } from "vue";
import type { StateUpdate } from "../types/simulation";
import { useLlmApi } from "../composables/useLlmApi";
import LlmActionBar from "./LlmActionBar.vue";
import LlmOutputViewer from "./LlmOutputViewer.vue";
import LlmChatBox from "./LlmChatBox.vue";
import UiButton from "./ui/UiButton.vue";

const props = defineProps<{ state: StateUpdate | null }>();

const {
  loading, error, lastOutput, chatHistory, ollamaStatus,
  health, generate, chat, exportReport,
} = useLlmApi();

const vehicleIds = computed(() =>
  props.state ? Object.keys(props.state.plans).map(Number).sort((a, b) => a - b) : [],
);
const hasPlans = computed(() => vehicleIds.value.length > 0);
const statusLabel = computed(() =>
  ollamaStatus.value?.ok ? "Ollama conectado" : (ollamaStatus.value?.message ?? "Verificando..."),
);

onMounted(() => health());

async function onGenerate(type: string, vehicleId?: number) {
  await generate(type as any, vehicleId);
}
</script>

<template>
  <div class="llm-panel">
    <div class="llm-status" :class="{ 'llm-status--ok': ollamaStatus?.ok }">
      ● {{ statusLabel }}
    </div>
    <p v-if="!ollamaStatus?.ok" class="llm-banner">
      Execute <code>ollama serve</code> e <code>ollama pull gemma4:e2b</code>
    </p>
    <p class="llm-disclaimer">Respostas baseadas nos dados da simulação. Verifique números críticos.</p>

    <LlmActionBar
      :loading="loading"
      :disabled="!hasPlans || !ollamaStatus?.ok"
      :vehicle-ids="vehicleIds"
      @generate="onGenerate"
    />

    <LlmOutputViewer id="llm-print-area" :content="lastOutput" />

    <div class="llm-export-row">
      <UiButton :disabled="!lastOutput" @click="exportReport(lastOutput, 'md')">Exportar MD</UiButton>
      <UiButton :disabled="!lastOutput" @click="exportReport(lastOutput, 'pdf')">Exportar PDF</UiButton>
    </div>

    <p v-if="error" class="error-text">{{ error }}</p>

    <LlmChatBox :loading="loading" :history="chatHistory" @send="chat" />
  </div>
</template>
```

Adicionar estilos scoped para `.llm-status`, `.llm-banner`, `.llm-disclaimer`, `.llm-export-row`.

---

### Task 12: Integrar aba no TabPanel

**Files:**
- Modify: `frontend/src/components/TabPanel.vue`

- [ ] **Step 1: Adicionar tab e componente**

```typescript
import LlmAssistantPanel from "./LlmAssistantPanel.vue";

const tabs = [
  { id: "resumo", label: "Resumo" },
  { id: "stats", label: "Estatísticas" },
  { id: "history", label: "Histórico" },
  { id: "logs", label: "Logs" },
  { id: "assistente", label: "Assistente" },
];
```

No template, após `LogConsole`:

```vue
<LlmAssistantPanel v-if="activeTab === 'assistente'" :state="state" />
```

- [ ] **Step 2: Build frontend**

Run: `cd frontend && npm run build`
Expected: build succeeds without TypeScript errors

---

### Task 13: Documentação

**Files:**
- Modify: `README.md`
- Modify: `docs/superpowers/specs/2026-07-13-llm-integration-design.md` (status → Implementado)

- [ ] **Step 1: Adicionar seção ao README**

```markdown
## Assistente LLM (Ollama)

Requisitos adicionais:
1. [Ollama](https://ollama.com/) instalado e rodando (`ollama serve`)
2. Modelo: `ollama pull gemma4:e2b`

No dashboard Web, aba **Assistente**:
- Gerar instruções para motoristas
- Relatórios diário/semanal e sugestões de melhoria
- Chat em linguagem natural sobre rotas
- Exportar Markdown ou PDF

Variáveis opcionais: ver `.env.example`.
```

- [ ] **Step 2: Verificação manual**

1. Terminal 1: `python web.py`
2. Terminal 2: `cd frontend && npm run dev`
3. Abrir `http://localhost:5173` → aba Assistente
4. Com Ollama offline: badge vermelho, simulação continua
5. Com Ollama + modelo: gerar instruções → Markdown aparece
6. Chat: perguntar "quantos veículos estão ativos?"
7. Exportar MD → download funciona

- [ ] **Step 3: Suite de testes final**

Run: `python -m pytest tests/test_session_history.py tests/test_context_builder.py tests/test_prompts.py tests/test_ollama_client.py tests/test_llm_service.py tests/test_llm_routes.py -v`
Expected: all passed

---

## Self-Review

| Spec requirement | Task |
|------------------|------|
| Instruções sob demanda | Task 11 (ActionBar) + Task 9 (generate) |
| Relatório diário/semanal | Task 4 (prompts) + Task 2 (SessionHistory) |
| Sugestões de melhoria | Task 4 + Task 9 |
| Chat NL | Task 9 + Task 11 (ChatBox) |
| Prompts eficientes | Task 3 + Task 4 |
| Export MD/PDF | Task 8 + Task 10 + Task 11 |
| Ollama offline graceful | Task 5 + Task 9 + Task 11 |
| Testes sem Ollama | Tasks 2–6, 9 |
| .env.example | Task 1 |
| README | Task 13 |

**Placeholder scan:** nenhum TBD encontrado.

**Type consistency:** `GenerateType`, `LlmService.generate`, `GenerateRequest.type` e `useLlmApi.generate` alinhados.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-13-llm-integration.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks, fast iteration

2. **Inline Execution** — execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
