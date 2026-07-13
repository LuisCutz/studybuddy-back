import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.chat import ChatSession
    from app.models.document import Document
    from app.models.flashcard_deck import FlashcardDeck
    from app.models.invitation import Invitation
    from app.models.quiz import Quiz
    from app.models.study_room_member import StudyRoomMember
    from app.models.summary import Summary


class StudyRoom(Base):
    __tablename__ = "study_room"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tenant_id: Mapped[str] = mapped_column(String(100), nullable=False, default="default-tenant")

    members: Mapped[list["StudyRoomMember"]] = relationship(
        back_populates="room",
        cascade="all, delete-orphan",
    )
    documents: Mapped[list["Document"]] = relationship(back_populates="room", cascade="all, delete-orphan")
    summaries: Mapped[list["Summary"]] = relationship(back_populates="room", cascade="all, delete-orphan")
    quizzes: Mapped[list["Quiz"]] = relationship(back_populates="room", cascade="all, delete-orphan")
    flashcard_decks: Mapped[list["FlashcardDeck"]] = relationship(back_populates="room", cascade="all, delete-orphan")
    chat_sessions: Mapped[list["ChatSession"]] = relationship(back_populates="room", cascade="all, delete-orphan")

    invitations: Mapped[list["Invitation"]] = relationship(
        back_populates="room",
        cascade="all, delete-orphan"
    )