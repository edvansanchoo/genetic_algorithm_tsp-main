# Design: Malha nativa, bloqueios e remoção de árvores/lagos (Camada 1)

**Data:** 2026-07-09  
**Status:** Aprovado — revisão pós-auditoria do repositório real  
**Branch:** `feature/road-network-blocked-nodes`  
**Commits:** nenhum até pedido explícito do usuário

**Contexto:** O checkout real é o TSP hospitalar de **1 veículo** com prioridades e obstáculos árvore/lago. Não existe pacote `delivery_simulation` nem VRP no `git HEAD`. Esta Camada 1 troca terreno por malha de nós **implementada dentro de** `traveling_salesman_problem`.

---

## 1. Objetivo (Camada 1)

- Remover árvores e lagos da experiência ativa.
- Introduzir malha:
  - **entregas** (genes do GA);
  - **trânsito** (só pathfinding);
  - **bloqueados** (≥ 1; display-only / fora do grafo — rota desvia por outros nós).
- Distância = caminho na malha (BFS), não euclidiana + multa de terreno.
- Manter GA TSP 1 veículo + prioridade.
- **Fora desta camada:** multi-veículo, capacidade, autonomia (Camadas 2–3).

---

## 2. Decisões

| Tópico | Decisão |
|--------|---------|
| Dependência | **Nenhuma** em `delivery_simulation` (ausente no repo) |
| Onde vive a malha | `traveling_salesman_problem/problem/road_network.py` + `delivery_mesh.py` |
| Bloqueio | Pontos; não entram no grafo; desvio via trânsito/entregas |
| Sem caminho | `fitness = ∞` |
| Cromossomo | Permutação de entregas (OX/mutação/elitismo iguais) |
| Git | Branch dedicada; sem commit até pedido |

---

## 3. Arquitetura

```
entregas + trânsito  →  grafo por raio  →  BFS (sem bloqueados)
bloqueados           →  só marcadores no mapa
GA                   →  permutação de entregas
fitness              →  Σ path_distance(ciclo) + w × prioridade
UI                   →  malha + polyline expandida; sem árvores/lagos
```

### Tipos de nó

| Tipo | No grafo? | No GA? |
|------|-----------|--------|
| Entrega `D{i}` | sim | sim |
| Trânsito `T{j}` | sim | não |
| Bloqueado `B{k}` | **não** | não |

### Módulos novos

| Arquivo | Papel |
|---------|--------|
| `problem/road_network.py` | `RoadNetwork`, grafo por raio, `find_path`, `path_distance`, `ensure_connectivity`, `connect_nearest_neighbor` |
| `problem/delivery_mesh.py` | Monta malha (entregas+trânsito+bloqueados), distâncias, polyline expandida |

---

## 4. Fitness

```text
fitness = distância_na_malha (ou ∞) + priority_weight × Σ(prioridade × posição)
```

- Prioridade: regra atual (`city_coordinates[0]` = posição 1).
- 2-opt usa a mesma distância de malha.
- Remover do caminho feliz: penalties de árvore/lago / tecla O.

---

## 5. UI

- Sliders: trânsito, bloqueados (mín. 1).
- Sortear: regenera entregas + malha.
- Mapa: arestas, trânsito cinza, bloqueado com X, rota = path expandido.
- Manter: mutação, prioridade, preset hospitalar, cenários, 2-opt.
- Remover da UX: painel terreno, Árvores/Lagos, tecla O.

---

## 6. Testes mínimos

1. Bloqueado nunca no path.  
2. Sem caminho → `∞`.  
3. Desvio via trânsito quando a geometria exige.  
4. Prioridade ainda entra no fitness.  
5. Entregas mutuamente alcançáveis após rebuild.

---

## 7. Critério de pronto

- `python main.py`: malha + bloqueios + desvio; sem árvores/lagos; GA + prioridade OK.
- Sem VRP/capacidade/autonomia nesta entrega.
- Sem commit até pedido.

---

## 8. Próximas camadas (não nesta entrega)

- **Camada 2:** VRP (depósito, N veículos, capacidade).  
- **Camada 3:** autonomia (spec 07-01 ou km máximo simplificado).
