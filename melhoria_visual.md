# Prompt — Criar uma versão Web do Simulador VRP Hospitalar preservando integralmente o núcleo da aplicação

## Objetivo

Desejo adicionar uma **nova interface Web** ao projeto existente, mantendo **100% da aplicação atual em Python + Pygame funcionando exatamente como está**.

A versão desktop continuará sendo a principal referência do projeto.

A versão Web será uma **segunda interface (frontend alternativo)** para o mesmo simulador, permitindo uma experiência muito mais agradável visualmente, responsiva e preparada para futuras evoluções.

**O core do sistema NÃO deve ser reescrito.**

---

# Regra mais importante

## O Algoritmo Genético é intocável.

Não alterar:

* representação genética
* cromossomos
* população
* seleção
* crossover
* mutação
* elitismo
* cálculo de fitness
* cálculo de distância
* penalidades
* capacidade dos veículos
* divisão em viagens
* prioridade das entregas
* lógica do depósito
* lógica dos bloqueios
* lógica dos nós de trânsito
* geração das rotas
* execução da simulação

Toda a lógica existente deve permanecer exatamente igual.

A interface Web deverá apenas consumir e apresentar as informações produzidas pelo algoritmo existente.

Caso seja necessário adaptar algo, criar apenas uma camada de comunicação (API ou adaptador), nunca alterar o núcleo do simulador.

---

# Compatibilidade obrigatória

O projeto deverá possuir dois modos de execução.

## Modo Desktop

Executa exatamente como hoje.

```
python main.py
```

Interface Pygame.

Sem alterações.

---

## Modo Web

Executa utilizando o mesmo algoritmo.

Exemplo:

```
python web.py
```

ou

```
python app.py --web
```

A interface deverá abrir no navegador.

---

# Arquitetura desejada

Separar claramente:

```
Core
│
├── Algoritmo Genético
├── VRP
├── Veículos
├── Entregas
├── Prioridades
├── Fitness
├── Simulação
└── Estado

Desktop
│
└── Interface Pygame

Web
│
├── Backend
└── Frontend
```

O Core não conhece nenhuma interface.

As interfaces apenas observam o estado do algoritmo.

---

# Objetivo da interface Web

Transformar o simulador em um dashboard profissional.

Inspirado em:

* Google Maps
* Grafana
* Power BI
* Uber Fleet
* Sistemas de monitoramento logístico

A aparência deve seguir exatamente o conceito visual da imagem de referência (dashboard moderno), com:

* muito espaço em branco
* cartões (cards)
* sombras suaves
* cantos arredondados
* excelente hierarquia visual
* foco principal no mapa

---

# Layout da aplicação

## Header

Barra superior fixa.

À esquerda:

```
VRP Hospitalar
Algoritmo Genético
```

No centro:

Cards de indicadores.

* Distância total
* Fitness atual
* Custo total
* Prioridade atendida
* Geração
* Tempo de execução

À direita:

* Nova execução
* Pausar
* Continuar
* Resetar
* Alternar tema

---

# Painel esquerdo

Dividido em seções recolhíveis.

---

## Informações gerais

Cards pequenos:

Veículos

```
3 / 3
```

Capacidade

```
58 un
```

Entregas

```
12 / 12
```

Viagens

```
5
```

Nós bloqueados

```
2
```

---

## Parâmetros

Todos os sliders atuais.

* Mutação
* Peso da prioridade
* Quantidade de veículos
* Capacidade
* Nós de trânsito

Cada slider deverá mostrar:

* valor atual
* faixa mínima
* faixa máxima

---

## Configurações

Switches modernos.

* Mostrar malha
* Mostrar nós
* Mostrar segunda rota
* Usar 2-opt
* Mostrar animação
* Mostrar direção das setas

---

## Rotas

Substituir o texto atual por cartões.

Exemplo:

---

Veículo 1

Cor Azul

Distância

18 km

Carga

46 / 58

Viagens

2

```
D → A → B → F → D

D → H → I → D
```

---

Veículo 2

Cor Verde

...

---

Cada cartão deverá utilizar a mesma cor da rota desenhada no mapa.

---

## Ações

Botões grandes.

🎲 Sortear posições

🏥 Cenário hospitalar

🔄 Reiniciar algoritmo

🧹 Limpar bloqueios

▶ Executar

⏸ Pausar

---

# Centro da tela

O mapa deve ocupar aproximadamente 70% da largura.

Este será o principal elemento da aplicação.

No mapa deverão aparecer:

* depósito
* entregas
* veículos
* rotas
* sentido das rotas
* nós de trânsito
* bloqueios

Tudo em tempo real.

---

# Elementos do mapa

O depósito deve ser o maior elemento visual.

As entregas devem utilizar um gradiente de prioridade.

Exemplo:

Prioridade baixa

Verde

↓

Amarelo

↓

Laranja

↓

Vermelho

Prioridade máxima

---

As rotas deverão utilizar cores diferentes por veículo.

Exemplo:

Veículo 1

Azul

Veículo 2

Verde

Veículo 3

Vermelho

Veículo 4

Roxo

Veículo 5

Laranja

---

As linhas deverão possuir:

* setas indicando direção
* animação suave
* espessura consistente

---

# Barra do mapa

Na parte superior direita.

Adicionar:

Filtro

Todos

Veículo 1

Veículo 2

Veículo 3

Checkbox

Mostrar malha

Mostrar nós

Mostrar segunda rota

Botão

Tela cheia

---

# Rodapé

Criar uma barra inferior semelhante a softwares profissionais.

Mostrar:

Fitness

Distância

Penalidade de prioridade

Penalidade de bloqueio

Tempo da geração

Tempo total

FPS

---

# Gráfico

Mover o gráfico para uma aba.

Criar três abas.

Resumo

Estatísticas

Histórico

O gráfico deverá possuir uma linha para cada veículo.

Com legenda.

Zoom.

Tooltip.

---

# Console

Não remover o console.

Criar uma aba chamada:

Logs

Mostrar:

* evolução do algoritmo
* geração
* fitness
* mutação
* crossover
* população
* eventos

Com opção de filtrar.

---

# Experiência do usuário

Adicionar:

Hover

Tooltips

Animações suaves

Transições

Ícones

Cards modernos

Espaçamento consistente

Tipografia moderna

Responsividade

---

# Funcionalidades existentes

Todas devem permanecer.

Sem exceção.

Inclusive:

* múltiplos veículos
* múltiplas viagens
* capacidade
* prioridade
* bloqueio manual
* cenário hospitalar
* sorteio de posições
* malha de ruas
* segunda melhor rota
* animação
* gráfico
* painel de rotas
* convergência
* cálculo de fitness
* filtro por veículo
* filtro por viagem

Nada pode ser removido.

---

# Comunicação entre Core e Web

A interface Web deve apenas consumir o estado atual do simulador.

Exemplo das informações disponíveis:

```
Estado atual

Geração

Fitness

Melhor indivíduo

Rotas

Veículos

Capacidade

Entregas

Prioridades

Posição dos veículos

Nós bloqueados

Distância

Histórico de fitness
```

A interface nunca recalcula nenhuma informação.

Todo cálculo permanece exclusivamente no Core.

---

# Escalabilidade

A arquitetura deve permitir adicionar futuramente:

* novos algoritmos (ACO, PSO, SA, etc.)
* múltiplos depósitos
* mapas reais (OpenStreetMap)
* simulação em tempo real
* WebSocket
* histórico das execuções
* salvar e carregar cenários
* comparação entre algoritmos
* exportação das rotas
* métricas avançadas

Sem necessidade de alterar o Core.

---

# Resultado esperado

O resultado deve ser uma aplicação híbrida:

* **Desktop (Pygame):** preservada integralmente, funcionando exatamente como hoje.
* **Web:** uma nova interface moderna, inspirada na referência visual do dashboard, consumindo o mesmo núcleo do sistema.

O algoritmo, as regras do VRP e toda a lógica de otimização devem permanecer **100% idênticos**, garantindo que ambas as interfaces exibam exatamente os mesmos resultados para um mesmo cenário. A evolução da interface deve ser exclusivamente visual e arquitetural, transformando o projeto em uma plataforma profissional para demonstração, estudo e futura expansão, sem comprometer a estabilidade ou o comportamento do simulador original.
