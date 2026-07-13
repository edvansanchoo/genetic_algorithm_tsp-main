"""Testes do cliente Ollama."""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from traveling_salesman_problem.llm.config import LlmConfig
from traveling_salesman_problem.llm.ollama_client import OllamaClient, OllamaOfflineError


class OllamaClientTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.config = LlmConfig(
            base_url="http://127.0.0.1:11434",
            model="gemma4:e2b",
            timeout=30.0,
            max_context_tokens=2000,
        )

    async def test_chat_returns_assistant_content(self):
        client = OllamaClient(self.config)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "message": {"content": "# Instruções\nPasso 1"}
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            client._client,
            "post",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await client.chat([{"role": "user", "content": "teste"}])
        self.assertIn("Instruções", result)

    async def test_health_check_detects_missing_model(self):
        client = OllamaClient(self.config)
        mock_response = MagicMock()
        mock_response.json.return_value = {"models": [{"name": "other:tag"}]}
        mock_response.raise_for_status = MagicMock()

        with patch.object(
            client._client,
            "get",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await client.health_check()
        self.assertFalse(result["ok"])
        self.assertIn("gemma4:e2b", result["message"])

    async def test_offline_raises(self):
        client = OllamaClient(self.config)
        with patch.object(
            client._client,
            "get",
            new_callable=AsyncMock,
            side_effect=httpx.ConnectError("offline"),
        ):
            with self.assertRaises(OllamaOfflineError):
                await client.health_check()


if __name__ == "__main__":
    unittest.main()
