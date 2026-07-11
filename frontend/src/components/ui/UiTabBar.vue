<script setup lang="ts">
defineProps<{
  tabs: Array<{ id: string; label: string }>;
  active: string;
}>();

const emit = defineEmits<{ change: [id: string] }>();
</script>

<template>
  <div class="ui-tab-bar">
    <button
      v-for="tab in tabs"
      :key="tab.id"
      class="ui-tab-bar__tab"
      :class="{ 'ui-tab-bar__tab--active': active === tab.id }"
      type="button"
      @click="emit('change', tab.id)"
    >
      {{ tab.label }}
    </button>
  </div>
</template>

<style scoped>
.ui-tab-bar {
  display: flex;
  gap: 4px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 12px;
}

.ui-tab-bar__tab {
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  padding: 8px 12px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-muted);
  cursor: pointer;
  margin-bottom: -1px;
  font-family: var(--font-ui);
  transition: color 150ms, border-color 150ms;
}

.ui-tab-bar__tab:hover {
  color: var(--text-primary);
}

.ui-tab-bar__tab--active {
  color: var(--accent);
  border-bottom-color: var(--accent);
  font-weight: 600;
}
</style>
