# Design: Simulador Guloso de Distribuição de Entregas

**Data:** 2026-07-08  
**Status:** Aprovado (design conversacional)  
**Contexto:** Substituir o fluxo principal Pygame (TSP com algoritmo genético) por um simulador didático de distribuição de entregas com múltiplos veículos, estratégia gulosa e capacidade por viagem.

---

## 1. Objetivo

Implementar um sistema de simulação de entregas inspirado no TSP, porém com lógica simplificada:

- Múltiplos veículos (1–3) partem de uma única distribuidora e retornam a ela ao final de cada viagem.
- Pontos de entrega (1–3) com demanda em itens distribuída aleatoriamente.
- Capacidade máxima de 10 itens por viagem; entrega parcial permitida quando um ponto excede a capacidade.
- Atribuição natural entre veículos: a cada passo, o par (veículo, ponto) com menor distância euclidiana é escolhido.
- Roteamento guloso: sempre o ponto pendente mais próximo da posição atual do veículo candidato.
- Interface Pygame no lugar do simulador GA atual, reutilizando layout e widgets existentes.

O objetivo é didático — não buscar solução ótima global — com arquitetura modular que permita substituir a estratégia gulosa por TSP ou VRP no futuro.

---

## 2. Decisões de design (validadas)

| Tópico | Decisão |
|--------|---------|
| Integração | Substituir fluxo Pygame principal; `main.py` continua como entry point |
| Preservar na UI | Layout Pygame, widgets, scroll da sidebar, geração de coordenadas |
| Remover da UI | GA, gráfico de convergência, obstáculos, prioridade, cenários hospitalares, 2-opt |
| Preservar no repo | Pacote `genetic_algorithm/` (demos), sem uso no fluxo principal |
| Terreno | Removido completamente — mapa limpo |
| Execução | Botão **Simular** → resultado estático no mapa e sidebar |
| Botões | **Sortear posições** (coords + pedidos) · **Simular** (só rotas) |
| Distribuidora | Sorteada junto com pontos a cada "Sortear posições" |
| Capacidade | 10 itens/viagem; entrega parcial permitida (mesmo ponto, múltiplas visitas) |
| Distância | Euclidiana; sem penalidades de terreno |
| Arquitetura | Núcleo `delivery_simulation/` desacoplado + Pygame como camada fina |
| Algoritmo | Guloso global unificado (multi-agente por menor distância) |
| Commits | Fora de escopo desta sessão de design |

---

## 3. Abordagens consideradas

### 3.1 Núcleo desacoplado + Pygame como camada fina (escolhida)

Pacote `delivery_simulation/` com módulos puros; `simulation/` orquestra a UI.

- **Prós:** responsabilidade única, testável sem Pygame, substituição futura de estratégia sem alterar UI.
- **Contras:** mais arquivos novos; adaptação da UI existente.

### 3.2 Tudo dentro de `simulation/`

Lógica embutida em `SimulationState`.

- **Prós:** diff menor no curto prazo.
- **Contras:** acopla regra de negócio à UI; difícil testar e evoluir.

### 3.3 Dois pacotes paralelos

Novo pacote completo; TSP intacto mas inativo.

- **Prós:** zero risco ao código GA.
- **Contras:** duplica layout/widgets; não atende "no local do atual".

### 3.4 Algoritmos de roteamento considerados

| Algoritmo | Descrição | Decisão |
|-----------|-----------|---------|
| **A — Guloso global** | A cada passo, escolhe (veículo, ponto) com menor distância entre todos os candidatos | **Escolhido** |
| B — Duas fases | Atribui pontos a veículos estaticamente, depois roteia | Descartado — atribuição ignora posição após primeiras entregas |
| C — Round-robin | Veículos alternam turnos | Descartado — regra artificial de turnos |

---

## 4. Arquitetura e modelo de dados

### 4.1 Pacote `delivery_simulation/`

```
delivery_simulation/
├── __init__.py
├── models.py           # dataclasses de domínio
├── point_generator.py  # coordenadas da distribuidora e pontos
├── order_generator.py  # distribuição aleatória de itens
├── distance.py         # distância euclidiana
├── routing.py          # algoritmo guloso + capacidade + viagens
├── assignment.py       # facade: config + coords + pedidos → SimulationResult
└── reporter.py         # formatação para sidebar/console
```

### 4.2 Modelos (`models.py`)

```python
Coordinate = Tuple[float, float]
MAX_CAPACITY = 10
VALID_TOTAL_ITEMS = (2, 4, 6, 8, 10, 12, 14)

@dataclass
class DeliveryPoint:
    id: str              # "A", "B", "C"
    coordinate: Coordinate
    total_items: int
    remaining_items: int

@dataclass
class Stop:
    point_id: str        # "DEPOT" ou id do ponto
    items_delivered: int # 0 na distribuidora

@dataclass
class Trip:
    stops: List[Stop]    # sempre inicia e termina em DEPOT
    distance: float

@dataclass
class Vehicle:
    id: int
    current_position: Coordinate
    current_load: int
    trips: List[Trip]
    assigned_points: List[str]

@dataclass
class SimulationConfig:
    vehicle_count: int         # 1–3
    delivery_point_count: int  # 1–3
    total_items: int           # par: 2, 4, …, 14

@dataclass
class SimulationResult:
    config: SimulationConfig
    depot: Coordinate
    delivery_points: List[DeliveryPoint]
    vehicles: List[Vehicle]
    total_system_distance: float
```

### 4.3 Geração de pontos (`point_generator.py`)

- Sorteia coordenada da distribuidora + N pontos dentro dos limites do mapa (`ApplicationSettings.map_minimum_x/y`, `map_maximum_x/y`).
- Garante distância mínima de 30 px entre quaisquer dois pontos (incluindo distribuidora); re-sorteia em caso de colisão (máximo 100 tentativas por ponto).
- IDs dos pontos: `"A"`, `"B"`, `"C"` conforme quantidade configurada.
- Sem dependência de obstáculos.

### 4.4 Geração de pedidos (`order_generator.py`)

Distribui `total_items` aleatoriamente entre N pontos:

1. Inicializa todos os pontos com 0 itens.
2. Para cada um dos `total_items`, escolhe um ponto aleatório e incrementa em 1.
3. Garante soma exata = `total_items`.

Regras permitidas: ponto com zero itens; ponto com todos os itens; qualquer combinação válida.

### 4.5 Distância (`distance.py`)

```python
def euclidean(a: Coordinate, b: Coordinate) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])
```

---

## 5. Algoritmo guloso global

### 5.1 Estado inicial

- Todos os veículos na distribuidora: `current_position = depot`, `current_load = 0`.
- Cada ponto: `remaining_items = total_items`.
- Nenhuma viagem registrada.

### 5.2 Loop principal

Repete enquanto existir ponto com `remaining_items > 0`:

```
candidatos = []

para cada veículo V:
    carga_restante = MAX_CAPACITY - V.current_load

    se carga_restante == 0 ou nenhum ponto pendente cabe em carga_restante:
        # veículo cheio ou sem ponto que caiba — deve retornar à distribuidora
        candidatos += (V, DEPOT, dist(V.pos, depot), 0)
    senão:
        para cada ponto P pendente (remaining_items > 0):
            entrega = min(carga_restante, P.remaining_items)
            candidatos += (V, P, dist(V.pos, P.coord), entrega)

escolher candidato com menor distância
    (desempate: veículo de menor id, depois ponto alfabético)

executar candidato:
    se destino == DEPOT:
        finalizar viagem atual (registrar Trip)
        V.current_position = depot
        V.current_load = 0
        iniciar nova viagem vazia
    senão:
        V move até P
        V.current_load += entrega
        P.remaining_items -= entrega
        registrar Stop(P.id, entrega) na viagem atual
        se viagem acabou de iniciar: adicionar Stop("DEPOT", 0) no início
        adicionar P.id em V.assigned_points (sem duplicata)
```

### 5.3 Finalização

Quando todos os pontos têm `remaining_items == 0`, se algum veículo não estiver na distribuidora, retorna e fecha a viagem aberta.

### 5.4 Exemplo validado (1 veículo, A=6, B=8, C=2)

| Passo | Ação | Carga após |
|-------|------|------------|
| 1 | Depot → A (6) | 6 |
| 2 | A → C (2) | 8 |
| 3 | C → Depot | 0 — fim viagem 1 |
| 4 | Depot → B (8) | 8 |
| 5 | B → Depot | 0 — fim viagem 2 |

Resultado: **2 viagens**, distância por trecho euclidiano.

### 5.5 Entrega parcial

Ponto com demanda > 10 (ex.: 14 itens em um único ponto):

- Viagem 1: entrega 10 itens, retorna à distribuidora.
- Viagem 2: retorna ao mesmo ponto, entrega 4 itens restantes, retorna à distribuidora.

---

## 6. Fluxo de interação

### 6.1 Botão "Sortear posições"

1. Gera coordenada da distribuidora + N pontos (`point_generator`).
2. Redistribui itens entre pontos (`order_generator`).
3. Limpa `simulation_result` (rotas somem do mapa).
4. Mapa exibe distribuidora + pontos com quantidades; sem rotas.

### 6.2 Botão "Simular"

1. Usa coordenadas e pedidos atuais (sem sortear).
2. Reseta `remaining_items` dos pontos para valores originais.
3. Executa `assignment.run_simulation(config, depot, points)`.
4. Armazena `SimulationResult` e atualiza sidebar.

**Pré-condição:** posições já sorteadas. Se não, botão desabilitado ou mensagem "Sorteie posições primeiro".

### 6.3 Sliders

| Controle | Faixa | Default |
|----------|-------|---------|
| Veículos | 1–3 | 1 |
| Pontos de entrega | 1–3 | 2 |
| Total de itens | 2, 4, 6, 8, 10, 12, 14 | 6 |

Alterar qualquer slider limpa o resultado até novo **Simular**. Mudar quantidade de pontos exige novo **Sortear posições** para regenerar coordenadas.

---

## 7. Interface Pygame

### 7.1 Sidebar (topo → scroll)

```
┌─ Resumo ──────────────────────┐
│  Distância total: --- px      │  ← preenchido após Simular
│  Viagens: ---                 │
├───────────────────────────────┤
│  CONFIGURAÇÃO                 │
│  Veículos        [1 ■─── 3]   │
│  Pontos          [1 ■─── 3]   │
│  Total de itens  [2 ■── 14]   │  ← DiscreteSlider (passos pares)
├───────────────────────────────┤
│  AÇÕES                        │
│  [ Sortear posições ]         │
│  [ Simular ]                  │
├───────────────────────────────┤
│  RESULTADO (scrollável)       │
│  config, pontos, rotas...     │
└───────────────────────────────┘
│  Q · Esc sair · F tela cheia  │
└───────────────────────────────┘
```

Gráfico de convergência (Matplotlib) **removido**. Área `plot_height` (400 px) vira painel de resumo.

### 7.2 Mapa

| Elemento | Visual |
|----------|--------|
| Distribuidora | Quadrado 14×14 px, azul escuro, label "D" |
| Pontos | Círculo vermelho + label (A/B/C) + quantidade acima |
| Rotas | Linhas coloridas por veículo; setas direcionais |
| Viagens múltiplas | Mesma cor por veículo; opacidade alternada (100% / 60%) |

Legenda no canto inferior direito: cor → Veículo 1/2/3.

### 7.3 Cores dos veículos

| Veículo | Cor |
|---------|-----|
| 1 | `(37, 99, 235)` — azul |
| 2 | `(234, 88, 12)` — laranja |
| 3 | `(22, 163, 74)` — verde |

### 7.4 Loop principal

Substitui `run_one_generation()` por loop estático:

```python
while running:
    handle_events()
    draw_chrome()
    draw_map_header(metrics)
    draw_depot(...)
    draw_delivery_points(...)
    if simulation_result:
        draw_vehicle_routes(...)
    draw_sidebar_scrollable(...)
    pygame.display.flip()
    clock.tick(30)
```

### 7.5 Controles

| Tecla / Ação | Efeito |
|---|---|
| **Q** / **Esc** | Encerrar |
| **F** | Tela cheia |
| Sliders | Ajustam config; limpam resultado |
| **Sortear posições** | Novas coords + novos pedidos |
| **Simular** | Calcula e exibe rotas |

---

## 8. Saída de resultados (`reporter.py`)

Sidebar e console (opcional) exibem:

- Configuração utilizada (veículos, pontos, itens totais).
- Coordenadas e quantidade de itens de cada ponto.
- Entregas atribuídas a cada veículo (ids dos pontos).
- Quantidade de viagens por veículo.
- Rota completa de cada viagem com itens entregues por parada.
- Distância de cada viagem.
- Distância total por veículo.
- Distância total do sistema.

Exemplo de formato:

```
── Configuração ──
Veículos: 2 | Pontos: 3 | Itens: 14

── Pontos ──
A (320, 180): 6 itens
B (450, 290): 4 itens
C (180, 350): 4 itens

── Veículo 1 (2 viagens, 842 px) ──
  Viagem 1: D → A(6) → C(2) → D  [512 px]
  Viagem 2: D → B(4) → D          [330 px]

── Veículo 2 (1 viagem, 210 px) ──
  Viagem 1: D → B(4) → D          [210 px]

── Total do sistema: 1052 px ──
```

---

## 9. Adaptações no código existente

| Arquivo | Mudança |
|---------|---------|
| `simulation_state.py` | Remove GA, população, obstáculos, prioridade; adiciona estado de entregas |
| `pygame_application.py` | Loop estático; remove convergência e terreno |
| `map_renderer.py` | `draw_depot`, `draw_delivery_points`, `draw_vehicle_routes`; remove terreno |
| `application_layout.py` | Painel de resumo e resultados; remove métricas GA |
| `application_settings.py` | Remove parâmetros GA; defaults do simulador de entregas |
| `city_generator.py` | Substituído/simplificado por `point_generator` |
| `visualization/widgets/` | Novo `DiscreteSlider` para itens totais |

Arquivos **não alterados** (permanecem no repo): `genetic_algorithm/*`, `demos/*`, `obstacles/*`.

---

## 10. Tratamento de erros

| Situação | Comportamento |
|----------|---------------|
| Simular sem posições sorteadas | Botão desabilitado ou mensagem na sidebar |
| `total_items` mínimo = 2 | Garantido pelo slider |
| Ponto com 0 itens | Exibido no mapa; ignorado pelo algoritmo |
| Coordenadas sobrepostas | `point_generator` re-sorteia (máx. 100 tentativas) |
| Loop sem candidatos | `RuntimeError` — não deve ocorrer com entrega parcial |

---

## 11. Testes

Testes unitários em `tests/` (sem Pygame):

| Arquivo | Casos |
|---------|-------|
| `test_order_generator.py` | Soma exata; valores ≥ 0; zeros permitidos; seed fixa reproduzível |
| `test_distance.py` | Distância euclidiana conhecida |
| `test_routing.py` | Exemplo A=6/B=8/C=2 → 2 viagens; entrega parcial (14 itens, 1 ponto); capacidade respeitada; retorno à distribuidora |
| `test_routing_multi_vehicle.py` | 2 veículos competem pela entrega mais próxima; capacidade respeitada |
| `test_point_generator.py` | N pontos + depot; distância mínima; coordenadas dentro dos limites |

Testes de integração Pygame: fora de escopo (validação manual).

---

## 12. Fora de escopo

- Algoritmo genético ou TSP ótimo na UI principal.
- Obstáculos, prioridade de entregas, postos de combustível.
- Animação de veículos percorrendo rotas.
- Mapas reais ou rotas rodoviárias.
- Mais de 3 veículos ou 3 pontos (expansão futura).
- Commit do spec nesta sessão (solicitação explícita do usuário).

---

## 13. Extensões futuras

- Substituir `routing.py` por solver TSP ou VRP sem alterar UI.
- Animação passo a passo das viagens.
- Exportar resultado em JSON/CSV.
- Expandir faixas de veículos, pontos e itens.
- Modo comparativo: guloso vs GA side-by-side.
