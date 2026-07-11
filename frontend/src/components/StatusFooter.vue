<script setup lang="ts">
import type { StateUpdate } from "../types/simulation";

defineProps<{ state: StateUpdate | null }>();
</script>

<template>
  <footer class="footer" v-if="state">
    <div class="footer__left">
      <span class="footer__title">
        Algoritmo Genético
        <span
          class="status-dot"
          :class="state.running ? 'status-dot--running' : 'status-dot--paused'"
        />
        {{ state.running ? "Executando" : "Pausado" }}
      </span>
      <span class="footer__meta">
        Geração {{ state.generation }} · População {{ state.metrics.population_size }} ·
        Elite {{ state.display?.elite_pct ?? 10 }}%
      </span>
    </div>
    <div class="footer__right">
      Fitness: {{ state.metrics.fitness }} · Distância: {{ state.metrics.distance }} km ·
      Penal. prioridade: {{ state.metrics.priority_penalty }} ·
      Penal. bloqueio: {{ state.metrics.blocked_penalty }}
    </div>
  </footer>
</template>
