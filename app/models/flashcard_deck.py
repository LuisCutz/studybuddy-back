import uuid
from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

class FlashcardDeck(Base):
    __tablename__ = "flashcard_deck"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("study_room.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    
    description: Mapped[str | None] = mapped_column(String, nullable=True)

    room: Mapped["StudyRoom"] = relationship(back_populates="flashcard_decks")
    user: Mapped["User"] = relationship()
    flashcards: Mapped[list["Flashcard"]] = relationship(back_populates="deck", cascade="all, delete-orphan")
    views: Mapped[list["FlashcardDeckView"]] = relationship(back_populates="deck", cascade="all, delete-orphan")