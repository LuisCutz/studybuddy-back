from abc import ABC, abstractmethod
from typing import AsyncGenerator
from langchain_core.embeddings import Embeddings

class ILLMService(ABC):
    # Interfaz base para todos los servicios de LLM.

    @abstractmethod
    async def generate_response(self, prompt: str) -> str:
        # Genera texto a partir de un prompt simple.
        pass

    @abstractmethod
    async def generate_summary(self, text: str) -> str:
        # Genera un resumen estructurado del texto recibido.
        pass
    
    @abstractmethod
    def get_embeddings(self) -> Embeddings:
        # Retorna el motor de embeddings compatible con LangChain.
        pass

    @abstractmethod
    async def generate_streaming_response(self, prompt: str) -> AsyncGenerator[str, None]:
        # Genera una respuesta en tiempo real (token por token).
        pass

    @abstractmethod
    async def generate_quiz(self, text: str, num_questions: int = 5) -> dict:
        # Genera un quiz estructurado en JSON a partir de un texto.
        pass