<script setup lang="ts">
import UiIcon from "./UiIcon.vue";

withDefaults(
  defineProps<{
    variant?: "primary" | "secondary" | "danger" | "ghost";
    icon?: string;
    disabled?: boolean;
  }>(),
  { variant: "secondary", disabled: false },
);
</script>

<template>
  <button
    class="ui-btn"
    :class="[`ui-btn--${variant}`]"
    :disabled="disabled"
    type="button"
  >
    <UiIcon v-if="icon" :name="icon" :size="16" />
    <slot />
  </button>
</template>

<style scoped>
.ui-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid var(--border);
  background: var(--bg-panel);
  color: var(--text-primary);
  border-radius: var(--radius-md);
  padding: 8px 12px;
  font-size: 13px;
  font-family: var(--font-ui);
  cursor: pointer;
  transition: background 150ms, border-color 150ms;
  white-space: nowrap;
}

.ui-btn:hover:not(:disabled) {
  background: var(--bg-muted);
}

.ui-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ui-btn--primary {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}

.ui-btn--primary:hover:not(:disabled) {
  background: var(--accent-hover);
  border-color: var(--accent-hover);
}

.ui-btn--danger {
  background: var(--danger-soft);
  border-color: #fecaca;
  color: var(--danger);
}

.ui-btn--ghost {
  background: transparent;
  border-color: transparent;
}

.ui-btn--ghost:hover:not(:disabled) {
  background: var(--bg-muted);
  border-color: var(--border);
}
</style>
