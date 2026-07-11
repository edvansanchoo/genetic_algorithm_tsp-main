<script setup lang="ts">
import { computed } from "vue";
import { priorityToColor } from "../../utils/priorityColor";

const props = defineProps<{ priority: number }>();

const color = computed(() => priorityToColor(props.priority));
</script>

<template>
  <span
    class="ui-badge"
    :style="{ background: color }"
    :title="`Prioridade ${priority}`"
  >
    {{ priority }}
  </span>
</template>

<style scoped>
.ui-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  padding: 0 4px;
  border-radius: 50%;
  font-size: 11px;
  font-weight: 700;
  color: #fff;
  font-family: var(--font-mono);
}
</style>
