# Design: Malha hub — entregas só via trânsito

**Data:** 2026-07-10  
**Status:** Aprovado (brainstorming) — aguardando review do arquivo  
**Branch:** `feature/road-network-blocked-nodes`

**Contexto:** Com grafo completo, entregas ligam diretamente entre si e o pathfinding usa atalhos `Entrega→Entrega`. O usuário quer que **dois pontos de entrega nunca se liguem diretamente**; o deslocamento entre entregas deve passar por **nó de trânsito (T)**. Ligação **entrega↔depósito** direta permanece válida. Depósito **não** pode ser intermediário entre duas entregas.

---

## 1. Objetivo

- Remover arestas **entrega↔entrega** do grafo da malha.
- Pathfinding **entrega→entrega**: obrigar passagem por trânsito; proibir depósito como hop intermediário.
- Garantir **mínimo 1 nó de trânsito** por cenário.

**Fora de escopo:** toggle para desligar regra; depósito como intermediário opcional; mudanças no GA/decoder além do pathfinding.

---

## 2. Decisões validadas

| Tópico | Decisão |
|--------|---------|
| Intermediário entre entregas | Somente trânsito (`T*`) |
| Entrega↔depósito | Aresta direta permitida |
| Depósito entre duas entregas | Proibido (`no_through={DEPOT}`) |
| Arestas entrega↔entrega | Não existem no grafo |
| Trânsito mínimo | 1 (slider clamp + validação) |
| Bloqueados | Fora do grafo (inalterado) |
| Demais arestas | depósito↔trânsito, entrega↔trânsito, trânsito↔trânsito |

---

## 3. Topologia

```text
Permitido:     DEPOT—Entrega, DEPOT—T, Entrega—T, T—T
Proibido:      Entrega—Entrega
```

Função `build_delivery_hub_network(nodes, delivery_ids, depot_id)` gera arestas do grafo completo **exceto** pares onde ambos ∈ `delivery_ids`.

---

## 4. Pathfinding

### 4.1 `no_through`

Novo parâmetro em `find_path` e `find_path_weighted`:

```python
no_through: Optional[Set[str]] = None
```

Nós em `no_through` podem ser **origem ou destino** do caminho, mas **não** nó intermediário na expansão.

### 4.2 `delivery_segment_path`

```python
no_through = None
if origin_id in mesh.delivery_ids and destination_id in mesh.delivery_ids:
    no_through = {DEPOT_ID}
```

Propagar para `find_path_weighted`.

### 4.3 Validação de malha

- `depot_reaches_all_deliveries`: path depósito→entrega (sem `no_through` especial).
- `deliveries_mutually_reachable`: path entrega→entrega com `no_through={DEPOT}`.

---

## 5. UI / settings

- Slider **Trânsito**: `minimum_value = 1`.
- `rebuild_scenario`: `transit_count = max(1, transit_count)`.

---

## 6. Componentes

| Arquivo | Mudança |
|---------|---------|
| `problem/road_network.py` | `build_delivery_hub_network`; `no_through` em pathfinding |
| `problem/delivery_mesh.py` | Usar hub network; propagar `no_through` em segment/reachability |
| `simulation/simulation_state.py` | Trânsito mínimo 1 |
| `tests/test_delivery_hub_mesh.py` (novo) | Topologia + paths |

**Sem mudança:** `vrp_decoder.py` (usa `delivery_segment_path`), `map_renderer.py`.

---

## 7. Testes

1. Nenhuma aresta entre dois `delivery_ids`.
2. Path entrega→entrega contém algum `transit_id`; `DEPOT` não aparece no meio.
3. Path depósito→entrega pode ser direto (2 nós).
4. `transit_count` clamped to ≥ 1.
5. Regressão: `test_vrp_decoder`, `test_delivery_mesh`, `test_return_path_diversification`.

---

## 8. Critérios de aceite

- [ ] Sem linhas malha entre pares de entregas.
- [ ] Rotas entre entregas passam por trânsito.
- [ ] `D→entrega` e `entrega→D` diretos funcionam.
- [ ] Trânsito mínimo = 1.
- [ ] Testes passam.
