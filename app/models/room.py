import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class StudyRoom(Base):
    __tablename__ = "study_room"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tenant_id: Mapped[str] = mapped_column(String(100), nullable=False, default="default-tenant")

    members: Mapped[list["StudyRoomMember"]] = relationship(
        back_populates="room",
        cascade="all, delete-orphan",
    )
    subjects: Mapped[list["Subject"]] = relationship(
        back_populates="room",
        cascade="all, delete-orphan",
    )

    invitations: Mapped[list["Invitation"]] = relationship(
        back_populates="room",
        cascade="all, delete-orphan"
    )