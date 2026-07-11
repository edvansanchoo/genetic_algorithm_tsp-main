<script setup lang="ts">
import type { StateUpdate } from "../types/simulation";

const props = defineProps<{ state: StateUpdate | null }>();
const emit = defineEmits<{
  setFocus: [vehicleId: number | null, tripIndex: number | null];
}>();

function groupedRoutes() {
  if (!props.state) return [];
  const groups: Record<number, { header: string; trips: Array<{ text: string; tripIndex: number }> }> = {};
  props.state.routes_panel.forEach((row) => {
    if (row.vehicle_id === undefined) return;
    if (!groups[row.vehicle_id]) {
      groups[row.vehicle_id] = { header: "", trips: [] };
    }
    if (row.type === "header") {
      groups[row.vehicle_id].header = row.text;
    } else if (row.trip_index !== undefined) {
      groups[row.vehicle_id].trips.push({ text: row.text.trim(), tripIndex: row.trip_index });
    }
  });
  return Object.entries(groups).map(([vehicleId, group]) => ({
    vehicleId: Number(vehicleId),
    ...group,
  }));
}
</script>

<template>
  <section v-if="state">
    <h3 class="section-title">Rotas</h3>
    <div
      v-for="group in groupedRoutes()"
      :key="group.vehicleId"
      class="route-card"
      :class="{ active: state.focus.vehicle_id === group.vehicleId }"
      @click="emit('setFocus', group.vehicleId, null)"
    >
      <strong>{{ group.header }}</strong>
      <div
        v-for="trip in group.trips"
        :key="trip.tripIndex"
        class="route-trip"
        @click.stop="emit('setFocus', group.vehicleId, trip.tripIndex)"
      >
        {{ trip.text }}
      </div>
    </div>
  </section>
</template>
