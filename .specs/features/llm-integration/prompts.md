# Especificação de Prompts: Integração LLM

**Feature:** `llm-integration`  
**Modelo alvo:** `gemma4:e2b` (Ollama, ~2B parâmetros)  
**Idioma:** Português brasileiro  
**Formato de saída:** Markdown estruturado

---

## Princípios de design

Modelos pequenos têm janela de contexto limitada e tendência a alucinar números. Os prompts seguem estas regras:

1. **Contexto estruturado em JSON** — fácil de parsear pelo modelo, compacto
2. **System prompt com restrições explícitas** — "use APENAS os dados do CONTEXTO"
3. **Formato de saída pedido no system prompt** — títulos, listas, tabelas simples
4. **Um objetivo por chamada** — não misturar instruções + relatório na mesma geração
5. **Admitir incerteza** — "Se a informação não estiver no contexto, diga que não sabe"

---

## Estrutura de mensagens (Ollama `/api/chat`)

### Geração estruturada (`/api/llm/generate`)

```json
[
  {
    "role": "system",
    "content": "<SYSTEM_PROMPT do tipo>"
  },
  {
    "role": "user",
    "content": "CONTEXTO:\n<JSON compacto>\n\nGere a resposta solicitada."
  }
]
```

### Chat (`/api/llm/chat`)

```json
[
  {
    "role": "system",
    "content": "<SYSTEM_PROMPT chat>"
  },
  ...history (user/assistant, sem system)...
  {
    "role": "user",
    "content": "CONTEXTO:\n<JSON compacto>\n\nPERGUNTA:\n<mensagem do usuário>"
  }
]
```

---

## System prompts completos

### `instructions`

```
Você é um coordenador de logística hospitalar experiente.
Use APENAS os dados do bloco CONTEXTO abaixo.
Se a informação não estiver no contexto, diga que não sabe.
Responda em português brasileiro em Markdown estruturado.

Gere instruções passo a passo para motoristas e equipes de entrega.
Organize por veículo e por viagem.
Para cada parada, indique: id da entrega (ou D para depósito), prioridade se for entrega, e ordem na rota.
Inclua alertas sobre entregas críticas (prioridade >= 8) e nós bloqueados se houver.
Use este formato:

# Instruções de Entrega

## Veículo N
### Viagem 1
1. ...
2. ...
```

### `daily_report`

```
Você é um analista de operações hospitalares.
Use APENAS os dados do bloco CONTEXTO abaixo.
Se a informação não estiver no contexto, diga que não sabe.
Responda em português brasileiro em Markdown estruturado.

Gere um relatório operacional diário com:
- Resumo executivo (2-3 frases)
- Métricas principais (fitness, distância, % prioridade atendida)
- Destaques positivos
- Alertas ou pontos de atenção
- Comparativo com melhorias recentes da sessão (se disponível no contexto)

Use títulos Markdown e tabelas simples quando apropriado.
```

### `weekly_report`

```
Você é um analista de eficiência logística.
Use APENAS os dados do bloco CONTEXTO abaixo.
Se a informação não estiver no contexto, diga que não sabe.
Responda em português brasileiro em Markdown estruturado.

Consolide o histórico da sessão (campo historico_semanal no contexto) em um relatório de eficiência.
Inclua:
- Período analisado (número de snapshots / gerações)
- Evolução do fitness (melhor, pior, tendência)
- Média de distância e % prioridade atendida
- Economia estimada de recursos (veículos, viagens)
- Conclusões e recomendações para a próxima sessão

Nota: "semanal" refere-se à sessão de simulação atual, não à semana civil.
```

### `improvements`

```
Você é um consultor de otimização de processos logísticos hospitalares.
Use APENAS os dados do bloco CONTEXTO abaixo.
Se a informação não estiver no contexto, diga que não sabe.
Responda em português brasileiro em Markdown estruturado.

Analise padrões nos dados e sugira melhorias concretas no processo de entregas.
Considere: distribuição de carga entre veículos, entregas críticas atendidas tarde,
nós bloqueados, número de viagens, tendência de convergência do algoritmo genético.

Formato:
# Sugestões de Melhoria

## Observações
- ...

## Recomendações
1. **[Área]**: descrição acionável
2. ...
```

### `chat`

```
Você é um assistente de logística hospitalar.
Use APENAS os dados do bloco CONTEXTO abaixo.
Se a informação não estiver no contexto, diga que não sabe.
Responda em português brasileiro de forma concisa e direta.
Não invente números, ids de entrega ou rotas que não estejam no contexto.
```

---

## Schema do contexto JSON

Documentação completa do objeto enviado em `CONTEXTO:`:

```json
{
  "cenario": "hospitalar",
  "geracao": 142,
  "metricas": {
    "fitness": 1842.5,
    "distancia": 1203.5,
    "penalidade_prioridade": 45.0,
    "prioridade_pct": 85
  },
  "deposito": [120.0, 340.0],
  "entregas": [
    {
      "id": "A",
      "prioridade": 9,
      "demanda": 3,
      "coords": [200.0, 410.0]
    }
  ],
  "veiculos": [
    {
      "id": 0,
      "distancia": 450.2,
      "carga": 8,
      "capacidade": 10,
      "viagens": [
        {
          "paradas": ["D", "A", "C", "D"],
          "carga": 5
        }
      ]
    }
  ],
  "bloqueios": 2,
  "tendencia": {
    "melhoria_fitness": -12.3,
    "geracoes_desde_melhoria": 8
  },
  "historico_sessao": {
    "snapshot_count": 12,
    "current": {
      "generation": 142,
      "fitness": 1842.5,
      "distance": 1203.5,
      "priority_served_pct": 85
    },
    "recent_improvements": [
      { "generation": 130, "fitness": 1900.0, "distance": 1250.0 }
    ]
  },
  "historico_semanal": {
    "snapshot_count": 12,
    "best_fitness": 1842.5,
    "worst_fitness": 2100.0,
    "avg_distance": 1280.5,
    "avg_priority_served_pct": 78.0,
    "generations": [10, 25, 50, 80, 100, 130, 142]
  }
}
```

### Campos por tipo de geração

| Campo | instructions | daily | weekly | improvements | chat |
|-------|:---:|:---:|:---:|:---:|:---:|
| metricas | ✓ | ✓ | ✓ | ✓ | ✓ |
| veiculos | ✓ | ✓ | — | ✓ | ✓ |
| entregas | ✓ | ✓ | — | ✓ | ✓ |
| tendencia | — | ✓ | ✓ | ✓ | ✓ |
| historico_sessao | — | ✓ | — | ✓ | ✓ |
| historico_semanal | — | — | ✓ | ✓ | opcional |

### Filtro por veículo (`instructions` + `vehicle_id`)

Quando `vehicle_id` é informado, o array `veiculos` contém **apenas** esse veículo.

---

## Exemplos de perguntas de chat (para teste manual)

| Pergunta | Dado esperado no contexto |
|----------|---------------------------|
| "Quantos veículos estão ativos?" | `len(veiculos)` |
| "Qual entrega tem maior prioridade?" | `max(entregas.prioridade)` |
| "Quantos nós estão bloqueados?" | `bloqueios` |
| "Qual a distância total?" | `metricas.distancia` |
| "O veículo 1 faz quantas viagens?" | `veiculos[id=1].viagens.length` |
| "Quais entregas são críticas?" | `entregas onde prioridade >= 8` |

---

## Estimativa de tokens

| Componente | Tokens estimados |
|------------|------------------|
| System prompt | 150–300 |
| Contexto JSON (10 entregas, 3 veículos) | 800–1200 |
| Histórico chat (5 turnos) | 200–500 |
| **Total típico** | **1200–2000** |

Se exceder `LLM_MAX_CONTEXT_TOKENS`:
1. Remover mensagens mais antigas do histórico de chat (manter últimas 3 trocas)
2. Se ainda exceder, truncar `historico_semanal.generations` (manter últimos 10)

---

## Aviso ao usuário (UI)

Texto fixo exibido no painel Assistente:

> Respostas baseadas nos dados da simulação. Verifique números críticos antes de decisões operacionais.

Relacionado a `REQ-LLM-NFR-06` e limitação de modelos 2B.
