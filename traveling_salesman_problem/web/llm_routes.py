"""Endpoints REST para integração LLM."""

from __future__ import annotations

from typing import Callable, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from traveling_salesman_problem.llm.export import PdfUnavailableError, export_markdown, export_pdf
from traveling_salesman_problem.llm.ollama_client import OllamaOfflineError, OllamaTimeoutError
from traveling_salesman_problem.llm.prompts import GenerateType


class GenerateRequest(BaseModel):
    type: GenerateType
    vehicle_id: Optional[int] = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    history: List[dict] = Field(default_factory=list)


class ExportRequest(BaseModel):
    content: str = Field(min_length=1)
    format: Literal["md", "pdf"] = "md"
    filename: Optional[str] = None


def create_llm_router(get_service: Callable):
    router = APIRouter(prefix="/api/llm", tags=["llm"])

    @router.get("/health")
    async def health(service=Depends(get_service)):
        try:
            return await service.health()
        except OllamaOfflineError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except OllamaTimeoutError as exc:
            raise HTTPException(status_code=504, detail=str(exc)) from exc

    @router.post("/generate")
    async def generate(body: GenerateRequest, service=Depends(get_service)):
        try:
            return await service.generate(body.type, vehicle_id=body.vehicle_id)
        except OllamaOfflineError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except OllamaTimeoutError as exc:
            raise HTTPException(status_code=504, detail=str(exc)) from exc

    @router.post("/chat")
    async def chat(body: ChatRequest, service=Depends(get_service)):
        try:
            return await service.chat(body.message, history=body.history)
        except OllamaOfflineError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except OllamaTimeoutError as exc:
            raise HTTPException(status_code=504, detail=str(exc)) from exc

    @router.post("/export")
    async def export_report(body: ExportRequest):
        name = body.filename or "relatorio-vrp"
        try:
            if body.format == "md":
                data, media_type, filename = export_markdown(body.content, f"{name}.md")
            else:
                data, media_type, filename = export_pdf(body.content, f"{name}.pdf")
        except PdfUnavailableError as exc:
            raise HTTPException(status_code=501, detail=str(exc)) from exc
        return Response(
            content=data,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    return router
