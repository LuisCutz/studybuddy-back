from __future__ import annotations

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.base import Base

if TYPE_CHECKING:
    from src.infrastructure.database.models.study_room_member import StudyRoomMember
    from src.infrastructure.database.models.subject import Subject
    from src.infrastructure.database.models.user import User


class StudyRoom(Base):
    __tablename__ = "study_room"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)

    memberships: Mapped[list["StudyRoomMember"]] = relationship(
        back_populates="room",
        cascade="all, delete-orphan",
    )
    users: Mapped[list["User"]] = relationship(
        secondary="study_room_member",
        back_populates="study_rooms",
        viewonly=True,
    )
    subjects: Mapped[list["Subject"]] = relationship(back_populates="room", cascade="all, delete-orphan")