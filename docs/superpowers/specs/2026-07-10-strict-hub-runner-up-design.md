# Design: Malha hub estrita + 2ª melhor rota (foco)

**Data:** 2026-07-10  
**Status:** Aprovado (brainstorming) — aguardando review do arquivo  
**Branch:** `feature/road-network-blocked-nodes`  
**Substitui parcialmente:** `2026-07-10-delivery-hub-mesh-design.md` (depósito↔entrega direto revogado)

**Contexto:** A malha hub atual proíbe entrega↔entrega mas ainda permite depósito↔entrega direto. O usuário quer que depósito e entregas sigam a mesma regra (só via trânsito). No TSP original, uma linha cinza mostrava a segunda melhor tentativa; o VRP deve reproduzir isso no veículo focado.

---

## 1. Objetivo

1. **Malha hub estrita:** nenhuma aresta direta entre nós “hub” (`DEPOT` e entregas); ligação apenas via trânsito (`T*`).
2. **2ª melhor rota:** com filtro em veículo focado (`V1`, `V2`, …), desenhar tracejado cinza do melhor plano válido alternativo ao `best_plan` atual.
3. **Malha jogável:** validar alcançabilidade na geração; re-sortear trânsito e subir trânsito efetivo automaticamente se necessário.

**Fora de escopo:** toggle para desligar regra hub; runner-up no painel de texto; histórico de 2ª melhor; animação no runner-up; mudanças no decoder além do que o pathfinding já impõe.

---

## 2. Decisões validadas

| Tópico | Decisão |
|--------|---------|
| Hub sem aresta direta | `hub_nodes = {DEPOT} ∪ delivery_ids`; sem arestas entre pares de hub |
| Arestas permitidas | `DEPOT—T`, `Entrega—T`, `T—T` |
| Entrega→entrega (path) | `no_through={DEPOT}` (inalterado) |
| Runner-up escopo | Só com veículo focado; em “Todos”, não desenha |
| Runner-up definição | Melhor plano válido da geração atual ≠ `best_plan` |
| Runner-up visual | Tracejado cinza (`route_second_best`), width=1, sem setas |
| Trânsito automático | Validar malha; re-sortear; bump `+2` até máximo do slider |
| Margem trânsito | `ceil(tokens / veículos) + 10` (era `+6`) |

---

## 3. Malha hub estrita

### 3.1 Topologia

```text
Permitido:     DEPOT—T, Entrega—T, T—T
Proibido:      Entrega—Entrega, DEPOT—Entrega
```

### 3.2 `build_delivery_hub_network`

Generalizar a regra existente:

```python
hub_set = {DEPOT_ID, *delivery_ids}
# Para cada par (a, b): se a ∈ hub_set e b ∈ hub_set → não criar aresta
```

Demais pares (hub↔trânsito, trânsito↔trânsito) permanecem no grafo completo entre não-hubs.

### 3.3 Pathfinding

- `delivery_segment_path` inalterado em estrutura: `no_through={DEPOT}` só em segmentos entrega→entrega.
- Depósito→entrega e entrega→depósito não têm aresta direta; Dijkstra obriga passagem por `T*`.
- Decoder (`plan_edges`, `plan_nodes`, não reutilização) sem mudança de interface.

### 3.4 Efeito visual da malha

- Some aresta cinza malha entre depósito e entregas.
- Rotas expandidas do GA passam por nós de trânsito ao sair/voltar ao depósito.

---

## 4. Validação e trânsito automático

### 4.1 `effective_transit_count`

```python
minimum = math.ceil(token_count / vehicle_count) + 10
return min(maximum_transit, max(requested_transit, minimum))
```

### 4.2 Loop `build_vrp_mesh`

Até `max_rebuild_attempts` (40) por valor de `effective_transit`:

1. Gerar nós de trânsito/bloqueados.
2. Montar malha com `build_delivery_hub_network`.
3. Validar:
   - `depot_reaches_all_deliveries(mesh)`
   - `deliveries_mutually_reachable(mesh)` (com `no_through={DEPOT}` em pares entrega↔entrega)
4. Se falhar: re-sortear posições (nova tentativa no loop interno).
5. Se esgotar 40 tentativas com o trânsito atual: `effective_transit += 2` (cap em `maximum_mesh_nodes_per_type`) e repetir.
6. Se esgotar máximo global: `RuntimeError("Could not build reachable VRP mesh")`.

### 4.3 `rebuild_scenario`

Continua usando `effective_transit_count`; `last_effective_transit_count` evita rebuild em loop (já implementado).

---

## 5. Segunda melhor rota

### 5.1 Dados (`vehicle_genetic.py`)

Após avaliar e ordenar a população em `run_vehicle_generation`:

1. `best` = primeiro da lista (lógica atual de `best_plan`).
2. `runner_up` = primeiro plano nas posições 2…N tal que:
   - `plan_has_drawable_trips(plan)` é verdadeiro
   - permutação ≠ `best_permutation` **ou** fitness estritamente maior que `best_fitness`
3. Armazenar em `VehicleGeneticState.runner_up_plan: Optional[DecodedVehiclePlan]`.
4. Se nenhum candidato: `runner_up_plan = None`.

Recalculado a cada geração (não é histórico).

### 5.2 Propagação (`simulation_state.py`)

`run_one_generation` retorna tupla estendida ou dict paralelo:

```python
runner_up_plans: Dict[int, DecodedVehiclePlan]  # só entradas com plano desenhável
```

### 5.3 Render (`map_renderer.py` + `pygame_application.py`)

| Filtro | Melhor | Runner-up |
|--------|--------|-----------|
| `focus_vehicle_id is None` | Todas coloridas | Não desenha |
| `focus_vehicle_id == n` | Vn colorida + setas | Vn tracejado cinza, se existir |

- Função `draw_runner_up_plan(screen, mesh, plan, color=route_second_best)`.
- Reutiliza `_draw_dashed_polyline` para **todas** as viagens do plano.
- `width=1`, sem setas, sem animação.
- Desenhar **antes** de `draw_vehicle_plans` (fica atrás da melhor rota).

### 5.4 Legenda

Adicionar em `draw_map_legend`:

```text
(route_second_best, "2ª melhor (foco)")
```

---

## 6. Componentes

| Arquivo | Mudança |
|---------|---------|
| `problem/road_network.py` | `build_delivery_hub_network` — hub_set inclui `DEPOT` |
| `problem/delivery_mesh.py` | `effective_transit_count` margem `+10`; loop bump em `build_vrp_mesh` |
| `simulation/vehicle_genetic.py` | `runner_up_plan`; seleção na geração |
| `simulation/simulation_state.py` | Propagar `runner_up_plans` |
| `simulation/pygame_application.py` | Desenhar runner-up quando focado |
| `visualization/map_renderer.py` | `draw_runner_up_plan` |
| `visualization/application_layout.py` | Item na legenda |
| `tests/test_delivery_hub_mesh.py` | Topologia estrita + paths |
| `tests/test_vehicle_genetic.py` | Runner-up seleção |
| `tests/test_delivery_mesh.py` | Margem `+10` em `effective_transit_count` |

**Sem mudança de interface pública:** `vrp_decoder.py`, `decode_vehicle_permutation`.

---

## 7. Testes

### 7.1 Malha

1. Nenhuma aresta entre dois `delivery_ids`.
2. Nenhuma aresta entre `DEPOT` e qualquer `delivery_id`.
3. Path `DEPOT→entrega` contém algum `transit_id`; comprimento ≥ 3 nós.
4. Path `entrega→entrega` contém trânsito; `DEPOT` não é intermediário.
5. `build_vrp_mesh` padrão (12 entregas, seed fixo) retorna malha alcançável.
6. `effective_transit_count`: margem `+10` verificada em teste unitário.

### 7.2 Runner-up

1. População com ≥2 planos válidos distintos → `runner_up_plan` preenchido e ≠ `best_plan`.
2. Apenas 1 plano válido → `runner_up_plan is None`.
3. Candidatos com `fitness = ∞` ou sem viagens ignorados.

### 7.3 Render (leve)

1. `focus_vehicle_id=None` → `draw_runner_up_plan` não invocado (ou plano vazio).
2. Foco em Vn com `runner_up_plans[n]` → desenho tracejado.

### 7.4 Regressão

- `test_vrp_decoder`, `test_return_path_diversification`, `test_delivery_mesh`, demais 79+ testes.

---

## 8. Critérios de aceite

- [ ] Malha sem arestas depósito↔entrega nem entrega↔entrega.
- [ ] Rotas GA passam por trânsito ao sair/voltar ao depósito.
- [ ] Filtro **Vn**: melhor colorida + tracejado cinza (2ª válida), quando existir.
- [ ] Filtro **Todos**: só melhores rotas, sem cinza.
- [ ] Legenda “2ª melhor (foco)”.
- [ ] Cenário padrão gera malha alcançável sem ajuste manual de trânsito.
- [ ] Suite de testes passa.
