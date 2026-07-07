# Design: Cenários fixos e toggle 2-opt

**Data:** 2026-07-06  
**Status:** Aprovado  
**Contexto:** Permitir comparação reproduzível de medidas do algoritmo genético (com/sem 2-opt, diferentes configs) usando layouts de cidades predefinidos selecionáveis na interface.

---

## 1. Objetivo

Adicionar à simulação visual:

1. **Seletor de cenário** com presets de posições fixas (5, 10, 12, 15 cidades) e opção Aleatório.
2. **Toggle 2-opt** na sidebar para ativar/desativar o refinamento local aplicado aos filhos após crossover/mutação.

Objetivo principal: comparar o impacto de configurações (especialmente 2-opt) sobre o **mesmo layout de cidades**, garantindo reprodutibilidade experimental.

---

## 2. Decisões de design (validadas)

| Tópico | Decisão |
|--------|---------|
| Seletor de cenário | Grupo de botões selecionáveis (estilo rádio), um por preset |
| Presets disponíveis | Aleatório, Pequeno (5), Médio (10), Grande (12), Extra (15) |
| Fonte dos presets fixos | Expandir/reestruturar `predefined_problems.py` existente |
| Troca de preset | Reset completo: cidades, prioridades, população, histórico, geração → 1 |
| Toggle 2-opt | Aplica na próxima geração; histórico e contador **não** resetam |
| Default 2-opt | Ativo (comportamento atual preservado) |
| Default cenário | Aleatório (comportamento atual preservado) |
| Prioridades ao trocar preset | Sorteio aleatório novo (1–10), como no `initialize()` |
| "Sortear posições" | Se cenário ≠ Aleatório → muda para Aleatório + reset; se já Aleatório → reshuffle como hoje |
| Cenário hospitalar | Fora do escopo desta feature |

---

## 3. Abordagens consideradas

### 3.1 Grupo de botões selecionáveis (escolhida)

Lista vertical na seção "Cenário", um botão por opção, destaque visual no ativo.

- **Prós:** simples, sem widget dropdown novo, todos os cenários visíveis, consistente com `ActionButton`/`ToggleButton`.
- **Contras:** ~140px extras na sidebar (já scrollável).

### 3.2 Dropdown expansível

Campo compacto que abre lista ao clicar.

- **Prós:** economiza espaço vertical.
- **Contras:** widget novo, lógica de fechar ao clicar fora, menos descoberta.

### 3.3 Botões anterior/próximo

Cicla entre cenários com setas.

- **Prós:** mínimo de espaço.
- **Contras:** difícil saltar para preset específico, menos claro para comparação.

---

## 4. Arquitetura

### 4.1 Presets (`genetic_algorithm/predefined_problems.py`)

Reestruturar o dicionário existente para incluir metadados:

```python
SCENARIO_PRESETS: Dict[str, ScenarioPreset] = {
    "random": ScenarioPreset(label="Aleatório", city_count=None, coordinates=None),
    "small_5": ScenarioPreset(label="Pequeno (5)", city_count=5, coordinates=[...]),
    "medium_10": ScenarioPreset(label="Médio (10)", city_count=10, coordinates=[...]),
    "large_12": ScenarioPreset(label="Grande (12)", city_count=12, coordinates=[...]),
    "extra_15": ScenarioPreset(label="Extra (15)", city_count=15, coordinates=[...]),
}
```

Manter compatibilidade exportando `predefined_city_problems` como alias derivado, se necessário para código existente.

### 4.2 Novo widget (`visualization/widgets/scenario_selector.py`)

```python
class ScenarioSelector:
    active_scenario_id: str
    was_changed: bool  # True quando usuário seleciona preset diferente

    def handle_event(event) -> None
    def draw(screen) -> None
```

- Altura por opção: ~28px + gap 4px.
- Botão ativo: borda `VisualTheme.accent`, fundo levemente destacado.
- Botão inativo: estilo card neutro (como `ToggleButton` inativo).

### 4.3 Estado (`SimulationState`)

Novos campos:

```python
active_scenario_id: str = "random"
scenario_selector: ScenarioSelector
two_opt_toggle: ToggleButton  # label="Refinamento 2-opt", is_active=True
section_scenario_y: int
effective_number_of_cities: int  # derivado do preset ativo ou settings
```

Novos métodos:

```python
def apply_scenario(scenario_id: str) -> None:
    """Carrega coords, regenera população, zera histórico e contador."""

def load_cities_for_scenario(scenario_id: str) -> List[CityCoordinate]:
    """Retorna coords fixas ou sorteia se Aleatório."""
```

### 4.4 Algoritmo (`genetic_algorithm/selection.py`)

```python
def evolve_next_generation(
    ...,
    use_2opt: bool = True,
) -> List[Route]:
    ...
    if use_2opt:
        child_route = add_2opt(child_route)
```

### 4.5 Integração no loop (`simulation_state.py` → `pygame_application.py`)

```
run_one_generation():
    ...
    self.population = evolve_next_generation(
        ...,
        use_2opt=self.two_opt_toggle.is_active,
    )
```

---

## 5. Interface (layout da sidebar)

```
ALGORITMO
├── Taxa de mutação          (slider)
├── Peso da prioridade       (slider)
└── Refinamento 2-opt        (ToggleButton, default Ativo)

CENÁRIO                      ← nova seção
├── Aleatório                (default, selecionado)
├── Pequeno (5)
├── Médio (10)
├── Grande (12)
└── Extra (15)

TERRENO NO MAPA
├── ...                      (inalterado)

AÇÕES
├── Sortear posições         (comportamento estendido, ver §6)
└── ...                      (demais botões inalterados)
```

Recalcular posições Y de todas as seções abaixo de "Cenário" em `_create_control_widgets()`.

Opcional (nice-to-have): exibir cenário ativo e estado 2-opt no cabeçalho do mapa (`draw_map_header`).

---

## 6. Comportamento detalhado

### 6.1 Troca de preset

Disparada ao clicar em botão diferente no `ScenarioSelector`:

1. Atualiza `active_scenario_id`.
2. Carrega `city_coordinates` (fixas do preset ou sorteadas se Aleatório).
3. Atualiza contagem efetiva de cidades.
4. Sorteia novas `city_priorities` (1–10).
5. Regenera `population` via `generate_random_population`.
6. Limpa `best_fitness_history` e `best_route_history`.
7. Reinicia `generation_counter` (`itertools.count(start=1)`).

### 6.2 Toggle 2-opt

- Clique no `ToggleButton` inverte `is_active`.
- Próxima chamada a `evolve_next_generation` respeita o flag.
- Histórico de convergência e número de geração **permanecem**.

### 6.3 "Sortear posições"

| Cenário ativo | Ação |
|---------------|------|
| Aleatório | Reshuffle de terreno + cidades + população (comportamento atual) |
| Preset fixo | Muda para Aleatório, executa reset completo, depois reshuffle |

### 6.4 Redimensionamento de janela

Ao receber `VIDEORESIZE`, recriar widgets preservando `active_scenario_id` e estado do `two_opt_toggle`.

---

## 7. Casos de borda

| Caso | Comportamento |
|------|---------------|
| Clicar no preset já ativo | Nenhuma ação |
| Preset fixo + obstáculos habilitados | Coordenadas dos presets já cabem no mapa; sem validação extra de colisão |
| 2-opt desligado + preset fixo | Válido; compara convergência com/sem refinamento no mesmo layout |
| Preset com N ≠ population_size | População regenerada com N cidades; `population_size` inalterado |

---

## 8. Testes

### 8.1 Manuais (UI)

1. Selecionar cada preset → mapa exibe N cidades corretas, gráfico zera, geração reinicia em 1.
2. Alternar 2-opt mid-run → gráfico continua, melhoria de fitness muda visivelmente.
3. Preset fixo + desligar 2-opt vs ligar 2-opt → comparar curvas no mesmo layout.
4. "Sortear posições" em preset fixo → volta para Aleatório.
5. Redimensionar janela → cenário e 2-opt preservados.

### 8.2 Unitários (opcional, baixa prioridade)

- `apply_scenario("small_5")` retorna exatamente 5 coordenadas do preset.
- `evolve_next_generation(..., use_2opt=False)` não chama `add_2opt` (mock).

---

## 9. Arquivos impactados

| Arquivo | Mudança |
|---------|---------|
| `genetic_algorithm/predefined_problems.py` | Reestruturar presets com metadados |
| `genetic_algorithm/selection.py` | Parâmetro `use_2opt` |
| `visualization/widgets/scenario_selector.py` | **Novo** widget |
| `visualization/widgets/__init__.py` | Exportar `ScenarioSelector`, `ToggleButton` |
| `simulation/simulation_state.py` | Estado, widgets, `apply_scenario`, wiring |
| `simulation/pygame_application.py` | Desenhar nova seção |
| `visualization/application_layout.py` | (Opcional) stats no header |

---

## 10. Fora de escopo

- Integração ATT48 (48 cidades reais).
- Cenário hospitalar como preset de posições.
- Export/import de layouts customizados.
- Reset automático ao togglear 2-opt.
