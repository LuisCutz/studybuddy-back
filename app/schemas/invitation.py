import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr

class InvitationCreate(BaseModel):
    email: EmailStr
    role: str = "alumno"

class InvitationResponse(BaseModel):
    id: uuid.UUID
    organization_id: str
    email: EmailStr
    token: str
    role: str
    expires_at: datetime
    status: str

class AcceptInvitationRequest(BaseModel):
    token: str