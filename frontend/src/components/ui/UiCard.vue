<script setup lang="ts">
withDefaults(
  defineProps<{
    padding?: string;
    noPadding?: boolean;
  }>(),
  { padding: "12px", noPadding: false },
);
</script>

<template>
  <div
    class="ui-card"
    :style="noPadding ? { padding: 0 } : { padding }"
  >
    <slot />
  </div>
</template>

<style scoped>
.ui-card {
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}
</style>
