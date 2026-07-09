# Design: Rede de Ruas, Pathfinding e Visualização por Viagem

**Data:** 2026-07-08  
**Status:** Aprovado (design conversacional)  
**Contexto:** Extensão do simulador guloso de entregas (`feat/greedy-delivery-simulation`) para deslocamento em grafo por raio (estilo TSP local), passagem obrigatória por nós de trânsito no caminho, e seletor interativo de veículo/viagem.

---

## 1. Objetivo

Substituir deslocamento em linha reta (euclidiana direta) por roteamento em **rede de ruas**:

- Nós: Distribuidora + pontos de entrega (A/B/C) + nós de trânsito sorteados.
- Arestas: conexão entre pares de nós cuja distância euclidiana ≤ raio configurável.
- O veículo move-se **somente** pelas arestas do grafo; nós intermediários do caminho são **obrigatórios** (não podem ser ignorados).
- Por viagem: **nenhum nó se repete**; Distribuidora aparece apenas no início e no fim da viagem.
- Manter algoritmo guloso global de atribuição de entregas; distância entre candidatos passa a ser distância no grafo.
- Visualização interativa: seletor de veículo + viagem; mapa destaca só a rota selecionada.

---

## 2. Decisões de design (validadas)

| Tópico | Decisão |
|--------|---------|
| Modelo de deslocamento | Grafo por raio (não linha reta entre nós distantes) |
| Inspiração TSP | Conectar pontos dentro do raio — rede local sensata ao trajeto |
| Nós do grafo | Distribuidora + entregas + nós de trânsito sorteados |
| Repetição de nós | Por viagem: proibida; Distribuidora só início/fim |
| Pathfinding | BFS (caminho simples mínimo em arestas) |
| Algoritmo de entregas | Guloso global mantido; distância = grafo |
| Configuração | Sliders: **Nós de trânsito** (3–15), **Raio de conexão** (80–250 px) |
| Visualização | Seletor interativo veículo + viagem; mapa focado na seleção |
| Identificação veículo | Cor + estilo de linha (sólida / tracejada / pontilhada) |
| Commits | Fora de escopo desta sessão de design (salvo pedido explícito) |

---

## 3. Abordagens consideradas

### 3.1 Grafo integrado ao roteamento guloso (escolhida)

Novo módulo `road_network.py`; `routing.py` usa pathfinding para distância e expansão de paradas.

- **Prós:** coerente, modular, trânsito obrigatório, testável.
- **Contras:** maior complexidade; grafo desconexo exige fallback.

### 3.2 Pós-processamento

Guloso em linha reta → substituir trechos por caminhos no grafo depois.

- **Prós:** diff menor no guloso.
- **Contras:** ordem gulosa baseada em distância errada.

### 3.3 TSP por viagem no grafo

- **Prós:** rotas mais curtas por viagem.
- **Contras:** abandona guloso; escopo maior.

---

## 4. Arquitetura e modelo de dados

### 4.1 Novos / alterados em `models.py`

```python
@dataclass
class TransitNode:
    id: str              # "T1", "T2", ...
    coordinate: Coordinate

@dataclass
class RoadNetwork:
    nodes: dict[str, Coordinate]       # DEPOT + A/B/C + T*
    edges: list[tuple[str, str]]     # bidirecionais
    connection_radius: float

@dataclass
class Stop:
    point_id: str
    items_delivered: int
    is_transit: bool = False         # True para nós T* sem entrega

@dataclass
class SimulationResult:
    # ... campos existentes ...
    road_network: RoadNetwork
    transit_nodes: list[TransitNode]
```

### 4.2 Módulo `road_network.py`

| Função | Responsabilidade |
|--------|------------------|
| `generate_transit_nodes(count, bounds, rng)` | Sorteia N nós de trânsito com separação mínima |
| `build_radius_graph(node_coords, radius)` | Lista arestas onde dist ≤ raio |
| `find_path(network, origin, dest, blocked)` | BFS; `blocked` = nós já visitados na viagem |
| `path_distance(network, path)` | Soma euclidiana dos trechos consecutivos |
| `ensure_connectivity(network, depot_id, delivery_ids)` | Valida alcançabilidade; retorna bool |

**Pathfinding — regras:**

1. BFS encontra caminho simples (sem repetir nós do caminho).
2. `blocked` inclui nós já visitados na viagem atual.
3. Distribuidora como **destino final** não está bloqueada (retorno permitido).
4. Distribuidora como origem de viagem: adicionada a `visited` após primeira parada.
5. Empate em BFS: preferir menor distância euclidiana total.
6. Caminho inclui **todos** os nós intermediários — registrados como `Stop` com `is_transit=True`, `items_delivered=0`.

**Fallback desconexão:**

- Ao sortear: re-sorteia trânsito até grafo conexo (máx. 50 tentativas).
- Se ainda desconexo: conecta par desconexo ao vizinho euclidiano mais próximo (aresta extra) — registrado no log da sidebar.

---

## 5. Integração com roteamento guloso

### 5.1 Distância entre candidatos

Substituir `euclidean(vehicle.pos, point.coord)` por:

```python
path = find_path(network, current_node_id, target_node_id, visited_in_trip)
distance = path_distance(network, path)
```

Se `find_path` retornar vazio → candidato descartado.

### 5.2 Execução de movimento

Para cada nó em `path[1:]` (pula origem):

1. Acumula distância do trecho.
2. Se nó de entrega com demanda: entrega `min(capacidade_restante, demanda)`.
3. Se nó de trânsito: `Stop(id, 0, is_transit=True)`.
4. Adiciona nó a `visited_in_trip`.

### 5.3 Ciclo de viagem

- Início viagem: `visited_in_trip = set()`; primeiro stop `DEPOT`.
- Retorno à Distribuidora: pathfinding para DEPOT; DEPOT como destino **não** bloqueado.
- Após fechar viagem: reset `visited_in_trip`.

### 5.4 Geração no "Sortear posições"

1. Sorteia Distribuidora + entregas (existente).
2. Sorteia N nós de trânsito.
3. Monta `RoadNetwork` com raio do slider.
4. Valida conectividade Distribuidora ↔ todas entregas.
5. Redistribui pedidos (existente).
6. Limpa resultado de simulação.

Alterar sliders de trânsito/raio → limpa simulação; exige novo sorteio.

---

## 6. Configuração na sidebar

| Controle | Faixa | Default |
|----------|-------|---------|
| Nós de trânsito | 3–15 | 8 |
| Raio de conexão | 80–250 px | 150 |
| Veículos | 1–3 | (existente) |
| Pontos | 1–3 | (existente) |
| Total de itens | 2–14 pares | (existente) |

---

## 7. Visualização interativa

### 7.1 Mapa

| Elemento | Visual |
|----------|--------|
| Arestas do grafo | Cinza claro `(120, 130, 140)`, 1 px — visível após sortear |
| Nós de trânsito | Círculo 6 px cinza `(150, 150, 150)`, label `T1`… |
| Distribuidora | Quadrado azul `D` (mantido) |
| Entregas | Círculo vermelho + label + itens (mantido) |
| Rota selecionada | Linha 4 px, cor do veículo, setas direcionais |
| Rotas não selecionadas | Ocultas (modo "Uma viagem") ou 20% opacidade (modo "Todas") |

### 7.2 Identificação por veículo

| Veículo | Cor | Estilo legenda |
|---------|-----|----------------|
| 1 | `(37, 99, 235)` azul | Sólido ▬ |
| 2 | `(234, 88, 12)` laranja | Tracejado ╌ |
| 3 | `(22, 163, 74)` verde | Pontilhado ··· |

Implementação tracejado/pontilhado: desenhar segmentos alternados em `_draw_open_route`.

### 7.3 Seletor interativo (`TripSelector` widget)

Posição: sidebar, seção **Visualização** (após Simular).

```
Veículo:  [1] [2] [3]
Viagem:   [1] [2] [3] [Todos]
Modo:     ◉ Uma viagem   ○ Todas do veículo
```

Estado em `SimulationState`:

```python
active_vehicle_id: int = 1
active_trip_index: int = 0      # -1 = "Todos"
trip_view_mode: str = "single"  # "single" | "all"
```

- Botões desabilitados até existir `simulation_result`.
- Ao simular: seleciona Veículo 1 · Viagem 1 automaticamente.
- Modo **Uma viagem**: desenha só `vehicles[v].trips[t]`.
- Modo **Todas**: desenha todas viagens do veículo com opacidade decrescente.

### 7.4 Sidebar — detalhe da viagem ativa

```
── Veículo 2 · Viagem 1 ──
D → T3 → T7 → A(4) → T2 → D
Distância: 342 px  |  Carga: 4/10
Trânsito: T3, T7, T2
```

`reporter.py` atualizado para incluir nós de trânsito na cadeia de paradas.

---

## 8. Arquivos afetados

| Arquivo | Mudança |
|---------|---------|
| `delivery_simulation/road_network.py` | **Create** |
| `delivery_simulation/models.py` | TransitNode, RoadNetwork, Stop.is_transit |
| `delivery_simulation/routing.py` | Pathfinding integrado ao guloso |
| `delivery_simulation/point_generator.py` | Orquestra trânsito + validação grafo |
| `delivery_simulation/reporter.py` | Trânsito na formatação |
| `delivery_simulation/assignment.py` | Passa `RoadNetwork` ao routing |
| `simulation_state.py` | Sliders trânsito/raio + TripSelector |
| `application_settings.py` | Defaults novos sliders |
| `map_renderer.py` | Grafo, trânsito, rotas filtradas, estilos linha |
| `application_layout.py` | Seção visualização + detalhe viagem |
| `visualization/widgets/trip_selector.py` | **Create** |
| `pygame_application.py` | Wiring seletor + render condicional |

---

## 9. Testes

| Arquivo | Casos |
|---------|-------|
| `test_road_network.py` | Arestas por raio; BFS caminho válido; bloqueio de visitados; distância do caminho |
| `test_routing_graph.py` | Movimento expande trânsito; viagem sem nó repetido; guloso usa distância do grafo |
| `test_connectivity.py` | Re-sorteio quando desconexo; fallback vizinho mais próximo |

Testes Pygame: validação manual.

---

## 10. Tratamento de erros

| Situação | Comportamento |
|----------|---------------|
| Grafo desconexo após 50 tentativas | Fallback: aresta ao vizinho mais próximo + aviso na sidebar |
| Pathfinding sem caminho mid-viagem | `RuntimeError` — não deve ocorrer se conectividade validada |
| Simular sem sortear | Botão desabilitado (existente) |
| Veículo sem viagens | Botões de viagem ocultos para índices inexistentes |

---

## 11. Fora de escopo

- Obstáculos / terreno.
- Animação passo a passo do veículo.
- Edição manual do grafo pelo usuário.
- Algoritmos avançados (A*, Dijkstra ponderado) — BFS suficiente para escala atual.

---

## 12. Extensões futuras

- Peso diferente por aresta (estrada vs beco).
- Slider de densidade de trânsito vs quantidade fixa.
- Exportar grafo + rotas em JSON.
- Highlight animado nó a nó na viagem selecionada.
