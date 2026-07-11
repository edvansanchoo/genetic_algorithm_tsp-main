<template>
  <div class="map-legend">
    <div class="map-legend__title">Legenda</div>
    <div class="map-legend__item">
      <span class="map-legend__depot" />
      <span>Depósito</span>
    </div>
    <div class="map-legend__item">
      <span class="map-legend__delivery" />
      <span>Entrega</span>
    </div>
    <div class="map-legend__item">
      <span class="map-legend__transit" />
      <span>Nó de trânsito</span>
    </div>
    <div class="map-legend__item">
      <span class="map-legend__blocked">✕</span>
      <span>Bloqueado</span>
    </div>
    <div class="map-legend__item">
      <span class="map-legend__route-solid" />
      <span>Rota atual</span>
    </div>
    <div class="map-legend__item">
      <span class="map-legend__route-dashed" />
      <span>2ª melhor rota</span>
    </div>
  </div>
</template>

<style scoped>
.map-legend {
  position: absolute;
  left: 12px;
  bottom: 12px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 10px 12px;
  font-size: 11px;
  color: var(--text-primary);
  box-shadow: var(--shadow-card);
  z-index: 2;
  min-width: 140px;
}

[data-theme="dark"] .map-legend {
  background: rgba(30, 41, 59, 0.92);
}

.map-legend__title {
  font-weight: 700;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.map-legend__item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 5px;
}

.map-legend__item:last-child {
  margin-bottom: 0;
}

.map-legend__depot {
  width: 14px;
  height: 14px;
  background: #1c2030;
  border-radius: 2px;
  flex-shrink: 0;
}

.map-legend__delivery {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: linear-gradient(135deg, #4caf50, #f44336);
  flex-shrink: 0;
}

.map-legend__transit {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #94a3b8;
  flex-shrink: 0;
}

.map-legend__blocked {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #dc2626;
  color: #fff;
  font-size: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.map-legend__route-solid {
  width: 20px;
  height: 3px;
  background: var(--accent);
  border-radius: 2px;
  flex-shrink: 0;
}

.map-legend__route-dashed {
  width: 20px;
  height: 0;
  border-top: 2px dashed var(--accent);
  flex-shrink: 0;
}
</style>
