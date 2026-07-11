# Web Dashboard F5 Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the functional Web dashboard (v1) into a pixel-close match of the reference image — design tokens, custom UI components, colored route cards, map legend, derived metrics, and light/dark theme — without touching GA/VRP core or Pygame desktop.

**Architecture:** Incremental frontend refactor using pure CSS design tokens + 8 reusable `Ui*` components; extend `state_serializer.py` with presentation-only fields (`total_cost`, `priority_served_pct`, `display.*`); frontend preferences in `localStorage` for runner-up and transit visibility.

**Tech Stack:** Vue 3, Vite, Chart.js, Canvas 2D, pure CSS variables. Python serializer tests (unittest). Spec: `docs/superpowers/specs/2026-07-11-web-dashboard-f5-polish-design.md`.

## Global Constraints

- **Do not create git commits** unless the user explicitly asks
- **Core intocável:** no changes to GA, VRP decoder, fitness, crossover, mutation, selection, population
- Desktop `python main.py` must work exactly as today
- CSS pure + design tokens only — **no Tailwind, no new CSS libraries**
- Vehicle UI colors: V1 `#2563eb`, V2 `#059669`, V3 `#dc2626`, V4 `#d97706`, V5 `#7c3aed`
- Keep 4 tabs: Resumo, Estatísticas, Histórico, Logs
- Toggle "2ª melhor rota" and "Nós de trânsito" = frontend `localStorage` only
- Spec: `docs/superpowers/specs/2026-07-11-web-dashboard-f5-polish-design.md`

---

## File map

| File | Responsibility |
|------|----------------|
| Create: `frontend/src/styles/tokens.css` | CSS variables light/dark |
| Create: `frontend/src/styles/theme.css` | Pulse animation, theme transitions |
| Create: `frontend/src/composables/useTheme.ts` | Theme toggle + localStorage |
| Create: `frontend/src/composables/usePreferences.ts` | `pref.show_runner_up`, `pref.show_transit` |
| Create: `frontend/src/components/ui/UiSwitch.vue` | Custom toggle |
| Create: `frontend/src/components/ui/UiSlider.vue` | Custom range slider |
| Create: `frontend/src/components/ui/UiCard.vue` | Panel card |
| Create: `frontend/src/components/ui/UiMetricCard.vue` | Header metric |
| Create: `frontend/src/components/ui/UiButton.vue` | Button variants |
| Create: `frontend/src/components/ui/UiBadge.vue` | Priority badge 1–10 |
| Create: `frontend/src/components/ui/UiTabBar.vue` | Underline tabs |
| Create: `frontend/src/components/ui/UiIcon.vue` | Inline SVG icons |
| Create: `frontend/src/components/VehicleRouteCard.vue` | Colored route card |
| Create: `frontend/src/components/MapLegend.vue` | Floating map legend |
| Create: `frontend/src/components/MapPanel.vue` | Map toolbar + canvas + legend |
| Create: `frontend/src/utils/priorityColor.ts` | JS port of `priority_to_color` |
| Modify: `frontend/src/styles/layout.css` | Grid 300px / 380px / 1fr |
| Modify: `frontend/src/main.ts` | Import tokens.css, theme.css |
| Modify: `frontend/src/App.vue` | Wire theme, preferences, MapPanel |
| Modify: `frontend/src/components/AppHeader.vue` | Pixel-close header |
| Modify: `frontend/src/components/StatusFooter.vue` | Pulsing dot footer |
| Modify: `frontend/src/components/Sidebar*.vue` | UiSwitch, UiSlider, icons |
| Modify: `frontend/src/components/TabPanel.vue` | UiTabBar, VehicleRouteCard |
| Modify: `frontend/src/canvas/mapRenderer.ts` | Prefs, UI colors, zoom |
| Modify: `frontend/src/canvas/mapTransform.ts` | Zoom scale factor |
| Modify: `frontend/src/types/simulation.ts` | New metrics/display fields |
| Modify: `traveling_salesman_problem/web/state_serializer.py` | Derived metrics |
| Modify: `tests/test_state_serializer.py` | New field tests |

---

### Task 1: Design tokens + theme composable

**Files:**
- Create: `frontend/src/styles/tokens.css`
- Create: `frontend/src/styles/theme.css`
- Create: `frontend/src/composables/useTheme.ts`
- Modify: `frontend/src/main.ts`

**Interfaces:**
- Produces:
```typescript
export function useTheme() {
  const theme: Ref<"light" | "dark">
  function toggleTheme(): void
  function initTheme(): void
  return { theme, toggleTheme, initTheme }
}
```

- [ ] **Step 1: Create `tokens.css`** with all variables from spec §4.1 and §4.2

- [ ] **Step 2: Create `theme.css`** with:
```css
@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
.status-dot--running {
  animation: pulse-dot 1.5s ease-in-out infinite;
}
```

- [ ] **Step 3: Implement `useTheme.ts`** — init on mount, persist to `localStorage` key `theme`

- [ ] **Step 4: Import in `main.ts`**
```typescript
import "./styles/tokens.css";
import "./styles/theme.css";
import "./styles/layout.css";
```

- [ ] **Step 5: Verify** — toggle `document.documentElement.dataset.theme` in browser devtools; colors change

---

### Task 2: UI base components (Switch, Button, Card, Badge)

**Files:**
- Create: `frontend/src/components/ui/UiSwitch.vue`
- Create: `frontend/src/components/ui/UiButton.vue`
- Create: `frontend/src/components/ui/UiCard.vue`
- Create: `frontend/src/components/ui/UiBadge.vue`
- Create: `frontend/src/utils/priorityColor.ts`

**Interfaces:**
- `UiSwitch`: props `modelValue: boolean`, `label: string`; emit `update:modelValue`
- `UiButton`: props `variant: 'primary'|'secondary'|'danger'|'ghost'`, `icon?: string`
- `UiBadge`: props `priority: number` (1–10)

- [ ] **Step 1: Implement `priorityColor.ts`**
```typescript
export function priorityToColor(priority: number): string {
  const p = Math.max(1, Math.min(10, priority));
  if (p <= 5) {
    const ratio = (p - 1) / 4;
    return interpolate("#4caf50", "#ffc107", ratio);
  }
  const ratio = (p - 5) / 5;
  return interpolate("#ffc107", "#f44336", ratio);
}
```

- [ ] **Step 2: Implement UiSwitch** — hidden checkbox + styled track/thumb, 36×20px

- [ ] **Step 3: Implement UiButton** — variants using CSS classes `.ui-btn--primary` etc.

- [ ] **Step 4: Implement UiCard** — slot content, `--shadow-card`, `--radius-lg`

- [ ] **Step 5: Implement UiBadge** — circular, uses `priorityToColor`

- [ ] **Step 6: Visual check** — mount components temporarily in App.vue or Story-like div

---

### Task 3: UI base components (Slider, MetricCard, TabBar, Icon)

**Files:**
- Create: `frontend/src/components/ui/UiSlider.vue`
- Create: `frontend/src/components/ui/UiMetricCard.vue`
- Create: `frontend/src/components/ui/UiTabBar.vue`
- Create: `frontend/src/components/ui/UiIcon.vue`

- [ ] **Step 1: UiSlider** — native range input visually hidden; custom track + thumb via CSS; label left, formatted value right

- [ ] **Step 2: UiMetricCard** — label muted small, value bold large, optional unit

- [ ] **Step 3: UiTabBar** — tabs array `{ id, label }`, active tab gets blue bottom border 2px

- [ ] **Step 4: UiIcon** — inline SVGs for: `ambulance`, `pause`, `play`, `dice`, `hospital`, `reset`, `fullscreen`, `zoom-in`, `zoom-out`, `sun`, `moon`

---

### Task 4: Serializer derived metrics

**Files:**
- Modify: `traveling_salesman_problem/web/state_serializer.py`
- Modify: `frontend/src/types/simulation.ts`
- Modify: `tests/test_state_serializer.py`

**Interfaces:**
- Produces in payload:
```python
"metrics": { ..., "total_cost": 1248, "priority_served_pct": 92 }
"display": { "vehicle_colors_ui": [...], "elite_pct": 10 }
```

- [ ] **Step 1: Write failing test**
```python
def test_serialize_state_includes_derived_metrics():
    # ... initialize_headless, run_one_generation ...
    assert "total_cost" in payload["metrics"]
    assert "priority_served_pct" in payload["metrics"]
    assert "display" in payload
    assert payload["display"]["vehicle_colors_ui"][0] == "#2563eb"
```

- [ ] **Step 2: Run test** → FAIL

- [ ] **Step 3: Implement helpers in state_serializer.py**
```python
VEHICLE_COLORS_UI = ["#2563eb", "#059669", "#dc2626", "#d97706", "#7c3aed"]

def _priority_served_pct(simulation, plans) -> int:
    critical = [d for d in simulation.deliveries if d.priority >= 8]
    if not critical:
        return 100
    # build visit order from plans, check first-third
    ...
```

- [ ] **Step 4: Add to serialize_state return dict**

- [ ] **Step 5: Run** `python -m unittest tests.test_state_serializer -v` → PASS

- [ ] **Step 6: Run full suite** `python -m unittest discover -s tests -q` → 124+ PASS

---

### Task 5: Header + Footer refactor

**Files:**
- Modify: `frontend/src/components/AppHeader.vue`
- Modify: `frontend/src/components/StatusFooter.vue`
- Modify: `frontend/src/App.vue`

- [ ] **Step 1: AppHeader** — UiIcon ambulance, 3× UiMetricCard (Distância, Custo total, Prioridade %), UiButton Tema/Pausar/Nova execução; remove "Conectado" pill

- [ ] **Step 2: StatusFooter** — left: title + pulsing dot + Geração/População/Elite; right: fitness metrics; remove FPS

- [ ] **Step 3: App.vue** — wire `useTheme().toggleTheme` to header; error banner below header only when `lastError`

- [ ] **Step 4: Visual verify** with `python web.py` + `npm run dev`

---

### Task 6: Sidebar refactor

**Files:**
- Modify: `frontend/src/components/SidebarInfo.vue`
- Modify: `frontend/src/components/SidebarParams.vue`
- Modify: `frontend/src/components/SidebarToggles.vue`
- Modify: `frontend/src/components/SidebarActions.vue`
- Create: `frontend/src/components/PriorityLegend.vue`

- [ ] **Step 1: SidebarInfo** — 3 horizontal mini-cards with UiIcon (vehicle, box, pin)

- [ ] **Step 2: SidebarParams** — replace native range with UiSlider × 5

- [ ] **Step 3: SidebarToggles** — UiSwitch × 3 (two_opt, show_mesh from WS; show_runner_up from usePreferences)

- [ ] **Step 4: SidebarActions** — UiButton with icons; "Resetar cenário" sends shuffle then clear_blocked

- [ ] **Step 5: PriorityLegend** — UiBadge 1 through 10 in horizontal row

---

### Task 7: VehicleRouteCard + TabPanel

**Files:**
- Create: `frontend/src/components/VehicleRouteCard.vue`
- Modify: `frontend/src/components/TabPanel.vue`
- Modify: `frontend/src/components/ConvergenceChart.vue`

- [ ] **Step 1: VehicleRouteCard** — props: `vehicleId`, `plan`, `deliveries`, `color`, `active`; left border 4px; header stats row; stop sequence with UiBadge per delivery stop

- [ ] **Step 2: TabPanel** — UiTabBar; Resumo tab shows ConvergenceChart + VehicleRouteCard list (remove embedded SidebarRoutes)

- [ ] **Step 3: ConvergenceChart** — use `display.vehicle_colors_ui` for dataset colors

- [ ] **Step 4: Delete or stop using `SidebarRoutes.vue`** in Resumo (keep file until confirmed unused)

---

### Task 8: Preferences composable + map renderer update

**Files:**
- Create: `frontend/src/composables/usePreferences.ts`
- Modify: `frontend/src/canvas/mapRenderer.ts`
- Modify: `frontend/src/canvas/mapTransform.ts`

**Interfaces:**
```typescript
export function usePreferences() {
  const showRunnerUp: Ref<boolean>
  const showTransit: Ref<boolean>
  return { showRunnerUp, showTransit }
}
```

- [ ] **Step 1: Implement usePreferences** — localStorage keys `pref.show_runner_up`, `pref.show_transit`, defaults `true`

- [ ] **Step 2: mapRenderer** — accept `prefs` and `vehicleColors` params; skip transit layer if `!showTransit`; skip runner-up if `!showRunnerUp`; use `vehicleColors[vehicleId]` for routes

- [ ] **Step 3: mapTransform** — add optional `zoom: number` multiplier to scale

---

### Task 9: MapPanel (legend, zoom, fullscreen)

**Files:**
- Create: `frontend/src/components/MapLegend.vue`
- Create: `frontend/src/components/MapPanel.vue`
- Modify: `frontend/src/components/MapCanvas.vue`
- Modify: `frontend/src/App.vue`

- [ ] **Step 1: MapLegend** — floating UiCard bottom-left with icon samples per spec §10.3

- [ ] **Step 2: MapPanel** — toolbar top-right (UiSwitch transit/mesh, vehicle select, fullscreen); toolbar bottom-right (zoom +/-, block mode toggle); contains MapCanvas + MapLegend

- [ ] **Step 3: MapCanvas** — accept `zoom`, `blockMode`, `prefs`; pass to mapRenderer; block mode shows hint overlay

- [ ] **Step 4: App.vue** — replace MapToolbar + MapCanvas with MapPanel; remove duplicate mesh toggle from old MapToolbar

- [ ] **Step 5: Fullscreen** — `mapPanelRef.value.requestFullscreen()`

---

### Task 10: Layout grid + dark theme pass

**Files:**
- Modify: `frontend/src/styles/layout.css`
- Modify: all components for `var(--*)` usage (replace hardcoded hex)

- [ ] **Step 1: Update grid**
```css
.main-grid {
  grid-template-columns: var(--sidebar-width) var(--center-width) 1fr;
}
.header { height: 64px; background: var(--bg-panel); box-shadow: var(--shadow-card); }
```

- [ ] **Step 2: Replace hardcoded colors** in layout.css and components with CSS variables

- [ ] **Step 3: Dark theme verify** — toggle theme; all panels readable

- [ ] **Step 4: Build** `cd frontend && npm run build` → success

---

### Task 11: Regression + acceptance checklist

**Files:**
- Modify: `tests/test_state_serializer.py` (edge cases for priority_served_pct)

- [ ] **Step 1: Run Python tests**
```bash
python -m unittest discover -s tests -q
```
Expected: all PASS

- [ ] **Step 2: Manual acceptance** — verify spec §15 checklist (15 items)

- [ ] **Step 3: Compare side-by-side** with reference image

- [ ] **Step 4: Confirm** `python main.py` still launches Pygame (smoke, 5s)

---

## Spec coverage checklist

| Spec requirement | Task |
|------------------|------|
| Design tokens light/dark | Task 1, 10 |
| UiSwitch, UiSlider, UiCard, UiBadge, UiButton, UiTabBar, UiIcon | Task 2, 3 |
| Header pixel-close | Task 5 |
| Footer pulsing dot | Task 5 |
| Sidebar icons, sliders, switches, legend | Task 6 |
| VehicleRouteCard | Task 7 |
| 4 tabs preserved | Task 7 |
| Derived metrics serializer | Task 4 |
| Map legend, zoom, fullscreen | Task 9 |
| Frontend preferences | Task 8 |
| vehicle_colors_ui on map | Task 8 |
| Layout 300/380/1fr | Task 10 |
| No GA/Pygame changes | All tasks |

---

## Execution commands

```bash
# Backend tests after Task 4
python -m unittest tests.test_state_serializer -v

# Full regression after Task 11
python -m unittest discover -s tests -q

# Frontend dev
python web.py
cd frontend && npm run dev

# Production build verify
cd frontend && npm run build
python web.py
```
