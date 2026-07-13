"""Servidor FastAPI para o dashboard Web."""

from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from traveling_salesman_problem.llm.config import load_llm_config
from traveling_salesman_problem.llm.ollama_client import OllamaClient
from traveling_salesman_problem.llm.service import LlmService
from traveling_salesman_problem.web.llm_routes import create_llm_router
from traveling_salesman_problem.web.simulation_service import SimulationService


def create_app(service: SimulationService) -> FastAPI:
    app = FastAPI(title="VRP Hospitalar Web")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    clients: set[WebSocket] = set()
    dist = Path("frontend/dist")

    llm_config = load_llm_config()
    ollama_client = OllamaClient(llm_config)
    llm_service = LlmService(service, ollama_client)

    @app.on_event("shutdown")
    async def shutdown_llm() -> None:
        await ollama_client.aclose()

    app.include_router(create_llm_router(lambda: llm_service))

    async def broadcast(payload: dict) -> None:
        dead: list[WebSocket] = []
        for websocket in list(clients):
            try:
                await websocket.send_json(payload)
            except Exception:
                dead.append(websocket)
        for websocket in dead:
            clients.discard(websocket)

    @app.on_event("startup")
    async def startup() -> None:
        asyncio.create_task(service.run_loop(broadcast))

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        await websocket.accept()
        clients.add(websocket)
        await websocket.send_json(service.build_state_payload())
        try:
            while True:
                message = await websocket.receive_json()
                error = service.handle_command(message)
                if error:
                    await websocket.send_json({"type": "error", "message": error})
        except WebSocketDisconnect:
            clients.discard(websocket)

    if dist.exists():
        assets_dir = dist / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        @app.get("/")
        async def index() -> FileResponse:
            return FileResponse(dist / "index.html")

    return app
