import { ref } from "vue";

const API_BASE = import.meta.env.DEV ? "http://127.0.0.1:8000" : "";

export type GenerateType =
  | "instructions"
  | "daily_report"
  | "weekly_report"
  | "improvements";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export function useLlmApi() {
  const loading = ref(false);
  const error = ref<string | null>(null);
  const lastOutput = ref("");
  const chatHistory = ref<ChatMessage[]>([]);
  const ollamaStatus = ref<{
    ok: boolean;
    model?: string;
    message?: string;
  } | null>(null);

  async function health() {
    try {
      const res = await fetch(`${API_BASE}/api/llm/health`);
      const data = await res.json();
      ollamaStatus.value = data;
      return data;
    } catch {
      ollamaStatus.value = { ok: false, message: "Backend indisponível" };
      return ollamaStatus.value;
    }
  }

  async function generate(type: GenerateType, vehicleId?: number | null) {
    loading.value = true;
    error.value = null;
    try {
      const res = await fetch(`${API_BASE}/api/llm/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type, vehicle_id: vehicleId ?? null }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? `Erro ${res.status}`);
      }
      const data = await res.json();
      lastOutput.value = data.content ?? "";
      return data;
    } catch (exc) {
      error.value = exc instanceof Error ? exc.message : "Erro desconhecido";
      throw exc;
    } finally {
      loading.value = false;
    }
  }

  async function chat(message: string) {
    loading.value = true;
    error.value = null;
    try {
      const res = await fetch(`${API_BASE}/api/llm/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, history: chatHistory.value }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? `Erro ${res.status}`);
      }
      const data = await res.json();
      chatHistory.value = data.history ?? chatHistory.value;
      return data;
    } catch (exc) {
      error.value = exc instanceof Error ? exc.message : "Erro desconhecido";
      throw exc;
    } finally {
      loading.value = false;
    }
  }

  async function exportReport(content: string, format: "md" | "pdf") {
    const res = await fetch(`${API_BASE}/api/llm/export`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content, format }),
    });
    if (!res.ok) {
      if (res.status === 501 && format === "pdf") {
        window.print();
        return;
      }
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail ?? `Erro ${res.status}`);
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = format === "md" ? "relatorio-vrp.md" : "relatorio-vrp.pdf";
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return {
    loading,
    error,
    lastOutput,
    chatHistory,
    ollamaStatus,
    health,
    generate,
    chat,
    exportReport,
  };
}
