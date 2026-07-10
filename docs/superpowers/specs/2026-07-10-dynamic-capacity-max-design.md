# Design: Capacidade máxima dinâmica (soma das demandas)

**Data:** 2026-07-10  
**Status:** Aprovado (brainstorming) — aguardando review do arquivo  
**Branch:** `feature/road-network-blocked-nodes`

**Contexto:** O slider de capacidade usa `maximum_capacity = 30` fixo. Com 12 entregas e demanda 1–12, a soma total pode chegar a 144 — impossibilitando configurar capacidade suficiente para uma única viagem. O usuário quer que o máximo do controlador seja a soma de todas as demandas do cenário atual.

---

## 1. Objetivo

- Definir **máximo do slider Capacidade** = `sum(delivery.demand)` do cenário ativo.
- Permitir capacidade = soma total → com 1 veículo, decoder produz **uma viagem** com todas as entregas.
- Quando a soma diminui (regenerar cenário), **clamp automático** se valor atual > novo máximo.

**Fora de escopo:** auto-ajuste de veículos; label “máx: X”; mudar `initial_capacity`; alterações no decoder ou atribuição greedy.

---

## 2. Decisões validadas

| Tópico | Decisão |
|--------|---------|
| Fórmula do máximo | `max(minimum_capacity, sum(demands))` |
| Mínimo do slider | `minimum_capacity = 1` (inalterado) |
| Valor inicial | `initial_capacity = 10` (inalterado) |
| Regenerar cenário | Atualiza máximo; clamp se valor > máximo |
| `maximum_capacity` em settings | **Removido** |
| Decoder / GA / atribuição | Sem mudança |

---

## 3. Comportamento

### 3.1 Sincronização

Após `rebuild_scenario()` (entregas definidas):

```text
total = sum(point.demand for point in deliveries)
slider.maximum_value = max(1, total)
if slider.integer_value > slider.maximum_value:
    slider.value = slider.maximum_value
```

### 3.2 Viagem única

| Config | Resultado |
|--------|-----------|
| 1 veículo + capacidade = soma total | Uma viagem com todas as entregas |
| N veículos + capacidade = soma total | Cada veículo: uma viagem com sua carga atribuída |
| Capacidade < carga do veículo | Múltiplas viagens (comportamento atual) |

### 3.3 Widget na criação

`IntegerSlider` criado com `maximum_value` provisório (`initial_capacity`); primeiro `rebuild_scenario` aplica o máximo real.

---

## 4. Componentes

| Arquivo | Mudança |
|---------|---------|
| `problem/vrp_models.py` ou `vrp_assignment.py` | `total_delivery_demand(deliveries)` |
| `simulation/simulation_state.py` | `_sync_capacity_slider_bounds()`; chamada em `rebuild_scenario` |
| `config/application_settings.py` | Remover `maximum_capacity` |
| `tests/test_capacity_slider.py` (novo) | Testes de soma e clamp |

**Sem mudança:** `vrp_decoder.py`, `vehicle_genetic.py`, `vrp_assignment.py` (lógica), `pygame_application.py`.

---

## 5. Testes

1. `total_delivery_demand` retorna soma correta.
2. Após rebuild simulado, `maximum_value == total_demand`.
3. Valor 80 com novo máximo 50 → clamp para 50.
4. Valor 10 com novo máximo 100 → permanece 10.

---

## 6. Critérios de aceite

- [ ] Slider permite capacidade até soma de todas as demandas.
- [ ] Regenerar cenário atualiza o máximo.
- [ ] Valor atual > novo máximo é reduzido automaticamente.
- [ ] `maximum_capacity` removido de `ApplicationSettings`.
- [ ] Testes novos passam; regressão VRP intacta.
