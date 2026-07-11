<script setup lang="ts">
import UiSlider from "./ui/UiSlider.vue";
import type { StateUpdate } from "../types/simulation";

defineProps<{ state: StateUpdate | null }>();
const emit = defineEmits<{ setParam: [key: string, value: number] }>();

type ParamKey = keyof Omit<StateUpdate["params"], "param_ranges">;

const paramLabels: Record<ParamKey, string> = {
  mutation: "Taxa de mutação",
  priority_weight: "Peso da prioridade",
  vehicle_count: "Veículos",
  capacity: "Capacidade",
  transit_count: "Nós de trânsito",
};

function paramValue(state: StateUpdate, key: ParamKey): number {
  return state.params[key];
}

function formatValue(state: StateUpdate, key: ParamKey): string {
  const value = paramValue(state, key);
  if (key === "mutation") return `${Math.round(value * 100)}%`;
  return String(value);
}
</script>

<template>
  <section v-if="state">
    <h3 class="section-title">Parâmetros</h3>
    <UiSlider
      v-for="(label, key) in paramLabels"
      :key="key"
      :label="label"
      :model-value="paramValue(state, key)"
      :min="state.params.param_ranges[key][0]"
      :max="state.params.param_ranges[key][1]"
      :step="key === 'mutation' ? 0.01 : 1"
      :format="() => formatValue(state, key)"
      @update:model-value="emit('setParam', key, $event)"
    />
  </section>
</template>
