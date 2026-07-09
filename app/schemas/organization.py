import uuid
from typing import Optional
from pydantic import BaseModel

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class OrganizationResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    tenant_id: str