import uuid
from sqlalchemy import Date, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

class Organization(Base):
    __tablename__ = "organization"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[object] = mapped_column(Date, nullable=False, server_default=func.current_date())

    invitations: Mapped[list["Invitation"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan",
    )