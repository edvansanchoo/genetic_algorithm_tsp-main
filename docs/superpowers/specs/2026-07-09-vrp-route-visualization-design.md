# Design: Clareza visual das rotas VRP (ida/volta ao depósito)

**Data:** 2026-07-09  
**Status:** Aprovado (brainstorming) — aguardando review do arquivo  
**Branch:** `feature/road-network-blocked-nodes`  
**Commits:** nenhum até pedido explícito do usuário

**Contexto:** O decoder VRP já gera viagens `Depósito → … → Depósito`, mas a UI atual (linha colorida + painel sem `D`) não deixa o retorno óbvio. Esta especificação cobre só melhorias de **visualização/apresentação**.

**Depende de:** Camada 2 VRP (`docs/superpowers/specs/2026-07-09-vrp-layer2-design.md`).

---

## 1. Objetivo

Tornar legível, na demo, que cada viagem **sai e volta ao depósito**, incluindo múltiplas viagens por capacidade.

**Escopo C (completo):**

1. Painel de rotas `D → … → D` com carga  
2. Setas na polyline (reforço no retorno ao D)  
3. Depósito maior / mais visível  
4. Filtro `Todos | V1 | V2 | …`  
5. Viagens extras com traço/opacidade distintos  
6. Animação do cursor **somente** no veículo filtrado  
7. Toggle da malha (arestas; trânsito segue o mesmo toggle)

**Fora de escopo:** mudanças em decoder, fitness, atribuição, GA, autonomia.

---

## 2. Decisões validadas

| Tópico | Decisão |
|--------|---------|
| Escopo | C — pacote completo |
| Animação | B — só com veículo filtrado; em “Todos”, estático |
| Abordagem | 1 — estender UI atual (sem modo apresentação separado) |
| Fonte de dados | `DecodedVehiclePlan` / `best_plan` já existentes |
| Git | Sem commit até pedido |

---

## 3. Comportamento

### 3.1 Painel de rotas

Substituir/estender o painel de ordem para texto estruturado:

```text
Veículo 1
  Viagem 1: D → A → C → D  (9/10)
  Viagem 2: D → B → D      (4/10)
Veículo 2
  Viagem 1: D → E → F → D  (7/10)
```

- Sempre incluir `D` no início e no fim de cada viagem.  
- Carga = soma das `quantity` das paradas de entrega da viagem / capacidade atual.  
- Com filtro ativo, listar só o veículo focado.

### 3.2 Filtro de veículo

- Estado: `focus_vehicle_id: Optional[int]` (`None` = Todos).  
- Controles na sidebar (botões ou seletor cíclico): `Todos`, `V1`, …  
- **Todos:** desenha todos os veículos; sem animação.  
- **Vn:** destaca Vn; demais ocultos ou bem apagados; animação ligada.

### 3.3 Mapa — rotas e setas

- Polyline expandida na malha (como hoje).  
- Viagem índice 0: traço contínuo, espessura maior.  
- Viagens seguintes: tracejado e/ou alpha menor, mesma cor do veículo.  
- Setas ao longo da polyline; reforço visual no segmento que **termina no depósito**.

### 3.4 Depósito

- Marcador maior que o atual, label “Depósito” (ou “D” grande + legenda).  
- Sempre desenhado por cima das rotas.

### 3.5 Toggle malha

- `show_mesh: bool` (default sugerido: `True`, ou `False` se a demo estiver poluída — default **True**, usuário desliga).  
- Off: não desenha arestas da malha; nós de trânsito seguem o mesmo flag (bloqueados e entregas permanecem).

### 3.6 Animação

- Ativa só se `focus_vehicle_id is not None`.  
- Polyline de animação = concatenação das viagens do `best_plan` (cada viagem já D…D).  
- Progresso ao longo do comprimento acumulado; ao fim, reinicia.  
- Reset de progresso ao: mudar filtro, sortear, rebuild, ou trocar `best_plan` de forma relevante.  
- Velocidade: constante no código no MVP (ex. pixels/segundo ou fração por frame); slider opcional = YAGNI.

---

## 4. Arquivos impactados (estimado)

| Arquivo | Mudança |
|---------|---------|
| `visualization/map_renderer.py` | Depósito, setas, traços por viagem, cursor, filtro/malha |
| `visualization/application_layout.py` (+ helper) | Formatação do painel `D → … → D` |
| `simulation/pygame_application.py` | Controles, loop de `t`, ordem de desenho |
| `simulation/simulation_state.py` | `focus_vehicle_id`, `show_mesh` |
| `config/visual_theme.py` | Tokens visuais do depósito/setas |
| Testes unitários do formatador / polyline de animação | |

Decoder/GA **não** mudam.

---

## 5. Testes mínimos

1. Formatador de viagem: string começa e termina com `D` (ou equivalente).  
2. Polyline de animação: primeiro e último ponto = coordenada do depósito.  
3. Com filtro V0, rotas “ativas” contêm só o plano do veículo 0.  
4. Manual: `python main.py` — painel mostra retorno; seta no D; com V1 selecionado o cursor sai e volta.

---

## 6. Critério de pronto

Na demonstração, sem abrir o código, fica claro que:

- cada viagem parte do depósito e retorna a ele;  
- capacidade pode gerar várias viagens do mesmo veículo;  
- o filtro + animação permitem acompanhar um veículo isolado.

---

## 7. Fora de escopo

- Play/Pause multi-veículo simultâneo  
- Modo “Apresentação” em tela separada  
- Alterar algoritmo VRP  
- Camada 3 (autonomia)
