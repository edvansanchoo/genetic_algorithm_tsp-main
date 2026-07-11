<script setup lang="ts">
import { computed, ref } from "vue";
import type { StateUpdate } from "../types/simulation";

const props = defineProps<{ state: StateUpdate }>();
const filter = ref("all");

const filteredLogs = computed(() => {
  if (filter.value === "all") return props.state.logs;
  return props.state.logs.filter((entry) => entry.type === filter.value);
});
</script>

<template>
  <div>
    <label>
      Filtro
      <select v-model="filter">
        <option value="all">Todos</option>
        <option value="generation">Geração</option>
        <option value="param">Parâmetros</option>
        <option value="toggle">Toggles</option>
        <option value="action">Ações</option>
        <option value="blocked">Bloqueios</option>
        <option value="event">Eventos</option>
      </select>
    </label>
    <div class="log-console">
      <div v-for="(entry, index) in filteredLogs" :key="`${entry.ts}-${index}`" class="log-line">
        [{{ entry.type }}] {{ entry.message }}
      </div>
    </div>
  </div>
</template>
