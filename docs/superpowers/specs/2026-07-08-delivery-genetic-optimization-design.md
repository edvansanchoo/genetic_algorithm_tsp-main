# Design: Otimização Genética por Veículo no Simulador de Entregas

**Data:** 2026-07-08  
**Status:** Aprovado em brainstorming  
**Base:** `feat/greedy-delivery-simulation` (simulador guloso + rede de ruas)

---

## 1. Objetivo

Substituir a simulação gulosa de execução única por um **loop contínuo de algoritmo genético (AG)**, no mesmo espírito do TSP original na branch `main`, com estas características:

- **Atribuição fixa via guloso:** quem entrega o quê é decidido uma vez ao clicar **Simular**.
- **AG por veículo:** cada veículo trata sua lista de entregas como um **TSP** (permutação de paradas).
- **Rede de ruas preservada:** distância e movimentação usam pathfinding BFS, nós de trânsito, capacidade e regras de viagem atuais.
- **Gráfico de convergência:** sidebar superior com **uma linha por veículo**, como o gráfico de fitness do TSP original.
- **Controle de mutação:** slider de mutação reaproveitado da `main`; população fixa em 100.

---

## 2. Decisões de produto (brainstorming)

| Tópico | Decisão |
|--------|---------|
| Algoritmo | AG como na `main` (população, elitismo, crossover, mutação) |
| Escopo por veículo | TSP individual com regras de rede atuais |
| Atribuição | Guloso fixo → AG otimiza apenas ordem de visita |
| Execução | Loop contínuo automático após **Sortear** + **Simular** |
| Controles AG | Slider de mutação; população fixa 100; sem 2-opt |
| Gráfico | N linhas (1 por veículo), melhor distância por geração |

---

## 3. Arquitetura

### 3.1 Fluxo da aplicação

```
Sortear posições
  → gera rede, trânsito, pedidos
  → reseta populações AG e histórico do gráfico
  → is_evolution_running = False

Simular
  → (1) run_greedy_simulation() uma vez
  → (2) extrair DeliveryTask[] por veículo (atribuição fixa)
  → (3) inicializar população AG por veículo (100 permutações aleatórias)
  → (4) is_evolution_running = True

A cada frame (30 fps, enquanto is_evolution_running):
  → run_one_generation() para cada veículo
  → atualizar vehicle_best_distance_history
  → redesenhar gráfico + mapa com melhores rotas atuais
```

### 3.2 Abordagem descartada

- **AG global multi-veículo:** cromossomo único codificando todos os veículos — complexidade alta, crossover difícil com capacidade/rede.
- **Guloso com reinícios aleatórios:** não é AG real; descartado.

### 3.3 Abordagem adotada

**Populações independentes por veículo.** Cada veículo evolui sua permutação em paralelo. O mapa exibe a composição dos melhores indivíduos de cada população (não um único indivíduo global).

### 3.4 Módulos

| Módulo | Ação | Responsabilidade |
|--------|------|------------------|
| `delivery_simulation/assignment.py` | Ajustar | Extrair `dict[int, list[DeliveryTask]]` do resultado guloso |
| `delivery_simulation/route_evaluator.py` | Criar | Simula permutação na rede → distância + viagens |
| `delivery_simulation/vehicle_genetic.py` | Criar | Estado AG por veículo; `run_one_generation()` |
| `delivery_simulation/models.py` | Estender | `DeliveryTask` dataclass |
| `traveling_salesman_problem/visualization/convergence_chart.py` | Estender | Suporte a N séries/linhas |
| `traveling_salesman_problem/simulation/simulation_state.py` | Reescrever parcial | Loop AG, históricos, slider mutação |
| `traveling_salesman_problem/simulation/pygame_application.py` | Ajustar | Gráfico no topo; loop contínuo |
| `traveling_salesman_problem/config/application_settings.py` | Estender | `population_size`, `initial_mutation_probability` |

Reaproveitar sem alteração:

- `genetic_algorithm/population.py`
- `genetic_algorithm/selection.py`
- `genetic_algorithm/mutation.py` (via `evolve_next_generation`)
- `delivery_simulation/road_network.py`
- `delivery_simulation/routing.py` (fase de atribuição gulosa)

---

## 4. Modelo de dados

### 4.1 `DeliveryTask`

```python
@dataclass(frozen=True)
class DeliveryTask:
    point_id: str
    items: int
```

Representa **uma parada com carga**. Pontos com mais itens que a capacidade geram múltiplos tokens.

Exemplo: ponto A com 14 itens, capacidade 10 → `[DeliveryTask("A", 10), DeliveryTask("A", 4)]`.

### 4.2 Cromossomo

Lista ordenada de índices ou tokens `DeliveryTask` — permutação completa da carga atribuída ao veículo. Sempre válida (todos os tokens presentes exatamente uma vez).

### 4.3 Histórico de convergência

```python
vehicle_best_distance_history: dict[int, list[float]]
# chave = vehicle_id (1..N), valor = melhor distância por geração
```

### 4.4 Estado de evolução (`SimulationState`)

Campos novos/alterados:

- `is_evolution_running: bool`
- `vehicle_genetic_states: dict[int, VehicleGeneticState]`
- `vehicle_assignments: dict[int, list[DeliveryTask]]`
- `vehicle_best_distance_history: dict[int, list[float]]`
- `generation_counter: int`
- `mutation_slider: MutationSlider`
- `best_simulation_result: SimulationResult | None` — composição das melhores rotas para o mapa

---

## 5. Atribuição gulosa (fase fixa)

### 5.1 Entrada

Resultado de `run_greedy_simulation(config, depot, points, road_network, transit_nodes)`.

### 5.2 Extração

Para cada veículo, percorrer todas as viagens e stops:

- Ignorar stops com `is_transit=True` e `point_id == DEPOT`.
- Para stops de entrega (`items_delivered > 0`), emitir `DeliveryTask(point_id, items_delivered)`.

### 5.3 Garantias

- Soma dos tokens por ponto = `total_items` daquele ponto (todas as entregas concluídas).
- Cada token tem `items <= MAX_CAPACITY` (10).
- A lista é **fixa** durante toda a evolução AG.

### 5.4 Função pública

```python
def extract_vehicle_assignments(result: SimulationResult) -> dict[int, list[DeliveryTask]]:
    ...
```

---

## 6. Avaliador de rotas (`route_evaluator.py`)

### 6.1 Assinatura

```python
def evaluate_permutation(
    tasks: list[DeliveryTask],
    permutation: list[int],  # índices em tasks
    road_network: RoadNetwork,
) -> tuple[float, list[Trip]]:
    ...
```

Retorna `(distância_total, viagens)`.

### 6.2 Algoritmo de simulação

Estado: `current_node = DEPOT`, `load = 0`, viagem aberta, `visited_nodes` da viagem.

Para cada índice na permutação:

1. `task = tasks[i]`
2. Se `load + task.items > MAX_CAPACITY`:
   - Pathfinding → DEPOT (regras de blocked para retorno)
   - Fechar viagem; abrir nova; `load = 0`; limpar `visited_nodes`
3. Pathfinding `current_node → task.point_id` (blocked = visited da viagem, exceto regras de trânsito/depósito)
4. Expandir path em stops (trânsito na ida; trânsito silencioso na volta)
5. Registrar entrega; `load += task.items`

Ao final: retornar ao DEPOT, fechar viagem.

### 6.3 Regras de pathfinding (herdadas de `routing.py`)

| Regra | Comportamento |
|-------|---------------|
| Movimento | Apenas arestas da rede |
| Pathfinding | BFS via `find_path` |
| Trânsito na ida | Registrado como stop |
| Trânsito na volta | Traçado no path; **não** duplica stop |
| DEPOT | Início e fim de cada viagem |
| Nós visitados | Sem repetir ponto de entrega na mesma viagem |
| `_blocked_for_pathfinding` | Reutilizar lógica existente |

### 6.4 Fitness

`fitness = distância_total` (menor é melhor). Sem penalidades extras.

---

## 7. AG por veículo (`vehicle_genetic.py`)

### 7.1 `VehicleGeneticState`

```python
@dataclass
class VehicleGeneticState:
    vehicle_id: int
    tasks: list[DeliveryTask]
    population: list[list[int]]       # permutações (índices)
    best_distance: float
    best_permutation: list[int]
    best_trips: list[Trip]
```

### 7.2 Inicialização

```python
def initialize_vehicle_genetic(
    vehicle_id: int,
    tasks: list[DeliveryTask],
    population_size: int = 100,
    rng: random.Random | None = None,
) -> VehicleGeneticState:
    ...
```

População = permutações aleatórias dos índices `0..len(tasks)-1`.

### 7.3 Uma geração

Equivalente ao `run_one_generation()` da `main`:

1. Calcular fitness de cada indivíduo via `evaluate_permutation`
2. Ordenar população por fitness (`sort_population_by_fitness`)
3. Registrar melhor distância no histórico
4. Evoluir: `evolve_next_generation(population, fitness, population_size=100, mutation_probability, mutation_type="adjacent", n_elite=3, use_2opt=False)`

**Nota:** `evolve_next_generation` espera `List[Route]` onde `Route = List[CityCoordinate]`. Adaptar com type alias `Permutation = list[int]` ou wrapper que trate permutações como rotas genéricas (lista de inteiros). Crossover/mutação adjacente funciona igual em permutações.

### 7.4 `SimulationState.run_one_generation()`

```python
def run_one_generation(self) -> None:
    for vehicle_id, state in self.vehicle_genetic_states.items():
        # avaliar, evoluir, atualizar best
        self.vehicle_best_distance_history[vehicle_id].append(state.best_distance)
    self.generation_counter += 1
    self._rebuild_best_simulation_result()  # compõe mapa
```

---

## 8. UI e layout

### 8.1 Sidebar (restaurar layout TSP)

```
┌──────────────────────────────┐
│ Gráfico Convergência (400px) │  ← N linhas, cores por veículo
├──────────────────────────────┤
│ Configuração                 │
│  - Veículos, pontos, itens   │
│  - Nós trânsito, raio        │
│  - Mutação (%)               │  ← MutationSlider da main
├──────────────────────────────┤
│ Ações                        │
│  - Sortear posições          │
│  - Simular                   │
├──────────────────────────────┤
│ Visualização (trip selector) │  ← após simular
├──────────────────────────────┤
│ Resultado                    │
└──────────────────────────────┘
```

### 8.2 `ApplicationSettings`

Restaurar/adicionar:

```python
population_size: int = 100
initial_mutation_probability: float = 0.01
mutation_slider_height: int = 58
```

Ajustar `summary_panel_height` → remover ou reduzir; gráfico ocupa `VisualTheme.plot_height` (400px) no topo.

### 8.3 Gráfico multi-linha

Estender `draw_convergence_chart`:

```python
def draw_convergence_chart(
    screen: pygame.Surface,
    generation_numbers: list[int],
    series: list[list[float]],
    series_colors: tuple[tuple[int,int,int], ...],
    series_labels: list[str],
    horizontal_axis_label: str = "Geração",
    vertical_axis_label: str = "Distância (px)",
) -> None:
```

- Uma linha por veículo, cor de `VisualTheme.vehicle_route_colors`
- Legenda compacta: V1, V2, V3
- Título: "Convergência"

### 8.4 Mapa

- Exibe `best_simulation_result` (composição das melhores rotas por veículo)
- Seletor de viagem/trip mantido
- Rede, trânsito, rotas estilizadas inalterados

### 8.5 Botões

| Botão | Comportamento |
|-------|---------------|
| **Sortear posições** | Reseta rede/pedidos; para AG; limpa históricos |
| **Simular** | Atribuição gulosa + init AG + inicia loop |

---

## 9. Loop Pygame

```python
# pygame_application.py — a cada frame:
simulation.update_controls()

if simulation.is_evolution_running:
    simulation.run_one_generation()

draw_convergence_chart(
    screen,
    list(range(simulation.generation_counter)),
    [simulation.vehicle_best_distance_history[v] for v in vehicle_ids],
    ...
)
# ... mapa, sidebar ...
```

Sem botão Pausar (decisão A do brainstorming).

---

## 10. Tratamento de erros

| Situação | Comportamento |
|----------|---------------|
| Simular sem sortear | Mensagem: "Sorteie posições antes de simular." |
| Guloso falha (RuntimeError) | Mensagem de erro na sidebar; AG não inicia |
| Veículo sem tarefas | População vazia/trivial; linha flat no gráfico |
| Pathfinding impossível na avaliação | Fitness = `float("inf")`; indivíduo descartado na seleção |

---

## 11. Testes

| Arquivo | Caso |
|---------|------|
| `test_assignment_extraction.py` | Tokens corretos por veículo a partir de resultado guloso |
| `test_route_evaluator.py` | Capacidade força retorno ao depósito; distância via grafo |
| `test_route_evaluator.py` | Path passa por trânsito quando necessário |
| `test_vehicle_genetic.py` | População inicial; uma geração reduz ou mantém melhor fitness |
| `test_vehicle_genetic.py` | Com seed fixo, distância melhora em ≥1 geração em cenário pequeno |
| `test_convergence_chart.py` | N séries renderizam sem exceção (smoke) |

Testes existentes de `routing.py` e `road_network.py` permanecem inalterados.

---

## 12. Fora de escopo

- AG global multi-veículo
- Slider de população
- Toggle 2-opt
- Botão Pausar/Retomar
- Alterar atribuição durante evolução
- Prioridades de entrega / obstáculos do TSP antigo

---

## 13. Critérios de aceite

1. Após **Sortear** + **Simular**, gerações avançam automaticamente a cada frame.
2. Gráfico no topo mostra **1 linha por veículo** convergindo (distância px vs geração).
3. Slider de mutação afeta evolução em tempo real.
4. Mapa mostra rotas na rede com trânsito; seletor de viagem funciona.
5. **Sortear** reseta gráfico e populações.
6. Atribuição de pontos/itens por veículo = resultado do guloso inicial (fixa).
7. Todos os testes passam.
