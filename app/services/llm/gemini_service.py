import os
from langchain_core.embeddings import Embeddings
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from app.services.llm.base import ILLMService

class GeminiService(ILLMService):
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            print("[Warning] GEMINI_API_KEY no está configurada en tu archivo .env")
            
        print("[LLM] Iniciando motor: Google Gemini (gemini-2.5-flash)")
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=self.api_key,
            temperature=0.3
        )

    async def generate_response(self, prompt: str) -> str:
        # Envía el prompt a Gemini de forma asíncrona.
        response = await self.llm.ainvoke(prompt)
        return response.content

    async def generate_summary(self, text: str) -> str:
        # Usa Gemini para resumir el texto proporcionado.
        prompt = f"Resume el siguiente texto en viñetas claras y concisas, resaltando los puntos más importantes:\n\n{text}"
        return await self.generate_response(prompt)

    def get_embeddings(self) -> Embeddings:
        # Retorna el motor de embeddings de Google.
        return GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-001",
            google_api_key=self.api_key
        )