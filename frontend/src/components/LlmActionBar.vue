<script setup lang="ts">
import { ref } from "vue";
import UiButton from "./ui/UiButton.vue";
import type { GenerateType } from "../composables/useLlmApi";

defineProps<{
  loading: boolean;
  disabled: boolean;
  vehicleIds: number[];
}>();

const emit = defineEmits<{
  generate: [type: GenerateType, vehicleId?: number | null];
}>();

const selectedVehicle = ref<string>("all");

function onGenerateInstructions() {
  const vehicleId =
    selectedVehicle.value === "all" ? null : Number(selectedVehicle.value);
  emit("generate", "instructions", vehicleId);
}
</script>

<template>
  <section class="llm-action-bar">
    <h3 class="section-title">Ações</h3>
    <div class="llm-action-row">
      <label class="vehicle-select">
        Veículo
        <select v-model="selectedVehicle" :disabled="disabled || loading">
          <option value="all">Todos os veículos</option>
          <option v-for="id in vehicleIds" :key="id" :value="String(id)">
            Veículo {{ id + 1 }}
          </option>
        </select>
      </label>
      <UiButton
        variant="primary"
        :disabled="disabled || loading"
        @click="onGenerateInstructions"
      >
        {{ loading ? "Gerando..." : "Gerar instruções" }}
      </UiButton>
    </div>
    <div class="llm-action-row">
      <UiButton :disabled="disabled || loading" @click="emit('generate', 'daily_report')">
        Rel. Diário
      </UiButton>
      <UiButton :disabled="disabled || loading" @click="emit('generate', 'weekly_report')">
        Rel. Semanal
      </UiButton>
      <UiButton :disabled="disabled || loading" @click="emit('generate', 'improvements')">
        Sugestões
      </UiButton>
    </div>
  </section>
</template>

<style scoped>
.llm-action-bar {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.llm-action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.vehicle-select {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: var(--text-muted);
}

.vehicle-select select {
  padding: 6px 8px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border);
  background: var(--bg-panel);
  color: var(--text-primary);
  font-size: 13px;
}
</style>
