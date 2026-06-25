# Design: Extensão TSP — Priorização de Entregas

**Data:** 2026-06-25  
**Status:** Aprovado  
**Contexto:** Evolução do TSP com Algoritmo Genético para cenário de distribuição hospitalar (medicamentos e insumos).

---

## 1. Objetivo

Adicionar **prioridade de entregas** ao sistema existente, permitindo que o algoritmo genético equilibre **distância total** e **urgência das entregas**. O usuário deve poder comparar cenários ajustando o peso da prioridade e analisar a qualidade da solução via métricas e visualização.

---

## 2. Decisões de design (validadas)

| Tópico | Decisão |
|--------|---------|
| Modelo de rota | Ciclo simétrico (TSP puro), sem depósito separado |
| Posição no ciclo | Referência fixa: `city_coordinates[0]` = posição 1 |
| Atribuição de prioridade | Aleatório (1–10) + preset hospitalar (botão / tecla P) |
| Penalidade | `Σ(prioridadeᵢ × posiçãoᵢ)` |
| Fitness | `distância + terreno + peso × penalidade_prioridade` |
| Peso configurável | Slider contínuo 0–100, default 0 |
| Visualização | Cor do nó por gradiente (verde → amarelo → vermelho) |
| Abordagem arquitetural | Extensão mínima do fitness (sem refatorar encoding do GA) |

---

## 3. Abordagens consideradas

### 3.1 Extensão mínima do fitness (escolhida)

Adicionar `city_priorities: List[int]` paralela às coordenadas, estender `calculate_route_fitness` e adicionar controles na sidebar.

- **Prós:** diff pequeno, padrão consistente com penalidades de terreno, demo ao vivo simples.
- **Contras:** lista paralela exige alinhamento manual de índices.

### 3.2 Modelo de domínio `DeliveryPoint`

Dataclass com coordenada + prioridade substituindo tuplas `(x, y)`.

- **Prós:** modelo expressivo, menos risco de desalinhamento.
- **Contras:** refatoração ampla (população, crossover, mutação, histórico).

### 3.3 Fitness multi-objetivo (Pareto)

Distância e prioridade como objetivos separados com seleção por dominância.

- **Prós:** academicamente rico para otimização multi-critério.
- **Contras:** muda seleção/elitismo, UI de convergência ambígua, escopo maior.

---

## 4. Arquitetura e modelo de dados

### 4.1 Novo estado (`SimulationState`)

```python
city_priorities: List[int]           # 1–10, alinhado por índice com city_coordinates
priority_weight_slider: MutationSlider  # reutiliza widget existente, faixa 0–100
hospital_preset_button: ActionButton     # reaplica preset sem mover cidades
```

### 4.2 Geração de prioridades

| Evento | Comportamento |
|--------|---------------|
| `initialize()` | Sorteia coordenadas + prioridades aleatórias (1–10) |
| "Sortear posições" | Regenera coordenadas **e** prioridades aleatórias |
| "Cenário hospitalar" / tecla **P** | Mantém coordenadas; reaplica preset hospitalar |
| Sliders de terreno | Não afetam prioridades |

### 4.3 Preset hospitalar (`problem/priority_presets.py`)

Distribuição determinística com `random.Random(42)`:

1. Embaralha índices das cidades.
2. Atribui:
   - **20%** (mínimo 1 cidade) → prioridade 8–10
   - **30%** → prioridade 5–7
   - **Restante** → prioridade 1–4

Valores dentro de cada faixa sorteados com a mesma seed → reprodutível para demonstração.

### 4.4 Cálculo de posição (referência índice 0)

A rota é permutação de coordenadas. Para contar posições:

1. Localizar `city_coordinates[0]` na rota.
2. Rotacionar mentalmente a partir desse ponto.
3. Atribuir posições 1, 2, …, N na ordem resultante.

### 4.5 Fitness estendida

```
fitness = distância_total
        + penalidades_terreno (se ativas)
        + peso_prioridade × Σ(prioridadeᵢ × posiçãoᵢ)
```

Com `peso = 0`, comportamento idêntico ao TSP atual.

### 4.6 Funções em `fitness.py`

```python
def calculate_priority_penalty(
    route: Route,
    city_coordinates: List[CityCoordinate],
    priorities: List[int],
) -> float:
    """Retorna Σ(prioridade × posição). Posição 1 = city_coordinates[0]."""

def calculate_route_fitness(
    route, obstacles, use_obstacle_penalties,
    city_coordinates, priorities, priority_weight,
) -> float:
    """Retorna fitness composto."""

def decompose_route_fitness(
    route, obstacles, use_obstacle_penalties,
    city_coordinates, priorities, priority_weight,
) -> tuple[float, float, float]:
    """Retorna (fitness_total, distância, penalidade_prioridade_ponderada)."""
```

### 4.7 Arquivos modificados

| Arquivo | Mudança |
|---------|---------|
| `genetic_algorithm/fitness.py` | Penalidade de prioridade + fitness composta + decomposição |
| `problem/city_generator.py` | Geração/regeneração de prioridades |
| `problem/priority_presets.py` | **Novo** — lógica do preset hospitalar |
| `simulation/simulation_state.py` | Estado, slider, botão preset, parâmetros ao fitness |
| `simulation/pygame_application.py` | Renderização de novos controles e métricas |
| `visualization/map_renderer.py` | Cor por prioridade |
| `visualization/application_layout.py` | Métricas no cabeçalho, legenda, painel de ordem |
| `config/application_settings.py` | `initial_priority_weight = 0` |
| `config/visual_theme.py` | Cores do gradiente + `priority_to_color()` |

### 4.8 O que não muda

- Encoding genético (permutação de coordenadas)
- Crossover (OX), mutação (swap), seleção, elitismo
- Penalidades de terreno (somam independentemente)
- Tamanho de população e taxa de mutação

---

## 5. UI, métricas e visualização

### 5.1 Sidebar — novos controles

**Slider "Peso da prioridade"** (seção *Algoritmo*, abaixo de mutação):
- Faixa: 0–100 (inteiro exibido)
- Default: 0
- Reutiliza `MutationSlider` com `minimum_value=0`, `maximum_value=100`

**Botão "Cenário hospitalar"** (seção *Ações*, abaixo de "Sortear posições"):
- Reaplica prioridades sem mover cidades/obstáculos
- Atalho: tecla **P**
- Subtítulo: `"Prioridades críticas fixas"`

**Rodapé atualizado:**
```
Q · Sair    O · Penalidades de terreno    P · Cenário hospitalar    Esc · Fechar
```

### 5.2 Cabeçalho do mapa

| Campo | Exemplo | Descrição |
|-------|---------|-----------|
| Geração | `Geração 142` | Inalterado |
| Fitness | `Fitness 2847.3` | Custo total |
| Distância | `Dist 2650.0` | Só euclidiana |
| Penal. prioridade | `Prior 197.3` | `peso × Σ(prioridade × posição)` |
| Mutação | `Mut 1%` | Inalterado |

**Indicador de modo** (substitui label de terreno):
- Peso 0 → `"Só distância"`
- Peso 1–49 → `"Equilibrado"`
- Peso 50–100 → `"Críticas primeiro"`

### 5.3 Painel de ordem de entregas

Lista na sidebar com a melhor rota, ordenada por posição de visita:

```
Ordem de entregas
─────────────────
 1 · Cidade 3  ·  prior. 9  ★
 2 · Cidade 7  ·  prior. 2
 3 · Cidade 1  ·  prior. 8  ★
 ...
```

- **★** marca prioridade ≥ 8
- Atualiza a cada geração

### 5.4 Mapa — cor por prioridade

`priority_to_color(priority: int) -> RGB` em `visual_theme.py`:
- Prioridade 1 → verde `(76, 175, 80)`
- Prioridade 5–6 → amarelo `(255, 193, 7)`
- Prioridade 10 → vermelho `(244, 67, 54)`
- Interpolação linear entre extremos

Legenda adiciona: Baixa (1), Média (5), Alta (10).

### 5.5 Gráfico de convergência

- Eixo Y: `"Fitness (custo total)"` quando peso > 0
- Eixo Y: `"Distância (pixels)"` quando peso = 0

### 5.6 Console

```
Geração 142: fitness=2847.3  dist=2650.0  prior=197.3  peso=50
```

---

## 6. Fluxo de dados

```
run_one_generation()
  → calculate_route_fitness() para cada rota
      → distância euclidiana
      → penalidade terreno (opcional)
      → penalidade prioridade (rotaciona a partir de city_coordinates[0])
      → fitness = dist + terreno + peso × prioridade
  → sort_population_by_fitness()
  → evolve_next_generation()
  → atualiza UI (mapa, métricas, ordem de entregas)
```

---

## 7. Casos limite

| Caso | Tratamento |
|------|------------|
| Peso = 0 | Penalidade ignorada; GA idêntico ao TSP atual |
| Todas prioridades iguais | Penalidade depende só da ordem; GA minimiza distância |
| Prioridade 1 em todas | Penalidade proporcional à posição; efeito reduzido |
| number_of_cities = 1 | Posição 1; sem efeito de reordenação |
| Coordenadas duplicadas | Impossível — população é permutação de coordenadas únicas |

---

## 8. Verificação manual

1. **Peso 0** — fitness = distância; comportamento igual ao TSP original
2. **Peso 100 + preset hospitalar** — entregas ★ nas primeiras posições, distância pode aumentar
3. **Slider ao vivo** — mudança de peso altera fitness sem reiniciar
4. **Sortear posições** — novas prioridades aleatórias; histórico limpo
5. **Tecla P** — prioridades mudam; cidades permanecem
6. **Cores** — gradiente verde → amarelo → vermelho coerente
7. **Métricas** — `fitness ≈ distância + penalidade_prioridade` (± terreno)
8. **Ordem de entregas** — coerente com rotação a partir de índice 0

Sem testes automatizados nesta fase — validação visual e via console, consistente com o projeto.

---

## 9. Escopo explícito fora deste design

- Refatoração para `DeliveryPoint` ou modelo VRP multi-veículo
- Seleção multi-objetivo (Pareto)
- Edição manual de prioridade por clique no mapa
- Persistência/exportação de cenários
