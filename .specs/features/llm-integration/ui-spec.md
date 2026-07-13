# Especificação de UI: Aba Assistente

**Feature:** `llm-integration`  
**Localização:** `TabPanel.vue` → aba "Assistente" (5ª aba)  
**Componente raiz:** `LlmAssistantPanel.vue`

---

## Posição no layout

O dashboard mantém o grid existente:

```
┌─────────────┬──────────────────┬─────────────────────────┐
│  Sidebar    │  TabPanel        │  MapPanel               │
│  300px      │  380px           │  flex 1                 │
│             │  [Assistente]    │                         │
└─────────────┴──────────────────┴─────────────────────────┘
```

A aba Assistente ocupa o corpo do `TabPanel` (mesma área de Resumo, Stats, etc.).

### Tabs atualizadas

```typescript
const tabs = [
  { id: "resumo", label: "Resumo" },
  { id: "stats", label: "Estatísticas" },
  { id: "history", label: "Histórico" },
  { id: "logs", label: "Logs" },
  { id: "assistente", label: "Assistente" },  // NOVA
];
```

---

## Wireframe detalhado

```
┌─────────────────────────────────────────┐
│ ● Ollama conectado          [badge]       │  ← llm-status
├─────────────────────────────────────────┤
│ ⚠ Execute ollama serve...   [banner]    │  ← só se offline
├─────────────────────────────────────────┤
│ ℹ Respostas baseadas nos dados...       │  ← disclaimer
├─────────────────────────────────────────┤
│ Ações                                   │
│ ┌─────────────────┐ ┌───────────────┐   │
│ │ Veículo: [Todos▾]│ │ Gerar Instr.  │   │
│ └─────────────────┘ └───────────────┘   │
│ [Rel. Diário] [Rel. Semanal] [Sugestões]│
├─────────────────────────────────────────┤
│ ┌─ Área de resposta ─────────────────┐  │
│ │ # Instruções de Entrega            │  │  ← LlmOutputViewer
│ │ ## Veículo 1                       │  │     max-height: 240px
│ │ 1. Saia do depósito...             │  │     scroll vertical
│ └────────────────────────────────────┘  │
│ [Exportar MD]  [Exportar PDF]           │
├─────────────────────────────────────────┤
│ Chat                                    │
│ ┌────────────────────────────────────┐  │
│ │ Você: Quantos veículos ativos?     │  │  ← LlmChatBox
│ │ Assistente: Há 3 veículos...       │  │
│ └────────────────────────────────────┘  │
│ [ Pergunte sobre rotas...        ][▶]   │
└─────────────────────────────────────────┘
```

---

## Componentes e props

### `LlmAssistantPanel.vue`

| Prop | Tipo | Descrição |
|------|------|-----------|
| `state` | `StateUpdate \| null` | Estado WebSocket atual |

**Comportamento:**
- `onMounted` → chama `health()`
- Deriva `vehicleIds` de `Object.keys(state.plans)`
- `hasPlans = vehicleIds.length > 0`

### `LlmActionBar.vue`

| Prop | Tipo | Descrição |
|------|------|-----------|
| `loading` | `boolean` | Desabilita botões durante geração |
| `disabled` | `boolean` | Sem plans ou Ollama offline |
| `vehicleIds` | `number[]` | IDs para dropdown |

| Emit | Payload |
|------|---------|
| `generate` | `(type: GenerateType, vehicleId?: number)` |

**Botões:**

| Botão | `type` | Notas |
|-------|--------|-------|
| Gerar Instruções | `instructions` | Usa `vehicleId` do dropdown |
| Rel. Diário | `daily_report` | — |
| Rel. Semanal | `weekly_report` | — |
| Sugestões | `improvements` | — |

**Dropdown veículo:**
- Opção default: "Todos os veículos" → `vehicleId = null`
- Opções: "Veículo 1", "Veículo 2", ... (id + 1 para display)

Usar `UiButton` existente (`variant="secondary"` ou `"primary"` no botão principal).

### `LlmOutputViewer.vue`

| Prop | Tipo |
|------|------|
| `content` | `string` |

- Renderiza com `marked.parse(content)`
- Placeholder se vazio: "_Sem conteúdo ainda. Use os botões acima para gerar._"
- `id="llm-print-area"` para fallback print PDF

### `LlmChatBox.vue`

| Prop | Tipo |
|------|------|
| `loading` | `boolean` |
| `history` | `ChatMessage[]` |

| Emit | Payload |
|------|---------|
| `send` | `(message: string)` |

- Enter no input envia mensagem
- Input desabilitado durante `loading`
- Mensagens user alinhadas à direita (opcional) ou estilo chat simples

---

## Estados visuais

### Status Ollama (`llm-status`)

| Condição | Cor | Texto |
|----------|-----|-------|
| `ok: true` | `--success` (#16a34a) | "Ollama conectado" |
| `ok: false` | `--danger` (#dc2626) | Mensagem do backend ou "Ollama indisponível" |
| Carregando | `--text-muted` | "Verificando..." |

### Banner offline (`llm-banner`)

Exibido quando `ollamaStatus?.ok === false`:

```
Execute ollama serve e ollama pull gemma4:e2b
```

Estilo: fundo `--danger-soft`, texto `--danger`, `font-size: 12px`.

### Disclaimer (`llm-disclaimer`)

Sempre visível:

```
Respostas baseadas nos dados da simulação. Verifique números críticos.
```

Estilo: `--text-muted`, `font-size: 11px`, itálico.

### Loading

- Botão clicado mostra texto "Gerando..." ou spinner inline
- Todos os botões de ação + chat input desabilitados
- `LlmOutputViewer` mantém conteúdo anterior até nova resposta

### Erro

- `error` do composable exibido abaixo dos botões de export
- Classe `.error-text` (vermelho, 12px)
- Erro 504: "Tempo esgotado — o modelo local pode estar lento."

---

## Estilos (CSS variables existentes)

```css
.llm-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
  height: 100%;
}

.llm-status {
  font-size: 12px;
  font-weight: 600;
  color: var(--danger);
}
.llm-status--ok {
  color: var(--success);
}

.llm-output {
  background: var(--bg-muted);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 12px;
  font-size: 13px;
  line-height: 1.5;
  max-height: 240px;
  overflow-y: auto;
  color: var(--text-primary);
}

.llm-export-row {
  display: flex;
  gap: 8px;
}

.llm-chat-messages {
  max-height: 160px;
  overflow-y: auto;
  font-size: 12px;
}

@media print {
  .llm-output { max-height: none; overflow: visible; }
  .llm-action-bar, .llm-chat, .llm-status { display: none; }
}
```

Compatível com `[data-theme="dark"]` — usar apenas CSS variables, sem cores hardcoded.

---

## Composable `useLlmApi`

### Estado reativo

| Ref | Tipo | Inicial |
|-----|------|---------|
| `loading` | `boolean` | `false` |
| `error` | `string \| null` | `null` |
| `lastOutput` | `string` | `""` |
| `chatHistory` | `ChatMessage[]` | `[]` |
| `ollamaStatus` | `object \| null` | `null` |

### URL base

```typescript
const API_BASE = import.meta.env.DEV
  ? "http://127.0.0.1:8000"
  : "";
```

Mesmo padrão de `useWebSocket.ts`.

### Fluxo generate

1. `loading = true`, `error = null`
2. `POST /api/llm/generate`
3. Sucesso → `lastOutput = data.content`
4. Falha → `error = detail`
5. `loading = false`

### Fluxo chat

1. Não atualiza `lastOutput` (chat separado da área de resposta)
2. Sucesso → `chatHistory = data.history`

### Fluxo export

1. `POST /api/llm/export` → Blob → download via `<a>`
2. Se 501 + format pdf → `window.print()` no `#llm-print-area`

---

## Acessibilidade (mínimo v1)

- Botões com `type="button"`
- Input chat com `aria-label="Pergunta sobre rotas"`
- Status Ollama não depende só de cor (inclui texto)
- Contraste adequado em dark mode via tokens

---

## Mapeamento REQ → UI

| Requisito | Elemento UI |
|-----------|-------------|
| REQ-LLM-01 | Botão "Gerar Instruções" + OutputViewer |
| REQ-LLM-02 | Dropdown veículo |
| REQ-LLM-03 | `:disabled="!hasPlans"` nos botões |
| REQ-LLM-09–12 | LlmChatBox |
| REQ-LLM-15–17 | Botões Exportar MD/PDF |
| REQ-LLM-18–21 | llm-status + llm-banner |
| REQ-LLM-NFR-06 | llm-disclaimer |
