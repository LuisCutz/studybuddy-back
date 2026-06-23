import uuid

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Flashcard(Base):
	__tablename__ = "flashcard"

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	deck_id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True),
		ForeignKey("flashcard_deck.id", ondelete="CASCADE"),
		nullable=False,
		index=True,
	)
	front: Mapped[str] = mapped_column(Text, nullable=False)
	back: Mapped[str] = mapped_column(Text, nullable=False)

	deck: Mapped["FlashcardDeck"] = relationship(back_populates="flashcards")