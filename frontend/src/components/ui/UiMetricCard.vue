<script setup lang="ts">
defineProps<{
  label: string;
  value: string | number;
  unit?: string;
}>();
</script>

<template>
  <div class="ui-metric">
    <span class="ui-metric__label">{{ label }}</span>
    <span class="ui-metric__value">
      {{ value }}<span v-if="unit" class="ui-metric__unit">{{ unit }}</span>
    </span>
  </div>
</template>

<style scoped>
.ui-metric {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 90px;
}

.ui-metric__label {
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.ui-metric__value {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.ui-metric__unit {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-muted);
  margin-left: 2px;
}
</style>
