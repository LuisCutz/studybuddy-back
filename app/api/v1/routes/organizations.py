import uuid
import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.invitation_repository import InvitationRepository
from app.models.invitation import Invitation
from app.models.room import StudyRoom
from app.models.study_room_member import StudyRoomMember
from app.schemas.organization import OrganizationUpdate, OrganizationResponse
from app.schemas.invitation import InvitationCreate, InvitationResponse, AcceptInvitationRequest

router = APIRouter()

# Listar organizaciones
@router.get("/", response_model=list[OrganizationResponse], summary="List all organizations")
async def list_organizations(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StudyRoom))
    return list(result.scalars().all())

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
    
    # TODO: Conectar servicio SMTP para mandar correo
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