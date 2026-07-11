<script setup lang="ts">
import type { StateUpdate } from "../types/simulation";

defineProps<{ state: StateUpdate }>();
</script>

<template>
  <table class="stats-table">
    <thead>
      <tr>
        <th>Veículo</th>
        <th>Fitness</th>
        <th>Distância</th>
        <th>Carga</th>
        <th>Viagens</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="(plan, vehicleId) in state.plans" :key="vehicleId">
        <td>V{{ Number(vehicleId) + 1 }}</td>
        <td>{{ plan.fitness.toFixed(2) }}</td>
        <td>{{ plan.distance.toFixed(2) }}</td>
        <td>{{ plan.load }} / {{ plan.capacity }}</td>
        <td>{{ plan.trips.length }}</td>
      </tr>
    </tbody>
  </table>
</template>
