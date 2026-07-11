<script setup lang="ts">
import type { HistoryEntry } from "../types/simulation";

defineProps<{ history: HistoryEntry[] }>();
</script>

<template>
  <table class="history-list">
    <thead>
      <tr>
        <th>Geração</th>
        <th>Fitness</th>
        <th>Distância</th>
        <th>Prioridade</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="entry in [...history].reverse()" :key="entry.generation">
        <td>{{ entry.generation }}</td>
        <td>{{ entry.fitness }}</td>
        <td>{{ entry.distance }}</td>
        <td>{{ entry.priority_penalty }}</td>
      </tr>
    </tbody>
  </table>
</template>
