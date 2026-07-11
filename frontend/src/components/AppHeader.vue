<script setup lang="ts">
import { useTheme } from "../composables/useTheme";
import UiIcon from "./ui/UiIcon.vue";
import UiMetricCard from "./ui/UiMetricCard.vue";
import UiButton from "./ui/UiButton.vue";
import type { StateUpdate } from "../types/simulation";

defineProps<{
  state: StateUpdate | null;
}>();

const emit = defineEmits<{
  pause: [];
  resume: [];
  restart: [];
}>();

const { theme, toggleTheme } = useTheme();
</script>

<template>
  <header class="header">
    <div class="header__brand">
      <UiIcon name="ambulance" :size="28" class="header__brand-icon" />
      <div>
        <div class="header__brand-title">VRP Hospitalar</div>
        <div class="header__brand-sub">Algoritmo Genético</div>
      </div>
    </div>

    <div class="header__metrics" v-if="state">
      <UiMetricCard
        label="Distância total"
        :value="state.metrics.distance.toFixed(2)"
        unit=" km"
      />
      <UiMetricCard
        label="Custo total"
        :value="Math.round(state.metrics.total_cost ?? state.metrics.fitness)"
      />
      <UiMetricCard
        label="Prioridade atendida"
        :value="state.metrics.priority_served_pct ?? 0"
        unit="%"
      />
    </div>

    <div class="header__actions">
      <UiButton variant="ghost" :icon="theme === 'dark' ? 'sun' : 'moon'" @click="toggleTheme">
        Tema
      </UiButton>
      <UiButton
        v-if="state?.running"
        variant="secondary"
        icon="pause"
        @click="emit('pause')"
      >
        Pausar
      </UiButton>
      <UiButton v-else variant="secondary" icon="play" @click="emit('resume')">
        Continuar
      </UiButton>
      <UiButton variant="primary" icon="reset" @click="emit('restart')">
        Nova execução
      </UiButton>
    </div>
  </header>
</template>
