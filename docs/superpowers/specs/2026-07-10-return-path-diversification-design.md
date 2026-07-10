# Design: Retorno ao depósito com rota diferente da ida

**Data:** 2026-07-10  
**Status:** Aprovado (brainstorming) — aguardando review do arquivo  
**Branch:** `feature/road-network-blocked-nodes`  
**Commits:** spec commitada; implementação segue plano separado

**Contexto:** A Camada edge-reuse (2026-07-09) penaliza arestas reutilizadas com multiplicador soft (×1.75), mas ida e volta ainda se sobrepõem quando a malha tem poucas alternativas ou o caminho curto continua vantajoso. O usuário quer **forçar** retorno diferente da ida, mesmo que mais longo.

**Depende de:** `docs/superpowers/specs/2026-07-09-edge-reuse-diversification-design.md`, Camada 2 VRP.

---

## 1. Objetivo

- Trecho **última parada → depósito** de cada viagem deve **evitar** arestas já usadas na mesma viagem.
- Se existir alternativa na malha, retorno usa caminho **disjunto** (arestas diferentes) da ida.
- Se não existir, **fallback soft forte** (×20) — nunca `∞` só por reuso.
- Demais trechos mantêm penalidade soft ×1.75 no plano do veículo.
- Cromossomo, atribuição e GA **não mudam**.

**Fora de escopo:** proibir reuso em todos os trechos; malha com corredores paralelos obrigatórios; toggle UI; autonomia.

---

## 2. Decisões validadas

| Tópico | Decisão |
|--------|---------|
| Quando não há alternativa “barata” | B — forçar volta diferente mesmo mais longa |
| Mecanismo | 1 — hard no retorno + fallback soft forte |
| Arestas proibidas no retorno | B — todas as arestas da viagem atual |
| Fallback | Soft ×20 se hard não achar path |
| Trechos não-retorno | Soft ×1.75 (comportamento atual) |
| `edge_reuse_penalty` | 1.75 (inalterado) |
| `return_fallback_penalty` | 20.0 (novo) |
| Visual | `Trip.path_node_ids` + mapa/animação (sem recalcular path) |

---

## 3. Comportamento

### 3.1 Por viagem

```text
trip_edges = ∅
used_edges_veículo = ∅  # persiste entre viagens do mesmo decode

para cada trecho NÃO-retorno (D→entrega, entrega→entrega):
  path = find_path_weighted(used_edges=used_edges_veículo, penalty=1.75)
  trip_edges ∪= arestas(path)
  used_edges_veículo ∪= arestas(path)
  distância += custo_weighted(path)

ao fechar viagem (última parada → D):
  path = find_path_weighted(forbidden_edges=trip_edges)
  se path vazio:
    path = find_path_weighted(used_edges=trip_edges, penalty=20.0)
  se path ainda vazio:
    fitness = ∞  # desconexão real
  senão:
    distância += path_distance(path)  # custo real, sem penalidade extra
    used_edges_veículo ∪= arestas(path)
  trip_edges reinicia na próxima viagem
```

### 3.2 `forbidden_edges`

- Conjunto de `EdgeKey` canônicas `(min_id, max_id)`.
- Aresta em `forbidden_edges` **não pode** ser percorrida (custo tratado como ∞ no Dijkstra).
- Distinto de `used_edges` (penalidade multiplicativa).

### 3.3 Custo do retorno

- Caminho encontrado via hard block: distância euclidiana **real** (soma dos segmentos).
- Caminho via fallback: `path_weighted_distance` com `reuse_penalty=20`.

### 3.4 Visualização

- Decoder persiste paths em `Trip.path_node_ids` como hoje.
- Mapa e animação **não** recalculam pathfinding.

---

## 4. Componentes

| Arquivo | Mudança |
|---------|---------|
| `problem/road_network.py` | `find_path_weighted(..., forbidden_edges: Optional[Set[EdgeKey]] = None)` |
| `problem/delivery_mesh.py` | Propagar `forbidden_edges` em segment path/distance |
| `problem/vrp_decoder.py` | `trip_edges`; hard return; fallback; reset por viagem |
| `config/application_settings.py` | `return_fallback_penalty: float = 20.0` |
| Testes | `test_return_path_diversification.py` ou estender existentes |

---

## 5. Testes mínimos

1. **Hard:** diamante D—A—X / D—B—X; após ida por A, retorno X→D usa B (arestas da ida proibidas).
2. **Fallback:** linha D—X; retorno ainda finito (pode repetir rota).
3. **Decoder:** `path_node_ids[0]` e `path_node_ids[1]` com arestas diferentes quando alternativa existe.
4. **Regressão:** `test_weighted_pathfinding`, `test_vrp_decoder_edge_reuse`, suite VRP.

---

## 6. Critério de pronto

- Filtro de um veículo: retorno ao D visualmente distinto da ida na maioria dos cenários com trânsito.
- Fitness reflete custo real ou weighted do fallback.
- Sem mudança de cromossomo/assignment.

---

## 7. Relação com edge-reuse (2026-07-09)

Esta camada **refina** o retorno ao depósito; não substitui a memória `used_edges` do veículo nos demais trechos. Spec anterior permanece válida para trechos intermediários e viagens seguintes.
