from pydantic import BaseModel, EmailStr
import uuid


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginResponse(TokenResponse):
    user_id: str
    tenant_id: str | None = None


class GoogleLoginRequest(BaseModel):
    token: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    name: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str