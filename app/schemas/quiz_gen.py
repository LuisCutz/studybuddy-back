from pydantic import BaseModel, Field

class GeneratedQuestion(BaseModel):
    type: str = Field(description="Siempre debe ser 'multiple_choice'")
    prompt: str = Field(description="La pregunta clara y directa")
    options: list[str] = Field(description="Un arreglo con exactamente 4 opciones posibles")
    correct_answer: str = Field(description="La respuesta correcta exacta (debe coincidir letra por letra con una de las opciones)")

class GeneratedQuiz(BaseModel):
    title: str = Field(description="Un título corto y atractivo para el quiz")
    topic: str = Field(description="El tema principal del documento")
    questions: list[GeneratedQuestion] = Field(description="Lista de preguntas generadas")