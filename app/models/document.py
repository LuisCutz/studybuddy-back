import uuid

from sqlalchemy import Date, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Document(Base):
    __tablename__ = "document"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("study_room.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    uploaded_at: Mapped[object] = mapped_column(Date, nullable=False, server_default=func.current_date())

    room: Mapped["StudyRoom"] = relationship(back_populates="documents")
    chat_sessions: Mapped[list["ChatSession"]] = relationship(
        secondary="chat_session_document",
        back_populates="documents",
        cascade="save-update, merge",
    )
