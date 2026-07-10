import os
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload
import fitz

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.quiz_attempt import QuizAttempt
from app.models.user import User
from app.models.document import Document
from app.models.quiz import Quiz
from app.models.question import Question
from app.schemas.quiz import GenerateQuizRequest, QuizResponse, QuizWithAnswersResponse
from app.services.llm.factory import get_llm_service
from app.services.storage import StorageService

router = APIRouter()

async def extract_text_from_r2(file_path: str) -> str:
    # Descarga el PDF usando StorageService y extrae el texto en memoria.
    storage = StorageService()
    
    file_key = file_path
    if "/" in file_path:
        file_key = file_path.split("/", 1)[1]
        
    pdf_bytes = await storage.get_file_content(file_key)
    
    text = ""
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
            
    return text


@router.post("/generate", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
async def generate_quiz(
    payload: GenerateQuizRequest, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Document).where(Document.id == payload.document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
        
    try:
        document_text = await extract_text_from_r2(document.file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error leyendo el documento de R2: {str(e)}")
        
    llm_service = get_llm_service()
    
    try:
        quiz_data = await llm_service.generate_quiz(text=document_text, num_questions=payload.num_questions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar el quiz con IA: {str(e)}")
        
    new_quiz = Quiz(
        subject_id=document.subject_id,
        title=quiz_data.get("title", f"Quiz de {document.title}"),
        topic=quiz_data.get("topic", "Tema general")
    )
    db.add(new_quiz)
    await db.flush()
    
    questions_to_insert = []
    for q_data in quiz_data.get("questions", []):
        new_question = Question(
            quiz_id=new_quiz.id,
            type=q_data.get("type", "multiple_choice"),
            prompt=q_data.get("prompt"),
            options=q_data.get("options"),
            correct_answer=q_data.get("correct_answer")
        )
        questions_to_insert.append(new_question)
        
    db.add_all(questions_to_insert)
    await db.commit()
    
    result = await db.execute(
        select(Quiz).options(selectinload(Quiz.questions)).where(Quiz.id == new_quiz.id)
    )
    final_quiz = result.scalar_one()

    return final_quiz

@router.get("/my-attempts", summary="Listar todos los intentos de quizzes del usuario")
async def get_my_quizzes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Devuelve la lista de intentos del usuario, incluyendo información del quiz asociado.
    stmt = (
        select(QuizAttempt)
        .options(joinedload(QuizAttempt.quiz))
        .where(QuizAttempt.user_id == current_user.id)
        .order_by(QuizAttempt.started_at.desc())
    )
    
    result = await db.execute(stmt)
    attempts = result.scalars().all()
    
    return [
        {
            "attempt_id": attempt.id,
            "quiz_id": attempt.quiz_id,
            "quiz_title": attempt.quiz.title,
            "score": attempt.score,
            "started_at": attempt.started_at,
            "completed_at": attempt.completed_at,
            "is_finished": attempt.completed_at is not None
        }
        for attempt in attempts
    ]

@router.get("/{quiz_id}", summary="Obtener un quiz específico")
async def get_quiz(
    quiz_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Devuelve las preguntas sin respuestas. Si el usuario ya lo completó, incluye las respuestas correctas.
    stmt_quiz = select(Quiz).options(selectinload(Quiz.questions)).where(Quiz.id == quiz_id)
    result_quiz = await db.execute(stmt_quiz)
    quiz = result_quiz.scalar_one_or_none()
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz no encontrado.")
        
    stmt_attempt = (
        select(QuizAttempt)
        .where(
            QuizAttempt.quiz_id == quiz_id,
            QuizAttempt.user_id == current_user.id,
            QuizAttempt.completed_at.is_not(None)
        )
    )
    result_attempt = await db.execute(stmt_attempt)
    completed_attempt = result_attempt.scalar_one_or_none()
    
    if completed_attempt:
        return QuizWithAnswersResponse.model_validate(quiz)
    else:
        return QuizResponse.model_validate(quiz)