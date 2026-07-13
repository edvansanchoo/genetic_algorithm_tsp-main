"""Testes do cliente Ollama (mock HTTP)."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from traveling_salesman_problem.llm.config import LlmConfig
from traveling_salesman_problem.llm.ollama_client import (
    OllamaClient,
    OllamaOfflineError,
    OllamaTimeoutError,
)


@pytest.fixture
def config():
    return LlmConfig(
        base_url="http://localhost:11434",
        model="test-model",
        timeout=5.0,
        max_context_tokens=2000,
    )


@pytest.mark.asyncio
async def test_health_check_ok(config):
    client = OllamaClient(config)
    mock_response = MagicMock()
    mock_response.json.return_value = {"models": [{"name": "test-model:latest"}]}
    mock_response.raise_for_status = MagicMock()

    with patch.object(client._client, "get", new_callable=AsyncMock, return_value=mock_response):
        result = await client.health_check()

    assert result["ok"] is True
    await client.aclose()


@pytest.mark.asyncio
async def test_health_check_model_missing(config):
    client = OllamaClient(config)
    mock_response = MagicMock()
    mock_response.json.return_value = {"models": [{"name": "other:latest"}]}
    mock_response.raise_for_status = MagicMock()

    with patch.object(client._client, "get", new_callable=AsyncMock, return_value=mock_response):
        result = await client.health_check()

    assert result["ok"] is False
    await client.aclose()


@pytest.mark.asyncio
async def test_health_check_offline(config):
    client = OllamaClient(config)
    with patch.object(
        client._client,
        "get",
        new_callable=AsyncMock,
        side_effect=httpx.ConnectError("offline"),
    ):
        with pytest.raises(OllamaOfflineError):
            await client.health_check()
    await client.aclose()


@pytest.mark.asyncio
async def test_chat_returns_content(config):
    client = OllamaClient(config)
    mock_response = MagicMock()
    mock_response.json.return_value = {"message": {"content": "  Resposta  "}}
    mock_response.raise_for_status = MagicMock()

    with patch.object(client._client, "post", new_callable=AsyncMock, return_value=mock_response):
        content = await client.chat([{"role": "user", "content": "oi"}])

    assert content == "Resposta"
    await client.aclose()


@pytest.mark.asyncio
async def test_chat_timeout(config):
    client = OllamaClient(config)
    with patch.object(
        client._client,
        "post",
        new_callable=AsyncMock,
        side_effect=httpx.TimeoutException("timeout"),
    ):
        with pytest.raises(OllamaTimeoutError):
            await client.chat([])
    await client.aclose()
