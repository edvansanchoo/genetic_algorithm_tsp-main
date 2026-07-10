# Design: Camada 2 — VRP hospitalar (depósito, frota, capacidade)

**Data:** 2026-07-09  
**Status:** Aprovado (brainstorming) — aguardando review do arquivo  
**Branch:** `feature/road-network-blocked-nodes` (continuidade da Camada 1)  
**Commits:** nenhum até pedido explícito do usuário

**Contexto:** A Camada 1 entregou TSP de 1 veículo com malha (trânsito/bloqueados), pathfinding e prioridade. A Camada 2 amplia para o **Problema de Roteamento de Veículos (VRP)** exigido pelo Tech Challenge: depósito real, múltiplos veículos, capacidade limitada e retorno ao depósito — mantendo GA e a malha existente.

**Depende de:** `docs/superpowers/specs/2026-07-09-road-network-blocked-nodes-design.md` (Camada 1).

---

## 1. Objetivo

- Introduzir **depósito separado** (não é gene de entrega): toda viagem `Depósito → … → Depósito`.
- Suportar **N veículos** (configurável na sidebar) com **capacidade** configurável (itens por viagem).
- Cada entrega tem **demanda** (itens) + prioridade (Camada 1).
- **Atribuição fixa** das entregas aos veículos (guloso por proximidade / balanceamento de carga), depois **GA (TSP) por veículo**.
- Decoder de capacidade: se não cabe, fecha viagem (volta ao depósito) e abre outra.
- Distâncias continuam na **malha** (pathfinding; bloqueados fora do grafo).
- Visualizar rotas por cor de veículo, com retornos ao depósito.

**Fora desta camada:** autonomia/combustível (Camada 3); cromossomo global que troca entregas entre veículos durante a evolução.

---

## 2. Decisões validadas

| Tópico | Decisão |
|--------|---------|
| Encoding GA | A — atribuição fixa + TSP/população por veículo |
| Depósito | B — ponto separado das entregas |
| Frota / capacidade | B — sliders na sidebar (veículos + capacidade) |
| Atribuição | B — guloso por proximidade + balanceamento de carga |
| Abordagem de produto | 1 — estender o app TSP atual (`main.py` único) |
| Malha | Reutilizar Camada 1; depósito entra como nó do grafo |
| Operadores | OX + mutação + elitismo por veículo (reuso) |
| Sem caminho na malha | `fitness = ∞` |
| Git | Sem commit até pedido explícito |

---

## 3. Arquitetura

### 3.1 Entidades

| Entidade | Campos principais | Papel |
|----------|-------------------|--------|
| Depósito | coordenada, id `DEPOT` | Origem/fim de toda viagem |
| Entrega | id, coordenada, prioridade, demanda | Parada obrigatória |
| Token | (entrega_id, quantidade) | Gene quando demanda > capacidade |
| Veículo | id, cor UI | Dono de uma população GA |
| Viagem | stops (depósito…depósito), distância | Resultado do decoder |
| Malha | entregas + depósito + trânsito; bloqueados display-only | Distâncias |

### 3.2 Fluxo

```text
gerar depósito + entregas (demanda/prioridade) + malha
  → atribuir entregas aos veículos (guloso)
  → tokens por veículo (partir demanda se > capacidade)
  → N populações (permutações de tokens)
  → por geração, por veículo:
        avaliar decoder(capacidade) + distância_malha + w×prioridade
        elitismo + OX + mutação (+ 2-opt opcional)
  → mapa: polylines por veículo; gráfico: N séries
```

### 3.3 Módulos novos (estimativa)

| Arquivo | Responsabilidade |
|---------|------------------|
| `traveling_salesman_problem/problem/vrp_models.py` | Depósito, entrega, token, viagem, veículo |
| `traveling_salesman_problem/problem/vrp_assignment.py` | Atribuição gulosa + balanceamento |
| `traveling_salesman_problem/problem/vrp_decoder.py` | Permutação → viagens com capacidade e retorno |
| `traveling_salesman_problem/simulation/vehicle_genetic.py` (ou equivalente) | Estado/população por veículo; uma geração |

### 3.4 Arquivos a adaptar

- `delivery_mesh` / `road_network` — incluir depósito no grafo
- `simulation_state.py`, `pygame_application.py` — estado VRP, sliders, N GAs
- `fitness` / avaliação — via decoder + malha
- `map_renderer`, `application_layout`, `visual_theme`, `convergence_chart` — depósito, cores, N linhas
- Geração de pontos / cenários — depósito + demandas

---

## 4. Fitness, decoder e GA

### 4.1 Cromossomo (por veículo)

Lista ordenada de tokens `(entrega_id, qty)` atribuídos àquele veículo.  
Exemplo: demanda 14, capacidade 10 → `[A:10, A:4]`.

### 4.2 Decoder

Partindo do depósito, carga = 0:

1. Próximo token cabe na capacidade restante → inclui na viagem atual.  
2. Não cabe → fecha viagem (`→ Depósito`), zera carga, inicia nova viagem com o token.  
3. Ao fim da permutação → retorna ao depósito.

Cada trecho usa distância na malha (`find_path` / `path_distance`).

### 4.3 Fitness por veículo

```text
distância = Σ path_malha de todas as viagens (inclui retornos)
prioridade = Σ (prioridade × ordem_de_visita)  // visitas do veículo a partir da 1ª saída
fitness_veículo = distância + priority_weight × prioridade
```

Fitness global exibido = soma dos veículos (e/ou breakdown).

### 4.4 Atribuição

1. Ordenar entregas por distância ao depósito (preferir malha; euclidiana aceitável se mais simples no MVP).  
2. Atribuir cada entrega ao veículo com **menor carga total acumulada** (soma das demandas já atribuídas).  
3. Desempate: menor id de veículo.  
4. Reatribuir ao mudar N veículos, capacidade relevante para tokens, demandas ou “Sortear”.

### 4.5 Evolução

- Uma geração do loop principal avança **todas** as populações de veículo.  
- 2-opt (se ativo) só na permutação do veículo; avaliação sempre pelo decoder + malha.  
- Mapear `inf →` valor grande finito na seleção de pais (como Camada 1).

---

## 5. Visualização e controles

### 5.1 Mapa

- Depósito: marcador distinto (“D”).  
- Entregas: cor por prioridade.  
- Malha: trânsito, bloqueados, arestas (Camada 1).  
- Rotas: cor por veículo; polyline expandida; viagens extras do mesmo veículo com opacidade/traço diferente.  
- Ordem de visita: por veículo (mapa e/ou painel), não um único ciclo TSP 1…N.

### 5.2 Sidebar

- Slider **nº de veículos** (faixa sugerida: 1–5; default 2 ou 3).  
- Slider **capacidade** (itens/viagem; default ex. 10).  
- Manter: mutação, peso prioridade, preset hospitalar, trânsito/bloqueados, sortear, 2-opt, cenários (adaptados).  
- Remover narrativa de “cidade 1 = origem do ciclo TSP”.

### 5.3 Gráfico e stats

- Convergência: **N linhas** (melhor custo/distância por veículo).  
- Header: distância total (soma), prioridade, geração; opcional por veículo.

### 5.4 Feedback

- Mudar veículos/capacidade → reatribuir + reiniciar populações + histórico.  
- Sortear → novo depósito/entregas/malha + reatribuir.

---

## 6. Testes mínimos

1. Toda viagem começa e termina no depósito.  
2. Carga por viagem ≤ capacidade.  
3. Demanda > capacidade → múltiplos tokens / múltiplas viagens.  
4. Cada entrega atribuída a exatamente um veículo.  
5. Distância usa malha; id bloqueado não aparece no path.  
6. Com `priority_weight > 0`, fitness inclui termo de prioridade.  
7. 1 veículo + capacidade alta o bastante: comportamento “TSP com depósito” (todas as entregas, retornos só no fim se uma viagem).

---

## 7. Critério de pronto

- `python main.py` mostra depósito, N veículos coloridos, retornos e capacidade respeitada.  
- GA por veículo + malha + prioridade funcionando.  
- Requisitos do enunciado cobertos nesta camada: multi-veículo + capacidade (+ prioridade e mapa já da Camada 1).  
- Autonomia **não** incluída.  
- Sem commit até pedido do usuário.

---

## 8. Fora de escopo / Camada 3

- Autonomia / distância máxima / postos de combustível.  
- Realocação genética de entregas entre veículos.  
- Frota heterogênea (capacidades diferentes por veículo) — YAGNI no MVP.  
- Reescrita completa de README/GUIA (follow-up).
