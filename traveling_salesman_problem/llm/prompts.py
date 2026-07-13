"""Templates de prompt para geração LLM."""

from __future__ import annotations

from typing import List, Literal, Optional

GenerateType = Literal["instructions", "daily_report", "weekly_report", "improvements"]

_SYSTEM_BASE = (
    "Você é um assistente de logística hospitalar. "
    "Use APENAS os dados do bloco CONTEXTO. "
    "Se a informação não estiver no contexto, diga que não sabe. "
    "Responda em português brasileiro em Markdown estruturado."
)

_PROMPTS: dict[str, str] = {
    "instructions": _SYSTEM_BASE
    + " Gere instruções passo a passo para motoristas e equipes de entrega, por veículo e por viagem.",
    "daily_report": _SYSTEM_BASE
    + " Gere um relatório operacional diário com métricas, destaques positivos e alertas.",
    "weekly_report": _SYSTEM_BASE
    + " Consolide o histórico da sessão em um relatório semanal de eficiência de rotas e uso de recursos.",
    "improvements": _SYSTEM_BASE
    + " Analise padrões nos dados e sugira melhorias concretas no processo de entregas.",
    "chat": _SYSTEM_BASE
    + " Responda perguntas sobre rotas, entregas e veículos de forma concisa.",
}


def build_messages(
    kind: str,
    context_json: str,
    *,
    user_message: Optional[str] = None,
    history: Optional[List[dict]] = None,
) -> List[dict]:
    system = _PROMPTS.get(kind, _PROMPTS["chat"])
    messages: List[dict] = [{"role": "system", "content": system}]
    if history:
        messages.extend(history)
    if kind == "chat" and user_message:
        messages.append(
            {
                "role": "user",
                "content": f"CONTEXTO:\n{context_json}\n\nPERGUNTA:\n{user_message}",
            }
        )
    else:
        messages.append(
            {
                "role": "user",
                "content": f"CONTEXTO:\n{context_json}\n\nGere a resposta solicitada.",
            }
        )
    return messages
