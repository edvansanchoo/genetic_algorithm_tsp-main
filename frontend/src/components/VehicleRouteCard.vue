<script setup lang="ts">
import { computed } from "vue";
import UiBadge from "./ui/UiBadge.vue";
import type { StateUpdate } from "../types/simulation";

const props = defineProps<{
  vehicleId: number;
  plan: StateUpdate["plans"][string];
  color: string;
  active: boolean;
  focusTripIndex: number | null;
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

function isDepot(stop: string): boolean {
  return stop === "DEPOT";
}

function stopPriority(stop: string): number | null {
  if (isDepot(stop)) return null;
  return props.deliveryPriorities[stop] ?? null;
}

function isTripActive(tripIndex: number): boolean {
  return props.active && props.focusTripIndex === tripIndex - 1;
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
      :class="{ 'vehicle-route-card__trip--active': isTripActive(trip.index) }"
      @click.stop="emit('selectTrip', trip.index - 1)"
    >
      <div class="vehicle-route-card__trip-label">
        <span>Viagem {{ trip.index }}</span>
        <span class="vehicle-route-card__trip-load">
          {{ trip.load }}/{{ plan.capacity }} un
        </span>
      </div>
      <div class="vehicle-route-card__stops">
        <span
          v-for="(stop, index) in trip.stops"
          :key="`${trip.index}-${index}`"
          class="vehicle-route-card__stop"
        >
          <span v-if="isDepot(stop)" class="vehicle-route-card__depot">D</span>
          <UiBadge
            v-else-if="stopPriority(stop) !== null"
            :priority="stopPriority(stop)!"
          />
          <span v-else class="vehicle-route-card__unknown">{{ stop }}</span>
          <span v-if="index < trip.stops.length - 1" class="vehicle-route-card__arrow">→</span>
        </span>
      </div>
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
  padding: 8px 10px;
  margin-top: 8px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm, 6px);
  background: var(--bg-muted, rgba(0, 0, 0, 0.03));
}

.vehicle-route-card__trip:first-of-type {
  margin-top: 0;
}

.vehicle-route-card__trip--active {
  border-color: var(--accent);
  background: var(--accent-soft);
  box-shadow: inset 0 0 0 1px var(--accent);
}

.vehicle-route-card__trip-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  font-family: var(--font-sans, inherit);
}

.vehicle-route-card__trip-load {
  font-weight: 500;
  font-family: var(--font-mono);
}

.vehicle-route-card__stops {
  font-family: var(--font-mono);
  font-size: 12px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
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

.vehicle-route-card__unknown {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  padding: 0 4px;
  border-radius: 4px;
  background: var(--bg-muted);
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 600;
}

.vehicle-route-card__arrow {
  color: var(--text-muted);
  margin: 0 2px;
}
</style>
