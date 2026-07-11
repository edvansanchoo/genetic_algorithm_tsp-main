# Design: Sprite de caminhão na animação de rota

**Data:** 2026-07-11  
**Status:** Aprovado (brainstorming) — aguardando review do arquivo  
**Branch:** `feature/road-network-blocked-nodes`

**Contexto:** Com filtro de veículo focado (`V1`, `V2`, …), uma bolinha colorida percorre a rota em loop (`draw_animation_cursor`). O usuário quer um caminhão ilustrativo no lugar da bolinha.

---

## 1. Objetivo

Substituir o cursor circular da animação de rota por um **sprite de caminhão** quando um veículo está em foco, mantendo o mesmo comportamento de percurso (polyline, velocidade, reset ao trocar foco).

**Fora de escopo:** animação em modo “Todos”; caminhão diferente por veículo (forma); múltiplos caminhões simultâneos; animação na 2ª melhor rota; sprites para depósito ou entregas.

---

## 2. Decisões validadas

| Tópico | Decisão |
|--------|---------|
| Asset | PNG flat gerado no Cursor, commitado no repositório |
| Caminho | `traveling_salesman_problem/assets/truck.png` |
| Formato do PNG | Silhueta clara (branco/cinza) em fundo transparente, vista lateral apontando para a **direita** (0° = leste) |
| Resolução fonte | ~32×32 px; exibição escalada para **16×16** px |
| Cor | Tint completo na cor da rota do veículo (`VisualTheme.vehicle_route_colors`) |
| Orientação | Rotação livre conforme direção do segmento atual da polyline |
| Gatilho | Mesmo de hoje: `focus_vehicle_id is not None` e plano desenhável |
| Velocidade | Mantém `ANIMATION_SPEED = 0.12` (fração do percurso por segundo) |
| Fallback | Se PNG não carregar, desenha bolinha atual (`draw_animation_cursor`) |

---

## 3. Abordagem escolhida

**Sprite + tint + rotação em tempo real** (sem cache pré-processado de ângulos/cores).

```text
load PNG → tint(cor veículo) → scale 16×16 → rotate(ângulo) → blit(centro na polyline)
```

Alternativas descartadas: cache de sprites por cor×ângulo (complexidade desnecessária para 16×16); desenho vetorial pygame (menos ilustrativo).

---

## 4. Componentes

### 4.1 Asset `truck.png`

- Gerado no Cursor antes da implementação.
- Silhueta monocromática para multiply-blend tint.
- Sem texto, sem fundo opaco.
- Incluir nota de origem em comentário no módulo de sprite (gerado para o projeto).

### 4.2 `vehicle_sprite.py` (novo)

Responsabilidades:

| Função | Papel |
|--------|-------|
| `load_vehicle_sprite_base()` | Carrega PNG uma vez; retorna `Surface` com alpha ou `None` em falha |
| `tint_surface(surface, color)` | Aplica cor do veículo preservando alpha |
| `render_vehicle_sprite(color, angle_deg, size)` | Tint + scale + rotate; retorna surface pronta para blit |

Carregamento lazy na primeira animação ou no init do app (preferência: init do `pygame_application` para falha antecipada).

### 4.3 `route_animation.py`

Novo helper:

```python
def heading_along_polyline(points: List[Coordinate], progress: float) -> float:
    """Ângulo em graus do segmento ativo (0 = leste, sentido horário pygame)."""
```

- Reutiliza a mesma lógica de segmento que `point_along_polyline`.
- Segmento degenerado (comprimento ≈ 0): mantém último ângulo ou 0°.

### 4.4 `map_renderer.py`

- Adicionar `draw_animation_vehicle(screen, point, angle_deg, color, sprite_size=16)`.
- Internamente chama `render_vehicle_sprite`; em falha, delega a `draw_animation_cursor`.
- `draw_animation_cursor` permanece (fallback + testes existentes).

### 4.5 `pygame_application.py`

Substituir no bloco de animação focada:

```python
# antes
cursor = point_along_polyline(polyline, animation_progress)
draw_animation_cursor(screen, cursor, color)

# depois
position = point_along_polyline(polyline, animation_progress)
heading = heading_along_polyline(polyline, animation_progress)
draw_animation_vehicle(screen, position, heading, color)
```

### 4.6 `visual_theme.py` (opcional)

```python
vehicle_sprite_size: int = 16
```

### 4.7 Legenda (`application_layout.py`)

Atualizar entrada da legenda do mapa: de cursor circular genérico para **“Veículo em rota”** com indicação visual coerente (texto; mini-preview opcional se couber sem poluir).

---

## 5. Fluxo de dados

```text
focus_vehicle_id set
  → build_animation_polyline(mesh, plan)
  → animation_progress += ANIMATION_SPEED * dt
  → position = point_along_polyline(...)
  → heading = heading_along_polyline(...)
  → color = vehicle_route_colors[focus_id % len(...)]
  → draw_animation_vehicle(screen, position, heading, color)
```

Ordem de desenho inalterada: caminhão **acima** da malha e rotas, **abaixo** de bloqueios/depósito (mesma camada da bolinha atual).

---

## 6. Tint e rotação (detalhe)

### Tint

- Usar `pygame.Surface` com `BLEND_RGBA_MULT` ou pixel array: RGB ← cor do veículo, alpha preservado do sprite base.
- Sprite base deve ser claro; áreas transparentes não recebem tint.

### Rotação

- `pygame.transform.rotate` no sprite já escalado.
- Offset de blit: centro do retângulo rotacionado alinhado a `position` (int x, int y).
- Convenção: sprite original aponta para +X; `heading` derivado de `atan2(dy, dx)` em graus.

---

## 7. Erros e fallback

| Situação | Comportamento |
|----------|---------------|
| Arquivo PNG ausente | Log/warning silencioso; usa bolinha |
| PNG corrompido | Idem |
| Polyline com &lt; 2 pontos | Não desenha animação (como hoje) |
| `focus_vehicle_id` None | Sem animação (como hoje) |

---

## 8. Testes

| Arquivo | Caso |
|---------|------|
| `tests/test_route_animation.py` | `heading_along_polyline` horizontal → 0°, vertical para baixo → 90° |
| `tests/test_vehicle_sprite.py` | Load base não vazio; `tint_surface` altera pixels; `render_vehicle_sprite` retorna surface com tamanho esperado |
| Smoke manual | Focar V1 → caminhão colorido percorre rota girando; trocar V2 → cor muda; “Todos” → sem caminhão |

---

## 9. Arquivos

| Arquivo | Ação |
|---------|------|
| `traveling_salesman_problem/assets/truck.png` | Criar |
| `traveling_salesman_problem/visualization/vehicle_sprite.py` | Criar |
| `traveling_salesman_problem/visualization/route_animation.py` | `heading_along_polyline` |
| `traveling_salesman_problem/visualization/map_renderer.py` | `draw_animation_vehicle` |
| `traveling_salesman_problem/simulation/pygame_application.py` | Wire animação |
| `traveling_salesman_problem/config/visual_theme.py` | `vehicle_sprite_size` (opcional) |
| `traveling_salesman_problem/visualization/application_layout.py` | Legenda |
| `traveling_salesman_problem/visualization/__init__.py` | Exports se necessário |
| `tests/test_route_animation.py` | Estender |
| `tests/test_vehicle_sprite.py` | Criar |

---

## 10. Critérios de aceite

1. Com veículo focado, **não** aparece bolinha; aparece caminhão ~16×16 na cor do veículo.
2. Caminhão **gira** ao mudar de segmento da rota.
3. Animação em loop contínuo na mesma velocidade perceptível de antes.
4. Modo “Todos” sem caminhão.
5. PNG ausente → bolinha (sem crash).
6. Testes unitários novos passam; suite existente verde.
