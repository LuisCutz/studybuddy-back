from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.quiz_attempt import QuizAttempt
from app.models.flashcard_deck import FlashcardDeck
from app.models.flashcard_deck_view import FlashcardDeckView
from app.models.daily_activity import DailyActivity

from app.schemas.progress import StudentProgressResponse, DailyActivityResponse
from app.schemas.flashcard import DeckResponse

router = APIRouter()


@router.get("/health", summary="Check Progress API Health")
async def progress_health_check():
    return {
        "status": "ok",
        "module": "Progress API",
        "version": "v1",
        "visibility": "private",
        "requires_jwt": True,
        "documentation": {
            "swagger_url": "/docs",
            "openapi_json_url": "/openapi.json",
        },
    }

@router.get("/me", response_model=StudentProgressResponse, summary="Obtener estadísticas generales del usuario")
async def get_my_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result_quizzes = await db.execute(
        select(func.count(QuizAttempt.id))
        .where(QuizAttempt.user_id == current_user.id, QuizAttempt.completed_at.is_not(None))
    )
    total_quizzes = result_quizzes.scalar() or 0

    result_score = await db.execute(
        select(func.avg(QuizAttempt.score))
        .where(QuizAttempt.user_id == current_user.id, QuizAttempt.completed_at.is_not(None))
    )
    avg_score = result_score.scalar() or 0.0

    result_decks = await db.execute(
        select(func.count(FlashcardDeck.id))
        .where(FlashcardDeck.user_id == current_user.id)
    )
    total_decks = result_decks.scalar() or 0

    return {
        "total_quizzes_taken": total_quizzes,
        "average_quiz_score": round(avg_score, 2),
        "total_flashcards_generated": total_decks
    }


@router.get("/unseen-flashcards", response_model=list[DeckResponse], summary="Mazos generados que el usuario no ha estudiado")
async def get_unseen_flashcards(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(FlashcardDeck)
        .outerjoin(
            FlashcardDeckView, 
            (FlashcardDeck.id == FlashcardDeckView.deck_id) & (FlashcardDeckView.viewer_id == current_user.id)
        )
        .where(
            FlashcardDeck.user_id == current_user.id,
            FlashcardDeckView.id.is_(None)
        )
    )
    
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("/ping", summary="Registrar 1 minuto de actividad para hoy")
async def ping_activity(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    today = date.today()
    
    result = await db.execute(
        select(DailyActivity)
        .where(DailyActivity.user_id == current_user.id, DailyActivity.activity_date == today)
    )
    activity = result.scalar_one_or_none()

    if activity:
        activity.minutes_spent += 1
    else:
        activity = DailyActivity(user_id=current_user.id, activity_date=today, minutes_spent=1)
        db.add(activity)

    await db.commit()
    return {"message": "Actividad registrada", "minutes_today": activity.minutes_spent}

@router.get("/activity", response_model=list[DailyActivityResponse], summary="Historial de tiempo en la plataforma")
async def get_activity_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(DailyActivity)
        .where(DailyActivity.user_id == current_user.id)
        .order_by(DailyActivity.activity_date.asc())
    )
    return list(result.scalars().all())