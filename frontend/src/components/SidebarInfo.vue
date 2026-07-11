<script setup lang="ts">
import UiIcon from "./ui/UiIcon.vue";
import type { StateUpdate } from "../types/simulation";

defineProps<{ state: StateUpdate | null }>();
</script>

<template>
  <section v-if="state">
    <h3 class="section-title">Resumo</h3>
    <div class="info-row">
      <div class="info-card">
        <UiIcon name="truck" :size="18" class="info-card__icon" />
        <span class="info-card__label">Veículos</span>
        <strong>{{ state.summary.vehicles_active }}/{{ state.summary.vehicles_total }}</strong>
      </div>
      <div class="info-card">
        <UiIcon name="box" :size="18" class="info-card__icon" />
        <span class="info-card__label">Capacidade</span>
        <strong>{{ state.summary.capacity_total }} un</strong>
      </div>
      <div class="info-card">
        <UiIcon name="pin" :size="18" class="info-card__icon" />
        <span class="info-card__label">Entregas</span>
        <strong>{{ state.summary.deliveries_done }}/{{ state.summary.deliveries_total }}</strong>
      </div>
    </div>
  </section>
</template>
