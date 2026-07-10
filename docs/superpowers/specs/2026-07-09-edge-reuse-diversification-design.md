# Design: Diversificação de rotas na malha (custo de aresta reutilizada)

**Data:** 2026-07-09  
**Status:** Aprovado (brainstorming) — aguardando review do arquivo  
**Branch:** `feature/road-network-blocked-nodes`  
**Commits:** nenhum até pedido explícito do usuário

**Contexto:** Hoje cada trecho do VRP usa sempre o shortest path na malha (`find_path` BFS). Ida e volta (e viagens seguintes do mesmo veículo) tendem a sobrepor as mesmas arestas, ignorando trajetos próximos. Esta camada faz o pathfinding **preferir arestas ainda não usadas** no plano do veículo, com penalidade soft — para visual mais realista e para o GA otimizar custo que reflete essa preferência.

**Depende de:** Camada 1 (malha) + Camada 2 (VRP decoder) + visualização de rotas.

---

## 1. Objetivo

- Visual + algoritmo: rotas podem usar caminhos **não-ótimos locais** quando há alternativa na malha.
- Memória de arestas no **plano do mesmo veículo** (todas as viagens daquele decode).
- Penalidade **soft** (sempre ligada): aresta reutilizada fica mais cara; se for a única opção, ainda é usada (`fitness` finito).
- Cromossomo, atribuição e operadores GA **não mudam**.

**Fora de escopo:** autonomia/combustível; waypoints no gene; k-paths explícitos; memória compartilhada entre veículos; toggle na UI.

---

## 2. Decisões validadas

| Tópico | Decisão |
|--------|---------|
| Objetivo | C — visual + GA sente caminhos alternativos |
| Mecanismo | Diversidade de custo (evitar arestas já usadas) |
| Escopo da memória | B — todas as viagens do mesmo veículo no plano |
| Conflito / único caminho | Soft com multiplicador fixo (recomendação D) |
| Ativação | A — sempre ligado no decoder |
| Abordagem | 1 — pathfinding com custo de aresta (Dijkstra) |
| Fitness | Distância = soma dos **custos weighted** dos trechos |
| UI | Sem toggle; constante no código |
| Git | Sem commit até pedido |

---

## 3. Comportamento

### 3.1 Decode por veículo

```text
used_edges = ∅
para cada trecho (inclui retornos ao depósito e viagens seguintes):
  path = find_path_weighted(origin, dest, used_edges, reuse_penalty)
  se path vazio → fitness = ∞ (como hoje: desconexão/bloqueio)
  senão:
    distância += custo_weighted(path)
    used_edges ∪= arestas(path)
```

- Aresta canônica: `(min(node_a, node_b), max(node_a, node_b))` (grafo não direcionado).
- `reuse_penalty` sugerido: **1.75** (constante nomeada, ex. em settings ou `road_network`).
- Custo de aresta: `euclidean(u,v) * (reuse_penalty se aresta ∈ used_edges senão 1.0)`.

### 3.2 Veículos distintos

Cada chamada a `decode_vehicle_permutation` tem seu próprio `used_edges`. Veículo A não “congesta” a malha para o veículo B.

### 3.3 Visualização / animação

O decoder **persiste** os node-ids (ou coordenadas) de cada trecho no `Trip` / plano. Mapa e animação **só consomem** esses paths — não re-rodam pathfinding com memória paralela. Assim o desenho bate com o custo do fitness.

### 3.4 Compatibilidade

- `used_edges` vazio e `reuse_penalty == 1.0` ≡ comportamento atual (shortest path).
- APIs existentes de `delivery_segment_path` / `distance` ganham parâmetros opcionais com defaults seguros.

---

## 4. Componentes

| Arquivo | Mudança |
|---------|---------|
| `problem/road_network.py` | `find_path_weighted`, helper de aresta canônica, custo weighted |
| `problem/delivery_mesh.py` | Propagar `used_edges` / `reuse_penalty` em segment path/distance |
| `problem/vrp_decoder.py` | Manter `used_edges` ao longo do plano; usar path weighted |
| `problem/vrp_models.py` | Estender `Trip` (ou stops) com `path_node_ids` / polylines por trecho geradas no decode |
| `visualization/route_animation.py` / `map_renderer.py` | Desenhar a partir dos paths guardados no plano (não recalcular shortest path) |
| `config/application_settings.py` | `edge_reuse_penalty: float = 1.75` |
| Testes | Grafo 2 caminhos; grafo 1 caminho; decoder ida≠volta; regressão |

`find_path` BFS atual permanece para checagens de conectividade / compatibilidade; o decode VRP passa a usar `find_path_weighted`.

---

## 5. Testes mínimos

1. **Dois caminhos:** após consumir o curto, o trecho seguinte escolhe o outro sob penalty.
2. **Um caminho:** path finito; sem ∞ só por reuso.
3. **Decoder:** em malha com alternativa, ida e volta de `D→X→D` usam conjuntos de arestas diferentes (ou paths de nós diferentes).
4. **Regressão:** testes VRP/GA/assignment existentes passam; empty used + penalty 1.0 ≡ antigo.

---

## 6. Critério de pronto

- Em cenário com trânsito suficiente, filtro de um veículo mostra ida/volta (ou viagens) **não sempre** sobrepostas.
- Fitness usa custo weighted.
- Sem alteração de cromossomo/assignment.
- Sem commit até pedido explícito.

---

## 7. Fora / próximas camadas

- Camada 3: autonomia/combustível (spec 07-01 ou simplificada).
- Waypoints genéticos ou k-paths explícitos (não nesta entrega).
