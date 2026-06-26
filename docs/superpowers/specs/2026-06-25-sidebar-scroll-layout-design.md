# Design: Correção de Layout — Sidebar Scrollável

**Data:** 2026-06-25  
**Status:** Aprovado  
**Contexto:** Após extensão de prioridade de entregas, a sidebar excede a altura da janela e textos se sobrepõem.

---

## 1. Objetivo

Eliminar sobreposição de textos e controles na interface Pygame, garantindo que todo o conteúdo da sidebar seja acessível via scroll, sem reduzir o gráfico de convergência.

---

## 2. Decisões de design (validadas)

| Tópico | Decisão |
|--------|---------|
| Escopo do scroll | Tudo abaixo do gráfico rola junto (controles + ordem de entregas); gráfico e rodapé fixos |
| Cabeçalho do mapa | Fonte menor (11px) + labels abreviadas (`Gen`, `Fit`, `Dist`, `Prior`, `Mut`) |
| Interação scroll | Roda do mouse + barra fina (6px) à direita da sidebar |
| Ordem de entregas | Integrada no fluxo scrollável; exibir todas as 15 linhas |
| Altura do rodapé | 36px, texto em 2 linhas |

---

## 3. Diagnóstico

| Área | Problema |
|------|----------|
| Sidebar controles | ~640px de conteúdo vs ~506px disponíveis |
| Ordem de entregas | Posição fixa `y = window_height - 200` colide com seções adjacentes |
| Painel de terreno | Termina abaixo de `window_height` (940px) |
| Cabeçalho do mapa | String de métricas longa ultrapassa largura útil (~670px) |
| Rodapé | Atalhos longos cortados na sidebar de 450px |

---

## 4. Abordagens consideradas

### 4.1 SidebarScrollView com surface offscreen (escolhida)

Renderizar conteúdo scrollável numa surface virtual; blitar janela visível com offset Y; ajustar hit-test de eventos.

- **Prós:** widgets existentes quase intactos; escala para futuras adições.
- **Contras:** requer conversão de coordenadas de mouse.

### 4.2 Reposicionar Y dinamicamente

Recalcular `position_y` por frame conforme scroll.

- **Prós:** hit-test simples.
- **Contras:** refatoração frágil em `_create_control_widgets`.

### 4.3 Reduzir gráfico / aumentar janela

- **Prós:** sem scroll.
- **Contras:** não escala; piora UX do gráfico.

---

## 5. Arquitetura

### 5.1 Layout da sidebar

```
┌─ Sidebar (450px) ─────────────┐
│ [Gráfico convergência] 400px  │  FIXO
├───────────────────────────────┤
│ ▲ viewport scrollável         │  y = 410, height = 494px
│   · Algoritmo                 │
│   · Terreno no mapa           │
│   · Ações                     │
│   · Penalidades de terreno    │
│   · Ordem de entregas (15)    │
│ ▼                        [▐]  │  barra 6px
├───────────────────────────────┤
│ Rodapé (2 linhas, 36px)       │  FIXO
└───────────────────────────────┘
```

**Cálculo viewport:**
```
viewport_top = plot_height + control_gap = 410
footer_height = 36
viewport_height = window_height - viewport_top - footer_height - control_gap = 494
```

### 5.2 SidebarScrollView (`visualization/sidebar_scroll.py`)

```python
class SidebarScrollView:
    scroll_offset: float
    content_height: int
    viewport_top: int
    viewport_height: int
    scrollbar_width: int = 6

    def handle_event(event: pygame.event.Event) -> bool
    def set_content_height(height: int) -> None
    def begin_draw(screen: pygame.Surface) -> float   # retorna offset Y
    def end_draw(screen: pygame.Surface) -> None      # blit + scrollbar
    def translate_mouse_position(position: tuple[int, int]) -> tuple[int, int]
```

**Comportamento:**
- Scroll wheel: 40px/tick quando `mouse.x < sidebar_width`
- Thumb arrastável; altura proporcional ao viewport/content ratio (mínimo 24px)
- Track: `VisualTheme.neutral_background`; thumb: `VisualTheme.neutral`

### 5.3 simulation_state.py

- Posições Y dos widgets relativas ao **topo do conteúdo scrollável** (origem interna y=0)
- Método `calculate_scrollable_content_height(delivery_order_rows: int) -> int`
- `handle_control_events`: traduzir `event.pos` via `scroll_view.translate_mouse_position` antes de repassar aos widgets

### 5.4 pygame_application.py

Ordem de desenho:
1. Chrome + gráfico (fixo)
2. `scroll_view.begin_draw()` → desenhar seções/controles/ordem de entregas com offset
3. `scroll_view.end_draw()` → barra
4. Rodapé (fixo)

Remover posição fixa `settings.window_height - 200` do painel de ordem de entregas.

### 5.5 Cabeçalho do mapa

- Fonte métricas: monospace **11px** (era 13px)
- Labels: `Gen`, `Fit`, `Dist`, `Prior`, `Mut`
- Valores inteiros quando possível
- Altura do cabeçalho: **44px** (inalterada)
- Fallback: truncar com `…` se ainda overflow

### 5.6 Rodapé

Duas linhas (fonte 10px):
```
Q · Sair          Esc · Fechar
O · Terreno       P · Hospitalar
```

---

## 6. Arquivos modificados

| Arquivo | Mudança |
|---------|---------|
| `visualization/sidebar_scroll.py` | **Novo** |
| `simulation/simulation_state.py` | Y relativos, content height, eventos |
| `simulation/pygame_application.py` | Loop com scroll viewport |
| `visualization/application_layout.py` | Métricas abreviadas, rodapé 2 linhas |
| `config/visual_theme.py` | `sidebar_footer_height`, `scrollbar_width` |
| `config/application_settings.py` | Ajuste `controls_top_position` se necessário |

---

## 7. Verificação manual

1. Nenhuma sobreposição visível na sidebar
2. Scroll por roda e barra funcional
3. Sliders/botões clicáveis após scroll
4. 15 linhas de ordem de entregas acessíveis
5. Cabeçalho do mapa sem overlap
6. Rodapé legível em 2 linhas

Sem testes automatizados de UI — validação visual.

---

## 8. Escopo fora deste design

- Redimensionamento dinâmico da janela
- Scroll no mapa ou legenda
- Abas/colapso de seções
