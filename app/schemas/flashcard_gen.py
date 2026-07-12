from pydantic import BaseModel, Field

class FlashcardFormat(BaseModel):
    front: str = Field(description="La pregunta, concepto clave o término (frente de la tarjeta)")
    back: str = Field(description="La respuesta, definición o explicación (reverso de la tarjeta)")

class FlashcardListFormat(BaseModel):
    title: str = Field(description="Un título corto y descriptivo para el mazo de tarjetas")
    cards: list[FlashcardFormat] = Field(description="Lista de tarjetas generadas")