<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import Chart from "chart.js/auto";
import type { StateUpdate } from "../types/simulation";

const props = defineProps<{ state: StateUpdate }>();
const canvasRef = ref<HTMLCanvasElement | null>(null);
let chart: Chart | null = null;

const defaultColors = ["#2563eb", "#059669", "#dc2626", "#d97706", "#7c3aed"];

const historiesSnapshot = computed(() => {
  const entries = Object.entries(props.state.histories)
    .sort(([a], [b]) => Number(a) - Number(b))
    .map(([vehicleId, values]) => ({
      vehicleId,
      values: values.slice(),
    }));
  return JSON.stringify(entries);
});

function vehicleColors(): string[] {
  return props.state.display?.vehicle_colors_ui ?? defaultColors;
}

function buildChartData() {
  const colors = vehicleColors();
  const labels = Array.from(
    {
      length: Math.max(
        ...Object.values(props.state.histories).map((values) => values.length),
        1,
      ),
    },
    (_, index) => String(index + 1),
  );
  const datasets = Object.entries(props.state.histories)
    .sort(([a], [b]) => Number(a) - Number(b))
    .map(([vehicleId, values]) => ({
      label: `V${Number(vehicleId) + 1}`,
      data: values.slice(),
      tension: 0.2,
      borderColor: colors[Number(vehicleId) % colors.length],
      backgroundColor: colors[Number(vehicleId) % colors.length],
      pointRadius: 0,
    }));
  return { labels, datasets };
}

function renderChart(forceRecreate = false) {
  const canvas = canvasRef.value;
  if (!canvas) return;

  const { labels, datasets } = buildChartData();

  if (!chart || forceRecreate) {
    chart?.destroy();
    chart = new Chart(canvas, {
      type: "line",
      data: { labels, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        plugins: { legend: { position: "top" } },
        scales: {
          x: { title: { display: true, text: "Geração" } },
          y: { title: { display: true, text: "Fitness" } },
        },
      },
    });
    return;
  }

  chart.data.labels = labels;
  datasets.forEach((dataset, index) => {
    const existing = chart!.data.datasets[index];
    if (existing && existing.label === dataset.label) {
      existing.data = dataset.data;
      existing.borderColor = dataset.borderColor;
      existing.backgroundColor = dataset.backgroundColor;
      return;
    }
    chart!.data.datasets[index] = dataset;
  });
  chart.data.datasets.length = datasets.length;
  chart.update("none");
}

onMounted(() => renderChart());
watch(historiesSnapshot, () => renderChart());
onUnmounted(() => chart?.destroy());
</script>

<template>
  <div style="height: 220px; margin-bottom: 12px">
    <canvas ref="canvasRef" />
  </div>
</template>
