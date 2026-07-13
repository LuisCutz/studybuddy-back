import uuid
import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import get_current_user
from app.repositories.invitation_repository import InvitationRepository
from app.models.invitation import Invitation
from app.models.room import StudyRoom
from app.models.user import User
from app.models.study_room_member import StudyRoomMember
from app.schemas.organization import OrganizationCreate, OrganizationUpdate, OrganizationResponse
from app.schemas.invitation import InvitationCreate, InvitationResponse, AcceptInvitationRequest
from app.services.email_service import EmailService

router = APIRouter()


@router.get("/health", summary="Check Organizations API Health")
async def organizations_health_check():
    return {
        "status": "ok",
        "module": "Organizations API",
        "version": "v1",
        "visibility": "private",
        "requires_jwt": True,
        "documentation": {
            "swagger_url": "/docs",
            "openapi_json_url": "/openapi.json",
        },
    }

# Listar organizaciones
@router.get("/", response_model=list[OrganizationResponse], summary="List user's organizations")
async def list_organizations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(StudyRoom)
        .join(StudyRoomMember, StudyRoom.id == StudyRoomMember.room_id)
        .where(StudyRoomMember.user_id == current_user.id)
    )
    
    result = await db.execute(stmt)
    return list(result.scalars().all())

@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED, summary="Create a new organization")
async def create_organization(
    payload: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    new_room = StudyRoom(
        name=payload.name,
        description=payload.description,
        tenant_id="pending"
    )
    db.add(new_room)
    await db.flush()

    new_room.tenant_id = f"room_{new_room.id}"
    
    membership = StudyRoomMember(
        user_id=current_user.id,
        room_id=new_room.id,
        role="admin"
    )
    db.add(membership)
    
    await db.commit()
    await db.refresh(new_room)

    return new_room

# Actualizar organización
@router.put("/{org_id}", response_model=OrganizationResponse, summary="Update organization details")
async def update_organization(org_id: uuid.UUID, payload: OrganizationUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StudyRoom).where(StudyRoom.id == org_id))
    room = result.scalar_one_or_none()
    
    if not room:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    
    if payload.name is not None:
        room.name = payload.name
    if payload.description is not None:
        room.description = payload.description
        
    db.add(room)
    await db.commit()
    await db.refresh(room)
    return room

# Enviar invitaciones
@router.post("/{org_id}/invitations", response_model=InvitationResponse, summary="Create and send an invitation")
async def create_invitation(org_id: uuid.UUID, payload: InvitationCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StudyRoom).where(StudyRoom.id == org_id))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="Organización no encontrada")

    inv_repo = InvitationRepository(db)
    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(days=7)

    new_invitation = Invitation(
        room_id=org_id,
        email=payload.email,
        token=token,
        role=payload.role,
        expires_at=expires
    )
    
    await inv_repo.save(new_invitation)
    await db.commit()
    await db.refresh(new_invitation)
    
    try:
        await EmailService.send_invitation_email(
            email_to=new_invitation.email,
            room_name=room.name,
            token=new_invitation.token
        )
    except Exception as e:
        print(f"Error enviando correo de invitación: {e}")

    return new_invitation

# Eliminar invitaciones vencidas
@router.delete("/invitations/expired", summary="Delete expired invitations")
async def delete_expired_invitations(db: AsyncSession = Depends(get_db)):
    inv_repo = InvitationRepository(db)
    await inv_repo.delete_expired(datetime.utcnow())
    await db.commit()
    return {"message": "Invitaciones vencidas eliminadas correctamente."}

# Aceptar invitaciones
@router.post("/invitations/accept", summary="Accept an invitation via token")
async def accept_invitation(payload: AcceptInvitationRequest, db: AsyncSession = Depends(get_db)):
    inv_repo = InvitationRepository(db)
    invitation = await inv_repo.get_by_token(payload.token)
    
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitación inválida o no encontrada.")
    
    if invitation.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Esta invitación ya ha expirado.")
        
    if invitation.status == "accepted":
        raise HTTPException(status_code=400, detail="Esta invitación ya fue aceptada previamente.")

    invitation.status = "accepted"
    await inv_repo.save(invitation)

    membership = StudyRoomMember(
        user_id=payload.user_id,
        room_id=invitation.room_id,
        role=invitation.role
    )
    db.add(membership)
    await db.commit()
    
    return {
        "message": "Invitación aceptada con éxito. Usuario agregado a la organización.", 
        "organization_id": invitation.room_id,
        "role_granted": invitation.role
    }