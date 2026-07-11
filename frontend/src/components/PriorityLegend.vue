<script setup lang="ts">
import UiBadge from "./ui/UiBadge.vue";
</script>

<template>
  <section>
    <h3 class="section-title">Legenda de prioridade</h3>
    <div class="priority-legend">
      <UiBadge v-for="priority in 10" :key="priority" :priority="priority" />
    </div>
  </section>
</template>

<style scoped>
.priority-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}
</style>
