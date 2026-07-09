# Design: Visualização ao Vivo da Evolução AG (estilo TSP main)

**Data:** 2026-07-08  
**Status:** Aprovado em brainstorming  
**Base:** simulador de entregas com AG por veículo (`feat/greedy-delivery-simulation`)

---

## 1. Objetivo

Replicar o comportamento visual do TSP original na branch `main`:

- AG continua tentando combinações **enquanto roda** (não parece “1 tentativa só”)
- Mapa mostra **melhor + 2ª melhor rota** do veículo selecionado a cada geração
- Gráfico de convergência **atualiza visivelmente** (não parece fixo)
- Gráfico mantém **1 linha por veículo**, com **destaque** no veículo selecionado

---

## 2. Decisões de produto (brainstorming)

| Tópico | Decisão |
|--------|---------|
| Mapa | Melhor + 2ª melhor do **veículo selecionado** (todas as viagens) |
| Velocidade AG | **2–5 gerações/segundo** (padrão 3/s) via throttle |
| Gráfico | Todas as linhas; veículo selecionado **destacado** |
| Fluxo | **Sortear** (rede/pedidos) + **Simular** (guloso + inicia AG) |

---

## 3. Problema atual

1. **Mapa:** só desenha a melhor solução; não mostra 2ª melhor “tentativa” como na `main`
2. **Gráfico:** parece fixo porque 1 geração (pop 100 × pathfinding × N veículos) pode levar segundos por frame
3. **Percepção “1 tentativa”:** guloso roda 1× (correto); AG evolui mas UI não comunica tentativas intermediárias

---

## 4. Arquitetura

### 4.1 Abordagem adotada

Estender `VehicleGeneticState` com 2ª melhor solução; throttle temporal no loop Pygame; estender renderização do mapa e gráfico.

### 4.2 Abordagens descartadas

- AG separado por viagem (complexidade alta, ordem entre viagens incoerente)
- Mostrar indivíduo aleatório da população (não espelha `main`)

### 4.3 Módulos afetados

| Módulo | Mudança |
|--------|---------|
| `delivery_simulation/vehicle_genetic.py` | Rastrear `second_best_*` |
| `traveling_salesman_problem/simulation/simulation_state.py` | Throttle gerações; expor 2ª melhor do veículo ativo |
| `traveling_salesman_problem/simulation/pygame_application.py` | Delta time + desenho melhor/2ª melhor |
| `traveling_salesman_problem/visualization/map_renderer.py` | `draw_vehicle_best_and_second_best()` |
| `traveling_salesman_problem/visualization/convergence_chart.py` | `highlight_index`, opacidade por série |
| `traveling_salesman_problem/config/application_settings.py` | `generations_per_second: float = 3.0` |

---

## 5. Estado AG — 2ª melhor solução

### 5.1 Campos novos em `VehicleGeneticState`

```python
second_best_distance: float = inf
second_best_permutation: TaskPermutation = []
second_best_trips: list[Trip] = []
```

### 5.2 Atualização por geração

Após `sort_population_by_fitness`:

1. `best` = população[0] (menor fitness finito)
2. `second_best` = população[1] se fitness finito; senão ignorar 2ª melhor no mapa

`run_vehicle_generation` atualiza `second_best_*` junto com `best_*`.

---

## 6. Throttle de gerações

### 6.1 Configuração

```python
generations_per_second: float = 3.0  # clamp 2.0–5.0
```

### 6.2 Loop (`pygame_application.py`)

```python
accumulated_evolution_time += clock.get_time() / 1000.0
generation_interval = 1.0 / settings.generations_per_second

while (
    simulation.is_evolution_running
    and accumulated_evolution_time >= generation_interval
):
    simulation.run_one_generation()
    accumulated_evolution_time -= generation_interval
```

### 6.3 Comportamento

- A 30 FPS com 3 gen/s: ~1 geração a cada 10 frames em média
- Gráfico ganha pontos regularmente; mapa alterna melhor/2ª melhor conforme evolui
- `generation_counter` incrementa 1 por `run_one_generation()` (como hoje)

---

## 7. Mapa — melhor + 2ª melhor (veículo selecionado)

### 7.1 Escopo

- Veículo ativo: `trip_selector.active_vehicle_id`
- Desenhar **todas as viagens** de `best_trips` e `second_best_trips` desse veículo
- **Não** desenhar rotas dos outros veículos (foco inspeção, como TSP mostra 1 solução principal)

### 7.2 Estilos

| Camada | Cor | Linha | Extra |
|--------|-----|-------|-------|
| Melhor | `vehicle_route_colors[id-1]` | 4px sólida | glow leve (opcional, reutilizar padrão TSP) |
| 2ª melhor | mesma cor | 2px tracejada | alpha 50% |

Ordem de desenho: 2ª melhor primeiro, melhor por cima.

### 7.3 Cabeçalho do mapa

Atualizar `draw_delivery_map_header` (ou texto auxiliar):

```
Gen {N} · V{id} · melhor {dist:.0f} px · 2ª {second:.0f} px
```

Se não houver 2ª melhor válida: omitir parte `2ª`.

### 7.4 Seletor de viagem

- **Mapa:** sempre mostra veículo completo (todas viagens)
- **Sidebar (trip detail):** continua filtrando viagem individual selecionada

---

## 8. Gráfico — destaque por veículo

### 8.1 API estendida

```python
draw_convergence_chart(
    screen,
    generation_numbers,
    series,
    series_colors=...,
    series_labels=...,
    highlight_index: int | None = None,  # 0-based
)
```

### 8.2 Estilo

| Série | linewidth | alpha |
|-------|-----------|-------|
| Destacada (`highlight_index`) | 2.5 | 1.0 |
| Demais | 1.5 | 0.4 |

Legenda matplotlib: V1, V2, V3 com cores existentes.

### 8.3 Escala Y

`matplotlib` autoscale a cada frame (comportamento padrão) — evita gráfico “congelado” visualmente quando distâncias caem.

### 8.4 Dados

Continua usando `vehicle_best_distance_history[vehicle_id]` — 1 valor por geração (melhor distância daquela geração).

---

## 9. Fluxo da aplicação (inalterado)

```
Sortear → reseta AG + gráfico + posições
Simular → guloso (1×) + init populações + is_evolution_running = True
Loop    → throttle 3 gen/s enquanto is_evolution_running
```

Subtítulo botão **Simular:** `"Guloso + AG contínuo"`.

---

## 10. Testes

| Teste | Valida |
|-------|--------|
| `test_vehicle_genetic_tracks_second_best` | 2ª melhor ≠ melhor com pop ≥ 2 |
| `test_throttle_limits_generations` | Mock tempo: N segundos → ≤ gps×N gerações |
| `test_convergence_chart_highlight` | `highlight_index` não levanta exceção |
| Smoke map renderer | Desenha 2 rotas sem erro |

Testes Pygame de integração: fora de escopo (manual).

---

## 11. Fora de escopo

- AG por viagem independente
- Slider de velocidade na UI (fixo 3/s em config; ajuste futuro)
- Mostrar população inteira no mapa
- Remover botão Simular / auto-start no Sortear
- 2ª melhor filtrada por viagem individual no mapa

---

## 12. Critérios de aceite

1. Após **Simular**, gráfico adiciona pontos regularmente (~3/s)
2. Mapa do veículo selecionado mostra **melhor + 2ª melhor** rotas distintas
3. Linha do veículo selecionado destacada no gráfico
4. Cabeçalho exibe número da geração e distâncias
5. **Sortear** reseta evolução e histórico
6. Testes unitários passam
