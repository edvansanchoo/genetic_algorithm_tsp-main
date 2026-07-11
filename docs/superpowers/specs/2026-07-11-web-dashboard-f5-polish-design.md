# Design: F5 — Polish visual pixel-close do dashboard Web

**Data:** 2026-07-11  
**Status:** Aprovado  
**Branch:** atual  
**Commits:** nenhum até pedido explícito do usuário

**Contexto:** A v1 Web (F1–F4) entrega paridade funcional com layout simples. Esta especificação cobre a **Fase F5**: transformar o dashboard em reprodução pixel-close da imagem de referência (`melhoria_visual.md`), preservando funcionalidade e core intocável.

**Depende de:** `docs/superpowers/specs/2026-07-11-web-dashboard-design.md` (v1 implementada).

---

## 1. Objetivo

Elevar a interface Web de wireframe funcional para dashboard profissional **pixel-close** à referência visual, incluindo:

- Design tokens CSS (claro + escuro)
- Componentes UI customizados (switch, slider, cards, badges)
- Layout com mapa dominante (~58% largura)
- Cartões de rota coloridos por veículo
- Legenda flutuante no mapa
- Métricas amigáveis no header (Custo total, Prioridade atendida %)
- Footer com indicador pulsante “Executando”

**Não alterar:** GA, VRP, Pygame desktop, lógica de simulação.

---

## 2. Decisões validadas (brainstorming)

| Tópico | Decisão |
|--------|---------|
| Fidelidade | **Pixel-close** à imagem de referência |
| Tema | Claro + escuro com toggle no header |
| CSS | Puro + design tokens (sem Tailwind/libs) |
| Abas | Manter 4: Resumo, Estatísticas, Histórico, Logs |
| Abordagem | Incremental por camada (tokens → layout → componentes → telas) |
| Toggle 2ª melhor rota | Preferência **frontend** (localStorage); não altera GA |
| Toggle nós trânsito | Preferência **frontend** (localStorage) |
| Cores veículo UI | Referência: V1 azul, V2 verde, V3 vermelho |
| Cores veículo mapa | Alinhar via `display.vehicle_colors_ui` no serializer (só Web) |
| Git | Sem commit até pedido explícito |

---

## 3. Regra inviolável: Core intocável

Adaptações permitidas:

- `state_serializer.py` — campos de **apresentação** (`total_cost`, `priority_served_pct`, `display.*`)
- Frontend — CSS, componentes, preferências locais (`localStorage`)
- **Não** alterar fitness, decoder, população, seleção, crossover, mutação

---

## 4. Design tokens

Arquivo: `frontend/src/styles/tokens.css`

### 4.1 Tema claro (`:root`)

| Token | Valor | Uso |
|-------|-------|-----|
| `--bg-app` | `#f8f9fc` | Fundo geral |
| `--bg-panel` | `#ffffff` | Cards/painéis |
| `--bg-muted` | `#f1f4f9` | Mini-cards sidebar |
| `--bg-map` | `#e8f5e0` | Fundo canvas |
| `--text-primary` | `#1c2030` | Texto principal |
| `--text-muted` | `#607080` | Labels, hints |
| `--accent` | `#2563eb` | Botões primários, switches ativos |
| `--accent-hover` | `#1d4ed8` | Hover |
| `--accent-soft` | `#eff6ff` | Cartão rota ativo |
| `--border` | `#d6dce5` | Bordas |
| `--shadow-card` | `0 1px 3px rgba(15,23,42,.08), 0 1px 2px rgba(15,23,42,.04)` | Elevação |
| `--radius-lg` | `12px` | Cards |
| `--radius-md` | `8px` | Botões, inputs |
| `--vehicle-1` | `#2563eb` | Veículo 1 |
| `--vehicle-2` | `#059669` | Veículo 2 |
| `--vehicle-3` | `#dc2626` | Veículo 3 |
| `--vehicle-4` | `#d97706` | Veículo 4 |
| `--vehicle-5` | `#7c3aed` | Veículo 5 |
| `--success` | `#16a34a` | Dot “Executando” |
| `--sidebar-width` | `300px` | Sidebar fixa |
| `--center-width` | `380px` | Coluna central |

### 4.2 Tema escuro (`[data-theme="dark"]`)

| Token | Valor |
|-------|-------|
| `--bg-app` | `#0f172a` |
| `--bg-panel` | `#1e293b` |
| `--bg-muted` | `#334155` |
| `--bg-map` | `#1a2e1a` |
| `--text-primary` | `#e2e8f0` |
| `--text-muted` | `#94a3b8` |
| `--border` | `#475569` |
| `--shadow-card` | `0 1px 3px rgba(0,0,0,.3)` |

### 4.3 Tipografia

- UI: `"Segoe UI", system-ui, sans-serif`
- Monospace (rotas): `"Consolas", monospace`
- Section titles: `11px`, `700`, uppercase, letter-spacing `0.06em`, cor `--text-muted`

---

## 5. Layout

```
┌─ Header (64px) ──────────────────────────────────────────────┐
├─ Sidebar ──┬─ Centro ─────────┬─ Mapa (~58%) ────────────────┤
│  300px     │  380px           │  flex: 1                     │
│            │  [4 abas]        │  toolbar + canvas + legenda  │
├─ Footer (48px) ──────────────────────────────────────────────┤
```

Grid CSS:

```css
.main-grid {
  grid-template-columns: var(--sidebar-width) var(--center-width) 1fr;
}
```

Breakpoint `< 1200px`: empilha colunas (comportamento responsivo preservado).

---

## 6. Componentes UI base

Diretório: `frontend/src/components/ui/`

| Componente | Props principais | Notas |
|------------|------------------|-------|
| `UiSwitch` | `modelValue`, `label` | Track 36×20px, thumb 16px, transição 200ms |
| `UiSlider` | `modelValue`, `min`, `max`, `step`, `label`, `suffix` | Valor à direita; track custom |
| `UiCard` | `padding`, `shadow` | Fundo `--bg-panel`, radius `--radius-lg` |
| `UiMetricCard` | `label`, `value`, `unit?` | Header metrics |
| `UiButton` | `variant`: primary/secondary/danger/ghost, `icon?` | Nova execução = primary |
| `UiBadge` | `priority`: 1–10 | Gradiente verde→amarelo→vermelho |
| `UiTabBar` | `tabs`, `active` | Underline azul na aba ativa |
| `UiIcon` | `name` | SVGs: ambulance, pause, play, dice, hospital, reset, fullscreen, zoom |

---

## 7. Header

| Zona | Conteúdo |
|------|----------|
| Esquerda | `UiIcon(ambulance)` + “VRP Hospitalar • Algoritmo Genético” |
| Centro | 3× `UiMetricCard`: Distância total, Custo total, Prioridade atendida % |
| Direita | Botão Tema, botão Pausar (ícone), botão Nova execução (primary) |

**Métricas (serializer):**

| Label UI | Campo JSON | Cálculo |
|----------|------------|---------|
| Distância total | `metrics.distance` | Existente, formato `X.XX km` |
| Custo total | `metrics.total_cost` | `round(total_fitness, 0)` |
| Prioridade atendida | `metrics.priority_served_pct` | Ver §12 |

**Remover** pill “Conectado/Desconectado” do header. Erros de conexão permanecem como banner discreto abaixo do header.

---

## 8. Sidebar

### 8.1 Resumo com ícones (topo)

Três mini-cards horizontais:

- Veículos: `summary.vehicles_active / summary.vehicles_total`
- Capacidade: `summary.capacity_total un`
- Entregas: `summary.deliveries_done / summary.deliveries_total`

### 8.2 Parâmetros

5× `UiSlider` ligados a `set_param` WebSocket (comportamento existente).

### 8.3 Configurações

3× `UiSwitch`:

| Label | Backend / Frontend |
|-------|-------------------|
| 2-opt (melhoria local) | `set_toggle` → `two_opt` |
| Exibir malha de ruas | `set_toggle` → `show_mesh` |
| Mostrar 2ª melhor rota | Frontend `localStorage` key `pref.show_runner_up` |

### 8.4 Ações rápidas

| Botão | Ícone | Comando |
|-------|-------|---------|
| Sortear posições | dice | `action: shuffle_positions` |
| Cenário hospitalar | hospital | `action: hospital_preset` |
| Resetar cenário | reset (danger) | `shuffle_positions` + `clear_blocked` sequencial |

### 8.5 Legenda prioridade

Barra horizontal com `UiBadge` 1–10, gradiente de cores.

---

## 9. Coluna central (abas)

### 9.1 UiTabBar

Abas: **Resumo** | **Estatísticas** | **Histórico** | **Logs**

Estilo: texto + underline azul na ativa (referência).

### 9.2 Aba Resumo

1. **Convergência do algoritmo** — Chart.js, linhas nas cores `--vehicle-N`, legenda V1/V2/V3
2. **Rotas por veículo** — lista de `VehicleRouteCard`

### 9.3 VehicleRouteCard

```
┌─ [cor borda esquerda 4px] Veículo N ──────────────────┐
│  {distance} km    {load}/{capacity} un    {trips} viagens │
│  D → [badge:8] A → [badge:5] C → D                        │
└───────────────────────────────────────────────────────────┘
```

- Cor do veículo: `display.vehicle_colors_ui[vehicle_id]`
- Clique header → `set_focus(vehicle_id, null)`
- Clique viagem → `set_focus(vehicle_id, trip_index)`
- Ativo: fundo `--accent-soft`, borda `--accent`

Dados: `state.plans[vehicle_id]` + `routes_panel` + prioridades de `map.deliveries`.

### 9.4 Abas Estatísticas / Histórico / Logs

Manter conteúdo atual, aplicar tokens visuais (cards, tabelas, log console).

---

## 10. Mapa

Componente: `MapPanel.vue` (toolbar + `MapCanvas` + `MapLegend`)

### 10.1 Toolbar superior direita

| Controle | Tipo | Estado |
|----------|------|--------|
| Nós de trânsito | `UiSwitch` | Frontend pref `pref.show_transit` |
| Malha de ruas | `UiSwitch` | Sincronizado com `toggles.show_mesh` |
| Filtro veículo | Select estilizado | `set_focus` |
| Fullscreen | Ícone | `requestFullscreen()` |

### 10.2 Toolbar inferior direita

| Controle | Comportamento |
|----------|---------------|
| Zoom + / − | Escala canvas 1.0–2.5, step 0.25 |
| Bloquear nó | Toggle modo; hint “Clique em um nó para bloquear/desbloquear” |

### 10.3 Legenda flutuante (`MapLegend.vue`)

Card branco semi-opaco, canto inferior esquerdo do mapa:

- Depósito (quadrado preto)
- Entrega (círculo gradiente)
- Nó de trânsito (círculo cinza)
- Bloqueado (X vermelho)
- Rota atual (linha sólida)
- 2ª melhor rota (linha tracejada)

### 10.4 Canvas

- Respeitar `pref.show_runner_up` e `pref.show_transit`
- Cores de rota: `display.vehicle_colors_ui` quando disponível
- Zoom: transformação aplicada em `mapTransform.ts`

---

## 11. Footer

**Esquerda:**
```
Algoritmo Genético  ● Executando
Geração {n}  ·  População {size}  ·  Elite {elite_pct}%
```

- Dot verde pulsante (`@keyframes pulse`) quando `running`
- `elite_pct` = `10` (fixo; `display.elite_pct` do serializer, derivado de população 100 com 10% elite)

**Direita:**
```
Fitness: {fitness}  ·  Distância: {distance} km  ·  Penal. prioridade: {n}  ·  Penal. bloqueio: {n}
```

FPS removido do footer (permanece acessível na aba Logs se necessário).

---

## 12. Métricas derivadas (serializer)

Arquivo: `traveling_salesman_problem/web/state_serializer.py`

### 12.1 Custo total

```python
total_cost = round(total_fitness, 0)
```

### 12.2 Prioridade atendida %

Para cada entrega com `priority >= 8`:

1. Encontrar posição na rota (ordem de visita entre todas as viagens)
2. Considerar “atendida cedo” se posição normalizada ≤ 0.33 (primeiro terço)
3. `priority_served_pct = round(atendidas_cedo / total_criticas * 100)` ou 100 se nenhuma crítica

Campo: `metrics.priority_served_pct`

### 12.3 Display helpers

```python
"display": {
  "vehicle_colors_ui": ["#2563eb", "#059669", "#dc2626", "#d97706", "#7c3aed"],
  "elite_pct": 10,
}
```

Cores UI aplicadas no frontend; mapa Web usa `vehicle_colors_ui` em vez de `VisualTheme.vehicle_route_colors` quando renderizando no browser.

---

## 13. Tema claro/escuro

Composable: `frontend/src/composables/useTheme.ts`

- Toggle no header alterna `document.documentElement.dataset.theme`
- Persistência: `localStorage.setItem('theme', 'light'|'dark')`
- Init: lê localStorage; fallback `prefers-color-scheme`
- Chart.js e canvas re-renderizam ao trocar tema

---

## 14. Preferências frontend (localStorage)

| Key | Default | Efeito |
|-----|---------|--------|
| `pref.show_runner_up` | `true` | Exibe runner-up no canvas |
| `pref.show_transit` | `true` | Exibe nós de trânsito |
| `theme` | `light` | Tema claro/escuro |

---

## 15. Critérios de aceite

- [ ] Header pixel-close: logo, 3 metrics, tema, pausar, nova execução
- [ ] Sidebar: ícones resumo, sliders custom, 3 switches, ações com ícone, legenda prioridade
- [ ] Cartões rota coloridos com badges de prioridade
- [ ] Gráfico com cores V1/V2/V3 da referência
- [ ] Mapa ~58% largura, legenda, zoom, fullscreen, bloquear nó
- [ ] Footer com dot pulsante
- [ ] Tema escuro funcional
- [ ] 4 abas preservadas
- [ ] 124+ testes Python passando
- [ ] `python main.py` inalterado
- [ ] Nenhuma alteração no GA/VRP core

---

## 16. Arquivos a criar/modificar

| Ação | Arquivo |
|------|---------|
| Create | `frontend/src/styles/tokens.css` |
| Create | `frontend/src/styles/theme.css` |
| Create | `frontend/src/composables/useTheme.ts` |
| Create | `frontend/src/composables/usePreferences.ts` |
| Create | `frontend/src/components/ui/*.vue` (8 componentes) |
| Create | `frontend/src/components/VehicleRouteCard.vue` |
| Create | `frontend/src/components/MapLegend.vue` |
| Create | `frontend/src/components/MapPanel.vue` |
| Modify | `frontend/src/styles/layout.css` |
| Modify | `frontend/src/App.vue` |
| Modify | `frontend/src/components/AppHeader.vue` |
| Modify | `frontend/src/components/StatusFooter.vue` |
| Modify | `frontend/src/components/Sidebar*.vue` |
| Modify | `frontend/src/components/TabPanel.vue` |
| Modify | `frontend/src/canvas/mapRenderer.ts` |
| Modify | `frontend/src/canvas/mapTransform.ts` |
| Modify | `traveling_salesman_problem/web/state_serializer.py` |
| Modify | `frontend/src/types/simulation.ts` |
| Modify | `tests/test_state_serializer.py` |

---

## 17. Fora de escopo

- Alterações Pygame desktop
- Alterações GA/VRP core
- Deploy cloud / Docker
- Mapas geográficos reais
- Bibliotecas CSS externas (Tailwind, Bootstrap)
- Geração máxima configurável (footer usa `Geração n` sem limite)

---

## 18. Ordem de implementação sugerida

1. Tokens + tema + useTheme
2. Componentes UI base
3. Header + Footer
4. Sidebar refactor
5. VehicleRouteCard + TabPanel Resumo
6. Serializer métricas derivadas
7. MapPanel + legenda + zoom/fullscreen
8. Tema escuro pass final + testes

---

## 19. Resultado esperado

Dashboard Web visualmente indistinguível da referência em layout, cores, componentes e hierarquia — mantendo paridade funcional completa da v1 e core Python intocável.
