from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.session import get_db
from app.models.user import User
from app.models.room import StudyRoom
from app.models.study_room_member import StudyRoomMember
from app.schemas.user import LoginRequest, RegisterRequest, TokenResponse

router = APIRouter()
    
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_user(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El correo ya está registrado.")

    user = User(
        name=payload.name,
        email=payload.email,
        password=get_password_hash(payload.password)
    )
    db.add(user)
    await db.flush()

    new_tenant_id = f"org_{user.id}"

    default_room = StudyRoom(
        name=f"Sala Principal de {user.name}",
        description="Tu espacio de estudio personal",
        tenant_id=new_tenant_id
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

    token = create_access_token(user_id=str(user.id), tenant_id=new_tenant_id, role="admin")
    return TokenResponse(access_token=token, token_type="bearer")


@router.post("/login", response_model=TokenResponse)
async def login_user(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    result = await db.execute(
        select(User)
        .options(selectinload(User.room_memberships).selectinload(StudyRoomMember.room))
        .where(User.email == payload.email)
    )
    user = result.scalar_one_or_none()
    
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