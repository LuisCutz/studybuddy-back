import os
import secrets
from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from app.core.security import create_access_token, create_refresh_token, create_reset_token, get_password_hash, verify_password, get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.models.room import StudyRoom
from app.models.study_room_member import StudyRoomMember
from app.schemas.user import ForgotPasswordRequest, LoginRequest, RegisterRequest, ResetPasswordRequest, TokenResponse, UserResponse
from app.schemas.user import GoogleLoginRequest
from app.repositories.user_repository import UserRepository
from app.services.email_service import EmailService

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
async def register_user(payload: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)) -> TokenResponse:
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

    tenant_id = default_room.tenant_id
    role = membership.role

    access_token = create_access_token(user_id=str(user.id), tenant_id=tenant_id, role=role)
    refresh_token = create_refresh_token(user_id=str(user.id), tenant_id=tenant_id, role=role)
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 60 * 60
    )
    
    return TokenResponse(access_token=access_token, token_type="bearer")


@router.post("/login", response_model=TokenResponse)
async def login_user(payload: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)) -> TokenResponse:
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

    access_token = create_access_token(user_id=str(user.id), tenant_id=active_tenant_id, role=active_role)
    refresh_token = create_refresh_token(user_id=str(user.id), tenant_id=active_tenant_id, role=active_role)
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 60 * 60
    )
    
    return TokenResponse(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse, summary="Get current user info")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/refresh", response_model=TokenResponse, summary="Refresh access token")
async def refresh_token(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db)
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token no encontrado en las cookies. Inicia sesión nuevamente.")

    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Token inválido")
            
        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        role = payload.get("role")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Token malformado")
            
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expirado. Inicia sesión nuevamente.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Refresh token inválido. Inicia sesión nuevamente.")

    new_access_token = create_access_token(user_id=user_id, tenant_id=tenant_id, role=role)
    
    return TokenResponse(access_token=new_access_token, token_type="bearer")


@router.post("/forgot-password", summary="Solicitar recuperación de contraseña")
async def forgot_password(payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(payload.email)
    
    if user:
        reset_token = create_reset_token(email=user.email)
        try:
            await EmailService.send_reset_password_email(email_to=user.email, token=reset_token)
        except Exception as e:
            print(f"Error enviando correo de recuperación: {e}")

    return {"message": "Si el correo está registrado, recibirás un enlace de recuperación pronto."}

@router.post("/reset-password", summary="Restablecer contraseña con token")
async def reset_password(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    try:
        token_data = jwt.decode(payload.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        if token_data.get("type") != "reset":
            raise HTTPException(status_code=400, detail="Token inválido para esta operación.")
            
        email = token_data.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="El token ha expirado. Solicita uno nuevo.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Token inválido.")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(email)
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    user.password = get_password_hash(payload.new_password)
    await user_repo.save(user)
    await db.commit()

    return {"message": "Contraseña actualizada exitosamente. Ya puedes iniciar sesión."}



@router.post("/google", response_model=TokenResponse)
async def google_auth(payload: GoogleLoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
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
        
        access_token = create_access_token(user_id=str(new_user.id), tenant_id=default_room.tenant_id, role="admin")
        refresh_token = create_refresh_token(user_id=str(new_user.id), tenant_id=default_room.tenant_id, role="admin")

    else:
        active_tenant_id = "default-tenant"
        active_role = "alumno"
        
        if user.room_memberships:
            first_membership = user.room_memberships[0]
            active_tenant_id = first_membership.room.tenant_id
            active_role = first_membership.role

        access_token = create_access_token(user_id=str(user.id), tenant_id=active_tenant_id, role=active_role)
        refresh_token = create_refresh_token(user_id=str(user.id), tenant_id=active_tenant_id, role=active_role)

        response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 60 * 60
    )

    return TokenResponse(access_token=access_token, token_type="bearer")
    

@router.post("/logout", summary="Logout user and clear refresh token cookie")
async def logout(response: Response):
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=False, 
        samesite="lax"
    )
    return {"message": "Sesión cerrada correctamente y cookies limpiadas."}