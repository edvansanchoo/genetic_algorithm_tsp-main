<script setup lang="ts">
import { ref } from "vue";
import MapCanvas from "./MapCanvas.vue";
import MapLegend from "./MapLegend.vue";
import UiSwitch from "./ui/UiSwitch.vue";
import UiButton from "./ui/UiButton.vue";
import type { StateUpdate } from "../types/simulation";

const props = defineProps<{
  state: StateUpdate | null;
  showTransit: boolean;
  showRunnerUp: boolean;
}>();

const emit = defineEmits<{
  setFocus: [vehicleId: number | null, tripIndex?: number | null];
  setToggle: [key: string, active: boolean];
  toggleBlocked: [mapX: number, mapY: number];
  "update:showTransit": [value: boolean];
}>();

const panelRef = ref<HTMLElement | null>(null);
const zoom = ref(1);

function vehicleOptions(state: StateUpdate) {
  return Array.from({ length: state.summary.vehicles_total }, (_, index) => index);
}

function tripOptions(state: StateUpdate) {
  const vehicleId = state.focus.vehicle_id;
  if (vehicleId === null) return [];
  const plan = state.plans[String(vehicleId)];
  if (!plan) return [];
  return plan.trips.map((trip) => ({
    index: trip.index - 1,
    label: trip.index,
  }));
}

function onVehicleFilterChange(event: Event) {
  const value = (event.target as HTMLSelectElement).value;
  emit("setFocus", value === "all" ? null : Number(value), null);
}

function onTripFilterChange(event: Event) {
  const vehicleId = props.state?.focus.vehicle_id;
  if (vehicleId === null || vehicleId === undefined) return;
  const value = (event.target as HTMLSelectElement).value;
  emit("setFocus", vehicleId, value === "all" ? null : Number(value));
}

function zoomIn() {
  zoom.value = Math.min(2.5, zoom.value + 0.25);
}

function zoomOut() {
  zoom.value = Math.max(1, zoom.value - 0.25);
}

function toggleFullscreen() {
  if (!panelRef.value) return;
  if (document.fullscreenElement) {
    document.exitFullscreen();
    return;
  }
  panelRef.value.requestFullscreen();
}
</script>

<template>
  <section ref="panelRef" class="map-panel">
    <div v-if="state" class="map-panel__toolbar map-panel__toolbar--top">
      <UiSwitch
        :model-value="showTransit"
        label="Nós de trânsito"
        @update:model-value="emit('update:showTransit', $event)"
      />
      <UiSwitch
        :model-value="state.toggles.show_mesh"
        label="Malha de ruas"
        @update:model-value="emit('setToggle', 'show_mesh', $event)"
      />
      <label class="map-panel__select-wrap">
        <span>Veículo</span>
        <select
          class="map-panel__select"
          :value="state.focus.vehicle_id ?? 'all'"
          @change="onVehicleFilterChange"
        >
          <option value="all">Todos</option>
          <option v-for="vehicleId in vehicleOptions(state)" :key="vehicleId" :value="vehicleId">
            Veículo {{ vehicleId + 1 }}
          </option>
        </select>
      </label>
      <label v-if="state.focus.vehicle_id !== null" class="map-panel__select-wrap">
        <span>Viagem</span>
        <select
          class="map-panel__select"
          :value="state.focus.trip_index ?? 'all'"
          @change="onTripFilterChange"
        >
          <option value="all">Todas</option>
          <option v-for="trip in tripOptions(state)" :key="trip.index" :value="trip.index">
            Viagem {{ trip.label }}
          </option>
        </select>
      </label>
      <UiButton variant="ghost" icon="fullscreen" @click="toggleFullscreen" />
    </div>

    <div class="map-panel__canvas-area">
      <MapCanvas
        :state="state"
        :zoom="zoom"
        :show-transit="showTransit"
        :show-runner-up="showRunnerUp"
        @toggle-blocked="(mapX, mapY) => emit('toggleBlocked', mapX, mapY)"
      />
      <MapLegend />
    </div>

    <div v-if="state" class="map-panel__toolbar map-panel__toolbar--bottom">
      <UiButton variant="ghost" icon="zoom-out" @click="zoomOut" />
      <span class="map-panel__zoom-label">{{ Math.round(zoom * 100) }}%</span>
      <UiButton variant="ghost" icon="zoom-in" @click="zoomIn" />
    </div>
  </section>
</template>

<style scoped>
.map-panel {
  display: flex;
  flex-direction: column;
  min-height: 520px;
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  overflow: hidden;
  position: relative;
}

.map-panel__toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: var(--bg-panel);
  border-bottom: 1px solid var(--border);
  flex-wrap: wrap;
}

.map-panel__toolbar--bottom {
  border-bottom: none;
  border-top: 1px solid var(--border);
  justify-content: flex-end;
}

.map-panel__canvas-area {
  flex: 1;
  position: relative;
  min-height: 460px;
}

.map-panel__hint {
  position: absolute;
  top: 12px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(37, 99, 235, 0.9);
  color: #fff;
  padding: 6px 14px;
  border-radius: 999px;
  font-size: 12px;
  z-index: 3;
  pointer-events: none;
}

.map-panel__select-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-primary);
}

.map-panel__select {
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 6px 8px;
  background: var(--bg-panel);
  color: var(--text-primary);
  font-size: 13px;
}

.map-panel__zoom-label {
  font-size: 12px;
  color: var(--text-muted);
  min-width: 40px;
  text-align: center;
}
</style>
