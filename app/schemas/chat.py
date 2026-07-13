import uuid
from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class ChatSessionCreate(BaseModel):
    room_id: uuid.UUID
    name: str | None = None
    document_ids: list[uuid.UUID] = Field(default_factory=list)


class ChatSessionUpdate(BaseModel):
    name: str | None = None
    document_ids: list[uuid.UUID] | None = None


class ChatMessageCreate(BaseModel):
    content: str


class DocumentSummary(BaseModel):
    id: uuid.UUID
    title: str
    status: str | None = None

    class Config:
        from_attributes = True


class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    citations: list[dict[str, Any]] | None = None
    created_at: date | None = None

    class Config:
        from_attributes = True


class ChatSessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    room_id: uuid.UUID
    name: str
    started_at: date
    documents: list[DocumentSummary] = Field(default_factory=list)

    class Config:
        from_attributes = True


class ChatMessageSendResponse(BaseModel):
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse
