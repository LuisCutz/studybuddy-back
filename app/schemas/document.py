import uuid
from datetime import date
from pydantic import BaseModel, Field

class DocumentResponse(BaseModel):
    id: uuid.UUID
    room_id: uuid.UUID
    title: str
    file_path: str
    status: str
    uploaded_at: date

    class Config:
        from_attributes = True