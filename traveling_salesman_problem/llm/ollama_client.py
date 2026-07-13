"""Cliente HTTP async para Ollama."""

from __future__ import annotations

from typing import List

import httpx

from traveling_salesman_problem.llm.config import LlmConfig


class OllamaError(Exception):
    pass


class OllamaOfflineError(OllamaError):
    pass


class OllamaTimeoutError(OllamaError):
    pass


class OllamaClient:
    def __init__(self, config: LlmConfig) -> None:
        self.config = config
        self._client = httpx.AsyncClient(base_url=config.base_url, timeout=config.timeout)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def health_check(self) -> dict:
        try:
            response = await self._client.get("/api/tags")
            response.raise_for_status()
        except (httpx.ConnectError, httpx.NetworkError) as exc:
            raise OllamaOfflineError(
                "Ollama não está rodando. Execute: ollama serve"
            ) from exc
        except httpx.TimeoutException as exc:
            raise OllamaTimeoutError("Timeout ao conectar ao Ollama") from exc

        models = response.json().get("models", [])
        names = {model.get("name", "") for model in models}
        model_ok = any(self.config.model in name for name in names)
        if not model_ok:
            return {
                "ok": False,
                "model": self.config.model,
                "message": (
                    f"Modelo '{self.config.model}' não encontrado. "
                    f"Execute: ollama pull {self.config.model}"
                ),
            }
        return {"ok": True, "model": self.config.model, "message": "ok"}

    async def chat(self, messages: List[dict]) -> str:
        try:
            response = await self._client.post(
                "/api/chat",
                json={
                    "model": self.config.model,
                    "messages": messages,
                    "stream": False,
                },
            )
            response.raise_for_status()
        except (httpx.ConnectError, httpx.NetworkError) as exc:
            raise OllamaOfflineError(
                "Ollama não está rodando. Execute: ollama serve"
            ) from exc
        except httpx.TimeoutException as exc:
            raise OllamaTimeoutError(
                "Tempo esgotado aguardando resposta do modelo"
            ) from exc

        payload = response.json()
        return payload.get("message", {}).get("content", "").strip()
