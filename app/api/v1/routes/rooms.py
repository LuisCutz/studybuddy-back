from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_room_access
from app.db.session import get_db
from app.models.room import StudyRoom
from app.models.study_room_member import StudyRoomMember
from app.models.user import User

router = APIRouter()


@router.get("/{room_id}", status_code=status.HTTP_200_OK)
async def get_room(
    room_id: str,
    current_user: User = Depends(require_room_access("admin", "profesor", "alumno")),
    db: AsyncSession = Depends(get_db),
):
    room_uuid = UUID(room_id)
    room = await db.get(StudyRoom, room_uuid)
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Study room not found")

    if current_user.tenant_id != room.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: room belongs to another tenant")

    membership_result = await db.execute(
        select(StudyRoomMember).where(
            StudyRoomMember.user_id == current_user.id,
            StudyRoomMember.room_id == room_uuid,
        )
    )
    membership = membership_result.scalar_one_or_none()
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: user is not a room member")

    return {"id": str(room.id), "name": room.name, "tenant_id": room.tenant_id, "role": membership.role}
