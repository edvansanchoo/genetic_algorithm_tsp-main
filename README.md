# Problema do Caixeiro Viajante com Algoritmo Genético

Simulador interativo em Python que resolve o **Problema do Caixeiro Viajante** (Traveling Salesman Problem) usando um **Algoritmo Genético**, com visualização em tempo real via Pygame.

## Executar

```bash
pip install -r requirements.txt
python main.py
```

## Estrutura do projeto

```
traveling_salesman_problem/
├── config/                  # Configurações da janela e tema visual
├── genetic_algorithm/       # População, fitness, crossover, mutação, seleção
├── obstacles/               # Modelos, colisão, penalidades e posicionamento
├── problem/                 # Geração de cidades e benchmark ATT48
├── visualization/           # Gráficos, mapa e widgets da interface
└── simulation/              # Estado da simulação e loop principal Pygame

demos/                       # Demonstrações isoladas de crossover e mutação
main.py                      # Ponto de entrada
```

## Controles

| Tecla / Ação | Efeito |
|---|---|
| **Q** ou **Esc** | Encerrar |
| **O** | Alternar penalidades de obstáculos |
| Slider de mutação | Ajustar taxa de mutação |
| Sortear posições | Reposicionar cidades e obstáculos |

## Dependências

- Python 3.9+
- Pygame
- Matplotlib
- NumPy

## Licença

[MIT License](LICENSE)
