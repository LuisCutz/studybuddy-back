import uuid

from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Question(Base):
	__tablename__ = "question"

	id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	quiz_id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True),
		ForeignKey("quiz.id", ondelete="CASCADE"),
		nullable=False,
		index=True,
	)
	type: Mapped[str] = mapped_column(String(50), nullable=False)
	prompt: Mapped[str] = mapped_column(Text, nullable=False)
	options: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
	correct_answer: Mapped[str] = mapped_column(Text, nullable=False)

	quiz: Mapped["Quiz"] = relationship(back_populates="questions")