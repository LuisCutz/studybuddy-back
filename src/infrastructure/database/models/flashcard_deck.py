from __future__ import annotations

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.base import Base

if TYPE_CHECKING:
    from src.infrastructure.database.models.flashcard import Flashcard
    from src.infrastructure.database.models.subject import Subject


class FlashcardDeck(Base):
    __tablename__ = "flashcard_deck"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("subject.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    subject: Mapped["Subject"] = relationship(back_populates="flashcard_decks")
    flashcards: Mapped[list["Flashcard"]] = relationship(back_populates="deck", cascade="all, delete-orphan")