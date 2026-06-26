# Design: Setas e Posição na Rota Sempre Visíveis

**Data:** 2026-06-25  
**Status:** Aprovado  
**Contexto:** Simplificar UX removendo toggle; exibir sempre setas de direção e posição de visita no mapa.

---

## 1. Objetivo

Mostrar **sempre** na melhor rota:
- setas de direção nos trechos
- número da **posição na rota** (1, 2, 3…) abaixo de cada nó

Manter cor de prioridade no círculo da cidade.

---

## 2. Decisões (validadas)

| Tópico | Decisão |
|--------|---------|
| Setas | Sempre visíveis (remove toggle) |
| Número | Posição na rota (não ID fixo da cidade) |
| Estilo número | Texto abaixo do nó, fonte 10px |
| Prioridade | Cor do círculo mantida |
| Posição 1 | Texto bold |
| Referência ordem | Rotação a partir de `city_coordinates[0]` |

---

## 3. Mudanças

### 3.1 Remover toggle

- `route_direction_toggle` em `SimulationState`
- `show_route_direction` property
- Recalcular `section_quantity_y` após slider de prioridade

### 3.2 `draw_route_visit_positions()` em `map_renderer.py`

- Mapa `coordenada → posição` via rota rotacionada
- Renderizar número centrado em `(x, y + node_radius + 6)`
- Posição 1 em bold

### 3.3 `pygame_application.py`

Ordem de desenho:
1. cidades
2. melhor rota + setas (sempre)
3. posições abaixo dos nós
4. segunda melhor rota

### 3.4 Legenda

- `→ Direção da rota` — sempre
- `Posição na rota (1–N)` — item explicativo

---

## 4. Verificação manual

1. Setas visíveis ao abrir sem ação do usuário
2. Números abaixo dos nós = sidebar ordem de entregas
3. Toggle removido da sidebar
4. Cor de prioridade preservada

---

## 5. Escopo fora

- Toggle para ocultar setas/números
- ID fixo da cidade no mapa
- Números dentro do círculo
