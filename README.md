# VRP Hospitalar com Algoritmo Genético

Simulador interativo em Python que resolve um **Problema de Roteamento de Veículos** (VRP — *Vehicle Routing Problem*) em cenário hospitalar, usando um **Algoritmo Genético** com visualização em tempo real.

O simulador distribui entregas entre múltiplos veículos respeitando **capacidade**, **prioridade** das entregas e uma **malha de ruas** com nós de trânsito e bloqueios. Duas interfaces compartilham o mesmo núcleo de simulação:

- **Desktop** — Pygame (`python main.py`)
- **Web** — dashboard Vue + FastAPI/WebSocket (`python web.py`)

## Executar

### Pré-requisitos

- Python 3.9+
- [Node.js](https://nodejs.org/) 18+ (apenas para desenvolvimento ou build do frontend Web)

### Modo Desktop

```bash
pip install -r requirements.txt
python main.py
```

### Modo Web

**Produção** (frontend empacotado servido pelo backend):

```bash
pip install -r requirements.txt
cd frontend
npm install
npm run build
cd ..
python web.py
```

Abra [http://127.0.0.1:8000](http://127.0.0.1:8000).

**Desenvolvimento** (hot-reload do frontend):

```bash
# Terminal 1 — backend
pip install -r requirements.txt
python web.py

# Terminal 2 — frontend
cd frontend
npm install
npm run dev
```

Abra [http://localhost:5173](http://localhost:5173). O WebSocket conecta diretamente em `ws://127.0.0.1:8000/ws`.

> Para rodar **somente** o backend Web (sem Pygame), use `pip install -r requirements-web.txt`.

## Estrutura do projeto

```
genetic_algorithm_tsp-main/
├── main.py                          ← entrada Desktop (Pygame)
├── web.py                           ← entrada Web (FastAPI)
├── requirements.txt
├── requirements-web.txt               ← dependências mínimas do modo Web
├── GUIA.md                          ← documentação didática em português
├── docs/
│   ├── ARQUITETURA.md               ← diagramas e camadas do sistema
│   └── API.md                       ← contrato WebSocket e REST LLM
│
├── traveling_salesman_problem/
│   ├── config/                      ← janela, algoritmo, tema visual
│   ├── genetic_algorithm/           ← população, fitness, crossover, mutação, seleção
│   ├── problem/                     ← entregas, malha de ruas, VRP, prioridades
│   ├── simulation/                  ← estado da simulação e loop Pygame
│   ├── visualization/               ← mapa, widgets, animação de rotas
│   ├── web/                         ← servidor, WebSocket, serialização de estado
│   └── llm/                         ← assistente Ollama (modo Web)
│
├── frontend/                        ← dashboard Vue 3 + TypeScript (Vite)
│   └── src/
│       ├── components/              ← painéis, mapa, gráficos, controles
│       ├── canvas/                  ← renderização do mapa no Canvas
│       └── composables/             ← WebSocket, tema, preferências
│
├── tests/                           ← testes automatizados (pytest)
└── demos/
    ├── demonstrate_crossover.py     ← operador de cruzamento
    ├── demonstrate_mutation.py      ← operador de mutação
    ├── demonstrate_fitness.py       ← cálculo de fitness e prioridade
    ├── demonstrate_priority.py      ← preset hospitalar
    ├── demonstrate_headless_generations.py  ← AG sem interface gráfica
    └── demonstrate_web_api.py       ← consumo da API Web
```

| Pacote | Responsabilidade |
|--------|------------------|
| `config` | Tamanho da janela, população, veículos, capacidade, cores e layout |
| `genetic_algorithm` | Lógica genética reutilizável (sem interface gráfica) |
| `problem` | Depósito, entregas, malha de ruas, prioridades e decodificação VRP |
| `simulation` | Estado mutável da simulação e loop principal |
| `visualization` | Sidebar, gráfico de convergência, mapa e animação de viagens |
| `web` | Serviço headless, comandos WebSocket e broadcast de estado |
| `frontend` | Interface Web responsiva consumindo o backend via WebSocket |

## Controles — Desktop

| Tecla / Ação | Efeito |
|---|---|
| **Q** ou **Esc** | Encerrar |
| **F** | Alternar tela cheia |
| Slider **Taxa de mutação** | Ajustar probabilidade de mutação em tempo real |
| Sliders **Veículos**, **Capacidade**, **Prioridade**, **Nós de trânsito** | Parâmetros do cenário VRP |
| **Sortear posições** | Reposicionar depósito, entregas e malha |
| **Cenário hospitalar** | Aplicar preset de prioridades hospitalares |
| **Reiniciar algoritmo** | Reiniciar população genética dos veículos |
| Clique no mapa | Alternar bloqueio de nó da malha |
| Painel de rotas | Focar veículo ou viagem específica |

## Interface Web

O dashboard replica os controles principais do Desktop e adiciona:

- Mapa interativo com zoom, pan e bloqueio de nós
- Gráfico de convergência e histórico de gerações
- Painel de rotas por veículo com animação de viagens
- Console de logs em tempo real
- Tema claro/escuro e preferências persistidas no navegador

Comandos são enviados via WebSocket (`/ws`); o backend executa a mesma lógica de simulação do modo headless.

## Assistente LLM (Ollama)

O dashboard Web inclui a aba **Assistente** para integração com LLM local:

- Gerar instruções para motoristas (por veículo ou todos)
- Relatórios diário/semanal e sugestões de melhoria
- Chat em linguagem natural sobre rotas e entregas
- Exportar conteúdo em Markdown ou PDF

### Requisitos adicionais

1. [Ollama](https://ollama.com/) instalado e em execução (`ollama serve`)
2. Modelo local: `ollama pull gemma4:e2b`
3. Dependências Python já incluídas em `requirements.txt` (`httpx`, `markdown`)
4. PDF opcional: `pip install -r requirements-llm.txt` (WeasyPrint)

Variáveis opcionais: ver `.env.example` (`OLLAMA_BASE_URL`, `OLLAMA_MODEL`, etc.).

## Dependências

### Python

| Pacote | Uso |
|--------|-----|
| [pygame-ce](https://github.com/pygame-community/pygame-ce) | Modo Desktop — janela, eventos e desenho |
| [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/) | Servidor Web |
| [websockets](https://websockets.readthedocs.io/) | Comunicação em tempo real |
| [Matplotlib](https://matplotlib.org/) | Gráfico de convergência |
| [NumPy](https://numpy.org/) | Pesos na seleção de pais |

### Frontend

| Pacote | Uso |
|--------|-----|
| [Vue 3](https://vuejs.org/) | Interface reativa |
| [Vite](https://vite.dev/) | Build e dev server |
| [Chart.js](https://www.chartjs.org/) | Gráfico de convergência |

## Testes automatizados

```bash
pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

Os testes cobrem operadores genéticos, fitness, comandos WebSocket, serialização de estado, serviço de simulação e endpoints LLM (com mocks — **não requer Ollama**).

## Demonstrações

Scripts executáveis que ilustram componentes isolados do sistema:

```bash
# Algoritmo Genético
python -m demos.demonstrate_crossover
python -m demos.demonstrate_mutation
python -m demos.demonstrate_fitness
python -m demos.demonstrate_priority
python -m demos.demonstrate_headless_generations

# API Web (requer python web.py em outro terminal)
python -m demos.demonstrate_web_api
```

## Documentação

| Documento | Conteúdo |
|-----------|----------|
| [GUIA.md](GUIA.md) | Explicação didática módulo a módulo |
| [docs/ARQUITETURA.md](docs/ARQUITETURA.md) | Camadas, diagramas e decisões de design |
| [docs/API.md](docs/API.md) | Contrato WebSocket (`/ws`) e REST (`/api/llm/*`) |
| `http://127.0.0.1:8000/docs` | Swagger UI (com backend rodando) |

## Licença

[MIT License](LICENSE)
