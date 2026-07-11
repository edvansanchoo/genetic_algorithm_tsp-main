<script setup lang="ts">
defineProps<{
  modelValue: boolean;
  label: string;
}>();

const emit = defineEmits<{ "update:modelValue": [value: boolean] }>();
</script>

<template>
  <label class="ui-switch">
    <input
      type="checkbox"
      class="ui-switch__input"
      :checked="modelValue"
      @change="emit('update:modelValue', ($event.target as HTMLInputElement).checked)"
    />
    <span class="ui-switch__track">
      <span class="ui-switch__thumb" />
    </span>
    <span class="ui-switch__label">{{ label }}</span>
  </label>
</template>

<style scoped>
.ui-switch {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  user-select: none;
}

.ui-switch__input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.ui-switch__track {
  position: relative;
  width: 36px;
  height: 20px;
  background: var(--border);
  border-radius: 10px;
  transition: background 200ms;
  flex-shrink: 0;
}

.ui-switch__thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 16px;
  height: 16px;
  background: #fff;
  border-radius: 50%;
  transition: transform 200ms;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.15);
}

.ui-switch__input:checked + .ui-switch__track {
  background: var(--accent);
}

.ui-switch__input:checked + .ui-switch__track .ui-switch__thumb {
  transform: translateX(16px);
}

.ui-switch__label {
  font-size: 13px;
  color: var(--text-primary);
}
</style>
