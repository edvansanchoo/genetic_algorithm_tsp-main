import type { StateUpdate } from "../types/simulation";
import { type MapTransform } from "./mapTransform";

const MAP_BG_URL = "/images/map-background.png";

let mapImage: HTMLImageElement | null = null;
let loadPromise: Promise<HTMLImageElement> | null = null;

interface BackgroundCache {
  key: string;
  canvas: HTMLCanvasElement;
}

let backgroundCache: BackgroundCache | null = null;

export function preloadMapBackground(): Promise<HTMLImageElement> {
  if (mapImage?.complete && mapImage.naturalWidth > 0) {
    return Promise.resolve(mapImage);
  }
  if (loadPromise) return loadPromise;

  loadPromise = new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => {
      mapImage = image;
      resolve(image);
    };
    image.onerror = () => {
      loadPromise = null;
      reject(new Error("Falha ao carregar imagem de fundo do mapa"));
    };
    image.src = MAP_BG_URL;
  });

  return loadPromise;
}

function drawImageCover(
  ctx: CanvasRenderingContext2D,
  image: HTMLImageElement,
  x: number,
  y: number,
  width: number,
  height: number,
) {
  const scale = Math.max(width / image.width, height / image.height);
  const sourceWidth = width / scale;
  const sourceHeight = height / scale;
  const sourceX = (image.width - sourceWidth) / 2;
  const sourceY = (image.height - sourceHeight) / 2;
  ctx.drawImage(image, sourceX, sourceY, sourceWidth, sourceHeight, x, y, width, height);
}

function cacheKey(
  state: StateUpdate,
  transform: MapTransform,
  isDark: boolean,
): string {
  return `${state.map.bounds.join(",")}|${transform.width}|${transform.height}|${transform.scale}|${isDark}`;
}

function renderBackgroundLayer(
  ctx: CanvasRenderingContext2D,
  transform: MapTransform,
  isDark: boolean,
) {
  ctx.fillStyle = isDark ? "#111827" : "#ffffff";
  ctx.fillRect(0, 0, transform.width, transform.height);

  if (!mapImage) return;

  drawImageCover(ctx, mapImage, 0, 0, transform.width, transform.height);

  if (isDark) {
    ctx.fillStyle = "rgba(15, 23, 42, 0.45)";
    ctx.fillRect(0, 0, transform.width, transform.height);
  }
}

export function drawMapBackgroundImage(
  ctx: CanvasRenderingContext2D,
  state: StateUpdate,
  transform: MapTransform,
  isDark: boolean,
) {
  const key = cacheKey(state, transform, isDark);

  if (!backgroundCache || backgroundCache.key !== key) {
    const layer = document.createElement("canvas");
    layer.width = transform.width;
    layer.height = transform.height;
    const layerCtx = layer.getContext("2d");
    if (!layerCtx) return;
    renderBackgroundLayer(layerCtx, transform, isDark);
    backgroundCache = { key, canvas: layer };
  }

  ctx.drawImage(backgroundCache.canvas, 0, 0);
}

export function clearMapBackgroundCache() {
  backgroundCache = null;
}

preloadMapBackground().catch(() => {
  // Fallback silencioso: o canvas usa cor sólida até a imagem carregar.
});
