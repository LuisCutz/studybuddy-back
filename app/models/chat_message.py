import uuid

from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class ChatMessage(Base):
	__tablename__ = "chat_message"

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	session_id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True),
		ForeignKey("chat_session.id", ondelete="CASCADE"),
		nullable=False,
		index=True,
	)
	role: Mapped[str] = mapped_column(String(50), nullable=False)
	content: Mapped[str] = mapped_column(Text, nullable=False)
	citations: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)

	session: Mapped["ChatSession"] = relationship(back_populates="messages")