# Design: Combustível e Postos no Simulador de Entregas

**Data:** 2026-07-09  
**Status:** Aprovado em brainstorming  
**Base:** `feat/greedy-delivery-simulation` (simulador guloso + rede de ruas + AG por veículo)  
**Origem:** `ideia.md`  
**Nota:** o spec `2026-07-01-fuel-stations-design.md` era para o TSP clássico; este documento substitui essa intenção no fluxo atual de entregas. Commits ficam fora desta sessão de design (pedido explícito do usuário).

---

## 1. Objetivo

Adicionar autonomia de combustível ao simulador de entregas:

- Cada veículo parte com tanque limitado (máximo **150**).
- Consumo **1:1** com a distância percorrida na **rede de ruas**.
- **Postos separados** (não são pontos de entrega) permitem reabastecimento opcional; visitar um posto **enche o tanque até 150**.
- Se o combustível acabar antes de chegar ao destino, a rota é **inválida** e recebe **penalidade forte** no fitness.
- Postos devem **fazer sentido na rota**: gerados perto da rede (≤ **100 px** de nós relevantes), não em posições arbitrárias no mapa vazio.
- Entregas e postos: **no máximo uma visita** a cada ponto (postos) / regras atuais de não repetir entregas.

O AG continua otimizando apenas a **ordem das entregas**; desvios a postos são decididos por **heurística na simulação**.

---

## 2. Decisões de produto (brainstorming)

| Tópico | Decisão |
|--------|---------|
| Onde integrar | Simulador de entregas atual (veículos + rede + AG por veículo) |
| Tanque seco | Rota inválida + penalidade forte no fitness |
| Tipo de posto | Nós separados (`F1`, `F2`, …), não entregas nem trânsito |
| Abastecimento | Enche até o máximo (150) |
| Posição dos postos | Perto da rede / caminhos possíveis (≤100 px de nó relevante) |
| Quem decide desvio | Heurística na simulação |
| Não repetir | Entregas como hoje; cada posto no máx. 1 visita por veículo |
| Abordagem | Camada de combustível na simulação (postos fora do cromossomo) |
| Commits | Fora de escopo desta sessão |

---

## 3. Abordagens consideradas

### 3.1 Camada de combustível na simulação (escolhida)

Postos entram na rede; `simulate_route_fuel` avalia consumo e desvios; AG só vê distância ou inválida.

- **Prós:** encaixa em `delivery_simulation/`; AG intacto; testável; alinhado às decisões.
- **Contras:** heurística de desvio pode não ser ótima globalmente.

### 3.2 Postos no cromossomo do AG

AG decide quais postos visitar e em que ordem.

- **Prós:** mais controle evolutivo.
- **Contras:** operadores complexos; contradiz a escolha de heurística; muitas rotas inválidas.

### 3.3 Só guloso / visual, sem fitness de combustível

Combustível só na execução visual; AG ignora autonomia.

- **Prós:** implementação mínima.
- **Contras:** AG favorece rotas que secam; pouco didático.

---

## 4. Arquitetura

### 4.1 Novos módulos

| Arquivo | Responsabilidade |
|---------|------------------|
| `delivery_simulation/fuel/models.py` | `GasStation`, `FuelLeg`, `FuelStopEvent`, `RouteFuelReport` |
| `delivery_simulation/fuel/placement.py` | Geração de postos perto da rede |
| `delivery_simulation/fuel/simulation.py` | `simulate_route_fuel` + invalidação |

### 4.2 Integração com o existente

- Postos viram nós `F*` em `RoadNetwork.nodes` e entram no grafo por raio (`build_radius_graph` / `build_road_network`).
- O avaliador de permutação passa a ter dois passos encadeados:
  1. Determinar a **sequência de destinos de entrega** (e retornos ao depot) como hoje — capacidade, trips, bloqueio de nós visitados.
  2. Para cada segmento `atual → próximo destino`, `simulate_route_fuel` decide se vai direto ou **insere desvio** a um posto `F*`, recalculando paths na rede. A distância e a rota expandidas do fitness vêm do `RouteFuelReport`, não da distância “seca” sem postos.
- Fitness efetivo por veículo: `report.total_distance` se `is_feasible`; caso contrário `float("inf")` (mesmo padrão de permutações inválidas no avaliador).
- Cromossomo do AG: **inalterado** (`TaskPermutation`).
- UI Pygame: slider de postos, desenho, métricas, log curto.

### 4.3 Constantes

```python
MAX_FUEL = 150
MAX_STATION_DISTANCE_FROM_NETWORK = 100.0  # px até nó relevante
FUEL_STATION_ID_PREFIX = "F"
```

Consumo: `fuel_consumed = path_distance(network, path_segment)`.

---

## 5. Modelo de dados

```python
@dataclass(frozen=True)
class GasStation:
    id: str                 # "F1", "F2", ...
    coordinate: Coordinate

@dataclass
class FuelLeg:
    leg_index: int
    from_node_id: str
    to_node_id: str
    distance: float
    fuel_before: float
    fuel_consumed: float
    fuel_after: float

@dataclass
class FuelStopEvent:
    station_id: str
    fuel_on_arrival: float
    fuel_on_departure: float  # sempre MAX_FUEL após abastecer

@dataclass
class RouteFuelReport:
    legs: List[FuelLeg]
    stops: List[FuelStopEvent]
    final_fuel: float
    is_feasible: bool
    expanded_node_ids: List[str]  # ordem percorrida (entregas + F* + trânsito se aplicável)
    total_distance: float
```

`SimulationResult` (ou estado da UI) passa a expor `gas_stations` e, por veículo / melhor indivíduo, um `RouteFuelReport` opcional.

---

## 6. Geração de postos

`place_gas_stations(count, network_nodes, map_bounds, rng) -> List[GasStation]`:

1. Para cada posto, sortear um **nó âncora** entre depot, entregas e trânsito.
2. Sortear coordenada a distância uniforme `[0, 100]` px do âncora (ou ponto ao longo de aresta incidente), dentro do mapa.
3. Rejeitar se: colide com depot/entrega/posto existente (separação mínima, ex. 30 px); ou, após inserir no grafo, o nó `F*` fica isolado (grau 0).
4. Até `max_attempts` por posto; se falhar, reduzir quantidade efetiva ou relançar (mesmo padrão de `generate_transit_nodes`).
5. Regenerar em **Sortear posições** e ao mudar o slider de quantidade de postos.

Slider UI: **Postos** 0–6, default 3.

---

## 7. Algoritmo de simulação de combustível

```text
fuel ← MAX_FUEL
visited_stations ← ∅
para cada segmento planejado (atual → destino_entrega_ou_depot):
  se fuel >= dist(atual, destino) via path:
    consumir; registrar FuelLeg; atual ← destino
  senão:
    candidatos ← postos F* ∉ visited_stations com path(atual→F) e path(F→destino)
    filtrar: fuel >= dist(atual→F)
    se vazio → is_feasible = False; return
    escolher F que minimiza dist(atual→F) + dist(F→destino)
    ir a F; registrar leg; abastecer até MAX_FUEL; visited_stations += F
    ir a destino; registrar leg; atual ← destino
```

**Regras:**

- Pathfinding usa a rede (BFS + `path_distance`), respeitando bloqueios de nós já visitados na viagem quando o avaliador atual já os aplica; postos visitados entram no conjunto bloqueado para não repetir.
- Posto não entrega itens e não altera `MAX_CAPACITY`.
- Nós `T*` não reabastecem.
- Retorno ao depot no fim da viagem também consome combustível e pode exigir desvio a posto.

**Fitness:**

```text
se not report.is_feasible: custo = +∞
senão: custo = report.total_distance   # já inclui desvios
```

Prioridade/capacidade/atribuição gulosa permanecem como hoje.

---

## 8. Fluxo de dados

```text
Sortear posições
  → gera depot, entregas, trânsito, rede
  → place_gas_stations → nós F* na rede

Simular / avaliar AG
  → atribuição gulosa (inalterada)
  → sequência de destinos (capacidade / trips)
  → simulate_route_fuel por segmento (insere F* se preciso)
  → fitness = total_distance ou ∞

UI (cada frame / melhor indivíduo)
  → desenha F*, rota expandida, métricas, log
```

---

## 9. UI e visualização

| Elemento | Comportamento |
|----------|----------------|
| Slider Postos | 0–6, default 3; regenera postos |
| Mapa | Ícone/cor distinta para `F*`; rota passa por postos visitados |
| Métricas | Combustível final por veículo; indicador “inválida” se seco |
| Log | Trechos com antes/gasto/depois; linhas de posto `chegou → 150` |
| AG | Sem novos controles; mutação/população inalterados |

---

## 10. Casos limite

| Caso | Tratamento |
|------|------------|
| 0 postos | Só consumo; se algum trecho > autonomia restante → inválida |
| Tanque 150 e mapa pequeno | Postos raramente usados; desvios quase nunca disparam |
| Posto isolado no grafo | Rejeitado na geração |
| Dois veículos | Cada um tem `visited_stations` próprio; postos são compartilháveis entre veículos |
| Mesmo posto duas vezes no mesmo veículo | Proibido (máx. 1 visita) |
| Path bloqueado por nós já visitados | Se não houver path viável com combustível → inválida |

---

## 11. Verificação

**Testes unitários** (`tests/test_fuel_simulation.py`, `tests/test_fuel_placement.py`):

- Consumo 1:1 e enchimento até 150.
- Desvio escolhe posto de menor custo total quando o trecho direto é impossível.
- Sem posto viável → `is_feasible=False`.
- Posto não é revisitado pelo mesmo veículo.
- Placement: distância ao âncora ≤ 100; sem colisão; nó conectado.

**Manual:**

1. 0 postos + trechos longos → rotas inválidas / fitness ∞.
2. 3 postos bem colocados → melhor rota desvia e completa.
3. Log mostra consumo e eventos de posto.
4. Sortear / slider postos regenera mapa e rede.

---

## 12. Escopo fora deste design

- Quantidade variável de litros no cromossomo (design 2026-07-01).
- Postos intercalados no cromossomo do AG.
- Consumo variável por terreno.
- Preço / penalidade por litro abastecido (aqui abastecer só custa o desvio em distância).
- Animação frame a frame do nível do tanque (barra opcional futura).
- Revisitar o mesmo posto no mesmo veículo.

---

## 13. Relação com specs anteriores

| Spec | Relação |
|------|---------|
| `2026-07-01-fuel-stations-design.md` | Conceito similar; **não implementar** no TSP antigo — este spec é a fonte de verdade no fluxo de entregas |
| `2026-07-08-greedy-delivery-simulation-design.md` | Base do domínio (veículos, rede, capacidade) |
| `2026-07-08-delivery-genetic-optimization-design.md` | AG por veículo; fitness passa a considerar combustível via avaliador |
