import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Subject(Base):
    __tablename__ = "subject"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("study_room.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    room: Mapped["StudyRoom"] = relationship(back_populates="subjects")
    documents: Mapped[list["Document"]] = relationship(back_populates="subject", cascade="all, delete-orphan")
    summaries: Mapped[list["Summary"]] = relationship(back_populates="subject", cascade="all, delete-orphan")
    quizzes: Mapped[list["Quiz"]] = relationship(back_populates="subject", cascade="all, delete-orphan")
    flashcard_decks: Mapped[list["FlashcardDeck"]] = relationship(back_populates="subject", cascade="all, delete-orphan")
    chat_sessions: Mapped[list["ChatSession"]] = relationship(back_populates="subject", cascade="all, delete-orphan")