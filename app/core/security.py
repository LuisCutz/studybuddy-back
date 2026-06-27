import os
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User

security = HTTPBearer(auto_error=False)


def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(user_id: str | UUID, tenant_id: str | UUID | None = None, role: str | None = None) -> str:
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id) if tenant_id is not None else None,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing credentials")

    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == UUID(str(user_id))))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


def require_room_access(*required_roles: str):
    allowed_roles = {normalize_role(role) for role in required_roles}

    async def dependency(
        room_id: str | UUID,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        from app.models.room import StudyRoom
        from app.models.study_room_member import StudyRoomMember

        room_uuid = UUID(str(room_id))
        room_result = await db.get(StudyRoom, room_uuid)
        if room_result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Study room not found")

        if current_user.tenant_id != room_result.tenant_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: room belongs to another tenant")

        membership_result = await db.execute(
            select(StudyRoomMember).where(
                StudyRoomMember.user_id == current_user.id,
                StudyRoomMember.room_id == room_uuid,
            )
        )
        membership = membership_result.scalar_one_or_none()
        if membership is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: user is not a room member")

        normalized_role = normalize_role(membership.role)
        if allowed_roles and normalized_role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: insufficient role")

        return current_user

    return dependency


def normalize_role(role: str | None) -> str:
    if role is None:
        return ""
    aliases = {
        "admin": "admin",
        "administrator": "admin",
        "administrador": "admin",
        "teacher": "profesor",
        "profesor": "profesor",
        "profesora": "profesor",
        "student": "alumno",
        "alumno": "alumno",
        "alumna": "alumno",
    }
    return aliases.get(role.lower(), role.lower())
