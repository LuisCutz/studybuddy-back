from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.organization import Organization

class OrganizationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> list[Organization]:
        # Obtiene todas las organizaciones
        result = await self.db.execute(select(Organization))
        return list(result.scalars().all())

    async def get_by_id(self, org_id: str) -> Organization | None:
        # Busca una organización específica.
        result = await self.db.execute(select(Organization).where(Organization.id == org_id))
        return result.scalar_one_or_none()

    async def save(self, org: Organization) -> Organization:
        # Crea o actualiza una organización
        self.db.add(org)
        await self.db.flush()
        return org