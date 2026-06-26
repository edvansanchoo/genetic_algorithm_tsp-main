# Design: Setas de Direção na Rota

**Data:** 2026-06-25  
**Status:** Aprovado  
**Contexto:** Visualizar no mapa a ordem de visita da melhor rota, complementando a lista textual da sidebar.

---

## 1. Objetivo

Permitir que o usuário veja **a direção da melhor rota** no mapa por meio de setas nos trechos, controlada por toggle na sidebar.

---

## 2. Decisões de design (validadas)

| Tópico | Decisão |
|--------|---------|
| Estilo | Setas triangulares no meio de cada segmento |
| Rota | Apenas a melhor rota |
| Controle | Toggle na sidebar (`ToggleButton`) |
| Default | Desligado |
| Ordem | Rotação a partir de `city_coordinates[0]` (mesma lógica da ordem de entregas) |
| Ciclo | Inclui trecho de volta ao ponto inicial |

---

## 3. Abordagens consideradas

### 3.1 Setas triangulares no ponto médio (escolhida)

Triângulo orientado pela tangente do segmento, posicionado a ~65% do trecho.

- **Prós:** simples, legível, baixo custo.
- **Contras:** segmentos curtos podem ficar apertados (omitir nesses casos).

### 3.2 Números nos nós

- **Prós:** posição explícita por cidade.
- **Contras:** poluição visual com 15 cidades; rejeitado pelo usuário.

### 3.3 Animação de veículo

- **Prós:** didático.
- **Contras:** escopo maior; rejeitado.

---

## 4. Arquitetura

### 4.1 Rota rotacionada

Reutilizar a mesma lógica de `build_delivery_visit_order`:

1. Localizar `city_coordinates[0]` na rota.
2. Rotacionar a lista de coordenadas a partir desse ponto.
3. Desenhar setas entre pares consecutivos, incluindo último → primeiro.

**Refatoração opcional:** extrair `get_rotated_route(route, city_coordinates) -> Route` em `fitness.py` para DRY com `build_delivery_visit_order`.

### 4.2 Desenho das setas (`map_renderer.py`)

```python
def draw_route_direction_arrows(
    screen: pygame.Surface,
    route: Route,
    city_coordinates: List[CityCoordinate],
    fill_color: Tuple[int, int, int] = (255, 255, 255),
    outline_color: Tuple[int, int, int] = VisualTheme.route_best,
    arrow_size: int = 8,
    min_segment_length: float = 20.0,
) -> None
```

**Por segmento:**
1. Calcular comprimento; omitir se `< min_segment_length`.
2. Posicionar seta a 65% do trecho (origem → destino).
3. Calcular ângulo `atan2(dy, dx)`.
4. Desenhar triângulo isósceles apontando para o destino.
5. Contorno 1px na cor da rota.

### 4.3 Toggle na sidebar

| Propriedade | Valor |
|-------------|-------|
| Widget | `ToggleButton` |
| Seção | *Algoritmo*, abaixo de "Peso da prioridade" |
| Label | `"Mostrar direção da rota"` |
| Default | `is_active=False` |
| Estado | `SimulationState.route_direction_toggle` |

**Propriedade:**
```python
@property
def show_route_direction(self) -> bool:
    return self.route_direction_toggle.is_active
```

**Layout:** recalcular `section_quantity_y` e offsets subsequentes em `_create_control_widgets`.

### 4.4 Integração (`pygame_application.py`)

Após `draw_route_paths` da melhor rota:

```python
if simulation.show_route_direction:
    draw_route_direction_arrows(
        screen,
        best_route,
        simulation.city_coordinates,
    )
```

Toggle desenhado no conteúdo scrollável; evento em `handle_control_events`.

### 4.5 Legenda do mapa

Quando toggle ativo, adicionar item `"→ Direção da rota"`.  
Parâmetro opcional `show_route_direction: bool` em `draw_map_legend`.

---

## 5. Arquivos modificados

| Arquivo | Mudança |
|---------|---------|
| `genetic_algorithm/fitness.py` | *(opcional)* `get_rotated_route()` |
| `visualization/map_renderer.py` | `draw_route_direction_arrows()` |
| `simulation/simulation_state.py` | toggle, layout, eventos |
| `simulation/pygame_application.py` | desenho condicional + toggle no scroll |
| `visualization/application_layout.py` | legenda condicional |

---

## 6. Casos limite

| Caso | Tratamento |
|------|------------|
| Toggle desligado | sem setas |
| 1 cidade | sem setas |
| Segmento < 20px | omitir seta |
| Segunda melhor rota | sem setas |
| Rota muda a cada geração | setas seguem `best_route` |

---

## 7. Verificação manual

1. Toggle off → mapa inalterado
2. Toggle on → setas na melhor rota, sentido coerente com sidebar
3. Último trecho volta à cidade de posição 1
4. Toggle funciona com scroll da sidebar
5. Segmentos curtos sem setas sobrepostas

Sem testes automatizados de UI.

---

## 8. Escopo fora deste design

- Setas na segunda melhor rota
- Números nos nós
- Animação de veículo
- Atalho de teclado (apenas toggle na sidebar)
