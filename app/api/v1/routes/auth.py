import os
import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.session import get_db
from app.models.user import User
from app.models.room import StudyRoom
from app.models.study_room_member import StudyRoomMember
from app.schemas.user import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import GoogleLoginRequest
from app.repositories.user_repository import UserRepository

router = APIRouter()
    
@router.get("/health", summary="Check Authentication API Health")
async def auth_health_check():
    return {
        "status": "ok",
        "module": "Authentication API",
        "version": "v1",
        "visibility": "public",
        "requires_jwt": False,
        "documentation": {
            "swagger_url": "/docs",
            "openapi_json_url": "/openapi.json"
        }
    }

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_user(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    user_repo = UserRepository(db)
    
    existing = await user_repo.get_by_email(payload.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El correo ya está registrado.")

    user = User(
        name=payload.name,
        email=payload.email,
        password=get_password_hash(payload.password)
    )
    await user_repo.save(user) 

    default_room = StudyRoom(
        name=f"Sala General de {user.name}",
        description="Tu espacio de estudio personal",
        tenant_id=f"room_{user.id}"
    )
    db.add(default_room)
    await db.flush()

    membership = StudyRoomMember(
        user_id=user.id,
        room_id=default_room.id,
        role="admin"
    )
    db.add(membership)
    
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user_id=str(user.id), tenant_id=default_room.tenant_id, role="admin")
    return TokenResponse(access_token=token, token_type="bearer")


@router.post("/login", response_model=TokenResponse)
async def login_user(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    user_repo = UserRepository(db)
    
    user = await user_repo.get_by_email_with_rooms(payload.email)
    
    if user is None or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Correo o contraseña incorrectos.")

    active_tenant_id = "default-tenant"
    active_role = "alumno"
    
    if user.room_memberships:
        first_membership = user.room_memberships[0]
        active_tenant_id = first_membership.room.tenant_id
        active_role = first_membership.role

    token = create_access_token(user_id=str(user.id), tenant_id=active_tenant_id, role=active_role)
    return TokenResponse(access_token=token, token_type="bearer")


@router.post("/google", response_model=TokenResponse)
async def google_auth(payload: GoogleLoginRequest, db: AsyncSession = Depends(get_db)):
    user_repo = UserRepository(db)
    
    try:
        id_info = id_token.verify_oauth2_token(
            payload.token, 
            google_requests.Request(), 
            os.getenv("GOOGLE_CLIENT_ID")
        )
        
        user_email = id_info.get("email")
        user_name = id_info.get("name")
        
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de Google inválido o expirado.")

    user = await user_repo.get_by_email_with_rooms(user_email)

    if not user:
        random_password = secrets.token_urlsafe(32) 
        
        new_user = User(
            name=user_name,
            email=user_email,
            password=get_password_hash(random_password)
        )
        await user_repo.save(new_user)
        
        default_room = StudyRoom(
            name=f"Sala General de {new_user.name}",
            description="Tu espacio de estudio personal",
            tenant_id=f"room_{new_user.id}"
        )
        db.add(default_room)
        await db.flush()

        membership = StudyRoomMember(
            user_id=new_user.id,
            room_id=default_room.id,
            role="admin"
        )
        db.add(membership)
        await db.commit()
        
        token = create_access_token(user_id=str(new_user.id), tenant_id=default_room.tenant_id, role="admin")
        return TokenResponse(access_token=token, token_type="bearer")

    else:
        active_tenant_id = "default-tenant"
        active_role = "alumno"
        
        if user.room_memberships:
            first_membership = user.room_memberships[0]
            active_tenant_id = first_membership.room.tenant_id
            active_role = first_membership.role

        token = create_access_token(user_id=str(user.id), tenant_id=active_tenant_id, role=active_role)
        return TokenResponse(access_token=token, token_type="bearer")