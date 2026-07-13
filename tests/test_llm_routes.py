"""Testes dos endpoints REST LLM."""

import unittest
from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from traveling_salesman_problem.web.llm_routes import create_llm_router


class LlmRoutesTests(unittest.TestCase):
    def setUp(self):
        self.llm_service = MagicMock()
        self.llm_service.health = AsyncMock(
            return_value={"ok": True, "model": "gemma4:e2b"}
        )
        self.llm_service.generate = AsyncMock(
            return_value={"type": "instructions", "content": "# OK"}
        )
        app = FastAPI()
        app.include_router(create_llm_router(lambda: self.llm_service))
        self.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/api/llm/health")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])

    def test_generate_endpoint(self):
        response = self.client.post(
            "/api/llm/generate",
            json={"type": "instructions"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("content", response.json())


if __name__ == "__main__":
    unittest.main()
