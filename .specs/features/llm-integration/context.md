# Contexto: Integração LLM — Decisões do Brainstorming

**Data:** 2026-07-13  
**Feature:** `llm-integration`  
**Status:** Aprovado pelo usuário

Este documento registra as decisões tomadas durante o brainstorming (perguntas A/B/C/D) e o raciocínio por trás delas. Serve como referência quando houver ambiguidade na implementação.

---

## Origem da demanda

Requisito do Tech Challenge / tarefa acadêmica:

> Integração com LLMs para Geração de Instruções e Relatórios
> - Gerar instruções detalhadas para motoristas e equipes de entrega
> - Criar relatórios diários/semanais sobre eficiência de rotas
> - Sugerir melhorias no processo com base em padrões identificados
> - Implementar prompts eficientes
> - Permitir perguntas em linguagem natural sobre rotas e entregas

---

## Perguntas e respostas

### Q1: Qual provedor/modelo de LLM?

| Opção | Descrição |
|-------|-----------|
| A | OpenAI (GPT-4o) — cloud |
| B | Azure OpenAI — corporativo |
| **C ✓** | **Ollama local** — offline, sem custo por token |
| D | Outro / indefinido |

**Resposta do usuário:** C, utilizando `gemma4:e2b`

**Implicações:**
- Backend faz chamadas HTTP para `localhost:11434`
- Dados da simulação **não saem da máquina** (adequado a cenário hospitalar)
- Modelo pequeno (~2B) → prompts devem ser compactos e estruturados
- Health check deve validar se o modelo está instalado (`ollama pull`)
- Nota: tag `gemma4:e2b` pode ser customizada; validar com `ollama list`

---

### Q2: Onde a integração LLM deve ficar disponível?

| Opção | Descrição |
|-------|-----------|
| A | Apenas dashboard Web (recomendado) |
| B | Apenas backend REST (sem UI) |
| C | Web + Desktop Pygame |
| **D ✓** | **Web com chat embutido + exportação MD/PDF** |

**Resposta do usuário:** D

**Implicações:**
- Nova aba "Assistente" no `TabPanel.vue`
- Chat conversacional embutido no painel
- Botões de exportação Markdown e PDF
- Desktop Pygame permanece **fora do escopo**

---

### Q3: Como funcionam os relatórios periódicos?

| Opção | Descrição |
|-------|-----------|
| A | Snapshot da sessão atual apenas |
| B | Persistência local (SQLite/JSON) |
| C | Manual sob demanda (templates sem agendamento) |
| **D ✓** | **Histórico leve em memória na sessão + templates diário/semanal sob demanda** |

**Resposta do usuário:** D

**Implicações:**
- `SessionHistory` no backend registra snapshots quando fitness melhora
- Frontend já mantém `history` de gerações (até 200 entradas) — backend espelha para relatórios
- "Relatório diário" = estado atual + últimas melhorias da sessão
- "Relatório semanal" = agregação de **todos** os snapshots da sessão (não é calendário real)
- Sem banco de dados na v1
- Ao recarregar a página, histórico de sessão reinicia

---

### Q4: Quando gerar instruções para motoristas?

| Opção | Descrição |
|-------|-----------|
| **A ✓** | **Sob demanda** — botão + dropdown de veículo |
| B | Automático ao estabilizar fitness |
| C | A + B combinados |

**Resposta do usuário:** A

**Implicações:**
- Nenhuma geração automática ao detectar convergência
- Usuário clica "Gerar instruções" explicitamente
- Dropdown permite: "Todos os veículos" ou veículo específico
- Botões desabilitados enquanto não há `plans` na simulação

---

## Abordagem arquitetural escolhida

Entre três opções apresentadas, o usuário aprovou **Abordagem A**:

- Pacote `traveling_salesman_problem/llm/` (cliente, contexto, prompts, histórico)
- Endpoints REST `/api/llm/*` no FastAPI
- WebSocket de simulação **inalterado**
- LLM **somente no backend**

Alternativas rejeitadas:
- B: tudo em `web/llm_service.py` (menos modular)
- C: frontend chama Ollama direto (CORS, contexto incompleto, segurança)

---

## Restrições implícitas do projeto

| Restrição | Origem |
|-----------|--------|
| Núcleo GA/VRP intocável | Convenção do repositório |
| Idioma português | Projeto e GUIA.md em PT |
| Sem commit até pedido explícito | Preferência do usuário |
| Testes sem Ollama no CI | Praticidade de CI/CD |
| CSS puro + tokens existentes | Padrão do frontend Web |

---

## Personas de uso

### Coordenador de logística hospitalar
- Pausa a simulação quando fitness estabiliza
- Gera instruções para repassar à equipe de entrega
- Exporta relatório diário para documentação

### Operador / analista
- Explora cenários (shuffle, bloqueios, preset hospitalar)
- Pede sugestões de melhoria à LLM
- Usa chat para perguntas ad hoc ("qual veículo atende mais críticos?")

### Desenvolvedor / avaliador
- Verifica integração com Ollama local
- Roda testes pytest sem dependência externa
- Consulta health endpoint

---

## Glossário

| Termo | Significado nesta feature |
|-------|---------------------------|
| Snapshot | Registro pontual de métricas quando fitness melhora |
| Sessão | Período entre `python web.py` iniciado e encerrado (ou reload da página no frontend) |
| Relatório diário | Template de prompt + dados atuais + melhorias recentes da sessão |
| Relatório semanal | Template de prompt + agregação de todos os snapshots da sessão |
| Contexto | JSON compacto com rotas, entregas, métricas e tendência enviado à LLM |
| Assistente | Aba do dashboard Web que concentra LLM, chat e exportação |
