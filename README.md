# Problema do Caixeiro Viajante com Algoritmo Genético

Simulador interativo em Python que resolve o **Problema do Caixeiro Viajante** (TSP — *Traveling Salesman Problem*) usando um **Algoritmo Genético**, com visualização em tempo real via Pygame.

O mapa inclui **árvores** e **lagos** desenhados proceduralmente. O algoritmo pode ignorá-los (apenas distância) ou penalizar rotas que os cruzam.

## Executar

```bash
pip install -r requirements.txt
python main.py
```

## Estrutura do projeto

```
genetic_algorithm_tsp-main/
├── main.py                          ← ponto de entrada
├── requirements.txt
├── GUIA.md                          ← documentação completa em português
│
├── traveling_salesman_problem/
│   ├── config/                      ← janela, algoritmo, tema visual
│   ├── genetic_algorithm/           ← população, fitness, crossover, mutação, seleção
│   ├── obstacles/                   ← árvores, lagos, colisão, penalidades, posicionamento
│   ├── problem/                     ← geração de cidades, benchmark ATT48
│   ├── visualization/               ← gráficos, mapa, widgets, desenho de terreno
│   └── simulation/                  ← estado da simulação e loop Pygame
│
└── demos/
    ├── demonstrate_crossover.py     ← demonstração isolada do crossover
    └── demonstrate_mutation.py      ← demonstração isolada da mutação
```

| Pacote | Responsabilidade |
|--------|------------------|
| `config` | Tamanho da janela, população, quantidade de árvores/lagos, cores e layout |
| `genetic_algorithm` | Lógica genética reutilizável (sem interface gráfica) |
| `obstacles` | Modelos de árvore e lago, colisão e penalidades no fitness |
| `problem` | Posicionamento aleatório de cidades e dados do benchmark ATT48 |
| `visualization` | Sidebar, gráfico de convergência, mapa e desenho de terreno |
| `simulation` | Estado mutável da simulação e loop principal |

## Controles

| Tecla / Ação | Efeito |
|---|---|
| **Q** ou **Esc** | Encerrar |
| **O** | Alternar penalidades de árvores e lagos no algoritmo |
| Slider **Taxa de mutação** | Ajustar probabilidade de mutação em tempo real |
| Sliders **Árvores** / **Lagos** | Definir quantidade de cada elemento no mapa |
| **Sortear posições** | Reposicionar árvores, lagos e cidades |
| Toggles no painel de terreno | Exibir árvores/lagos e ajustar penalidade por tipo |

## Dependências

- Python 3.9+
- [Pygame](https://www.pygame.org/) — janela, eventos e desenho
- [Matplotlib](https://matplotlib.org/) — gráfico de convergência
- [NumPy](https://numpy.org/) — pesos na seleção de pais

## Demonstrações isoladas

```bash
python -m demos.demonstrate_crossover
python -m demos.demonstrate_mutation
```

## Documentação detalhada

Para explicação passo a passo, conceitos, fluxogramas e referência de código, consulte [GUIA.md](GUIA.md).

## Licença

[MIT License](LICENSE)
