<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from "vue";
import { useWebSocket } from "./composables/useWebSocket";
import { usePreferences } from "./composables/usePreferences";
import AppHeader from "./components/AppHeader.vue";
import SidebarInfo from "./components/SidebarInfo.vue";
import SidebarParams from "./components/SidebarParams.vue";
import SidebarToggles from "./components/SidebarToggles.vue";
import SidebarActions from "./components/SidebarActions.vue";
import PriorityLegend from "./components/PriorityLegend.vue";
import TabPanel from "./components/TabPanel.vue";
import MapPanel from "./components/MapPanel.vue";
import StatusFooter from "./components/StatusFooter.vue";
import type { HistoryEntry } from "./types/simulation";

const { state, lastError, sendCommand } = useWebSocket();
const { showRunnerUp, showTransit } = usePreferences();
const history = ref<HistoryEntry[]>([]);

watch(
  state,
  (value, previous) => {
    if (!value) return;
    if (!previous || value.generation !== previous.generation) {
      history.value.push({
        generation: value.generation,
        fitness: value.metrics.fitness,
        distance: value.metrics.distance,
        priority_penalty: value.metrics.priority_penalty,
      });
      if (history.value.length > 200) {
        history.value.shift();
      }
    }
  },
  { deep: true },
);

function setParam(key: string, value: number) {
  sendCommand({ action: "set_param", key, value });
}

function setToggle(key: string, active: boolean) {
  sendCommand({ action: "set_toggle", key, active });
}

function runAction(name: string) {
  sendCommand({ action: "action", name });
}

function setFocus(vehicleId: number | null, tripIndex: number | null = null) {
  sendCommand({ action: "set_focus", vehicle_id: vehicleId, trip_index: tripIndex });
}

function toggleBlocked(mapX: number, mapY: number) {
  sendCommand({ action: "toggle_blocked", map_x: mapX, map_y: mapY });
}

function resetScenario() {
  runAction("shuffle_positions");
  runAction("clear_blocked");
}
</script>

<template>
  <div class="app-shell">
    <AppHeader
      :state="state"
      @pause="sendCommand({ action: 'pause' })"
      @resume="sendCommand({ action: 'resume' })"
      @restart="runAction('restart_algorithm')"
    />
    <div class="app-shell__main">
      <p v-if="lastError" class="error-banner">{{ lastError }}</p>
      <div class="main-grid">
        <aside class="panel sidebar">
          <SidebarInfo :state="state" />
          <SidebarParams :state="state" @set-param="setParam" />
          <SidebarToggles :state="state" @set-toggle="setToggle" />
          <SidebarActions
            @shuffle="runAction('shuffle_positions')"
            @hospital="runAction('hospital_preset')"
            @reset="resetScenario"
          />
          <PriorityLegend />
        </aside>
        <TabPanel
          :state="state"
          :history="history"
          @set-focus="setFocus"
        />
        <MapPanel
          :state="state"
          :show-transit="showTransit"
          :show-runner-up="showRunnerUp"
          @set-focus="setFocus"
          @set-toggle="setToggle"
          @toggle-blocked="toggleBlocked"
          @update:show-transit="showTransit = $event"
        />
      </div>
    </div>
    <StatusFooter :state="state" />
  </div>
</template>
