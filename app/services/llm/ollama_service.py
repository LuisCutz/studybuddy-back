import os
from langchain_core.embeddings import Embeddings
from langchain_ollama import ChatOllama, OllamaEmbeddings
from typing import AsyncGenerator

from app.services.llm.base import ILLMService

class OllamaService(ILLMService):
    def __init__(self):
        self.host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model_name = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        print(f"[LLM] Iniciando motor: Ollama (Modelo: {self.model_name})")
        
        self.llm = ChatOllama(
            model=self.model_name,
            base_url=self.host,
            temperature=0.3
        )

    async def generate_response(self, prompt: str) -> str:
        # Envía el prompt a Ollama de forma asíncrona.
        response = await self.llm.ainvoke(prompt)
        return response.content
    
    async def generate_streaming_response(self, prompt: str) -> AsyncGenerator[str, None]:
        # Envía el prompt al modelo y devuelve los pedazos de texto en tiempo real.
        async for chunk in self.llm.astream(prompt):
            yield chunk.content

    async def generate_summary(self, text: str) -> str:
        # Usa Ollama para resumir el texto proporcionado.
        prompt = f"Resume el siguiente texto en viñetas claras y concisas:\n\n{text}"
        return await self.generate_response(prompt)

    def get_embeddings(self) -> Embeddings:
        # Retorna el motor de embeddings de Ollama.
        return OllamaEmbeddings(
            model=os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text:latest"),
            base_url=self.host
        )