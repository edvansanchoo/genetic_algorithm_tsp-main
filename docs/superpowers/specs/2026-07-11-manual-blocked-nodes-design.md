# Design: Bloqueio manual de nós no mapa

**Data:** 2026-07-11  
**Status:** Aprovado (brainstorming) — aguardando review do arquivo  
**Branch:** `feature/road-network-blocked-nodes`

**Contexto:** Ao mover o slider "Bloqueados", `rebuild_scenario()` regenera a malha inteira porque `blocked_count` entra no seed RNG. Isso reposiciona nós de trânsito e reinicia o GA, embora depósito e entregas sejam preservados. O usuário quer bloquear **pontos já existentes** no mapa, manter posições estáveis e forçar novas rotas sem alterar as rotas já exibidas.

---

## 1. Objetivo

- Substituir o slider "Bloqueados" por **clique no mapa** (toggle bloquear/desbloquear).
- Qualquer nó visível pode ser bloqueado: trânsito, entrega ou depósito.
- Bloquear/desbloquear faz **atualização incremental** da malha — sem `rebuild_scenario` completo.
- Rotas já desenhadas permanecem iguais; nó desbloqueado fica disponível apenas para rotas **futuras** (próximas gerações do GA).
- Cenário novo começa com **0 bloqueados**; usuário marca manualmente.

**Fora de escopo:** modo bloqueio separado na sidebar; persistir bloqueios entre sessões; recalcular rotas existentes ao desbloquear; bloquear arestas individuais.

---

## 2. Decisões validadas

| Tópico | Decisão |
|--------|---------|
| Seleção | Clique no nó mais próximo (toggle) |
| Tipos bloqueáveis | Trânsito, entrega, depósito |
| Slider "Bloqueados" | **Removido** |
| Efeito na simulação | Só atualiza malha; GA e `best_plan` intactos |
| Rotas exibidas | Usam `trip.path_node_ids` armazenados — não recalculam |
| Novas rotas | Pathfinding usa `blocked_ids` atualizado |
| Rebuild (trânsito, sortear, resize) | Limpa `blocked_ids` |
| Seed da malha | **Não** inclui `blocked_count` |
| Geração aleatória de bloqueados | **Removida** de `build_vrp_mesh` / `build_delivery_mesh` |
| Bloquear depósito/entrega | Permitido; novas avaliações podem retornar fitness `∞` |

---

## 3. Comportamento e UX

### 3.1 Interação

- Clique esquerdo na área do mapa (`x >= plot_horizontal_offset`) no nó mais próximo dentro do raio de hit (`city_node_radius + 6px`).
- Cliques na sidebar são ignorados.
- 1º clique → bloqueia (overlay vermelho com X).
- 2º clique no mesmo nó → desbloqueia (volta à aparência normal).

### 3.2 Prioridade do hit-test

1. Nós em `blocked_coordinates` (para desbloquear)
2. Depósito
3. Entregas
4. Trânsito em `network.nodes`

### 3.3 O que não muda ao bloquear/desbloquear

- Posições de depósito, entregas e trânsito.
- `best_plan`, `runner_up_plan`, população do GA, contador de geração.
- Polylines desenhadas (caminhos em `trip.path_node_ids`).

### 3.4 O que muda

- `blocked_ids` e `blocked_coordinates` na malha.
- Nó bloqueado removido de `network.nodes`; arestas reconstruídas.
- Próximas gerações do GA avaliam fitness com malha atualizada.
- Nó desbloqueado volta ao grafo e pode aparecer em caminhos novos.

### 3.5 UI

- Seção "Malha": slider Trânsito ocupa largura total (sem slider Bloqueados).
- Legenda mantém "Nó bloqueado".
- Ordem de desenho: trânsito → malha → rotas → entregas → depósito → **bloqueados por cima**.

### 3.6 Reset de bloqueios

- `shuffle_all` / "Sortear posições": `blocked_ids` zerado.
- `rebuild_scenario` (slider trânsito, veículos, capacidade): `blocked_ids` zerado.
- Resize da janela: rebuild limpa bloqueios (aceitável).

---

## 4. Arquitetura técnica

### 4.1 Modelo de dados

```
DeliveryMesh
  network.nodes     → só nós ativos (não bloqueados)
  blocked_ids       → Set[str] controlado por cliques
  blocked_coordinates → Dict[str, Coordinate] para overlay e paths armazenados
```

Bloquear = mover nó de `network.nodes` para `blocked_ids` + `blocked_coordinates`.  
Desbloquear = operação inversa + reconstruir arestas.

### 4.2 Novas funções (`delivery_mesh.py`)

| Função | Papel |
|--------|-------|
| `resolve_node_coordinate(mesh, node_id)` | Lookup em `network.nodes` ou `blocked_coordinates` |
| `rebuild_mesh_network(mesh)` | Reconstrói `network` com nós ativos |
| `toggle_node_blocked(mesh, node_id, delivery_ids)` | Toggle incremental |

### 4.3 Seed

`_mesh_rng_seed(depot, deliveries, transit_count)` — sem `blocked_count`.

### 4.4 Builders

`build_vrp_mesh` e `build_delivery_mesh`:
- Geram apenas `transit_count` nós extras (não `transit_count + blocked_count`).
- Inicializam `blocked_ids = {}`, `blocked_coordinates = {}`.
- Parâmetro `blocked_count` removido (ou ignorado com deprecação nos testes).

### 4.5 Rotas armazenadas

`_trip_polyline_from_stored` em `map_renderer.py` usa `resolve_node_coordinate` ao expandir `path_node_ids`. Caminhos que passam por nó bloqueado continuam renderizando a rota histórica.

### 4.6 Pathfinding

Sem mudança em `find_path` — já recebe `blocked=mesh.blocked_ids`. Nós bloqueados estão fora do grafo e no set `blocked` (defesa em profundidade).

### 4.7 Simulação (`simulation_state.py`)

| Mudança | Detalhe |
|---------|---------|
| Remover | `blocked_count_slider`, `last_blocked_count`, checks em `update_controls_if_changed` |
| Adicionar | `toggle_blocked_at(screen_pos)` — hit-test + `toggle_node_blocked` |
| `rebuild_scenario` | Não passa `blocked_count`; zera bloqueios |

### 4.8 Eventos (`pygame_application.py`)

- `MOUSEBUTTONDOWN` no mapa → `simulation.toggle_blocked_at(event.pos)`.
- Remover draw/handle do slider bloqueados.
- Remover salvamento de `saved_blocked` no resize.

### 4.9 Hit-test (`map_hit_test.py`)

Função pura testável:

```python
hit_test_map_node(
    mesh, depot, deliveries, screen_pos, hit_radius
) -> Optional[str]
```

---

## 5. Consequências de bloquear nós críticos

| Nó bloqueado | Rotas exibidas | Novas avaliações GA |
|--------------|----------------|---------------------|
| Trânsito Tn | Intactas (path armazenado) | Desvia por outros nós |
| Entrega D | Intactas | Decoder pode falhar (`∞`) |
| Depósito | Intactas | Retorno ao depósito falha (`∞`) |

Comportamento aceito — usuário escolheu bloquear qualquer nó.

---

## 6. Testes

| Teste | Verifica |
|-------|----------|
| `test_toggle_block_transit_node` | T1 sai do grafo, coordenada em `blocked_coordinates` |
| `test_toggle_unblock_restores_graph` | T1 volta com arestas |
| `test_blocked_independent_of_transit_positions` | Toggle não move outros nós |
| `test_resolve_coordinate_blocked_node` | Path armazenado resolve coord de nó bloqueado |
| `test_hit_test_blocked_node` | Clique perto de bloqueado retorna id |
| Atualizar `test_delivery_mesh.py` | Remover/adaptar testes com `blocked_count` na geração |

---

## 7. Arquivos afetados

| Arquivo | Ação |
|---------|------|
| `problem/delivery_mesh.py` | Toggle, resolve, rebuild; remover geração aleatória |
| `simulation/simulation_state.py` | Remover slider; `toggle_blocked_at` |
| `simulation/pygame_application.py` | Clique mapa; draw order |
| `visualization/map_renderer.py` | `resolve_node_coordinate` no polyline |
| `visualization/map_hit_test.py` | **Novo** |
| `config/application_settings.py` | Remover `initial_blocked_count` |
| `visualization/application_layout.py` | Slider trânsito largura total |
| `tests/test_delivery_mesh.py` | Adaptar + novos testes |

---

## 8. Critérios de aceite

1. Mover bloqueios via clique **não** reposiciona nenhum ponto no mapa.
2. Rotas desenhadas permanecem iguais imediatamente após bloquear/desbloquear.
3. Nó desbloqueado pode aparecer em rotas de gerações posteriores.
4. Slider "Bloqueados" ausente da sidebar.
5. Sortear posições limpa todos os bloqueios.
6. Testes unitários passam.
