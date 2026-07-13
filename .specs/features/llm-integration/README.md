# Feature: Integração LLM

Pacote de especificação para integração Ollama no simulador VRP hospitalar.

## Documentos

| Arquivo | Propósito |
|---------|-----------|
| [spec.md](spec.md) | Requisitos com IDs rastreáveis (REQ-LLM-XX), user stories P1/P2 |
| [context.md](context.md) | Decisões do brainstorming (Q1–Q4) e glossário |
| [api-contract.md](api-contract.md) | Contrato REST `/api/llm/*` + integração Ollama |
| [prompts.md](prompts.md) | System prompts completos, schema JSON, exemplos de chat |
| [ui-spec.md](ui-spec.md) | Wireframe, componentes Vue, estados visuais |

## Documentos relacionados (legado superpowers)

| Arquivo | Propósito |
|---------|-----------|
| [design.md](../../../docs/superpowers/specs/2026-07-13-llm-integration-design.md) | Visão arquitetural consolidada |
| [plan.md](../../../docs/superpowers/plans/2026-07-13-llm-integration.md) | Plano de implementação task-by-task |

## Status

- **Especificação:** Completa (2026-07-13)
- **Design:** Aprovado
- **Implementação:** Pendente

## Decisões-chave (resumo)

- Ollama local + `gemma4:e2b`
- Dashboard Web, aba Assistente, chat + export MD/PDF
- Histórico em memória na sessão; relatórios sob demanda
- Instruções geradas manualmente (não automático ao convergir)

## Requisitos

34 requisitos funcionais/NFR + 6 edge cases — ver [spec.md](spec.md#requirement-traceability).
