import uuid
from datetime import date
from typing import Optional
from pydantic import BaseModel

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class OrganizationResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: date