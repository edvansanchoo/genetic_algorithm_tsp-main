# Documentação da API

O modo Web expõe duas interfaces: **WebSocket** para a simulação em tempo real e **REST** para o assistente LLM.

**Base URL (produção):** `http://127.0.0.1:8000`  
**Base URL (desenvolvimento frontend):** `http://127.0.0.1:8000` (WebSocket direto; UI em `http://localhost:5173`)

Documentação interativa automática (OpenAPI/Swagger): `http://127.0.0.1:8000/docs` (após `python web.py`).

---

## WebSocket — Simulação em tempo real

### Endpoint

```
ws://127.0.0.1:8000/ws
```

### Conexão

1. Cliente conecta ao endpoint.
2. Servidor envia imediatamente um `state_update` com o estado completo.
3. A cada frame da simulação (~30 FPS), o servidor envia novo `state_update`.
4. Cliente pode enviar comandos a qualquer momento.

### Mensagens do servidor → cliente

#### `state_update`

Payload principal com todo o estado da simulação.

```json
{
  "type": "state_update",
  "generation": 42,
  "running": true,
  "metrics": {
    "fitness": 1250.5,
    "distance": 1100.0,
    "priority_penalty": 150.5,
    "blocked_penalty": 0.0,
    "population_size": 100,
    "fps": 28.5,
    "total_cost": 1251.0,
    "priority_served_pct": 80
  },
  "params": {
    "mutation": 0.15,
    "priority_weight": 10.0,
    "vehicle_count": 3,
    "capacity": 5,
    "transit_count": 12,
    "param_ranges": {
      "mutation": [0.0, 1.0],
      "priority_weight": [0.0, 100.0],
      "vehicle_count": [1, 5],
      "capacity": [1, 20],
      "transit_count": [1, 30]
    }
  },
  "toggles": {
    "two_opt": false,
    "show_mesh": true
  },
  "focus": {
    "vehicle_id": null,
    "trip_index": null
  },
  "summary": {
    "vehicles_active": 3,
    "vehicles_total": 3,
    "capacity_total": 5,
    "deliveries_done": 15,
    "deliveries_total": 15,
    "trips_total": 6,
    "blocked_nodes": 0
  },
  "map": { "...": "ver seção Mapa abaixo" },
  "plans": { "...": "planos por veículo" },
  "runner_up": {},
  "histories": { "0": [1200, 1180, 1150] },
  "animation": null,
  "routes_panel": [],
  "logs": [
    { "ts": "2026-07-13T19:00:00+00:00", "type": "generation", "message": "Geração 42: ..." }
  ],
  "display": {
    "vehicle_colors_ui": ["#2563eb", "#059669", "#dc2626", "#d97706", "#7c3aed"],
    "elite_pct": 10
  }
}
```

#### `error`

```json
{
  "type": "error",
  "message": "Parâmetro inválido: foo"
}
```

### Comandos do cliente → servidor

O frontend envolve comandos com `type: "command"`. O backend lê apenas os campos de ação.

#### Pausar / retomar

```json
{ "action": "pause" }
{ "action": "resume" }
```

#### Alterar parâmetro

```json
{
  "action": "set_param",
  "key": "mutation",
  "value": 0.25
}
```

| `key` | Descrição |
|-------|-----------|
| `mutation` | Taxa de mutação (0.0–1.0) |
| `priority_weight` | Peso da penalidade de prioridade |
| `vehicle_count` | Número de veículos |
| `capacity` | Capacidade por veículo |
| `transit_count` | Nós de trânsito na malha |

#### Alternar toggle

```json
{
  "action": "set_toggle",
  "key": "two_opt",
  "active": true
}
```

| `key` | Descrição |
|-------|-----------|
| `two_opt` | Ativa melhoria 2-opt nas rotas |
| `show_mesh` | Exibe malha de ruas no mapa |

#### Ações de cenário

```json
{ "action": "action", "name": "shuffle_positions" }
{ "action": "action", "name": "hospital_preset" }
{ "action": "action", "name": "restart_algorithm" }
{ "action": "action", "name": "clear_blocked" }
```

#### Focar veículo / viagem

```json
{ "action": "set_focus", "vehicle_id": 1, "trip_index": 2 }
{ "action": "set_focus", "vehicle_id": null }
```

#### Bloquear nó no mapa

Coordenadas em pixels do mapa (mesmo sistema do clique no canvas).

```json
{
  "action": "toggle_blocked",
  "map_x": 450,
  "map_y": 320
}
```

### Objeto `map`

```json
{
  "bounds": [0, 0, 1200, 800],
  "depot": [600.0, 400.0],
  "deliveries": [
    {
      "id": "A",
      "x": 120.0,
      "y": 200.0,
      "priority": 9,
      "demand": 2,
      "color": "#dc2626"
    }
  ],
  "mesh": {
    "edges": [[x1, y1, x2, y2]],
    "transit_nodes": [[x, y]],
    "blocked": [[x, y]]
  },
  "theme": {
    "vehicle_colors": ["#..."],
    "depot_color": "#...",
    "mesh_edge_color": "#...",
    "transit_color": "#...",
    "blocked_color": "#...",
    "background_map": "#...",
    "route_second_best": "#..."
  }
}
```

### Objeto `plans`

Chave = ID do veículo (string).

```json
{
  "1": {
    "distance": 450.5,
    "load": 8,
    "capacity": 5,
    "priority_penalty": 42.0,
    "fitness": 492.5,
    "trips": [
      {
        "index": 1,
        "stops": ["D", "A", "B", "D"],
        "load": 4,
        "polylines": [[[x, y], [x, y]]]
      }
    ]
  }
}
```

`"D"` representa o depósito.

---

## REST — Assistente LLM

Prefixo: `/api/llm`

Requer Ollama em execução (`ollama serve`) e modelo configurado (ver `.env.example`).

### `GET /api/llm/health`

Verifica conectividade e disponibilidade do modelo.

**Resposta 200:**

```json
{
  "ok": true,
  "model": "gemma4:e2b",
  "message": "ok"
}
```

**Resposta 200 (modelo ausente):**

```json
{
  "ok": false,
  "model": "gemma4:e2b",
  "message": "Modelo 'gemma4:e2b' não encontrado. Execute: ollama pull gemma4:e2b"
}
```

**Erros:**

| Status | Condição |
|--------|----------|
| 503 | Ollama offline |
| 504 | Timeout de conexão |

---

### `POST /api/llm/generate`

Gera conteúdo estruturado com base no estado atual da simulação.

**Corpo:**

```json
{
  "type": "instructions",
  "vehicle_id": 1
}
```

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `type` | string | sim | `instructions`, `daily_report`, `weekly_report`, `improvements` |
| `vehicle_id` | int | não | Filtra contexto para um veículo (`instructions`) |

**Resposta 200:**

```json
{
  "type": "instructions",
  "content": "## Instruções — Veículo 1\n\n..."
}
```

---

### `POST /api/llm/chat`

Chat em linguagem natural sobre rotas e entregas.

**Corpo:**

```json
{
  "message": "Qual veículo tem a rota mais longa?",
  "history": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ]
}
```

| Campo | Tipo | Obrigatório |
|-------|------|-------------|
| `message` | string | sim (min 1 caractere) |
| `history` | array | não (padrão: `[]`) |

**Resposta 200:**

```json
{
  "reply": "O veículo 2 possui a maior distância...",
  "history": [
    { "role": "user", "content": "Qual veículo..." },
    { "role": "assistant", "content": "O veículo 2..." }
  ]
}
```

---

### `POST /api/llm/export`

Exporta conteúdo Markdown como arquivo.

**Corpo:**

```json
{
  "content": "# Relatório\n\nConteúdo em Markdown...",
  "format": "md",
  "filename": "relatorio-vrp"
}
```

| Campo | Tipo | Padrão | Descrição |
|-------|------|--------|-----------|
| `content` | string | — | Texto Markdown |
| `format` | `"md"` \| `"pdf"` | `"md"` | Formato de saída |
| `filename` | string | `"relatorio-vrp"` | Nome sem extensão |

**Resposta:** arquivo binário com header `Content-Disposition: attachment`.

| Status | Condição |
|--------|----------|
| 501 | PDF solicitado sem WeasyPrint (`pip install -r requirements-llm.txt`) |

---

## Variáveis de ambiente (LLM)

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | URL do Ollama |
| `OLLAMA_MODEL` | `gemma4:e2b` | Modelo local |
| `OLLAMA_TIMEOUT` | `120` | Timeout em segundos |
| `LLM_MAX_CONTEXT_TOKENS` | `2000` | Limite de contexto |

---

## CORS

Em desenvolvimento, o backend aceita origens:

- `http://localhost:5173`
- `http://127.0.0.1:5173`

---

## Exemplo rápido (Python)

```python
import asyncio
import json
import websockets

async def main():
    async with websockets.connect("ws://127.0.0.1:8000/ws") as ws:
        state = json.loads(await ws.recv())
        print(f"Geração: {state['generation']}")

        await ws.send(json.dumps({"action": "pause"}))
        await ws.recv()

asyncio.run(main())
```

Script completo: [`demos/demonstrate_web_api.py`](../demos/demonstrate_web_api.py).
