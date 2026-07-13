"""Testes dos templates de prompt LLM."""

from traveling_salesman_problem.llm.prompts import build_messages


def test_build_messages_includes_context():
    messages = build_messages("daily_report", '{"geracao": 1}')
    assert messages[0]["role"] == "system"
    assert "CONTEXTO" in messages[-1]["content"]
    assert '{"geracao": 1}' in messages[-1]["content"]


def test_chat_messages_include_user_question():
    messages = build_messages(
        "chat",
        "{}",
        user_message="Quantas entregas críticas?",
    )
    assert "PERGUNTA" in messages[-1]["content"]
    assert "Quantas entregas críticas?" in messages[-1]["content"]


def test_chat_preserves_history():
    history = [{"role": "user", "content": "oi"}]
    messages = build_messages("chat", "{}", user_message="tchau", history=history)
    assert messages[1] == history[0]
    assert len(messages) == 3


def test_all_generate_types_have_system_prompt():
    for kind in ("instructions", "daily_report", "weekly_report", "improvements", "chat"):
        messages = build_messages(kind, "{}")
        assert "logística hospitalar" in messages[0]["content"].lower()
