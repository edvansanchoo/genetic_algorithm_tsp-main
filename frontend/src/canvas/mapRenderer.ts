import type { StateUpdate } from "../types/simulation";
import { drawMapBackgroundImage } from "./mapBackground";
import {
  createMapTransform,
  type MapTransform,
  worldToCanvas,
} from "./mapTransform";

export interface DrawOptions {
  showTransit?: boolean;
  showRunnerUp?: boolean;
}

function drawDashedLine(
  ctx: CanvasRenderingContext2D,
  points: [number, number][],
  color: string,
  width = 2,
) {
  if (points.length < 2) return;
  ctx.save();
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  ctx.setLineDash([8, 6]);
  ctx.beginPath();
  ctx.moveTo(points[0][0], points[0][1]);
  for (let index = 1; index < points.length; index += 1) {
    ctx.lineTo(points[index][0], points[index][1]);
  }
  ctx.stroke();
  ctx.restore();
}

function drawSolidLine(
  ctx: CanvasRenderingContext2D,
  points: [number, number][],
  color: string,
  width = 3,
) {
  if (points.length < 2) return;
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  ctx.beginPath();
  ctx.moveTo(points[0][0], points[0][1]);
  for (let index = 1; index < points.length; index += 1) {
    ctx.lineTo(points[index][0], points[index][1]);
  }
  ctx.stroke();
}

function drawArrow(
  ctx: CanvasRenderingContext2D,
  from: [number, number],
  to: [number, number],
  color: string,
) {
  const angle = Math.atan2(to[1] - from[1], to[0] - from[0]);
  const size = 7;
  const tipX = to[0];
  const tipY = to[1];
  const baseX = tipX - Math.cos(angle) * size;
  const baseY = tipY - Math.sin(angle) * size;
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.moveTo(tipX, tipY);
  ctx.lineTo(
    baseX + Math.cos(angle + Math.PI / 2) * size * 0.4,
    baseY + Math.sin(angle + Math.PI / 2) * size * 0.4,
  );
  ctx.lineTo(
    baseX - Math.cos(angle + Math.PI / 2) * size * 0.4,
    baseY - Math.sin(angle + Math.PI / 2) * size * 0.4,
  );
  ctx.closePath();
  ctx.fill();
}

function polylineToCanvas(
  polyline: number[][],
  transform: MapTransform,
): [number, number][] {
  return polyline.map(([x, y]) => worldToCanvas(x, y, transform));
}

function drawCircleMarker(
  ctx: CanvasRenderingContext2D,
  cx: number,
  cy: number,
  radius: number,
  fill: string,
  stroke = "#ffffff",
  strokeWidth = 3,
) {
  ctx.save();
  ctx.shadowColor = "rgba(15, 23, 42, 0.35)";
  ctx.shadowBlur = 4;
  ctx.shadowOffsetY = 1;
  ctx.beginPath();
  ctx.arc(cx, cy, radius, 0, Math.PI * 2);
  ctx.fillStyle = fill;
  ctx.fill();
  ctx.shadowColor = "transparent";
  ctx.strokeStyle = stroke;
  ctx.lineWidth = strokeWidth;
  ctx.stroke();
  ctx.restore();
}

function vehicleColor(state: StateUpdate, vehicleId: number): string {
  const uiColors = state.display?.vehicle_colors_ui;
  if (uiColors?.length) {
    return uiColors[vehicleId % uiColors.length] ?? "#2563eb";
  }
  const colors = state.map.theme.vehicle_colors as string[];
  return colors[vehicleId % colors.length] ?? "#2563eb";
}

function drawPlanRoutes(
  ctx: CanvasRenderingContext2D,
  state: StateUpdate,
  transform: MapTransform,
  plans: StateUpdate["plans"],
  dashed = false,
  alpha = 1,
) {
  const focusId = state.focus.vehicle_id;
  Object.entries(plans).forEach(([vehicleIdText, plan]) => {
    const vehicleId = Number(vehicleIdText);
    if (focusId !== null && focusId !== vehicleId) return;
    const color = vehicleColor(state, vehicleId);
    ctx.globalAlpha = alpha;
    plan.trips.forEach((trip, tripIndex) => {
      trip.polylines.forEach((polyline) => {
        const points = polylineToCanvas(polyline, transform);
        if (dashed || tripIndex > 0) {
          drawDashedLine(ctx, points, color, tripIndex > 0 ? 2 : 2);
        } else {
          drawSolidLine(ctx, points, color, focusId === vehicleId ? 3 : 2);
        }
        for (let index = 1; index < points.length; index += 4) {
          drawArrow(ctx, points[index - 1], points[index], color);
        }
      });
    });
    ctx.globalAlpha = 1;
  });
}

export function drawMap(
  ctx: CanvasRenderingContext2D,
  state: StateUpdate,
  transform: MapTransform,
  hoverDeliveryId: string | null,
  options: DrawOptions = {},
) {
  const showTransit = options.showTransit ?? true;
  const showRunnerUp = options.showRunnerUp ?? true;
  const theme = state.map.theme;
  const isDark = document.documentElement.dataset.theme === "dark";
  ctx.clearRect(0, 0, transform.width, transform.height);
  drawMapBackgroundImage(ctx, state, transform, isDark);

  if (state.toggles.show_mesh) {
    ctx.strokeStyle = String(theme.mesh_edge_color);
    ctx.lineWidth = 2;
    ctx.globalAlpha = 0.85;
    state.map.mesh.edges.forEach(([x1, y1, x2, y2]) => {
      const start = worldToCanvas(x1, y1, transform);
      const end = worldToCanvas(x2, y2, transform);
      ctx.beginPath();
      ctx.moveTo(start[0], start[1]);
      ctx.lineTo(end[0], end[1]);
      ctx.stroke();
    });
    ctx.globalAlpha = 1;
  }

  if (showTransit) {
    state.map.mesh.transit_nodes.forEach(([x, y]) => {
      const [cx, cy] = worldToCanvas(x, y, transform);
      drawCircleMarker(ctx, cx, cy, 7, "#64748b", "#ffffff", 2.5);
    });
  }

  if (
    showRunnerUp &&
    state.focus.vehicle_id !== null &&
    state.runner_up[String(state.focus.vehicle_id)]
  ) {
    drawPlanRoutes(
      ctx,
      state,
      transform,
      { [String(state.focus.vehicle_id)]: state.runner_up[String(state.focus.vehicle_id)] },
      true,
      0.55,
    );
  }

  drawPlanRoutes(ctx, state, transform, state.plans);

  state.map.deliveries.forEach((delivery) => {
    const [cx, cy] = worldToCanvas(delivery.x, delivery.y, transform);
    const radius = hoverDeliveryId === delivery.id ? 15 : 13;
    drawCircleMarker(ctx, cx, cy, radius, delivery.color, "#ffffff", 3);
    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 12px Consolas, monospace";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(String(delivery.priority), cx, cy);
  });

  if (state.map.depot) {
    const [cx, cy] = worldToCanvas(state.map.depot[0], state.map.depot[1], transform);
    const size = 24;
    ctx.save();
    ctx.shadowColor = "rgba(15, 23, 42, 0.35)";
    ctx.shadowBlur = 4;
    ctx.fillStyle = String(theme.depot_color);
    ctx.fillRect(cx - size / 2, cy - size / 2, size, size);
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 3;
    ctx.strokeRect(cx - size / 2, cy - size / 2, size, size);
    ctx.restore();
    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 13px Consolas, monospace";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText("D", cx, cy);
  }

  state.map.mesh.blocked.forEach(([x, y]) => {
    const [cx, cy] = worldToCanvas(x, y, transform);
    drawCircleMarker(ctx, cx, cy, 11, String(theme.blocked_color), "#ffffff", 3);
    ctx.strokeStyle = "#7f1d1d";
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.moveTo(cx - 5, cy - 5);
    ctx.lineTo(cx + 5, cy + 5);
    ctx.moveTo(cx - 5, cy + 5);
    ctx.lineTo(cx + 5, cy - 5);
    ctx.stroke();
  });

  if (state.animation?.position) {
    const [cx, cy] = worldToCanvas(
      state.animation.position[0],
      state.animation.position[1],
      transform,
    );
    const color = vehicleColor(state, state.animation.vehicle_id);
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(cx, cy, 8, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#ffffff";
    ctx.beginPath();
    ctx.arc(cx, cy, 3, 0, Math.PI * 2);
    ctx.fill();
  }
}

export function buildTransform(
  state: StateUpdate,
  width: number,
  height: number,
  zoom = 1,
): MapTransform {
  return createMapTransform(state.map.bounds, width, height, 24, zoom);
}
