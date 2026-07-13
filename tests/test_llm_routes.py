"""Testes dos endpoints REST LLM."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from traveling_salesman_problem.llm.ollama_client import OllamaOfflineError
from traveling_salesman_problem.web.llm_routes import create_llm_router


@pytest.fixture
def client():
    mock_service = MagicMock()
    mock_service.health = AsyncMock(
        return_value={"ok": True, "model": "test-model", "message": "ok"}
    )
    mock_service.generate = AsyncMock(
        return_value={"type": "instructions", "content": "# Instruções"}
    )
    mock_service.chat = AsyncMock(
        return_value={"reply": "Resposta", "history": [{"role": "user", "content": "oi"}]}
    )

    app = FastAPI()
    app.include_router(create_llm_router(lambda: mock_service))
    return TestClient(app), mock_service


def test_health_endpoint(client):
    test_client, _ = client
    response = test_client.get("/api/llm/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_generate_endpoint(client):
    test_client, mock_service = client
    response = test_client.post(
        "/api/llm/generate",
        json={"type": "daily_report"},
    )
    assert response.status_code == 200
    assert response.json()["content"] == "# Instruções"
    mock_service.generate.assert_awaited_once()


def test_chat_endpoint(client):
    test_client, _ = client
    response = test_client.post(
        "/api/llm/chat",
        json={"message": "Quantos veículos?"},
    )
    assert response.status_code == 200
    assert response.json()["reply"] == "Resposta"


def test_export_markdown(client):
    test_client, _ = client
    response = test_client.post(
        "/api/llm/export",
        json={"content": "# Relatório", "format": "md"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    assert b"# Relat" in response.content


def test_health_offline_returns_503():
    mock_service = MagicMock()
    mock_service.health = AsyncMock(side_effect=OllamaOfflineError("offline"))

    app = FastAPI()
    app.include_router(create_llm_router(lambda: mock_service))
    test_client = TestClient(app)
    response = test_client.get("/api/llm/health")
    assert response.status_code == 503
