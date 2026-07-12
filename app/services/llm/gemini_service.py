import os
from langchain_core.embeddings import Embeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from typing import AsyncGenerator

from app.schemas.quiz_gen import GeneratedQuiz
from app.schemas.flashcard_gen import FlashcardFormat, FlashcardListFormat
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
    
    async def generate_streaming_response(self, prompt: str) -> AsyncGenerator[str, None]:
        # Envía el prompt al modelo y devuelve los pedazos de texto en tiempo real.
        async for chunk in self.llm.astream(prompt):
            yield chunk.content

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

    async def generate_quiz(self, text: str, num_questions: int = 5) -> dict:
        # Usa Gemini para generar un quiz estructurado.
        parser = JsonOutputParser(pydantic_object=GeneratedQuiz)
        
        template = """
        Eres un profesor experto diseñando evaluaciones. 
        Basándote ÚNICAMENTE en el siguiente texto, genera un quiz de {num_questions} preguntas de opción múltiple.
        
        TEXTO:
        {text}
        
        INSTRUCCIONES DE FORMATO:
        {format_instructions}
        """
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["num_questions", "text"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )
        
        chain = prompt | self.llm | parser
        return await chain.ainvoke({"num_questions": num_questions, "text": text})
    
    async def generate_flashcards(self, text: str, num_cards: int) -> dict:
        parser = JsonOutputParser(pydantic_object=FlashcardListFormat)
        
        template = """
        Eres un experto creando material de estudio. 
        Tu tarea es extraer los conceptos más importantes y generar {num_cards} flashcards a partir del texto proporcionado.
        
        TEXTO:
        {text}
        
        INSTRUCCIONES DE FORMATO:
        {format_instructions}
        """
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["num_cards", "text"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )
        
        chain = prompt | self.llm | parser
        return await chain.ainvoke({"num_cards": num_cards, "text": text})

    async def edit_flashcard(self, front: str, back: str, instructions: str) -> dict:
        parser = JsonOutputParser(pydantic_object=FlashcardFormat)
        
        template = """
        Eres un asistente de estudio. Modifica la siguiente flashcard siguiendo EXACTAMENTE las instrucciones del usuario.
        
        FRENTE ACTUAL: {front}
        REVERSO ACTUAL: {back}
        INSTRUCCIONES DEL USUARIO: {instructions}
        
        INSTRUCCIONES DE FORMATO:
        {format_instructions}
        """
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["front", "back", "instructions"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )
        
        chain = prompt | self.llm | parser
        return await chain.ainvoke({
            "front": front, 
            "back": back, 
            "instructions": instructions
        })