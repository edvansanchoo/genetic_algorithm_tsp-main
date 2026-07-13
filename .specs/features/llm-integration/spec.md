# Especificação: Integração LLM — Instruções, Relatórios e Chat

**Feature ID:** `llm-integration`  
**Data:** 2026-07-13  
**Status:** Especificado — pronto para implementação  
**Design:** [`docs/superpowers/specs/2026-07-13-llm-integration-design.md`](../../../docs/superpowers/specs/2026-07-13-llm-integration-design.md)  
**Plano:** [`docs/superpowers/plans/2026-07-13-llm-integration.md`](../../../docs/superpowers/plans/2026-07-13-llm-integration.md)  
**Contexto:** [`.specs/features/llm-integration/context.md`](context.md)

---

## Problem Statement

O simulador VRP hospitalar otimiza rotas e exibe métricas em tempo real, mas não traduz esses resultados em **orientações operacionais** para equipes de entrega nem permite **consultas em linguagem natural** sobre o cenário. Coordenadores precisam manualmente interpretar mapas, painéis de rotas e gráficos de convergência — processo lento e sujeito a erro, especialmente em cenários com múltiplos veículos, prioridades hospitalares e nós bloqueados.

Esta feature fecha essa lacuna usando uma LLM local (Ollama) que consome o estado da simulação e produz instruções, relatórios e respostas contextualizadas — sem enviar dados para a nuvem.

---

## Goals

- [ ] Coordenador gera instruções de entrega por veículo em **< 2 minutos** (incluindo latência do modelo local)
- [ ] Relatórios diário e semanal produzidos sob demanda com métricas reais da simulação
- [ ] Chat responde perguntas sobre rotas usando **apenas** dados do contexto atual
- [ ] Simulação Web continua funcionando normalmente com Ollama offline
- [ ] 100% dos testes automatizados passam sem Ollama instalado

---

## Out of Scope

| Feature | Motivo |
|---------|--------|
| Integração Desktop Pygame | Escopo limitado ao dashboard Web (decisão Q2-D) |
| Persistência em banco de dados | v1 usa memória de sessão (decisão Q3-D) |
| Relatórios por calendário real (seg–dom) | "Semanal" = agregação da sessão, não semana civil |
| Streaming de respostas LLM | v2 — resposta completa na v1 |
| Geração automática ao estabilizar fitness | Decisão Q4-A — apenas sob demanda |
| Agendamento/cron de relatórios | Fora do escopo acadêmico |
| Fine-tuning ou treinamento de modelo | Usa modelo pré-treinado via Ollama |
| Multi-idioma | Apenas português brasileiro |
| Integração OpenAI/Azure | Decisão Q1-C — Ollama local |

---

## User Stories

### P1: Instruções para motoristas ⭐ MVP

**User Story:** Como coordenador de logística hospitalar, quero gerar instruções passo a passo para motoristas com base nas rotas otimizadas, para repassar à equipe de entrega sem interpretar manualmente o mapa.

**Why P1:** Requisito central da tarefa; entrega valor imediato e demonstrável.

**Acceptance Criteria:**

1. WHEN o usuário clica "Gerar instruções" com veículo "Todos" THEN o sistema SHALL chamar a LLM e exibir Markdown com seções por veículo e viagem. `(REQ-LLM-01)`
2. WHEN o usuário seleciona um veículo específico no dropdown THEN o sistema SHALL gerar instruções apenas para esse veículo. `(REQ-LLM-02)`
3. WHEN `state.plans` está vazio THEN os botões de geração SHALL permanecer desabilitados. `(REQ-LLM-03)`
4. WHEN a LLM responde THEN o conteúdo SHALL mencionar paradas na ordem da rota (ids de entrega ou "D" para depósito). `(REQ-LLM-04)`

**Independent Test:** Iniciar simulação Web, aguardar rotas, clicar "Gerar instruções", verificar Markdown com passos por veículo.

---

### P1: Relatórios diário e semanal ⭐ MVP

**User Story:** Como analista operacional, quero relatórios sobre eficiência de rotas e uso de recursos, para documentar o desempenho da sessão de simulação.

**Why P1:** Segundo requisito explícito da tarefa.

**Acceptance Criteria:**

1. WHEN o usuário clica "Relatório diário" THEN o sistema SHALL incluir fitness, distância, % prioridade atendida e destaques da sessão atual. `(REQ-LLM-05)`
2. WHEN o usuário clica "Relatório semanal" THEN o sistema SHALL agregar todos os snapshots registrados na sessão (count, melhor/pior fitness, médias). `(REQ-LLM-06)`
3. WHEN o fitness melhora em uma geração THEN o `SessionHistory` SHALL registrar um novo snapshot automaticamente. `(REQ-LLM-07)`
4. WHEN não há snapshots anteriores THEN o relatório semanal SHALL indicar dados limitados sem erro fatal. `(REQ-LLM-08)`

**Independent Test:** Rodar simulação por várias gerações, gerar ambos relatórios, verificar métricas coerentes com o painel lateral.

---

### P1: Chat em linguagem natural ⭐ MVP

**User Story:** Como operador, quero fazer perguntas em português sobre rotas e entregas, para obter respostas rápidas sem navegar por múltiplas abas.

**Why P1:** Terceiro requisito explícito da tarefa.

**Acceptance Criteria:**

1. WHEN o usuário envia uma pergunta no chat THEN o sistema SHALL incluir o contexto atual da simulação na chamada à LLM. `(REQ-LLM-09)`
2. WHEN a pergunta é respondida THEN o histórico local SHALL exibir mensagens user/assistant em ordem. `(REQ-LLM-10)`
3. WHEN a informação não está no contexto THEN a LLM SHALL indicar que não sabe (via instrução de system prompt). `(REQ-LLM-11)`
4. WHEN múltiplas perguntas são feitas na mesma sessão THEN o histórico de chat SHALL ser enviado para manter coerência conversacional. `(REQ-LLM-12)`

**Independent Test:** Perguntar "quantos veículos estão ativos?" e "qual entrega tem maior prioridade?" — respostas coerentes com o estado.

---

### P2: Sugestões de melhoria

**User Story:** Como gestor de processos, quero sugestões de melhoria baseadas nos padrões da simulação, para iterar parâmetros e cenários.

**Why P2:** Requisito da tarefa; complementa relatórios mas não bloqueia MVP.

**Acceptance Criteria:**

1. WHEN o usuário clica "Sugestões" THEN o sistema SHALL analisar métricas, bloqueios, distribuição de carga e tendência de convergência. `(REQ-LLM-13)`
2. WHEN a resposta é gerada THEN o formato SHALL ser lista de sugestões acionáveis em Markdown. `(REQ-LLM-14)`

**Independent Test:** Clicar "Sugestões" com cenário com nós bloqueados — resposta menciona bloqueios ou redistribuição.

---

### P2: Exportação MD/PDF

**User Story:** Como coordenador, quero exportar o conteúdo gerado para compartilhar com a equipe ou arquivar.

**Why P2:** Decisão Q2-D; importante para entrega mas não bloqueia geração.

**Acceptance Criteria:**

1. WHEN o usuário clica "Exportar MD" com conteúdo na área de resposta THEN o browser SHALL baixar arquivo `.md`. `(REQ-LLM-15)`
2. WHEN o usuário clica "Exportar PDF" e WeasyPrint está disponível THEN o browser SHALL baixar arquivo `.pdf`. `(REQ-LLM-16)`
3. WHEN WeasyPrint não está instalado THEN o sistema SHALL retornar HTTP 501 e o frontend SHALL oferecer fallback `window.print()`. `(REQ-LLM-17)`

**Independent Test:** Gerar instruções, exportar MD, abrir arquivo e verificar conteúdo.

---

### P2: Health check e resiliência

**User Story:** Como desenvolvedor/usuário, quero saber se o Ollama está disponível, para diagnosticar problemas sem quebrar a simulação.

**Why P2:** Operação confiável em ambiente local heterogêneo.

**Acceptance Criteria:**

1. WHEN a aba Assistente é aberta THEN o sistema SHALL chamar `GET /api/llm/health` e exibir status visual. `(REQ-LLM-18)`
2. WHEN Ollama está offline THEN a simulação WebSocket SHALL continuar funcionando normalmente. `(REQ-LLM-19)`
3. WHEN o modelo configurado não está instalado THEN o health check SHALL retornar `ok: false` com instrução `ollama pull`. `(REQ-LLM-20)`
4. WHEN a LLM excede timeout THEN o sistema SHALL retornar HTTP 504 e exibir mensagem amigável. `(REQ-LLM-21)`

**Independent Test:** Parar Ollama, abrir aba Assistente — badge vermelho, mapa ainda anima.

---

## Edge Cases

| Cenário | Comportamento esperado | Req |
|---------|------------------------|-----|
| Simulação pausada | Geração usa estado/plans do momento da pausa | REQ-LLM-22 |
| Shuffle de posições após snapshots | Novos snapshots refletem novo cenário; antigos permanecem no histórico da sessão | REQ-LLM-23 |
| Plano com fitness infinito (rota inválida) | Contexto inclui veículo; LLM pode alertar rota inválida | REQ-LLM-24 |
| Mensagem de chat vazia | API rejeita com validação (min_length=1) | REQ-LLM-25 |
| Contexto muito grande (>2000 tokens estimados) | Truncar histórico de chat antigo antes de enviar | REQ-LLM-26 |
| CORS em dev (5173 → 8000) | FastAPI permite origem do Vite dev server | REQ-LLM-27 |
| Reload da página | Chat history e lastOutput reiniciam; SessionHistory no backend persiste até reiniciar `web.py` | REQ-LLM-28 |

---

## Non-Functional Requirements

| ID | Requisito |
|----|-----------|
| REQ-LLM-NFR-01 | Latência aceitável: até 120s timeout configurável |
| REQ-LLM-NFR-02 | Nenhum dado enviado fora de `localhost` (Ollama local) |
| REQ-LLM-NFR-03 | Prompts em português brasileiro |
| REQ-LLM-NFR-04 | Testes unitários/integração sem Ollama real |
| REQ-LLM-NFR-05 | Não modificar módulos `genetic_algorithm/`, `problem/vrp_decoder.py`, fitness |
| REQ-LLM-NFR-06 | Aviso visível: "Verifique números críticos" (modelo 2B pode alucinar) |

---

## Requirement Traceability

| Requirement ID | Story | Fase | Status |
|----------------|-------|------|--------|
| REQ-LLM-01 | P1 Instruções | Design | Especificado |
| REQ-LLM-02 | P1 Instruções | Design | Especificado |
| REQ-LLM-03 | P1 Instruções | Design | Especificado |
| REQ-LLM-04 | P1 Instruções | Design | Especificado |
| REQ-LLM-05 | P1 Relatórios | Design | Especificado |
| REQ-LLM-06 | P1 Relatórios | Design | Especificado |
| REQ-LLM-07 | P1 Relatórios | Design | Especificado |
| REQ-LLM-08 | P1 Relatórios | Design | Especificado |
| REQ-LLM-09 | P1 Chat | Design | Especificado |
| REQ-LLM-10 | P1 Chat | Design | Especificado |
| REQ-LLM-11 | P1 Chat | Design | Especificado |
| REQ-LLM-12 | P1 Chat | Design | Especificado |
| REQ-LLM-13 | P2 Sugestões | Design | Especificado |
| REQ-LLM-14 | P2 Sugestões | Design | Especificado |
| REQ-LLM-15 | P2 Export | Design | Especificado |
| REQ-LLM-16 | P2 Export | Design | Especificado |
| REQ-LLM-17 | P2 Export | Design | Especificado |
| REQ-LLM-18 | P2 Health | Design | Especificado |
| REQ-LLM-19 | P2 Health | Design | Especificado |
| REQ-LLM-20 | P2 Health | Design | Especificado |
| REQ-LLM-21 | P2 Health | Design | Especificado |
| REQ-LLM-22–28 | Edge cases | Design | Especificado |
| REQ-LLM-NFR-01–06 | NFR | Design | Especificado |

**Coverage:** 34 requisitos, 0 sem mapeamento no plano de implementação.

---

## Success Criteria

- [ ] Demo completa: simular → gerar instruções → chat → exportar MD em < 5 minutos
- [ ] Zero regressão nos testes existentes do projeto
- [ ] 6+ arquivos de teste novos passando sem Ollama
- [ ] README documenta setup Ollama + aba Assistente
