import os
from app.services.llm.base import ILLMService
from app.services.llm.gemini_service import GeminiService
from app.services.llm.ollama_service import OllamaService

def get_llm_service() -> ILLMService:
    # Fábrica que decide qué LLM instanciar basándose en las variables de entorno.
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()

    if provider == "ollama":
        return OllamaService()
    elif provider == "gemini":
        return GeminiService()
    else:
        raise ValueError(f"Proveedor de LLM no soportado: {provider}")