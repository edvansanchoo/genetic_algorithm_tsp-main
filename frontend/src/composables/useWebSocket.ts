import { onMounted, onUnmounted, ref } from "vue";
import type { StateUpdate } from "../types/simulation";

const DEV_WS_URL = "ws://127.0.0.1:8000/ws";

function resolveWebSocketUrl(url?: string): string {
  if (url) return url;
  if (import.meta.env.DEV) {
    return DEV_WS_URL;
  }
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  return `${protocol}://${window.location.host}/ws`;
}

export function useWebSocket(url?: string) {
  const state = ref<StateUpdate | null>(null);
  const connected = ref(false);
  const lastError = ref<string | null>(null);
  let socket: WebSocket | null = null;
  let reconnectTimer: number | null = null;
  let shouldReconnect = true;

  const wsUrl = resolveWebSocketUrl(url);

  function sendCommand(command: Record<string, unknown>) {
    if (socket && socket.readyState === WebSocket.OPEN) {
      lastError.value = null;
      socket.send(JSON.stringify({ type: "command", ...command }));
    }
  }

  function scheduleReconnect() {
    if (!shouldReconnect || reconnectTimer !== null) return;
    reconnectTimer = window.setTimeout(() => {
      reconnectTimer = null;
      connect();
    }, 1500);
  }

  function connect() {
    if (!shouldReconnect) return;
    socket?.close();
    socket = new WebSocket(wsUrl);
    socket.onopen = () => {
      connected.value = true;
      lastError.value = null;
    };
    socket.onclose = () => {
      connected.value = false;
      scheduleReconnect();
    };
    socket.onerror = () => {
      lastError.value =
        import.meta.env.DEV
          ? "Sem conexão com o backend. Execute: python web.py"
          : "Falha na conexão WebSocket";
    };
    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data);
      if (payload.type === "state_update") {
        state.value = payload as StateUpdate;
      } else if (payload.type === "error") {
        lastError.value = payload.message;
      }
    };
  }

  onMounted(connect);
  onUnmounted(() => {
    shouldReconnect = false;
    if (reconnectTimer) window.clearTimeout(reconnectTimer);
    socket?.close();
  });

  return { state, connected, lastError, sendCommand };
}
