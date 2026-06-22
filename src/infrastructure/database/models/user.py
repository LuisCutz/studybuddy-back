from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.base import Base

if TYPE_CHECKING:
    from src.infrastructure.database.models.chat_session import ChatSession
    from src.infrastructure.database.models.quiz_attempt import QuizAttempt
    from src.infrastructure.database.models.study_room import StudyRoom
    from src.infrastructure.database.models.study_room_member import StudyRoomMember


class User(Base):
    __tablename__ = "user"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    current_streak: Mapped[int] = mapped_column(default=0, nullable=False)
    created_at: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)

    room_memberships: Mapped[list["StudyRoomMember"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    study_rooms: Mapped[list["StudyRoom"]] = relationship(
        secondary="study_room_member",
        back_populates="users",
        viewonly=True,
    )
    chat_sessions: Mapped[list["ChatSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    quiz_attempts: Mapped[list["QuizAttempt"]] = relationship(back_populates="user", cascade="all, delete-orphan")