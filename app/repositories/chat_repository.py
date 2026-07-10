import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chat import ChatSession
from app.models.chat_message import ChatMessage


class ChatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_session_for_user(self, session_id: uuid.UUID, user_id: uuid.UUID) -> ChatSession | None:
        result = await self.db.execute(
            select(ChatSession)
            .where(ChatSession.id == session_id, ChatSession.user_id == user_id)
            .options(selectinload(ChatSession.documents))
        )
        return result.scalar_one_or_none()

    async def list_sessions(self, user_id: uuid.UUID) -> list[ChatSession]:
        result = await self.db.execute(
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .options(selectinload(ChatSession.documents))
            .order_by(ChatSession.started_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, session: ChatSession) -> ChatSession:
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def save(self, entity) -> None:
        self.db.add(entity)
        await self.db.flush()

    async def delete(self, entity) -> None:
        await self.db.delete(entity)
        await self.db.flush()

    async def list_messages(self, session_id: uuid.UUID) -> list[ChatMessage]:
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_message_by_id(self, message_id: uuid.UUID) -> ChatMessage | None:
        result = await self.db.execute(select(ChatMessage).where(ChatMessage.id == message_id))
        return result.scalar_one_or_none()
