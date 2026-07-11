<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  modelValue: number;
  min: number;
  max: number;
  step?: number;
  label: string;
  suffix?: string;
  format?: (value: number) => string;
}>();

const emit = defineEmits<{ "update:modelValue": [value: number] }>();

const displayValue = computed(() => {
  if (props.format) return props.format(props.modelValue);
  if (props.suffix) return `${props.modelValue}${props.suffix}`;
  return String(props.modelValue);
});

const fillPercent = computed(() => {
  const range = props.max - props.min;
  if (range <= 0) return 0;
  return ((props.modelValue - props.min) / range) * 100;
});

function onInput(event: Event) {
  emit("update:modelValue", Number((event.target as HTMLInputElement).value));
}
</script>

<template>
  <div class="ui-slider">
    <div class="ui-slider__header">
      <span class="ui-slider__label">{{ label }}</span>
      <span class="ui-slider__value">{{ displayValue }}</span>
    </div>
    <div class="ui-slider__track-wrap">
      <div class="ui-slider__track">
        <div class="ui-slider__fill" :style="{ width: `${fillPercent}%` }" />
      </div>
      <input
        type="range"
        class="ui-slider__input"
        :min="min"
        :max="max"
        :step="step ?? 1"
        :value="modelValue"
        @input="onInput"
      />
    </div>
  </div>
</template>

<style scoped>
.ui-slider {
  margin-bottom: 12px;
}

.ui-slider__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.ui-slider__label {
  font-size: 13px;
  color: var(--text-primary);
}

.ui-slider__value {
  font-size: 12px;
  font-weight: 600;
  color: var(--accent);
}

.ui-slider__track-wrap {
  position: relative;
  height: 20px;
  display: flex;
  align-items: center;
}

.ui-slider__track {
  position: absolute;
  left: 0;
  right: 0;
  height: 4px;
  background: var(--border);
  border-radius: 2px;
  pointer-events: none;
}

.ui-slider__fill {
  height: 100%;
  background: var(--accent);
  border-radius: 2px;
}

.ui-slider__input {
  position: relative;
  width: 100%;
  height: 20px;
  margin: 0;
  background: transparent;
  appearance: none;
  cursor: pointer;
}

.ui-slider__input::-webkit-slider-thumb {
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--accent);
  border: 2px solid #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.ui-slider__input::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--accent);
  border: 2px solid #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}
</style>
