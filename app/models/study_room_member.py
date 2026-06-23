import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class StudyRoomMember(Base):
	__tablename__ = "study_room_member"

	user_id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True),
		ForeignKey("user.id", ondelete="CASCADE"),
		primary_key=True,
	)
	room_id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True),
		ForeignKey("study_room.id", ondelete="CASCADE"),
		primary_key=True,
	)
	role: Mapped[str] = mapped_column(String(50), nullable=False)

	user: Mapped["User"] = relationship(back_populates="room_memberships")
	room: Mapped["StudyRoom"] = relationship(back_populates="members")