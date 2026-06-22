from __future__ import annotations

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.base import Base

if TYPE_CHECKING:
    from src.infrastructure.database.models.chat_session import ChatSession
    from src.infrastructure.database.models.document import Document
    from src.infrastructure.database.models.flashcard_deck import FlashcardDeck
    from src.infrastructure.database.models.quiz import Quiz
    from src.infrastructure.database.models.study_room import StudyRoom
    from src.infrastructure.database.models.summary import Summary


class Subject(Base):
    __tablename__ = "subject"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("study_room.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    room: Mapped["StudyRoom"] = relationship(back_populates="subjects")
    documents: Mapped[list["Document"]] = relationship(back_populates="subject", cascade="all, delete-orphan")
    flashcard_decks: Mapped[list["FlashcardDeck"]] = relationship(back_populates="subject", cascade="all, delete-orphan")
    quizzes: Mapped[list["Quiz"]] = relationship(back_populates="subject", cascade="all, delete-orphan")
    summaries: Mapped[list["Summary"]] = relationship(back_populates="subject", cascade="all, delete-orphan")
    chat_sessions: Mapped[list["ChatSession"]] = relationship(back_populates="subject", cascade="all, delete-orphan")