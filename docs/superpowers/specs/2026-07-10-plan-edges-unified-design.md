# Design: Memória unificada de arestas no plano do veículo (TSP-like)

**Data:** 2026-07-10  
**Status:** Aprovado (brainstorming) — aguardando review do arquivo  
**Branch:** `feature/road-network-blocked-nodes`  
**Commits:** spec commitada; implementação segue plano separado

**Contexto:** Os specs 07-09 (soft ×1.75 no veículo) e 07-10 (hard no retorno só da viagem atual) ainda permitem reutilizar arestas entre viagens do mesmo veículo. O usuário quer comportamento **TSP-like**: aresta usada em qualquer trecho do plano não deve ser reutilizada em viagens seguintes nem em retornos — com modelo unificado mais simples.

**Depende de:** Camada 2 VRP, edge-reuse (07-09), return diversification (07-10). **Substitui** a lógica dual `trip_edges` + `used_edges` por um único `plan_edges`.

---

## 1. Objetivo

- Um conjunto **`plan_edges`** acumula todas as arestas percorridas no decode de **um veículo** (todas as viagens).
- **Todo** trecho (ida, volta, viagem 2+) tenta evitar `plan_edges` com escalação em 3 níveis.
- Nó depósito pode ser revisitado; **arestas** não devem repetir quando houver alternativa.
- Cromossomo, atribuição e GA **não mudam**.
- Visual: `Trip.path_node_ids` inalterado.

**Fora de escopo:** memória entre veículos; toggle UI; autonomia; mudança na malha.

---

## 2. Decisões validadas

| Tópico | Decisão |
|--------|---------|
| Escopo | Plano inteiro do veículo (todas as viagens) |
| Mecanismo | Hard primeiro + fallback soft (recomendação D) |
| Modelo | A — unificar; remover `trip_edges` / `used_edges` separados |
| Níveis | 1 hard forbidden → 2 soft ×20 → 3 soft ×1.75 → ∞ |
| Penalidades | `plan_fallback_penalty = 20.0`, `plan_last_resort_penalty = 1.75` |
| Custo hard | `path_distance` (euclidiana real) |
| Custo fallback | `path_weighted_distance` com penalty do nível |
| Veículos | Memória independente por decode |

---

## 3. Comportamento

### 3.1 Algoritmo por trecho

```text
plan_edges = ∅

função segmento(origem, destino):
  path = delivery_segment_path(..., forbidden_edges=plan_edges)
  se path: custo = path_distance; goto registrar

  path = delivery_segment_path(..., used_edges=plan_edges, penalty=20)
  se path: custo = path_weighted_distance(..., 20); goto registrar

  path = delivery_segment_path(..., used_edges=plan_edges, penalty=1.75)
  se path: custo = path_weighted_distance(..., 1.75); goto registrar

  retornar inválido (∞)

registrar:
  plan_edges ∪= arestas(path)
  retornar custo, path
```

Aplicar a **todos** os trechos: `D→entrega`, `entrega→entrega`, `última→D`, e trechos da viagem 2+ após split de capacidade.

### 3.2 Relação com specs anteriores

| Antes | Depois |
|-------|--------|
| `used_edges` soft ×1.75 só na ida | Absorvido em `plan_edges` nível 3 |
| `trip_edges` hard só no retorno da viagem | Absorvido em `plan_edges` nível 1 em **todos** os trechos |
| `trip_edges` reset por viagem | Removido — `plan_edges` **não** reseta entre viagens |

### 3.3 Visualização

Decoder persiste paths em `Trip.path_node_ids`. Mapa/animação não recalculam pathfinding.

---

## 4. Componentes

| Arquivo | Mudança |
|---------|---------|
| `problem/vrp_decoder.py` | `_segment_with_plan_memory(plan_edges, ...)`; remover `_return_segment`, `trip_edges`, dual traverse |
| `config/application_settings.py` | Opcional: renomear `return_fallback_penalty` → `plan_fallback_penalty`; manter `edge_reuse_penalty` como `plan_last_resort_penalty` (ou aliases) |
| `simulation/vehicle_genetic.py` | Passar penalties renomeados se settings mudar |
| Testes | Caso 2 viagens; regressão retorno; fallback linha única |

`road_network.py` e `delivery_mesh.py` **sem** mudança de API.

---

## 5. Testes mínimos

1. **Inter-viagem:** 2 viagens por capacidade; viagem 2 não compartilha arestas com viagem 1+retorno (malha com alternativa).
2. **Retorno:** `D→X→D` diamante — paths de ida e volta distintos (regressão).
3. **Fallback:** linha `D—X` — fitness finito.
4. **Regressão:** `test_return_path_diversification`, `test_vrp_decoder_edge_reuse`, suite VRP/GA.

---

## 6. Critério de pronto

- Arestas usadas na viagem 1 indisponíveis na viagem 2 (hard ou fallback visível).
- Decoder sem `trip_edges` / `used_edges` duplicados.
- Testes passam; manual com filtro Vn mostra rotas menos sobrepostas entre viagens.

---

## 7. Settings (nomes sugeridos)

```python
plan_fallback_penalty: float = 20.0      # nível 2
plan_last_resort_penalty: float = 1.75    # nível 3 (ex edge_reuse_penalty)
```

Migração: remover ou deprecar `return_fallback_penalty` no decoder; wire único helper.
