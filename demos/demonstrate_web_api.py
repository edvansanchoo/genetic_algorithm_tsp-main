"""Demonstração da API Web (WebSocket + REST LLM).

Requer o backend em execução: python web.py

Uso:
    python -m demos.demonstrate_web_api
    python -m demos.demonstrate_web_api --generations 3
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

try:
    import httpx
    import websockets
except ImportError:
    print("Instale dependências: pip install httpx websockets")
    sys.exit(1)

BASE_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000/ws"


async def demo_websocket(generations: int) -> None:
    print("\n--- WebSocket /ws ---")
    async with websockets.connect(WS_URL) as ws:
        payload = json.loads(await ws.recv())
        print(f"Conectado. Geração inicial: {payload['generation']}")
        print(f"Métricas: fitness={payload['metrics']['fitness']}, "
              f"dist={payload['metrics']['distance']}")

        await ws.send(json.dumps({"action": "pause"}))
        await ws.recv()
        print("Simulação pausada.")

        await ws.send(json.dumps({
            "action": "set_param",
            "key": "mutation",
            "value": 0.2,
        }))
        await ws.recv()
        print("Taxa de mutação ajustada para 0.2.")

        await ws.send(json.dumps({"action": "resume"}))
        for _ in range(generations):
            payload = json.loads(await ws.recv())
        print(f"Após {generations} updates: geração {payload['generation']}, "
              f"fitness={payload['metrics']['fitness']}")


def demo_llm_health() -> None:
    print("\n--- REST GET /api/llm/health ---")
    try:
        response = httpx.get(f"{BASE_URL}/api/llm/health", timeout=5.0)
        print(f"Status: {response.status_code}")
        print(f"Corpo:  {response.json()}")
    except httpx.ConnectError:
        print("Backend não está rodando. Execute: python web.py")


def demo_llm_export() -> None:
    print("\n--- REST POST /api/llm/export ---")
    try:
        response = httpx.post(
            f"{BASE_URL}/api/llm/export",
            json={"content": "# Demo\n\nRelatório de teste.", "format": "md"},
            timeout=5.0,
        )
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        print(f"Tamanho: {len(response.content)} bytes")
    except httpx.ConnectError:
        print("Backend não está rodando.")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Demo da API Web VRP")
    parser.add_argument("--generations", type=int, default=2, help="Updates WS a aguardar")
    args = parser.parse_args()

    print("=== Demonstração da API Web ===")
    print(f"Backend esperado em {BASE_URL}")

    try:
        await demo_websocket(args.generations)
    except (ConnectionRefusedError, OSError):
        print("\nWebSocket: backend não disponível. Execute: python web.py")

    demo_llm_health()
    demo_llm_export()
    print("\nDocumentação completa: docs/API.md")


if __name__ == "__main__":
    asyncio.run(main())
