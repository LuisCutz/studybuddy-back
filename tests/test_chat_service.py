import unittest

from app.services.chat_service import ChatService


class ChatServiceTests(unittest.TestCase):
    def test_build_prompt_includes_context_and_history(self):
        service = ChatService(db=None)

        prompt = service._build_prompt(
            user_message="¿Qué dice el documento?",
            context_text="Fragmento relevante del documento",
            history=[{"role": "user", "content": "Hola"}],
            citations=[{"document_id": "doc-1", "title": "Documento A"}],
        )

        self.assertIn("Fragmento relevante del documento", prompt)
        self.assertIn("Hola", prompt)
        self.assertIn("¿Qué dice el documento?", prompt)
        self.assertIn("Documento A", prompt)


if __name__ == "__main__":
    unittest.main()
