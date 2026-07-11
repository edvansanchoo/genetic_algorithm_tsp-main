<script setup lang="ts">
import { computed, ref } from "vue";
import ConvergenceChart from "./ConvergenceChart.vue";
import LogConsole from "./LogConsole.vue";
import StatsTable from "./StatsTable.vue";
import HistoryList from "./HistoryList.vue";
import VehicleRouteCard from "./VehicleRouteCard.vue";
import UiTabBar from "./ui/UiTabBar.vue";
import type { HistoryEntry, StateUpdate } from "../types/simulation";

const props = defineProps<{
  state: StateUpdate | null;
  history: HistoryEntry[];
}>();

const emit = defineEmits<{
  setFocus: [vehicleId: number | null, tripIndex: number | null];
}>();

const activeTab = ref("resumo");
const tabs = [
  { id: "resumo", label: "Resumo" },
  { id: "stats", label: "Estatísticas" },
  { id: "history", label: "Histórico" },
  { id: "logs", label: "Logs" },
];

const deliveryPriorities = computed(() => {
  if (!props.state) return {};
  return Object.fromEntries(
    props.state.map.deliveries.map((delivery) => [delivery.id, delivery.priority]),
  );
});

function vehicleColor(state: StateUpdate, vehicleId: number): string {
  const colors = state.display?.vehicle_colors_ui ?? [
    "#2563eb",
    "#059669",
    "#dc2626",
    "#d97706",
    "#7c3aed",
  ];
  return colors[vehicleId % colors.length] ?? "#2563eb";
}

function vehiclePlans(state: StateUpdate) {
  return Object.entries(state.plans)
    .map(([vehicleId, plan]) => ({
      vehicleId: Number(vehicleId),
      plan,
      color: vehicleColor(state, Number(vehicleId)),
    }))
    .sort((a, b) => a.vehicleId - b.vehicleId);
}

const vehicleEntries = computed(() => {
  if (!props.state) return [];
  return vehiclePlans(props.state);
});
</script>

<template>
  <div class="panel tab-panel">
    <UiTabBar :tabs="tabs" :active="activeTab" @change="activeTab = $event" />

    <div class="tab-panel__body">
      <div v-if="activeTab === 'resumo' && state" class="resumo-tab">
        <div class="resumo-chart">
          <p class="chart-section-title">Convergência do algoritmo</p>
          <ConvergenceChart :state="state" />
        </div>
        <div class="resumo-routes">
          <p class="routes-section-title">Rotas por veículo</p>
          <div
            class="routes-scroll"
            :class="{ 'routes-scroll--limited': vehicleEntries.length > 4 }"
          >
            <VehicleRouteCard
              v-for="entry in vehicleEntries"
              :key="entry.vehicleId"
              :vehicle-id="entry.vehicleId"
              :plan="entry.plan"
              :color="entry.color"
              :active="state.focus.vehicle_id === entry.vehicleId"
              :delivery-priorities="deliveryPriorities"
              @select-vehicle="emit('setFocus', entry.vehicleId, null)"
              @select-trip="emit('setFocus', entry.vehicleId, $event)"
            />
          </div>
        </div>
      </div>

      <StatsTable v-if="activeTab === 'stats' && state" :state="state" />
      <div v-if="activeTab === 'history'" class="history-scroll">
        <HistoryList :history="history" />
      </div>
      <LogConsole v-if="activeTab === 'logs' && state" :state="state" />
    </div>
  </div>
</template>
