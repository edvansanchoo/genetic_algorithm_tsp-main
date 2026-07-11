<script setup lang="ts">
import UiSwitch from "./ui/UiSwitch.vue";
import { usePreferences } from "../composables/usePreferences";
import type { StateUpdate } from "../types/simulation";

defineProps<{ state: StateUpdate | null }>();
const emit = defineEmits<{ setToggle: [key: string, active: boolean] }>();

const { showRunnerUp } = usePreferences();
</script>

<template>
  <section v-if="state">
    <h3 class="section-title">Configurações</h3>
    <UiSwitch
      :model-value="state.toggles.two_opt"
      label="2-opt (melhoria local)"
      @update:model-value="emit('setToggle', 'two_opt', $event)"
    />
    <UiSwitch
      :model-value="state.toggles.show_mesh"
      label="Exibir malha de ruas"
      @update:model-value="emit('setToggle', 'show_mesh', $event)"
    />
    <UiSwitch
      v-model="showRunnerUp"
      label="Mostrar 2ª melhor rota"
    />
  </section>
</template>

<style scoped>
section :deep(.ui-switch) {
  margin-bottom: 10px;
}
</style>
