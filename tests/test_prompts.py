"""Testes dos templates de prompt LLM."""

import unittest

from traveling_salesman_problem.llm.prompts import build_messages


class PromptsTests(unittest.TestCase):
    def test_instructions_includes_context_and_portuguese(self):
        messages = build_messages("instructions", '{"geracao": 1}')
        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("motorista", messages[0]["content"].lower())
        self.assertIn("CONTEXTO:", messages[1]["content"])
        self.assertIn('{"geracao": 1}', messages[1]["content"])

    def test_chat_includes_user_message(self):
        messages = build_messages(
            "chat",
            "{}",
            user_message="Qual veículo tem mais carga?",
            history=[{"role": "user", "content": "Olá"}],
        )
        roles = [message["role"] for message in messages]
        self.assertIn("user", roles)
        self.assertTrue(
            any("Qual veículo" in message.get("content", "") for message in messages)
        )

    def test_all_generate_types_have_system_prompt(self):
        for kind in ("instructions", "daily_report", "weekly_report", "improvements"):
            messages = build_messages(kind, "{}")
            self.assertGreater(len(messages[0]["content"]), 50)


if __name__ == "__main__":
    unittest.main()
