# Design: Extensão TSP — Postos de Combustível e Rastreio de Autonomia

**Data:** 2026-07-01  
**Status:** Aprovado  
**Contexto:** Evolução do TSP com priorização hospitalar. Adiciona veículo com tanque limitado, postos opcionais de reabastecimento e log detalhado de consumo trecho a trecho.

---

## 1. Objetivo

Estender o simulador para modelar **autonomia de combustível** no cenário de entregas prioritárias:

- Veículo percorre cidades com consumo 1:1 em relação à distância euclidiana.
- **Postos de gasolina** gerados proceduralmente permitem reabastecimento opcional; cada desvio aumenta o trajeto.
- O GA codifica **quanto abastecer em cada posto** (`0` = ignorar posto).
- Abastecer mais melhora autonomia, mas aplica **penalidade proporcional aos litros**.
- Secar o tanque aplica **penalidade proporcional** à distância até o posto ativo mais próximo.
- Usuário visualiza **combustível em cada ponto**, **chegada/saída nos postos** e **gasto entre trechos**.

---

## 2. Decisões de design (validadas)

| Tópico | Decisão |
|--------|---------|
| Postos no trajeto | Opcionais — visita só quando simulação exige ou desvio é vantajoso |
| Posição dos postos | Gerados proceduralmente; quantidade via slider (padrão árvores/lagos) |
| Consumo | 1 unidade de combustível por 1 unidade de distância euclidiana |
| Capacidade do tanque | Valor fixo configurável via slider (ex.: 150–400, default 250) |
| Abastecimento | GA define `refuel_amounts[i]` por posto; `0` = não usar |
| Quantidade abastecida | Codificada no cromossomo (gene por posto) |
| Penalidade de abastecimento | `peso_combustível × Σ(litros_abastecidos)` |
| Tanque seco | Penalidade proporcional à distância ao posto ativo mais próximo |
| Prioridade de entrega | Inalterada — só cidades entram em `Σ(prioridade × posição)` |
| Abordagem arquitetural | Rota de cidades + vetor paralelo `refuel_amounts` (extensão mínima) |
| Rastreio | `RouteFuelReport` com legs e eventos de posto; painel scrollável na sidebar |

---

## 3. Abordagens consideradas

### 3.1 Rota de cidades + vetor de abastecimento (escolhida)

Cromossomo = permutação de cidades (inalterada) + `refuel_amounts: List[float]` alinhado aos postos. A simulação de combustível decide **quando** desviar (heurística por autonomia); o GA decide **quanto** abastecer em cada posto.

- **Prós:** crossover/mutação de cidades quase intactos; padrão consistente com `city_priorities`; diff moderado.
- **Contras:** timing de visita aos postos não é gene direto — fica na heurística da simulação.

### 3.2 Super-rota (cidades + postos intercalados)

Sequência única misturando cidades e postos com litros por parada.

- **Prós:** controle total de ordem e quantidade.
- **Contras:** crossover/mutação complexos; cromossomos inválidos frequentes; escopo grande.

### 3.3 Plano de paradas explícito

Rota de cidades + lista ordenada `[(posto_id, litros), …]`.

- **Prós:** separação clara entre entregas e abastecimento.
- **Contras:** sincronização frágil entre plano e rota; crossover difícil.

---

## 4. Arquitetura e modelo de dados

### 4.1 Novos tipos (`fuel/models.py`)

```python
@dataclass(frozen=True)
class GasStation:
    coordinate: Tuple[float, float]
    name: str  # "Posto 1", "Posto 2", ...

@dataclass
class FuelLeg:
    leg_index: int
    from_label: str       # "Cidade 3" ou "Posto 2"
    to_label: str
    distance: float
    fuel_before: float    # ao sair da origem do trecho
    fuel_consumed: float  # = distance (consumo 1:1)
    fuel_after: float     # ao chegar (antes de abastecer, se posto)

@dataclass
class FuelStopEvent:
    station_label: str
    fuel_on_arrival: float
    refuel_amount: float
    fuel_on_departure: float  # min(capacidade, chegada + abastecimento)
    refuel_penalty: float

@dataclass
class RouteFuelReport:
    legs: List[FuelLeg]
    stops: List[FuelStopEvent]
    expanded_route: List[Tuple[float, float]]  # coordenadas na ordem percorrida
    total_distance: float
    total_refuel_penalty: float
    dry_run_penalty: float
    final_fuel: float
```

### 4.2 Cromossomo estendido (`fuel/individual.py`)

```python
@dataclass
class RouteIndividual:
    route: Route                          # permutação de CityCoordinate
    refuel_amounts: List[float]           # um valor por posto; 0 = ignorar
```

A população passa de `List[Route]` para `List[RouteIndividual]`. Crossover/mutação de rota permanecem iguais; genes de abastecimento têm operadores próprios.

### 4.3 Novo estado (`SimulationState`)

```python
gas_stations: List[GasStation]
gas_station_count_slider: IntegerSlider
fuel_tank_capacity_slider: IntegerSlider      # faixa 150–400, default 250
fuel_penalty_weight_slider: MutationSlider    # faixa 0–100, default 10
```

Postos regeneram quando:
- `initialize()`
- "Sortear posições" (junto com cidades)
- Slider de quantidade de postos muda

### 4.4 Geração de postos (`fuel/placement.py`)

Segue padrão de `obstacles/placement.py`:

- Posição aleatória dentro do mapa, sem sobrepor cidades nem postos existentes.
- Raio visual pequeno (ícone ⛽, ~12 px).
- Tentativas máximas por posto: 200 (padrão terreno).
- Renumerar: `"Posto 1"`, `"Posto 2"`, …

### 4.5 Simulação de combustível (`fuel/simulation.py`)

```python
def simulate_route_fuel(
    route: Route,
    refuel_amounts: List[float],
    gas_stations: List[GasStation],
    tank_capacity: float,
    fuel_penalty_weight: float,
    city_coordinates: List[CityCoordinate],
) -> RouteFuelReport:
    """
    Percorre rota de cidades (referência city_coordinates[0]), insere desvios
    opcionais a postos ativos e produz log trecho a trecho.
    """
```

**Algoritmo de desvio (heurística):**

1. Tanque inicia cheio (`tank_capacity`) em `city_coordinates[0]`.
2. Para cada cidade-alvo na rota rotacionada (excluindo repetição do ponto inicial até fechar ciclo):
   - Calcule distância direta até a cidade.
   - Se `combustível_atual >= distância`: vá direto; registre `FuelLeg`.
   - Senão, entre postos com `refuel_amounts[i] > 0`, escolha o de **menor distância total** (posição atual → posto → cidade-alvo).
   - Desvie ao posto; registre leg + `FuelStopEvent` (chegada, abastecimento, saída).
   - Se nenhum posto viável: percorra até secar; aplique `dry_run_penalty = fuel_penalty_weight × distância_ao_posto_ativo_mais_próximo`; registre leg parcial.
3. Ao fechar ciclo (última cidade → `city_coordinates[0]`), mesma lógica.
4. `expanded_route` acumula todas as coordenadas visitadas na ordem (cidades + postos).

**Regras de abastecimento:**

- `refuel_amount` vem do gene; clamp em `[0, tank_capacity - fuel_on_arrival]`.
- `fuel_on_departure = min(tank_capacity, fuel_on_arrival + refuel_amount)`.
- `refuel_penalty = fuel_penalty_weight × refuel_amount`.

**Prioridade:** cálculo de posição usa apenas cidades da rota base (sem postos).

### 4.6 Fitness estendida (`fitness.py`)

```
fitness = distância_expandida                    # inclui desvios a postos
        + penalidades_terreno (segmentos expandidos)
        + peso_prioridade × Σ(prioridade × posição)
        + peso_combustível × Σ(litros_abastecidos)
        + penalidade_secagem
```

```python
def calculate_route_fitness(
    individual: RouteIndividual,
    obstacles, use_obstacle_penalties,
    city_coordinates, priorities, priority_weight,
    gas_stations, tank_capacity, fuel_penalty_weight,
) -> float:

def decompose_route_fitness(...) -> tuple[
    float,  # fitness_total
    float,  # distância_expandida
    float,  # penalidade_prioridade_ponderada
    float,  # penalidade_abastecimento
    float,  # penalidade_secagem
]:
```

Com `fuel_penalty_weight = 0` e postos ausentes (slider = 0), comportamento idêntico ao TSP com prioridade atual.

### 4.7 Operadores genéticos (`fuel/genetics.py`)

| Operador | Comportamento |
|----------|---------------|
| **Inicialização** | Rota aleatória + `refuel_amounts` sorteados em `[0, tank_capacity]` (50% chance de 0 por posto) |
| **Crossover rota** | OX existente (inalterado) |
| **Crossover abastecimento** | Por posto: herda valor do pai A ou pai B (50/50) |
| **Mutação rota** | Swap existente (inalterado) |
| **Mutação abastecimento** | Com prob. `mutation_rate`: sorteia posto e ajusta ±`delta` (ex.: 20), clamp `[0, tank_capacity]` |

Elitismo preserva `RouteIndividual` completo (rota + abastecimentos).

### 4.8 Arquivos

| Arquivo | Mudança |
|---------|---------|
| `fuel/models.py` | **Novo** — tipos de domínio |
| `fuel/placement.py` | **Novo** — geração procedural de postos |
| `fuel/simulation.py` | **Novo** — simulação + `RouteFuelReport` |
| `fuel/individual.py` | **Novo** — `RouteIndividual` |
| `fuel/genetics.py` | **Novo** — init/crossover/mutação de abastecimento |
| `genetic_algorithm/fitness.py` | Integrar simulação de combustível |
| `genetic_algorithm/population.py` | População de `RouteIndividual` |
| `genetic_algorithm/selection.py` | Aceitar `RouteIndividual` |
| `simulation/simulation_state.py` | Estado, sliders, postos, relatório |
| `simulation/pygame_application.py` | Renderização postos, log, métricas |
| `visualization/map_renderer.py` | Desenhar postos e rota expandida |
| `visualization/application_layout.py` | Painel log combustível, legenda, métricas |
| `config/application_settings.py` | Defaults de postos, tanque, peso combustível |
| `config/visual_theme.py` | Cor/ícone de posto |
| `tests/test_fuel_simulation.py` | **Novo** — simulação, penalidades, log |

---

## 5. UI, métricas e visualização

### 5.1 Sidebar — novos controles (seção *Quantidade*)

| Controle | Faixa | Default |
|----------|-------|---------|
| Slider "Postos" | 0–8 | 3 |
| Slider "Tanque" | 150–400 | 250 |
| Slider "Peso combustível" | 0–100 | 10 |

Reutiliza `IntegerSlider` (postos, tanque) e `MutationSlider` (peso).

### 5.2 Cabeçalho do mapa — métricas adicionais

| Campo | Exemplo |
|-------|---------|
| Combustível | `Comb 161/250` |
| Penal. abastecimento | `Abast 1200` |
| Penal. secagem | `Sec 0` |

Indicador de modo combustível:
- Peso 0 → `"Sem custo de abastecimento"`
- Peso 1–49 → `"Abastecimento moderado"`
- Peso 50–100 → `"Abastecimento caro"`

### 5.3 Painel "LOG DE COMBUSTÍVEL"

Abaixo de "Ordem de entregas", painel scrollável (mesmo padrão de sidebar scroll):

```
LOG DE COMBUSTÍVEL
──────────────────
T01 · Cidade 1 → Cidade 4
     dist 142 · gasto 142 · antes 250 · depois 108

T02 · Cidade 4 → Posto 2  ⛽
     dist  67 · gasto  67 · antes 108 · depois  41
     posto: chegou 41 · abasteceu +120 · saiu 161

T03 · Posto 2 → Cidade 7
     dist  95 · gasto  95 · antes 161 · depois  66
...
```

Função: `draw_fuel_log_panel(screen, report: RouteFuelReport, ...)`.

### 5.4 Mapa

- Postos desenhados como ⛽ com cor dedicada (`VisualTheme.gas_station`).
- Melhor rota usa `expanded_route` (linha passa por postos visitados).
- Label opcional nos postos visitados: `"41→161"` (chegada→saída).
- Barra de combustível no canto inferior do mapa (% tanque da posição atual na animação).

### 5.5 Legenda

Adicionar: `(cor_posto, "Posto de combustível")`.

### 5.6 Console

```
Geração 142: fitness=3120.5  dist=2780  prior=197  abast=1200  sec=0  tanque=250
```

---

## 6. Fluxo de dados

```
run_one_generation()
  → para cada RouteIndividual:
      simulate_route_fuel() → RouteFuelReport
      calculate_route_fitness() usando distância_expandida + penalidades
  → sort_population_by_fitness()
  → evolve_next_generation()  # crossover/mutação rota + abastecimento
  → atualiza UI (mapa expandido, log combustível, métricas)
```

Relatório de combustível calculado para **melhor indivíduo** a cada frame (ou a cada geração — preferir cada frame para slider ao vivo, cacheando se performance degradar).

---

## 7. Casos limite

| Caso | Tratamento |
|------|------------|
| 0 postos | Simulação só consome; secagem penaliza `peso × distância_restante_ate_destino × 2` |
| Todos `refuel_amounts = 0` | Sem desvios; se tanque insuficiente para ciclo, acumula penalidade de secagem |
| Tanque muito grande | Rota nunca precisa de postos; genes de abastecimento irrelevantes |
| Peso combustível = 0 | Abastecimento não penaliza fitness; desvios só por distância |
| Posto coincidente com cidade | Evitar na geração (colisão) |
| `refuel_amount` > espaço no tanque | Clamp para encher até capacidade |
| Prioridade + combustível | Prioridade calculada só sobre cidades; postos não alteram posição de entrega |

**Caso 0 postos — decisão explícita:** se combustível acabar e não houver postos, `dry_run_penalty = fuel_penalty_weight × distância_restante_ate_destino × 2` (penalidade proporcional ao trecho não percorrido).

---

## 8. Verificação manual

1. **0 postos, tanque pequeno** — penalidade de secagem visível; log mostra trecho interrompido.
2. **3 postos, tanque médio** — melhor rota desvia a postos; distância expandida > distância base.
3. **Log de combustível** — cada trecho mostra antes/gasto/depois; postos mostram chegada/abastecimento/saída.
4. **Peso combustível alto** — GA prefere abastecer menos (genes menores).
5. **Slider postos ao vivo** — postos aparecem/somem; população regenere `refuel_amounts` com tamanho correto.
6. **Prioridade ativa** — ordem de entregas ignora postos; cidades críticas continuam primeiro.
7. **Sortear posições** — postos e genes reinicializados.
8. **Métricas** — `fitness ≈ dist_expandida + prior + abast + sec` (± terreno).

Testes unitários em `tests/test_fuel_simulation.py` para simulação, clamp, penalidades e estrutura do log.

---

## 9. Escopo explícito fora deste design

- Super-rota com postos no cromossomo de visita
- Multi-veículo / VRP
- Consumo variável por terreno
- Preço diferenciado por posto
- Animação passo a passo do veículo consumindo combustível
- Persistência de cenários
