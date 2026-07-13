<script setup lang="ts">
import { computed } from "vue";
import { marked } from "marked";

const props = defineProps<{ content: string }>();
const html = computed(() =>
  marked.parse(props.content || "_Sem conteúdo ainda. Use os botões acima para gerar._"),
);
</script>

<template>
  <div id="llm-print-area" class="llm-output" v-html="html" />
</template>

<style scoped>
.llm-output {
  background: var(--bg-muted);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 12px;
  font-size: 13px;
  line-height: 1.5;
  max-height: 240px;
  overflow-y: auto;
  color: var(--text-primary);
}

.llm-output :deep(h1),
.llm-output :deep(h2),
.llm-output :deep(h3) {
  margin: 0.5em 0 0.25em;
  font-size: 1em;
}

.llm-output :deep(ul),
.llm-output :deep(ol) {
  padding-left: 1.25em;
}

@media print {
  .llm-output {
    max-height: none;
    overflow: visible;
    border: none;
  }
}
</style>
