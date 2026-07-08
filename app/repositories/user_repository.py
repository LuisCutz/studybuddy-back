from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.study_room_member import StudyRoomMember

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> User | None:
        # Busca un usuario por su correo electrónico.
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_email_with_rooms(self, email: str) -> User | None:
        # Busca un usuario y trae precargadas sus membresías y salas.
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.room_memberships).selectinload(StudyRoomMember.room))
            .where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def save(self, model_instance):
        # Guarda cualquier instancia en la base de datos.
        self.db.add(model_instance)
        await self.db.flush()
        return model_instance