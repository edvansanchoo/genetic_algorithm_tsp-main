"""Servidor FastAPI para o dashboard Web."""

from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from traveling_salesman_problem.web.simulation_service import SimulationService


def create_app(service: SimulationService) -> FastAPI:
    app = FastAPI(title="VRP Hospitalar Web")
    clients: set[WebSocket] = set()
    dist = Path("frontend/dist")

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
