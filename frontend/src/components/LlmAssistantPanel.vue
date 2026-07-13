<script setup lang="ts">
import { computed, onMounted } from "vue";
import type { StateUpdate } from "../types/simulation";
import { useLlmApi, type GenerateType } from "../composables/useLlmApi";
import LlmActionBar from "./LlmActionBar.vue";
import LlmOutputViewer from "./LlmOutputViewer.vue";
import LlmChatBox from "./LlmChatBox.vue";
import UiButton from "./ui/UiButton.vue";

const props = defineProps<{ state: StateUpdate | null }>();

const {
  loading,
  error,
  lastOutput,
  chatHistory,
  ollamaStatus,
  health,
  generate,
  chat,
  exportReport,
} = useLlmApi();

const vehicleIds = computed(() =>
  props.state
    ? Object.keys(props.state.plans)
        .map(Number)
        .sort((a, b) => a - b)
    : [],
);
const hasPlans = computed(() => vehicleIds.value.length > 0);
const statusLabel = computed(() => {
  if (!ollamaStatus.value) return "Verificando...";
  return ollamaStatus.value.ok
    ? "Ollama conectado"
    : ollamaStatus.value.message ?? "Ollama indisponível";
});

onMounted(() => {
  void health();
});

async function onGenerate(type: GenerateType, vehicleId?: number | null) {
  try {
    await generate(type, vehicleId);
  } catch {
    // error ref already set
  }
}

async function onChat(message: string) {
  try {
    await chat(message);
  } catch {
    // error ref already set
  }
}

async function onExport(format: "md" | "pdf") {
  if (!lastOutput.value) return;
  try {
    await exportReport(lastOutput.value, format);
  } catch (exc) {
    error.value = exc instanceof Error ? exc.message : "Erro ao exportar";
  }
}
</script>

<template>
  <div class="llm-panel">
    <div class="llm-status" :class="{ 'llm-status--ok': ollamaStatus?.ok }">
      ● {{ statusLabel }}
    </div>

    <p v-if="ollamaStatus && !ollamaStatus.ok" class="llm-banner">
      Execute <code>ollama serve</code> e <code>ollama pull gemma4:e2b</code>
    </p>

    <p class="llm-disclaimer">
      Respostas baseadas nos dados da simulação. Verifique números críticos.
    </p>

    <LlmActionBar
      :loading="loading"
      :disabled="!hasPlans || !ollamaStatus?.ok"
      :vehicle-ids="vehicleIds"
      @generate="onGenerate"
    />

    <LlmOutputViewer :content="lastOutput" />

    <div class="llm-export-row">
      <UiButton :disabled="!lastOutput" @click="onExport('md')">Exportar MD</UiButton>
      <UiButton :disabled="!lastOutput" @click="onExport('pdf')">Exportar PDF</UiButton>
    </div>

    <p v-if="error" class="error-text">{{ error }}</p>

    <LlmChatBox
      :loading="loading"
      :history="chatHistory"
      @send="onChat"
    />
  </div>
</template>

<style scoped>
.llm-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
  height: 100%;
}

.llm-status {
  font-size: 12px;
  font-weight: 600;
  color: var(--danger);
}

.llm-status--ok {
  color: var(--success);
}

.llm-banner {
  margin: 0;
  padding: 8px 10px;
  background: var(--danger-soft);
  color: var(--danger);
  border-radius: var(--radius-md);
  font-size: 12px;
}

.llm-banner code {
  font-family: var(--font-mono);
  font-size: 11px;
}

.llm-disclaimer {
  margin: 0;
  font-size: 11px;
  font-style: italic;
  color: var(--text-muted);
}

.llm-export-row {
  display: flex;
  gap: 8px;
}

.error-text {
  margin: 0;
  color: var(--danger);
  font-size: 12px;
}

@media print {
  .llm-action-bar,
  .llm-chat,
  .llm-status,
  .llm-banner,
  .llm-disclaimer,
  .llm-export-row,
  .error-text {
    display: none;
  }
}
</style>
