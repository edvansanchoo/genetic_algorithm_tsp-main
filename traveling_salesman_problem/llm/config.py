"""Configuração do módulo LLM via variáveis de ambiente."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class LlmConfig:
    base_url: str
    model: str
    timeout: float
    max_context_tokens: int


def load_llm_config() -> LlmConfig:
    return LlmConfig(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/"),
        model=os.getenv("OLLAMA_MODEL", "gemma4:e2b"),
        timeout=float(os.getenv("OLLAMA_TIMEOUT", "120")),
        max_context_tokens=int(os.getenv("LLM_MAX_CONTEXT_TOKENS", "2000")),
    )
