<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from "vue";
import type { StateUpdate } from "../types/simulation";
import { buildTransform, drawMap } from "../canvas/mapRenderer";
import { clearMapBackgroundCache, preloadMapBackground } from "../canvas/mapBackground";
import { canvasToWorld, worldToCanvas } from "../canvas/mapTransform";
import { useTheme } from "../composables/useTheme";

const props = defineProps<{
  state: StateUpdate | null;
  zoom?: number;
  showTransit?: boolean;
  showRunnerUp?: boolean;
}>();

const emit = defineEmits<{ toggleBlocked: [mapX: number, mapY: number] }>();

const { theme } = useTheme();

const canvasRef = ref<HTMLCanvasElement | null>(null);
const hoverDeliveryId = ref<string | null>(null);
const isOverClickableNode = ref(false);
let resizeObserver: ResizeObserver | null = null;

const HIT_RADIUS_PX = 22;
const DEPOT_HIT_RADIUS_PX = 16;
const TRANSIT_HIT_RADIUS_PX = 12;
const BLOCKED_HIT_RADIUS_PX = 14;

function render() {
  const canvas = canvasRef.value;
  if (!canvas || !props.state) return;
  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const transform = buildTransform(
    props.state,
    rect.width,
    rect.height,
    props.zoom ?? 1,
  );
  drawMap(ctx, props.state, transform, hoverDeliveryId.value, {
    showTransit: props.showTransit ?? true,
    showRunnerUp: props.showRunnerUp ?? true,
  });
}

function canvasPoint(event: MouseEvent) {
  const canvas = canvasRef.value;
  if (!canvas) return null;
  const rect = canvas.getBoundingClientRect();
  return {
    x: event.clientX - rect.left,
    y: event.clientY - rect.top,
    rect,
  };
}

function onClick(event: MouseEvent) {
  const canvas = canvasRef.value;
  const point = canvasPoint(event);
  if (!canvas || !point || !props.state) return;

  const transform = buildTransform(
    props.state,
    point.rect.width,
    point.rect.height,
    props.zoom ?? 1,
  );
  const [mapX, mapY] = canvasToWorld(point.x, point.y, transform);
  emit("toggleBlocked", mapX, mapY);
}

function onMouseMove(event: MouseEvent) {
  const point = canvasPoint(event);
  if (!point || !props.state) return;

  const transform = buildTransform(
    props.state,
    point.rect.width,
    point.rect.height,
    props.zoom ?? 1,
  );

  let closestId: string | null = null;
  let closestDistance = HIT_RADIUS_PX;
  let overClickable = false;

  props.state.map.deliveries.forEach((delivery) => {
    const [cx, cy] = worldToCanvas(delivery.x, delivery.y, transform);
    const distance = Math.hypot(cx - point.x, cy - point.y);
    if (distance <= HIT_RADIUS_PX) {
      overClickable = true;
      if (distance <= closestDistance) {
        closestId = delivery.id;
        closestDistance = distance;
      }
    }
  });

  if (props.state.map.depot) {
    const [cx, cy] = worldToCanvas(props.state.map.depot[0], props.state.map.depot[1], transform);
    const depotDistance = Math.hypot(cx - point.x, cy - point.y);
    if (depotDistance <= DEPOT_HIT_RADIUS_PX) {
      overClickable = true;
      if (depotDistance <= closestDistance) {
        closestId = "__depot__";
        closestDistance = depotDistance;
      }
    }
  }

  if (props.showTransit ?? true) {
    props.state.map.mesh.transit_nodes.forEach(([x, y]) => {
      const [cx, cy] = worldToCanvas(x, y, transform);
      if (Math.hypot(cx - point.x, cy - point.y) <= TRANSIT_HIT_RADIUS_PX) {
        overClickable = true;
      }
    });
  }

  props.state.map.mesh.blocked.forEach(([x, y]) => {
    const [cx, cy] = worldToCanvas(x, y, transform);
    if (Math.hypot(cx - point.x, cy - point.y) <= BLOCKED_HIT_RADIUS_PX) {
      overClickable = true;
    }
  });

  isOverClickableNode.value = overClickable;

  if (hoverDeliveryId.value !== closestId) {
    hoverDeliveryId.value = closestId;
    render();
  }
}

function onMouseLeave() {
  isOverClickableNode.value = false;
  if (hoverDeliveryId.value !== null) {
    hoverDeliveryId.value = null;
    render();
  }
}

onMounted(async () => {
  resizeObserver = new ResizeObserver(render);
  if (canvasRef.value) resizeObserver.observe(canvasRef.value);
  try {
    await preloadMapBackground();
    clearMapBackgroundCache();
  } catch {
    // Mantém fallback de cor sólida.
  }
  render();
});

onUnmounted(() => resizeObserver?.disconnect());

watch(theme, () => {
  clearMapBackgroundCache();
  render();
});

watch(
  () => [props.state, props.zoom, props.showTransit, props.showRunnerUp],
  render,
  { deep: true },
);
</script>

<template>
  <div class="map-canvas-wrap">
    <canvas
      ref="canvasRef"
      :style="{ cursor: isOverClickableNode ? 'pointer' : 'default' }"
      @click="onClick"
      @mousemove="onMouseMove"
      @mouseleave="onMouseLeave"
    />
  </div>
</template>
