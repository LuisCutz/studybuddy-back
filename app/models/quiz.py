import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

class Quiz(Base):
	__tablename__ = "quiz"

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	room_id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True),
		ForeignKey("study_room.id", ondelete="CASCADE"),
		nullable=False,
		index=True,
	)
	title: Mapped[str] = mapped_column(String(255), nullable=False)
	topic: Mapped[str] = mapped_column(String(255), nullable=False)

	room: Mapped["StudyRoom"] = relationship(back_populates="quizzes")
	questions: Mapped[list["Question"]] = relationship(back_populates="quiz", cascade="all, delete-orphan")
	attempts: Mapped[list["QuizAttempt"]] = relationship(back_populates="quiz", cascade="all, delete-orphan")
