import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.invitation_repository import InvitationRepository
from app.models.invitation import Invitation
from app.schemas.organization import OrganizationUpdate, OrganizationResponse
from app.schemas.invitation import InvitationCreate, InvitationResponse, AcceptInvitationRequest
from app.models.organization import Organization

router = APIRouter()

# Listar organizaciones
@router.get("/", response_model=list[OrganizationResponse], summary="List all organizations")
async def list_organizations(db: AsyncSession = Depends(get_db)):
    org_repo = OrganizationRepository(db)
    return await org_repo.get_all()

# Crear nueva organización
@router.post("/", response_model=OrganizationResponse, summary="Create a new organization", status_code=status.HTTP_201_CREATED)
async def create_organization(payload: OrganizationUpdate, db: AsyncSession = Depends(get_db)):
    org_repo = OrganizationRepository(db)
    
    import uuid
    new_org_id = f"org_{uuid.uuid4()}"
    
    new_org = Organization(
        id=new_org_id,
        name=payload.name,
        description=payload.description
    )
    return await org_repo.save(new_org)

# Actualizar organización
@router.put("/{org_id}", response_model=OrganizationResponse, summary="Update organization details")
async def update_organization(org_id: str, payload: OrganizationUpdate, db: AsyncSession = Depends(get_db)):
    org_repo = OrganizationRepository(db)
    org = await org_repo.get_by_id(org_id)
    
    if not org:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    
    if payload.name is not None:
        org.name = payload.name
    if payload.description is not None:
        org.description = payload.description
        
    return await org_repo.save(org)

# Enviar invitaciones
@router.post("/{org_id}/invitations", response_model=InvitationResponse, summary="Create and send invitation")
async def create_invitation(org_id: str, payload: InvitationCreate, db: AsyncSession = Depends(get_db)):
    org_repo = OrganizationRepository(db)
    org = await org_repo.get_by_id(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organización no encontrada")

    inv_repo = InvitationRepository(db)
    
    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(days=7)

    new_invitation = Invitation(
        organization_id=org_id,
        email=payload.email,
        token=token,
        role=payload.role,
        expires_at=expires
    )
    
    await inv_repo.save(new_invitation)
    
    # TODO: Conectar servicio SMTP para mandar correo con el token
    
    return new_invitation

# Eliminar invitaciones vencidas
@router.delete("/invitations/expired", summary="Delete expired invitations")
async def delete_expired_invitations(db: AsyncSession = Depends(get_db)):
    inv_repo = InvitationRepository(db)
    await inv_repo.delete_expired(datetime.utcnow())
    return {"message": "Invitaciones vencidas eliminadas correctamente."}

# Aceptar invitaciones
@router.post("/invitations/accept", summary="Accept an invitation using token")
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
    
    return {
        "message": "Invitación aceptada con éxito.", 
        "organization_id": invitation.organization_id,
        "role_granted": invitation.role
    }