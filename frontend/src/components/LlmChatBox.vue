<script setup lang="ts">
import { ref } from "vue";
import UiButton from "./ui/UiButton.vue";
import type { ChatMessage } from "../composables/useLlmApi";

defineProps<{
  loading: boolean;
  history: ChatMessage[];
}>();

const emit = defineEmits<{
  send: [message: string];
}>();

const draft = ref("");

function submit() {
  const message = draft.value.trim();
  if (!message) return;
  emit("send", message);
  draft.value = "";
}
</script>

<template>
  <section class="llm-chat">
    <h3 class="section-title">Chat</h3>
    <div class="llm-chat-messages">
      <p v-if="history.length === 0" class="llm-chat-empty">
        Pergunte sobre rotas, entregas ou veículos.
      </p>
      <div
        v-for="(entry, index) in history"
        :key="index"
        class="llm-chat-line"
        :class="`llm-chat-line--${entry.role}`"
      >
        <strong>{{ entry.role === "user" ? "Você" : "Assistente" }}:</strong>
        {{ entry.content }}
      </div>
    </div>
    <div class="llm-chat-input">
      <input
        v-model="draft"
        type="text"
        aria-label="Pergunta sobre rotas"
        placeholder="Pergunte sobre rotas..."
        :disabled="loading"
        @keydown.enter="submit"
      />
      <UiButton variant="primary" :disabled="loading || !draft.trim()" @click="submit">
        Enviar
      </UiButton>
    </div>
  </section>
</template>

<style scoped>
.llm-chat {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.llm-chat-messages {
  max-height: 160px;
  overflow-y: auto;
  background: var(--bg-muted);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 8px;
  font-size: 12px;
}

.llm-chat-empty {
  color: var(--text-muted);
  margin: 0;
}

.llm-chat-line {
  margin-bottom: 6px;
  line-height: 1.4;
}

.llm-chat-line--assistant {
  color: var(--text-primary);
}

.llm-chat-input {
  display: flex;
  gap: 8px;
}

.llm-chat-input input {
  flex: 1;
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--bg-panel);
  color: var(--text-primary);
  font-size: 13px;
}
</style>
