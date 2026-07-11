export interface MapTransform {
  scale: number;
  offsetX: number;
  offsetY: number;
  width: number;
  height: number;
}

export function createMapTransform(
  bounds: [number, number, number, number],
  width: number,
  height: number,
  padding = 24,
  zoom = 1,
): MapTransform {
  const [xMin, yMin, xMax, yMax] = bounds;
  const mapWidth = Math.max(1, xMax - xMin);
  const mapHeight = Math.max(1, yMax - yMin);
  const baseScale = Math.min(
    (width - padding * 2) / mapWidth,
    (height - padding * 2) / mapHeight,
  );
  const scale = baseScale * zoom;
  const offsetX = padding + (width - padding * 2 - mapWidth * scale) / 2 - xMin * scale;
  const offsetY = padding + (height - padding * 2 - mapHeight * scale) / 2 - yMin * scale;
  return { scale, offsetX, offsetY, width, height };
}

export function worldToCanvas(
  x: number,
  y: number,
  transform: MapTransform,
): [number, number] {
  return [x * transform.scale + transform.offsetX, y * transform.scale + transform.offsetY];
}

export function canvasToWorld(
  x: number,
  y: number,
  transform: MapTransform,
): [number, number] {
  return [
    (x - transform.offsetX) / transform.scale,
    (y - transform.offsetY) / transform.scale,
  ];
}
