import uuid
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class QuizAttempt(Base):
	__tablename__ = "quiz_attempt"

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	user_id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True),
		ForeignKey("user.id", ondelete="CASCADE"),
		nullable=False,
		index=True,
	)
	quiz_id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True),
		ForeignKey("quiz.id", ondelete="CASCADE"),
		nullable=False,
		index=True,
	)
	score: Mapped[float] = mapped_column(Float, nullable=False)
	completed_at: Mapped[date] = mapped_column(Date, nullable=False, server_default=func.current_date())

	user: Mapped["User"] = relationship(back_populates="quiz_attempts")
	quiz: Mapped["Quiz"] = relationship(back_populates="attempts")