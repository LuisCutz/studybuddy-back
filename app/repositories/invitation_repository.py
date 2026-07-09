from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.invitation import Invitation

class InvitationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_token(self, token: str) -> Invitation | None:
        # Busca una invitación válida por su token.
        result = await self.db.execute(select(Invitation).where(Invitation.token == token))
        return result.scalar_one_or_none()

    async def save(self, invitation: Invitation) -> Invitation:
        # Guarda una nueva invitación.
        self.db.add(invitation)
        await self.db.flush()
        return invitation

    async def delete_expired(self, current_time: datetime):
        # Elimina las invitaciones vencidas de la base de datos.
        await self.db.execute(delete(Invitation).where(Invitation.expires_at < current_time))
        await self.db.flush()