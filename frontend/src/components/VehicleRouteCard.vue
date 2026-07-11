<script setup lang="ts">
import { computed } from "vue";
import UiBadge from "./ui/UiBadge.vue";
import type { StateUpdate } from "../types/simulation";

const props = defineProps<{
  vehicleId: number;
  plan: StateUpdate["plans"][string];
  color: string;
  active: boolean;
  deliveryPriorities: Record<string, number>;
}>();

const emit = defineEmits<{
  selectVehicle: [];
  selectTrip: [tripIndex: number];
}>();

const stats = computed(() => ({
  distance: props.plan.distance.toFixed(1),
  load: props.plan.load,
  capacity: props.plan.capacity,
  trips: props.plan.trips.length,
}));

function stopLabel(stop: string): string {
  return stop === "D" ? "D" : stop;
}

function stopPriority(stop: string): number | null {
  if (stop === "D") return null;
  return props.deliveryPriorities[stop] ?? null;
}
</script>

<template>
  <div
    class="vehicle-route-card"
    :class="{ 'vehicle-route-card--active': active }"
    :style="{ borderLeftColor: color }"
    @click="emit('selectVehicle')"
  >
    <div class="vehicle-route-card__header">
      <strong :style="{ color }">Veículo {{ vehicleId + 1 }}</strong>
      <div class="vehicle-route-card__stats">
        <span>{{ stats.distance }} km</span>
        <span>{{ stats.load }}/{{ stats.capacity }} un</span>
        <span>{{ stats.trips }} viagens</span>
      </div>
    </div>
    <div
      v-for="trip in plan.trips"
      :key="trip.index"
      class="vehicle-route-card__trip"
      @click.stop="emit('selectTrip', trip.index)"
    >
      <span
        v-for="(stop, index) in trip.stops"
        :key="`${trip.index}-${index}`"
        class="vehicle-route-card__stop"
      >
        <UiBadge v-if="stopPriority(stop) !== null" :priority="stopPriority(stop)!" />
        <span v-else class="vehicle-route-card__depot">D</span>
        <span v-if="index < trip.stops.length - 1" class="vehicle-route-card__arrow">→</span>
      </span>
    </div>
  </div>
</template>

<style scoped>
.vehicle-route-card {
  border: 1px solid var(--border);
  border-left-width: 4px;
  border-radius: var(--radius-md);
  padding: 10px 12px;
  margin-bottom: 8px;
  cursor: pointer;
  background: var(--bg-panel);
  transition: background 150ms, border-color 150ms;
}

.vehicle-route-card:hover {
  background: var(--bg-muted);
}

.vehicle-route-card--active {
  background: var(--accent-soft);
  border-color: var(--accent);
  border-left-width: 4px;
}

.vehicle-route-card__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 8px;
}

.vehicle-route-card__stats {
  display: flex;
  gap: 8px;
  font-size: 11px;
  color: var(--text-muted);
  flex-wrap: wrap;
  justify-content: flex-end;
}

.vehicle-route-card__trip {
  font-family: var(--font-mono);
  font-size: 12px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
  padding: 4px 0;
  border-top: 1px solid var(--border);
}

.vehicle-route-card__trip:first-of-type {
  border-top: none;
}

.vehicle-route-card__stop {
  display: inline-flex;
  align-items: center;
  gap: 2px;
}

.vehicle-route-card__depot {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  background: #1c2030;
  color: #fff;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
}

.vehicle-route-card__arrow {
  color: var(--text-muted);
  margin: 0 2px;
}
</style>
