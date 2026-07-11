Segue um prompt detalhado que você pode utilizar em outra IA (Lovable, Bolt, Cursor, Claude, GPT, etc.) para refatorar a interface mantendo todas as funcionalidades atuais, mas deixando-a com uma aparência moderna e focada na experiência do usuário.

---

# Prompt

Quero redesenhar completamente a interface do meu simulador de VRP Hospitalar (Vehicle Routing Problem) desenvolvido em Python + Pygame.

**IMPORTANTE:** Não quero alterar nenhuma regra do algoritmo nem remover funcionalidades. O objetivo é apenas reorganizar a interface para ficar mais moderna, limpa e agradável visualmente, semelhante a dashboards profissionais.

## Sobre o projeto

O sistema é um simulador educacional em tempo real onde um Algoritmo Genético resolve um problema de roteirização de veículos.

O cenário representa entregas hospitalares.

Os veículos:

* saem do depósito
* visitam entregas
* respeitam capacidade
* podem fazer múltiplas viagens
* retornam ao depósito

O algoritmo otimiza:

* distância total
* prioridade das entregas
* capacidade dos veículos
* penalidades por bloqueios
* fitness

Tudo acontece em tempo real enquanto o usuário acompanha a evolução.

---

# Objetivo do redesign

A interface atual está muito carregada visualmente.

Quero uma aparência semelhante a sistemas profissionais como:

* Power BI
* Grafana
* Google Maps
* dashboards logísticos
* softwares de gestão de frota

Com bastante espaço em branco, cantos arredondados, sombras leves e boa hierarquia visual.

---

# Layout desejado

## Barra superior (Header)

Criar uma barra horizontal contendo:

Título

VRP Hospitalar • Algoritmo Genético

Ao lado colocar cartões pequenos com:

* Distância total
* Fitness atual
* Custo total
* Prioridade atendida (%)
* Geração atual
* Status do algoritmo (Executando / Pausado)

Na extrema direita:

* botão Nova Execução
* botão Pausar
* botão Tema Claro/Escuro

---

## Painel esquerdo

Transformar em um painel organizado por seções recolhíveis.

### Seção 1 — Informações gerais

Mostrar cartões:

Veículos

3 / 3

Capacidade

58 un

Entregas

12 / 12

Viagens

5

---

### Seção 2 — Parâmetros

Colocar todos os sliders dentro desta seção.

Exemplo:

Taxa de mutação

Peso da prioridade

Número de veículos

Capacidade

Nós de trânsito

Cada slider deve mostrar o valor atual ao lado.

Adicionar tooltip explicando cada parâmetro.

---

### Seção 3 — Configurações

Switches modernos para:

* Mostrar malha de ruas
* Usar 2-opt
* Mostrar segunda melhor rota
* Mostrar nós de trânsito
* Mostrar animação

---

### Seção 4 — Rotas

Em vez de um texto longo, criar cartões para cada veículo.

Exemplo:

Veículo 1

Cor azul

Distância

18 km

Carga

46 / 58

Viagens

2

Logo abaixo:

D → A → F → G → D

D → C → H → D

Mesmo padrão para todos os veículos.

Cada cartão usa a cor da rota correspondente.

---

### Seção 5 — Ações

Botões grandes:

🎲 Sortear cenário

🏥 Cenário hospitalar

🔄 Reiniciar algoritmo

🧹 Limpar bloqueios

---

## Centro da tela

Mapa ocupando aproximadamente 70% da largura.

Esse deve ser o foco principal.

O mapa deve ter:

rotas coloridas

setas discretas indicando direção

depósito bem destacado

entregas coloridas conforme prioridade

nós de trânsito menores

linhas suaves

Legenda pequena e discreta no canto.

---

## Barra superior do mapa

Adicionar controles:

Filtro:

Todos os veículos

Veículo 1

Veículo 2

Veículo 3

Checkbox:

Mostrar malha

Mostrar nós

Mostrar segunda rota

Botão:

Tela cheia

---

## Rodapé

Criar uma barra inferior mostrando:

Fitness

4869

Distância

48,69 km

Penalidade prioridade

156

Penalidade bloqueios

0

Tempo da geração

0,08 s

---

# Gráfico

Mover o gráfico de convergência para dentro do painel esquerdo.

Colocar em uma aba chamada:

Resumo

Ao lado criar outras abas:

Resumo

Estatísticas

Histórico

No gráfico:

cada veículo possui uma cor diferente

linha mais fina

grade discreta

fundo branco

---

# Paleta de cores

Fundo:

cinza muito claro

Painéis:

branco

Sombras suaves

Bordas arredondadas

Azul:

veículo 1

Verde:

veículo 2

Vermelho:

veículo 3

Prioridade:

verde → amarelo → laranja → vermelho

Nunca utilizar cores muito saturadas.

---

# Tipografia

Fonte moderna.

Exemplo:

Inter

Roboto

Segoe UI

Títulos maiores.

Valores em destaque.

Textos secundários menores.

---

# Melhorias de UX

Adicionar:

hover nos botões

animações suaves

tooltips

ícones

cards com bordas arredondadas

espaçamento consistente

alinhamentos perfeitos

boa responsividade para resoluções Full HD.

---

# Organização visual

O usuário deve conseguir entender em poucos segundos:

* Quantos veículos existem.
* Quantas entregas existem.
* Qual o fitness atual.
* Qual a distância total.
* Como cada veículo está roteirizado.
* Qual rota pertence a cada veículo.
* Qual veículo está sendo visualizado.
* Em qual geração o algoritmo está.
* Se o algoritmo ainda está evoluindo.

Sem precisar procurar essas informações.

---

# Funcionalidades que DEVEM permanecer

Manter exatamente todas as funcionalidades existentes:

* Algoritmo Genético em tempo real.
* Múltiplos veículos.
* Múltiplas viagens.
* Capacidade por veículo.
* Prioridade das entregas.
* Bloqueio manual de nós.
* Malha de ruas.
* Segunda melhor rota.
* Filtro por veículo.
* Animação das rotas.
* Gráfico de convergência.
* Painel de rotas.
* Cenário hospitalar.
* Sorteio de posições.
* Controle por sliders.

Nenhuma funcionalidade deve ser removida.

Apenas reorganizada.

---

# Resultado esperado

A interface deve transmitir a sensação de um software profissional de otimização logística, mantendo o caráter educacional do simulador. O mapa deve ser o elemento central da aplicação, enquanto as informações de configuração, métricas e controle ficam organizadas em painéis laterais e superiores, com excelente hierarquia visual, leitura rápida e baixo nível de poluição visual. O usuário deve conseguir acompanhar facilmente a evolução do Algoritmo Genético, compreender o desempenho da solução e inspecionar as rotas de cada veículo sem dificuldade.
