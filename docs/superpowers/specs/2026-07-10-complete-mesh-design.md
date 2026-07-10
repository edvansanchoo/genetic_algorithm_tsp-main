# Design: Malha completa (grafo total, sem limite por distância)

**Data:** 2026-07-10  
**Status:** Aprovado (brainstorming) — aguardando review do arquivo  
**Branch:** `feature/road-network-blocked-nodes`

**Contexto:** A malha atual conecta nós apenas se a distância euclidiana ≤ `connection_radius` (140 px). Isso deixa nós de trânsito isolados e entregas com poucas arestas visíveis. O usuário quer que **todos os pontos da malha** (depósito, entregas, trânsito) sejam caminhos possíveis, **sem** limite por distância. Pontos **bloqueados** continuam fora do grafo.

---

## 1. Objetivo

- Substituir o grafo por raio por um **grafo completo** entre todos os nós ativos da malha.
- Garantir que nenhum nó de trânsito ou entrega fique sem arestas.
- Manter bloqueados (`B*`) **fora** de `network.nodes` — só visual + obstáculo no pathfinding.
- Remover `connection_radius` de settings e dos builders de malha da simulação.

**Fora de escopo:** slider de densidade; Delaunay/MST; incluir bloqueados no grafo; mudanças no decoder/`plan_edges`.

---

## 2. Decisões validadas

| Tópico | Decisão |
|--------|---------|
| Topologia | Grafo completo (aresta entre todo par de nós ativos) |
| Bloqueados | Não entram em `nodes`; permanecem em `blocked_ids` / `blocked_coordinates` |
| `connection_radius` | Removido de `ApplicationSettings`, `build_vrp_mesh`, `build_delivery_mesh`, `simulation_state` |
| `build_radius_graph` | Mantido para testes unitários do comportamento por raio |
| `RoadNetwork.connection_radius` | Mantido no dataclass para redes manuais em testes; malha gerada usa `0.0` (sem significado de raio) |
| Custo de aresta | Inalterado: distância euclidiana |
| Pathfinding | Inalterado: Dijkstra/BFS + `blocked_ids` + `plan_edges` |
| Visual | Toggle malha desenha todas as arestas (teia densa — aceito) |

---

## 3. Comportamento

### 3.1 Geração da malha

```text
nodes = { DEPOT, entregas, trânsito T* }
# bloqueados B* → blocked_coordinates apenas, NÃO em nodes

edges = todas as combinações (u, v) com u < v em nodes
network = RoadNetwork(nodes, edges, connection_radius=0.0)
```

Com n nós ativos: `len(edges) = n * (n - 1) / 2`.

### 3.2 Efeito no roteamento

- Caminho mínimo entre dois pontos tende a ser a **aresta direta** (euclidiana).
- Nós de trânsito entram quando atalhos diretos são impossíveis (`blocked_ids`) ou desencorajados (`plan_edges` hard/soft).
- `depot_reaches_all_deliveries` permanece como sanity check; com grafo completo falha só se nó ausente.

### 3.3 Loop de rebuild

`max_rebuild_attempts` continua para re-sortear posições de trânsito/bloqueados; **não** mais por falha de conectividade por raio.

---

## 4. Componentes

| Arquivo | Mudança |
|---------|---------|
| `problem/road_network.py` | `build_complete_graph`, `build_complete_network` |
| `problem/delivery_mesh.py` | Usar grafo completo; remover `connection_radius` dos builders |
| `config/application_settings.py` | Remover `connection_radius` |
| `simulation/simulation_state.py` | Parar de passar raio para `build_vrp_mesh` |
| `tests/test_delivery_mesh.py` | Novos testes de grafo completo; atualizar chamadas a `build_delivery_mesh` |

**Sem mudança:** `map_renderer.py`, `vrp_decoder.py`, `vehicle_genetic.py`, lógica de bloqueados.

---

## 5. Testes

1. **`build_complete_graph`**: n=4 → 6 arestas; todo par conectado.
2. **`build_vrp_mesh` / `build_delivery_mesh`**: todo `transit_id` tem grau ≥ 1; `len(edges) == n*(n-1)/2`.
3. **`test_blocked_node_never_on_path`**: bloqueado fora de `network.nodes`; path não passa por `blocked_ids`.
4. **Regressão**: `test_return_path_diversification`, `test_vrp_decoder*`, `test_vehicle_genetic`, `test_weighted_pathfinding` — redes manuais com arestas explícitas continuam válidas.

Testes que validam **apenas** `build_radius_graph` permanecem inalterados.

---

## 6. Riscos e mitigação

| Risco | Mitigação |
|-------|-----------|
| Malha visual poluída | Aceito nesta versão; toggle malha permite ocultar |
| Performance com muitos nós | ~21 nós → ~210 arestas; Dijkstra trivial |
| Testes com `connection_radius` em `RoadNetwork` manual | Campo mantido no dataclass; valor ignorado quando `edges` é explícito |

---

## 7. Critérios de aceite

- [ ] Nenhum nó de trânsito isolado após `build_vrp_mesh`.
- [ ] Bloqueados sem arestas e fora de `network.nodes`.
- [ ] `connection_radius` ausente de settings e simulação.
- [ ] Suite de testes listada na seção 5 passa.
