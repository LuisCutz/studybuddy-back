import os
import httpx
from langchain_core.embeddings import Embeddings

from app.services.llm.base import ILLMService

class OllamaService(ILLMService):
    def __init__(self):
        # Por defecto Ollama corre en el puerto 11434
        self.host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3") # O gemma, mistral, etc.
        print(f"🦙 [LLM] Iniciando motor: Ollama (Modelo: {self.model})")

    async def generate_response(self, prompt: str) -> str:
        """Hace una petición POST a la API local de Ollama."""
        # --- (Código comentado hasta que instalemos Ollama) ---
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         f"{self.host}/api/generate",
        #         json={"model": self.model, "prompt": prompt, "stream": False}
        #     )
        #     return response.json()["response"]
        return f"[Ollama dice]: Respuesta simulada localmente para: {prompt}"

    async def generate_summary(self, text: str) -> str:
        prompt = f"Resume el siguiente texto en viñetas:\n\n{text}"
        return await self.generate_response(prompt)
    
    def get_embeddings(self) -> Embeddings:
        from langchain_ollama import OllamaEmbeddings
        return OllamaEmbeddings(
            base_url=self.host,
            model=os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text:latest")
        )