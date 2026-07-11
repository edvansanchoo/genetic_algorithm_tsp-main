<script setup lang="ts">
import type { StateUpdate } from "../types/simulation";

const props = defineProps<{ state: StateUpdate | null }>();
const emit = defineEmits<{
  setFocus: [vehicleId: number | null];
  setToggle: [key: string, active: boolean];
}>();

function vehicleOptions() {
  if (!props.state) return [];
  return Array.from({ length: props.state.summary.vehicles_total }, (_, index) => index);
}
</script>

<template>
  <div class="map-toolbar" v-if="state">
    <label>
      Filtro
      <select
        :value="state.focus.vehicle_id ?? 'all'"
        @change="
          emit(
            'setFocus',
            ($event.target as HTMLSelectElement).value === 'all'
              ? null
              : Number(($event.target as HTMLSelectElement).value),
          )
        "
      >
        <option value="all">Todos</option>
        <option v-for="vehicleId in vehicleOptions()" :key="vehicleId" :value="vehicleId">
          Veículo {{ vehicleId + 1 }}
        </option>
      </select>
    </label>
    <label>
      <input
        type="checkbox"
        :checked="state.toggles.show_mesh"
        @change="emit('setToggle', 'show_mesh', ($event.target as HTMLInputElement).checked)"
      />
      Malha
    </label>
  </div>
</template>
