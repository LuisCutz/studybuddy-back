from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

class FlashcardBase(BaseModel):
    front: str
    back: str

class FlashcardCreate(FlashcardBase):
    pass

class FlashcardResponse(FlashcardBase):
    id: UUID
    deck_id: UUID

    class Config:
        from_attributes = True

class FlashcardLLMEditRequest(BaseModel):
    instructions: str

class DeckCreateEmpty(BaseModel):
    subject_id: UUID
    title: str
    description: Optional[str] = None

class DeckGenerateRequest(BaseModel):
    document_id: UUID
    num_cards: int = 10
    description: Optional[str] = None

class DeckUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

class DeckResponse(BaseModel):
    id: UUID
    subject_id: UUID
    user_id: UUID
    title: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

class DeckWithCardsResponse(DeckResponse):
    flashcards: List[FlashcardResponse] = []