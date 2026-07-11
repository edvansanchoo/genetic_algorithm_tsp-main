# Design: Interface Web do Simulador VRP Hospitalar

**Data:** 2026-07-11  
**Status:** Aprovado  
**Branch:** atual  
**Commits:** nenhum até pedido explícito do usuário

**Contexto:** O projeto possui apenas interface Pygame (`python main.py`). O documento `melhoria_visual.md` descreve uma segunda interface Web como dashboard profissional, consumindo o mesmo núcleo VRP/GA sem alterá-lo. Esta especificação formaliza a arquitetura e o escopo de implementação.

**Depende de:** Core VRP existente (`SimulationState`, `vehicle_genetic`, `map_renderer`, `route_panel`, `route_animation`).

---

## 1. Objetivo

Adicionar uma **interface Web** ao simulador VRP Hospitalar, mantendo:

1. **Desktop Pygame intacto** — `python main.py` funciona exatamente como hoje.
2. **Core intocável** — GA, VRP, fitness, malha, bloqueios, prioridades permanecem idênticos.
3. **Paridade funcional completa** na v1 — todos os controles e ações do desktop disponíveis na Web, mesmo com visual inicialmente mais simples.

A evolução visual (cards, sombras, referência do dashboard) é **v1.1** (Fase F5).

---

## 2. Regra inviolável: Core intocável

Não alterar:

- Representação genética, cromossomos, população, seleção, crossover, mutação, elitismo
- Cálculo de fitness, distância, penalidades
- Capacidade, divisão em viagens, prioridade, depósito, bloqueios, nós de trânsito
- Geração de rotas e execução da simulação

Adaptações permitidas **somente** na camada de interface/comunicação:

- Controles headless (substituem widgets Pygame no modo Web)
- `initialize_headless()` em `SimulationState` (novo método, desktop inalterado)
- Serialização de estado para JSON
- Servidor FastAPI + WebSocket

---

## 3. Decisões validadas (brainstorming)

| Tópico | Decisão |
|--------|---------|
| Prioridade v1 | **B** — paridade funcional completa; visual simples aceitável |
| Modo de execução | **A** — processo independente `python web.py`, sem Pygame |
| Tempo real | **A** — WebSocket (push contínuo de estado) |
| Frontend | **C** — Vue 3 + Vite |
| Mapa | **A** — Canvas 2D (hit-test manual para bloqueios) |
| Backend | FastAPI + uvicorn (inferido; WebSocket nativo) |
| Abordagem arquitetural | **1** — camada Web + controles headless (recomendada) |
| Desktop | Inalterado — `python main.py` |
| Git | Sem commit até pedido explícito |

---

## 4. Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│  python main.py          python web.py                  │
│  (Pygame — inalterado)   (FastAPI + WebSocket)          │
└──────────┬──────────────────────────┬───────────────────┘
           │                          │
           ▼                          ▼
┌──────────────────────┐   ┌──────────────────────────────┐
│  pygame_application  │   │  web/simulation_service.py   │
│  + widgets Pygame    │   │  + headless controls         │
└──────────┬───────────┘   └──────────────┬───────────────┘
           │                              │
           └──────────┬───────────────────┘
                      ▼
           ┌──────────────────────┐
           │   SimulationState    │
           │   (core intocável)   │
           └──────────────────────┘
```

### 4.1 Estrutura de pastas

```
genetic_algorithm_tsp-main/
├── main.py                         # desktop (inalterado)
├── web.py                          # entry point web
├── traveling_salesman_problem/
│   ├── simulation/                 # core existente
│   └── web/                        # NOVO
│       ├── server.py               # FastAPI app
│       ├── simulation_service.py   # loop + orquestração
│       ├── state_serializer.py     # SimulationState → JSON
│       ├── command_handler.py      # comandos WebSocket → ações
│       ├── headless_controls.py    # sliders/toggles sem Pygame
│       └── log_buffer.py           # captura de logs/eventos
└── frontend/                       # NOVO — Vue 3 + Vite
    ├── src/
    │   ├── components/             # Header, Sidebar, Tabs, Footer
    │   ├── composables/            # useWebSocket, useSimulation
    │   └── canvas/                 # MapRenderer (Canvas 2D)
    └── dist/                       # build servido pelo FastAPI
```

### 4.2 Princípio de comunicação

A interface Web **apenas consome e apresenta** o estado produzido pelo algoritmo. O frontend nunca recalcula fitness, rotas ou distâncias.

---

## 5. Backend

### 5.1 Headless controls

Classes em `headless_controls.py` com interface idêntica aos widgets Pygame:

| Classe | Propriedades usadas por `SimulationState` |
|--------|---------------------------------------------|
| `HeadlessSlider` | `.value`, `.integer_value`, `.minimum_value`, `.maximum_value` |
| `HeadlessToggle` | `.is_active` |
| `HeadlessButton` | `.label` (ações disparadas via `command_handler`, sem `handle_event`) |

`SimulationState.initialize_headless()` cria controles headless em vez de widgets Pygame. O método `initialize()` existente permanece para o desktop.

### 5.2 SimulationService

Responsabilidades:

1. Instanciar `SimulationState` em modo headless
2. Executar loop de gerações (~30 FPS, igual ao desktop)
3. Avançar animação de rota (`advance_trip_animation` de `route_animation.py`)
4. Processar comandos recebidos via WebSocket
5. Serializar e broadcast do estado

Estado interno adicional:

- `paused: bool` — pausa o loop de gerações
- `log_buffer: LogBuffer` — captura prints e eventos
- `animation_state: TripAnimationState` — reutiliza módulo existente

### 5.3 Servidor FastAPI

- `GET /` → `frontend/dist/index.html`
- `GET /assets/*` → arquivos estáticos do build Vue
- `WS /ws` → canal bidirecional
- Um único `SimulationService` por processo (single-player local)
- Startup: inicia loop asyncio + abre navegador em `http://localhost:8000`

### 5.4 WebSocket — mensagens

**Server → Client: `state_update`**

```json
{
  "type": "state_update",
  "generation": 18,
  "running": true,
  "metrics": {
    "fitness": 4869.0,
    "distance": 48.69,
    "priority_penalty": 156.0,
    "blocked_penalty": 0.0,
    "population_size": 100,
    "fps": 30
  },
  "params": {
    "mutation": 0.18,
    "priority_weight": 2.4,
    "vehicle_count": 3,
    "capacity": 58,
    "transit_count": 20,
    "param_ranges": {
      "mutation": [0.0, 1.0],
      "priority_weight": [0.0, 100.0],
      "vehicle_count": [1, 5],
      "capacity": [1, 120],
      "transit_count": [1, 40]
    }
  },
  "toggles": {
    "two_opt": true,
    "show_mesh": true
  },
  "focus": {
    "vehicle_id": 0,
    "trip_index": null
  },
  "summary": {
    "vehicles_active": 3,
    "vehicles_total": 3,
    "capacity_total": 58,
    "deliveries_done": 12,
    "deliveries_total": 12,
    "trips_total": 5,
    "blocked_nodes": 2
  },
  "map": {
    "bounds": [x_min, y_min, x_max, y_max],
    "depot": [x, y],
    "deliveries": [
      { "id": "A", "x": 0, "y": 0, "priority": 8, "demand": 5 }
    ],
    "mesh": {
      "edges": [[x1, y1, x2, y2]],
      "transit_nodes": [[x, y]],
      "blocked": [[x, y]]
    },
    "theme": {
      "vehicle_colors": ["#2563eb", "#dc2626", "#059669", "#d97706", "#7c3aed"],
      "depot_color": "#0f172a",
      "mesh_edge_color": "#cbd5e1",
      "transit_color": "#94a3b8",
      "blocked_color": "#ef4444",
      "background_map": "#e8f5e0"
    }
  },
  "plans": {
    "0": {
      "distance": 18.42,
      "load": 46,
      "capacity": 58,
      "trips": [
        {
          "index": 1,
          "stops": ["D", "A", "C", "F", "D"],
          "load": 46,
          "polylines": [[[x, y], ...]]
        }
      ]
    }
  },
  "runner_up": {
    "0": { "trips": [...], "polylines": [...] }
  },
  "histories": {
    "0": [1200.0, 980.0, 870.0]
  },
  "animation": {
    "vehicle_id": 0,
    "position": [x, y],
    "trip_index": 1
  },
  "routes_panel": [
    { "type": "header", "vehicle_id": 0, "text": "Veículo 1" },
    { "type": "trip", "vehicle_id": 0, "trip_index": 0, "text": "  Viagem 1: D → A → C → D  (46/58)" }
  ],
  "logs": [
    { "ts": "2026-07-11T17:00:00", "type": "generation", "message": "Geração 18: fitness=4869" }
  ]
}
```

**Client → Server: `command`**

| Comando | Payload | Equivalente desktop |
|---------|---------|-------------------|
| `set_param` | `{ "key": "mutation", "value": 0.18 }` | Slider correspondente |
| `set_toggle` | `{ "key": "show_mesh", "active": true }` | Toggle correspondente |
| `action` | `{ "name": "shuffle_positions" }` | Sortear posições |
| `action` | `{ "name": "hospital_preset" }` | Cenário hospitalar |
| `action` | `{ "name": "restart_algorithm" }` | Reiniciar GA |
| `action` | `{ "name": "clear_blocked" }` | Limpar bloqueios |
| `set_focus` | `{ "vehicle_id": 0, "trip_index": null }` | Filtro / painel de rotas |
| `toggle_blocked` | `{ "map_x": 450.0, "map_y": 320.0 }` | Clique no mapa |
| `pause` | `{}` | Pausar gerações |
| `resume` | `{}` | Retomar gerações |

**Server → Client: `error`**

```json
{ "type": "error", "message": "Parâmetro inválido: foo" }
```

### 5.5 State serializer

Reutiliza funções existentes — não duplica lógica:

| Dado serializado | Fonte |
|------------------|-------|
| Painel de rotas | `build_route_panel_rows()` |
| Planos | `DecodedVehiclePlan`, `Trip` |
| Cores | `VisualTheme.vehicle_route_colors`, `priority_to_color()` |
| Histórico | `VehicleGeneticState.fitness_history` |
| Polylines | `expand_route_polyline()`, `delivery_segment_path()` |

### 5.6 Tratamento de erros

| Situação | Comportamento |
|----------|---------------|
| Comando inválido | Responde `error` no WebSocket; simulação continua |
| Cliente desconecta | Remove da lista de clientes; simulação não para |
| Parâmetro fora de faixa | Clamp ao min/max (mesmo comportamento dos sliders) |
| Rebuild durante geração | Aguarda fim da geração atual, depois rebuild |
| Frontend não buildado | Mensagem: executar `npm run build` em `frontend/` |

### 5.7 Dependências Python novas

```
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
websockets>=12.0
```

`web.py` não importa `pygame` nem `pygame_application`.

---

## 6. Frontend (Vue 3 + Vite)

### 6.1 Layout v1 (funcional, visual simples)

```
┌──────────────────────────────────────────────────────────────┐
│ Header: título + métricas + Nova execução / Pausar / Tema   │
├────────────┬─────────────────────────┬───────────────────────┤
│ Sidebar    │ Painel central          │ Mapa (Canvas)         │
│ (scroll)   │ [Resumo|Stats|Hist|Logs]│                       │
│            │                         │ Toolbar + legenda     │
│ • Info     │ Conteúdo da aba         │                       │
│ • Params   │                         │                       │
│ • Toggles  │                         │                       │
│ • Rotas    │                         │                       │
│ • Ações    │                         │                       │
├────────────┴─────────────────────────┴───────────────────────┤
│ Footer: geração, população, fitness, dist, penalidades, FPS │
└──────────────────────────────────────────────────────────────┘
```

### 6.2 Componentes

| Componente | Responsabilidade |
|------------|------------------|
| `AppHeader` | Métricas + play/pause/reset/tema |
| `SidebarInfo` | Veículos, capacidade, entregas, viagens, bloqueios |
| `SidebarParams` | 5 sliders (mutação, prioridade, veículos, capacidade, trânsito) |
| `SidebarToggles` | 2-opt, malha (únicos toggles do desktop) |
| `SidebarRoutes` | Cartões por veículo; clique define foco |
| `SidebarActions` | Sortear, hospitalar, reiniciar, limpar bloqueios |
| `TabPanel` | Resumo / Estatísticas / Histórico / Logs |
| `ConvergenceChart` | Chart.js — linha por veículo, legenda, tooltip |
| `LogConsole` | Buffer de eventos com filtro por tipo |
| `MapCanvas` | Canvas 2D — todas as camadas do mapa |
| `MapToolbar` | Filtro veículo, toggles, fullscreen |
| `StatusFooter` | Métricas detalhadas da geração |

### 6.3 Mapa Canvas — camadas (ordem de desenho)

| # | Camada | Condição |
|---|--------|----------|
| 1 | Fundo do mapa | sempre |
| 2 | Malha (arestas) | `show_mesh` |
| 3 | Nós de trânsito | sempre |
| 4 | 2ª melhor rota (tracejada) | somente com veículo focado (igual desktop) |
| 5 | Rotas por veículo + setas | filtro; viagens 2+ tracejadas; setas sempre |
| 6 | Entregas (cor por prioridade) | sempre; tooltip no hover |
| 7 | Depósito (maior marcador, label "D") | sempre |
| 8 | Bloqueios (X vermelho) | sempre; clique → `toggle_blocked` |
| 9 | Cursor animado | somente com veículo focado (igual desktop) |

**Coordenadas:** backend envia `map.bounds`; Canvas aplica transformação escala + offset para responsividade. Cliques convertem pixel → coordenada do mapa antes de enviar ao servidor.

**Hit-test bloqueios:** mesma lógica de `map_hit_test.py` — pode ser reimplementada no frontend para feedback visual imediato, com confirmação pelo backend.

### 6.4 Abas

| Aba | Conteúdo v1 |
|-----|-------------|
| Resumo | Gráfico de convergência + cartões de rota |
| Estatísticas | Tabela fitness/dist/prior por veículo |
| Histórico | Lista scrollável de gerações com métricas |
| Logs | Console com filtro (geração, mutação, crossover, eventos) |

### 6.5 Dependências frontend

```
vue@3, vite, chart.js
```

---

## 7. Paridade funcional — checklist

Todas as funcionalidades do desktop devem estar disponíveis na Web:

- [ ] Múltiplos veículos e múltiplas viagens
- [ ] Capacidade dinâmica (slider com bounds)
- [ ] Prioridade das entregas (gradiente visual)
- [ ] Bloqueio manual de nós (clique no mapa)
- [ ] Cenário hospitalar
- [ ] Sorteio de posições
- [ ] Malha de ruas (toggle)
- [ ] Segunda melhor rota (runner-up, automático ao focar veículo)
- [ ] Animação de rota (automática ao focar veículo)
- [ ] Setas de direção nas rotas (sempre visíveis, igual desktop)
- [ ] Gráfico de convergência (por veículo)
- [ ] Painel de rotas `D → … → D`
- [ ] Filtro por veículo e viagem
- [ ] Toggle 2-opt
- [ ] Sliders: mutação, prioridade, veículos, capacidade, trânsito
- [ ] Console/logs de evolução
- [ ] Pausar/retomar simulação

---

## 8. Fases de entrega

| Fase | Entregável | Critério de pronto |
|------|------------|-------------------|
| **F1 — Fundação** | `headless_controls`, `initialize_headless()`, `SimulationService`, WebSocket | `python web.py` conecta e recebe `state_update` |
| **F2 — Paridade de controles** | Todos sliders, toggles, ações, foco, bloqueios | Cada ação desktop funciona via WebSocket |
| **F3 — Mapa Canvas** | `MapCanvas` com camadas, animação, hit-test | Mapa equivalente ao Pygame |
| **F4 — Painéis** | Abas, gráfico, logs, footer, cartões de rota | 4 abas funcionais |
| **F5 — Polish visual** | Cards, sombras, tema claro/escuro, responsividade | Aproxima referência visual (`melhoria_visual.md`) |

**Escopo v1:** F1 + F2 + F3 + F4. F5 é v1.1.

---

## 9. Testes

| Teste | Valida |
|-------|--------|
| `test_headless_controls.py` | Interface dos controles headless |
| `test_state_serializer.py` | JSON completo, campos obrigatórios |
| `test_simulation_service.py` | Loop, pause/resume, comandos |
| `test_command_handler.py` | Cada comando → mesmo efeito que desktop |
| `test_web_blocked_toggle.py` | Bloqueio via coordenadas = desktop |
| Paridade manual | Mesmo cenário → mesmo fitness desktop vs web |

Todos os testes existentes do desktop devem continuar passando sem alteração.

---

## 10. Execução

```bash
# Desktop (inalterado)
python main.py

# Web — desenvolvimento
cd frontend && npm install && npm run dev    # proxy → :8000
python web.py

# Web — produção local
cd frontend && npm run build
python web.py
```

---

## 11. Escalabilidade futura (fora de escopo v1)

A arquitetura deve permitir, sem alterar o Core:

- Novos algoritmos (ACO, PSO, SA)
- Múltiplos depósitos
- Mapas reais (OpenStreetMap)
- Histórico de execuções, salvar/carregar cenários
- Comparação entre algoritmos
- Exportação de rotas

---

## 12. Fora de escopo

- Alterações no algoritmo genético ou decoder VRP
- Remoção ou simplificação de funcionalidades desktop
- Deploy em produção (cloud, Docker) — v1 é local
- Mapas geográficos reais — v1 usa coordenadas abstratas do simulador
- Polish visual completo (F5) — v1.1
- Toggles extras de exibição do `melhoria_visual.md` (animação, setas, 2ª rota como switches) — F5; v1 segue regras automáticas do desktop

---

## 13. Resultado esperado

Aplicação híbrida:

- **Desktop (Pygame):** preservada integralmente.
- **Web:** dashboard funcional consumindo o mesmo núcleo, com paridade completa de controles na v1.

Ambas as interfaces exibem os mesmos resultados para o mesmo cenário e parâmetros.
