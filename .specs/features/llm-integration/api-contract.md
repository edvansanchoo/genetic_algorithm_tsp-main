# Contrato de API: Integração LLM

**Feature:** `llm-integration`  
**Base URL:** `http://127.0.0.1:8000` (mesmo host do `web.py`)  
**Prefixo:** `/api/llm`  
**Autenticação:** Nenhuma (ambiente local de desenvolvimento/demo)

---

## Visão geral

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/llm/health` | Verifica Ollama e modelo |
| POST | `/api/llm/generate` | Gera conteúdo estruturado (instruções, relatórios, sugestões) |
| POST | `/api/llm/chat` | Pergunta em linguagem natural |
| POST | `/api/llm/export` | Download MD ou PDF |

**Nota:** A simulação continua via WebSocket `ws://127.0.0.1:8000/ws` — endpoints LLM são independentes.

---

## CORS (desenvolvimento)

O FastAPI deve permitir origens do Vite dev server:

```
http://localhost:5173
http://127.0.0.1:5173
```

Em produção (frontend build servido pelo FastAPI na porta 8000), CORS same-origin — sem configuração extra.

---

## GET `/api/llm/health`

Verifica conectividade com Ollama e presença do modelo configurado.

### Response 200 — OK

```json
{
  "ok": true,
  "model": "gemma4:e2b",
  "message": "ok"
}
```

### Response 200 — Modelo ausente

```json
{
  "ok": false,
  "model": "gemma4:e2b",
  "message": "Modelo 'gemma4:e2b' não encontrado. Execute: ollama pull gemma4:e2b"
}
```

### Response 503 — Ollama offline

```json
{
  "detail": "Ollama não está rodando. Execute: ollama serve"
}
```

### Response 504 — Timeout

```json
{
  "detail": "Timeout ao conectar ao Ollama"
}
```

---

## POST `/api/llm/generate`

Gera conteúdo Markdown a partir do estado atual da simulação.

### Request

```json
{
  "type": "instructions",
  "vehicle_id": null
}
```

| Campo | Tipo | Obrigatório | Valores |
|-------|------|-------------|---------|
| `type` | string | sim | `instructions`, `daily_report`, `weekly_report`, `improvements` |
| `vehicle_id` | int \| null | não | Apenas para `instructions`; `null` = todos os veículos |

### Response 200

```json
{
  "type": "instructions",
  "content": "# Instruções de Entrega\n\n## Veículo 1\n\n1. Saia do depósito (D)...\n"
}
```

### Erros

| Status | Condição |
|--------|----------|
| 422 | `type` inválido ou body malformado |
| 503 | Ollama offline ou modelo ausente |
| 504 | Timeout na geração (> `OLLAMA_TIMEOUT`) |

### Exemplo cURL

```bash
curl -X POST http://127.0.0.1:8000/api/llm/generate \
  -H "Content-Type: application/json" \
  -d '{"type": "daily_report"}'
```

---

## POST `/api/llm/chat`

Conversa em linguagem natural com contexto da simulação.

### Request

```json
{
  "message": "Qual veículo tem mais entregas críticas?",
  "history": [
    { "role": "user", "content": "Quantos veículos estão ativos?" },
    { "role": "assistant", "content": "Há 3 veículos ativos na simulação atual." }
  ]
}
```

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `message` | string | sim | Pergunta atual (min 1 caractere) |
| `history` | array | não | Mensagens anteriores `{role, content}` |

**Roles válidos:** `user`, `assistant` (não enviar `system` — montado no backend).

### Response 200

```json
{
  "reply": "O veículo 2 transporta as entregas A e F, ambas com prioridade 9.",
  "history": [
    { "role": "user", "content": "Quantos veículos estão ativos?" },
    { "role": "assistant", "content": "Há 3 veículos ativos na simulação atual." },
    { "role": "user", "content": "Qual veículo tem mais entregas críticas?" },
    { "role": "assistant", "content": "O veículo 2 transporta as entregas A e F, ambas com prioridade 9." }
  ]
}
```

### Comportamento

- Backend injeta contexto JSON atual em cada chamada (não confia no cliente).
- Histórico limitado se estimativa de tokens exceder `LLM_MAX_CONTEXT_TOKENS`.
- Respostas em português brasileiro.

---

## POST `/api/llm/export`

Converte conteúdo Markdown em arquivo para download.

### Request

```json
{
  "content": "# Relatório Diário\n\nFitness: 1842\n...",
  "format": "md",
  "filename": "relatorio-2026-07-13"
}
```

| Campo | Tipo | Default | Descrição |
|-------|------|---------|-----------|
| `content` | string | — | Markdown a exportar (min 1 char) |
| `format` | string | `md` | `md` ou `pdf` |
| `filename` | string | `relatorio-vrp` | Nome sem extensão |

### Response 200 — Markdown

```
Content-Type: text/markdown; charset=utf-8
Content-Disposition: attachment; filename="relatorio-vrp.md"

# Relatório Diário
...
```

### Response 200 — PDF

```
Content-Type: application/pdf
Content-Disposition: attachment; filename="relatorio-vrp.pdf"

<binary>
```

### Response 501 — PDF indisponível

```json
{
  "detail": "WeasyPrint não instalado. Use requirements-llm.txt ou exporte MD."
}
```

Frontend deve chamar `window.print()` como fallback.

---

## Integração Ollama (backend interno)

O backend chama Ollama diretamente — **não exposto ao frontend**.

### Health: GET `{OLLAMA_BASE_URL}/api/tags`

### Chat: POST `{OLLAMA_BASE_URL}/api/chat`

```json
{
  "model": "gemma4:e2b",
  "messages": [
    { "role": "system", "content": "..." },
    { "role": "user", "content": "CONTEXTO:\n{...}\n\nGere a resposta solicitada." }
  ],
  "stream": false
}
```

### Response Ollama

```json
{
  "message": {
    "role": "assistant",
    "content": "..."
  }
}
```

---

## Mapeamento de erros HTTP

| Exceção interna | HTTP | Mensagem ao usuário |
|-----------------|------|---------------------|
| `OllamaOfflineError` | 503 | Ollama não está rodando. Execute: ollama serve |
| `OllamaTimeoutError` | 504 | Tempo esgotado aguardando resposta do modelo |
| Modelo não encontrado | 200 (health) / 503 (generate) | ollama pull gemma4:e2b |
| `PdfUnavailableError` | 501 | WeasyPrint não instalado |
| Validação Pydantic | 422 | Detalhe do campo inválido |

---

## Variáveis de ambiente

| Variável | Default | Usado em |
|----------|---------|----------|
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | OllamaClient |
| `OLLAMA_MODEL` | `gemma4:e2b` | OllamaClient |
| `OLLAMA_TIMEOUT` | `120` | httpx timeout (segundos) |
| `LLM_MAX_CONTEXT_TOKENS` | `2000` | Truncagem de histórico |

Ver `.env.example` na raiz do projeto.
